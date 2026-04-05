# Bölmə 7 — OWASP Top 10 ilə Müqayisə

**Fənn:** Web Təhlükəsizliyi  
**Tələbə:** Mubariz Pashayev  
**Kurs:** II kurs  
**Tarix:** Aprel 2026

---

## 7.1 OWASP Nədir?

**OWASP (Open Web Application Security Project)** — 2001-ci ildə yaradılmış beynəlxalq qeyri-kommersiya təşkilatıdır. Məqsədi veb tətbiqlərinin təhlükəsizliyini artırmaqdır. OWASP könüllü mütəxəssislər tərəfindən idarə olunur və bütün materialları pulsuzdur.

OWASP-ın ən məşhur nəşri **"Top 10"** siyahısıdır — dünya üzrə veb tətbiqlərində ən çox rast gəlinən 10 təhlükəsizlik riskini sıralayır. Bu siyahı hər 3-4 ildən bir yenilənir. Ən son versiya **OWASP Top 10:2021**-dir.

Bu siyahı:
- Proqramçılara — nəyə diqqət etmək lazım olduğunu göstərir
- Şirkətlərə — audit zamanı standart çərçivə verir
- Tələbələrə — veb təhlükəsizliyini sistematik öyrənmək üçün əsas mənbədir

Bu bölmədə Aviakassa layihəsini OWASP Top 10:2021 siyahısının **hər bir maddəsi** ilə müqayisə edəcəm.

---

## 7.2 A01:2021 — Broken Access Control (Sınıq Giriş Nəzarəti)

### Nə deməkdir?

İstifadəçilərin icazə verilməyən resurslara çatması və ya başqasının məlumatlarını görməsi. Məsələn, adi istifadəçinin admin panel-ə girməsi, və ya bir istifadəçinin başqasının hesab məlumatlarını oxuması.

### Bu Layihədə Vəziyyət: ⚠️ Qismən Qorunub

**Müsbət:** `/api/me` endpointi session yoxlayır:

```python
# backend/app.py — 217-225-ci sətir
@app.route("/api/me", methods=["GET"])
def api_me():
    if "user_id" not in session:
        return jsonify({"ok": False, "logged_in": False})
    u = user_get_public(session["user_id"])
    if not u:
        session.clear()
        return jsonify({"ok": False, "logged_in": False})
    return jsonify({"ok": True, "logged_in": True, "user": u})
```

Session-da `user_id` yoxdursa — istifadəçi daxil deyil, məlumat verilmir. Bu, əsas access control mexanizmidir.

**Mənfi:** Centralized auth middleware yoxdur. Hazırda yalnız `/api/me` session yoxlayır, çünki sistemdə yalnız bu endpoint qorunan resurs qaytarır. Lakin sistema yeni endpoint əlavə edilsə (məsələn `/api/profile/update`), developer unutub session yoxlamasını əlavə etməyə bilər:

```python
# ❌ Potensial risk — yeni endpoint əlavə edildikdə:
@app.route("/api/profile/update", methods=["POST"])
def update_profile():
    data = request.get_json()
    # session yoxlaması UNUDULUB!
    # hər kəs istənilən profili dəyişə bilər
    ...
```

**Tövsiyə:** Bütün `/api/` endpointləri üçün mərkəzi decorator yaratmaq:

```python
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"ok": False, "error": "Daxil olun."}), 401
        return f(*args, **kwargs)
    return decorated

# İstifadəsi:
@app.route("/api/profile/update", methods=["POST"])
@login_required       # ← bir sətir əlavə etmək kifayətdir
def update_profile():
    ...
```

**Həmçinin**, `logged-in.html` server tərəfindən qorunmur — hər kəs URL-ə birbaşa daxil ola bilər. JavaScript `/api/me` cavabına görə "Daxil deyilsiniz" göstərsə də, HTML-in özü açıqdır.

### Qiymətləndirmə: ⚠️ Qismən

---

## 7.3 A02:2021 — Cryptographic Failures (Kriptoqrafik Uğursuzluqlar)

### Nə deməkdir?

Həssas məlumatların düzgün şifrələnməməsi. Parolların açıq saxlanması, zəif hash alqoritmlər, şifrələnməmiş əlaqə (HTTP) və s.

### Bu Layihədə Vəziyyət: ✅ Əsasən Qorunub (parol), ⚠️ Qismən (transport)

**Güclü tərəf — Parol hashing:**

```python
# backend/app.py — 173-cü sətir
pw_hash = generate_password_hash(password)
```

