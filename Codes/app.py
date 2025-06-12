from flask import Flask, render_template, request, session, redirect, url_for, send_file, jsonify
import os
import sqlite3
from auth import auth
from models import init_db
from utils import generate_sql
import pandas as pd
import io
from collections import Counter
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.register_blueprint(auth)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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


@app.route("/ask", methods=["GET", "POST"])
def ask():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "GET":
        return render_template("ask.html")

    # Mevcut sorgu işlemleri (POST) burada kalacak

    user_id = session["user_id"]
    question = request.form["question"]
    db_file = request.files["database"]

    filename = f"user{user_id}_{db_file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    db_file.save(filepath)

    conn = sqlite3.connect("database.sqlite")
    conn.execute("INSERT INTO db_uploads (user_id, filename) VALUES (?, ?)", (user_id, filename))
    conn.commit()
    conn.close()

    schema = get_schema(filepath)
    sql = generate_sql(schema, question)

    try:
        userdb = sqlite3.connect(filepath)
        cursor = userdb.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        userdb.close()
        result = {"rows": rows, "columns": columns, "sql": sql}
    except Exception as e:
        result = {"rows": [["Hata: " + str(e)]], "columns": ["Hata"], "sql": sql[:500]}

    conn = sqlite3.connect("database.sqlite")
    conn.execute("INSERT INTO query_history (user_id, question, sql_query, result) VALUES (?, ?, ?, ?)",
                 (user_id, question, result["sql"], str(result["rows"])))
    conn.commit()
    conn.close()

    return render_template("ask.html", result=result)

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
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    query_filter = request.args.get("query_filter", "")
    sort_order = request.args.get("sort_order", "desc")

    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row

    uploads = conn.execute("SELECT * FROM db_uploads WHERE user_id = ? ORDER BY uploaded_at DESC", (user_id,)).fetchall()

    history_query = "SELECT * FROM query_history WHERE user_id = ?"
    params = [user_id]
    if query_filter:
        history_query += " AND question LIKE ?"
        params.append(f"%{query_filter}%")
    history_query += " ORDER BY timestamp " + ("ASC" if sort_order == "asc" else "DESC")
    history = conn.execute(history_query, params).fetchall()
    conn.close()

    if sort_order == "desc":
        history = list(reversed(history))

    indexed_history = list(enumerate(history, 1))
    return render_template("dashboard.html", uploads=uploads, history=indexed_history)

@app.route("/download_db/<filename>")
def download_db(filename):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    path = os.path.join(UPLOAD_FOLDER, filename)
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
        path = os.path.join(UPLOAD_FOLDER, upload["filename"])
        if os.path.exists(path):
            os.remove(path)
        conn.execute("DELETE FROM db_uploads WHERE id = ?", (upload_id,))
        conn.commit()

    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/download_query/<int:query_id>")
def download_query(query_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row
    query = conn.execute("SELECT * FROM query_history WHERE id = ? AND user_id = ?", (query_id, session["user_id"])).fetchone()
    conn.close()

    if not query:
        return "Sorgu bulunamadı", 404

    df = pd.DataFrame(eval(query["result"]))
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"query_{query_id}.csv", mimetype="text/csv")

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

@app.route("/contact", methods=["GET", "POST"])
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True)
