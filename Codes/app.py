from flask import Flask, render_template, request, session, redirect, url_for, send_file, jsonify
import os, zipfile
import sqlite3
from auth import auth
from models import init_db
from utils import generate_sql
import pandas as pd
import io
from collections import Counter
from datetime import datetime
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from functools import wraps


app = Flask(__name__)
app.secret_key = "super_secret_key"
app.register_blueprint(auth)
DB_UPLOAD_FOLDER = os.path.join("uploads")
PROFILE_PIC_FOLDER = os.path.join("static", "uploads")

os.makedirs(DB_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROFILE_PIC_FOLDER, exist_ok=True)


init_db()

def get_schema(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    schema = ""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for (table,) in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        cols = cursor.fetchall()
        schema += f"Table: {table}\n"
        for col in cols:
            schema += f" - {col[1]} ({col[2]})\n"
    conn.close()
    return schema

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Bu sayfayı görüntülemek için giriş yapmalısınız.", "warning")
            return redirect(url_for("auth.login"))
        return view_func(**kwargs)
    return wrapped_view

@app.route("/ask", methods=["GET", "POST"])
def ask():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    if request.method == "GET":
        last_db = session.get("current_db")
        return render_template("ask.html", last_db=last_db)

    question = request.form.get("question", "").strip()
    db_file = request.files.get("database")

    if not question:
        flash("Lütfen bir soru girin.", "warning")
        return render_template("ask.html", last_db=session.get("current_db"))

    # Eğer yeni veritabanı dosyası yüklenmişse...
    if db_file and db_file.filename:
        filename = f"user{user_id}_{db_file.filename}"
        filepath = os.path.join(DB_UPLOAD_FOLDER, filename)
        db_file.save(filepath)

        # Veritabanı kaydı
        conn = sqlite3.connect("database.sqlite")
        conn.execute("INSERT INTO db_uploads (user_id, filename) VALUES (?, ?)", (user_id, filename))
        conn.commit()
        conn.close()

        session["current_db"] = filename
    else:
        # Yeni veritabanı yüklenmediyse, daha önceki yüklü dosya var mı kontrol et
        if "current_db" not in session:
            flash("Lütfen önce bir veritabanı yükleyin.", "danger")
            return render_template("ask.html")
        filename = session["current_db"]
        filepath = os.path.join(DB_UPLOAD_FOLDER, filename)

    # Şema çıkarımı ve SQL üretimi
    schema = get_schema(filepath)
    sql = generate_sql(schema, question)

    print("== Soru:", question)
    print("== SQL:", sql)

    try:
        userdb = sqlite3.connect(filepath)
        cursor = userdb.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        userdb.close()
        result = {"rows": rows, "columns": columns, "sql": sql}
    except Exception as e:
        print("[!] SQL çalıştırma hatası:", str(e))
        result = {
            "rows": [["Hata: " + str(e)]],
            "columns": ["Hata"],
            "sql": sql[:500]
        }

    # Sorgu geçmişine kaydet
    conn = sqlite3.connect("database.sqlite")
    conn.execute(
    "INSERT INTO query_history (user_id, question, sql_query, result, columns, db_filename) VALUES (?, ?, ?, ?, ?, ?)",
    (user_id, question, result["sql"], str(result["rows"]), str(result["columns"]), filename)
    )


    conn.commit()
    conn.close()

    # SQL sorgusunu da template'e gönderiyoruz
    return render_template("ask.html", result=result, last_db=filename, sql_query=result["sql"])


@app.route("/download", methods=["POST"])
def download():
    rows = request.json.get("rows")
    columns = request.json.get("columns")
    format = request.json.get("format", "csv")
    df = pd.DataFrame(rows, columns=columns)
    buffer = io.BytesIO()

    if format == "xlsx":
        df.to_excel(buffer, index=False, engine="openpyxl")
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "query_result.xlsx"
    else:
        df.to_csv(buffer, index=False)
        mimetype = "text/csv"
        filename = "query_result.csv"

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    query_filter = request.args.get("query_filter", "")
    sort_order = request.args.get("sort_order", "desc").lower()

    # --- Sorgu geçmişi sayfalama ---
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        if per_page not in [10, 15, 20]:
            per_page = 10
    except:
        page = 1
        per_page = 10

    # --- Veritabanı uploads için sayfalama ---
    try:
        uploads_page = int(request.args.get("uploads_page", 1))
        uploads_per_page = int(request.args.get("uploads_per_page", 10))
        if uploads_per_page not in [10, 15, 20]:
            uploads_per_page = 10
    except:
        uploads_page = 1
        uploads_per_page = 10

    if sort_order not in ["asc", "desc"]:
        sort_order = "desc"

    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row

    # --- Uploads ile ilgili kısım ---
    uploads_count = conn.execute(
        "SELECT COUNT(*) FROM db_uploads WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    uploads_offset = (uploads_page - 1) * uploads_per_page
    uploads_total_pages = (uploads_count + uploads_per_page - 1) // uploads_per_page

    uploads = conn.execute("""
        SELECT * FROM db_uploads 
        WHERE user_id = ? 
        ORDER BY uploaded_at DESC
        LIMIT ? OFFSET ?
    """, (user_id, uploads_per_page, uploads_offset)).fetchall()

    uploads_start_page = max(1, uploads_page - 2)
    uploads_end_page = min(uploads_page + 2, uploads_total_pages)

    # --- Sorgu geçmişi ile ilgili kısım ---
    history_query = "SELECT * FROM query_history WHERE user_id = ?"
    params = [user_id]
    if query_filter:
        history_query += " AND LOWER(question) LIKE ?"
        params.append(f"%{query_filter.lower()}%")
    history_query += f" ORDER BY timestamp {sort_order.upper()}"

    # Toplam kayıt sayısı (sayfalama için)
    count_query = "SELECT COUNT(*) FROM query_history WHERE user_id = ?"
    count_params = [user_id]
    if query_filter:
        count_query += " AND LOWER(question) LIKE ?"
        count_params.append(f"%{query_filter.lower()}%")
    total_queries = conn.execute(count_query, count_params).fetchone()[0]

    # Sayfalama parametreleri
    offset = (page - 1) * per_page
    history_query += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    history = conn.execute(history_query, params).fetchall()

    indexed_history = list(enumerate(history, offset + 1))
    total_pages = (total_queries + per_page - 1) // per_page  # yukarı yuvarlama

    start_page = max(1, page - 2)
    end_page = min(page + 2, total_pages)

    conn.close()
    return render_template(
        "dashboard.html",
        # uploads (veritabanı dosyaları)
        uploads=uploads,
        uploads_page=uploads_page,
        uploads_per_page=uploads_per_page,
        uploads_count=uploads_count,
        uploads_total_pages=uploads_total_pages,
        uploads_start_page=uploads_start_page,
        uploads_end_page=uploads_end_page,
        # sorgu geçmişi (history)
        history=indexed_history,
        page=page,
        per_page=per_page,
        total_queries=total_queries,
        total_pages=total_pages,
        start_page=start_page,
        end_page=end_page,
    )


@app.route("/download_db/<filename>")
def download_db(filename):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    path = os.path.join(DB_UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        return "Dosya bulunamadı", 404

    return send_file(path, as_attachment=True)

@app.route("/delete_upload/<int:upload_id>")
def delete_upload(upload_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row
    upload = conn.execute("SELECT * FROM db_uploads WHERE id = ? AND user_id = ?", (upload_id, session["user_id"])).fetchone()

    if upload:
        path = os.path.join(DB_UPLOAD_FOLDER, upload["filename"])
        if os.path.exists(path):
            os.remove(path)
        conn.execute("DELETE FROM db_uploads WHERE id = ?", (upload_id,))
        conn.commit()

    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/download_query/<int:query_id>/<format>")
def download_query(query_id, format):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row
    query = conn.execute(
        "SELECT * FROM query_history WHERE id = ? AND user_id = ?",
        (query_id, session["user_id"])
    ).fetchone()
    conn.close()

    if not query:
        return "Sorgu bulunamadı", 404

    rows = eval(query["result"])
    # YENİ EKLENDİ:
    if "columns" in query.keys() and query["columns"]:
        columns = eval(query["columns"])
        df = pd.DataFrame(rows, columns=columns)
    else:
        df = pd.DataFrame(rows)

    buffer = io.BytesIO()
    if format == "xlsx":
        df.to_excel(buffer, index=False, engine="openpyxl")
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"
    else:
        df.to_csv(buffer, index=False)
        mimetype = "text/csv"
        ext = "csv"
    buffer.seek(0)
    filename = f"query_{query_id}.{ext}"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )



@app.route("/delete_query/<int:query_id>")
def delete_query(query_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = sqlite3.connect("database.sqlite")
    conn.execute("DELETE FROM query_history WHERE id = ? AND user_id = ?", (query_id, session["user_id"]))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))

@app.route("/stats")
def stats():
    if "user_id" not in session:
        return jsonify({})

    user_id = session["user_id"]
    chart_type = request.args.get("type", "status")

    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row
    queries = conn.execute("SELECT * FROM query_history WHERE user_id = ?", (user_id,)).fetchall()
    uploads = conn.execute("SELECT * FROM db_uploads WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()

    def is_error_result(result_text):
        try:
            rows = eval(result_text)
            return isinstance(rows, list) and len(rows) == 1 and len(rows[0]) == 1 and str(rows[0][0]).startswith("Hata")
        except:
            return False

    if chart_type == "status":
        total = len(queries)
        errors = sum(1 for q in queries if is_error_result(q["result"]))
        success = total - errors
        return jsonify({
            "chartType": "bar",
            "labels": ["Toplam", "Başarılı", "Hatalı"],
            "data": [total, success, errors],
            "label": "Sorgu Sayısı",
            "title": "Sorgu Başarı Durumu",
            "colors": ["#007bff", "#28a745", "#dc3545"]
        })

    elif chart_type == "daily":
        daily = Counter([q["timestamp"].split(" ")[0] for q in queries])
        days = sorted(daily.keys())
        counts = [daily[day] for day in days]
        return jsonify({
            "chartType": "line",
            "labels": days,
            "data": counts,
            "label": "Sorgu Sayısı",
            "title": "Günlük Sorgu Sayısı"
        })

    elif chart_type == "keywords":
        all_words = " ".join(q["question"] for q in queries).lower().split()
        common = Counter(all_words).most_common(5)
        labels = [word for word, _ in common]
        counts = [count for _, count in common]
        return jsonify({
            "chartType": "doughnut",
            "labels": labels,
            "data": counts,
            "label": "Anahtar Kelimeler",
            "title": "En Sık Geçen Anahtar Kelimeler"
        })

    elif chart_type == "usage":
        db_counts = Counter([u["filename"] for u in uploads])
        labels = list(db_counts.keys())
        counts = list(db_counts.values())
        return jsonify({
            "chartType": "pie",
            "labels": labels,
            "data": counts,
            "label": "Veritabanı Kullanımı",
            "title": "Veritabanı Kullanım Oranı"
        })

    return jsonify({})

@app.route("/features")
def features():
    return render_template("features.html")

@app.route("/about")
def about():
    return render_template("about.html")

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'DataSageContact@gmail.com'       # değiştir!
app.config['MAIL_PASSWORD'] = 'elyswfmlwxkgddib'     # değiştir!
app.config['MAIL_DEFAULT_SENDER'] = 'DataSageContact@gmail.com' # değiştir!

mail = Mail(app)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        # 1. Veritabanına kaydet
        try:
            conn = sqlite3.connect("database.sqlite")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
                           (name, email, message))
            conn.commit()
            conn.close()
        except Exception as db_error:
            print("[!] DB Hatası:", db_error)
            return render_template("contact.html", error=True)

        try:
            # 2. Yöneticiyi bilgilendir
            admin_msg = Message(
                subject="Yeni İletişim Mesajı - DataSage",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=["DataSageContact@gmail.com"],
                reply_to=email,
                body=f"Ad: {name}\nEmail: {email}\nMesaj:\n{message}"
            )
            mail.send(admin_msg)

            # 3. Kullanıcıya otomatik teşekkür maili
            user_msg = Message(
                subject="İletişime Geçtiğiniz İçin Teşekkürler! - DataSage",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[email],
                body=f"Merhaba {name},\n\nMesajınızı aldık. En kısa sürede sizinle iletişime geçeceğiz.\n\nTeşekkür ederiz!\n\n— DataSage Ekibi"
            )
            mail.send(user_msg)

            return render_template("contact.html", success=True)

        except Exception as e:
            print("[!] Mail gönderim hatası:", e)
            return render_template("contact.html", error=True)

    return render_template("contact.html")

@app.route("/admin/messages")
def admin_messages():
    if "user_id" not in session or session.get("username") != "admin":
        return redirect(url_for("auth.login"))

    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row
    messages = conn.execute("SELECT * FROM contact_messages ORDER BY created_at DESC").fetchall()
    conn.close()

    return render_template("admin_messages.html", messages=messages)

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()

    return render_template("profile.html", user=user)

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        conn = sqlite3.connect("database.sqlite")
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

        if not check_password_hash(user["password"], old_password):
            flash("Mevcut şifre hatalı!", "danger")
            return redirect(url_for("change_password"))

        if new_password != confirm_password:
            flash("Yeni şifreler eşleşmiyor.", "warning")
            return redirect(url_for("change_password"))

        hashed_pw = generate_password_hash(new_password)
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, session["user_id"]))
        conn.commit()
        conn.close()

        flash("Şifre başarıyla güncellendi.", "success")
        return redirect(url_for("profile"))

    return render_template("change_password.html")

