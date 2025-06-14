# auth.py
import sqlite3
from flask import Blueprint, request, redirect, session, render_template, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint("auth", __name__)

def get_db_connection():
    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row
    return conn

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].lower()  # lowercase
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        gender = request.form.get('gender')

        hashed_pw = generate_password_hash(password)

        conn = sqlite3.connect("database.sqlite")
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (username, password, first_name, last_name, email, gender)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, hashed_pw, first_name, last_name, email, gender))
            conn.commit()

            # Otomatik giriş için ekle
            user_id = cursor.lastrowid
            session["user_id"] = user_id
            session["username"] = username

        except sqlite3.IntegrityError:
            flash("Bu kullanıcı adı zaten kayıtlı.", "danger")
            return redirect(url_for("auth.register"))
        finally:
            conn.close()

        flash("Kayıt başarılı, hoş geldiniz!", "success")
        return redirect(url_for("ask"))  # veya dashboard

    return render_template("register.html")



@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].lower()
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Giriş başarılı!", "success")
            return redirect(url_for("ask"))  # Ana sayfa vs. yönlendirmesi
        else:
            flash("Hatalı kullanıcı adı veya şifre.", "danger")

    return render_template("login.html")

@auth.route("/logout")
def logout():
    session.clear()
    flash("Oturum sonlandırıldı.", "info")
    return redirect(url_for("auth.login"))
