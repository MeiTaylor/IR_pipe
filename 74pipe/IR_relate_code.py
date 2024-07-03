import requests
import json
import difflib
import regex
import textwrap


import requests
from bs4 import BeautifulSoup
import time
import random

import time
import logging
import os




# 你的API密钥
api_key = 'sk-NMDvPWjVD75ac1ba4D4cT3BLbkFJb3a0AeE39e8C4E6D9022'

# Google搜索函数
def google_search(question):
    base_url = "https://cn2us02.opapi.win/api/v1/openapi/search/google-search/v1"
    url = f"{base_url}?key={api_key}&q={question}"
    
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer ' + api_key,
    }
    
    response = requests.request("GET", url, headers=headers)
    return response.text



# GPT-3.5分析函数
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



# 提取完整的JSON数据
def extract_complete_json(response_text):
    json_pattern = r'(\{(?:[^{}]|(?1))*\})'
    matches = regex.findall(json_pattern, response_text)
    if matches:
        try:
            for match in matches:
                json_data = json.loads(match)
                return json_data
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
    return None




# 定义一个函数来找到最相似的URL
def find_best_match(link, evaluation):
    best_match = None
    highest_ratio = 0
    for eval_url in evaluation:
        # SequenceMatcher的基本思想是找到不包含“junk”元素的最长连续匹配子序列（LCS）。
        # 这不会产生最小的编辑序列，但是会产生对人“看起来正确”的匹配
        ratio = difflib.SequenceMatcher(None, link, eval_url).ratio()
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = eval_url
    return best_match, highest_ratio



def process_google_search(query, output_file_path):
    # 调用谷歌搜索函数获取结果
    data = google_search(query)

    data = json.loads(data)

    # 将每个 item 包装在一个 "evidenceN": {item} 结构中重命名
    new_items = []
    total_items = 0
    for i, item in enumerate(data.get('items', [])):
        # 提取链接
        link = item.get('link')
        # 获取网页内容和字数
        content, content_num = get_content_and_word_count(link)
        # 添加网页内容和字数到item中
        item['website_content'] = {
            'content': content,
            'content_num': content_num
        }
        new_items.append({f'evidence{i}': item})
        total_items = i

    total_items += 1

    # 使用新的 items 结构更新数据字典
    data['items'] = new_items

    # 将更新后的数据字典写入文件
    with open(output_file_path, 'w', encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)





def generate_and_format_queries(claim, Video_information, QA_CONTEXTS, question, output_file_path):
    # 构建用于生成查询的提示
    prompt_for_queries_generation = f"""
    {{
      "Claim": "{claim}",
      "Video_information": {json.dumps(Video_information)},
      "QA_CONTEXTS": {json.dumps(QA_CONTEXTS)},
      "New_Question": {{
        "Question": "{question}"
      }},
      "Task": "In order to answer this question, please determine what information is required, and design queries to search for this information on Google.And the most important point is that the final generated questions do not exceed two. Please generate the most important questions that require online retrieval of relevant information",
      "Queries": {{
        "Query 1": "",
        "Query 2": ""
      }}
    }}
    """

    logging.info("Prompts for Queries Generation")
    logging.info(prompt_for_queries_generation)

    # 生成查询
    query_answer = gpt35_analysis(prompt_for_queries_generation)

    # 构建用于格式化查询的提示
    prompt_for_query_format = f"""
    Please convert the following text content into the specified JSON structure. Make sure the output is in JSON format.

    The desired JSON structure:
    {{
      "Queries": {{
        "Query 1": "",
        "Query 2": ""
      }}
    }}

    The content to be converted:
    {query_answer}
    """

    # 格式化查询答案为 JSON 结构
    query_json_answer = gpt35_analysis(prompt_for_query_format)
    query_complete_json_answer = extract_complete_json(query_json_answer)

    # 读取现有的 JSON 数据，更新并写回文件
    with open(output_file_path, 'r', encoding='utf-8') as file:
        full_data = json.load(file)
        full_data.update(query_complete_json_answer)

    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(full_data, f, indent=4, ensure_ascii=False)

    return query_complete_json_answer













