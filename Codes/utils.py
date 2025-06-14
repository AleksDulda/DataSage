# utils.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate_sql(schema, question):
    prompt = f"""
Aşağıda bir SQLite veritabanı şeması bulunmaktadır.

Veritabanı şeması:
{schema}

Kullanıcıdan gelen doğal dildeki sorgu:
"{question}"

Kriterler:
- Kullanıcı SQL bilmeyebilir.
- Sorular bazen eksik, muğlak veya yanlış terimlerle ifade edilmiş olabilir.
- Uygun JOIN, GROUP BY, HAVING, COUNT, ORDER BY gibi SQL yapıları gerekiyorsa kullan.
- Eğer kullanıcının isteği bir metrik içeriyorsa (örneğin "en çok", "kaç film", "sayısı") → sayısal sütunlar üret.
- Sonuç tablosu kullanıcıya açık ve sade olmalı. Sütun adları anlamlı seçilmeli (örneğin: "oyuncu", "film_sayisi" gibi).
- Sadece kullanıcı açıkça istemişse ORDER BY veya LIMIT kullan.
- “sırala” gibi ifadeler varsa sıralama yap. Aksi halde, doğal tablo sırasını koru.

Çıktı:
- SADECE çalıştırılabilir ve tamamlanmış SQL sorgusunu üret.
- Açıklama, yorum veya format dışı bilgi verme.

SQL Sorgusu:
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "DataSage"
    }

    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"OpenRouter API Hatası: {response.text}")

    return response.json()['choices'][0]['message']['content']

