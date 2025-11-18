#!/usr/bin/env python
# 实现简单的jq功能, 解决在有些机器上不能安装jq的问题
import sys
import json

def get_value(data, path):
    parts = path.split('.')
    result = data
    for part in parts:
        print(part)
        if part.endswith('[]'):
            key = part[:-2]
            result = [item[key] for item in result if isinstance(item, dict) and key in item]
        else:
            key = part
            if isinstance(result, dict):
                result = result.get(key, None)
            elif isinstance(result, list) and key.isdigit():
                result = result[int(key)] if int(key) < len(result) else None
            else:
                result = None
    return result

def main():
    if len(sys.argv) < 2:
        print("用法: python jq.py '.path' [文件名]")
        sys.exit(1)

    query = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else None

    # 读取 JSON 数据
    if filename:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    # 提取字段
    result = get_value(data, query.strip('.'))

    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()