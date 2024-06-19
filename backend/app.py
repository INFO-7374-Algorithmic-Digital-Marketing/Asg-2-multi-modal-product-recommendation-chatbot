from fastapi import FastAPI
import llm_layer
import mongo_db_interface as mdb

app = FastAPI()

@app.post("/search_similar")
async def search_similar(prompt: str):
    intent = llm_layer.__check_intent_with_gpt(prompt)
    if intent == "normal_chat":
        response = llm_layer.normal_chat(prompt)
        return {"response": response}

    elif intent == "show_similar":
        N, category = llm_layer.extract_details_from_prompt(prompt)
        search_results = mdb.image_search(mdb.encode_text(prompt), N)
        metadata = [str(mdb.extract_fields_from_document(mdb.get_document_by_id(search_results[i]["_id"]))) for i in range(N)]
        response = llm_layer.gpt_response_similar(prompt, metadata)
        return {"response": response}





