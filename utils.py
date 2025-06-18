import os
import requests
from dotenv import load_dotenv
import sqlite3
from datetime import datetime, timedelta

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_openrouter(prompt, model="openai/gpt-3.5-turbo"):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "DataSage"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"OpenRouter API Hatası: {response.text}")
    return response.json()['choices'][0]['message']['content'].strip()


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
- Sonuç tablosu kullanıcıya açık ve sade olmalı.
- SADECE SQL sorgusu üret, başka açıklama yazma.

SQL Sorgusu:
    """
    return call_openrouter(prompt)

def summarize_db(db_path, mode="short"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    schema_info = f"Bu veritabanında {len(tables)} tablo var: {', '.join(tables)}.\n"

    for t in tables:
        cursor.execute(f"PRAGMA table_info({t})")
        cols = [col[1] for col in cursor.fetchall()]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            row_count = cursor.fetchone()[0]
        except Exception:
            row_count = "?"
        schema_info += f"- Tablo: {t}, kolonlar: {', '.join(cols)}, satır sayısı: {row_count}\n"
    conn.close()

    if mode == "short":
        prompt = f"""
Aşağıda bir SQLite veritabanının tablo ve kolon isimleri özetlenmiştir:

{schema_info}

Kullanıcıya, bu veritabanının gerçek hayatta neyi modellediğini kısa ve sade bir dille anlat.
En fazla 2-3 cümle yaz. Teknik detay verme.

Açıklaman:
"""
    else:
        prompt = f"""
Aşağıda bir SQLite veritabanının detaylı şema bilgisi ve tabloları listelenmiştir:

{schema_info}

Kullanıcıya bu veritabanının;
- Hangi iş için tasarlandığını,
- Ana tabloları ve ilişkilerini,
- Yapısını ve veri akışını
teknik ve açıklayıcı bir dille anlat. En fazla 6-8 cümle kullan.

Açıklaman:
"""
    return call_openrouter(prompt)


def summarize_schema(schema_text, mode="short"):
    if mode == "short":
        prompt = f"""
Aşağıda bir SQL veritabanının tablo ve sütun yapıları listelenmiştir:

{schema_text}

Bu veritabanının genel amacı nedir? Sade ve kısa (2-3 cümle) şekilde açıkla.

Cevap:
"""
    else:
        prompt = f"""
Aşağıda bir SQL veritabanının tablo yapıları listelenmiştir:

{schema_text}

Veritabanı hakkında:
- Hangi iş için kullanılır?
- Ana tablolar ne işe yarar?
- Olası ilişkiler?
- Yapısı nasıl?

Teknik ama açıklayıcı şekilde anlat (6-8 cümle). Tablo isimlerini kullanabilirsin.

Açıklama:
"""
    return call_openrouter(prompt)


def reset_tokens_if_needed(user_id):
    conn = sqlite3.connect("database.sqlite")
    cursor = conn.cursor()

    cursor.execute("SELECT tokens, last_token_reset FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    if row:
        tokens, last_reset_str = row
        try:
            last_reset = datetime.fromisoformat(last_reset_str)
        except Exception:
            last_reset = datetime.utcnow()

        now = datetime.utcnow()
        if now - last_reset >= timedelta(hours=24):
            cursor.execute("UPDATE users SET tokens = 10, last_token_reset = ? WHERE id = ?", (now.isoformat(), user_id))
            conn.commit()

    conn.close()


def get_token_status(user_id):
    conn = sqlite3.connect("database.sqlite")
    cursor = conn.cursor()

    cursor.execute("SELECT tokens, last_token_reset FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        tokens, last_reset_str = row
        if last_reset_str:
            try:
                last_reset = datetime.fromisoformat(last_reset_str)
            except ValueError:
                last_reset = datetime.utcnow()
        else:
            last_reset = datetime.utcnow()

        now = datetime.utcnow()
        elapsed = now - last_reset
        remaining = max(timedelta(0), timedelta(hours=24) - elapsed)

        return tokens, remaining

    return 10, timedelta(hours=24)


def decrement_token_if_success(user_id, result):
    if result.get("columns", [])[0] == "Hata":
        return  # başarısızsa token düşme

    conn = sqlite3.connect("database.sqlite")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET tokens = tokens - 1 WHERE id = ? AND tokens > 0", (user_id,))
    conn.commit()
    conn.close()
