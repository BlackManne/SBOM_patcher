from cryptography.fernet import Fernet

# 生成一个密钥
key = Fernet.generate_key()
cipher_suite = Fernet(key)

filename = 'github_token'
directory = '../crypto'  # 数据保存的目录
filepath = directory + '/' + filename


def crypt_token():
    # 要加密的 token
    token = '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'
    token_bytes = token.encode()

    # 加密 token
    encrypted_token = cipher_suite.encrypt(token_bytes)
    print("加密后的 token:", encrypted_token)

    with open(filepath, 'wb') as file:
        file.write(encrypted_token)  # 将内容写入文件


def decrypt_token():
    with open(filepath, 'rb') as file:
        byte_data = file.read()
        # 解密 token
        decrypted_token = cipher_suite.decrypt(byte_data).decode()
        print("解密后的 token:", decrypted_token)
        return decrypted_token

