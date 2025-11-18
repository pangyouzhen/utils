#!/usr/bin/env python
"""
Zstandard 压缩/解压命令行工具

功能：
- 不指定 -d：压缩文件，自动添加 .zst 后缀
- 指定 -d：解压文件，自动去除 .zst 后缀
- 无需手动输入输出文件名
"""

import argparse
import sys
import zstandard as zstd
import os

def compress_file(input_path):
    output_path = input_path + '.zst'
    with open(input_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            cctx = zstd.ZstdCompressor()
            compressed_data = cctx.compress(f_in.read())
            f_out.write(compressed_data)
    print(f"✅ 已压缩: {input_path} -> {output_path}")

def decompress_file(input_path):
    # 推断输出文件名：移除末尾的 .zst
    if input_path.endswith('.zst'):
        output_path = input_path[:-4]  # 去掉 .zst
    else:
        output_path = input_path + '.out'  # 回退方案
        print(f"⚠️ 无法识别 .zst 后缀，默认输出为: {output_path}")

    with open(input_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            dctx = zstd.ZstdDecompressor()
            decompressed_data = dctx.decompress(f_in.read())
            f_out.write(decompressed_data)
    print(f"✅ 已解压: {input_path} -> {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Zstandard 压缩/解压工具",
        usage="""
%(prog)s [选项] 文件

示例:
  %(prog)s file.txt           # 压缩为 file.txt.zst
  %(prog)s -d file.txt.zst    # 解压为 file.txt
        """
    )
    parser.add_argument('file', help='输入文件路径')
    parser.add_argument('-d', '--decompress', action='store_true',
                        help='解压模式')

    args = parser.parse_args()

    # 检查文件是否存在
    if not os.path.isfile(args.file):
        print(f"❌ 错误: 文件不存在: {args.file}")
        sys.exit(1)

    try:
        if args.decompress:
            print(f"🔄 正在解压 {args.file}")
            decompress_file(args.file)
        else:
            print(f"🔄 正在压缩 {args.file}")
            compress_file(args.file)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

