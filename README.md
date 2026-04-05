# Login / Register — minimal paket

Ana `WebSec` layihəsindən **ayrıca** qovluq: yalnız **giriş**, **qeydiyyat**, **sessiya** (`/api/me`, `/api/logout`) və **`users`** cədvəli.

Burada SQLi lab, panel, admin və s. **yoxdur**.

## Struktur

```
login-register-only/
├── backend/app.py          # Flask: /api/register, /api/login, /api/logout, /api/me, /api/health
├── database/schema.sql     # Yalnız users cədvəli (əl ilə psql üçün)
├── frontend/
│   ├── login.html
│   ├── register.html
│   ├── logged-in.html      # Uğurlu girişdən sonra
│   ├── auth.js
│   ├── style.css           # Ana layihədən kopya (böyük fayl)
│   └── aviakassa-background.jpg  # Əgər yoxdursa, fon şəkli əlavə edin
├── requirements.txt
├── .env.example
└── README.md
```

## Quraşdırma

```bash
cd login-register-only
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`.env` yaradın (`.env.example` əsasında): `DATABASE_URL`, `FLASK_SECRET_KEY`.

## İşə salma

**Paket kökündən** (bu qovluğun içindən):

```bash
python backend/app.py
```

Brauzer: `http://127.0.0.1:5000/login.html`

Sağlamlıq: `GET http://127.0.0.1:5000/api/health`

## Verilənlər bazası

`backend/app.py` işə düşəndə `users` cədvəli avtomatik yaradılır. Əl ilə sxem üçün: `database/schema.sql`.

## Qeyd

Ana repozitoriyadakı tam tətbiqlə **eyni PostgreSQL bazasını** paylaşsanız, mövcud `users` cədvəli istifadə olunur (struktur uyğun olmalıdır).
