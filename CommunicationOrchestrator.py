from fastapi import FastAPI
from pydantic import BaseModel
import json
import os
import requests
from dotenv import load_dotenv

app = FastAPI()

class ReplacementOffer(BaseModel):
    fromm: dict
    to: str

# Load JSON
with open('UnfulfilledOrderInfoTest.json') as f:
    data = json.load(f)

# Called to pass data
@app.post("post_item")
async def post_item(BaseModel):

    with open(BaseModel) as f:
        data = json.load(f)


    # Validate and parse to local format
    order = ReplacementOffer.model_validate(data)  
    print(order)
    print(order.to)
    
    # send message to client askng if they need substitutiion for the product
    # get responce, Yes or No
    response = "So man I don't now, maybe yeah, yeah this 2 procent should be fine. I will go with 2 procent milk box."  # Placeholder for actual response handling
    
    url = "http://localhost:5000/nlu/parse"
    
    payload = {
        "text": text
    }

    response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
    # return the json format

    return {
        "decisions": [
        { "lineId": 1, "action": "REPLACE", "replacementQty": 4.0 },
        { "lineId": 13, "action": "KEEP" },
        { "lineId": 2, "action": "DELETE" }
        ]
    }

@app.get("get_item")
async def get_item(id: int):

    if item:
        return item
    return {"error": "Item not found"}, 404