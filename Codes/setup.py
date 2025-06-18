# setup.py
import sqlite3
import os

DB_PATH = "database.sqlite"

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("[✔] Eski veritabanı silindi.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Kullanıcılar tablosu
    cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        email TEXT UNIQUE,
        gender TEXT,
        birth_date TEXT,
        profile_picture TEXT,
        role TEXT DEFAULT 'user',
        tokens INTEGER DEFAULT 10,
        last_token_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reset_token TEXT,
        reset_expiry TIMESTAMP
    )
    """)

    # Sorgu geçmişi tablosu
    cursor.execute("""
    CREATE TABLE query_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question TEXT,
        sql_query TEXT,
        result TEXT,
        columns TEXT,
        db_filename TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Veritabanı yükleme geçmişi
    cursor.execute("""
    CREATE TABLE db_uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # İletişim mesajları
    cursor.execute("""
    CREATE TABLE contact_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("[✔] Yeni veritabanı oluşturuldu ve tüm tablolar hazır.")

if __name__ == "__main__":
    init_db()
