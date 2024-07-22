# 定义输出为utf8
# -*- coding: utf-8 -*-

import json
import requests
import re
import regex
from IR2_relate_code import *

import logging
import os
from concurrent.futures import ThreadPoolExecutor
import threading


# logging.basicConfig(filename='test_IR.log', level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')




def information_retriever_complete(claim, Video_information, QA_CONTEXTS, question, output_file_path):
    logging.warning("-----------------------------------------")
    logging.warning("--------- INFORMATION RETRIEVER ---------")
    logging.warning("-----------------------------------------")


    
    
    def process_query(key, value, claim, Video_information, QA_CONTEXTS, question, output_file_path):
        logging.info(f"Processing query key: {key}, value: {value}")
        now_useful = LLM_online_fact_check(key, value, output_file_path)
        return now_useful





    attempt_count = 0  # 初始化尝试计数器

    while attempt_count < 5:
        attempt_count += 1

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

        search_and_queries = check_online_search_and_generate_queries(claim, Video_information, QA_CONTEXTS, question, output_file_path)



        # 检查是否需要在线搜索
        if search_and_queries['Prediction']['need_online_search'] == "No":
            logging.info("No online search needed.")
            process_claim_and_generate_answer_without_gs(claim, Video_information, question, output_file_path)
            
            return  # 直接跳出函数

        else:
            logging.info("Online search needed.")
            queries = search_and_queries['Prediction']['Queries']

            # 使用 ThreadPoolExecutor 并发处理查询
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = []
                for key, value in queries.items():
                    futures.append(executor.submit(process_query, key, value, claim, Video_information, QA_CONTEXTS, question, output_file_path))
                
                # 等待所有线程完成
                all_useful = True
                for future in futures:
                    if not future.result():
                        all_useful = False
                        break

            logging.info("两个线程均执行完毕")


        if not all_useful:
            continue

        is_useful = check_online_LLM_answer_useful(claim, Video_information, QA_CONTEXTS, question, output_file_path)

        if is_useful and all_useful:
            break
        else:
            logging.info("Some queries failed, retrying...")

            # 清空 output_file_path 文件内容
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.truncate(0)
            logging.info(f"Cleared file contents: {output_file_path}")



    # Prompts for Question Answer based on the Evidence
    # 处理声明并生成回答，将结果保存到输出文件路径
    process_claim_and_generate_answer_only_online_LLM(claim, Video_information, QA_CONTEXTS, question, output_file_path)




# output_file_path = "/workspaces/IR_pipe/IR/IR_result.json"



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

# Question = "Is there verifiable documentation or eyewitness testimony corroborating the presence of a shark on the flooded highway during Hurricane Ian in Florida?"


# information_retriever_complete(Claim, Video_information, QA_CONTEXTS, Question, output_file_path)


