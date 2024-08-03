



import requests
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
import logging
import threading

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
]

def fetch_webpage_content_bs4(link, retries=2):
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

            return {"success": True, "content": content}
        except requests.exceptions.RequestException as e:
            # logging.error(f"BS4 Error fetching {link}: {str(e)}")
            if attempt < retries - 1:
                time.sleep(3)  # 等待3秒后重试
            else:
                return {"success": False, "error": f"Error fetching {link}: {str(e)}"}

def fetch_webpage_content_selenium(link):
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')  # 无头模式，不打开浏览器窗口
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    options.set_preference("general.useragent.override", random.choice(user_agents))
    
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
        
        return {"success": True, "content": content}
    except Exception as e:
        # logging.error(f"Selenium Error fetching {link}: {str(e)}")
        return {"success": False, "error": f"Error fetching {link}: {str(e)}"}
    finally:
        if driver:
            driver.quit()






def readAPI_fetch_content(url):
    api_key = None

    def fetch(url, headers):
        response = requests.get(url, headers=headers)
        response.raise_for_status()  
        if 'application/json' in response.headers.get('Content-Type'):
            return response.json()
        else:
            raise requests.exceptions.ContentTypeError(
                f"Unexpected content type: {response.headers.get('Content-Type')}"
            )

    def remove_unwanted_text(text):
        # 匹配括号中的 URL
        url_pattern = re.compile(r'\(https?://[^\)]+\)')
        # 匹配 mailto 编码字符串
        mailto_pattern = re.compile(r'\(mailto:[^\)]+\)')
        # 匹配 [] 及其内部内容
        brackets_pattern = re.compile(r'\[.*?\]')
        
        # 移除 URL 和编码字符串
        text = url_pattern.sub('', text)
        text = mailto_pattern.sub('', text)
        text = brackets_pattern.sub('', text)
        
        # 移除空行
        text = '\n'.join([line for line in text.split('\n') if line.strip()])

        return text

    headers_common = {
        "Accept": "application/json",
    }

    if api_key:
        headers_common["Authorization"] = f"Bearer {api_key}"

    url1 = f"https://r.jina.ai/{url}"

    try:
        response_default = fetch(url1, headers_common)

        # 清除 default 键中的不需要的文本
        default_content = response_default.get('data').get('content')
        clean_default_content = remove_unwanted_text(default_content)

        result = {
            'success': True,
            'content': clean_default_content,
        }
    except Exception as e:
        result = {
            'success': False,
            'error': f"Error fetching {url}: {str(e)}"
        }

    return result




