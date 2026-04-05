# Bölmə 1 — Giriş

**Fənn:** Web Təhlükəsizliyi  
**Tələbə:** Mubariz Pashayev
**Kurs:** II kurs  
**Tarix:** Aprel 2026

---

## 1.1 Layihə Haqqında

Bu report **Aviakassa** adlı veb layihəsinin giriş-qeydiyyat modulunu — yəni istifadəçilərin sistemə necə daxil olduğunu, parolların necə qorunduğunu və bu prosesdə hansı təhlükəsizlik mexanizmlərinin tətbiq edildiyini analiz edir.

Aviakassa, aviabilet satışı üçün nəzərdə tutulmuş, sadə amma real texnologiyalarla qurulmuş bir veb tətbiqidir. Bu layihənin **yalnız bir hissəsi** — istifadəçi girişi (login) və qeydiyyat (register) modulu — burada araşdırılır.

Layihə üç əsas hissədən ibarətdir:

| Hissə | Texnologiya | Məqsəd |
|---|---|---|
| **Backend** | Python + Flask | API sorğularını qəbul edir, iş məntiqi burada işləyir |
| **Frontend** | HTML + CSS + JavaScript | İstifadəçinin gördüyü səhifələr |
| **Verilənlər Bazası** | PostgreSQL | İstifadəçi məlumatlarını saxlayır |

---

## 1.2 Texnoloji Stack

Layihənin `requirements.txt` faylına baxdıqda istifadə edilən kitabxanalar görünür:

```
flask>=3.0.0
python-dotenv>=1.0.0
psycopg2-binary>=2.9.9
```

Bu üç kitabxananın hər birinin rolu var:

**`flask>=3.0.0`** — Python üçün yüngül veb çərçivəsidir (framework). Flask vasitəsilə URL-lərə (endpoint-lərə) funksiyalar bağlanır. Məsələn, `/api/login` ünvanına göndərilən sorğu Flask tərəfindən uyğun funksiyana yönləndirilir:

```python
# backend/app.py — 181-ci sətir
@app.route("/api/login", methods=["POST"])
def api_login():
    ...
```

Burada `@app.route("/api/login", methods=["POST"])` o deməkdir ki: "Brauzer `/api/login` ünvanına `POST` sorğusu göndərəndə, aşağıdakı `api_login()` funksiyasını çalışdır."

---

**`python-dotenv>=1.0.0`** — Gizli məlumatları (parol, verilənlər bazası ünvanı və s.) birbaşa kodun içinə yazmamaq üçün `.env` faylından oxuyur. Bu, təhlükəsizlik baxımından çox vacibdir — çünki kod GitHub-a yüklənəndə `.env` faylı yüklənmir, gizli qalır.

`.env.example` faylında bunlar göstərilib:
```
FLASK_SECRET_KEY=uzun-tesadufi-mətn
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

Kod bu dəyərləri belə oxuyur:
```python
# backend/app.py — 21-22-ci sətir
load_dotenv(PROJECT_ROOT / ".env", override=True)
load_dotenv(BACKEND_DIR / ".env", override=True)

DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()
```

Əgər `DATABASE_URL` boşdursa, kod işə düşmür — bu da təhlükəsizlik üçün düzgün yanaşmadır, çünki konfiqurasiyasız sistem çalışmamalıdır:

```python
# backend/app.py — 25-31-ci sətir
if not DATABASE_URL:
    print(
        "DATABASE_URL boşdur. .env faylında məs. "
        "DATABASE_URL=postgresql://user:pass@localhost:5432/dbname",
        file=sys.stderr,
    )
    sys.exit(1)   # ← proqram burada dayanır
```

---

**`psycopg2-binary>=2.9.9`** — Python-dan PostgreSQL verilənlər bazasına qoşulmaq üçün istifadə olunan kitabxanadır. Bütün `SELECT`, `INSERT` sorğuları bu kitabxana vasitəsilə işləyir.

```python
# backend/app.py — 47-51-ci sətir
def get_db():
    import psycopg2
    from psycopg2.extras import RealDictCursor

    return psycopg2.connect(_effective_database_url(), cursor_factory=RealDictCursor)
```

Burada `RealDictCursor` parametri verilənlər bazasından gələn cərgələri Python lüğəti (dictionary) kimi qaytarır. Yəni `row["email"]` kimi əlçatan olur, indeks nömrəsi ilə deyil — bu kodu daha oxunaqlı edir.

---

## 1.3 Layihənin Qovluq Strukturu

Layihə açıq və anlaşılan bir quruluşa malikdir:

```
login-register-only/
│
├── backend/
│   └── app.py              ← Bütün API endpoint-ləri burada
│
├── frontend/
│   ├── login.html          ← Giriş forması
│   ├── register.html       ← Qeydiyyat forması
│   ├── logged-in.html      ← Uğurlu girişdən sonra göstərilən səhifə
│   ├── auth.js             ← Formların işi üçün JavaScript
│   └── style.css           ← Vizual dizayn
│
├── database/
│   └── schema.sql          ← Verilənlər bazası cədvəlinin sxemi
│
├── requirements.txt        ← Python kitabxanaları siyahısı
├── .env.example            ← Konfiqurasiya şablonu
└── README.md               ← İşə salma təlimatı
```

Bu quruluş **Separation of Concerns** (vəzifələrin ayrılması) prinsipinə əsaslanır — hər hissə öz işini görür, bir-birinə qarışmır. Bu, həm kodun oxunmasını, həm də təhlükəsizlik auditini asanlaşdırır: backend kodunu yoxlamaq istəyirsənsə — yalnız `backend/app.py`-ə baxmaq kifayətdir.

---

## 1.4 Arxitektura: 3 Qatlı Model

Layihə **3 qatlı arxitektura** (Three-Tier Architecture) modelinə uyğun qurulub. Bu model veb tətbiqetmə mühəndisliyinin əsas dizayn nümunələrindən biridir:

```
┌──────────────────────────────────┐
│  PRESENTATION LAYER (Frontend)   │
│  login.html · register.html      │
│  auth.js · style.css             │
└────────────────┬─────────────────┘
                 │  HTTP sorğusu (JSON)
                 ▼
