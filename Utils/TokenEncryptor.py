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
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        self.directory = 'C:\\BlackMann\\MASTER\\PMX\\coding\\SBOM_patcher\\crypto\\'  # 设置绝对路径

    def encrypt_token(self, token):
        token_bytes = token.encode()
        encrypted_token = self.cipher_suite.encrypt(token_bytes)
        return encrypted_token

    def save_encrypted_token_to_file(self, encrypted_token):
        filename = 'github_token'
        filepath = os.path.join(self.directory, filename)
        with open(filepath, 'wb') as file:
            file.write(encrypted_token)

    def decrypt_token_from_file(self):
        filename = 'github_token'
        filepath = os.path.join(self.directory, filename)
        with open(filepath, 'rb') as file:
            byte_data = file.read()
            decrypted_token = self.cipher_suite.decrypt(byte_data).decode()
            print(decrypted_token)
            return decrypted_token