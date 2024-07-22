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


# logging.basicConfig(filename='test_IR.log', level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')




def information_retriever_complete(claim, Video_information, QA_CONTEXTS, question, output_file_path):
    
    
    logging.warning("\n" * 5)
    logging.warning("-----------------------------------------")
    logging.warning("--------- Information Retriever ---------")
    logging.warning("-----------------------------------------")
    
    
    def process_query(key, value, claim, Video_information, QA_CONTEXTS, question, output_file_path):
        logging.info(f"Processing query key: {key}, value: {value}")

        # 获取输出文件路径的目录部分
        prefix = os.path.dirname(output_file_path)

        # 构建单个查询的文件路径
        single_query_path = os.path.join(prefix, f"{key}.json")


        # 处理查询并计算网站的质量得分，将结果保存到output_file_path
        process_query_and_quality_score_value(value, claim, Video_information, QA_CONTEXTS, question, single_query_path)
        
        # 更新后的查询文件路径
        updated_single_query_path = single_query_path.replace(".json", "_updated.json")

        process_evidence_and_Newness_Relevance(key, value, claim, Video_information, QA_CONTEXTS, question, updated_single_query_path)







    attempt_count = 0  # 初始化尝试计数器

    while attempt_count < 3:

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


        attempt_count += 1
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
                for future in futures:
                    future.result()

            logging.info("两个线程均执行完毕")

            # 获取当前输出文件路径的目录部分
            now_folder_path = os.path.dirname(output_file_path)

            # 处理JSON文件，将结果合并并保存到输出文件路径
            process_json_files(now_folder_path, output_file_path)


            now_evidences_useful = select_useful_evidence(claim, Video_information, QA_CONTEXTS, question, output_file_path)

            if now_evidences_useful:
                break  # 如果所有查询都成功处理，则退出循环
            else:
                logging.info("Some queries failed, retrying...")

                # 删除指定文件
                for key in queries.keys():
                    prefix = os.path.dirname(output_file_path)
                    single_query_path = os.path.join(prefix, f"{key}.json")
                    updated_single_query_path = single_query_path.replace(".json", "_updated.json")

                    if os.path.exists(single_query_path):
                        os.remove(single_query_path)
                        logging.info(f"Deleted file: {single_query_path}")
                        
                    if os.path.exists(updated_single_query_path):
                        os.remove(updated_single_query_path)
                        logging.info(f"Deleted file: {updated_single_query_path}")

                # 清空 output_file_path 文件内容
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.truncate(0)
                logging.info(f"Cleared file contents: {output_file_path}")




    # Prompts for Question Answer based on the Evidence
    # 处理声明并生成回答，将结果保存到输出文件路径
    process_claim_and_generate_answer(claim, Video_information, QA_CONTEXTS, question, output_file_path)




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


# process_and_retrieve_information(Claim, Video_information, QA_CONTEXTS, Question, output_file_path)


