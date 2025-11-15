from fastapi import FastAPI
from pydantic import BaseModel
import json

app = FastAPI()

class AbsentItemOrder(BaseModel):
    clientName: str
    absentItem: str

# Load JSON
with open('UnfulfilledOrderInfoTest.json') as f:
    data = json.load(f)

# Validate and parse
order1 = AbsentItemOrder.model_validate(data)  # v2

print(order1)
print(order1.clientName)


@app.post("post_item")
async def post_item():
    
    return item

@app.get("get_item")
async def get_item(id: int):

    if item:
        return item
    return {"error": "Item not found"}, 404