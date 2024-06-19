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