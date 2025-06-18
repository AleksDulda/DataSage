import sqlite3
import uuid
from datetime import datetime, timedelta
from flask_mail import Message

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

        conn = get_db_connection()
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

        # ✅ Kayıt işlemi + token başlangıç verisi
        cursor.execute("""
            INSERT INTO users (
                username, password, first_name, last_name, email, gender, role,
                tokens, last_token_reset
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            hashed_pw,
            first_name,
            last_name,
            email,
            gender,
            role,
            10,
            datetime.utcnow().isoformat()
        ))

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
            session["role"] = user["role"]
            flash("Giriş başarılı!", "success")
            return redirect(url_for("ask"))
        else:
            flash("Hatalı kullanıcı adı veya şifre.", "danger")

    return render_template("login.html")

@auth.route("/logout")
def logout():
    session.clear()
    flash("Oturum sonlandırıldı.", "info")
    return redirect(url_for("auth.login"))

@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (identifier, identifier)).fetchone()
        
        if user:
            token = str(uuid.uuid4())
            expiry = datetime.utcnow() + timedelta(hours=1)
            conn.execute("UPDATE users SET reset_token = ?, reset_expiry = ? WHERE id = ?", (token, expiry.isoformat(), user["id"]))
            conn.commit()
            reset_link = url_for("auth.reset_password", token=token, _external=True)

            msg = Message("Şifre Sıfırlama - DataSage",
                          recipients=[user["email"]],
                          body=f"Merhaba {user['first_name']},\n\nŞifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:\n{reset_link}\n\nBağlantı 1 saat boyunca geçerlidir.")
            from app import mail
            mail.send(msg)

            flash("Eğer bilgiler doğruysa şifre sıfırlama bağlantısı e-posta adresinize gönderildi.", "info")
        else:
            flash("Eğer bilgiler doğruysa şifre sıfırlama bağlantısı e-posta adresinize gönderildi.", "info")

        conn.close()
    return render_template("forgot_password.html")

@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE reset_token = ?", (token,)).fetchone()

    if not user or datetime.utcnow() > datetime.fromisoformat(user["reset_expiry"]):
        flash("Bu bağlantı geçersiz veya süresi dolmuş.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm = request.form.get("confirm_password")

        print("DEBUG:", new_password, confirm)  # GEÇİCİ

        if new_password != confirm:
            flash("Şifreler eşleşmiyor.", "warning")
        else:
            hashed = generate_password_hash(new_password)
            conn.execute("UPDATE users SET password = ?, reset_token = NULL, reset_expiry = NULL WHERE id = ?", (hashed, user["id"]))
            conn.commit()
            flash("Şifreniz başarıyla sıfırlandı. Giriş yapabilirsiniz.", "success")
            return redirect(url_for("auth.login"))

    conn.close()
    return render_template("reset_password.html", token=token)

