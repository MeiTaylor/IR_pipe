import json
import requests
import re

import logging
import os
import sys
import regex
import traceback

from CV_relate_code import *
# from InformationRetriever import information_retriever_complete
# from IR1 import *

from IR2 import *


logging.basicConfig(filename='claim_verifer.log', level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')









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





































CV_output_file_path = "/workspaces/IR_pipe/zero_shot_llmfnd/CV_result.json"



# Claim = "A video that went viral in August 2023 showed a beach party in Kyiv, proving that the war in Ukraine is a hoax."

# Video_information = {
#     "Video_headline": "Is This An Authentic Video from a Beach Party in Kyiv in August 2023? | Snopes.com",
#     "Video_transcript": "",
#     "Video_description_on_platform": "This video clip is used in a fact-check article on Snopes.com. Visit the website for more details.",
#     "Video_platform": "youtube",
#     "Video_date": "2023_08_07",
#     "Video_description_from_descriptor": ("The video clip is a mix-up, which shows a beach party with clips and photos of many boys and girls, "
#                                          "drinks and beach umbrellas. It seems to happen on a daytime with lots of sunshine. "
#                                          "It is hard to determine the location of party from the video pictures or contents.")
# }

# QA_CONTEXTS = {}

# # # # # 46506212
# Claim = "A video that went viral in August 2023 showed a beach party in Kyiv, proving that the war in Ukraine is a hoax."
# Video_information = {
#     "Video_description_from_descriptor": "The video captures scenes from a beach club setting, presumably in Kyiv during a time of war, juxtaposing the leisurely atmosphere of the pool party with the underlying tensions of the conflict. The video begins with a man walking on a serene beach, followed by a scene featuring a group of people relaxing on the beach in a beach club setting. The camera then focuses on a man preparing a drink before shifting to a couple enjoying the beach ambiance. Subsequently, the frame transitions to another man engaging in drink preparation. The key frame highlights consist of several snapshots showcasing a beach club in Kyiv during a war. These frames capture a bustling atmosphere with people sunbathing, lounging, and socializing amidst the backdrop of conflict. Scenes include individuals in swimwear, lounging by a pool and under white umbrellas, enjoying a leisurely time despite the mention of war in the captions."
# }
# QA_CONTEXTS = {}



# # # # # 46591501
# Claim = "A video shows North Korean leader Kim Jong Un and Russian President Vladimir Putin toasting each other then placing their drinks on the table without consuming them."
# Video_information = {
#     "Video_description_from_descriptor": "The video opens with a man in a black suit standing at a podium, holding a glass of wine, and appearing to deliver a speech or presentation in a formal setting with blue curtains in the background. The focus then shifts to another man in a suit standing at a table, also holding a glass of wine and giving a speech at the same event. Throughout the video, the man in the black suit with the wine glass remains the central figure, although both men are speaking. The scenes depict interactions between the individuals, highlighting moments of toasting and gestures with the glasses of wine. The setting suggests a formal event or ceremony, with microphone setups on the tables indicating a structured gathering. The key frames capture various interactions between the two men, showcasing subtle moments of trust issues or skepticism humorously referenced in the captions. These moments include both men holding glasses of what is presumed to be champagne, engaging in dialogue or gestures, and maintaining a serious demeanor. The occurrences culminate with the man in the black suit finishing his speech, implying a conclusion to the event or presentation. Overall, the video portrays a sequence of formal interactions and speeches at an organized function, emphasizing the dynamic between the two suited men through moments of raising glasses and engaging in speech delivery."
# }
# QA_CONTEXTS = {}


# # # 46512203
# Claim = "Online video showed U.S. President Donald Trump visiting Maui in the aftermath of the August 2023 wildfires."
# Video_information = {
#     "Video_description_from_descriptor": "The video captures scenes of volunteers engaging in post-hurricane cleanup efforts, emphasizing community resilience and support. President Trump is featured delivering a speech, instilling a sense of unity and encouragement among the volunteers. Key frames display social media posts with messages like 'A Real President Truly cares' and '#TRUMP2024', as well as images of individuals surrounded by supportive crowds, reinforcing themes of care, patriotism, and collective action. The visuals highlight the spirit of volunteerism and public service, intertwining with political messaging promoting a specific candidacy for the presidency. The juxtaposition of disaster response, political discourse, and online engagement underscores a multifaceted narrative of civic duty, leadership, and social media advocacy within the context of post-disaster recovery efforts."
# }
# QA_CONTEXTS = {}



# 46592810
Claim = "A viral video shared in January 2023 authentically shows young girls in a house on Jeffrey Epstein's island."
Video_information = {
    "Video_description_from_descriptor": "The video primarily centers around a little girl playing with a dog in a bathtub. The key frame highlights provide glimpses into various indoor settings, potentially a spa or bathhouse, featuring large pillars, checkered floors, and different individuals in the background. One key frame captures the young child interacting near a sink, another shows the girl in a bikini holding a teddy bear amidst other children and a unique circular platform, and yet another displays luxurious indoor surroundings with two women engaged in pouring liquid into a bowl. The images consistently depict intricate architectural details, including pillars and distinct floor patterns, hinting at a high-end or exotic location where the playful interactions unfold between the girl and her surroundings."
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
    # logging.info("process_claim_verifier result - Judgment: %s, Confidence: %s", judgment, confidence)

    # 判断是否需要生成问题
    # 如果 judgment 为 true，并且 confidence >= 0.9 才不需要生成问题，其余的情况都需要生成问题
    if_generate_question = not (judgment and confidence >= 0.9)

    logging.warning("\n" * 5)
    logging.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    logging.info("!!!!!!!!!! Processing Initial Question !!!!!!!!!!")
    logging.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    logging.warning("\n" * 5)


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
                # logging.info("Generated Initial Question: %s", question)

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
    while if_generate_question:
                
        new_QA_CONTEXTS = extract_qa_contexts(CV_output_file_path)

        # 调用 process_claim_verifier 函数
        new_judgment, new_confidence = process_claim_verifier(Claim, Video_information, new_QA_CONTEXTS, CV_output_file_path)
        logging.info("New process_claim_verifier result - Judgment: %s, Confidence: %s", new_judgment, new_confidence)

        # 如果 new_judgment 为 true，并且 new_confidence >= 0.91 才不需要生成问题，其余的情况都需要生成问题
        if new_judgment and new_confidence >= 0.9:
            break


        if new_question_count >= 3:
            break

        logging.warning("\n" * 5)
        logging.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        logging.info("!!!!!!!!!! Processing question #%d !!!!!!!!!!", new_question_count)
        logging.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        logging.warning("\n" * 5)





        new_question_count += 1


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
