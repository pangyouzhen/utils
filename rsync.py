#!/usr/bin/env python
import os
import stat
import argparse
import paramiko
import zlib
import posixpath
import time


def load_ssh_config(host):
    config = paramiko.SSHConfig()
    cfg_path = os.path.expanduser("~/.ssh/config")
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            config.parse(f)
    return config.lookup(host)


def create_ssh_client(host_alias):
    cfg = load_ssh_config(host_alias)
    hostname = cfg.get("hostname", host_alias)
    port = int(cfg.get("port", 22))
    user = cfg.get("user", None)
    key_file = cfg.get("identityfile", [None])[0]

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(
        hostname=hostname,
        username=user,
        port=port,
        key_filename=key_file,
        compress=True,
    )
    return ssh


def ensure_remote_dir(sftp, rdir):
    dirs = []
    while True:
        head, tail = posixpath.split(rdir)
        if head == rdir:
            dirs.append(head)
            break
        if tail:
            dirs.append(rdir)
        rdir = head

    for d in reversed(dirs):
        try:
            sftp.stat(d)
        except IOError:
            print(f"[MKDIR] {d}")
            sftp.mkdir(d)


# =====================================
# PULL: remote → local
# =====================================
def rsync_pull(ssh, remote_path, local_path):
    sftp = ssh.open_sftp()

    def download_recursive(rpath, lpath):
        try:
            st = sftp.stat(rpath)
        except FileNotFoundError:
            print(f"[ERROR] Remote path not found: {rpath}")
            return

        # ==== file ====
        if stat.S_ISREG(st.st_mode):
            os.makedirs(os.path.dirname(lpath), exist_ok=True)

            # 增量判断：本地存在且时间+大小相同 → 跳过
            if os.path.exists(lpath):
                lst = os.stat(lpath)
                if lst.st_size == st.st_size and int(lst.st_mtime) == int(st.st_mtime):
                    print(f"[SKIP] {rpath}")
                    return

            print(f"[FILE] {rpath} → {lpath}")

            with sftp.open(rpath, "rb") as rf:
                data = rf.read()

            data = zlib.decompress(zlib.compress(data, 6))

            with open(lpath, "wb") as lf:
                lf.write(data)

            os.utime(lpath, (st.st_atime, st.st_mtime))
            return

        # ==== dir ====
        if stat.S_ISDIR(st.st_mode):
            os.makedirs(lpath, exist_ok=True)
            print(f"[DIR ] {rpath}")

            for item in sftp.listdir_attr(rpath):
                rchild = posixpath.join(rpath, item.filename)
                lchild = os.path.join(lpath, item.filename)
                download_recursive(rchild, lchild)

    download_recursive(remote_path, local_path)
    sftp.close()
    print("=== PULL DONE ===")


# =====================================
# PUSH: local → remote
# =====================================
def rsync_push(ssh, local_path, remote_path):
    sftp = ssh.open_sftp()

    def upload_recursive(lpath, rpath):
        # ==== file ====
        if os.path.isfile(lpath):
            rdir = posixpath.dirname(rpath)
            ensure_remote_dir(sftp, rdir)

            # remote 文件存在 → 判断增量
            try:
                rst = sftp.stat(rpath)
                lst = os.stat(lpath)
                if rst.st_size == lst.st_size and int(rst.st_mtime) == int(lst.st_mtime):
                    print(f"[SKIP] {lpath}")
                    return
            except IOError:
                pass

            print(f"[FILE] {lpath} → {rpath}")

            with open(lpath, "rb") as lf:
                data = lf.read()

            data_out = zlib.decompress(zlib.compress(data, 6))

            with sftp.open(rpath, "wb") as rf:
                rf.write(data_out)

            st = os.stat(lpath)
            sftp.utime(rpath, (st.st_atime, st.st_mtime))
            return

        # ==== dir ====
        if os.path.isdir(lpath):
            ensure_remote_dir(sftp, rpath)
            print(f"[DIR ] {lpath}")

            for name in os.listdir(lpath):
                upload_recursive(
                    os.path.join(lpath, name),
                    posixpath.join(rpath, name),   # ← 修复关键点：确保文件名拼接正确
                )

    upload_recursive(local_path, remote_path)
    sftp.close()
    print("=== PUSH DONE ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-avzP")
    parser.add_argument("src")
    parser.add_argument("dst")
    args = parser.parse_args()

    # pull
    if ":" in args.src and not os.path.exists(args.src.split(":", 1)[0]):
        host, remote_path = args.src.split(":", 1)
        ssh = create_ssh_client(host)
        rsync_pull(ssh, remote_path, args.dst)
        ssh.close()
        exit(0)

    # push
    if ":" in args.dst and not os.path.exists(args.dst.split(":", 1)[0]):
        host, remote_path = args.dst.split(":", 1)
        ssh = create_ssh_client(host)
        rsync_push(ssh, args.src, remote_path)
        ssh.close()
        exit(0)

    raise ValueError("You must specify either src or dst in host:/path format")
