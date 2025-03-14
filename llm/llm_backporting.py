import openai
import os
from code_verify import calculate_similarity,standardize_code
from data_process import data_process
from fine_tuning import load_dataset_from_directory

# 设置你的 OpenAI API 密钥
API_SECRET_KEY = "sk-zk267352d807f7d1a01483983343a67214267ce9292da282"
BASE_URL = "https://api.zhizengzeng.com/v1/"
openai.api_key = API_SECRET_KEY
openai.api_base = BASE_URL


# type1 1条 type2 235条 type3 9条，type4 30条，type5 75条 共350条
# 各自50条， type2 31条 type3 2条， type4 5条， type5 12条
def generate_test_data(start_idx=0, end_idx=50):
    data_directory = os.path.join(".", "data/testing_data")
    data_process(base_directory=data_directory, train=False, start_idx=start_idx, end_idx=end_idx)


def load_test_data(num=60):
    data_directory = os.path.join(".", "data/testing_data")
    testing_data = load_dataset_from_directory(data_dir=data_directory,num=num)
    return testing_data


def generate_code_samples_from_dataset(testing_data):
    code_samples = []
    for entry in testing_data:
        for v in entry.values():
            code_samples.append(v)
    return code_samples


def remove_redundant_text(code):
    # 查找开头 '''c 的位置
    start_index = code.find("```c")
    if start_index != -1:
        # 把'''c及之前截取掉
        code = code[start_index + 4:]
    # 查找结尾 ''' 的位置
    end_index = code.rfind("```")
    if end_index != -1:
        # 把'''及之后截取掉
        code = code[:end_index]
    code = code.strip()
    return code


def generate_prompt(original_code, fixed_code, latest_code):
    """
    生成用于测试的提示语
    :param original_code: 原始代码（A 版本）
    :param fixed_code: 修复代码（B 版本）
    :param latest_code: 最新代码（C 版本）
    :return: 生成的提示语
    """
    prompt = (
        f"原始代码 (A 版本) 存在漏洞：\n{standardize_code(original_code)}\n"
        f"修复代码 (B 版本) 修复了该漏洞：\n{standardize_code(fixed_code)}\n"
        f"最新代码 (C 版本) 是：\n{standardize_code(latest_code)}\n"
        "请将 A 版本到 B 版本的补丁应用到 C 版本，并返回生成后的代码。请仅生成代码，不需要任何文字提示。"
    )
    return prompt


def query_gpt3_5(query):
    try:
        response = openai.ChatCompletion.create(
            # model="gpt-3.5-turbo-SBOM_LLM",  # 使用名为 SBOM_LLM 的微调模型
            model="ft:gpt-3.5-turbo-0125:note-vibes:sbom-llm:B9rALFx1",  # 使用微调模型
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"查询 GPT-3.5 时出现错误: {e}")
        return None


def testing(start_idx, end_idx):
    testing_data = load_test_data()
    valid_count = 0
    count_by_type = {}
    valid_by_type = {}
    testing_data = testing_data[start_idx:end_idx]
    for i, entry in enumerate(testing_data):
        original_code = entry["original_code"]
        fixed_code = entry["fixed_code"]
        target_code = entry["target_code"]
        latest_code = entry["latest_code"]
        patch_type = entry["patch_type"]

        if patch_type not in count_by_type:
            count_by_type[patch_type] = 1
        else:
            count_by_type[patch_type] += 1

        prompt = generate_prompt(original_code, fixed_code, target_code)
        generated_code = query_gpt3_5(prompt)

        generated_code = remove_redundant_text(generated_code)
        if generated_code:
            print(f"测试数据条目 {start_idx + i} 的结果:")
            print(f"生成的新代码:\n{generated_code}")
        else:
            print(f"测试数据条目 {start_idx + i} 未能成功生成结果，请检查。")
        # similarity = code_similarity(generated_code, latest_code)
        similarity = calculate_similarity(generated_code, standardize_code(latest_code))
        print(f'第{start_idx + i}行数据的相似度为{similarity}')
        if similarity > 0.9:
            valid_count += 1
            if patch_type not in valid_by_type:
                valid_by_type[patch_type] = 1
            else:
                valid_by_type[patch_type] += 1

    print(f"满足生成阈值的代码共{valid_count}个, 成功率为{float(valid_count) / 50}。")
    for k, v in count_by_type.items():
        type_count = v
        if k in valid_by_type:
            valid_count = valid_by_type[k]
        else:
            valid_count = 0
        print(f"Patch type为{k}的数据共{type_count}条，成功{valid_count}条，修复成功率为{float(valid_count) / float(type_count)}。")


if __name__ == '__main__':
    # generate_test_data(start_idx=9, end_idx=10)
    testing(45, 46)