Werkzeug-un `generate_password_hash` funksiyası PBKDF2-SHA256 və ya scrypt alqoritmi ilə hash yaradır. Bu, sənaye standartıdır:
- Salt əlavə edir (rainbow table hücumuna qarşı)
- Çoxsaylı iterasiya (brute-force-u yavaşladır)
- Timing-safe müqayisə (`check_password_hash`)

Bazadakı sütun adı da düzgündür:

```sql
-- database/schema.sql — 7-ci sətir
password_hash TEXT NOT NULL     -- ← "password" yox, "password_hash"
```

**Zəif tərəf — Transport Layer:**

Lakin parol brauzer ilə server arasında **şifrələnmədən** (HTTP) ötürülür:

```javascript
// frontend/auth.js — 141-146-cı sətir
fetchJsonApi("/api/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: email, password: pw }),
})
// ↑ Bu JSON açıq HTTP ilə gedir — şəbəkədə ələ keçirilə bilər
```

Yəni parol bazada düzgün hash-lənir, amma bazaya çatana qədər yolda oğurlana bilər.

### Qiymətləndirmə: ✅ Yaxşı (storage) / ⚠️ Zəif (transport)

---

## 7.4 A03:2021 — Injection (İnyeksiya)

### Nə deməkdir?

İstifadəçi daxil etdiyi məlumatın kod kimi icra edilməsi. SQL Injection, XSS (Cross-Site Scripting), Command Injection və s.

### Bu Layihədə Vəziyyət: ✅ Qorunub

**SQL Injection qorunması:**

Layihədəki bütün SQL sorğuları parametrized query istifadə edir:

```python
# backend/app.py — 107-110-cu sətir
cur.execute(
    "SELECT id, email, password_hash, full_name FROM users WHERE lower(email) = %s",
    (email_lower,),    # ← dəyər ayrıca ötürülür, SQL-ə birbaşa qatılmır
)
```

```python
# backend/app.py — 141-144-cü sətir
cur.execute(
    "INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s)",
    (email_lower, password_hash, full_name),
)
```

`psycopg2`-nin `%s` placeholder mexanizmi dəyəri SQL kodundan tam ayırır. İstifadəçi `'; DROP TABLE users; --` yazsa belə, bu yalnız mətn (data) kimi müalicə olunur, kod kimi icra edilmir.

**XSS qorunması:**

Bütün dinamik DOM əməliyyatları `textContent` istifadə edir:

```javascript
// frontend/auth.js — 10-cu sətir
msgEl.textContent = text || "";

// frontend/logged-in.html — 46-cı sətir
info.textContent = (d.user.full_name || d.user.email) + " · " + d.user.email;
```

`textContent` HTML tag-larını render etmir — `<script>alert(1)</script>` daxil edilsə, bu düz mətn kimi görünür, JavaScript kimi icra edilmir.

### Qiymətləndirmə: ✅ Güclü

---

## 7.5 A04:2021 — Insecure Design (Təhlükəsiz Olmayan Dizayn)

### Nə deməkdir?

Tətbiqin memarlıq səviyyəsində təhlükəsizlik düşünülməyib. Məsələn, parol sıfırlama funksiyası "gizli sual" istifadə edir (asanlıqla təxmin edilir), və ya CAPTCHA-sız qeydiyyat forması (bot hücumu).

### Bu Layihədə Vəziyyət: ⚠️ Qismən

**Müsbət dizayn qərarları:**

- 3 qatlı arxitektura — frontend birbaşa bazaya çata bilmir
- Parol hashing qeydiyyat anında tətbiq edilir
- İkiqat doğrulama (client + server) — Defense in Depth
- Generic xəta mesajları login-da

**Əksik dizayn elementləri:**

1. **CSRF mexanizmi dizayn edilməyib** — token və ya SameSite planlanmayıb
2. **Rate limiting nəzərdə tutulmayıb** — brute-force ssenarisi düşünülməyib

```python
# Layihədə login axını:
# İstifadəçi sorğu göndərir → doğrula → bazada axtar → hash yoxla → session yarat
#
# Bu axında ƏSKIK olan:
# → "Bu IP neçə dəfə cəhd edib?" yoxlaması
# → "Bu hesaba neçə dəfə giriş cəhdi olub?" yoxlaması
# → "Bu sorğu insan tərəfindən göndərilib?" (CAPTCHA) yoxlaması
```

3. **Parol sıfırlama funksiyası yoxdur** — istifadəçi parolunu unudarsa, yenidən əldə edə bilmir
4. **E-poçt doğrulaması yoxdur** — saxta hesab açılmasının qarşısı alınmır

### Qiymətləndirmə: ⚠️ Qismən

---

