import os

from cryptography.fernet import Fernet


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class TokenEncryptor:
    def __init__(self):
        self.key_file = os.path.join(find_project_root(__file__), 'key.key')  # 密钥文件路径
        self.token_file = os.path.join(find_project_root(__file__), 'github_token')  # 加密后token文件路径
        self.key = self.load_key()
        self.cipher_suite = Fernet(self.key)

    def generate_and_save_key(self):
        self.key = Fernet.generate_key()
        with open(self.key_file, 'wb') as key_file:
            key_file.write(self.key)

    def load_key(self):
        if not os.path.exists(self.key_file):
            self.generate_and_save_key()
        with open(self.key_file, 'rb') as key_file:
            return key_file.read()

    def encrypt_token(self, token):
        token_bytes = token.encode()
        encrypted_token = self.cipher_suite.encrypt(token_bytes)
        self.save_encrypted_token_to_file(encrypted_token)
        return encrypted_token

    def save_encrypted_token_to_file(self, encrypted_token):
        with open(self.token_file, 'wb') as file:
            file.write(encrypted_token)


@singleton
class TokenDecryptor:
    def __init__(self):
        self.key_file = os.path.join(find_project_root(__file__), 'key.key')  # 密钥文件路径
        self.token_file = os.path.join(find_project_root(__file__), 'github_token')  # 加密后token文件路径
        self.key = self.load_key()
        self.cipher_suite = Fernet(self.key)

    def load_key(self):
        with open(self.key_file, 'rb') as key_file:
            return key_file.read()

    def decrypt_token(self):
        with open(self.token_file, 'rb') as file:
            encrypted_token = file.read()
            decrypted_token = self.cipher_suite.decrypt(encrypted_token).decode()
            return decrypted_token


def find_project_root(start_path, root_marker='.git'):
    """
    从start_path开始向上遍历目录，直到找到包含root_marker的目录。
    """
    current_path = start_path
    while True:
        parent_path = os.path.abspath(os.path.join(current_path, os.pardir))
        if os.path.samefile(current_path, parent_path):
            # 达到了文件系统的根目录
            return None
        if os.path.exists(os.path.join(current_path, root_marker)):
            return current_path
        current_path = parent_path


# if __name__ == "__main__":
#     token = "请在这里输入你使用的token"
#     encryptor = TokenEncryptor()
#     encryptor.encrypt_token(token)
#     decryptor = TokenDecryptor()
#     github_token = decryptor.decrypt_token()
#     print(github_token)
