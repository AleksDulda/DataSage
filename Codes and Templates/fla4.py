from flask import Flask, request, render_template
import sqlite3
from openai import OpenAI
import os
from tabulate import tabulate
import re

app = Flask(__name__)

# OpenAI API Anahtarı (gizli tutun)
DATABASE_PATH = os.path.join(os.getcwd(), 'sakila.db')


# Yeni client tanımı (global olarak yazabilirsin)
client = OpenAI(api_key="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")  # ← API anahtarını buraya yaz

def generate_sql(query_text):
    prompt = f"""
Veritabanında aşağıdaki tablolar ve sütunlar var:
Tablolar: {get_tables(DATABASE_PATH)}
Sütunlar: {get_columns(DATABASE_PATH)}

'{query_text}' ifadesini karşılayan yalnızca geçerli bir **SQL sorgusu** üret. Açıklama yazma.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"API Hatası: {str(e)}"



def get_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    return [table[0] for table in tables]


def get_columns(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema_info = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        schema_info[table_name] = [column[1] for column in columns]
    conn.close()
    return schema_info


@app.route('/')
def home():
    return render_template('Data_Sage.html')


def extract_sql(response_text):
    # Eğer kod blokları varsa yalnızca SQL kısmını ayıkla
    match = re.search(r"```sql(.*?)```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response_text


def generate_sql_query():
    query_text = request.form.get('text', '').strip()
    sql_query = generate_sql(query_text)
    return extract_sql(sql_query)


@app.route('/generate_sql', methods=['POST'])
def response():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    query = generate_sql_query()

    # Eğer sorgu "API Hatası" ile başlıyorsa hata mesajı göster
    if query.startswith("API Hatası"):
        table_sql = query
        result = ""
    else:
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]

            if results:
                table_sql = tabulate(results, headers=headers, tablefmt='grid')
            else:
                table_sql = "Sonuç bulunamadı."
                result = table_sql
        except Exception as e:
            table_sql = f"Sorgu Hatası: {e}"
            result = table_sql

    conn.close()
    return render_template('Data_Sage.html', sql_query={"query": table_sql, "result": result})



if __name__ == '__main__':
    app.run(debug=True)
