import requests
import os
import time
import random
from database import fetch, execute

HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

def moderate_text(text):
    toxic_words = ["spam", "crypto link", "nsfw_word1", "hack"]
    for w in toxic_words:
        if w.lower() in text.lower():
            return True # Flagged
    return False

def generate_ai_response(user_input, user_lang="en"):
    # Simulated human reading typing delay
    time.sleep(random.uniform(0.5, 1.5))
    
    sys_prompt = fetch("SELECT value FROM settings WHERE key='sys_prompt'", one=True)["value"]
    mode = fetch("SELECT value FROM settings WHERE key='mode'", one=True)["value"]
    temp = float(fetch("SELECT value FROM settings WHERE key='ai_temp'", one=True)["value"])
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    prompt = f"<s>[INST] {sys_prompt}. Mode: {mode}. User language: {user_lang}. User asks: {user_input} [/INST]"
    payload = {
        "inputs": prompt,
        "parameters": {"temperature": temp, "max_new_tokens": 512, "return_full_text": False}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        response_json = response.json()
        if type(response_json) is list and "generated_text" in response_json[0]:
            return response_json[0]["generated_text"].strip()
        else:
            return "System Overloaded. Entering safe-mode. Try again."
    except Exception as e:
        return f"AI Offline fallback activated. Reason: {str(e)}"
