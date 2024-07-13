import json
import requests
import re

import logging
import os
import sys
import regex

from CV_relate_code import *
from InformationRetriever import information_retriever_complete


logging.basicConfig(filename='claim_verifer.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')









def update_cv_result_with_ir_data(key, cv_output_file_path, ir_output_file_path):
    # 从IR_output_file_path中提取内容
    with open(ir_output_file_path, 'r') as ir_file:
        ir_data = json.load(ir_file)

    qa_data = ir_data.get('QA', {})
    qa_question = qa_data.get('Question', '')
    qa_answer = qa_data.get('Answer', '')
    qa_confidence = qa_data.get('Confidence', '')

    # 更新CV_output_file_path中的json文件
    cv_json_file_path = os.path.join(cv_output_file_path)

    # 读取CV_result.json内容
    with open(cv_json_file_path, 'r') as cv_file:
        cv_data = json.load(cv_file)

    # 更新Initial_Question_Generation部分
    initial_question_generation = cv_data.get(key, {})
    initial_question_generation['Question'] = qa_question
    initial_question_generation['Answer'] = qa_answer
    initial_question_generation['Confidence'] = qa_confidence

    cv_data[key] = initial_question_generation

    # 将更新后的数据写回CV_result.json
    with open(cv_json_file_path, 'w') as cv_file:
        json.dump(cv_data, cv_file, indent=4)

    logging.info("Updated CV_result.json with QA data from IR_result.json")