┌──────────────────────────────────┐
│  LOGIC LAYER (Backend)           │
│  Flask · app.py                  │
│  /api/login · /api/register      │
│  /api/logout · /api/me           │
└────────────────┬─────────────────┘
                 │  SQL sorğusu
                 ▼
┌──────────────────────────────────┐
│  DATA LAYER (Database)           │
│  PostgreSQL · users cədvəli      │
└──────────────────────────────────┘
```

**Niyə bu vacibdir?** Təhlükəsizlik baxımından bu ayrılma çox önəmlidir: istifadəçi birbaşa verilənlər bazasına çatmır — mütləq backend-dən keçməlidir. Backend isə hər sorğunu yoxlayır, doğrulayır, icazə verir ya da rədd edir.

---

## 1.5 İstifadəçi Axını (Data Flow)

Bir istifadəçi sistemə daxil olmaq istədikdə prosesə nələr baş verir? Addım-addım izah edək:

```
1. İstifadəçi login.html-i açır
        │
        ▼
2. E-poçt və parol daxil edir, "Daxil ol" düyməsinə basır
        │
        ▼
3. auth.js — əvvəlcə JavaScript ilə yoxlayır:
   ├── E-poçt formatı düzgündürmü? (@ işarəsi var?)
   └── Parol sahəsi boşdurmu?
        │
        ▼
4. POST /api/login sorğusu göndərilir (JSON formatında):
   { "email": "...", "password": "..." }
        │
        ▼
5. Flask (app.py) sorğunu alır:
   ├── Uzunluq yoxlaması (email ≤ 254, şifrə ≤ 256)
   ├── Null byte yoxlaması (\x00 var?)
   ├── E-poçt formatı yoxlaması
   └── Verilənlər bazasında e-poçtu axtarır
        │
        ▼
6. PostgreSQL — "bu e-poçt bazadadır?"
   ├── YOX → "E-poçt və ya parol səhvdir" (401)
   └── HƏ  → parol hash-ini çıxarır
        │
        ▼
7. Flask — parol hash-i yoxlanılır:
   ├── hash uyğun gəlmir → "E-poçt və ya parol səhvdir" (401)
   └── uyğun gəlir       → session yaradılır
        │
        ▼
8. Session cookie brauzərə göndərilir
        │
        ▼
9. auth.js — uğurlu cavab alır, 500ms sonra:
   window.location.href = "logged-in.html"
        │
        ▼
10. logged-in.html açılır → /api/me sorğusu göndərir
    → Flask session-ı yoxlayır → istifadəçi məlumatını qaytarır
```

Bu axının hər addımında müəyyən təhlükəsizlik yoxlamaları mövcuddur — bu reportun sonrakı bölmələrində hər biri ətraflı analiz ediləcək.

---

## 1.6 Reportun Məqsədi və Araşdırma Sualları

Bu report aşağıdakı sualları cavablandırmağı hədəf götürür:

**1. Parollar necə qorunur?**  
İstifadəçinin daxil etdiyi parol verilənlər bazasına birbaşa yazılırmı, yoxsa hansısa kriptoqrafik emal keçirilirmi?

**2. SQL Injection mümkündürmü?**  
Bir hacker e-poçt sahəsinə `' OR 1=1 --` kimi kod yazarsa nə baş verər?

**3. Giriş doğrulaması kifayət qədər güclüdürmü?**  
Çox uzun, xüsusi simvol içərən, boş girişlər sistemi sıradan çıxara bilərmi?

**4. Session idarəetməsi etibarlıdırmı?**  
İstifadəçi çıxış etdikdə session tam silinirmi? Session-u başqa biri oğurlaya bilərmi?

**5. Hansı zəifliklər mövcuddur?**  
Tətbiq edilən qorunma mexanizmləri nə dərəcədə tam və kifayətlidir?

---

## 1.7 İstifadə Edilən Analiz Metodologiyası

Bu layihəni analiz etmək üçün aşağıdakı metodlardan istifadə edilib:

- **Statik Kod Analizi** — Kodu birbaşa oxumaq, şübhəli yerləri müəyyən etmək
- **OWASP Top 10 çərçivəsi** — Dünyada ən çox rast gəlinən 10 veb zəifliklə müqayisə
- **Manual Test** — Müxtəlif giriş scenariləri ilə əl ilə yoxlama (boş sahələr, çox uzun mətnlər, xüsusi simvollar)

**OWASP (Open Web Application Security Project)** — veb tətbiqlərinin təhlükəsizliyini artırmaq üçün yaradılmış beynəlxalq bir qeyri-hökumət təşkilatıdır. Onların nəşr etdiyi "Top 10" siyahısı hər il dünya üzrə ən çox istismar edilən veb zəifliklərini sıralar. Bu report Bölmə 7-də layihəni həmin siyahıyla müqayisə edəcək.

---

*Növbəti bölmədə layihənin verilənlər bazası sxemi və istifadəçi məlumatlarının saxlanma üsulu ətraflı araşdırılacaq.*
