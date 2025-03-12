from collections import defaultdict

import gensim
import numpy as np
import re
from sklearn.metrics.pairwise import cosine_similarity


def standardize_code(code):
    """预处理代码：标准化格式并提取关键结构"""
    # 处理换行符和空白
    code = re.sub(r'\r\n', '\n', code)
    code = re.sub(r'\s+', ' ', code)

    # 移除注释
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code = re.sub(r'//.*', '', code)

    # 标准化格式
    code = re.sub(r'\s+', ' ', code)  # 压缩空格
    code = re.sub(r'\s*([;{},()])\s*', r'\1', code)  # 清理符号周围空格
    return code.strip()


def preprocess_code(code_str, n=3):
    length = len(code_str)
    if length < n:
        code_str += ' ' * (n - length)
        return [code_str]
    return [code_str[i:i+n] for i in range(len(code_str)-n+1)]


def parse_code_blocks(code):
    # 分割代码块
    blocks = []

    for token in re.split(r'([{};])', code):
        token = token.strip()
        if not token:
            continue
        # 收集全局声明
        if token not in ['{', '}']:
            blocks.append(token)

    return blocks


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


# def tokenize_code(code):
#     """
#     将代码分割成单词
#     :param code: 代码字符串
#     :return: 单词列表
#     """
#     import re
#     # 移除换行符等空白字符
#     code = re.sub(r'\s+', ' ', code).strip()
#     # 只匹配字母、数字和下划线组成的单词
#     tokens = re.findall(r'\w+', code)
#     # tokens = re.findall(r'\w+|[^\w\s]', code)
#     return tokens
#
#
# def generate_ngrams(tokens, n):
#     """
#     生成 N - grams
#     :param tokens: 单词列表
#     :param n: N 的值
#     :return: N - grams 列表
#     """
#     ngrams = []
#     for i in range(len(tokens) - n + 1):
#         ngram = ' '.join(tokens[i:i + n])
#         ngrams.append(ngram)
#     return ngrams


def code_to_vector(ngrams, model):
    """向量转换函数（与之前相同）"""
    vectors = []
    for ng in ngrams:
        try:
            vectors.append(model.wv[ng])
        except KeyError:
            vectors.append(np.zeros(model.vector_size))
    return np.mean(vectors, axis=0)


def calculate_similarity(code1, code2, n=3):
    if not code1 or not code2:
        return 0.0
    # 标准化
    code1 = standardize_code(code1)
    code2 = standardize_code(code2)

    # 解析代码结构
    code1 = parse_code_blocks(code1)
    code2 = parse_code_blocks(code2)

    # 去除重复代码
    code1, code2 = filter_common_blocks(code1, code2)
    # 合并过滤结果
    code1 = ';'.join(code1)
    code2 = ';'.join(code2)

    print(f"最终的代码1为:{code1}")
    print(f"最终的代码2为:{code2}")

    if code1 == '' and code2 == '':
        return 1.0

    # 预处理，分割成n-grams
    ngrams1 = preprocess_code(code1, n)
    ngrams2 = preprocess_code(code2, n)
    all_ngrams = ngrams1 + ngrams2

    model = gensim.models.Word2Vec(
        sentences=[all_ngrams],
        vector_size=64,
        window=5,
        min_count=1,
        epochs=100,
        workers=4,
        seed=42,
        hs=1
    )
    vec1 = code_to_vector(ngrams1, model)
    vec2 = code_to_vector(ngrams2, model)
    if np.all(vec1 == 0) and np.all(vec2 == 0):
        return 1.0 if code1 == code2 else 0.0
    return cosine_similarity([vec1], [vec2])[0][0]