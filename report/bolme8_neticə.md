# Bölmə 8 — Nəticə

**Fənn:** Web Təhlükəsizliyi  
**Tələbə:** [Ad Soyad]  
**Kurs:** II kurs  
**Tarix:** Aprel 2026

---

## 8.1 Reportun Xülasəsi

Bu reportda **Aviakassa** layihəsinin giriş/qeydiyyat modulu web təhlükəsizlik baxımından ətraflı analiz edildi. Layihə Python (Flask), PostgreSQL və HTML/CSS/JavaScript texnologiyaları ilə qurulmuş minimal, lakin real dünya standartlarına yaxın bir autentifikasiya sistemidir.

Report 7 bölmədə layihənin aşağıdakı aspektlərini araşdırdı:

| Bölmə | Mövzu | Nəticə |
|---|---|---|
| 1 — Giriş | Layihənin təsviri, texnoloji stack, data flow | 3 qatlı arxitektura, 5 API endpoint |
| 2 — Arxitektura | Frontend / Backend / Database ayrılması | Separation of Concerns düzgün tətbiq edilib |
| 3 — Verilənlər Bazası | Schema analizi, bağlantı idarəsi | `password_hash`, `UNIQUE`, parametrized query |
| 4 — Backend Təhlükəsizlik | Hashing, SQLi, session, path traversal | 7 mexanizm analiz edildi |
| 5 — Frontend Təhlükəsizlik | HTML atributları, XSS, Fetch API, CSRF | textContent ilə XSS qorunması |
| 6 — Zəifliklər | 11 zəiflik aşkar edildi | 2 yüksək, 4 orta, 5 aşağı risk |
| 7 — OWASP Top 10 | 10 kateqoriya ilə müqayisə | 2 tam, 5 qismən, 1 zəif, 2 yoxlanılmalı |

---

## 8.2 Layihənin Güclü Tərəfləri

Bu layihədə bir neçə fundamental təhlükəsizlik prinsipi **düzgün tətbiq edilib**. Bunları xülasə edirəm:

### 8.2.1 Parol Hashing ✅

İstifadəçi parolları heç vaxt açıq saxlanılmır. Werkzeug-un sənaye standartı alqoritmi tətbiq edilib:

```python
# backend/app.py — 173-cü sətir
pw_hash = generate_password_hash(password)
```

Bu bir sətir kodun arxasında PBKDF2-SHA256 və ya scrypt alqoritmi, salt generasiyası, çoxsaylı iterasiya və timing-safe müqayisə dayanır. Real dünyada bank sistemləri, sosial şəbəkələr eyni yanaşmanı istifadə edir.

### 8.2.2 SQL Injection Qorunması ✅

Layihədəki **bütün** SQL sorğuları (5 ədəd) parametrized query ilə yazılıb:

```python
# backend/app.py — 107-110-cu sətir
cur.execute(
    "SELECT id, email, password_hash, full_name FROM users WHERE lower(email) = %s",
    (email_lower,),
)
```

OWASP A03 (Injection) kateqoriyasında tam qorunma. Heç bir SQL sorğusunda string birləşdirmə yoxdur.

### 8.2.3 XSS Qorunması ✅

Bütün dinamik DOM əməliyyatları `textContent` ilə idarə olunur:

```javascript
// frontend/auth.js — 10-cu sətir
msgEl.textContent = text || "";

// frontend/logged-in.html — 46-cı sətir
info.textContent = (d.user.full_name || d.user.email) + " · " + d.user.email;
```

`innerHTML` yalnız bir yerdə istifadə edilir və orada sabit HTML string var — dinamik dəyər yoxdur. XSS riski sıfırdır.

### 8.2.4 Path Traversal Qorunması ✅

```python
# backend/app.py — 247-251-ci sətir
safe_path = (FRONTEND_DIR / path).resolve()
try:
    safe_path.relative_to(FRONTEND_DIR.resolve())
except ValueError:
    return "Forbidden", 403
```

`.resolve()` + `.relative_to()` kombinasiyası ilə `../../.env` kimi hücum cəhdləri bloklanır. Əlavə olaraq icazə verilmiş uzantılar siyahısı (`.html`, `.css`, `.js` və s.) var.

### 8.2.5 Defense in Depth ✅

Doğrulama həm client-side (JavaScript), həm server-side (Python) tərəfdə aparılır:

```javascript
// frontend/auth.js — 50-ci sətir (client)
function parolQeydiyyat(pw) {
    if (!pw || pw.length < 8) return "...";
    ...
}
```

```python
# backend/app.py — 86-cı sətir (server)
def validate_password_strength(pw: str) -> Tuple[bool, str]:
    if not pw or len(pw) < 8:
        return False, "..."
    ...
```

