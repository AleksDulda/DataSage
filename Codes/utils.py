import os
import requests

def generate_sql(schema, question):
    api_key = os.getenv("OPENROUTER_API_KEY")

    prompt = f"""
SQL veritabanı şeması:
{schema}

Soru: "{question}"

Bu soruya karşılık gelen SQL sorgusunu üret. Sadece SQL döndür.
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",  
        "X-Title": "DATASAGE-Demo"
    }

    data = {
        "model": "openai/gpt-3.5-turbo",  
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code != 200:
        return f"[HATA] OpenRouter: {response.json()}"

    return response.json()['choices'][0]['message']['content']