## 7.6 A05:2021 — Security Misconfiguration (Təhlükəsizlik Konfiqurasiya Xətaları)

### Nə deməkdir?

Tətbiqin, framework-ün, serverin və ya verilənlər bazasının yanlış konfiqurasiya edilməsi. Default parolların dəyişdirilməməsi, lazımsız xidmətlərin aktiv olması, debug rejimin production-da açıq qalması.

### Bu Layihədə Vəziyyət: ⚠️ Qismən

**Problem 1: Debug rejim:**

```python
# backend/app.py — 261-ci sətir
app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
```

`debug=True` production-da ciddi təhlükədir — Werkzeug interactive debugger aktiv olur, bu da brauzerdən Python kodu icra etməyə imkan verir.

**Problem 2: Security headers yoxdur:**

Server cavablarında `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options` başlıqları yoxdur:

```python
# Hazırda server cavabı:
# HTTP/1.1 200 OK
# Content-Type: text/html; charset=utf-8
#
# Əskik başlıqlar:
# Content-Security-Policy: ...      ← YOX
# X-Frame-Options: DENY             ← YOX
# X-Content-Type-Options: nosniff   ← YOX
```

**Problem 3: Secret key fallback:**

```python
# backend/app.py — 34-cü sətir
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)
```

`.env` faylı olmadan tətbiq hər yenidən başlayanda yeni random key yaradır — bütün mövcud session-lar etibarsız olur. Production-da secret key həmişə `.env`-dən oxunmalıdır, fallback qəbulediləcək olmamalıdır.

**Müsbət:** `.env` faylı istifadə ilə gizli məlumatlar koddan ayrılıb:

```python
# backend/app.py — 21-22-ci sətir
load_dotenv(PROJECT_ROOT / ".env", override=True)
```

Və `.env.example` faylı şablon kimi verilir:
```
FLASK_SECRET_KEY=uzun-tesadufi-mətn
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

### Qiymətləndirmə: ⚠️ Qismən

---

## 7.7 A06:2021 — Vulnerable and Outdated Components (Zəif və Köhnəlmiş Komponentlər)

### Nə deməkdir?

İstifadə olunan kitabxana, framework və ya əməliyyat sisteminin köhnə versiyasında məlum zəiflik (CVE) olması.

### Bu Layihədə Vəziyyət: ℹ️ Qiymətləndirmə Tələb Edir

Layihənin `requirements.txt` faylı:

```
flask>=3.0.0
python-dotenv>=1.0.0
psycopg2-binary>=2.9.9
```

`>=` operatoru — minimum versiyanı təyin edir, amma maksimumu yox. `pip install -r requirements.txt` çalışdırıldıqda ən son versiya quraşdırılır. Bu yaxşıdır — ən son versiyalar ən son təhlükəsizlik yamaqlarını ehtiva edir.

Lakin problem budur ki, **versiya pin-lənməyib** (exact version fixed deyil). Production-da:

```
# Tövsiyə: müəyyən versiya istifadə et
flask==3.1.0
python-dotenv==1.0.1
psycopg2-binary==2.9.10
```

`==` ilə versiya dondurularsa, "yeni versiyada nəsə sındı" riski azalır.

Hazırkı versiyaların bilşən zəifliklərin olub-olmadığını yoxlamaq üçün:

```bash
# pip-audit aləti:
pip install pip-audit
pip-audit
```

Bu alət quraşdırılmış kitabxanaları CVE verilənlər bazası ilə müqayisə edir.

### Qiymətləndirmə: ℹ️ Bilinmir — audit lazımdır

---

## 7.8 A07:2021 — Identification and Authentication Failures (Autentifikasiya Uğursuzluqları)

### Nə deməkdir?

Giriş mexanizmindəki zəifliklər: zəif parol siyasəti, brute-force qorunmasının olmaması, session idarəetmə problemləri.

### Bu Layihədə Vəziyyət: ⚠️ Qismən

**Müsbət:**

Parol minimum mürəkkəbliyi tələb edir:

```python
# backend/app.py — 86-93-cü sətir
def validate_password_strength(pw: str) -> Tuple[bool, str]:
    if not pw or len(pw) < 8:
        return False, "Parol ən azı 8 simvol olmalıdır."
    if not any(c.isalpha() for c in pw):
        return False, "Parolda ən azı bir hərf olmalıdır."
    if not any(c.isdigit() for c in pw):
        return False, "Parolda ən azı bir rəqəm olmalıdır."
    return True, ""
