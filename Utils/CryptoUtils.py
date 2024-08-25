import os

import keyring

from Utils.TokenEncryptor import singleton


# 服务名和用户名，对于GitHub，通常是固定的

@singleton
class KeyRingEncryptor:

    def __init__(self):
        self.github_service = 'github-token'
        self.github_user = 'SBOM'
        self.directory = 'C:\\BlackMann\\MASTER\\PMX\\coding\\SBOM_patcher\\crypto\\'
        self.set_github_token(self.read_token_from_file())

    # 设置GitHub token
    def set_github_token(self, token):
        keyring.set_password(self.github_service, self.github_user, self.read_token_from_file())

    # 获取GitHub token
    def get_github_token(self):
        return keyring.get_password(self.github_service, self.github_user)

    def read_token_from_file(self):
        filename = 'raw_token'
        filepath = os.path.join(self.directory, filename)
        with open(filepath, 'r') as file:
            data = file.read()
            return data


# if __name__ == "__main__":
#     print(KeyRingEncryptor().get_github_token())