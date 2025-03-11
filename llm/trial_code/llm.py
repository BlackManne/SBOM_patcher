from openai import OpenAI

client = OpenAI(
    base_url='https://api.openai-proxy.org/v1',
    api_key='sk-DCop5RvCupZY7tJ88m8WWPEgkl51x7bGRjUQ0Mihve4UFUey',
)

with open("base.py", "r") as base_file:
    base_code = base_file.read()

with open("base.py", "r") as patch_file:
    patched_code = patch_file.read()

with open("base.py", "r") as new_file:
    new_code = new_file.read()

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "请帮我合并一下以下两个代码：" + base_code + "\n" + patched_code + "\n" + new_code
        }
    ],
    model="gpt-3.5-turbo",
)

print(chat_completion.choices[0].message.content)

# file_completion = client.chat.completions.create(
#     messages=[
#         {
#             "role": "user",
#             "content": content,
#         }
#     ],
#     model="gpt-3.5-turbo",
# )
# print(file_completion.choices[0].message.content)