def fetch_webpage_content(link, retries=3):
    results = [None, None, None]

    def run_bs4():
        results[0] = fetch_webpage_content_bs4(link, retries)
        # logging.info(f"BS4 result: {results[0]}")

    def run_selenium():
        results[1] = fetch_webpage_content_selenium(link)
        # logging.info(f"Selenium result: {results[1]}")

    def run_readapi():
        results[2] = readAPI_fetch_content(link)
        # logging.info(f"ReadAPI result: {results[2]}")

    threads = [
        threading.Thread(target=run_bs4),
        threading.Thread(target=run_selenium),
        threading.Thread(target=run_readapi),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


    # 返回内容最长的结果
    valid_results = [result for result in results if result and result.get("content")]
    if valid_results:
        valid_results.sort(key=lambda x: len(x.get("content", "")), reverse=True)
        return valid_results[0]

    # 如果都失败，返回最后一个结果
    return results[-1] if results[-1] else {"success": False, "content": ""}











import tiktoken

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
        content_tokens = count_tokens(content)
        # if content_tokens > 1000:
        #     content = ' '.join(content.split()[:1000]) + " ... [Content truncated]"
        #     content_tokens = 1000
        # if content_tokens > 300:
        #     content = ' '.join(content.split()[:300]) + " ... [Content truncated]"
        #     content_tokens = 300
    else:
        content = content_result["error"]
        content_tokens = 0
    
    return content, content_tokens

















link = "https://www.cnbc.com/2023/09/13/putin-and-kim-jong-uns-dinner-menu-after-two-hour-meeting-.html"

content, content_tokens = get_content_and_word_count(link)


print("content")
print(content)

print("content_tokens")
print(content_tokens)








import spacy
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np



snippet = "Sep 13, 2023 ... Russian President Vladimir Putin and North Korean leader Kim Jong Un shaking hands during their meeting at the Vostochny Cosmodrome in the Amur ..."





import os
import spacy
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import tiktoken

def extract_surrounding_text(content, snippet, num_tokens=250):
    # 加载spaCy的英语模型

    # 获取当前 Python 文件所在的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 构建模型路径
    en_core_web_sm_path = os.path.join(current_dir, 'model', 'en_core_web_sm-3.7.1')


    nlp = spacy.load(en_core_web_sm_path)

    # 将content转换为spaCy Doc对象
    content_doc = nlp(content)

    # 将content转换为句子列表
    sentences = [sent.text for sent in content_doc.sents]

    # 将snippet转换为spacy Doc对象
    snippet_doc = nlp(snippet)

    # 定义一个函数来计算相似度
    def calculate_similarity(snippet_doc, sentences):
        vectorizer = CountVectorizer().fit_transform([snippet_doc.text] + sentences)
        vectors = vectorizer.toarray()
        cosine_matrix = cosine_similarity(vectors)
        similarities = cosine_matrix[0][1:]  # 跳过第一个，因为那是snippet和自己的相似度
        return similarities

    # 计算每个句子与snippet的相似度
    similarities = calculate_similarity(snippet_doc, sentences)

    # 找到相似度最高的句子索引
    best_sentence_index = np.argmax(similarities)

    # 找到相似度最高的句子
    best_sentence = sentences[best_sentence_index]

    print("best_sentence")
    print(best_sentence)

    # 定义函数来计算token数量
    def count_tokens(text, model_name='gpt-3.5-turbo'):
        # 加载与模型对应的编码器
        encoding = tiktoken.encoding_for_model(model_name)
        
        # 将文本编码为tokens
        tokens = encoding.encode(text)
        
        # 返回token的数量
        return len(tokens)

    # 定义函数来编码文本为tokens
    def encode_text(text, model_name='gpt-3.5-turbo'):
        # 加载与模型对应的编码器
        encoding = tiktoken.encoding_for_model(model_name)
        
        # 将文本编码为tokens
        tokens = encoding.encode(text)
        
        return tokens, encoding

    # 提取最佳句子的前后各num_tokens个tokens
    def get_surrounding_tokens(doc, target_sentence, num_tokens=200):
        # 找到目标句子的开始和结束索引
        target_start_index = doc.text.find(target_sentence)
        target_end_index = target_start_index + len(target_sentence)
        
        # 提取目标句子的Token索引
        target_start_token_index = None
        target_end_token_index = None
        
        for token in doc:
            if token.idx == target_start_index:
                target_start_token_index = token.i
            if token.idx + len(token.text) - 1 == target_end_index - 1:
                target_end_token_index = token.i

        if target_start_token_index is None or target_end_token_index is None:
            return ""
        
        # 将全文转为tokens
        all_tokens, encoding = encode_text(doc.text)

        # 计算前后num_tokens个Token的范围
        start_token_index = max(0, target_start_token_index - num_tokens)
        end_token_index = min(len(all_tokens), target_end_token_index + num_tokens + 1)

        # 检查是否到达文本的开头或结尾，并添加提示
        prefix = "" if start_token_index == 0 else "[Content truncated]..."
        suffix = "" if end_token_index == len(all_tokens) else "...[Content truncated]"


        # 提取前后num_tokens个Token并拼接成字符串
        surrounding_tokens = all_tokens[start_token_index:end_token_index]
        surrounding_text = prefix + encoding.decode(surrounding_tokens) + suffix
        return surrounding_text

    # 获取前后各num_tokens个tokens的文本
    surrounding_text = get_surrounding_tokens(content_doc, best_sentence, num_tokens)

    return surrounding_text


surr = extract_surrounding_text(content, snippet)

print()
print()
print()
print()
print("surr")
print(surr)