@app.route("/delete-account", methods=["GET", "POST"])
def delete_account():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    if request.method == "POST":
        conn = sqlite3.connect("database.sqlite")
        cursor = conn.cursor()

        # Sorgu geçmişi ve dosyaları sil
        cursor.execute("DELETE FROM query_history WHERE user_id = ?", (user_id,))
        uploads = cursor.execute("SELECT filename FROM db_uploads WHERE user_id = ?", (user_id,)).fetchall()
        for (filename,) in uploads:
            filepath = os.path.join(DB_UPLOAD_FOLDER, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        cursor.execute("DELETE FROM db_uploads WHERE user_id = ?", (user_id,))

        # Kullanıcıyı sil
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        session.clear()
        flash("Hesabınız ve tüm verileriniz silindi.", "info")
        return redirect(url_for("index"))

    return render_template("confirm_delete.html")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/update-profile", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    gender = request.form.get("gender")
    birth_date = request.form.get("birth_date")
    profile_picture = request.files.get("profile_picture")
    remove_picture = request.form.get("remove_picture") == "1"

    conn = sqlite3.connect("database.sqlite")
    cursor = conn.cursor()

    if remove_picture:
        old_pic = cursor.execute("SELECT profile_picture FROM users WHERE id = ?", (user_id,)).fetchone()[0]
        if old_pic:
            old_path = os.path.join("static", "uploads", old_pic)
            if os.path.exists(old_path):
                os.remove(old_path)
        cursor.execute("""
            UPDATE users
            SET first_name = ?, last_name = ?, email = ?, gender = ?, birth_date = ?, profile_picture = NULL
            WHERE id = ?
        """, (first_name, last_name, email, gender, birth_date, user_id))

    elif profile_picture and profile_picture.filename:
        if allowed_file(profile_picture.filename):
            filename = secure_filename(f"user_{user_id}_{profile_picture.filename}")
            filepath = os.path.join("static", "uploads", filename)
            profile_picture.save(filepath)

            cursor.execute("""
                UPDATE users
                SET first_name = ?, last_name = ?, email = ?, gender = ?, birth_date = ?, profile_picture = ?
                WHERE id = ?
            """, (first_name, last_name, email, gender, birth_date, filename, user_id))
        else:
            flash("Geçersiz dosya türü. Sadece PNG, JPG, JPEG veya GIF yükleyebilirsiniz.", "danger")
            return redirect(url_for("profile"))

    else:
        cursor.execute("""
            UPDATE users
            SET first_name = ?, last_name = ?, email = ?, gender = ?, birth_date = ?
            WHERE id = ?
        """, (first_name, last_name, email, gender, birth_date, user_id))

    conn.commit()
    conn.close()
    flash("Profil bilgileri başarıyla güncellendi.", "success")
    return redirect(url_for("profile"))

@app.route("/download_all_dbs")
@login_required
def download_all_dbs():
    user_id = session["user_id"]
    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row
    uploads = conn.execute(
        "SELECT * FROM db_uploads WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()

    if not uploads:
        return "Hiçbir veritabanı bulunamadı.", 404

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for db in uploads:
            file_path = os.path.join("db_files", db["filename"])
            if os.path.exists(file_path):
                zf.write(file_path, arcname=db["filename"])
    memory_file.seek(0)
    return send_file(memory_file, as_attachment=True, download_name="veritabanlari.zip", mimetype="application/zip")

@app.route("/delete_all_uploads")
@login_required
def delete_all_uploads():
    user_id = session["user_id"]
    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row
    uploads = conn.execute(
        "SELECT * FROM db_uploads WHERE user_id = ?", (user_id,)
    ).fetchall()
    for db in uploads:
        file_path = os.path.join("db_files", db["filename"])
        if os.path.exists(file_path):
            os.remove(file_path)
    conn.execute("DELETE FROM db_uploads WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

import pandas as pd

@app.route("/download_all_queries_zip/<format>")
@login_required
def download_all_queries_zip(format):
    user_id = session["user_id"]
    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row
    queries = conn.execute(
        "SELECT * FROM query_history WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    if not queries:
        return "Hiçbir sorgu bulunamadı.", 404

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for idx, query in enumerate(queries, 1):
            try:
                rows = eval(query["result"])
                columns = eval(query["columns"]) if query["columns"] else []
                if not isinstance(rows, list):
                    rows = []
                df = pd.DataFrame(rows, columns=columns)
            except Exception as e:
                df = pd.DataFrame([{"Hata": str(e)}])

            if format == "csv":
                file_buffer = df.to_csv(index=False).encode("utf-8")
                file_name = f"sorgu_{idx}.csv"
            elif format == "xlsx":
                excel_buffer = io.BytesIO()
                df.to_excel(excel_buffer, index=False, engine="openpyxl")
                excel_buffer.seek(0)
                file_buffer = excel_buffer.read()
                file_name = f"sorgu_{idx}.xlsx"
            else:
                return "Desteklenmeyen format.", 400

            zf.writestr(file_name, file_buffer)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=f"tum_sorgu_sonuclari_{format}.zip",
        mimetype="application/zip"
    )


@app.route("/delete_all_queries")
@login_required
def delete_all_queries():
    user_id = session["user_id"]
    conn = sqlite3.connect("database.sqlite")
    conn.execute("DELETE FROM query_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)