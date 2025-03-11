import os
import openai
import requests
import time
import json
import time

API_SECRET_KEY = "sk-zk267352d807f7d1a01483983343a67214267ce9292da282";
BASE_URL = "https://api.zhizengzeng.com/v1/"


# chat
def chat_completions2(query):
    openai.api_key = API_SECRET_KEY
    openai.api_base = BASE_URL
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": query}
        ]
    )
    print(resp)
    print(resp.choices[0].message.content)


if __name__ == '__main__':
    chat_completions2("圆周率的前10位");
