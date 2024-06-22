import streamlit as st
import requests
import os
import hashlib
import json
import logging
from typing import Dict, Any, Optional, BinaryIO
from google.cloud import storage
from dotenv import load_dotenv
from langchain.chains.openai_functions.openapi import get_openapi_chain
from langchain_openai import ChatOpenAI
from streamlit_lottie import st_lottie

# Constants
UPLOAD_FOLDER = "uploads"
OPENAPI_URL = "http://127.0.0.1:8000/openapi.json"
API_BASE_URL = "http://127.0.0.1:8000"

# Load environment variables and set up logging
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BUCKET_NAME = os.getenv('BUCKET_NAME')


# Add this function to load Lottie animations
def load_lottieurl(url: str) -> Optional[Dict[str, Any]]:
    """Load a Lottie animation from a URL."""
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        logger.error(f"Error loading Lottie animation: {e}")
        return None


def upload_blob(source_file_name: str, destination_blob_name: str, bucket_name: str = BUCKET_NAME) -> Optional[str]:
    """Uploads a file to Google Cloud Storage and returns its public URL."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_name, if_generation_match=0)
        logger.info(f"File {source_file_name} uploaded to {destination_blob_name}.")
        
        blob.make_public()
        return blob.public_url
    except Exception as e:
        logger.error(f"Error uploading file to GCS: {e}")
        return None

async def fetch_openapi_spec(url: str) -> Dict[str, Any]:
    """Fetches the OpenAPI specification from the given URL."""
    response = await requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch OpenAPI JSON. Status code: {response.status_code}")
    return response.json()

async def send_to_api(prompt: str, file_url: Optional[str] = None) -> Dict[str, Any]:
    """Sends a prompt to the API and returns the response."""
    try:
        llm = ChatOpenAI()
        openapi_spec_json = await fetch_openapi_spec(OPENAPI_URL)
        
        if "servers" not in openapi_spec_json:
            openapi_spec_json["servers"] = [{"url": API_BASE_URL}]
        else:
            openapi_spec_json["servers"].append({"url": API_BASE_URL})
        
        chain = get_openapi_chain(spec=openapi_spec_json, llm=llm)
        query = f"{prompt} For the following image: {file_url}" if file_url else prompt
        response = await chain(query)
        
        return response
    except Exception as e:
        logger.error(f"Error sending prompt to API: {e}")
        return {"error": str(e)}

def compute_file_hash(file: BinaryIO) -> str:
    """Computes MD5 hash of the given file."""
    hasher = hashlib.md5()
    for chunk in iter(lambda: file.read(4096), b""):
        hasher.update(chunk)
    file.seek(0)
    return hasher.hexdigest()

def save_uploaded_file(uploaded_file) -> Optional[str]:
    """Saves the uploaded file and returns its public URL."""
    file_hash = compute_file_hash(uploaded_file)
    
    if file_hash in st.session_state.file_hashes:
        return st.session_state.file_hashes[file_hash]
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    destination_blob_name = f"{UPLOAD_FOLDER}/{file_hash}_{uploaded_file.name}"
    public_url = upload_blob(file_path, destination_blob_name)
    
    if public_url:
        st.session_state.file_hashes[file_hash] = public_url
    
    return public_url

def show_upload(state: bool):
    """Sets the visibility state of the file uploader."""
    st.session_state["uploader_visible"] = state

def display_results():
    """Displays the results of the API query with improved formatting and animations."""
    if st.session_state.results:
        st.write("## Results")
        
        # Load and display a Lottie animation
        lottie_url = "https://assets9.lottiefiles.com/packages/lf20_8J3yk8.json"  # You can change this URL to any Lottie animation you prefer
        lottie_json = load_lottieurl(lottie_url)
        if lottie_json:
            st_lottie(lottie_json, speed=1, height=200, key="lottie")

        for idx, item_dict in enumerate(st.session_state.results, 1):
            with st.container():
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.image(item_dict['thumbnailImages'][0]['imageUrl'], use_column_width=True)
                
                with col2:
                    st.subheader(f"{idx}. {item_dict['title']}")
                    st.markdown(f"**Price:** {item_dict['price']['value']} {item_dict['price']['currency']}")
                    st.markdown(f"**Condition:** {item_dict['condition']}")
                    st.markdown(f"**Category:** {item_dict['categories'][0]['categoryName']}")
                    
                    # Add a "View Details" expander for additional information
                    with st.expander("View Details"):
                        st.json(item_dict)  # Display all item details in JSON format
                
            st.markdown("---")  # Add a separator between items
    else:
        st.info("No results to display yet. Try asking a question like Show me N pictures of Centerpieces or Upload an image and we'll show similar ones from our store!")



# Show me 4 examples of plates with floral design
# Can I see 6 more tables like this one !
# I want to checkout 4 variations of wooden dining tables
