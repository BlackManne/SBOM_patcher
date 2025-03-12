import re
from difflib import SequenceMatcher
from collections import defaultdict

import gensim


def preprocess_code(code):
    """预处理代码：标准化格式并提取关键结构"""
    # 移除注释
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code = re.sub(r'//.*', '', code)

    # 标准化格式
    code = re.sub(r'\s+', ' ', code)  # 压缩空格
    code = re.sub(r'\s*([;{},()])\s*', r'\1', code)  # 清理符号周围空格
    return code.strip()


def parse_code_blocks(code):
    """解析代码结构：返回全局声明和函数字典"""
    # 分割全局声明和函数定义
    global_blocks = []
    functions = defaultdict(str)

    # 使用状态机解析代码结构
    current_func = None
    brace_count = 0
    buffer = []

    for token in re.split(r'([{};])', code):
        token = token.strip()
        if not token:
            continue

        # # 函数解析状态管理
        # if current_func:
        #     buffer.append(token)
        #     if token == '{':
        #         brace_count += 1
        #     elif token == '}':
        #         brace_count -= 1
        #         if brace_count == 0:
        #             functions[current_func] = ' '.join(buffer)
        #             current_func = None
        #             buffer = []
        #     continue
        #
        # func_pattern = re.compile(r'^\s((?:static\s+|inline\s+|attribute\s\(\(.?\)\)\s)*)'
        #                           r'((?:\w+|\+|\s&?)\s+)+?'
        #                           r'(\w+)\s\(([^)])\)\s*{'
        #                           )
        # # 检测函数定义
        # if re.match(func_pattern, token):
        #     match = re.search(func_pattern, token)
        #     if match:
        #         current_func = match.group(3)
        #         brace_count = 0
        #         buffer = [token]
        # 收集全局声明
        elif token not in ['{', '}']:
            global_blocks.append(token)

    return ';'.join(global_blocks), dict(functions)


def filter_common_blocks(blocks1, blocks2):
    """过滤相同结构的代码块"""
    counter1 = defaultdict(int)
    counter2 = defaultdict(int)

    # 统计块出现次数
    for b in blocks1:
        counter1[b] += 1
    for b in blocks2:
        counter2[b] += 1

    # 生成过滤后的块
    filtered1 = []
    filtered2 = []

    temp_counter = defaultdict(int)
    for b in blocks1:
        if counter2.get(b, 0) > temp_counter[b]:
            temp_counter[b] += 1
        else:
            filtered1.append(b)

    temp_counter = defaultdict(int)
    for b in blocks2:
        if counter1.get(b, 0) > temp_counter[b]:
            temp_counter[b] += 1
        else:
            filtered2.append(b)

    return filtered1, filtered2


def code_similarity(patch1, patch2):
    """主计算函数"""
    # 预处理
    code1 = preprocess_code(patch1)
    code2 = preprocess_code(patch2)

    # 解析代码结构
    global1, funcs1 = parse_code_blocks(code1)
    global2, funcs2 = parse_code_blocks(code2)

    # 处理全局声明
    global_blocks1 = [b for b in global1.split(';') if b]
    global_blocks2 = [b for b in global2.split(';') if b]
    filtered_globals1, filtered_globals2 = filter_common_blocks(global_blocks1, global_blocks2)

    # 处理函数定义
    func_names = set(funcs1.keys()) | set(funcs2.keys())
    filtered_funcs1 = []
    filtered_funcs2 = []

    for name in func_names:
        f1 = funcs1.get(name, '')
        f2 = funcs2.get(name, '')
        if f1 == f2:
            continue
        filtered_funcs1.append(f1)
        filtered_funcs2.append(f2)

    # 合并过滤结果
    final_code1 = ';'.join(filtered_globals1) + ''.join(filtered_funcs1)
    final_code2 = ';'.join(filtered_globals2) + ''.join(filtered_funcs2)

    print(f"最终的代码1为:{final_code1}")
    print(f"最终的代码2为:{final_code2}")
    # 计算相似度
    sm = SequenceMatcher(None, final_code1, final_code2)
    return sm.ratio()


# 示例使用
if __name__ == "__main__":
    system_patch = """
    int global_var;

    void vulnerable_func() {
        char buffer[10];
        gets(buffer);
    }

    void safe_func() {
        printf("Secure code");
    }
    """

    official_patch = """
    int global_var;

    void vulnerable_func() {
        char buffer[10];
        fgets(buffer, 10, stdin);
    }

    void new_func() {
        log("Security fix");
    }
    """

    similarity = code_similarity(system_patch, official_patch)
    print(f"去重后代码相似度: {similarity:.2%}")