def process_query_and_quality_score_value(query, claim, Video_information, QA_CONTEXTS, question, output_file_path):
    
    process_google_search(query, output_file_path)

    with open(output_file_path, 'r', encoding="utf-8") as file:
        data = json.load(file)

    # 提取所有的 'displayLink' 值
    display_links = []
    for evidence in data.get('items', []):
        for key, item in evidence.items():
            if isinstance(item, dict):
                display_link = item.get('displayLink')
                if display_link:
                    display_links.append(display_link)

    logging.info("display_links")
    logging.info(display_links)


    prompt = f"""
{{
"Claim": "{claim}",
"Video_information": {Video_information},
"QA_CONTEXTS": {QA_CONTEXTS},
"Relate_Website": {display_links},
"Task": "Based on the provided Claim, Video_information, and QA_CONTEXTS, evaluate the listed websites to determine which ones have high credibility in terms of truthfulness and accuracy, and can aid in detecting fake news. Please provide a quality score (website_quality) out of 10 for each website and explain the reasoning for the score. The evaluation criteria include the website's overall reliability, historical accuracy, and capability to detect and expose fake news.

Please combine the evaluations for these aspects to give an overall quality score (website_quality) for each website, and provide detailed explanations for each score."
}}
In your response, when referring to related websites, be sure to provide the original name of the specific and detailed website in Relate_Website, and do not modify this name.
It is required to rate and explain the reasons for all websites. Each website should be rated an overall quality score (website_quality) out of 10, with detailed explanations for each score.
"""



    logging.info("rate and explain the reasons for all websites")
    logging.info(prompt)

    while True:
        # 获取GPT-3.5的分析结果
        answer = gpt35_analysis(prompt)
        logging.info(answer)

        # 构建GPT-3.5的格式转换提示
        prompt_for_format = f"""
Please convert the following text content into JSON format. For each website, use the following format:
{{
    "website": {{
    "website_quality Score": "quality_score_value",
    "justification": "justification_text"
    }}
}}

Note: 
- "quality_score_value" should be an integer between 0 and 10.
- "justification" should be a string.

Website represents the current website URL for rating and evaluation, rather than the word "website", preferably with a complete link via HTTP or HTTPS. For each website, quality_score_value, relevances_score_value, and newness_score_value are integers that represent the website's ratings in terms of quality, relevance, and novelty, ranging from 1 to 10. Justification_text is a string that provides reasons and explanations for the rating.
The following is the text content that needs to be converted:
{answer}
"""


        # 获取格式化的JSON结果
        answer_format = gpt35_analysis(prompt_for_format)

        # 提取评价信息
        evaluation = extract_complete_json(answer_format)
        logging.info("rating and evaluation")
        logging.info(evaluation)

        if not evaluation:
            print("未能提取有效的JSON格式评价信息，重新获取GPT-3.5的分析结果。")
            continue  # 重新开始while循环



        # 初始化 match_count 和 total_items
        match_count = 0
        total_items = 0

        # 遍历所有的 items 并处理每个 evidence
        for evidence in data.get('items', []):
            total_items += 1  # 每遍历一个 item，total_items 加 1
            for key, item in evidence.items():
                if isinstance(item, dict):
                    display_link = item.get('displayLink')
                    if display_link:
                        best_match, ratio = find_best_match(display_link, evaluation)
                        logging.info(f"Display Link: {display_link}, Best Match: {best_match}, Ratio: {ratio}")
                        if ratio > 0.6:  # 设定一个相似度阈值，可以根据需要调整
                            item['website_quality_evaluation'] = evaluation[best_match]
                            match_count += 1

        if match_count == total_items:
            break  # 如果所有的items都匹配到了评价信息，则跳出while循环
    


    # 将更新后的数据写回output_file_pathjson文件
    updated_single_query_path = output_file_path.replace(".json", "_updated.json")
    with open(updated_single_query_path, 'w', encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    




def process_evidence_and_Newness_Relevance(key, query, claim, Video_information, QA_CONTEXTS, question, updated_single_query_path):

    
    # 选择10个证据的部分信息进行下一步的证据选择
    evidence_json = process_evidence(updated_single_query_path)

    logging.info("-" * 50)
    logging.info("Selecting the 10 quality evidence for further selection:")
    logging.info("-" * 50)
    logging.info(evidence_json)


    prompt_for_evidence_selection = f"""
{{
  "Claim": "{claim}",
  "Video_information": {json.dumps(Video_information)},
  "QA_CONTEXTS": {json.dumps(QA_CONTEXTS)},
  "New_Question": {{
    "Question": "{question}"
  }},
  "Current Evidence Searching queries on google": {{
    "{key}": "{query}"
  }},
  "Evidence Found and Judgments on Them": {json.dumps(evidence_json)},
  "Task": "Based on the information of each evidence in 'Evidence Found and Judgments on Them', especially the link and snippet which generally contain the publication time of the webpage, evaluate the timeliness (Newness score, 0~10 points, provide a score). Consider how recent the evidence is compared to the current date of July 2024. More recent evidence should receive higher scores, while older evidence should receive lower scores.

  Similarly, based on the information of each evidence, especially the content of the title and snippet, evaluate the relevance of this evidence to the current question (Relevance score, 0~10 points, provide a score). Consider how closely the evidence addresses the specifics of the question. More directly relevant evidence should receive higher scores, while less relevant evidence should receive lower scores.

  For each evidence (evidence0, evidence1, evidence2, evidence3, evidence4, evidence5, evidence6, evidence7, evidence8, evidence9), provide the following:
  1. "Newness Score": score, justification
  2. "Relevance Score": score, justification
  Each evidence should include these details, specified as 'evidenceN' where N is the evidence number."
}}
"""

    complete_json_evidence_answer = {}
    expected_evidences = {f"evidence{i}" for i in range(10)}

    while not expected_evidences.issubset(complete_json_evidence_answer.keys()):
        evidence_selection = gpt35_analysis(prompt_for_evidence_selection)

        logging.info("-" * 50)
        logging.info("prompt_for_evidence_selection")
        logging.info(prompt_for_evidence_selection)
        logging.info("-" * 50)
        logging.info("evidence_selection")
        logging.info(evidence_selection)

        format_prompt = f"""
Please convert the following text content into the specified JSON structure. Ensure the output is in JSON format and maintain the original content as much as possible, changing only the structure to the specified JSON format.

The desired JSON structure:
"evidenceN": {{
  "Newness Score": "score",
  "Newness Justification": "justification",
  "Relevance Score": "score",
  "Relevance Justification": "justification"
}}

Note: 
- "score" should be an integer between 0 and 10.
- "justification" should be a string.

The content to be converted:
{evidence_selection}
"""

        json_evidence_answer = gpt35_analysis(format_prompt)
        logging.info("json_evidence_answer")
        logging.info(json_evidence_answer)

        new_evidence = extract_complete_json(json_evidence_answer)
        complete_json_evidence_answer.update(new_evidence)
        logging.info("complete_json_evidence_answer")
        logging.info(complete_json_evidence_answer)

    with open(updated_single_query_path, 'r', encoding="utf-8") as file:
        data = json.load(file)

    for evidence_key, scores in complete_json_evidence_answer.items():
        for item in data['items']:
            if evidence_key in item:
                item[evidence_key]['Content Score'] = scores

    with open(updated_single_query_path, 'w', encoding="utf-8") as file:
        json.dump(data, file, indent=4)






import json
import logging
def process_claim_and_generate_answer(claim, Video_information, QA_CONTEXTS, question, output_file_path):
    # 加载 JSON 数据
    with open(output_file_path, 'r', encoding='utf-8') as file:
        new_data = json.load(file)

    # 用于存储所有转换后的证据的字典
    all_transformed_evidence = {}

    # 遍历数据中的每个查询
    for query_key in new_data:
        if query_key.startswith("Query"):  # 检查键是否以“Query”开头
            evidence_list = new_data[query_key]
            for i, evidence_dict in enumerate(evidence_list):
                # 构造新键
                new_key = f"{query_key}_evidence_{i + 1}"

                # 提取所需的字段
                extracted_info = {
                    "title": evidence_dict.get("title", ""),
                    "link": evidence_dict.get("link", ""),
                    "snippet": evidence_dict.get("snippet", ""),
                    "content": evidence_dict.get("content", {}).get("content", "")
                }

                # 将提取的信息添加到转换后的证据字典中
                all_transformed_evidence[new_key] = extracted_info

    logging.info("all_transformed_evidence")
    logging.info(all_transformed_evidence)

    # 提取 Queries 内容
    queries_content = new_data.get("Queries", {})

    # 构建 prompt
    prompt_for_question_answer_based_on_evidence = f"""
    {{
      "Claim": "{claim}",
      "Video_information": {json.dumps(Video_information, ensure_ascii=False, indent=4)},
      "QA_CONTEXTS": {json.dumps(QA_CONTEXTS, ensure_ascii=False, indent=4)},
      "New_Question": {{
        "Question": "{question}"
      }},
      "Queries": {json.dumps(queries_content, ensure_ascii=False, indent=4)},
      "Good evidence information": {json.dumps(all_transformed_evidence, ensure_ascii=False, indent=4)},
      "Task": "Based on the evidence extracted, generate an explanatory answer to the question: '{question}' that references the evidence. Evaluate the confidence (XX%) of your answer based on the analysis of the above evaluation of the evidence and the logic of the reasoning process."
    }}
    """

    logging.info("prompt_for_question_answer_based_on_evidence")
    logging.info(prompt_for_question_answer_based_on_evidence)

    token_count = count_tokens(prompt_for_question_answer_based_on_evidence)
    print(f"Token count: {token_count}")
    logging.info(f"Token count: {token_count}")

    attempt = 0
    max_attempts = 5
    final_json_answer = None

    while attempt < max_attempts:
        attempt += 1
        answer = gpt35_analysis(prompt_for_question_answer_based_on_evidence)

        logging.info("prompt_for_question_answer_based_on_evidence ANSWER")
        logging.info(answer)

        format_final_prompt = f"""
        Please convert the given text content into the specified JSON structure. Ensure that the output is properly formatted as JSON.

        Desired JSON structure:
        {{
          "QA": {{
            "Question": "{question}",
            "Answer": "",
            "Confidence": ""
          }}
        }}

        Please note: Only modify the structure of the given following content, keeping the content as intact as possible and preserving the original language and descriptions.

        Text content to be converted:
        "{answer}"
        """

        logging.info("format_final_prompt")
        logging.info(format_final_prompt)

        final_answer = gpt35_analysis(format_final_prompt)

        final_json_answer = extract_complete_json(final_answer)

        logging.info("final_json_answer")
        logging.info(final_json_answer)

        # 检查 Answer 和 Confidence 字段是否为空
        if final_json_answer and final_json_answer.get("QA", {}).get("Answer") and final_json_answer.get("QA", {}).get("Confidence"):
            break  # 如果不为空，则跳出循环

    with open(output_file_path, 'r', encoding='utf-8') as file:
        full_data = json.load(file)
    full_data.update(final_json_answer)

    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(full_data, f, indent=4, ensure_ascii=False)


























def process_evidence(file_path):
    # 加载 JSON 数据
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 提取 items
    items = data.get("items", [])

    # 选择前 10 项
    top_items = items[:10]

    # 从每个 top item 提取所需的字段，并重命名
    evidence_found_and_judgments = []
    for i, item_dict in enumerate(top_items):
        for key, item in item_dict.items():
            evidence = {
                "title": item.get("title"),
                "link": item.get("link"),
                "displayLink": item.get("displayLink"),
                "snippet": item.get("snippet"),
                "htmlSnippet": item.get("htmlSnippet"),
                "website_quality_evaluation": item.get("website_quality_evaluation")
            }
            evidence_found_and_judgments.append({f'evidence{i}': evidence})

    # 以 JSON 格式输出结果
    output_json = json.dumps(evidence_found_and_judgments, indent=4, ensure_ascii=False)

    return output_json



import requests
from bs4 import BeautifulSoup
import time
import random
import json
import textwrap
from selenium import webdriver
from selenium.webdriver.common.by import By
import tiktoken
import logging

# 随机选择 User-Agent 以模拟不同的浏览器和操作系统
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
]

