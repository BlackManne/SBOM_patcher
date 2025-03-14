import openai
import time
import json
import os
from Utils.file_utils import read_files
from data_process import data_process

# 设置你的 OpenAI API 密钥
API_SECRET_KEY = "sk-zk267352d807f7d1a01483983343a67214267ce9292da282"
BASE_URL = "https://api.zhizengzeng.com/v1/"
openai.api_key = API_SECRET_KEY
openai.api_base = BASE_URL


def generate_train_data():
    data_directory = os.path.join(".", "data/training_data")
    data_process(base_directory=data_directory, train=True)


def load_train_data(num):
    data_directory = os.path.join(".", "data/training_data")
    training_data = load_dataset_from_directory(data_dir=data_directory, num=num)
    return training_data


def modify_code_prompt(code):
    return "'''c" + '\n' + code + "'''"


def load_dataset_from_directory(data_dir, num=50):
    """
    从目录中加载训练数据，假设每个条目包含三个文件：original_code.txt, fixed_code.txt, latest_code.txt
    :param num:加载的数据条数
    :param data_dir: 存储训练数据文件的目录路径
    :return: 训练数据列表
    """
    training_data = []
    for i in range(0, num):  # 假设共有 50 组数据
        original_code_path = f"{data_dir}/entry_{i}/newpa.c"
        fixed_code_path = f"{data_dir}/entry_{i}/newpb.c"
        target_code_path = f"{data_dir}/entry_{i}/newpc.c"
        latest_code_path = f"{data_dir}/entry_{i}/newpe.c"
        patch_type_path = f"{data_dir}/entry_{i}/type.txt"

        original_code = read_files(original_code_path)
        fixed_code = read_files(fixed_code_path)
        target_code = read_files(target_code_path)
        latest_code = read_files(latest_code_path)
        patch_type = int(read_files(patch_type_path))

        if original_code and fixed_code and target_code and latest_code:
            entry = {
                "original_code": original_code,
                "fixed_code": fixed_code,
                "target_code": target_code,
                "latest_code": latest_code,
                "patch_type": patch_type
            }
            training_data.append(entry)
            print(f"加载数据条目 {i} 成功。")
        else:
            print(f"数据条目 {i} 加载不完整，请检查文件。")
    return training_data


def upload_training_file(file_path):
    """
    此函数用于将训练文件上传到 OpenAI 平台，并返回文件的 ID
    :param file_path: 训练文件的本地路径
    :return: 上传成功的文件的 ID
    """
    try:
        with open(file_path, "rb") as file:
            response = openai.File.create(
                file=file,
                purpose="fine-tune"
            )
        return response["id"]
    except Exception as e:
        print(f"文件上传时出现错误: {e}")
        return None


def check_file_status(file_id):
    """
    此函数用于检查文件的处理状态
    :param file_id: 上传文件的 ID
    :return: 文件的处理状态
    """
    try:
        response = openai.File.retrieve(file_id)
        return response["status"]
    except Exception as e:
        print(f"检查文件状态时出现错误: {e}")
        return None


def wait_for_file_processing(file_id):
    """
    此函数会等待文件处理完成，会持续检查文件状态，直到文件状态为 'processed'
    :param file_id: 上传文件的 ID
    """
    while True:
        status = check_file_status(file_id)
        if status == "processed":
            print("文件已处理完成，可以开始微调。")
            break
        elif status == "error":
            print("文件处理出现错误，请检查。")
            break
        else:
            print(f"文件正在处理中，当前状态: {status}，等待 10 秒后再次检查。")
            time.sleep(10)


def fine_tune_gpt3_5(training_file_id):
    """
    此函数用于调用 GPT-3.5 的微调接口进行模型微调
    :param training_file_id: 训练文件的 ID
    :return: 微调任务的响应结果
    """
    try:
        # 使用新版Fine-tuning Jobs API
        response = openai.FineTuningJob.create(
            training_file=training_file_id,
            model="gpt-3.5-turbo",  # 使用支持微调的模型版本
            hyperparameters={
                "n_epochs": 4,
                "batch_size": 4,
                "learning_rate_multiplier": 0.1
            },
            suffix="SBOM_LLM"
        )
        return response
    except Exception as e:
        print(f"微调过程中出现错误: {e}")
        return None


def check_fine_tune_status(fine_tune_id):
    """
    此函数用于检查微调任务的状态
    :param fine_tune_id: 微调任务的 ID
    :return: 微调任务的状态
    """
    try:
        response = openai.FineTuningJob.retrieve(fine_tune_id)
        return response["status"]
    except Exception as e:
        print(f"检查微调任务状态时出现错误: {e}")
        return None


def wait_for_fine_tuning(fine_tune_id):
    """
    此函数会等待微调任务完成，会持续检查微调任务状态，直到任务状态为 'succeeded' 或 'failed'
    :param fine_tune_id: 微调任务的 ID
    """
    while True:
        status = check_fine_tune_status(fine_tune_id)
        if status == "succeeded":
            print("微调任务已成功完成。")
            break
        elif status == "failed":
            print("微调任务失败，请检查。")
            break
        else:
            print(f"微调任务正在进行中，当前状态: {status}，等待 10 秒后再次检查。")
            time.sleep(10)


def generate_prompt(original_code, fixed_code, target_code):
    """
    生成用于微调的提示语
    :param original_code: 原始代码（A 版本）
    :param fixed_code: 修复代码（B 版本）
    :param target_code: 最新代码（C 版本）
    :return: 生成的提示语
    """
    prompt = (
        f"原始代码 (A 版本) 存在漏洞：\n{original_code}\n"
        f"修复代码 (B 版本) 修复了该漏洞：\n{fixed_code}\n"
        f"最新代码 (C 版本) 是：\n{target_code}\n"
        "请将 A 版本到 B 版本的补丁应用到 C 版本。"
    )
    return prompt


def generate_completion(latest_code):
    completion = (
        f"将补丁应用到最新代码 (C版本) 后的结果：\n{latest_code}\n"
    )
    return completion


def generate_fine_tune_data(prompt, completion):
    res = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": completion}
        ]
    }
    return res


def training(num=50):
    training_data = load_train_data(num=num)

    # 将训练数据转换为所需的 JSONL 格式，每条数据由 prompt 和 completion 组成
    training_data_jsonl = []
    for entry in training_data:
        original_code = modify_code_prompt(entry["original_code"])
        fixed_code = modify_code_prompt(entry["fixed_code"])
        target_code = modify_code_prompt(entry["target_code"])
        latest_code = modify_code_prompt(entry["latest_code"])
        prompt = generate_prompt(original_code, fixed_code, target_code)
        completion = generate_completion(latest_code)
        training_data_jsonl.append(json.dumps(generate_fine_tune_data(prompt=prompt, completion=completion)))

    # 将转换后的数据保存到一个临时的 JSONL 文件中
    with open("temp_training_data.jsonl", "w") as file:
        file.write("\n".join(training_data_jsonl))

    # 上传训练文件
    training_file_id = upload_training_file("temp_training_data.jsonl")
    if training_file_id:
        wait_for_file_processing(training_file_id)
        fine_tune_response = fine_tune_gpt3_5(training_file_id)
        if fine_tune_response:
            fine_tune_id = fine_tune_response["id"]
            wait_for_fine_tuning(fine_tune_id)


if __name__ == "__main__":
    training(50)
