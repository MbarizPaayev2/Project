# -*- coding: utf-8 -*-
"""
Minimal Flask: yalnız /api/register, /api/login, /api/logout, /api/me + statik frontend.
İşə salma (layihə kökündən): python backend/app.py
"""

# Standart Python kitabxanaları
import os  # Ətraf mühit dəyişənlərini oxumaq (DATABASE_URL, PORT vəs.)
import sys  # Sistem əməliyyatları (xəta çıxışına yazma, proqramı bitirmə)
from pathlib import Path  # Fayl yollarını işləmək üçün (cross-platform uyğunluq)
from typing import Any, Dict, Optional, Tuple  # Tip işarətləmə (type hints)
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse  # URL-i parse etmə

# Üçüncü tərəf kitabxanaları
from dotenv import load_dotenv  # .env faylından mühit dəyişənləri oxumaq
from flask import Flask, jsonify, request, send_from_directory, session  # Flask veb çərçivəsi
from werkzeug.security import check_password_hash, generate_password_hash  # Parol şifrələmə

# Fayl yollarını təyin etmə
BACKEND_DIR = Path(__file__).resolve().parent  # Backend qovluğunun yolu
PROJECT_ROOT = BACKEND_DIR.parent  # Layihənin kök qovluğu
FRONTEND_DIR = PROJECT_ROOT / "frontend"  # Frontend qovluğunun yolu

# .env faylından mühit dəyişənlərini oxumaq
load_dotenv(PROJECT_ROOT / ".env", override=True)
load_dotenv(BACKEND_DIR / ".env", override=True)

# PostgreSQL verilənlər bazasına qoşulma URL-i oxumaq
DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()
if not DATABASE_URL:
    print(
        "DATABASE_URL boşdur. .env faylında məs. "
        "DATABASE_URL=postgresql://user:pass@localhost:5432/dbname",
        file=sys.stderr,
    )
    sys.exit(1)

# Flask tətbiqini yaratmaq və secret key təyin etmək
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)


# Vercel kimi cloud platformalarda SSL qoşulmayını tələb etmə
def _effective_database_url() -> str:
    """
    DATABASE_URL-i parse etmə və Vercel ortamında sslmode əlavə etmə.
    SSL şifrələmərinin mövcud olmasını tələb edir.
    """
    parsed = urlparse(DATABASE_URL)
    qs = parse_qs(parsed.query)
    keys_lower = {k.lower() for k in qs}
    if os.environ.get("VERCEL") and "sslmode" not in keys_lower:
        qs["sslmode"] = ["require"]
    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


# PostgreSQL verilənlər bazasına qoşulmaq
def get_db():
    """
    PostgreSQL-ə yeni qoşulma açmaq.
    RealDictCursor istifadə edilərək nəticələr dict kimi qaytarılır.
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor

    return psycopg2.connect(_effective_database_url(), cursor_factory=RealDictCursor)


# Verilənlər bazasını başlanğıclaş (cədvəlləri yaratmaq)
def init_db():
    """
    'users' cədvəlini yaratmaq (əgər artıq mövcud deyilsə).
    Həər istifadəçi: id, email, password_hash, full_name, created_at
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    conn.commit()
    cur.close()
    conn.close()


# Tətbiq başladıqda verilənlər bazasını başlanğıclaş
try:
    init_db()
except Exception as ex:
    print("DB init:", ex)


# E-poçt düzgünlüyünü yoxlamaq
def validate_email(email: str) -> bool:
    """
    E-poçt formatını yoxlamaq.
    Ən azı 5 simvol, @ işarəsi və domainə malik olmalıdır.
    """
    email = (email or "").strip()
    if len(email) < 5 or "@" not in email or "." not in email.split("@")[-1]:
        return False
    return True


