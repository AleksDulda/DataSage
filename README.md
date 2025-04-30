# DataSage

#  Text-to-SQL Arayüzü (OpenAI GPT ile)

Bu proje, bir Flask uygulaması üzerinden doğal dilde verilen sorguları OpenAI API aracılığıyla **SQL sorgularına çevirir** ve `sakila.db` veritabanı üzerinde çalıştırarak sonucu kullanıcıya HTML tabanlı bir arayüzde gösterir.

---
## Gereksinimler

- Python 3.9+
- `pip` (Python package manager)
- Bir SQLite veritabanı (`sakila.db`)
- Geçerli bir OpenAI API anahtarı (GPT-3.5 için)

---
## Dosya Yapısı
.
├── fla4.py                 # Flask uygulaması
├── sakila.db               # SQLite veritabanı
├── templates/
│   └── top_renters.html    # Web arayüzü


##  Kütüphaneler

```python
from flask import Flask, request, render_template
import sqlite3
from openai import OpenAI
import os
from tabulate import tabulate
import re
```

Flask: Web uygulamasını oluşturur.

sqlite3: Sakila veritabanına bağlanmak için kullanılır.

OpenAI: GPT modellerine erişmek için kullanılır (v1.0+ uyumlu).

os: Dosya yolları ve ortam değişkenleri için.

tabulate: SQL sorgusu sonuçlarını tablo biçiminde göstermek için.

re: Yanıt metni içinden SQL kodunu ayıklamak için (regex).

## GPT ile SQL Üreten Fonksiyon

```python
def generate_sql(query_text):
```
prompt içinde veritabanı yapısı ve kullanıcı sorgusu modele verilir.

Modelden dönen yanıt işlenerek sadece SQL çıktısı elde edilir.

## Veritabanı Şeması Çekme Fonksiyonları

```python
def get_tables(db_path):
    ...
def get_columns(db_path):
    ...
```
## Ana Sayfa (HTML Formu)

```
@app.route('/')
def home():
    return render_template('top_renters.html')
```

## SQL Kodunu Ayıklayan Fonksiyon

```python
def extract_sql(response_text):
    match = re.search(r"```sql(.*?)```", response_text, re.DOTALL)
    ...
```

## Doğal Dilden SQL Üreten Ara Fonksiyon
 
 ```python
def generate_sql_query():
    query_text = request.form['text']
    sql_query = generate_sql(query_text)
    return extract_sql(sql_query)
```

Kullanıcının formdan gönderdiği metni alır.

SQL üretimi yapılır ve sadece SQL kısmı döndürülür.

## SQL'i Çalıştıran ve Sonucu Gösteren Ana Route

```python
@app.route('/generate_sql', methods=['POST'])
def response():
    ...
```

Kullanıcının gönderdiği sorguya karşılık:

SQL üretilir

Veritabanında çalıştırılır

Sonuçlar tablo olarak HTML'de gösterilir

Eğer API'den hata dönüyorsa startswith("API Hatası") kontrolü ile sorgu çalıştırılmaz

