# Delete all items in a collection
result = collection.delete_many({})

# Vector Search Index Defination
{
  "fields": [
    {
      "numDimensions": 768,
      "path": "plot_embedding",
      "similarity": "cosine",
      "type": "vector"
    }
  ]
}

## run the api
uvicorn app:app --reload

## Kill pid at 8000
kill $(lsof -t -i:8000)