# Parol gücünü yoxlamaq
def validate_password_strength(pw: str) -> Tuple[bool, str]:
    """
    Parolun güclü olmasını yoxlamaq:
    - Ən azı 8 simvol
    - Ən azı bir hərf
    - Ən azı bir rəqəm
    Qaytararaq: (Düzgün yoxsa yanlış, Xəta mesajı)
    """
    if not pw or len(pw) < 8:
        return False, "Parol ən azı 8 simvol olmalıdır."
    if not any(c.isalpha() for c in pw):
        return False, "Parolda ən azı bir hərf olmalıdır."
    if not any(c.isdigit() for c in pw):
        return False, "Parolda ən azı bir rəqəm olmalıdır."
    return True, ""


# Giriş məlumatlarının məhdudiyyətini yoxlamaq
def login_input_bounds(email: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    E-poçt və parolun uzunluğunu yoxlamaq (təhlükəsizlik üçün).
    Hər biri maksimum uzunluğu aşmamalıdır.
    """
    if len(email) > 254 or len(password) > 256:
        return False, "E-poçt və ya parol çox uzundur."
    if "\x00" in email or "\x00" in password:
        return False, "Yanlış simvol."
    return True, None


# Verilənlər bazasından istifadəçi məlumatlarını almaq
def user_get_by_email(email_lower: str) -> Optional[Dict[str, Any]]:
    """
    E-poçtə görə istifadəçini axtarmaq (böyük-kiçik həarf fərqi olmadan).
    Parol hash-ini daxil edib, bütün məlumatı qaytarır.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, password_hash, full_name FROM users WHERE lower(email) = %s",
        (email_lower,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


# Publik istifadəçi məlumatlarını almaq (parol olmadan)
def user_get_public(user_id: Any) -> Optional[Dict[str, Any]]:
    """
    İstifadəçi ID-sinə görə publik məlumatlarını almaq.
    Parol hash-i daxil edilmir (təhlükəsizlik üçün).
    created_at ISO formatında qaytarılır.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, full_name, created_at FROM users WHERE id = %s",
        (user_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    d = dict(row)
    # Tarix formatını ISO-ya çevirmə
    if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
        d["created_at"] = d["created_at"].isoformat()
    return d


# Yeni istifadəçini verilənlər bazasına əlavə etmə
def user_insert(email_lower: str, password_hash: str, full_name: str) -> Tuple[bool, Optional[str]]:
    """
    Yeni istifadəçi qeydiyyat etmə.
    E-poçt unikal olmalıdır (duplikat ola bilməz).
    Qaytararaq: (Uğurlu yoxsa uğursuz, Xəta mesajı)
    """
    import psycopg2

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s)",
            (email_lower, password_hash, full_name),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except psycopg2.IntegrityError:
        # E-poçt artıq mövcud
        return False, "Bu e-poçt artıq qeydiyyatdan keçib."
    except Exception as ex:
        return False, str(ex)


# API ENDPOINT-LƏRİ

# Qeydiyyat endpoint-i
@app.route("/api/register", methods=["POST"])
def api_register():
    """
    Yeni istifadəçi qeydiyyat etmə.
    POST məlumatı: email, password, password_confirm, full_name
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    password2 = data.get("password_confirm") or ""
    full_name = (data.get("full_name") or "").strip()

    # Ad doğrulaması
    if not full_name or len(full_name) < 2:
        return jsonify({"ok": False, "error": "Ad ən azı 2 simvol olmalıdır."}), 400
    
    # E-poçt doğrulaması
    if not validate_email(email):
        return jsonify({"ok": False, "error": "E-poçt düzgün deyil."}), 400
    
    # Parol gücünü yoxlamaq
    ok, msg = validate_password_strength(password)
    if not ok:
        return jsonify({"ok": False, "error": msg}), 400
    
    # Parolların üst-üstə düşməsini yoxlamaq
    if password != password2:
        return jsonify({"ok": False, "error": "Parollar üst-üstə düşmür."}), 400

    # Parol hash-i yaratmaq (təhlükəsizlik üçün)
    pw_hash = generate_password_hash(password)
    # Istifadəçini verilənlər bazasına əlavə etmə
    ok_ins, err = user_insert(email.lower(), pw_hash, full_name)
    if not ok_ins:
        return jsonify({"ok": False, "error": err or "Qeydiyyat alınmadı."}), 400

    return jsonify({"ok": True, "message": "Qeydiyyat tamamlandı."})


# Giriş endpoint-i
@app.route("/api/login", methods=["POST"])
def api_login():
    """
    İstifadəçi girişi (seans açmaq).
    POST məlumatı: email, password
    Uğurlu olduqda: seansdə user_id saxlanır.
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # Giriş məlumatlarının məhdudiyyətini yoxlamaq
    ok_b, err_b = login_input_bounds(email, password)
    if not ok_b:
        return jsonify({"ok": False, "error": err_b}), 400
    
    # Zəruri məlumatların mövcudluğunu yoxlamaq
    if not validate_email(email) or not password:
        return jsonify({"ok": False, "error": "E-poçt və parol yazın."}), 400

    # Verilənlər bazasında istifadəçini axtarmaq
    row = user_get_by_email(email)
    if row is None:
        return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401

    # Parolun düzgün olmasını yoxlamaq
    ph = row.get("password_hash")
    try:
        pw_ok = bool(ph) and check_password_hash(str(ph), password)
    except (TypeError, ValueError):
        pw_ok = False
    if not pw_ok:
        return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401

    # Seansdə istifadəçi məlumatlarını saxlamaq
    session["user_id"] = row["id"]
    session["email"] = row["email"]
    u = user_get_public(row["id"])
    return jsonify({"ok": True, "message": "Xoş gəldiniz!", "user": u})


# Çıxış endpoint-i
@app.route("/api/logout", methods=["POST"])
def api_logout():
    """
    İstifadəçi seanını bitirmə (çıxış).
    Seansda saxlanılan bütün məlumatlar silinir.
    """
    session.clear()
    return jsonify({"ok": True})


# Cari istifadəçi məlumatlarını almaq
@app.route("/api/me", methods=["GET"])
def api_me():
    """
    Cari seansdakı istifadəçi məlumatlarını almaq.
    Seans daxilində user_id olmazsa, qeydiyyatsız təsir edilir.
    """
    if "user_id" not in session:
        return jsonify({"ok": False, "logged_in": False})
    u = user_get_public(session["user_id"])
    if not u:
        session.clear()
        return jsonify({"ok": False, "logged_in": False})
    return jsonify({"ok": True, "logged_in": True, "user": u})


# Sağlamlıq yoxlaması endpoint-i
@app.route("/api/health", methods=["GET"])
def api_health():
    """
    Tətbiqin və verilənlər bazasının işinin yoxlanması.
    Əgər hamı işləyirsə, OK qaytarılır.
    """
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({"ok": True, "db": "postgres"})
    except Exception as ex:
        return jsonify({"ok": False, "error": str(ex)}), 503


# Statik faylları vəzifə etmə (frontend qovluğundan)
@app.route("/", defaults={"path": "login.html"})
@app.route("/<path:path>")
def serve_file(path):
    """
    Statik faylları (HTML, CSS, JS, şəkillər) təqdim etmə.
    /api/ ilə başlayanlar API endpoint-ləri olaraq bloklanır.
    Təhlükəsizlik üçün, yalnız icazə verilən fayl növləri təqdim olunur.
    """
    # API tələblərini rədd etmə
    if path.startswith("api/"):
        return "Tapılmadı", 404
    
    # İcazə verilən fayl tipləri
    allowed = {".html", ".css", ".js", ".jpg", ".jpeg", ".png", ".ico", ".svg"}
    
    # Yol təhlükəsizliyini yoxlamaq (fayl traversal hücumundan qoruma)
    safe_path = (FRONTEND_DIR / path).resolve()
    try:
        safe_path.relative_to(FRONTEND_DIR.resolve())
    except ValueError:
        return "Forbidden", 403
    
    # Fayl mövcudluğunu yoxlamaq
    if not safe_path.is_file():
        return "Tapılmadı", 404
    
    # Fayl tipini yoxlamaq
    if safe_path.suffix.lower() not in allowed:
        return "Forbidden", 403
    
    return send_from_directory(FRONTEND_DIR, path)


# Tətbiqin başlanması
if __name__ == "__main__":
    print("Frontend:", FRONTEND_DIR)
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
