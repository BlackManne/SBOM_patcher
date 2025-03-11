import difflib

# 定义两个示例代码字符串
code1 = """
def add(a, b):
    return a + b

print(add(1, 2))
"""

code2 = """
def add_numbers(a, b):
    return a + b

print(add(1, 2))
"""

# 将字符串按行分割成列表
lines1 = code1.splitlines(keepends=True)
lines2 = code2.splitlines(keepends=True)

# 使用 unified_diff 函数比较两个代码块
diff = difflib.unified_diff(lines1, lines2, fromfile='code1.py', tofile='code2.py', n=2)

# 输出比较结果
print(''.join(diff))