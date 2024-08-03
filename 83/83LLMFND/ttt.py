# import requests
# import json


# # 你的API密钥
# api_key = 'sk-VEA93CzU9Fd892f859C8T3BLBKFJ9d70149fe12640739881'

# # Google搜索函数
# def google_search(question):
#     base_url = "https://cn2us02.opapi.win/api/v1/openapi/search/google-search/v1"
#     excluded_sites = "www.snopes.com, www.factcheck.org, www.politifact.com"
    
#     # 构建请求 URL
#     url = f"{base_url}?key={api_key}&q={question}&siteSearch={excluded_sites}&siteSearchFilter=e"
    

#     headers = {
#         'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
#         'Content-Type': 'application/x-www-form-urlencoded',
#         'Authorization': 'Bearer ' + api_key,
#     }

    
#     response = requests.request("GET", url, headers=headers)
#     return response.text


# question = """snopes"""
# print()
# print()
# print()
# print()

# result = google_search(question)

# print(result)
# data = json.loads(result)

# # Save the result to a JSON file
# with open('search_result_noSnopes2.json', 'w') as json_file:
#     json.dump(data, json_file, indent=4)

# print("Result saved to search_result.json")















import logging
from datetime import datetime
import pytz

# 定义一个自定义的北京时间格式化器
class BeijingFormatter(logging.Formatter):
    def converter(self, timestamp):
        # 将时间戳转换为UTC时间
        dt = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
        # 将UTC时间转换为北京时间
        return dt.astimezone(pytz.timezone('Asia/Shanghai'))

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        # 使用自定义的日期格式
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    def format(self, record):
        record.asctime = self.formatTime(record)
        return super().format(record)

# 创建一个自定义的日志记录器
logger = logging.getLogger()

# 设置日志记录级别
logger.setLevel(logging.INFO)

# 创建一个文件处理器
file_handler = logging.FileHandler('claim_verifer.log')

# 创建一个自定义格式化器
formatter = BeijingFormatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')

# 为文件处理器设置格式化器
file_handler.setFormatter(formatter)

# 将文件处理器添加到日志记录器中
logger.addHandler(file_handler)

# 记录一个示例日志消息
logger.info('这是一条日志消息。')

# 使用 logging.info 记录日志消息
logging.info('这又是一条日志消息。')
