import os
from Utils.github_utils import get_commit_info_for_llm, get_file_content_for_llm
from Utils.file_utils import save_codes_to_files, decode_base64_from_file
from simplify_code import simplify_code_from_diff

import pandas as pd
import warnings


def get_rows_from_excel(file_path, train=True):
    """
    根据Patch Type比例从Excel文件采样数据

    参数：
    file_path (str): Excel文件路径
    train (bool): True生成训练集（前向采样），False生成测试集（后向采样）

    返回：
    pd.DataFrame: 采样后的数据集
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)

        # 检查必要列是否存在
        if 'Patch Type' not in df.columns:
            raise ValueError("Excel文件中缺少'Patch Type'列")

        # 定义各类型采样数量
        type_quota = {
            2: 31,
            3: 2,
            4: 5,
            5: 12
        }

        # # 给测试集使用的，多找一些数据
        # type_quota = {
        #     2: 37,
        #     3: 2,
        #     4: 6,
        #     5: 15
        # }

        sampled_dfs = []

        # 遍历每个类型进行采样
        for patch_type, quota in type_quota.items():
            # 过滤当前类型数据
            type_df = df[df['Patch Type'] == patch_type]

            if type_df.empty:
                warnings.warn(f"警告：未找到Patch Type={patch_type}的数据")
                continue

            # 确定实际采样数量
            actual_quota = min(quota, len(type_df))

            if actual_quota < quota:
                warnings.warn(f"警告：Patch Type={patch_type}数据不足（需要{quota}条，实际{len(type_df)}条）")

            # 根据采样方向选择数据
            if train:  # 训练集：从前往后取
                sampled = type_df.head(actual_quota)
            else:  # 测试集：从后往前取
                sampled = type_df.tail(actual_quota)
                sampled = sampled.iloc[::-1]  # 保持原始顺序，只是采样方向变化

            sampled_dfs.append(sampled)

        if not sampled_dfs:
            raise ValueError("没有找到符合条件的数据")

        # 合并结果并重置索引
        result_df = pd.concat(sampled_dfs).reset_index(drop=True)

        print(f'成功从{len(result_df)}条数据中采样{len(result_df)}条')
        return result_df

    except FileNotFoundError:
        print(f"错误：文件未找到 - {file_path}")
        return None
    except Exception as e:
        print(f"发生错误：{str(e)}")
        return None


def get_trial_rows_from_excel(file_path, num_rows=50):
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        # 获取数据的行数
        total_rows = len(df)
        # 确保选取的行数不超过总数据行数
        num_rows = min(num_rows, total_rows)

        # # 生成随机行索引
        # random_indices = random.sample(range(total_rows), num_rows)
        #
        # # 选取随机行数据
        # random_rows = df.iloc[random_indices]

        # 选取前num_rows行数据
        first_rows = df.head(num_rows)
        print('从excel中读取数据成功！')
        return first_rows
    except FileNotFoundError:
        print(f"文件未找到: {file_path}")
        return None


def get_and_parse_data(rows, base_directory):
    if rows is None:
        print("没有传入任何数据")
        return None
    # 循环遍历每一行并获取需要的每一列数据
    for index, row in rows.iterrows():
        # 目标是将A->B的补丁移植到C->E上，因此需要获取四个文件的内容，以及A->B和C->E的patch
        pa_cid = row.get('Commit - Pa')
        pb_cid = row.get('Commit - Pb')
        pc_cid = row.get('Commit - Pc')
        pe_cid = row.get('Commit - Pe')
        ab_file_name = row.get('Program AB')
        ce_file_name = row.get('Program CE')
        patch_type = str(row.get('Patch Type'))
        # 文件名从.o换成.c
        ab_file_name = str.replace(ab_file_name, '.o', '.c')
        ce_file_name = str.replace(ce_file_name, '.o', '.c')
        print(f"第{index}行数据的pa、pb、的commitId分别为：{pa_cid}, {pb_cid}, 文件名称为：{ab_file_name}。")
        print(f"第{index}行数据的pc、pe、的commitId分别为：{pc_cid}, {pe_cid}, 文件名称为：{ce_file_name}。")

        # 分别获取四个文件的内容
        pa_base64_file = get_file_content_for_llm(pa_cid, ab_file_name)
        pb_base64_file = get_file_content_for_llm(pb_cid, ab_file_name)
        pc_base64_file = get_file_content_for_llm(pc_cid, ce_file_name)
        pe_base64_file = get_file_content_for_llm(pe_cid, ce_file_name)

        # 分别获取两个patch
        origin_patch_obj = get_patch(pb_cid, ab_file_name)
        ab_patch = origin_patch_obj['patch']
        patch_message = origin_patch_obj['message']
        ce_patch = get_patch(pe_cid, ce_file_name)['patch']

        data_directory = os.path.join(base_directory, f'entry_{index}')

        # 将代码文件存储到c文件中,patch文件存储到txt文件中
        save_codes_to_files(data_directory, pa_c=decode_base64_from_file(pa_base64_file),
                            pb_c=decode_base64_from_file(pb_base64_file),
                            pc_c=decode_base64_from_file(pc_base64_file), pe_c=decode_base64_from_file(pe_base64_file),
                            abpatch_txt=ab_patch, cepatch_txt=ce_patch)
        # 将patch message文件存储到txt文件中
        save_codes_to_files(data_directory, description_txt=patch_message)
        # 将类型数据存储到txt文件中
        save_codes_to_files(data_directory, type_txt=patch_type)
        print(f'成功解析并存储第{index}行数据')

        # 然后对文件做精简
        ab_simplifed_code = simplify_code_from_diff(origin_path=os.path.join(data_directory, 'pa.c'),
                                                    patched_path=os.path.join(data_directory, 'pb.c'),
                                                    diff_path=os.path.join(data_directory, 'abpatch.txt'))
        s_pa = ab_simplifed_code['origin_code']
        s_pb = ab_simplifed_code['target_code']
        ce_simplifed_code = simplify_code_from_diff(origin_path=os.path.join(data_directory, 'pc.c'),
                                                    patched_path=os.path.join(data_directory, 'pe.c'),
                                                    diff_path=os.path.join(data_directory, 'cepatch.txt'))

        s_pc = ce_simplifed_code['origin_code']
        s_pe = ce_simplifed_code['target_code']
        save_codes_to_files(data_directory, newpa_c=s_pa, newpb_c=s_pb, newpc_c=s_pc, newpe_c=s_pe)
        print(f'成功简化并存储第{index}行数据')


def get_patch(commit_id, file_name):
    commit_info = get_commit_info_for_llm(commit_id)
    commit_object = {}
    if commit_info is not None:
        commit_object['message'] = commit_info['commit']['message'].strip()
        # 单次commit可能修改了很多个文件，只有一个文件和patch对应
        for file in commit_info['files']:
            if file['filename'] != file_name:
                continue
            else:
                commit_object['patch'] = file['patch']
                break
    return commit_object


def data_process(base_directory, train, start_idx=0, end_idx=50):
    file_path = 'Main-data-set.xlsx'
    rows = get_rows_from_excel(file_path, train=train)
    rows = rows.iloc[start_idx:end_idx]
    get_and_parse_data(rows, base_directory)