def extract_qa_contexts(cv_output_file_path):
    # 检查文件是否存在，如果存在则读取现有内容
    if os.path.exists(cv_output_file_path):
        with open(cv_output_file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                logging.error("Error reading JSON file.")
                return {}
    else:
        logging.error(f"File {cv_output_file_path} does not exist.")
        return {}
    
    # 提取Initial_Question_Generation和Follow_Up_Question_{counter}的内容
    new_QA_CONTEXTS = {}
    for key, value in data.items():
        if key == "Initial_Question_Generation" or key.startswith("Follow_Up_Question_"):
            new_QA_CONTEXTS[key] = value

    return new_QA_CONTEXTS





































CV_output_file_path = "/workspaces/llmfnd/CV_result.json"



Claim = "A video showing a shark swimming on a flooded highway during Hurricane Ian in Florida."
Video_information = {
    "Video_headline": "a shark swimming on a flooded highway",
    "Video_transcript": "",
    "Video_description_on_platform": "This video analyzes and debunks the photo of a shark allegedly swimming on a flooded highway.",
    "Video_platform": "youtube",
    "Video_date": "2023_08_07",
    "Video_description_from_descriptor": "A video, including the shark on a flooded highway."
}
QA_CONTEXTS = {}




# 检查文件是否存在
if not os.path.exists(CV_output_file_path):
    # 如果文件不存在，创建文件并写入一个空的JSON对象
    with open(CV_output_file_path, 'w') as file:
        json.dump({}, file)

with open(CV_output_file_path, 'r+') as file:
    data = json.load(file)
    data["Claim"] = Claim
    data["Video_information"] = Video_information
    file.seek(0)
    json.dump(data, file, indent=4)










try:
    # 调用 process_claim_verifier 函数
    judgment, confidence = process_claim_verifier(Claim, Video_information, QA_CONTEXTS, CV_output_file_path)
    logging.info("process_claim_verifier result - Judgment: %s, Confidence: %s", judgment, confidence)

    # 判断是否需要生成问题
    if_generate_question = judgment and confidence >= 0.5

    if if_generate_question:
        # false 的分支循环
        # 调用 generate_initial_question 函数并获取返回的问题
        max_attempts = 3
        attempts = 0
        is_now_QA_useful = False

        while not is_now_QA_useful and attempts < max_attempts:
            try:
                # 调用 generate_initial_question 函数并获取返回的问题
                key, question = generate_initial_question(Claim, Video_information, CV_output_file_path)
                logging.info("Generated Question: %s", question)

                # 获取 CV_output_file_path 所在的目录路径
                directory_path = os.path.dirname(CV_output_file_path)
                
                # 在该目录下创建一个以 key 命名的文件夹
                key_folder_path = os.path.join(directory_path, key)
                os.makedirs(key_folder_path, exist_ok=True)

                # 创建 IR_output_file_path
                IR_output_file_path = os.path.join(key_folder_path, "IR_result.json")

                # 调用 information_retriever_complete 函数
                information_retriever_complete(Claim, Video_information, QA_CONTEXTS, question, IR_output_file_path)
                logging.info("IR results saved to: %s", IR_output_file_path)

                # 打开并读取JSON文件
                with open(IR_output_file_path, 'r', encoding='utf-8') as file:
                    newest_QA_Context = json.load(file)
                
                is_now_QA_useful = get_validator_result(Claim, Video_information, newest_QA_Context)
                
                # 增加尝试次数
                attempts += 1
            except Exception as e:
                logging.error("Error in initial question generation attempt %d: %s", attempts, str(e))
                logging.error(traceback.format_exc())

        if is_now_QA_useful:
            # 如果 is_now_QA_useful 为 True，则执行以下代码
            update_cv_result_with_ir_data(key, CV_output_file_path, IR_output_file_path)
        else:
            logging.warning("Max generate_initial_question attempts reached and QA context is still not useful.")







    new_question_count = 1
    while(if_generate_question and new_question_count < 2):
        new_question_count += 1
        new_QA_CONTEXTS = extract_qa_contexts(CV_output_file_path)

        # 调用 process_claim_verifier 函数
        new_judgment, new_confidence = process_claim_verifier(Claim, Video_information, new_QA_CONTEXTS, CV_output_file_path)
        logging.info("New process_claim_verifier result - Judgment: %s, Confidence: %s", new_judgment, new_confidence)

        if new_judgment and new_confidence <= 0.5:
            break

        max_attempts = 3
        attempts = 0
        is_now_QA_useful = False

        while not is_now_QA_useful and attempts < max_attempts:
            try:
                new_key, follow_up_question = generate_follow_up_question(Claim, Video_information, new_QA_CONTEXTS, CV_output_file_path)
                logging.info("%s Generated Question: %s", new_key, follow_up_question)

                # 获取 CV_output_file_path 所在的目录路径
                directory_path = os.path.dirname(CV_output_file_path)
                
                # 在该目录下创建一个以 key 命名的文件夹
                key_folder_path = os.path.join(directory_path, new_key)
                os.makedirs(key_folder_path, exist_ok=True)

                # 创建 IR_output_file_path
                IR_output_file_path = os.path.join(key_folder_path, "IR_result.json")

                # 调用 information_retriever_complete 函数
                information_retriever_complete(Claim, Video_information, new_QA_CONTEXTS, follow_up_question, IR_output_file_path)
                logging.info("IR results saved to: %s", IR_output_file_path)

                # 打开并读取JSON文件
                with open(IR_output_file_path, 'r', encoding='utf-8') as file:
                    newest_QA_Context = json.load(file)
                
                is_now_QA_useful = get_validator_result(Claim, Video_information, newest_QA_Context)
                
                # 增加尝试次数
                attempts += 1
            except Exception as e:
                logging.error("Error in follow-up question generation attempt %d: %s", attempts, str(e))
                logging.error(traceback.format_exc())

        if is_now_QA_useful:
            # 如果 is_now_QA_useful 为 True，则执行以下代码
            update_cv_result_with_ir_data(new_key, CV_output_file_path, IR_output_file_path)
        else:
            logging.warning("Max generate_follow_up_question attempts reached and QA context is still not useful.")

    new_QA_CONTEXTS = extract_qa_contexts(CV_output_file_path)
    final_json_answer = process_claim_final(Claim, Video_information, new_QA_CONTEXTS, CV_output_file_path)
    logging.info("final_json_answer \n%s", final_json_answer)

except Exception as e:
    logging.error("An error occurred: %s", str(e))
    logging.error(traceback.format_exc())
