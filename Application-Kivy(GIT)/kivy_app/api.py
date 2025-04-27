import requests

API_URL = "http://127.0.0.1:5000/ask"

def get_ai_response(text):
    try:
        response = requests.post(API_URL, json={"message": text})
        return response.json().get("response", "No response received.")
    except:
        return "I'm currently offline."
