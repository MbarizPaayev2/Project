# 🔐 Web Təhlükəsizlik — Kurs Tapşırığı

**Aviakassa** veb tətbiqinin təhlükəsizlik auditi və hesabatı.

## 📋 Tapşırığın məqsədi

Bu layihədə real veb tətbiq nümunəsi (Aviakassa — aviabilet satış sistemi) üzərində **təhlükəsizlik analizi** aparılmışdır. Məqsəd tətbiqin backend və frontend komponentlərinin təhlükəsizlik baxımından qiymətləndirilməsi, zəifliklərin aşkarlanması və OWASP Top 10 standartlarına uyğunluğunun yoxlanmasıdır.

## 📁 Layihə strukturu

```
├── backend/
│   └── app.py                  # Flask backend (API endpointləri)
├── database/
│   └── schema.sql              # PostgreSQL verilənlər bazası sxemi
├── frontend/
│   ├── login.html              # Giriş səhifəsi
│   ├── register.html           # Qeydiyyat səhifəsi
│   ├── logged-in.html          # İstifadəçi paneli
│   ├── auth.js                 # Autentifikasiya JS
│   └── style.css               # Stil faylı
├── report/                     # 📝 Təhlükəsizlik hesabatı
│   ├── bolme1_giris.md         # Giriş və ümumi məlumat
│   ├── bolme2_arxitektura.md   # Arxitektura və texnologiyalar
│   ├── bolme3_database.md      # Verilənlər bazası təhlükəsizliyi
│   ├── bolme4_backend_security.md   # Backend təhlükəsizliyi
│   ├── bolme5_frontend_security.md  # Frontend təhlükəsizliyi
│   ├── bolme6_zeiflikler.md    # Aşkarlanan zəifliklər
│   ├── bolme7_owasp_top10.md   # OWASP Top 10 analizi
│   └── bolme8_neticə.md        # Nəticə və tövsiyələr
├── requirements.txt
└── README.md
```

## 📝 Hesabat bölmələri

| # | Bölmə | Məzmun |
|---|-------|--------|
| 1 | **Giriş** | Layihənin təsviri, məqsəd və aktuallıq |
| 2 | **Arxitektura** | Texnologiya yığını, sistem arxitekturası |
| 3 | **Verilənlər bazası** | DB sxemi, sorğular, təhlükəsizlik mexanizmləri |
| 4 | **Backend təhlükəsizliyi** | Autentifikasiya, sessiya, giriş nəzarəti |
| 5 | **Frontend təhlükəsizliyi** | XSS qorunma, form validasiya, CORS |
| 6 | **Zəifliklər** | Aşkarlanan boşluqlar və risk dərəcələri |
| 7 | **OWASP Top 10** | Hər bir OWASP kateqoriyasına uyğunluq |
| 8 | **Nəticə** | Yekun qiymətləndirmə və tövsiyələr |

## 🛠 Texnologiyalar

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Verilənlər bazası:** PostgreSQL
- **Təhlükəsizlik standartı:** OWASP Top 10

## 🚀 Quraşdırma və işə salma

```bash
# Virtual mühit yaradın
python -m venv .venv
.venv\Scripts\activate

# Asılılıqları quraşdırın
pip install -r requirements.txt

# .env faylı yaradın (.env.example əsasında)
# DATABASE_URL və FLASK_SECRET_KEY dəyişənlərini təyin edin

# Tətbiqi işə salın
python backend/app.py
```

Brauzer: `http://127.0.0.1:5000/login.html`

## 👤 Müəllif

**Mübariz Paşayev** — 2-ci kurs tələbəsi
