import re
import clang.cindex

from llm.Utils.file_utils import read_files, read_files_by_lines

clang.cindex.Config.set_library_file('C:/BlackMann/Download Software/clang+llvm-18.1.8-x86_64-pc-windows-msvc'
                                     '/clang+llvm-18.1.8-x86_64-pc-windows-msvc/bin/libclang.dll')
# 定义预定义宏
macros = ['DEBUG', 'ENABLE_FEATURE']


def extract_called_function_name_from_diff(diff_line):
    """
    从 diff 行中提取被调用的函数名
    :param diff_line: 包含函数修改信息的 diff 行
    :return: 提取到的被调用函数名，如果没有则返回 None
    """
    # 匹配函数调用的模式
    pattern = re.compile(r'\b([a-zA-Z_]\w*)\(')
    match = pattern.search(diff_line)
    if match:
        return match.group(1)
    return None


def remove_between_double_at_signs(input_string):
    """
    从输入字符串中去除 @@ 和 @@ 之间的内容（包括两个 @@ 本身）
    :param input_string: 原始输入字符串
    :return: 去除 @@ 和 @@ 之间内容后的字符串
    """
    start_index = input_string.find('@@')
    end_index = input_string.find('@@', start_index + 2)
    if start_index == -1 or end_index == -1:
        return input_string
    result = input_string[:start_index] + input_string[end_index + 2:]
    return result


def extract_function_name_from_diff(diff_line):
    """
    从 GitHub 的 diff 行中提取函数名称
    :param diff_line: 包含函数修改信息的 diff 行
    :return: 提取到的函数名称，如果没有则返回 None
    """
    # 匹配函数定义的模式，将 static 关键字标记为可选
    diff_line = remove_between_double_at_signs(diff_line).replace('\n', '')
    pattern = re.compile(r'\s+([\w_]+)\(')
    match = pattern.search(diff_line)
    if match:
        return match.group(1)
    return None


def parse_diff_file(diff_lines):
    """
    解析 diff 文件
    :param diff_lines: diff 文件的内容
    :return: 包含添加和删除代码的字典
    """
    current_function = []
    added_function = set()
    deleted_function = set()
    global_added_code = []
    global_deleted_code = []
    for line in diff_lines:
        if line.startswith('@@'):
            # 尝试提取函数信息
            current_function = extract_function_name_from_diff(line)
        elif line.startswith('-'):
            # 如果没有当前函数，说明是外面的
            if not current_function:
                # 找到第一个'-'的位置
                dash_index = line.find('-')
                line = line[dash_index + 1:].lstrip()
                global_deleted_code.append(line)
            # 如果一个函数里面的代码行出现修改，不管是添加还是删除，前后文件中都应该加入该函数以便于对比
            else:
                deleted_function.add(current_function)
                added_function.add(current_function)
            called_func = extract_called_function_name_from_diff(line)
            if called_func:
                deleted_function.add(called_func)
        elif line.startswith('+'):
            if not current_function:
                # 找到第一个'+'的位置
                dash_index = line.find('+')
                line = line[dash_index + 1:].lstrip()
                global_added_code.append(line)
            else:
                added_function.add(current_function)
                deleted_function.add(current_function)
            called_func = extract_called_function_name_from_diff(line)
            if called_func:
                added_function.add(called_func)
    return \
        {
            'global_deleted_code': global_deleted_code,
            'global_added_code': global_added_code,
            'added_function': added_function,
            'deleted_function': deleted_function
        }


def find_function_body(ast, function_name):
    """
    从 AST 中查找函数的函数体
    :param ast: 解析后的 AST,以dict形式给出函数列表
    :param function_name: 函数名
    :return: 函数体的代码行
    """
    if function_name not in ast:
        print(f'名称为{function_name}的函数不存在!')
        return None
    return ast[function_name]


def get_function_code(cursor, code):
    start_offset = cursor.extent.start.offset
    end_offset = cursor.extent.end.offset
    raw_code = code[start_offset:end_offset]

    # 有效性检查（过滤空函数体）
    code_content = raw_code.strip()
    if code_content in {"{}", "{ }", "{;}"}: # 常见空函数体模式
        return None

    return raw_code

