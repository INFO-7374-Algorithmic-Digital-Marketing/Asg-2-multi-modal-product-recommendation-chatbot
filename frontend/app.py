import streamlit as st
import requests
import os
import time
from langchain.chains.openai_functions.openapi import get_openapi_chain
from langchain_openai import ChatOpenAI
import json
import logging
from google.cloud import storage
from dotenv import load_dotenv
import hashlib
import streamlit as st
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from frontend_utils import (
    show_upload,
    save_uploaded_file,
    send_to_api,
    display_results
)

# Load environment variables
load_dotenv()

api_host = os.getenv('API_HOST')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Cloud Storage configuration
bucket_name = os.getenv('BUCKET_NAME')

def upload_blob(source_file_name, destination_blob_name, bucket_name=bucket_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    generation_match_precondition = 0

    blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")
   
    blob.make_public()

    # Return the public URL of the uploaded file
    return blob.public_url

def send_to_api(prompt, file_url=None):
    logger.info(f"Sending prompt to API: {prompt}")
    # Create the LLM instance
    llm = ChatOpenAI()
    # URL of the local FastAPI OpenAPI documentation
    # for local testing 
    # openapi_url = "http://127.0.0.1:8000/openapi.json"

    # once docker compose is up and running
    # openapi_url = "http://backend:8000/openapi.json"
    openapi_url = f"{api_host}/openapi.json"
    # Fetch the OpenAPI spec to ensure it's accessible
    def fetch_openapi_spec(url):
        response = requests.get(url)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch OpenAPI JSON. Status code: {response.status_code}")
        return response.json()
    try:
        openapi_spec_json = fetch_openapi_spec(openapi_url)
        # Manually add the base URL to the OpenAPI spec
        # base_url = "http://backend:8000"
        base_url = api_host
        if "servers" not in openapi_spec_json:
            openapi_spec_json["servers"] = [{"url": base_url}]
        else:
            openapi_spec_json["servers"].append({"url": base_url})
        # Save the updated OpenAPI spec to a temporary file
        with open("updated_openapi.json", "w") as f:
            json.dump(openapi_spec_json, f)
        # Create the chain using the updated OpenAPI spec file
        chain = get_openapi_chain(spec="updated_openapi.json", llm=llm)
        # Example query to the /search_similar endpoint
        query = prompt
        if file_url:
            query = query + f" For the following image: {file_url}"
        response = chain(query)
        return response
    except Exception as e:
        return f"Error: {e}"

def compute_file_hash(file):
    hasher = hashlib.md5()
    for chunk in iter(lambda: file.read(4096), b""):
        hasher.update(chunk)
    file.seek(0)  # Reset file pointer to the beginning
    return hasher.hexdigest()

def save_uploaded_file(uploaded_file):
    file_hash = compute_file_hash(uploaded_file)
    
    # Check if this file has been uploaded before
    if file_hash in st.session_state.file_hashes:
        return st.session_state.file_hashes[file_hash]
    
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    file_path = os.path.join("uploads", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Upload to Google Cloud Storage and get the public URL
    destination_blob_name = f"uploads/{file_hash}_{uploaded_file.name}"
    public_url = upload_blob(file_path, destination_blob_name)
    
    # Store the hash and URL
    st.session_state.file_hashes[file_hash] = public_url
    
    return public_url

def main():
    st.set_page_config(page_title="DineDecor AI", layout="wide")

    # Custom CSS
    st.markdown("""
        <style>
        .stApp {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
        }
        .stTextInput>div>div>input {
            background-color: #2C2C2C;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

    # Main header
    colored_header(
        label="DineDecor AI",
        description="Your Personal Dining Room Design Assistant",
        color_name="blue-70"
    )

    add_vertical_space(2)

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "file_url" not in st.session_state:
        st.session_state.file_url = None
    if "file_hashes" not in st.session_state:
        st.session_state.file_hashes = {}
    if "uploader_visible" not in st.session_state:
        st.session_state.uploader_visible = False
    if "results" not in st.session_state:
        st.session_state.results = []

    # File upload option
    with st.chat_message("system"):
        cols = st.columns((3, 1, 1))
        cols[0].write("Do you want to upload a file?")
        cols[1].button("Yes", use_container_width=True, on_click=show_upload, args=[True])
        cols[2].button("No", use_container_width=True, on_click=show_upload, args=[False])

    # File uploader functionality
    if st.session_state["uploader_visible"]:
        uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "gif"])
        if uploaded_file:
            with st.spinner("Processing your file"):
                new_file_url = save_uploaded_file(uploaded_file)
                if new_file_url != st.session_state.file_url:
                    st.session_state.file_url = new_file_url
                    st.success(f"File uploaded: {uploaded_file.name}")
                else:
                    st.info(f"This image has been uploaded before. Using existing URL.")
                st.write(f"Image URL: {st.session_state.file_url}")

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Display existing results
    display_results()

    # Accept user input
    if prompt := st.chat_input("What is your question?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            response = send_to_api(prompt, st.session_state.file_url)
            if isinstance(response, dict) and 'response' in response:
                try:
                    items = response['response']['response']
                    new_results = []
                    for item in items:
                        item_dict = eval(item)  # Be cautious with eval, use only with trusted data
                        new_results.append(item_dict)
                    st.session_state.results.extend(new_results)
                    
                    display_results()
                except Exception as e:
                    st.write(response['response'])
            else:
                st.write(response)

        st.session_state.messages.append({"role": "assistant", "content": "I've provided the results based on your query. You can see them displayed above."})
        st.session_state.file_url = None

    # Clear results button
    if st.button("Clear Results"):
        st.session_state.results = []
        st.rerun()

if __name__ == "__main__":
    main()