def fetch_webpage_content_bs4(link, retries=3):
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Upgrade-Insecure-Requests': '1'
    }
    
    session = requests.Session()
    session.headers.update(headers)

    for attempt in range(retries):
        try:
            response = session.get(link)
            response.raise_for_status()
            response.encoding = 'utf-8'  # 明确指定响应的编码
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            content = '\n'.join([para.get_text() for para in paragraphs])

            # 确保内容是UTF-8编码
            content = content.encode('utf-8', errors='replace').decode('utf-8')
            logging.info(f"BS4 Successfully fetched content from {link}")

            # 输出content前100字内容
            logging.info(f"Content preview: {content[:100]}")

            return {"success": True, "content": content}
        except requests.exceptions.RequestException as e:
            logging.error(f"BS4 Error fetching {link}: {str(e)}")
            if attempt < retries - 1:
                time.sleep(3)  # 等待15秒后重试
            else:
                return {"success": False, "error": f"Error fetching {link}: {str(e)}"}
            



from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import time


def fetch_webpage_content_selenium(link):
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')  # 无头模式，不打开浏览器窗口
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    
    driver = None
    try:
        driver_path = '/usr/local/bin/geckodriver'  # GeckoDriver的路径
        service = FirefoxService(executable_path=driver_path)
        driver = webdriver.Firefox(service=service, options=options)
        
        driver.get(link)
        
        # 模拟滚动页面以触发动态加载
        SCROLL_PAUSE_TIME = 2
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # 使用WebDriverWait等待页面特定元素加载
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'p')))
        
        paragraphs = driver.find_elements(By.TAG_NAME, 'p')
        content = '\n'.join([para.text for para in paragraphs])
        logging.info(f"selenium Successfully fetched content from {link}")
        # 输出content前100字内容
        logging.info(f"Content preview: {content[:100]}")
        
        return {"success": True, "content": content}
    except Exception as e:
        logging.error(f"selenium Error fetching {link}: {str(e)}")
        return {"success": False, "error": f"Error fetching {link}: {str(e)}"}
    finally:
        if driver:
            driver.quit()










