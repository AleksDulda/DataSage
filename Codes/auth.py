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
        username = request.form['username'].lower()
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email'].lower()
        gender = request.form.get('gender')
        role = request.form.get('role', 'user').lower()  # default: user

        hashed_pw = generate_password_hash(password)

        conn = sqlite3.connect("database.sqlite")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # ❌ Eğer admin kaydı yapılmak isteniyor ve zaten admin varsa, engelle
        if role == "admin":
            existing_admin = cursor.execute(
                "SELECT id FROM users WHERE role = 'admin'"
            ).fetchone()
            if existing_admin:
                flash("Zaten bir admin hesabı mevcut. Yeni bir admin oluşturamazsınız.", "danger")
                conn.close()
                return redirect(url_for("auth.register"))

        # ❌ Aynı e-posta kayıtlı mı?
        existing_email = cursor.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        if existing_email:
            flash("Bu e-posta adresi zaten kayıtlı.", "danger")
            conn.close()
            return redirect(url_for("auth.register"))

        # ❌ Aynı kullanıcı adı kayıtlı mı?
        existing_username = cursor.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing_username:
            flash("Bu kullanıcı adı zaten alınmış.", "danger")
            conn.close()
            return redirect(url_for("auth.register"))

        # ✅ Kayıt işlemi
        cursor.execute("""
            INSERT INTO users (username, password, first_name, last_name, email, gender, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, hashed_pw, first_name, last_name, email, gender, role))
        conn.commit()

        user_id = cursor.lastrowid
        session["user_id"] = user_id
        session["username"] = username
        session["role"] = role

        flash("Kayıt başarılı. Hoş geldiniz!", "success")
        conn.close()
        return redirect(url_for("ask"))

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
