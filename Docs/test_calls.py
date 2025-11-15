import requests

baseURL = "http://127.0.0.1:8000"

# POST
payload = {"id": 1, "name": "Test Item"}
response = requests.post(f"{baseURL}/items", json=payload)
print("POST:", response.status_code, response.json())

# GET
response = requests.get(f"{baseURL}/items", params={"id": 1})
print("GET:", response.status_code, response.json())