Haker JavaScript-i keçsə belə, eyni yoxlama serverdə onu gözləyir.

### 8.2.6 User Enumeration Qorunması ✅

```python
# backend/app.py — 195, 203-cü sətir
return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401
```

İstifadəçi yoxdur da, parol yanlışdır da — eyni mesaj, eyni HTTP kodu. Haker hansı e-poçtların qeydiyyatlı olduğunu login formasından öyrənə bilmir.

### 8.2.7 Input Bounds Checking ✅

```python
# backend/app.py — 96-101-ci sətir
def login_input_bounds(email: str, password: str):
    if len(email) > 254 or len(password) > 256:
        return False, "E-poçt və ya parol çox uzundur."
    if "\x00" in email or "\x00" in password:
        return False, "Yanlış simvol."
    return True, None
```

RFC standartına uyğun uzunluq limitləri, null byte injection bloku.

---

## 8.3 Layihənin Zəif Tərəfləri

Analiz zamanı 11 zəiflik aşkar edildi. Bunlardan ən kritik olanları:

### Yüksək Risk (🔴):

| Zəiflik | Problem | Həll Müddəti |
|---|---|---|
| HTTPS yoxdur | Parol və session cookie şifrələnmədən ötürülür | ~30 dəqiqə |
| Debug rejim açıqdır | Werkzeug debugger + traceback-lər | ~5 dəqiqə |

### Orta Risk (🟠):

| Zəiflik | Problem | Həll Müddəti |
|---|---|---|
| CSRF qorunması yoxdur | Başqa saytdan saxta sorğu göndərilə bilər | ~20 dəqiqə |
| Rate limiting yoxdur | Sonsuz brute-force cəhdi mümkündür | ~20 dəqiqə |
| Account lockout yoxdur | Hesab kilidlənmir | ~45 dəqiqə |
| Loqlama yoxdur | Hücumlar aşkar edilə bilmir | ~15 dəqiqə |

### Aşağı Risk (🟡):

| Zəiflik | Problem |
|---|---|
| Security headers yoxdur | CSP, X-Frame-Options əskikdir |
| E-poçt doğrulaması yoxdur | Saxta e-poçtla qeydiyyat mümkündür |
| DB connection pool yoxdur | Yüksək trafikdə performans düşə bilər |
| Session expiration yoxdur | Session müddətsiz aktiv qalır |
| Register user enumeration | "Bu e-poçt artıq var" mesajı |

---

## 8.4 OWASP Top 10 Uyğunluq Nəticəsi

10 kateqoriyanın qiymətləndirilməsi:

```
Tam qorunma (✅):     2 / 10    (A03 Injection, A10 SSRF)
Qismən qorunma (⚠️):  6 / 10    (A01, A02, A04, A05, A07, A09)
Yoxlanılmalı (ℹ️):     2 / 10    (A06, A08)
```

Bu nəticə göstərir ki, layihə **əsas injection hücumlarına** qarşı güclüdür, lakin **operasional təhlükəsizlik** (logging, monitoring, rate limiting, konfiqurasiya) sahəsində təkmilləşməyə ehtiyac var.

---

## 8.5 Öyrənilən Əsas Dərslər

Bu layihənin analizi zamanı bir neçə mühüm web təhlükəsizlik prinsipi praktikada müşahidə edildi:

### Dərs 1: Frontend Doğrulaması Güvənlik Deyil

JavaScript-dəki doğrulamalar istifadəçiyə tez geri bildiriş vermək üçündür. Haker brauzerin developer tools-u ilə JavaScript-i söndürə, dəyişdirə və ya birbaşa API-yə `curl` ilə sorğu göndərə bilər. **Həqiqi güvənlik həmişə backend-dədir.**

### Dərs 2: Hər Şeyi Logla

Əgər hücumu görmürsənsə, qarşısını ala bilməzsən. Bu layihədə uğursuz giriş cəhdləri, path traversal cəhdləri heç bir yerdə qeyd edilmir. Real dünyada SIEM (Security Information and Event Management) sistemləri logları analiz edərək hücumları real-time aşkar edir.

### Dərs 3: Bir Xət Müdafiə Kifayət Deyil

Bu layihə "bir xətt" müdafiə yaxşı nümunəsidir: parol hash-lənir (bir qat), amma HTTPS yoxdur (başqa qat yoxdur). Parol bazada qorunsa da, yolda oğurlanır. **Defense in Depth** — hər qatda müdafiə olmalıdır.

### Dərs 4: Default Konfiqurasiya Təhlükəlidir

`debug=True`, `SameSite` təyin edilməmiş cookie, security headers olmadan — bunların hamısı default dəyərlərdir. Real dünyada default konfiqurasiyalar çox vaxt **ən az təhlükəsiz** olanıdır. Hər konfiqurasiyanı **açıq şəkildə** təyin etmək lazımdır.

### Dərs 5: Sadə ≠ Zəif

Bu layihə yalnız 262 sətir Python, 265 sətir JavaScript və 11 sətir SQL-dən ibarətdir. Lakin bu kiçik kod bazasında:
- SQL injection tam bloklanıb
- Parol hashing sənaye standartındadır
- XSS riski sıfırdır
- Path traversal qorunması güclüdür

Bu onu göstərir ki, təhlükəsiz kod yazmaq üçün böyük framework-lər lazım deyil — düzgün prinsipləri bilmək və tətbiq etmək kifayətdir.

---

## 8.6 Gələcək İnkişaf Üçün Yol Xəritəsi

Bu layihəni tam production-a hazır vəziyyətə gətirmək üçün tövsiyə olunan addımlar:

### Faza 1 — Kritik Düzəlişlər (1 gün):

```python
# 1. Debug rejimi söndür
debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
app.run(debug=debug_mode)

# 2. Session cookie parametrləri
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)

# 3. Security headers
@app.after_request
def security_headers(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
```

### Faza 2 — Əsas Qorunma (1 həftə):

```python
# 4. Rate limiting
from flask_limiter import Limiter
limiter = Limiter(app=app, key_func=get_remote_address)

@app.route("/api/login", methods=["POST"])
@limiter.limit("5 per minute")
def api_login(): ...

# 5. Təhlükəsizlik loqu
import logging
logger = logging.getLogger("security")

# 6. Account lockout
# failed_login_count + locked_until sütunları
```

### Faza 3 — Tam Sistem (1 ay):

```
7. HTTPS (Let's Encrypt / Caddy reverse proxy)
8. E-poçt doğrulaması (SMTP / SendGrid inteqrasiyası)
9. Parol sıfırlama funksiyası
10. Connection pooling (psycopg2.pool)
11. Versiya pinləmə (requirements.txt-də == operatoru)
12. CAPTCHA (reCAPTCHA v3) qeydiyyat formasında
```

---

## 8.7 Yekun Qiymətləndirmə

| Kriteriya | Qiymət | İzah |
|---|---|---|
| **Parol Qorunması** | 9/10 | scrypt/PBKDF2 hash, salt, timing-safe müqayisə |
| **SQL Injection** | 10/10 | Bütün sorğular parametrized |
| **XSS Qorunması** | 10/10 | textContent, innerHTML yalnız sabit dəyərlə |
| **Input Validation** | 8/10 | Client + server; RFC uyğun limitlər; sadə email regex |
| **Session İdarəetməsi** | 6/10 | İmzalı cookie var; HTTPS, SameSite, expiry yoxdur |
| **Path Traversal** | 9/10 | resolve + relative_to + uzantı filtri |
| **Konfiqurasiya** | 4/10 | debug=True, headers yox |
| **Logging** | 2/10 | Yalnız print(), strukturlaşdırılmış log yoxdur |
| **Brute-force Qorunması** | 1/10 | Rate limit və lockout yoxdur |
| **Arxitektura** | 8/10 | 3-tier, separation of concerns, .env ayrılığı |

**Ümumi ortalama: 6.7 / 10**

Bu qiymət göstərir ki, layihə **fundamental təhlükəsizlik prinsiplərini** (A03 Injection, Kriptoqrafiya) çox yaxşı tətbiq edir — bu, kod yazan tələbənin bu sahədə biliyinin olduğunu sübut edir. Əsas inkişaf sahəsi isə **operasional təhlükəsizlikdir** — logging, monitoring, rate limiting, konfiqurasiya sıxılaşdırması. Bu sahələr əlavə kitabxanalar (Flask-Limiter, Flask-Talisman) və konfiqurasiya dəyişiklikləri ilə qısa müddətdə həll edilə bilər.

---

## 8.8 İstifadə Edilən Mənbələr

1. OWASP Top 10:2021 — https://owasp.org/Top10/
2. Flask Documentation — https://flask.palletsprojects.com/
3. Werkzeug Security — https://werkzeug.palletsprojects.com/en/stable/utils/#module-werkzeug.security
4. psycopg2 Documentation — https://www.psycopg.org/docs/
5. RFC 5321 (SMTP) — https://datatracker.ietf.org/doc/html/rfc5321
6. MDN Web Docs: textContent vs innerHTML — https://developer.mozilla.org/en-US/docs/Web/API/Node/textContent
7. MDN Web Docs: Fetch API — https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
8. NIST SP 800-63B (Digital Identity Guidelines) — https://pages.nist.gov/800-63-3/sp800-63b.html

---

*Report sonu.*
