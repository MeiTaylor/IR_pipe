# 定义输出为utf8
# -*- coding: utf-8 -*-

import json
import requests
import re
import regex
from IR_relate_code import process_query_and_quality_score_value,process_evidence_and_Newness_Relevance,process_claim_and_generate_answer,generate_and_format_queries

import logging
import os



logging.basicConfig(filename='queries_processing.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



api_key = 'sk-NMDvPWjVD75ac1ba4D4cT3BLbkFJb3a0AeE39e8C4E6D9022'

def gpt35_analysis(prompt):
    url = "https://cn2us02.opapi.win/v1/chat/completions"

    payload = json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    })
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json',
        "Authorization": 'Bearer ' + api_key,
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    res = response.json()
    res_content = res['choices'][0]['message']['content']
    return res_content




def analyze_string(answer):
    # 去除标点符号，并转换为小写
    answer = re.sub(r'[^\w\s]', '', answer).lower()
    words = answer.split()
    
    # 统计 "yes" 和 "no" 的出现次数
    yes_count = words.count("yes")
    no_count = words.count("no")
    
    # 找到字符串的第一个单词
    first_word = words[0] if words else ""
    
    # 判断第一个单词是否是 "yes" 或 "no"
    first_word_is = "yes" if first_word == "yes" else "no" if first_word == "no" else "neither"
    
    # 计算最终结果
    
    if yes_count > no_count and first_word_is == "yes":
        final_result = "yes"
    elif yes_count < no_count and first_word_is == "no":
        final_result = "no"
    
    # return yes_count, no_count, first_word_is, final_result
    return final_result





def extract_complete_json(response_text):
    # 使用正则表达式模式匹配嵌套的JSON结构，使用`regex`模块
    json_pattern = r'(\{(?:[^{}]|(?1))*\})'
    matches = regex.findall(json_pattern, response_text)
    if matches:
        try:
            # 尝试解析每个匹配项以找到第一个有效的JSON
            for match in matches:
                json_data = json.loads(match)
                # 返回第一个有效的JSON数据
                return json_data
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
    return None




def process_json_files(folder_path, output_file_path):
    # 初始化一个字典来保存所有符合条件的证据
    output_data = {}

    # 遍历文件夹中的所有文件
    files = [f for f in os.listdir(folder_path) if f.startswith("Query") and f.endswith("_updated.json")]

    # 按照文件名中的数字排序
    files.sort(key=lambda f: int(re.search(r'Query (\d+)', f).group(1)))

    # 处理每个文件
    for filename in files:
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            evidences = []
            # 遍历文件中的所有证据
            for item in data.get("items", []):
              for key, evidence in item.items():
                  if evidence.get("website_content", {}).get("content_num", 0) != 0:
                      quality_score = evidence["website_quality_evaluation"].get("website_quality Score", 0)
                      newness_score = evidence["Content Score"].get("Newness Score", 0)
                      relevance_score = evidence["Content Score"].get("Relevance Score", 0)
                      total_score = quality_score + newness_score + relevance_score
                      evidences.append({
                          "title": evidence["title"],
                          "link": evidence["link"],
                          "snippet": evidence["snippet"],
                          "content": evidence["website_content"],
                          "website_quality_evaluation": evidence["website_quality_evaluation"],
                          "Content Score": evidence["Content Score"],
                          "total_score": total_score  # 临时存储用于排序
                      })

            # 根据总得分对证据进行排序，并选择得分最高的三个证据
            top_evidences = sorted(evidences, key=lambda x: x["total_score"], reverse=True)[:3]
            # 去除total_score字段
            for evidence in top_evidences:
                del evidence["total_score"]
            
            # 获取文件前缀作为key
            query_key = filename.replace('_updated.json', '')
            output_data[query_key] = top_evidences

    # 如果输出文件存在，读取其内容
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r', encoding='utf-8') as output_file:
            existing_data = json.load(output_file)
    else:
        existing_data = {}

    # 将新的数据合并到现有数据中
    existing_data.update(output_data)

    # 将合并后的结果写入输出文件
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(existing_data, output_file, ensure_ascii=False, indent=4)

    print(f"结果已追加写入 {output_file_path}")


import tiktoken

def count_tokens(text, model_name='gpt-3.5-turbo'):
    # 加载与模型对应的编码器
    encoding = tiktoken.encoding_for_model(model_name)
    
    # 将文本编码为tokens
    tokens = encoding.encode(text)
    
    # 返回token的数量
    return len(tokens)













output_file_path = "/workspaces/llmfnd/IR_test_result.json"








claim = "A video showing a shark swimming on a flooded highway during Hurricane Ian in Florida is real."
Video_information = {
    "Video_headline": "Fact-Checking Viral Photos",
    "Video_transcript": "",
    "Video_description_on_platform": "This video analyzes and debunks the viral photo of a shark allegedly swimming on a flooded highway.",
    "Video_platform": "youtube",
    "Video_date": "2023_08_07",
    "Video_description_from_descriptor": "A critical examination of viral photos, including the infamous shark on a flooded highway."
}
QA_CONTEXTS = {}

question = "What is the original source of the shark swimming on a flooded highway?"




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






# ------------------------------------------ #
# Prompts for Information Retrieving Verifier

# 输出yes或no，表示是否需要在网上搜索信息 
# ------------------------------------------ #


prompt_for_information_retrieving_verifier = f"""
{{
  "Claim": "{claim}",
  "Video_information": {json.dumps(Video_information)},
  "QA_CONTEXTS": {json.dumps(QA_CONTEXTS)},
  "New_Question": {{
    "Question": "{question}"
  }},
  "Task": "To answer the question, is searching information online needed? Yes or no? Please provide a precise probability, and if the threshold is greater than 80%, give the result as 'Yes', otherwise give the result as 'No'.",
  "Prediction": ""
}}

Please note that the first word must be either yes or no
"""

# answer = gpt35_analysis(prompt_for_information_retrieving_verifier)

# print(answer)


# final_result = analyze_string(answer)

# print(f"The final result is: {final_result}")






# Prompts for Queries Generation
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
# Evidence Selection（但是打分在之前的prompt中）
process_json_files(now_folder_path, output_file_path)

# Prompts for Question Answer based on the Evidence
# 处理声明并生成回答，将结果保存到输出文件路径
process_claim_and_generate_answer(claim, Video_information, QA_CONTEXTS, question, output_file_path)
