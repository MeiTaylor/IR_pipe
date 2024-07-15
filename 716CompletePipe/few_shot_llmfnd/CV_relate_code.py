import json
import requests
import re

import logging
import os
import sys
import regex


# logging.basicConfig(filename='claim_verifer.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')






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


























def is_valid_json_claim_verifier_answer(json_data):
    """
    Validate that the JSON data has "Judgment" as "Yes" or "No", 
    and "Confidence" as a percentage (0% to 100%).
    """
    try:
        # data = json.loads(json_data)
        judgment = json_data["CVResult"]["Judgment"]
        confidence = json_data["CVResult"]["Confidence"]
        
        if judgment in ["Yes", "No"] and confidence.endswith("%"):
            confidence_value = int(confidence.strip('%'))
            if 0 <= confidence_value <= 100:
                return True
    except (KeyError, ValueError, json.JSONDecodeError):
        pass
    
    return False


# ------------------------------------------ #
# Prompts for Claim Verifier 
# ------------------------------------------ #

def process_claim_verifier(Claim, Video_information, QA_CONTEXTS, output_file_path):
    # 构建用于验证声明的提示
    prompt_for_claim_verifier = f"""
{{
  "Claim": "{Claim}",
  "Video_information": {json.dumps(Video_information)},
  "QA_CONTEXTS": {json.dumps(QA_CONTEXTS)},
  "Task": "Based on the content of the Video_information and the QA_CONTEXTS, accurately and rigorously determine whether the claim is true or false. Can we determine the truthfulness of the claim based on the existing information? Please provide a reliability probability, and clearly answer 'Yes' (the existing information can determine the truthfulness) or 'No' (the existing information cannot determine the truthfulness). Answer 'Yes' only if the reliability probability is sufficiently high.",
  "Examples": [
    {{
      "Claim": "A video that went viral in August 2023 showed a beach party in Kyiv, proving that the war in Ukraine is a hoax.",
      "Video_information": {{
        "Video_headline": "Stew Peters - The war in Ukraine is FAKE.",
        "Video_transcript": "",
        "Video_decription": "The war in Ukraine is FAKE. https://t.co/l63GG7oUTl",
        "Video_platform": "twitter",
        "Video_date": "2023_08_07",
        "Video_description_from_descriptor": "The video clip is a mix-up, which shows a beach party with clips and photos of many boys and girls, drinks and beach umbrellas. It seems to happen on a daytime with lots of sunshine. It is hard to determine the location of party from the video pictures or contents."
      }},
      "QA_CONTEXTS": {{
        "Question 1": "Is there a beach party in Kyiv on or around the date of the video (Aug. 7, 2023)?",
        "Answer 1": "Yes, there was indeed a beach party in Kyiv on August 6, 2023. The event, held at a local beach club, drew attention and was documented in online posts and social media, highlighting the Ukrainians' efforts to maintain some semblance of normalcy despite the ongoing war.",
        "Question 2": "Are there credible reports or evidence of continued conflict or other significant events in Ukraine on or around the date of the video (August 7, 2023)?",
        "Answer 2": "Yes, there were credible reports and evidence of continued conflict and other significant events in Ukraine around the date of the video (August 7, 2023). During this period, there were ongoing military actions, including shelling and missile attacks in various regions of Ukraine. For instance, reports from early August 2023 highlighted Ukrainian forces making gains in the south while facing continued hostilities in other parts, such as Kherson, which was under shelling​​."
      }},
      "Prediction": "99%. Yes."
    }}
  ],
  "Prediction": ""
}}
"""

    for attempt in range(3):
        # 获取声明验证的答案
        claim_verifier_answer = gpt35_analysis(prompt_for_claim_verifier)
        logging.info("claim_verifier_answer")
        logging.info(claim_verifier_answer)

        # 格式化声明验证的提示
        format_prompt_for_claim_verifier = f"""
        Please convert the following text content into the specified JSON structure. Ensure the output is in JSON format and maintain the original content as much as possible, changing only the structure to the specified JSON format.

        The desired JSON structure:
        {{
        "CVResult": {{
            "Judgment": "Yes or No",
            "Confidence": "0%~100%"
        }}
        }}

        The content to be converted:
        {claim_verifier_answer}
        """

        # 获取格式化后的JSON答案
        json_claim_verifier_answer = gpt35_analysis(format_prompt_for_claim_verifier)

        # 提取完整的JSON声明验证答案
        complete_json_claim_verifier_answer = extract_complete_json(json_claim_verifier_answer)

        logging.info("complete_json_claim_verifier_answer")
        logging.info(complete_json_claim_verifier_answer)

        # 检查 complete_json_claim_verifier_answer 是否满足要求
        if is_valid_json_claim_verifier_answer(complete_json_claim_verifier_answer):
            break

    logging.info("----------complete_json_claim_verifier_answer----------")
    logging.info(complete_json_claim_verifier_answer)

    # 确保文件是字典结构而不是列表
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r+') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    # 确保现有数据是一个字典
    if not isinstance(existing_data, dict):
        existing_data = {}

    # 删除已有的 CVResult
    if "CVResult" in existing_data:
        del existing_data["CVResult"]

    # 追加新生成的声明验证答案
    existing_data.update(complete_json_claim_verifier_answer)

    # 保存更新后的内容到文件
    with open(output_file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    logging.info("complete_json_claim_verifier_answer successfully appended to %s", output_file_path)

    # 提取 Judgement 和 Confidence 并进行转换
    judgment_str = complete_json_claim_verifier_answer["CVResult"]["Judgment"]
    confidence_str = complete_json_claim_verifier_answer["CVResult"]["Confidence"]

    judgment_bool = True if judgment_str.lower() == "yes" else False
    confidence_float = float(confidence_str.strip('%')) / 100.0

    return judgment_bool, confidence_float






# ------------------------------------------ #
# Prompts for the initial question generation
# ------------------------------------------ #



def generate_initial_question(Claim, Video_information, output_file_path):
    # 初始问题生成的提示
    prompt_for_initial_question = f"""
{{
  "Claim": "{Claim}",
  "Video_information": {json.dumps(Video_information)},
  "Task": "Based on the relevant information from the Video_information and Claim, generate a professional and detailed question that can help determine the authenticity of the video content and the Claim. The goal is to assess whether the Claim is a true statement or misinformation. The final output should be a single question, in one sentence, not exceeding 30 words.",
  "Examples": [
    {{
      "Claim": "A video that went viral in August 2023 showed a beach party in Kyiv, proving that the war in Ukraine is a hoax.",
      "Video_information": {{
        "Video_headline": "Stew Peters - The war in Ukraine is FAKE.",
        "Video_transcript": "",
        "Video_decription": "The war in Ukraine is FAKE. https://t.co/l63GG7oUTl",
        "Video_platform": "twitter",
        "Video_date": "2023_08_07",
        "Video_description_from_descriptor": "The video clip is a mix-up, which shows a beach party with clips and photos of many boys and girls, drinks and beach umbrellas. It seems to happen on a daytime with lots of sunshine. It is hard to determine the location of party from the video pictures or contents."
      }},
      "Initial_Question_Generation": {{
        "Question": "Is there a beach party in Kyiv on or around the date of the video (Aug. 7, 2023)?"
      }}
    }}
  ],
  "Initial_Question_Generation": {{
    "Question": ""
  }}
}}
"""

    # 使用gpt35_analysis生成初始问题
    initial_question_answer = gpt35_analysis(prompt_for_initial_question)

    # logging.info("initial_question_answer")
    # logging.info(initial_question_answer)

    # 格式化初始问题生成的提示
    prompt_for_initial_question_json = f"""
    Please convert the following text content into the specified JSON structure. Ensure the output is in JSON format and maintain the original content as much as possible, changing only the structure to the specified JSON format. The final output should be a single question, in one sentence, not exceeding 30 words.

    The desired JSON structure:
    {{
      "Initial_Question_Generation": {{
        "Question": ""
      }}
    }}

    The content to be converted:
    {initial_question_answer}
    """

    # 使用gpt35_analysis转换为JSON格式
    json_initial_question_answer = gpt35_analysis(prompt_for_initial_question_json)

    # logging.info("json_initial_question_answer")
    # logging.info(json_initial_question_answer)

    # 提取完整的JSON结构
    complete_json_initial_question_answer = extract_complete_json(json_initial_question_answer)

    # logging.info("complete_json_initial_question_answer")
    # logging.info(complete_json_initial_question_answer)

    # 确保文件是字典结构而不是列表
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r+') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    # 确保现有数据是一个字典
    if not isinstance(existing_data, dict):
        existing_data = {}
    
    # 删除已有的Initial_Question_Generation键
    existing_data.pop("Initial_Question_Generation", None)


    # 追加新生成的问题
    existing_data.update(complete_json_initial_question_answer)

    # 保存更新后的内容到文件
    with open(output_file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)


    logging.info("Initial question has been generated and saved successfully.")

    # 返回生成的问题
    return "Initial_Question_Generation", complete_json_initial_question_answer["Initial_Question_Generation"]["Question"]



# ---------------------------------------------- #
# Prompts for the follow-up question generation
# ---------------------------------------------- #


def generate_follow_up_question(Claim, Video_information, QA_CONTEXTS, output_file_path):
    # 跟进问题生成的提示
    prompt_for_the_follow_up_question = f"""
{{
  "Claim": "{Claim}",
  "Video_information": {json.dumps(Video_information)},
  "QA_CONTEXTS": {json.dumps(QA_CONTEXTS)},
  "Task": "To verify the Claim, generate a professional and detailed follow-up question based on the relevant information from the Claim and Video_information, which are our fundamental sources for identifying misinformation. QA_CONTEXTS are previous QA pairs that can serve as a reference. The goal is to determine the next step in assessing the authenticity of the Claim and Video_information. The final output should be a single question, in one sentence, not exceeding 30 words.",
  "Examples": [
    {{
      "Claim": "A video that went viral in August 2023 showed a beach party in Kyiv, proving that the war in Ukraine is a hoax.",
      "Video_information": {{
        "Video_headline": "Stew Peters - The war in Ukraine is FAKE.",
        "Video_transcript": "",
        "Video_description": "The war in Ukraine is FAKE. https://t.co/l63GG7oUTl",
        "Video_platform": "twitter",
        "Video_date": "2023_08_07",
        "Video_description_from_descriptor": "The video clip is a mix-up, which shows a beach party with clips and photos of many boys and girls, drinks and beach umbrellas. It seems to happen on a daytime with lots of sunshine. It is hard to determine the location of party from the video pictures or contents."
      }},
      "QA_CONTEXTS": {{
        "Question 1": "Is there a beach party in Kyiv on or around the date of the video (Aug. 7, 2023)?",
        "Answer 1": "Yes, there was indeed a beach party in Kyiv on August 6, 2023. The event, held at a local beach club, drew attention and was documented in online posts and social media, highlighting the Ukrainians' efforts to maintain some semblance of normalcy despite the ongoing war."
      }},
      "Task": "To verify the claim, what is the next question we need to know the answer to?",
      "Prediction": "Are there credible reports or evidence of continued conflict or other significant events in Ukraine on or around the date of the video (August 7, 2023)?"
    }}
  ],
  "Prediction": ""
}}
"""

    # 使用gpt35_analysis生成跟进问题
    follow_up_question_answer = gpt35_analysis(prompt_for_the_follow_up_question)

    logging.info("follow_up_question_answer")
    logging.info(follow_up_question_answer)

    # 格式化跟进问题生成的提示
    prompt_for_follow_up_question_formatting = f"""
    Please convert the following text content into the specified JSON structure. Ensure the output is in JSON format and maintain the original content as much as possible, changing only the structure to the specified JSON format. The final output should be a single question, in one sentence, not exceeding 30 words.

    The desired JSON structure:
    {{
      "Follow_Up_Question_Generation": {{
        "Question": ""
      }}
    }}

    The content to be converted:
    {follow_up_question_answer}
    """

    # 使用gpt35_analysis转换为JSON格式
    json_follow_up_question_answer = gpt35_analysis(prompt_for_follow_up_question_formatting)

    logging.info("json_follow_up_question_answer")
    logging.info(json_follow_up_question_answer)

    # 提取完整的JSON结构
    complete_json_follow_up_question_answer = extract_complete_json(json_follow_up_question_answer)

    logging.info("complete_json_follow_up_question_answer")
    logging.info(complete_json_follow_up_question_answer)

    # 检查文件是否存在，如果存在则读取现有内容
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r+', encoding='utf-8') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    # 确保现有数据是一个字典
    if not isinstance(existing_data, dict):
        existing_data = {}

    # 确定新的键名
    counter = 1
    new_key = f"Follow_Up_Question_{counter}"
    while new_key in existing_data:
        if all(k in existing_data[new_key] for k in ['Question', 'Answer', 'Confidence']):
            counter += 1
            new_key = f"Follow_Up_Question_{counter}"
        else:
            break

    # 删除已有的Follow_Up_Question_{counter}键
    existing_data.pop(f"Follow_Up_Question_{counter}", None)


    # 修改键名
    complete_json_follow_up_question_answer = {
        new_key: complete_json_follow_up_question_answer["Follow_Up_Question_Generation"]
    }

    # 追加新生成的问题
    existing_data.update(complete_json_follow_up_question_answer)

    # 保存更新后的内容到文件
    with open(output_file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    # print("Follow-up question has been generated and saved successfully.")
    return new_key, complete_json_follow_up_question_answer[new_key]["Question"]





















# ------------------------------- #
# Prompts for Validator
# 我能理解这个的作用是判断当前的
# ------------------------------- #



# 分析结果并提取yes或no

def analyze_string_yes_no(answer):
    # 去除标点符号，并转换为小写
    answer = re.sub(r'[^\w\s]', '', answer).lower()
    words = answer.split()
    
    # 如果只有一个单词，并且是 "yes" 或 "no"
    if len(words) == 1 and (words[0] == "yes" or words[0] == "no"):
        return words[0]
    else:
        return "neither"




def get_validator_result(Claim, Video_information, QA_CONTEXTS):
    # 生成prompt
    # prompt_for_validator = f"""
    # {{
    # "Claim": "{Claim}",
    # "Video_information": {Video_information},
    # "QA_CONTEXTS": {QA_CONTEXTS},
    # "Task": "Based on the QA_CONTEXTS, is there enough information to determine if the Claim is true or false? Answer only with 'yes' or 'no'. A 'yes' indicates that the Question_Answer pair is valuable for verifying the Claim's accuracy, while a 'no' indicates that it is not valuable."
    # }}
    # Answer only with 'yes' or 'no'. A 'yes' indicates that the Question_Answer pair is valuable for verifying the Claim's accuracy, while a 'no' indicates that it is not valuable.
    # Answer only one word 'yes' or' no '
    # Answer only one word 'yes' or' no '
    # """

    prompt_for_validator = f"""
{{
    "Claim": "{Claim}",
    "Video_information": {Video_information},
    "QA_CONTEXTS": {QA_CONTEXTS},
    "Task": "Based on the QA_CONTEXTS, is there enough information to determine if the Claim is true or false? Answer only with 'yes' or 'no'. A 'yes' indicates that the Question_Answer pair is valuable for verifying the Claim's accuracy, while a 'no' indicates that it is not valuable.",
    "Examples": [
        {{
            "Claim": "A video that went viral in August 2023 showed a beach party in Kyiv, proving that the war in Ukraine is a hoax.",
            "Video_information": {{
                "Video_headline": "Stew Peters - The war in Ukraine is FAKE.",
                "Video_transcript": "",
                "Video_description": "The war in Ukraine is FAKE. https://t.co/l63GG7oUTl",
                "Video_platform": "twitter",
                "Video_date": "2023_08_07",
                "Video_description_from_descriptor": "The video clip is a mix-up, which shows a beach party with clips and photos of many boys and girls, drinks and beach umbrellas. It seems to happen on a daytime with lots of sunshine. It is hard to determine the location of party from the video pictures or contents."
            }},
            "QA_CONTEXTS": {{
                "Question 1": "Is there a beach party in Kyiv on or around the date of the video (Aug. 7, 2023)?",
                "Answer 1": "Yes, there was indeed a beach party in Kyiv on August 6, 2023. The event, held at a local beach club, drew attention and was documented in online posts and social media, highlighting the Ukrainians' efforts to maintain some semblance of normalcy despite the ongoing war.",
                "Question 2": "Are there credible reports or evidence of continued conflict or other significant events in Ukraine on or around the date of the video (August 7, 2023)?",
                "Answer 2": "Yes"
            }},
            "Task": "Based on the QA_CONTEXTS, is there enough information to determine if the Claim is true or false? Answer only with 'yes' or 'no'. A 'yes' indicates that the Question_Answer pair is valuable for verifying the Claim's accuracy, while a 'no' indicates that it is not valuable.",
            "Prediction": "yes"
        }}
    ],
    "Prediction": ""
}}

Answer only with 'yes' or 'no'. A 'yes' indicates that the Question_Answer pair is valuable for verifying the Claim's accuracy, while a 'no' indicates that it is not valuable.
Answer only one word 'yes' or' no '
Answer only one word 'yes' or' no '
"""


    # 初始化循环次数
    max_attempts = 5
    attempts = 0
    
    while attempts < max_attempts:
        # 调用模型分析并获取答案
        answer = gpt35_analysis(prompt_for_validator)
        
        # 获取最终的yes或no结果
        final_result = analyze_string_yes_no(answer)

        logging.info("validator_result")
        logging.info(answer)
        logging.info(final_result)
        
        if final_result == "yes":
            return True
        elif final_result == "no":
            return False
        else:
            attempts += 1
    
    # 如果循环达到最大次数，返回False
    return False

















def validate_json_structure(json_data):
    # 验证JSON结构是否符合预期格式
    if not isinstance(json_data, dict):
        return False

    final_judgement = json_data.get("Final_Judgement")
    if not final_judgement:
        return False

    answer = final_judgement.get("Answer")
    reasons = final_judgement.get("Reasons")
    claim_authenticity = final_judgement.get("Therefore, the Claim authenticity is")
    info_type = final_judgement.get("The information type is")

    if answer == "True":
        return reasons and claim_authenticity == "True" and info_type == "Real" and "The specific type of False Information is" not in final_judgement

    if answer == "False":
        false_info_type = final_judgement.get("The specific type of False Information is")
        return reasons and claim_authenticity == "False" and info_type == "False" and false_info_type

    return False

# ------------------------------- #
# Prompts for Reasoner
# ------------------------------- #


def process_claim_final(Claim, Video_information, QA_CONTEXTS, output_file_path):
    # Prompts for Reasoner
    prompt_for_reasoner = f"""
{{
  "Claim": "{Claim}",
  "Video_information": {Video_information},
  "QA_CONTEXTS": {QA_CONTEXTS},
  "Task": "Is this Claim true or false? And which information type does it belong to: Real, Unverified, Outdated, or False? If 'False,' specify the type: False video description, Video Clip Edit, Computer-generated Imagery, False speech, Staged Video, Text-Video Contradictory, Text unsupported by the video. Please provide your reasoning process. Ensure the final answer addresses all the following aspects: Answer, Reasons, Therefore, the Claim authenticity is, The information type is, If it is false, the specific type of False Information is.",
  "Output_Answer_Format": {{
    "Answer": "",
    "Reasons": "",
    "Therefore, the Claim authenticity is": "",
    "The information type is": "",
    "If it is false, the specific type of False Information is": ""
  }},
  "Please Note": "Make sure to address Answer, Reasons, Therefore, the Claim authenticity is, The information type is, If it is false, the specific type of False Information is."
}}
"""


   
    answer = gpt35_analysis(prompt_for_reasoner)

    attempt = 0
    max_attempts = 3
    true_json_answer = {}

    while attempt < max_attempts:
        attempt += 1
        answer = gpt35_analysis(prompt_for_reasoner)

        # 格式化初始问题生成的提示
        prompt_for_format = f"""
        Please convert the following text content into the specified JSON structure. Ensure the output is in JSON format and maintain the original content as much as possible, changing only the structure to the specified JSON format.

        First, determine whether the claim is True or False.

        For True claims, use the following JSON structure:
        {{
        "Final_Judgement": {{
        "Answer": "True",
        "Reasons": "{{{{reasons}}}}",
        "Therefore, the Claim authenticity is": "True",
        "The information type is": "Real"
        }}
        }}

        For False claims, use the following JSON structure:
        {{
        "Final_Judgement": {{
        "Answer": "False",
        "Reasons": "{{{{reasons}}}}",
        "Therefore, the Claim authenticity is": "False",
        "The information type is": "False",
        "The specific type of False Information is": "{{{{false_info_type}}}}"
        }}
        }}

        If the claim is False, please choose the specific type of False Information from the following options:
        False video description, Video Clip Edit, Computer-generated Imagery, False speech, Staged Video, Text-Video Contradictory, Text unsupported by the video, Other.

        Content to be converted:
        {answer}

        Please Note: The final task is to first determine the authenticity of the claim. If it is True, only the "Reasons" field needs to be filled. If it is False, the "Reasons" field should be filled, and the "The specific type of False Information" field should be selected.
        """

        # 使用 gpt35_analysis 将结果转换为 JSON 格式
        json_answer = gpt35_analysis(prompt_for_format)
        true_json_answer = extract_complete_json(json_answer)

        # 检查提取和验证是否成功
        if validate_json_structure(true_json_answer):
            break



    # 确保文件是字典结构而不是列表
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r+') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    # 确保现有数据是一个字典
    if not isinstance(existing_data, dict):
        existing_data = {}

    # 追加新生成的数据
    existing_data.update(true_json_answer)

    # 保存更新后的内容到文件
    with open(output_file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    logging.info("声明处理结果已生成并成功保存。")

    # 返回处理结果
    return true_json_answer