```

Generic xəta mesajları ilə user enumeration qarşısı alınır (login-da):

```python
# backend/app.py — 195, 203-cü sətir
return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401
```

Session çıxışda tam təmizlənir:

```python
# backend/app.py — 213-cü sətir
session.clear()
```

**Mənfi:**

| Əskik Mexanizm | Risk |
|---|---|
| Rate limiting yoxdur | Brute-force hücumu mümkündür |
| Account lockout yoxdur | Sonsuz parol cəhdi mümkündür |
| Parolda xüsusi simvol tələb yoxdur | `abcde123` kimi zəif parollar keçə bilər |
| Session expiration yoxdur | Session müddətsiz aktiv qala bilər |
| Multi-factor authentication yoxdur | Yalnız parol ilə qorunma |
| "Parolu unutdum" yoxdur | İstifadəçi parolu bərpa edə bilmir |

### Qiymətləndirmə: ⚠️ Qismən

---

## 7.9 A08:2021 — Software and Data Integrity Failures (Proqram və Verilənlər Bütövlüyü)

### Nə deməkdir?

Tətbiqin yenilənmə prosesində, CI/CD pipeline-da və ya kitabxana yüklənməsində bütövlüyün pozulması. Məsələn, NPM paketinə zərərli kod yeridilməsi (supply chain attack).

### Bu Layihədə Vəziyyət: ℹ️ Yoxlanılmayıb

Bu layihə kiçik miqyaslıdır:
- CI/CD pipeline yoxdur
- NPM istifadə edilmir (yalnız Python)
- Avtomatik yenilənmə mexanizmi yoxdur

`requirements.txt`-dəki `>=` operatoru gönüllü olaraq yeni versiyalar quraşdırmağa imkan verir — bu, supply chain riski yarada bilər (əgər kitabxananın yeni versiyasına zərərli kod yeridilərsə).

```
# Hazırda:
flask>=3.0.0         # ← istənilən yeni versiya quraşdırıla bilər

# Daha təhlükəsiz:
flask==3.1.0         # ← yalnız bu versiya
```

### Qiymətləndirmə: ℹ️ Aktual risk aşağıdır

---

## 7.10 A09:2021 — Security Logging and Monitoring Failures (Təhlükəsizlik Log və Monitorinq Uğursuzluqları)

### Nə deməkdir?

Təhlükəsizlik hadisələrinin (giriş cəhdləri, xəta mesajları, icazə rəddləri) loglanmaması. Hücum baş verdikdə aşkar etmək, analiz etmək və cavab vermək mümkün olmur.

### Bu Layihədə Vəziyyət: ⚠️ Zəif

Bu layihədə təhlükəsizlik loqu **heç yoxdur**. Baxaq hansı hadisələr loglanmalıdır amma loglanmır:

```python
# backend/app.py — 193-203-cü sətir
row = user_get_by_email(email)
if row is None:
    return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401
    # ← LOG YOX: kim cəhd etdi? hansı IP-dən? hansı e-poçt ilə?

# ...
if not pw_ok:
    return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401
    # ← LOG YOX: hansı hesaba uğursuz cəhd? neçənci cəhd?
```

```python
# backend/app.py — 248-251-ci sətir (path traversal)
try:
    safe_path.relative_to(FRONTEND_DIR.resolve())
except ValueError:
    return "Forbidden", 403
    # ← LOG YOX: kim path traversal cəhdi etdi? hansı yolu istədi?
```

```python
# backend/app.py — 73-76-cı sətir
try:
    init_db()
except Exception as ex:
    print("DB init:", ex)    # ← yalnız konsolda, fayla yazılmır