def func_definition_or_not(cursor):
    has_body = False
    for child in cursor.get_children():
        if child.kind == clang.cindex.CursorKind.COMPOUND_STMT:
            has_body = True
            break
    if has_body:
        return True


def find_all_functions(cursor, source_code):
    """
    递归遍历 AST，查找所有函数定义并提取函数体代码
    :param cursor: 当前遍历到的 AST 节点
    :param source_code: 包含函数的源代码
    :return: 包含函数名和函数体代码的字典
    """
    functions = {}
    if cursor.kind in {clang.cindex.CursorKind.FUNCTION_DECL,
                       clang.cindex.CursorKind.CONSTRUCTOR,
                       clang.cindex.CursorKind.DESTRUCTOR}:
        # 如果是一个函数定义，才添加函数代码
        if cursor.is_definition():
            children = list(cursor.get_children())  # 获取子节点列表
            if children:  # 确保函数体不为空
                function_name = cursor.spelling
                # if function_name == 'call_console_drivers':
                #     print('111')
                if (function_code := get_function_code(cursor, source_code)) is not None:
                    functions[function_name] = function_code
    for child in cursor.get_children():
        functions.update(find_all_functions(child, source_code))
    return functions


def get_defined_macros(file_path, code):
    index = clang.cindex.Index.create()
    tu = index.parse(file_path, args=['-dM'], unsaved_files=[(file_path, code)])

    macro_definitions = set()  # 存储宏定义列表

    # 获取所有的宏定义
    for cursor in tu.cursor.get_children():
        if cursor.kind == clang.cindex.CursorKind.MACRO_DEFINITION:
            macro_name = cursor.spelling
            macro_definitions.add(macro_name)

    return macro_definitions


def parse_c_file(file_path):
    """
    解析 C 语言代码文件
    :param file_path: C 语言文件的路径
    :return: 解析后的 AST 根节点游标对象
    """

    with open(file_path, 'r') as file:
        code = file.read()

    # 创建虚拟文件
    virtual_file = [(file_path, code)]

    index = clang.cindex.Index.create()

    # defined_macros = get_defined_macros(file_path, code)
    # args = ['-std=c11'] + ['-D{}'.format(mac) for mac in defined_macros]

    # 解析 C 语言文件
    tu = index.parse(file_path, args=['std=c11'], unsaved_files=virtual_file)

    if not tu:
        print("无法解析文件")
        return None

    functions = find_all_functions(cursor=tu.cursor, source_code=code)

    return functions


def add_new_code(old_code, new_code):
    old_code = old_code + '\n' + '\n' + new_code
    return old_code


def extract_simplified_code_from_file(ast_with_func, global_code, functions):
    generated_code = ""
    for code in global_code:
        generated_code = add_new_code(old_code=generated_code, new_code=code)
    for function in functions:
        function_code = find_function_body(ast_with_func, function_name=function)
        # 说明这个文件里没有这个函数，这个函数来源于外部
        # 该语句所存在的函数代码已经获取，包括了该外部函数调用，因此可以忽略
        if function_code is None:
            continue
        generated_code = add_new_code(old_code=generated_code, new_code=function_code)
    return generated_code


def simplify_code_from_diff(origin_path, patched_path, diff_path):
    diff_file = read_files_by_lines(diff_path)

    # 解析 diff 文件
    diff_result = parse_diff_file(diff_file)
    deleted_function = diff_result['deleted_function']
    added_function = diff_result['added_function']
    global_added_code = diff_result['global_added_code']
    global_deleted_code = diff_result['global_deleted_code']

    # 解析 C 语言文件为 AST
    origin_ast_with_func = parse_c_file(origin_path)
    patched_ast_with_func = parse_c_file(patched_path)

    # 获取简化后的文件代码
    simplified_origin_code = extract_simplified_code_from_file(ast_with_func=origin_ast_with_func,
                                                               global_code=global_deleted_code,
                                                               functions=deleted_function)
    simplified_target_code = extract_simplified_code_from_file(ast_with_func=patched_ast_with_func,
                                                               global_code=global_added_code,
                                                               functions=added_function)

    return {
        'origin_code': simplified_origin_code,
        'target_code': simplified_target_code
    }
