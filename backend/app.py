import requests
import os
from fastapi import FastAPI, UploadFile, File
import logging
import llm_layer
import mongo_db_interface as mdb
from typing import Literal

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting the FastAPI server now...")

app = FastAPI()

@app.post("/search")
async def search(prompt: str, intent: Literal["show_similar", "show_complementary", "normal_chat"], category: Literal["Center_Piece", "Glass_Set", "Dinner_Table", "Cutlery"], num_of_items: int, image_path: str = None):
    logger.info(f"Received request with prompt: {prompt}, intent: {intent}, category: {category}, num_of_items: {num_of_items}, image_path: {image_path}")
    if intent == "normal_chat":
        response = llm_layer.normal_chat(prompt)
        logger.info(f"Generated response: {response}")
        return {"response": response}

    elif intent == "show_similar":
        if not image_path:         
            logger.info(f"Image not provided")
            logger.info(f"Searching for similar images for the prompt: {prompt}")
            # search_results = mdb.image_search(mdb.encode_text(prompt), num_of_items)
            search_results = mdb.hybrid_search(mdb.encode_text(prompt), category, num_of_items, float(os.getenv('VECTOR_PENALTY', 1.0)), float(os.getenv('FULL_TEXT_PENALTY', 1.0))) #Hybrid search
            print(search_results)
            logger.info(f"Found {len(search_results)} search results")  
            metadata = [str(mdb.extract_fields_from_document(mdb.get_document_by_id(search_results[i]["_id"]))) for i in range(num_of_items)]
            logger.info(f"Extracted metadata: {metadata}")
            return {"response": metadata}
        else:
            image = requests.get(image_path).content
            emb = mdb.encode_image_from_bytes(image)
            logger.info(f"Encoded image")
            # search_results = mdb.image_search(emb, num_of_items)
            search_results = mdb.hybrid_search(mdb.encode_text(prompt), category, num_of_items, float(os.getenv('VECTOR_PENALTY_IMAGE', 1.0)), float(os.getenv('FULL_TEXT_PENALTY_IMAGE', 1.0))) #Hybrid search
            # print(search_results)
            logger.info(f"Found {len(search_results)} search results")
            metadata = [str(mdb.extract_fields_from_document(mdb.get_document_by_id(search_results[i]["_id"]))) for i in range(num_of_items)]
            logger.info(f"Extracted metadata: {metadata}")
            return {"response" : metadata}
    elif intent == "show_complementary":
        if not image_path:
            logger.info("Image not provided")
            return {"response": "Didn't detect your image. Please provide an image for complementary suggestions."}
        else:
            image = requests.get(image_path).content
            complementary_text, complementary_category = llm_layer.get_complementary(image_path, prompt)
            logger.info(f"Complementary suggestion: {complementary_text}, Category: {complementary_category}")
            # search_results = mdb.image_search(mdb.encode_text(complementary_text), num_of_items)
            search_results = mdb.hybrid_search(mdb.encode_text(prompt), complementary_category, num_of_items, float(os.getenv('VECTOR_PENALTY', 1.0)), float(os.getenv('FULL_TEXT_PENALTY', 1.0))) #Hybrid search
            logger.info(f"Found {len(search_results)} search results")
            metadata = [str(mdb.extract_fields_from_document(mdb.get_document_by_id(search_results[i]["_id"]))) for i in range(num_of_items)]
            logger.info(f"Extracted metadata: {metadata}")
            return {"response": metadata, "complementary_suggestion": complementary_text, "category": complementary_category}