def fetch_webpage_content(link, retries=1):
    # 尝试使用 BeautifulSoup 抓取网页内容
    content_result = fetch_webpage_content_bs4(link, retries)
    if not content_result["success"] or not content_result["content"].strip() or count_tokens(content_result["content"]) < 100:
        # 如果 BeautifulSoup 抓取失败或内容为空或内容少于100字，使用 Selenium
        content_result = fetch_webpage_content_selenium(link)
        
        # 检查 Selenium 抓取结果
        if not content_result["success"] or not content_result["content"].strip() or count_tokens(content_result["content"]) < 100:
            content_result["content"] = ""  # 确保最终返回空内容

    if not content_result["success"]:
        content_result["content"] = ""

    return content_result





def count_tokens(text, model_name='gpt-3.5-turbo'):
    # 加载与模型对应的编码器
    encoding = tiktoken.encoding_for_model(model_name)
    
    # 将文本编码为tokens
    tokens = encoding.encode(text)
    
    # 返回token的数量
    return len(tokens)







def modified_final_evidence(evidence):
    # 解析JSON数据
    json_evidence = evidence

    # 处理每一个evidence
    for query_key, evidences in json_evidence.items():
        if query_key.startswith("Query") and isinstance(evidences, dict):  # 确保只处理以Query开头的键
            for evidence_key, value in evidences.items():
                # 去除evaluation
                if 'website_quality_evaluation' in value:
                    del value['website_quality_evaluation']

                # 获取网页内容并添加到JSON数据中
                link = value['link']
                content_result = fetch_webpage_content(link)
                if content_result["success"]:
                    content = content_result["content"]
                    if count_tokens(content) > 4000:
                        content = ' '.join(content.split()[:4000]) + " ... [Content truncated]"
                    value['complete_content'] = content
                else:
                    value['complete_content'] = content_result["error"]

    return json_evidence




def get_content_and_word_count(link):
    # 获取网页内容
    content_result = fetch_webpage_content(link)
    if content_result["success"]:
        content = content_result["content"]
        content_num = count_tokens(content)
        if content_num > 1000:
            content = ' '.join(content.split()[:1000]) + " ... [Content truncated]"
            content_num = 1000
    else:
        content = content_result["error"]
        content_num = 0
    
    return content, content_num