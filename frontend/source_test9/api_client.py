import requests
from config import API_KEY

def get_user():
    headers = {
        "Authorization": "Bearer " + API_KEY
    }

    response = requests.get(
        "https://api.example.com/users",
        headers=headers
    )

    return response.json()