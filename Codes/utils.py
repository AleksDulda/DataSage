# utils.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate_sql(schema, question):
    prompt = f"""
SQL veritabanı şeması:
{schema}

Soru: "{question}"
print(f"API Key: {repr(OPENROUTER_API_KEY)}")


Bu soruya karşılık gelen SQL sorgusunu üret. Sadece SQL döndür.
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "DataSage"  # Sadece ASCII karakter, sorun yaratmaz
    }

    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code != 200:
        return f"[HATA] OpenRouter: {response.text}"

    return response.json()['choices'][0]['message']['content']
