from openai import OpenAI
import numpy as np
import json
import requests
import logging
import matplotlib.pyplot as plt
import json
import requests
import torch
from PIL import Image
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI()

def normal_chat(prompt):
    logger.info(f"Normal chat detected. Responding with the same prompt.")
    # Later change this to a proper response
    return prompt

def extract_n_category_prompt(prompt):
    logger.info(f"Extracting details from prompt: {prompt}")
    prompt=f"Extract the number of similar images (N) and the category from the following prompt: '{prompt}'. If not sure about the category, default to 'all'. If not sure about the number of images, default to 3. Return response in strictly json format with keys 'N' and 'category'.",
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"{prompt}"}
        ]
    )
    return response.choices[0].message.content

def extract_details_from_prompt(prompt):
    logger.info(f"Extracting details from prompt: {prompt}")
    try:
        details = extract_n_category_prompt(prompt)
        logger.info(f"Received response from OpenAI: {details}")
        details_json = json.loads(details)
        N = int(details_json.get("N", 3))
        category = details_json.get("category", "all")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        N, category = 3, "all"
    except Exception as e:
        logger.error(f"Error in extracting details: {e}")
        N, category = 3, "all"
    logger.info(f"Extracted details - N: {N}, category: {category}")
    return N, category


def __check_intent_with_gpt(user_input):
    prompt = (
        "You are an AI assistant. A user is interacting with a chatbot. "
        "Based on the user's input, identify if the user is engaging in normal chat, "
        "asking to show similar images, or asking for complementary items.\n\n"
        "User input: " + user_input + "\n\n"
        "Identify the intent as one of the following: normal_chat, show_similar, show_complementary. "
        "Respond with the intent in the following JSON format: {\"intent\": \"<intent>\"}"
    )
    logger.info(f"Extracting intent from prompt: {prompt}")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[  
            {"role": "user", "content": f"{prompt}"}
        ]
    )
    logger.info(f"Received response from OpenAI: {response.choices[0].message.content}")
    intent = response.choices[0].message.content
    intent_json = json.loads(intent)
    intent = intent_json.get("intent")
    return intent

def __gpt_response(prompt):
    logger.info(f"Generating response for prompt: {prompt}")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"{prompt}"}
        ]
    )
    
    return response.choices[0].message.content

def gpt_response_similar(user_prompt, metadata):
    similar_prompt = f'''You are a chatbot assistant. A user is interacting with you and 
                        has asked you to show similar products using this prompt {user_prompt}. 
                        Following is the details of the recomended products {metadata}. 
                        Use this information and generate a chat reposnse'''


    return __gpt_response(similar_prompt)


# def determine_intent(user_input):
#     # First layer: Keyword matching
#     intent = __check_intent_with_keywords(user_input)
#     logger.info(f"Intent from keyword matching: {intent}")
    
#     # Second layer: If no intent found, use GPT-3.5
#     if intent is None:
#         intent = __check_intent_with_gpt(user_input)
#         intent_json = json.loads(intent)
    
#     return intent
