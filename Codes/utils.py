# utils.py
import os
import requests
from dotenv import load_dotenv
import sqlite3

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_openrouter(prompt, model="openai/gpt-3.5-turbo"):
    """
    Her türlü doğal dil işleme ve özetleme işlerinde kullanılabilir.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "DataSage"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
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
- Sonuç tablosu kullanıcıya açık ve sade olmalı. Sütun adları anlamlı seçilmeli (örneğin: "oyuncu", "film_sayisi" gibi).
- Sadece kullanıcı açıkça istemişse ORDER BY veya LIMIT kullan.
- “sırala” gibi ifadeler varsa sıralama yap. Aksi halde, doğal tablo sırasını koru.
- Tabloların yapısını ve ilişkilerini doğru analiz et. Her tablo için birincil anahtar (primary key) ve yabancı anahtar (foreign key) sütunlarını belirle.
- JOIN işlemlerinde uygun şekilde birincil ve yabancı anahtar eşleştirmelerini kullan.
- Eğer tablo adları benzerse (örneğin "film", "filmler") doğru olanı seçmek için sütun yapılarına bak.
- Eğer kullanıcı tablo adı ya da sütun adını yanlış verdiyse, veritabanı şemasına göre en yakın ve mantıklı eşleşmeyi kullan.

Çıktı:
- SADECE çalıştırılabilir ve tamamlanmış SQL sorgusunu üret.
- Açıklama, yorum veya format dışı bilgi verme.
- SQL sorgusunu kesinlikle hiçbir tırnak, üçlü tırnak, backtick (`), kod bloğu veya markdown formatı içinde döndürme. Yalnızca düz metin olarak üret.

SQL Sorgusu:
    """
    return call_openrouter(prompt)

def summarize_db(db_path, mode="short"):
    """
    db_path: Yüklü SQLite dosyasının yolu
    mode: "short" = kullanıcıya dost kısa özet, "detail" = çok daha teknik/ayrıntılı özet
    """
    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Tabloları bul
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

Kullanıcıya, bu veritabanının gerçek hayatta neyi modellediğini, ana tabloları ve genel kullanım amacını kısa ve sade bir dille anlat.
- En fazla 2-3 cümle yaz.
- Tablo/kolon/satır sayılarını ve teknik terimleri belirtme.
- Kullanıcıya dost, açıklayıcı bir metin ver.

Açıklaman:
"""
    else:
        prompt = f"""
Aşağıda bir SQLite veritabanının detaylı şema bilgisi ve tabloları listelenmiştir:

{schema_info}

Kullanıcıya bu veritabanının;
- Hangi alan/iş için tasarlandığını,
- Ana tabloların adını ve neyi tuttuğunu,
- Tablolar arası ilişkiler ve olası yabancı anahtarları,
- Eğer mümkünse, veritabanındaki tipik veri akışını, 
- Genel yapısını
daha teknik ama anlaşılır ve uzun bir dille (en fazla 6-8 cümle ile) açıkla.

- Tablo isimlerini, kolon adlarını ve önemli ilişkileri özellikle belirt.
- Kullanıcı dostu ol, ama ayrıntıdan kaçınma.

Açıklaman:
"""

    return call_openrouter(prompt)
