# 定义输出为utf8
# -*- coding: utf-8 -*-

import json
import requests
import re
import regex
from IR_relate_code import *

import logging
import os
from concurrent.futures import ThreadPoolExecutor
import threading




def process_single_query(key, value, claim, Video_information, QA_CONTEXTS, question, output_file_path):
    logging.info(f"Processing query key: {key}, value: {value}")

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

    # 使用ThreadPoolExecutor并发处理查询
    # 开一个多线程处理问题的查询过程
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for key, value in queries.items():
            futures.append(executor.submit(process_single_query, key, value, claim, Video_information, QA_CONTEXTS, question, output_file_path))
        
        # 等待所有线程完成
        for future in futures:
            future.result()

    # 获取当前输出文件路径的目录部分
    now_folder_path = os.path.dirname(output_file_path)

    # 处理JSON文件，将结果合并并保存到输出文件路径
    process_json_files(now_folder_path, output_file_path)

    # Prompts for Question Answer based on the Evidence
    # 处理声明并生成回答，将结果保存到输出文件路径
    process_claim_and_generate_answer(claim, Video_information, QA_CONTEXTS, question, output_file_path)




# output_file_path = "/workspaces/llmfnd/test/IR_result.json"



# Claim = "A video showing a shark swimming on a flooded highway during Hurricane Ian in Florida."
# Video_information = {
#     "Video_headline": "a shark swimming on a flooded highway",
#     "Video_transcript": "",
#     "Video_description_on_platform": "This video analyzes and debunks the photo of a shark allegedly swimming on a flooded highway.",
#     "Video_platform": "youtube",
#     "Video_date": "2023_08_07",
#     "Video_description_from_descriptor": "A video, including the shark on a flooded highway."
# }
# QA_CONTEXTS = {}

# Question = "Can the source and background of the video showing a shark swimming on a flooded highway during Hurricane Ian in Florida be verified to validate the claim?"


# information_retriever_complete(Claim, Video_information, QA_CONTEXTS, Question, output_file_path)