```

`print()` istifadəsi — bu, loq deyil. Print:
- Fayla yazılmır (server bağlananda itirilir)
- Timestamp yoxdur
- Severity level yoxdur (WARNING? ERROR? CRITICAL?)
- Strukturlaşdırılmamışdır (avtomatik analiz mümkün deyil)

Loglanmalı olan hadisələr:

| Hadisə | Log Səviyyəsi | Niyə |
|---|---|---|
| Uğursuz giriş cəhdi | WARNING | Brute-force aşkarlama |
| Uğurlu giriş | INFO | Audit trail |
| Qeydiyyat | INFO | Hesab yaradılma izləmə |
| Path traversal cəhdi | WARNING | Hücum aşkarlama |
| DB bağlantı xətası | ERROR | Sistem sağlamlığı |
| Session etibarsızlığı | WARNING | Session oğurluğu cəhdi |

### Qiymətləndirmə: ⚠️ Zəif

---

## 7.11 A10:2021 — Server-Side Request Forgery (SSRF)

### Nə deməkdir?

Server tətbiqin istifadəçi tərəfindən verilmiş URL-ə sorğu göndərməsi. Haker bunu istifadə edərək serverin daxili şəbəkəsinə (localhost, internal API-lər) çata bilər.

### Bu Layihədə Vəziyyət: ✅ Aktual Deyil

Bu layihədə server heç bir xarici URL-ə sorğu göndərmir. Backend yalnız:
- PostgreSQL-ə SQL sorğusu göndərir
- Session cookie yaradır
- Statik faylları servis edir

Heç bir yerdə `requests.get(user_input)` və ya oxşar URL-ə əsaslanan sorğu yoxdur, buna görə SSRF riski mövcud deyil.

```python
# Layihədəki yeganə xarici əlaqə — verilənlər bazası:
psycopg2.connect(_effective_database_url())
# ← URL .env faylından oxunur, istifadəçi daxil etmir
```

### Qiymətləndirmə: ✅ Aktual Deyil

---

## 7.12 Yekun Müqayisə Cədvəli

| № | OWASP Kateqoriyası | Status | Qorunma | Əsas Əskiklik |
|---|---|---|---|---|
| A01 | Broken Access Control | ⚠️ Qismən | `/api/me` session yoxlayır | Auth middleware yoxdur |
| A02 | Cryptographic Failures | ✅/⚠️ | PBKDF2/scrypt hash | HTTPS yoxdur (transport) |
| A03 | Injection | ✅ Güclü | Parametrized query + textContent | — |
| A04 | Insecure Design | ⚠️ Qismən | 3-tier, Defense in Depth | CSRF, rate limit planlanmayıb |
| A05 | Security Misconfiguration | ⚠️ Qismən | `.env` fayl ayrılığı | debug=True, headers yox |
| A06 | Vulnerable Components | ℹ️ | `>=` versiyalar | Audit edilməyib |
| A07 | Auth Failures | ⚠️ Qismən | Parol gücü, generic xəta | Brute-force, lockout yox |
| A08 | Software Integrity | ℹ️ | — | CI/CD yoxdur |
| A09 | Logging Failures | ⚠️ Zəif | Yalnız `print()` | Strukturlaşdırılmış log yox |
| A10 | SSRF | ✅ | Xarici URL sorğusu yoxdur | — |

### Statistik Xülasə:

```
✅ Tam qorunma:     2 kateqoriya  (A03, A10)
⚠️ Qismən qorunma:  5 kateqoriya  (A01, A02, A04, A05, A07)
⚠️ Zəif:            1 kateqoriya  (A09)
ℹ️ Yoxlanılmalı:     2 kateqoriya  (A06, A08)
```

---

## 7.13 Vizual Qiymətləndirmə

```
OWASP Top 10 Uyğunluq Diaqramı
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A01 Access Control    [████████░░░░░░░░░░░░]  40%
A02 Cryptography      [██████████████░░░░░░]  70%
A03 Injection         [████████████████████]  100%
A04 Insecure Design   [████████░░░░░░░░░░░░]  40%
A05 Misconfiguration  [██████████░░░░░░░░░░]  50%
A06 Components        [░░░░░░░░░░░░░░░░░░░░]  ?
A07 Auth Failures     [████████████░░░░░░░░]  60%
A08 Integrity         [░░░░░░░░░░░░░░░░░░░░]  ?
A09 Logging           [████░░░░░░░░░░░░░░░░]  20%
A10 SSRF              [████████████████████]  100%

Ortalama (qiymətləndirilənlər):  ≈ 60%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 7.14 Nəticə

Bu layihə 2-ci kurs tələbəsi tərəfindən hazırlanmış bir minimal giriş/qeydiyyat sistemi üçün **yaxşı təhlükəsizlik əsaslarına** malikdir. Xüsusilə:

- **A03 (Injection)** — tam qorunub: parametrized query + textContent
- **A10 (SSRF)** — risk yoxdur: xarici sorğu yoxdur
- **A02 (Cryptography)** — parol storage güclüdür: PBKDF2/scrypt

Əsas inkişaf sahələri:
- **A09 (Logging)** — ən zəif yer: təhlükəsizlik loqu tamamilə yoxdur
- **A05 (Misconfiguration)** — `debug=True` və security headers əlavə edilməlidir
- **A07 (Auth Failures)** — rate limiting və account lockout əlavə edilməlidir

Bu nəticələr göstərir ki, layihə **fundamental təhlükəsizlik prinsiplərini** (hashing, parametrized query, input validation) düzgün tətbiq edir, lakin **operational təhlükəsizlik** (logging, monitoring, rate limiting) sahəsində inkişaf etməlidir.

---

*Növbəti bölmədə reportun yekun nəticəsi yazılacaq.*
