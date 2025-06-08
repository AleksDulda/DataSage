# auth.py
import sqlite3
from flask import Blueprint, request, redirect, session, render_template, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint("auth", __name__)

def get_db_connection():
    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row
    return conn

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_pw = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            flash("Kayıt başarılı! Giriş yapabilirsiniz.", "success")
            return redirect(url_for("auth.login"))
        except sqlite3.IntegrityError:
            flash("Bu kullanıcı adı zaten alınmış.", "danger")
        finally:
            conn.close()

    return render_template("register.html")

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Giriş başarılı!", "success")
            return redirect(url_for("index"))
        else:
            flash("Hatalı kullanıcı adı veya şifre.", "danger")

    return render_template("login.html")

@auth.route("/logout")
def logout():
    session.clear()
    flash("Oturum sonlandırıldı.", "info")
    return redirect(url_for("auth.login"))
