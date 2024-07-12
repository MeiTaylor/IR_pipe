# 定义输出为utf8
# -*- coding: utf-8 -*-

import json
import requests
import re
import regex
from IR_relate_code import *

import logging
import os



def information_retriever_complete(claim, Video_information, QA_CONTEXTS, question, output_file_path):
    # 尝试读取 JSON 文件
    try:
        with open(output_file_path, 'r', encoding='utf-8') as file:
            try:
                full_data = json.load(file)
            except json.JSONDecodeError:
                full_data = {}  # 如果文件为空或无效，则初始化为空的 JSON 结构
    except FileNotFoundError:
        full_data = {}  # 如果文件不存在，则初始化为空的 JSON 结构

    # 更新数据
    full_data["Question"] = question

    # 写入更新后的数据到文件
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(full_data, f, indent=4, ensure_ascii=False)

    # Prompts for Information Retrieving Verifier
    result = check_online_search_needed(claim, Video_information, QA_CONTEXTS, question, output_file_path)

    logging.info(f"Online information retrieving required : {result}")

    query_complete_json_answer = generate_and_format_queries(claim, Video_information, QA_CONTEXTS, question, output_file_path)

    # 从生成的JSON结果中提取生成的Queries
    queries = query_complete_json_answer.get('Queries', {})

    # 遍历所有生成的查询
    for key, value in queries.items():
        # 记录每个查询的键和值到日志
        logging.info(f"{key}: {value}")

        # 获取输出文件路径的目录部分
        prefix = os.path.dirname(output_file_path)

        # 构建单个查询的文件路径
        single_query_path = os.path.join(prefix, f"{key}.json")

        # 处理查询并计算网站的质量得分，将结果保存到output_file_path
        process_query_and_quality_score_value(value, claim, Video_information, QA_CONTEXTS, question, single_query_path)
        
        # 更新后的查询文件路径
        updated_single_query_path = single_query_path.replace(".json", "_updated.json")

        # 处理证据的新鲜度和相关性，并将结果保存到更新后的查询文件路径
        process_evidence_and_Newness_Relevance(key, value, claim, Video_information, QA_CONTEXTS, question, updated_single_query_path)

    # 获取当前输出文件路径的目录部分
    now_folder_path = os.path.dirname(output_file_path)

    # 处理JSON文件，将结果合并并保存到输出文件路径
    # 也就是根据之前的Query的相关json文件，修改output_file_path的json文件
    process_json_files(now_folder_path, output_file_path)

    # Prompts for Question Answer based on the Evidence
    # 处理声明并生成回答，将结果保存到输出文件路径
    process_claim_and_generate_answer(claim, Video_information, QA_CONTEXTS, question, output_file_path)

# 使用该函数
# process_and_generate_answer(claim, Video_information, QA_CONTEXTS, question, output_file_path)
