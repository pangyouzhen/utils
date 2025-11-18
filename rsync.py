#!/usr/bin/env python
import os
import stat
import argparse
import paramiko
import zlib
import posixpath


# -----------------------------
# SSH CONFIG
# -----------------------------
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


# -----------------------------
# INTERNAL HELPERS
# -----------------------------
def ensure_remote_dir(sftp, rdir):
    """
    递归创建远程目录，类似 mkdir -p
    """
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


# -----------------------------
# PULL: remote → local
# -----------------------------
def rsync_pull(ssh, remote_path, local_path):
    sftp = ssh.open_sftp()

    def download_recursive(rpath, lpath):
        try:
            st = sftp.stat(rpath)
        except FileNotFoundError:
            print(f"[ERROR] Remote path not found: {rpath}")
            return

        # file
        if stat.S_ISREG(st.st_mode):
            os.makedirs(os.path.dirname(lpath), exist_ok=True)
            print(f"[FILE] {rpath} → {lpath}")

            with sftp.open(rpath, "rb") as rf:
                data = rf.read()

            # zlib 解压 = 模拟 rsync -z
            decompressed = zlib.decompress(zlib.compress(data, 6))

            with open(lpath, "wb") as lf:
                lf.write(decompressed)

            os.utime(lpath, (st.st_atime, st.st_mtime))
            return

        # dir
        if stat.S_ISDIR(st.st_mode):
            os.makedirs(lpath, exist_ok=True)
            print(f"[DIR ] {rpath}")

            for item in sftp.listdir_attr(rpath):
                rchild = f"{rpath}/{item.filename}"
                lchild = os.path.join(lpath, item.filename)
                download_recursive(rchild, lchild)

    download_recursive(remote_path, local_path)

    sftp.close()
    print("=== PULL DONE ===")


# -----------------------------
# PUSH: local → remote
# -----------------------------
def rsync_push(ssh, local_path, remote_path):
    sftp = ssh.open_sftp()

    def upload_recursive(lpath, rpath):
        if os.path.isfile(lpath):
            rdir = posixpath.dirname(rpath)
            ensure_remote_dir(sftp, rdir)

            print(f"[FILE] {lpath} → {rpath}")

            with open(lpath, "rb") as lf:
                data = lf.read()

            compressed = zlib.compress(data, 6)
            data_out = zlib.decompress(compressed)

            with sftp.open(rpath, "wb") as rf:
                rf.write(data_out)

            st = os.stat(lpath)
            sftp.utime(rpath, (st.st_atime, st.st_mtime))
            return

        if os.path.isdir(lpath):
            print(f"[DIR ] {lpath}")

            ensure_remote_dir(sftp, rpath)

            for name in os.listdir(lpath):
                upload_recursive(
                    os.path.join(lpath, name),
                    posixpath.join(rpath, name),
                )

    upload_recursive(local_path, remote_path)

    sftp.close()
    print("=== PUSH DONE ===")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("dst")
    args = parser.parse_args()

    # Case 1: src = host:/path  → pull
    if ":" in args.src and not os.path.exists(args.src.split(":", 1)[0]):
        host, remote_path = args.src.split(":", 1)
        local_path = args.dst
        ssh = create_ssh_client(host)
        rsync_pull(ssh, remote_path, local_path)
        ssh.close()
        exit(0)

    # Case 2: dst = host:/path  → push
    if ":" in args.dst and not os.path.exists(args.dst.split(":", 1)[0]):
        host, remote_path = args.dst.split(":", 1)
        local_path = args.src
        ssh = create_ssh_client(host)
        rsync_push(ssh, local_path, remote_path)
        ssh.close()
        exit(0)

    raise ValueError("You must specify either src or dst in host:/path format")
