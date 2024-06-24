# DineDecor AI

DineDecor AI is a personal dining room design assistant that leverages AI to help users find and visualize complementary decor items for their dining spaces.

![Screenshot 2024-06-22 at 7 40 50 PM](https://github.com/INFO-7374-Algorithmic-Digital-Marketing/multi-modal-product-recommendation-chatbot/assets/37287532/13df19bb-d789-4980-b84d-94aa2e2ebe4b)


## Table of Contents
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

## Features

- Image upload functionality for user's current dining space
- AI-powered suggestions for complementary decor items
- Search for similar products based on user prompts
- Interactive chat interface for user queries
- Display of product details including images, prices, and conditions

## Technologies Used

- Python
- FastAPI
- Streamlit
- OpenAI GPT models
- MongoDB
- Google Cloud Storage
- Sentence Transformers (CLIP model)
- Langchain

## Installation

1. Clone the repository:

```
git clone https://github.com/yourusername/dinedecor-ai.git
cd dinedecor-ai
```

2. Install required packages:

```
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory and add the following:

```
OPENAI_API_KEY=your_openai_api_key
MONGO_DB_USER=your_mongodb_username
MONGO_DB_PASSWORD=your_mongodb_password
MONGO_DB_NAME=your_database_name
MONGO_COLLECTION_NAME=your_collection_name
BUCKET_NAME=your_gcs_bucket_name
```

## Usage

1. Start the FastAPI backend:
```
uvicorn main:app --reload
```

![Screenshot 2024-06-22 at 7 40 20 PM](https://github.com/INFO-7374-Algorithmic-Digital-Marketing/multi-modal-product-recommendation-chatbot/assets/37287532/5924e355-a72c-4c1e-9bdd-e8950f0221fa)

2. Run the Streamlit frontend:
```
streamlit run frontend.py
```

3. Open your web browser and navigate to the provided local URL.

## API Endpoints

- `/search`: POST request to search for similar or complementary items based on user input and images.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the [MIT License](LICENSE).
This README provides a basic structure and information about your project. You may want to add or modify sections based on specific details of your project, such as:
