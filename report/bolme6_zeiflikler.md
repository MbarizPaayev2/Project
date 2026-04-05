# Bölmə 6 — Aşkar Edilmiş Zəifliklər və Tövsiyələr

**Fənn:** Web Təhlükəsizliyi  
**Tələbə:** [Ad Soyad]  
**Kurs:** II kurs  
**Tarix:** Aprel 2026

---

## 6.1 Giriş

Əvvəlki bölmələrdə layihənin güclü tərəfləri analiz edildi — parol hashing, SQL injection qorunması, XSS-ə qarşı tədbirlər və s. Lakin heç bir tətbiq mükəmməl deyil. Bu bölmədə layihədəki **mövcud zəiflikləri**, onların **real riskini** və hər biri üçün **konkret həll yolunu** izah edəcəm.

Zəifliklər risk səviyyəsinə görə sıralanıb:
- 🔴 **Yüksək** — istismar edilərsə ciddi ziyan verə bilər
- 🟠 **Orta** — müəyyən şərtlər altında təhlükəli
- 🟡 **Aşağı** — sənaye standartlarına uyğun olmasa da, birbaşa hücum vektoru yaratmır

---

## 6.2 Zəiflik №1 — HTTPS Yoxdur (🔴 Yüksək)

### Problemin İzahı

Layihə HTTP (şifrələnməmiş) protokol üzərində işləyir:

```python
# backend/app.py — 261-ci sətir
app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
```

Bu kodda `ssl_context` parametri yoxdur — yəni bağlantı şifrələnmir. İstifadəçi giriş etdikdə brauzerlə server arasında gedən məlumat belə görünür:

```
POST /api/login HTTP/1.1
Content-Type: application/json

{"email":"ali@mail.com","password":"Sifre123"}
```

Bu sorğu şəbəkədən **açıq mətn kimi** keçir. Eyni Wi-Fi şəbəkəsindəki (məsələn, kafe, aeroport) hər hansı biri Wireshark və ya tcpdump kimi alətlərlə bu trafiki ələ keçirə bilər. Bu, **Man-in-the-Middle (MitM)** hücumu adlanır.

Session cookie-si də eyni şəkildə şifrələnmədən göndərilir:

```
Cookie: session=eyJ1c2VyX2lkIjo0MiwiZW1haWwiOi...
```

Haker bu cookie-ni ələ keçirərsə, istifadəçinin hesabına onun adından daxil ola bilər — buna **Session Hijacking** (session oğurluğu) deyilir.

### Həll Yolu

**Production mühitdə** TLS/SSL sertifikatı istifadə etmək:

```python
# Həll yolu 1: Flask-da birbaşa (development üçün)
app.run(host="0.0.0.0", port=443, ssl_context=("cert.pem", "key.pem"))

# Həll yolu 2: Reverse proxy (production üçün — daha yaxşı)
# Nginx və ya Caddy serveri TLS-i idarə edir, Flask yalnız daxili trafik alır
```

Cookie-yə `Secure` atributu əlavə etmək:

```python
# Həll yolu: Flask konfiqurasiyası
app.config["SESSION_COOKIE_SECURE"] = True      # Cookie yalnız HTTPS ilə göndərilir
app.config["SESSION_COOKIE_HTTPONLY"] = True     # JavaScript cookie-yə çata bilməz
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"   # CSRF qorunması
```

`SESSION_COOKIE_SECURE = True` olduqda brauzer bu cookie-ni HTTP sorğularında **göndərməz** — yalnız HTTPS ilə. Bu, MitM hücumunda cookie-nin ələ keçirilməsinin qarşısını alır.

---

## 6.3 Zəiflik №2 — CSRF Qorunması Yoxdur (🟠 Orta)

### Problemin İzahı

CSRF (Cross-Site Request Forgery) — haker istifadəçinin brauzərini istifadə edərək onun adından sorğu göndərir.

Bu layihədə heç bir CSRF token mexanizmi yoxdur. Baxaq niyə bu problem ola bilər:

```javascript
// frontend/auth.js — 141-146-cı sətir
fetchJsonApi("/api/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  credentials: "same-origin",
  body: JSON.stringify({ email: email, password: pw }),
})
```

Haker öz saytında belə JavaScript yazarsa:

```javascript
// ❌ hacker-site.com-da:
fetch("http://aviakassa.com/api/logout", {
  method: "POST",
  credentials: "include"    // ← istifadəçinin cookie-sini göndər
});
```

İstifadəçi `hacker-site.com`-u açarsa və aviakassa.com-a daxil olubsa — session-ı silinə bilər.

Bu layihədə **dolayı bir qorunma var**: backend yalnız `application/json` content-type qəbul edir. HTML formaları yalnız `application/x-www-form-urlencoded` göndərə bilir — yəni klassik HTML form CSRF işləmir. Lakin JavaScript ilə cross-origin sorğu hələ də mümkündür (CORS düzgün konfiqurasiya edilməyibsə).

### Həll Yolu

**Variant 1: Flask-WTF CSRF Token**

```python
# pip install flask-wtf
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# Hər API sorğusunda:
# Request header-də X-CSRFToken olmalıdır
# Token server tərəfindən yaradılır və cookie ilə brauzərə göndərilir
```

**Variant 2: SameSite Cookie Atributu**

```python
# ən sadə həll:
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
```

`SameSite=Strict` — cookie yalnız eyni saytdan gələn sorğularda göndərilir. Başqa saytdan (`hacker-site.com`) gələn sorğularda cookie **avtomatik olaraq əlavə edilmir**. Bu, CSRF-in ən müasir və sadə həllidir.

`SameSite` dəyərləri:
| Dəyər | Mənası |
|---|---|
| `Strict` | Cookie yalnız eyni saytın sorğularında göndərilir |
| `Lax` | Cookie GET sorğularında göndərilir (link klik), POST-da yox |
| `None` | Cookie hər yerdə göndərilir (Secure atributu tələb edir) |

---

## 6.4 Zəiflik №3 — Rate Limiting Yoxdur (🟠 Orta)

### Problemin İzahı

Layihədə girış cəhdlərinə heç bir məhdudiyyət yoxdur. Haker avtomatlaşdırılmış alətlə (Hydra, Burp Suite, sadə Python scripti) saniyədə yüzlərlə parol sınaya bilər:

```python
# ❌ Haker bu scripti yazıb brute-force edə bilər:
import requests

parollar = open("rockyou.txt").readlines()    # 14 milyon parol siyahısı

for parol in parollar:
    r = requests.post("http://localhost:5000/api/login", json={
        "email": "ali@mail.com",
        "password": parol.strip()
    })
    if r.json().get("ok"):
        print("TAPILDI:", parol)
        break
```

Backend bu sorğuların heç birini bloklamır:

```python
# backend/app.py — 181-208-ci sətir
@app.route("/api/login", methods=["POST"])
def api_login():
    # ... doğrulamalar ...

    row = user_get_by_email(email)
    if row is None:
        return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401

    # ... hash yoxlaması ...
    if not pw_ok:
        return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401

    # Heç bir yerdə "neçənci cəhddir?" yoxlanılmır
    # Heç bir yerdə IP ünvanı loglanmır
    # Heç bir yerdə gecikmə (delay) tətbiq edilmir
```

Haker `rockyou.txt` kimi məşhur parol siyahıları ilə zəif parolları bir neçə dəqiqə ərzində tapa bilər. Bu, **Brute-Force Attack** adlanır.

### Həll Yolu

**Flask-Limiter kitabxanası:**

```python
# pip install flask-limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(get_remote_address, app=app)

@app.route("/api/login", methods=["POST"])
@limiter.limit("5 per minute")    # ← eyni IP-dən dəqiqədə max 5 cəhd
def api_login():
    ...
```

`"5 per minute"` — eyni IP ünvanından dəqiqədə ən çox 5 giriş cəhdi icazə verilir. 6-cı cəhddə server **HTTP 429 (Too Many Requests)** qaytarır:

```json
{"error": "Çox sayda cəhd. 1 dəqiqə gözləyin."}
```

Bu, brute-force hücumunu **çox yavaşladır**: 14 milyon parol üçün dəqiqədə 5 cəhd = 2.8 milyon dəqiqə = 5.3 il. Praktiki olaraq mümkünsüz olur.

Əlavə olaraq **progressive delay** (artan gözləmə) tətbiq etmək olar:
- 3-cü uğursuz cəhd: 5 saniyə gözlə
- 5-ci cəhd: 30 saniyə gözlə  
- 10-cu cəhd: hesabı 15 dəqiqə kilidlə

---

## 6.5 Zəiflik №4 — Security HTTP Headers Yoxdur (🟡 Aşağı)

### Problemin İzahı

HTTP cavabları ilə birlikdə göndərilən bəzi başlıqlar (headers) brauzərlərə təhlükəsizlik qaydaları bildirir. Bu layihədə heç biri tətbiq edilmir.

Hazırda server cavabı belə görünür:

```
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
```

Aşağıdakı başlıqlar əskikdir:

### Content-Security-Policy (CSP)

