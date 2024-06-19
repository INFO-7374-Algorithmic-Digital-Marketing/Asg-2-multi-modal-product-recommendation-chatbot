import os
from PIL import Image
from io import BytesIO
from tqdm import tqdm
from dotenv import load_dotenv
from bson.objectid import ObjectId

# Function to vector search the images
from urllib.parse import quote_plus
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import CollectionInvalid, DuplicateKeyError
from pymongo.operations import SearchIndexModel
from sentence_transformers import SentenceTransformer

load_dotenv()

mongo_db_user = quote_plus(os.getenv('MONGO_DB_USER'))
mongo_db_password = quote_plus(os.getenv('MONGO_DB_PASSWORD'))
mongo_db_name = os.getenv('MONGO_DB_NAME')
collection_name = os.environ.get('MONGO_COLLECTION_NAME')
uri = f"mongodb+srv://{mongo_db_user}:{mongo_db_password}@cluster0.eld31uu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
model = SentenceTransformer("clip-ViT-L-14")


# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.get_database(mongo_db_name)
collection = db.get_collection(collection_name)


def encode_image(image_path):
    image = Image.open(image_path)
    encoding = model.encode([image])
    return encoding[0]

def encode_text(text):
    encoding = model.encode(text)
    return encoding

def image_search(emb, n = 9, collection=collection):
    """
    Use MongoDB Vector Search to search for a matching image.
    The `search_phrase` is first converted to a vector embedding using
    the `model` loaded earlier in the Jupyter notebook. The vector is then used
    to search MongoDB for matching images.
    """
    # emb = model.encode(search_phrase)
    cursor = collection.aggregate(
        [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": emb.tolist(),
                    "numCandidates": 100,
                    "limit": n,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
        ]
    )

    return list(cursor)

def get_document_by_id(doc_id, collection=collection): 
    """
    Retrieve a MongoDB document by its _id and return all its fields as a dictionary.
    """
    document = collection.find_one({"_id": doc_id})
    return document

def extract_fields_from_document(document, fields = ["title", "categories", "price", "thumbnailImages", "condition"]):
    """
    Extract the fields 'title', 'description', 'category', 'image_url' from the MongoDB document.
    """
    return {field: document.get(field) for field in fields}