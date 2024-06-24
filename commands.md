# Delete all items in a collection
result = collection.delete_many({})

# Vector Search Index Defination
{
  "fields": [
    {
      "numDimensions": 768,
      "path": "embedding",
      "similarity": "cosine",
      "type": "vector"
    }
  ]
}

# Text Search Defination
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "categories": {
        "fields": {
          "categoryName": {
            "type": "string"
          }
        },
        "type": "document"
      }
    }
  }
}

## run the api
uvicorn app:app --reload