CSP brauzərə deyir: "Yalnız bu mənbələrdən gələn kodlara icazə ver." Əgər haker səhifəyə xarici script əlavə etməyə çalışarsa, brauzer bunu bloklayar.

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'
```

Bu başlıq belə deyir:
- `default-src 'self'` — bütün resurslar yalnız eyni domain-dən yüklənsin
- `script-src 'self'` — JavaScript yalnız öz saytımızdan icra edilsin; xarici script yox
- `style-src 'self' 'unsafe-inline'` — CSS öz saytımızdan + inline CSS icazəli

### X-Frame-Options

```
X-Frame-Options: DENY
```

Bu başlıq **Clickjacking** hücumunun qarşısını alır. Clickjacking — haker öz saytında aviakassa.com-u görünməz `<iframe>` içində yükləyir, üstündə "Pulsuz bilet qazan" düyməsi qoyur. İstifadəçi düyməyə basanda əslində aviakassa-dakı düyməyə basır.

`DENY` — bu səhifə heç bir iframe içdə yüklənə bilməz.

### X-Content-Type-Options

```
X-Content-Type-Options: nosniff
```

Brauzərlər bəzən faylın content-type-ını "təxmin etməyə" çalışır (MIME sniffing). Məsələn, `.txt` faylını HTML kimi render edə bilər. `nosniff` bunu söndürür — fayl yalnız server dediyi tip kimi işlənir.

### Həll Yolu

```python
# backend/app.py — bütün cavablara başlıq əlavə et
@app.after_request
def add_security_headers(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response
```

`@app.after_request` — Flask-da hər cavab göndərilmədən əvvəl çağırılan hook-dur. Bu funksiya bütün cavablara təhlükəsizlik başlıqları əlavə edir.

`Referrer-Policy` — başqa sayta keçid edildikdə hansı referrer məlumatı göndərilməsini idarə edir. `strict-origin-when-cross-origin` — eyni sayta tam URL, xarici sayta yalnız domain adı göndərir.

`Permissions-Policy` — veb tətbiqin kamera, mikrofon, geolokasiya kimi cihaz API-lərinə girişini bloklayır. Aviakassa-nın bunlara ehtiyacı yoxdur.

---

## 6.6 Zəiflik №5 — Account Lockout Yoxdur (🟠 Orta)

### Problemin İzahı

Rate limiting IP əsaslıdır — eyni IP-dən çox sorğunu bloklayır. Lakin haker VPN, proxy, botnet istifadə edərək fərqli IP-lərdən eyni hesaba hücum edə bilər. Bu halda rate limiting işləmir.

Account lockout — **hesab əsaslı** müdafiədir: bir hesaba N uğursuz giriş cəhdi olubsa, bu hesab müvəqqəti kilidlənir.

Hazırda backend-də belə bir mexanizm yoxdur:

```python
# backend/app.py — 193-203-cü sətir
row = user_get_by_email(email)
if row is None:
    return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401

# ... hash yoxlaması ...
if not pw_ok:
    return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401

# Uğursuz cəhd heç bir yerdə sayılmır
# Hesab heç vaxt kilidlənmir
```

### Həll Yolu

Bazaya uğursuz cəhd sayğacı əlavə etmək:

```sql
-- users cədvəlinə yeni sütunlar:
ALTER TABLE users
  ADD COLUMN failed_login_count INTEGER DEFAULT 0,
  ADD COLUMN locked_until TIMESTAMPTZ DEFAULT NULL;
```

```python
# Həll yolu: login funksiyasında
def api_login():
    ...
    row = user_get_by_email(email)
    if row is None:
        return error_response()

    # Hesab kilidlənib?
    if row.get("locked_until") and row["locked_until"] > datetime.now(timezone.utc):
        remaining = (row["locked_until"] - datetime.now(timezone.utc)).seconds // 60
        return jsonify({
            "ok": False,
            "error": f"Hesab kilidlənib. {remaining} dəqiqə gözləyin."
        }), 429

    if not check_password_hash(row["password_hash"], password):
        # Uğursuz cəhd sayğacını artır
        new_count = row["failed_login_count"] + 1
        locked = None
        if new_count >= 5:
            locked = datetime.now(timezone.utc) + timedelta(minutes=15)  # 15 dəq kilidlə
        update_login_attempts(row["id"], new_count, locked)
        return error_response()

    # Uğurlu giriş — sayğacı sıfırla
    update_login_attempts(row["id"], 0, None)
    ...
```

Bu mexanizm:
- 5 uğursuz cəhddən sonra hesab 15 dəqiqə kilidlənir
- Uğurlu girişdə sayğac sıfırlanır
- Hücumçu fərqli IP-lərdən gəlsə belə, hədəf hesab qorunur

---

## 6.7 Zəiflik №6 — Uğursuz Giriş Cəhdləri Loglanmır (🟠 Orta)

### Problemin İzahı

Backend-dəki login funksiyası uğursuz cəhdləri heç bir yerdə qeyd etmir:

```python
# backend/app.py — 194-195-ci sətir
if row is None:
    return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401
    # ← burada log yoxdur: kim, harada, nə vaxt?
```

Əgər bir hesaba gecə 3:00-da Braziliyadan 500 uğursuz cəhd olubsa — sistem administratoru bundan xəbərsiz qalır. Audit trail olmadan:
- Hücum aşkar edilə bilmir
- Hücumdan sonra təhqiqat aparmaq mümkün olmur
- Qanuni tələblərə (GDPR, PCI DSS) uyğunluq pozulur

### Həll Yolu

Python-un `logging` modulu ilə:

```python
import logging

# Logger qurulması
logging.basicConfig(
    filename="security.log",
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("auth")

@app.route("/api/login", methods=["POST"])
def api_login():
    ...
    if row is None:
        logger.warning(
            "LOGIN_FAILED email=%s ip=%s reason=user_not_found",
            email, request.remote_addr
        )
        return error_response()

    if not pw_ok:
        logger.warning(
            "LOGIN_FAILED email=%s ip=%s reason=wrong_password user_id=%s",
            email, request.remote_addr, row["id"]
        )
        return error_response()

    # Uğurlu giriş
    logger.info(
        "LOGIN_SUCCESS email=%s ip=%s user_id=%s",
        email, request.remote_addr, row["id"]
    )
    ...
```

Log faylı belə görünər:

```
2026-04-05 01:30:15 [WARNING] LOGIN_FAILED email=ali@mail.com ip=192.168.1.55 reason=wrong_password user_id=42
2026-04-05 01:30:16 [WARNING] LOGIN_FAILED email=ali@mail.com ip=192.168.1.55 reason=wrong_password user_id=42
2026-04-05 01:30:17 [WARNING] LOGIN_FAILED email=ali@mail.com ip=185.22.33.44 reason=wrong_password user_id=42
2026-04-05 01:31:02 [INFO] LOGIN_SUCCESS email=ali@mail.com ip=10.0.0.15 user_id=42
```

Bu loglar ilə administrator bir baxışda brute-force hücumunu görə bilər.

---

## 6.8 Zəiflik №7 — E-poçt Doğrulaması Yoxdur (🟡 Aşağı)

### Problemin İzahı

İstifadəçi istənilən e-poçt ünvanı ilə qeydiyyatdan keçə bilər — həqiqətən o ünvanın sahibi olub-olmadığı yoxlanılmır:

```python
# backend/app.py — 155-178-ci sətir
@app.route("/api/register", methods=["POST"])
def api_register():
    ...
    # E-poçt formatı yoxlanılır:
    if not validate_email(email):
        return jsonify({"ok": False, "error": "E-poçt düzgün deyil."}), 400

    # Amma e-poçtun REAL olub-olmadığı yoxlanılmır!
    # Heç bir doğrulama e-maili göndərilmir!

    pw_hash = generate_password_hash(password)
    ok_ins, err = user_insert(email.lower(), pw_hash, full_name)
    ...
```

Bu o deməkdir ki:
- Kimsə `prezident@gov.az` ilə qeydiyyatdan keçə bilər
- Kimsə başqasının e-poçtunu istifadə edə bilər
- Saxta hesablar kütləvi yaradıla bilər

### Həll Yolu

Qeydiyyatdan sonra doğrulama e-maili göndərmək:

```python
import secrets

# 1. Qeydiyyat zamanı:
token = secrets.token_urlsafe(32)    # təsadüfi 43 simvollu token
# Token-i bazada saxla (müddətli — məs. 24 saat)
# E-poçta link göndər:
# "http://aviakassa.com/api/verify?token=abc123..."

# 2. İstifadəçi linkə kliklədikdə:
@app.route("/api/verify")
def verify_email():
    token = request.args.get("token")
    # Token-i bazada yoxla
    # Əgər düzgündürsə → hesab aktiv
    # Əks halda → "Yanlış və ya müddəti bitmiş link"
```

`secrets.token_urlsafe(32)` — kriptoqrafik təhlükəsiz 32 bayt təsadüfi token yaradır, URL-friendly simbollarla (A-Z, a-z, 0-9, -, _).

---

## 6.9 Zəiflik №8 — DB Connection Pool Yoxdur (🟡 Aşağı)

### Problemin İzahı

Hazırda hər API sorğusu üçün yeni bağlantı açılır və sonra bağlanır:

```python
# backend/app.py — 47-51-ci sətir
def get_db():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    return psycopg2.connect(_effective_database_url(), cursor_factory=RealDictCursor)

# Hər funksiyada:
def user_get_by_email(email_lower):
    conn = get_db()       # ← yeni bağlantı AÇ
    cur = conn.cursor()
    cur.execute(...)
    row = cur.fetchone()
    cur.close()
    conn.close()          # ← bağlantı BAĞLA
    return dict(row) if row else None
```

Bir login sorğusu zamanı ən azı 2 dəfə `get_db()` çağırılır:
1. `user_get_by_email(email)` — e-poçt axtarışı
2. `user_get_public(row["id"])` — istifadəçi məlumatının alınması

Hər biri ayrı TCP bağlantısı açır, SSL əl sıxışması (handshake) edir, sonra bağlanır. Bu, kiçik layihədə problem deyil, amma yüksək trafikdə:
- PostgreSQL-in bağlantı limiti (default 100) tükənə bilər
- Hər bağlantı ~50ms vaxt alır — performans aşağı düşür
- Bağlantı açıq qalanda (connection leak) server resursları tükənir

### Həll Yolu

```python
# Connection pool istifadəsi:
from psycopg2.pool import SimpleConnectionPool

pool = SimpleConnectionPool(
    minconn=2,      # minimum açıq bağlantı
    maxconn=10,     # maksimum açıq bağlantı
    dsn=_effective_database_url()
)

def get_db():
    return pool.getconn()    # mövcud bağlantını al

def release_db(conn):
    pool.putconn(conn)       # bağlantını pool-a qaytar (bağlama!)
```

Pool mexanizmi ilə bağlantılar **yenidən istifadə edilir** — açılıb-bağlanma əvəzinə, pool-dan alınır və qaytarılır. Bu, performansı 3-5x artıra bilər.

---

## 6.10 Zəiflik №9 — Debug Rejim Production-da (🔴 Yüksək)

### Problemin İzahı

```python
# backend/app.py — 261-ci sətir
app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
```

`debug=True` — bu parametr **inkişaf mühiti üçündür**. Production-da bu ciddi təhlükədir:

1. **Xəta zamanı tam traceback göstərilir** — server fayl yolları, kod sətirləri, dəyişən dəyərləri brauzerdə görünür
2. **Werkzeug debugger aktiv olur** — brauzer vasitəsilə serverdə **Python kodu icra etmək mümkündür**
3. **Avtomatik reload** — fayl dəyişikliklərini izləyir (performans yükü)

Əgər production-da xəta baş versə, istifadəçi belə məlumat görə bilər:

```
Traceback (most recent call last):
  File "D:\login-register-only\backend\app.py", line 108, in user_get_by_email
    cur.execute("SELECT id, email, password_hash...")
psycopg2.OperationalError: connection to server at "db.example.com" (5432) refused
```

Bu, hakere baza serverinin ünvanını, fayl yollarını və SQL sorğularını göstərir.

### Həll Yolu

```python
# backend/app.py — düzəliş:
import os

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=debug_mode    # ← .env-dən oxu, default False
    )
```

```
# .env (development):
FLASK_DEBUG=true

# .env (production):
FLASK_DEBUG=false    # və ya bu sətri ümumiyyətlə yaz
```

---

## 6.11 Zəiflik №10 — Session Expiration Yoxdur (🟡 Aşağı)

### Problemin İzahı

Flask-da default olaraq session cookie-si **brauzer bağlananda** silinir (session cookie). Lakin brauzer açıq qaldığı müddətcə session aktiv qalır — 1 gün, 1 həftə, 1 ay.

```python
# backend/app.py — 205-206-cı sətir
session["user_id"] = row["id"]
session["email"] = row["email"]
# Session müddəti (expiry) təyin edilmir
```

Əgər istifadəçi ümumi kompüterdə (kitabxana, internet kafe) giriş edib çıxış etməyi unutsa, brauzer açıq qaldığı müddətcə hesab əlçatan olur.

### Həll Yolu

```python
from datetime import timedelta

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)

