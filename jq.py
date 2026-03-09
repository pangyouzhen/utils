import sys
import json
import re

def parse_query(query):
    """解析 jq 查询语法，转换为操作令牌 (Tokens) 列表"""
    if query.startswith('.'):
        query = query[1:]
        
    tokens = []
    # 正则：匹配 1.字典键名 2.数组索引 3.空括号迭代器[]
    # 组1: 键名 (例如 users)
    # 组2: 索引数字 (如果为空，代表匹配到了 [])
    for match in re.finditer(r'([^.\[\]]+)|\[(\d*)\]', query):
        g1, g2 = match.groups()
        if g1:
            tokens.append(('key', g1))
        elif g2 == "":
            tokens.append(('iter', None)) # 匹配到 []
        else:
            tokens.append(('index', int(g2))) # 匹配到 [0], [1] 等
    return tokens

def execute_query(data, tokens):
    """递归执行查询，使用生成器返回数据流以支持迭代器"""
    # 如果没有剩余的操作令牌，直接产出当前数据
    if not tokens:
        yield data
        return
        
    token_type, value = tokens[0]
    rest_tokens = tokens[1:]
    
    if token_type == 'key':
        # 处理字典键提取
        if isinstance(data, dict) and value in data:
            yield from execute_query(data[value], rest_tokens)
        else:
            yield None
            
    elif token_type == 'index':
        # 处理具体的数组索引 [N]
        if isinstance(data, list):
            try:
                yield from execute_query(data[value], rest_tokens)
            except IndexError:
                yield None
        else:
            yield None
            
    elif token_type == 'iter':
        # 处理迭代器 []
        if isinstance(data, list):
            # 遍历数组，对每个元素继续执行后续查询
            for item in data:
                yield from execute_query(item, rest_tokens)
        elif isinstance(data, dict):
            # jq 中对对象使用 [] 会迭代其 values
            for item in data.values():
                yield from execute_query(item, rest_tokens)
        else:
            yield None

def main():
    if len(sys.argv) < 2:
        print("用法: python pyjq.py '<查询表达式>' [文件路径]")
        print("示例: cat data.json | python pyjq.py '.users[].name'")
        sys.exit(1)
        
    query = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            with open(sys.argv[2], 'r', encoding='utf-8') as f:
                raw_data = f.read()
        except FileNotFoundError:
            print(f"错误: 找不到文件 {sys.argv[2]}", file=sys.stderr)
            sys.exit(1)
    else:
        raw_data = sys.stdin.read()
        
    if not raw_data.strip():
        print("错误: 没有接收到输入数据", file=sys.stderr)
        sys.exit(1)
        
    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}", file=sys.stderr)
        sys.exit(1)
        
    tokens = parse_query(query)
    
    # 消费生成器并逐行打印，完全模仿 jq 数据流的输出方式
    for result in execute_query(data, tokens):
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()