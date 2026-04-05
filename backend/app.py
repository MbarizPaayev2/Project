# -*- coding: utf-8 -*-
"""
Minimal Flask: yalnız /api/register, /api/login, /api/logout, /api/me + statik frontend.
İşə salma (layihə kökündən): python backend/app.py
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

load_dotenv(PROJECT_ROOT / ".env", override=True)
load_dotenv(BACKEND_DIR / ".env", override=True)

DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()
if not DATABASE_URL:
    print(
        "DATABASE_URL boşdur. .env faylında məs. "
        "DATABASE_URL=postgresql://user:pass@localhost:5432/dbname",
        file=sys.stderr,
    )
    sys.exit(1)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)


def _effective_database_url() -> str:
    parsed = urlparse(DATABASE_URL)
    qs = parse_qs(parsed.query)
    keys_lower = {k.lower() for k in qs}
    if os.environ.get("VERCEL") and "sslmode" not in keys_lower:
        qs["sslmode"] = ["require"]
    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def get_db():
    import psycopg2
    from psycopg2.extras import RealDictCursor

    return psycopg2.connect(_effective_database_url(), cursor_factory=RealDictCursor)


def init_db():
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


try:
    init_db()
except Exception as ex:
    print("DB init:", ex)


def validate_email(email: str) -> bool:
    email = (email or "").strip()
    if len(email) < 5 or "@" not in email or "." not in email.split("@")[-1]:
        return False
    return True


def validate_password_strength(pw: str) -> Tuple[bool, str]:
    if not pw or len(pw) < 8:
        return False, "Parol ən azı 8 simvol olmalıdır."
    if not any(c.isalpha() for c in pw):
        return False, "Parolda ən azı bir hərf olmalıdır."
    if not any(c.isdigit() for c in pw):
        return False, "Parolda ən azı bir rəqəm olmalıdır."
    return True, ""


def login_input_bounds(email: str, password: str) -> Tuple[bool, Optional[str]]:
    if len(email) > 254 or len(password) > 256:
        return False, "E-poçt və ya parol çox uzundur."
    if "\x00" in email or "\x00" in password:
        return False, "Yanlış simvol."
    return True, None


def user_get_by_email(email_lower: str) -> Optional[Dict[str, Any]]:
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


def user_get_public(user_id: Any) -> Optional[Dict[str, Any]]:
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
    if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
        d["created_at"] = d["created_at"].isoformat()
    return d


def user_insert(email_lower: str, password_hash: str, full_name: str) -> Tuple[bool, Optional[str]]:
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
        return False, "Bu e-poçt artıq qeydiyyatdan keçib."
    except Exception as ex:
        return False, str(ex)


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    password2 = data.get("password_confirm") or ""
    full_name = (data.get("full_name") or "").strip()

    if not full_name or len(full_name) < 2:
        return jsonify({"ok": False, "error": "Ad ən azı 2 simvol olmalıdır."}), 400
    if not validate_email(email):
        return jsonify({"ok": False, "error": "E-poçt düzgün deyil."}), 400
    ok, msg = validate_password_strength(password)
    if not ok:
        return jsonify({"ok": False, "error": msg}), 400
    if password != password2:
        return jsonify({"ok": False, "error": "Parollar üst-üstə düşmür."}), 400

    pw_hash = generate_password_hash(password)
    ok_ins, err = user_insert(email.lower(), pw_hash, full_name)
    if not ok_ins:
        return jsonify({"ok": False, "error": err or "Qeydiyyat alınmadı."}), 400

    return jsonify({"ok": True, "message": "Qeydiyyat tamamlandı."})


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    ok_b, err_b = login_input_bounds(email, password)
    if not ok_b:
        return jsonify({"ok": False, "error": err_b}), 400
    if not validate_email(email) or not password:
        return jsonify({"ok": False, "error": "E-poçt və parol yazın."}), 400

    row = user_get_by_email(email)
    if row is None:
        return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401

    ph = row.get("password_hash")
    try:
        pw_ok = bool(ph) and check_password_hash(str(ph), password)
    except (TypeError, ValueError):
        pw_ok = False
    if not pw_ok:
        return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401

    session["user_id"] = row["id"]
    session["email"] = row["email"]
    u = user_get_public(row["id"])
    return jsonify({"ok": True, "message": "Xoş gəldiniz!", "user": u})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/me", methods=["GET"])
def api_me():
    if "user_id" not in session:
        return jsonify({"ok": False, "logged_in": False})
    u = user_get_public(session["user_id"])
    if not u:
        session.clear()
        return jsonify({"ok": False, "logged_in": False})
    return jsonify({"ok": True, "logged_in": True, "user": u})


@app.route("/api/health", methods=["GET"])
def api_health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({"ok": True, "db": "postgres"})
    except Exception as ex:
        return jsonify({"ok": False, "error": str(ex)}), 503


@app.route("/", defaults={"path": "login.html"})
@app.route("/<path:path>")
def serve_file(path):
    if path.startswith("api/"):
        return "Tapılmadı", 404
    allowed = {".html", ".css", ".js", ".jpg", ".jpeg", ".png", ".ico", ".svg"}
    safe_path = (FRONTEND_DIR / path).resolve()
    try:
        safe_path.relative_to(FRONTEND_DIR.resolve())
    except ValueError:
        return "Forbidden", 403
    if not safe_path.is_file():
        return "Tapılmadı", 404
    if safe_path.suffix.lower() not in allowed:
        return "Forbidden", 403
    return send_from_directory(FRONTEND_DIR, path)


if __name__ == "__main__":
    print("Frontend:", FRONTEND_DIR)
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
