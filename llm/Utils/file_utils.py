import base64
import os
import chardet


def decode_base64_from_file(base64_string):
    try:
        decoded_bytes = base64.b64decode(base64_string)
        # 猜测字节数据的编码
        encoding = chardet.detect(decoded_bytes)['encoding']
        decoded_string = decoded_bytes.decode(encoding)
        return decoded_string
    except Exception as e:
        print(f"解码时出现错误: {e}")
        return None


def save_string_to_txt(path, string):
    if string is not None:
        try:
            with open(path, 'w') as file:
                file.write(string)
                print(f"成功存储到文件{path}")
        except Exception as e:
            print(f"存储到文件 {path} 时出错: {e}")


def save_codes_to_files(folder_path, **kwargs):
    try:
        # 创建新文件夹
        os.makedirs(folder_path, exist_ok=True)
    except Exception as e:
        print(f"创建文件夹 {folder_path} 时出错: {e}")
        return
    for key, value in kwargs.items():
        split_keys = key.split("_")
        # key的前半部分标识文件名,后半部分表示文件类型
        file_path = os.path.join(folder_path, f'{split_keys[0]}.{split_keys[1]}')
        save_string_to_txt(file_path, value)


def read_files_by_lines(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return lines


def read_files(file_path):
    """
    从文件中加载代码
    :param file_path: 代码文件的路径
    :return: 代码字符串
    """
    try:
        with open(file_path, 'r') as file:
            code = file.read()
        return code
    except Exception as e:
        print(f"加载代码文件时出现错误: {e}")
        return None