@app.route("/api/login", methods=["POST"])
def api_login():
    ...
    session.permanent = True    # ← session müddətli olsun
    session["user_id"] = row["id"]
    ...
```

`PERMANENT_SESSION_LIFETIME = timedelta(hours=2)` — session 2 saatdan sonra avtomatik etibarsız olur. İstifadəçi 2 saatdan sonra yenidən daxil olmalıdır.

---

## 6.12 Zəiflik №11 — Qeydiyyatda User Enumeration (🟡 Aşağı)

### Problemin İzahı

Giriş zamanı eyni xəta mesajı qaytarılır (düzgündür):

```python
# backend/app.py — 195, 203-cü sətir
return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401
# ↑ İstifadəçi yoxdur da → eyni mesaj
# ↑ Parol yanlışdır da  → eyni mesaj
```

Lakin qeydiyyatda fərqli mesaj qaytarılır:

```python
# backend/app.py — 149-150-ci sətir
except psycopg2.IntegrityError:
    return False, "Bu e-poçt artıq qeydiyyatdan keçib."
```

Haker qeydiyyat formasına müxtəlif e-poçtlar daxil edərək hansı hesabların mövcud olduğunu öyrənə bilər. Bu, **User Enumeration** hücumudur.

### Həll Yolu

```python
# Qeydiyyatda da ümumi mesaj:
def user_insert(email_lower, password_hash, full_name):
    try:
        ...
    except psycopg2.IntegrityError:
        return False, "Qeydiyyat tamamlana bilmədi. Məlumatları yoxlayın."
        # ↑ E-poçtun artıq olub-olmadığını açıq demir
