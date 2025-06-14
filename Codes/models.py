import sqlite3

def init_db():
    conn = sqlite3.connect("database.sqlite")
    cursor = conn.cursor()

    # Kullanıcı tablosu (güncellenmiş)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        gender TEXT,
        birth_date TEXT,
        profile_picture TEXT
    )
    """)
# Sorgu geçmişi tablosu (GÜNCEL)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS query_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question TEXT,
        sql_query TEXT,
        result TEXT,
        columns TEXT,         -- EKLENDİ!
        db_filename TEXT,     -- YENİ: Sorgunun çalıştığı veritabanı dosya adı
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)



    # Yüklenen veritabanı geçmişi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS db_uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # İletişim mesajları tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
