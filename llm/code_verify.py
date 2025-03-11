import gensim
import numpy as np
import re
from sklearn.metrics.pairwise import cosine_similarity


def preprocess_code(code_str, n=3):
    """预处理函数（与之前相同）"""
    code_str = re.sub(r'\r\n', '\n', code_str)
    code_str = re.sub(r'\s+', ' ', code_str)
    code_str = code_str.strip()
    length = len(code_str)
    if length < n:
        code_str += ' ' * (n - length)
        return [code_str]
    return [code_str[i:i+n] for i in range(len(code_str)-n+1)]


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