```

Daha yaxşı variant: qeydiyyat həmişə "Əgər bu e-poçt istifadə edilməyibsə, təlimatlar göndərildi" mesajı qaytarsın — həqiqi doğrulama e-poçta göndərilsin.

---

## 6.13 Tam Zəiflik Matrisi

| № | Zəiflik | Risk | OWASP | Kod Nümunəsi | Həll |
|---|---|---|---|---|---|
| 1 | HTTPS yoxdur | 🔴 Yüksək | A02 | `app.run(debug=True)` | TLS/SSL + `SESSION_COOKIE_SECURE` |
| 2 | CSRF qorunması yoxdur | 🟠 Orta | A01 | `credentials: "same-origin"` | Flask-WTF token / `SameSite=Strict` |
| 3 | Rate limiting yoxdur | 🟠 Orta | A07 | `/api/login` limitsiz | Flask-Limiter, 5/dəq |
| 4 | Security headers yoxdur | 🟡 Aşağı | A05 | Cavabda CSP yox | `@app.after_request` hook |
| 5 | Account lockout yoxdur | 🟠 Orta | A07 | Cəhd sayılmır | `failed_login_count` + `locked_until` |
| 6 | Uğursuz giriş loglanmır | 🟠 Orta | A09 | `return 401` (log yox) | Python `logging` modulu |
| 7 | E-poçt doğrulaması yoxdur | 🟡 Aşağı | A07 | Birbaşa `INSERT` | Doğrulama token + e-mail |
| 8 | DB connection pool yoxdur | 🟡 Aşağı | A05 | Hər sorğuda `connect()` | `SimpleConnectionPool` |
| 9 | Debug rejim production-da | 🔴 Yüksək | A05 | `debug=True` | `.env`-dən `FLASK_DEBUG` oxu |
| 10 | Session expiration yoxdur | 🟡 Aşağı | A07 | `session.permanent` yox | `PERMANENT_SESSION_LIFETIME` |
| 11 | Register user enumeration | 🟡 Aşağı | A01 | `"Bu e-poçt artıq..."` | Ümumi mesaj qaytarmaq |

---

## 6.14 Prioritizasiya — Nədən Başlamaq?

Zəiflikləri aradan qaldırmaq üçün tövsiyə olunan sıra:

```
1. debug=True söndür           (5 dəqiqə — ən böyük risk)
2. HTTPS konfiqurasiya et      (30 dəqiqə — bütün trafiği qoruyur)
3. Security headers əlavə et   (10 dəqiqə — bir funksiya)
4. Session cookie parametrləri  (5 dəqiqə — SameSite, Secure, Expiry)
5. Rate limiting əlavə et      (20 dəqiqə — Flask-Limiter)
6. Login log əlavə et          (15 dəqiqə — logging modulu)
7. Account lockout              (45 dəqiqə — baza dəyişikliyi lazım)
8. Connection pool              (15 dəqiqə — psycopg2.pool)
9. E-poçt doğrulaması          (1-2 saat — e-mail göndərmə servisi lazım)
10. Register mesajı düzəlt     (5 dəqiqə — string dəyişikliyi)
```

İlk 4 addım 1 saatdan az vaxt alır və ən böyük riskləri aradan qaldırır.

---

*Növbəti bölmədə layihə OWASP Top 10 standartı ilə müqayisə ediləcək və yekun nəticə yazılacaq.*
