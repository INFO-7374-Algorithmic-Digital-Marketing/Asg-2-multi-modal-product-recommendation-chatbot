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

def encode_image_from_bytes(image_data):
    image = Image.open(BytesIO(image_data))
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

def hybrid_search(emb, category_name, n=9, vector_penalty=1.0, full_text_penalty=0.01):
    """
    Perform a hybrid search using both vector search and full-text search.
    The `emb` parameter is the vector embedding of the query.
    The `category_name` is the category to search for using full-text search.
    The `vector_penalty` and `full_text_penalty` are used to control the influence of each search method.
    """

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": emb.tolist(),
                "numCandidates": 100,
                "limit": 20
            }
        },
        {
            "$group": {
                "_id": None,
                "docs": { "$push": "$$ROOT" }
            }
        },
        {
            "$unwind": {
                "path": "$docs",
                "includeArrayIndex": "rank"
            }
        },
        {
            "$addFields": {
                "vs_score": {
                    "$divide": [1.0, { "$add": ["$rank", vector_penalty, 1] }]
                }
            }
        },
        {
            "$project": {
                "vs_score": 1,
                "_id": "$docs._id",
                "title": "$docs.title",
                "categories": "$docs.categories",
                "final_category": "$docs.final_category"
            }
        },
        {
            "$unionWith": {
                "coll": "dining_products_cat",  # Replace with your actual collection name
                "pipeline": [
                    {
                        "$search": {
                            "index": "default",
                            "text": {
                                "query": category_name,
                                "path": "final_category"
                            }
                        }
                    },
                    {
                        "$limit": 20
                    },
                    {
                        "$group": {
                        "_id": None,
                        "docs": { "$push": "$$ROOT" }
                        }
                    },
                    {
                        "$unwind": {
                            "path": "$docs",
                            "includeArrayIndex": "rank"
                        }
                    },
                    {
                        "$addFields": {
                            "fts_score": {
                                "$divide": [1.0, { "$add": ["$rank", full_text_penalty, 1] }]
                            }
                        }
                    },
                    {
                        "$project": {
                            "fts_score": 1,
                            "_id": "$docs._id",
                            "title": "$docs.title",
                            "categories": "$docs.categories",
                            "final_category": "$docs.final_category"
                        }
                    }
                ]
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "vs_score": { "$max": "$vs_score" },
                "fts_score": { "$max": "$fts_score" },
                "categories": { "$first": "$categories" },
                "title": { "$first": "$title" },
                "final_category": { "$first": "$final_category" }
            }
        },
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "vs_score": { "$ifNull": ["$vs_score", 0] },
                "fts_score": { "$ifNull": ["$fts_score", 0] },
                "categories": 1,
                "final_category": 1
            }
        },
        {
            "$project": {
                "score": { "$add": ["$fts_score", "$vs_score"] },
                "_id": 1,
                "title": 1,
                "vs_score": 1,
                "fts_score": 1,
                "categories": 1,
                "final_category": 1
            }
        },
        {
            "$sort": { "score": -1 }
        },
        {
            "$limit": n
        }
    ]

    # Execute the aggregation pipeline
    results = list(collection.aggregate(pipeline))

    # Print the results
    for result in results:
        print(f"ID: {result['_id']}, Title: {result['title']}, VS Score: {result['vs_score']}, FTS Score: {result['fts_score']}, Categories: {result['categories']}, Final Category: {result['final_category']}")

    return results

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