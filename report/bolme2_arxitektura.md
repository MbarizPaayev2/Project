# Bölmə 2 — Layihənin Arxitekturası

**Fənn:** Web Təhlükəsizliyi  
**Tələbə:** Mubariz Pashayev  
**Kurs:** II kurs  
**Tarix:** Aprel 2026

---

## 2.1 Arxitektura Nədir?

Bir veb tətbiqini düzgün qurmaq üçün onu hissələrə bölmək lazımdır — necə ki bir binanın özülü, divarları və çatısı ayrı-ayrı elementlərdir, veb tətbiqin də öz quruluş prinsipləri var.

**Arxitektura** — bir proqramın hissələrinin bir-biri ilə necə əlaqələndirildiyi, işin necə bölündüyü deməkdir. Düzgün arxitektura olmadan kod tez bir zamanda dolaşıq, test edilməsi çətin, təhlükəsizliyi qiymətləndirmək mümkünsüz bir hala gəlir.

Bu layihədə **3 Qatlı Arxitektura (Three-Tier Architecture)** modeli tətbiq edilib. Bu model sənaye standartıdır — böyük şirkətlər (bank sistemləri, aviakassa platformaları, e-ticarət saytları) da eyni prinsipdən istifadə edir.

---

## 2.2 3 Qatlı Arxitektura: Ümumi Baxış

```
┌─────────────────────────────────────────────────────────┐
│                  QATLAR VƏ FAYLLAR                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1-ci Qat  ──  PRESENTATION LAYER (İstifadəçi Qatı)    │
│                login.html                               │
│                register.html                            │
│                logged-in.html                           │
│                auth.js                                  │
│                style.css                                │
│                                                         │
│       ↕  HTTP sorğuları (POST, GET)                     │
│                                                         │
│  2-ci Qat  ──  BUSINESS LOGIC LAYER (Məntiq Qatı)      │
│                backend/app.py                           │
│                /api/login · /api/register               │
│                /api/logout · /api/me · /api/health      │
│                                                         │
│       ↕  SQL sorğuları (SELECT, INSERT)                 │
│                                                         │
│  3-cü Qat  ──  DATA LAYER (Verilənlər Qatı)            │
│                PostgreSQL → users cədvəli               │
│                database/schema.sql                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

Bu üç qatın **hər biri öz işini görür** və digər qatın daxili işlərindən xəbərsizdir:

- **Frontend** — yalnız istifadəçidən məlumat alır və API-yə göndərir. Parolun necə yoxlandığını, verilənlər bazasının harada olduğunu bilmir.
- **Backend** — yalnız gələn sorğunu analiz edir, qaydaları yoxlayır, verilənlər bazasına müraciət edir. HTML səhifənin necə göründüyünü bilmir.
- **Verilənlər bazası** — yalnız məlumatı saxlayır. Nə HTML, nə Python məntiqi ilə işi var.

Bu ayrılma **təhlükəsizlik üçün kritikdir**: haker brauzer vasitəsilə yalnız frontend ilə danışa bilər. Backend-i keçmədən bazaya birbaşa çata bilməz.

---

## 2.3 Birinci Qat — Frontend (Presentation Layer)

### 2.3.1 HTML Səhifələri

Layihədə 3 HTML səhifəsi var: `login.html`, `register.html`, `logged-in.html`. Onların rolu yalnız **vizualdır** — formanı göstərir, istifadəçidən məlumat alır.

`login.html` faylından form strukturu:

```html
<!-- frontend/login.html — 27-63-cü sətirlər -->
<form id="login-form" class="form-grid" novalidate>
  <div class="form-group form-grid--full-width">
    <label for="login-email">E-poçt</label>
    <input
      type="text"
      id="login-email"
      name="email"
      autocomplete="email"
      inputmode="email"
      placeholder="nümunə@mail.com"
      maxlength="254"
    />
    <span id="login-email-hint" class="auth-hint" aria-live="polite">
      Düzgün e-poçt formatı
    </span>
  </div>
  <div class="form-group form-grid--full-width">
    <label for="login-password">Parol</label>
    <input
      type="password"
      id="login-password"
      name="password"
      autocomplete="current-password"
      placeholder="****"
      maxlength="256"
    />
  </div>
  <div class="form-group form-grid--full-width">
    <button type="submit" class="btn">Daxil ol</button>
  </div>
</form>
```

Burada diqqət çəkən bir neçə atribut var:

| Atribut | Dəyər | Məna |
|---|---|---|
| `novalidate` | — | BrauZerin öz doğrulamasını söndürür; doğrulamalar JavaScript ilə idarə edilir |
| `maxlength="254"` | e-poçt sahəsi | RFC standartına görə e-poçt maksimum 254 simvol ola bilər |
| `maxlength="256"` | parol sahəsi | Çox uzun parol göndərilməsini əvvəlcədən məhdudlaşdırır |
| `type="password"` | parol sahəsi | Brauzər parol simvollarını nöqtə ilə gizlədir, clipboard log-larında əks olunmur |
| `autocomplete="current-password"` | parol sahəsi | Brauzərə bu sahənin parol olan olduğunu bildirir — şifrə menecerləri ilə uyğun işləyir |

`novalidate` atributunun istifadəsi maraqlıdır: bu atribut HTML5-in öz doğrulamasını (məsələn, `required`, `type="email"` yoxlamaları) söndürür. Bunun əvəzinə bütün doğrulama `auth.js`-də JavaScript ilə idarə olunur — bu, daha çevik xəta mesajları göstərməyə imkan verir.

### 2.3.2 JavaScript Faylı (auth.js)

`auth.js` — frontend-in "beyni"dir. O, iki əsas işi görür:

1. İstifadəçi daxil etdiyi məlumatı **real vaxtda yoxlayır** (hər simvol yazılanda)
2. Formu göndərdikdə **backend API-yə sorğu göndərir** və cavaba görə davranır

Bütün kod **IIFE (Immediately Invoked Function Expression)** içindədir:

```javascript
// frontend/auth.js — 3-cü sətir
(function () {
  // ... bütün kod burada
})();
```

**IIFE nədir?** Bu, funksiyanı yaradıb dərhal çalışdıran konstruksiyadır. Bunu etməyin səbəbi — daxildəki bütün dəyişənlər yalnız bu funksiyanın içdə mövcuddur, qlobal `window` obyektini kirletmir. Bu, **namespace pollution** (ad fəzası çirklənməsi) adlanan problemi həll edir — böyük layihələrdə müxtəlif JavaScript fayllarındakı eyni adlı dəyişənlər bir-birinə mane olmur.

Formların müəyyən edilməsi:
```javascript
// frontend/auth.js — 4-6-cı sətir
var msgEl = document.getElementById("auth-message");
var formLogin = document.getElementById("login-form");
var formRegister = document.getElementById("register-form");
```

Hər bir `id` dəqiq HTML-dəki `id` atributuna uyğun gəlir — bu bağlantı olmadan JavaScript HTML forması ilə "danışa" bilməz.

---

## 2.4 İkinci Qat — Backend (Business Logic Layer)

### 2.4.1 Flask Tətbiqinin Qurulması

Backend tamamilə `backend/app.py` faylındadır. Flask tətbiqi bu şəkildə qurulur:

```python
# backend/app.py — 33-34-cü sətir
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)
```

`Flask(__name__)` — bu sətir Flask tətbiq obyektini yaradır. `__name__` Python-da cari modulun adını verir — Flask bunu fayl axtarışları üçün istifadə edir.

`app.secret_key` — **Session security** üçün kritikdir. Bu açar session cookie-lərini **imzalamaq** üçün işlədilir. Əgər bu açar məlum olsa, haker özü üçün saxta session cookie yarada bilər. Buna görə:
- `.env` faylından oxunur (kodun içinə yazılmır)
- Əgər `.env`-də yoxdursa — `os.urandom(24)` ilə 192-bit (24 bayt) tam təsadüfi açar yaradılır

### 2.4.2 Endpoint-lər (API Marşrutları)

Backend 5 endpoint (API ünvanı) təqdim edir:

| Endpoint | Metod | Funksiya |
|---|---|---|
| `/api/register` | POST | Yeni istifadəçi qeydiyyatı |
| `/api/login` | POST | Giriş, session yaratma |
| `/api/logout` | POST | Çıxış, session silmə |
| `/api/me` | GET | Cari istifadəçi məlumatı |
| `/api/health` | GET | Sistem sağlamlığı yoxlaması |

Hər endpoint bir Python funksiyasına bağlıdır. Flask-da bu bağlantı `@app.route()` dekoratoru ilə qurulur:

```python
# backend/app.py — 155, 181, 211, 217, 228-ci sətir
@app.route("/api/register", methods=["POST"])
def api_register(): ...

@app.route("/api/login", methods=["POST"])
def api_login(): ...

@app.route("/api/logout", methods=["POST"])
def api_logout(): ...

@app.route("/api/me", methods=["GET"])
def api_me(): ...

@app.route("/api/health", methods=["GET"])
def api_health(): ...
```

**POST vs GET fərqi:**
- `GET` — məlumat **oxumaq** üçün. URL-də parametrlər görünür. Parol kimi həssas məlumat göndərilməməlidir.
- `POST` — məlumat **göndərmək/yaratmaq** üçün. Məlumat sorğunun **body** hissəsindədir, URL-də görünmür.

Login və register POST istifadə edir — çünki istifadəçinin parolu URL-də görünməməlidir.

### 2.4.3 Statik Faylların Servis Edilməsi

Layihədə ayrıca statik fayl serveri yoxdur (nginx, Apache kimi). Flask özü `frontend/` qovluğunu servis edir:

```python
# backend/app.py — 241-256-cı sətir
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
```

Bu kod necə işləyir? Addım-addım:

1. İstifadəçi `http://localhost:5000/login.html` açır
2. Flask bu sorğunu `serve_file("login.html")` funksiyasına yönləndirir
3. `"api/"` ilə başlayırmı? — Xeyr, davam edir
4. `allowed` uzantılar içindədir? — `.html` var, keçir
5. **Path traversal yoxlaması:** `../../etc/passwd` kimi hücum cəhdi backend-in fayl sistemindən kənara çıxa bilərmi? — `relative_to()` bunu bloklayır
6. Fayl mövcuddurmu? — Bəli
7. `send_from_directory()` faylı brauzərə göndərir

Başlanğıc marşrut (`/`) birbaşa `login.html`-ə yönləndirir — yəni `http://localhost:5000/` açıldıqda avtomatik giriş səhifəsi gəlir.

### 2.4.4 Yol Dəyişənlərinin Hesablanması

Flask-ın işə başladığı anda əsas qovluq yolları hesablanır:

```python
# backend/app.py — 17-19-cu sətir
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
```

- `__file__` — bu faylın (`app.py`) tam yolu
- `.resolve()` — simvolik linkləri açır, tam mütləq yol verir
- `.parent` — bir qovluq yuxarı çıxır

Yəni əgər `app.py` buradadırsa: `D:\web-security-task\backend\app.py`

O zaman:
```
BACKEND_DIR  = D:\web-security-task\backend
PROJECT_ROOT = D:\web-security-task
FRONTEND_DIR = D:\web-security-task\frontend
```

Bu hesablama statik olaraq yox, **dinamik** edilir. Layihə başqa diskə köçürülsə də, başqa istifadəçinin kompüterində işlədilsə də — düzgün yollar tapılır.

---

## 2.5 Üçüncü Qat — Verilənlər Bazası (Data Layer)

### 2.5.1 Cədvəl Strukturu

Layihədə yalnız bir cədvəl var — `users`. Cədvəlin sxemi `database/schema.sql`-dədir:

```sql
-- database/schema.sql
CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL    PRIMARY KEY,
    email       TEXT         UNIQUE NOT NULL,
    password_hash TEXT        NOT NULL,
    full_name   TEXT,
    created_at  TIMESTAMPTZ  DEFAULT NOW()
);
```

Hər sütunun rolu var:

| Sütun | Tip | Məqsəd |
|---|---|---|
| `id` | `BIGSERIAL` | Avtomatik artan unikal tam ədəd (PRIMARY KEY) |
| `email` | `TEXT UNIQUE NOT NULL` | E-poçt ünvanı; boş ola bilməz; təkrar ola bilməz |
| `password_hash` | `TEXT NOT NULL` | Parolun **hash-i**, xam parolu yox! |
| `full_name` | `TEXT` | Ad soyad; isteğe bağlı (`NULL` ola bilər) |
| `created_at` | `TIMESTAMPTZ` | Qeydiyyat tarixi/vaxtı; avtomatik doldurulur |

`BIGSERIAL` — PostgreSQL-in böyük tam ədədlər üçün avtomatik artan tipidir. Standart `SERIAL`-dan fərqi, daha böyük aralığı var (9 kvintilyon qədər). Gələcəkdə cədvəl çox böyüsə belə `id` sahəsi daşmaz.

`TIMESTAMPTZ` — timestamp with time zone deməkdir. Tarixin yanaşı saat dilimini də saxlayır — beynəlxalq sistemlər üçün doğru yanaşmadır.

### 2.5.2 Verilənlər Bazası Bağlantısı

Hər sorğu üçün yeni bağlantı açılır:

```python
# backend/app.py — 47-51-ci sətir
def get_db():
    import psycopg2
    from psycopg2.extras import RealDictCursor

    return psycopg2.connect(_effective_database_url(), cursor_factory=RealDictCursor)
```

Bağlantı URL-i Vercel mühitini nəzərə alaraq SSL ilə tənzimlənir:

```python
# backend/app.py — 37-44-cü sətir
def _effective_database_url() -> str:
    parsed = urlparse(DATABASE_URL)
    qs = parse_qs(parsed.query)
    keys_lower = {k.lower() for k in qs}
    if os.environ.get("VERCEL") and "sslmode" not in keys_lower:
        qs["sslmode"] = ["require"]
    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))
```

Bu funksiya belə işləyir:
- Normal mühitdə (lokal): URL olduğu kimi qalır
- Vercel (cloud) mühitdə: `?sslmode=require` əlavə edilir — şifrələnmədən verilənlər bazasına qoşulma yasaqlanır

### 2.5.3 Cədvəlin Avtomatik Yaradılması

Tətbiq işə düşəndə cədvəlin mövcud olub olmadığı yoxlanılır, yoxdursa yaradılır:

```python
# backend/app.py — 54-76-cı sətir
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
```

`CREATE TABLE IF NOT EXISTS` — əgər cədvəl artıq varsa heç nə etmir, yoxdursa yaradır. Bu sayədə tətbiq hər işə düşəndə xəta vermir.

`try/except` bloku ilə əhatə olunub — verilənlər bazası bağlantısı uğursuz olsa belə tətbiq işə düşür, yalnız konsola xəta yazılır. Bu müzakirə doğura bilər: bəlkə DB bağlantısı uğursuzsa tətbiq işə düşməməlidir? Bölmə 6-da bu məsələyə qayıdacağıq.

---

## 2.6 Qatlar Arası Əlaqə: Tam Nümunə

Gəlin qeydiyyat prosesini tam axın kimi izləyək — hər üç qat iştirak edir:

### Addım 1 — Frontend: İstifadəçi məlumat daxil edir

`register.html`-də formaya ad, e-poçt, parol yazılır. Göndər düyməsi basılır.

### Addım 2 — Frontend (auth.js): Məlumat yoxlanılır

```javascript
// frontend/auth.js — 191-236-cı sətir
formRegister.addEventListener("submit", function (e) {
  e.preventDefault();   // ← standart form göndərilməsini dayandırır

  var ad    = trim(rAd.value);
  var email = trim(rEmail.value);
  var pw    = rPw.value;
  var pw2   = rPw2.value;

  // Yoxlamalar:
  if (ad.length < 2) { ... return; }         // ad çox qısa?
  if (!emailDuzdur(email)) { ... return; }   // e-poçt formatı?
  var px = parolQeydiyyat(pw);
  if (px) { ... return; }                    // parol zəifdir?
  if (pw !== pw2) { ... return; }            // parollar uyğun gəlmir?

  // Yoxlamalar keçildisə → API-yə göndər
  fetchJsonApi("/api/register", { ... });
});
```

`e.preventDefault()` — brauzerin formu ənənəvi üsulla (səhifəni yeniləyərək) göndərməsinin qarşısını alır. Bunun yerinə JavaScript `fetch` API ilə sorğu göndərilir.

### Addım 3 — Frontend → Backend: HTTP sorğusu

```javascript
// frontend/auth.js — 238-248-ci sətir
fetchJsonApi("/api/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  credentials: "same-origin",
  body: JSON.stringify({
    full_name: ad,
    email:     email,
    password:  pw,
    password_confirm: pw2,
  }),
})
```

Bu sorğu belə görünür (network tab-da):
```
POST /api/register HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "full_name": "Əli Həsənov",
  "email": "ali@mail.com",
  "password": "Sifre123",
  "password_confirm": "Sifre123"
}
```

### Addım 4 — Backend (app.py): Sorğu qəbul edilib analiz edilir

```python
# backend/app.py — 156-178-ci sətir
@app.route("/api/register", methods=["POST"])
def api_register():
    data      = request.get_json(silent=True) or {}
    email     = (data.get("email") or "").strip()
    password  = data.get("password") or ""
    password2 = data.get("password_confirm") or ""
    full_name = (data.get("full_name") or "").strip()

    # Server-side doğrulamalar:
    if not full_name or len(full_name) < 2:
        return jsonify({"ok": False, "error": "Ad ən azı 2 simvol olmalıdır."}), 400

    if not validate_email(email):
        return jsonify({"ok": False, "error": "E-poçt düzgün deyil."}), 400

    ok, msg = validate_password_strength(password)
    if not ok:
        return jsonify({"ok": False, "error": msg}), 400

    if password != password2:
        return jsonify({"ok": False, "error": "Parollar üst-üstə düşmür."}), 400

    # Parol hash-lənir:
    pw_hash = generate_password_hash(password)

    # Bazaya yazılır:
    ok_ins, err = user_insert(email.lower(), pw_hash, full_name)
    if not ok_ins:
        return jsonify({"ok": False, "error": err or "Qeydiyyat alınmadı."}), 400

    return jsonify({"ok": True, "message": "Qeydiyyat tamamlandı."})
```

`request.get_json(silent=True)` — gələn sorğunun body-sini JSON kimi oxuyur. `silent=True` parametri — JSON formatı yanlışdırsa `None` qaytarır, istisna atmır. `or {}` isə `None` halında boş lüğət verir — kod xəta vermir.

### Addım 5 — Backend → Database: SQL sorğusu

```python
# backend/app.py — 135-152-ci sətir
def user_insert(email_lower: str, password_hash: str, full_name: str):
    import psycopg2
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s)",
            (email_lower, password_hash, full_name),
        )
        conn.commit()    # ← dəyişikliyi bazaya tətbiq edir
        cur.close()
        conn.close()
        return True, None
    except psycopg2.IntegrityError:
        return False, "Bu e-poçt artıq qeydiyyatdan keçib."
    except Exception as ex:
        return False, str(ex)
```

`psycopg2.IntegrityError` — `email TEXT UNIQUE` məhdudiyyəti pozulanda baş verir. Yəni eyni e-poçtla ikinci qeydiyyat cəhdi bazada rədd edilir və backend bu xətanı tutaraq istifadəçiyə aydın mesaj göndərir.

`conn.commit()` — PostgreSQL-də dəyişikliklər avtomatik bazaya yazılmır. `commit()` çağırılana qədər dəyişiklik müvəqqətidir. Əgər `commit()` edilməsə sorğu "itirilir."

### Addım 6 — Backend → Frontend: JSON cavabı

Uğurlu halda backend belə cavab göndərir:
```json
HTTP/1.1 200 OK
Content-Type: application/json

{"ok": true, "message": "Qeydiyyat tamamlandı."}
```

### Addım 7 — Frontend: Cavab işlənir

```javascript
// frontend/auth.js — 249-261-ci sətir
.then(function (res) {
  if (res.data.ok) {
    setAuthMsg(res.data.message || "Oldu.", false);  // yaşıl mesaj
    setTimeout(function () {
      window.location.href = "login.html";           // 800ms sonra yönləndir
    }, 800);
  } else {
    setAuthMsg(res.data.error || "Xəta", true);      // qırmızı xəta
  }
})
```

---

## 2.7 Konfiqurasiya Qatı — .env Faylı

`.env` faylı texniki olaraq ayrıca bir "qat" deyil, amma layihənin işləməsi üçün vacibdir. O, həssas məlumatları koddan ayırır:

```
# .env.example faylı
FLASK_SECRET_KEY=uzun-tesadufi-mətn
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

Bu dəyişənlər tətbiq başlayanda yüklənir:

```python
# backend/app.py — 21-22-ci sətir
load_dotenv(PROJECT_ROOT / ".env", override=True)
load_dotenv(BACKEND_DIR / ".env", override=True)
```

İki yerdən oxunur — həm layihənin kökündən, həm `backend/` qovluğundan. `override=True` parametri — əgər hər ikisidə eyni dəyişən varsa, sonra oxunan (backend/.env) üstünlük alır. Bu, inkişaf mərhələsinde lokal tənzimləmə üçün çevikllik verir.

`.env` faylı `.gitignore`-a əlavə edilməlidir — real layihələrdə bu fayl GitHub-da görünmür, yerli kompüterdə qalır.

---

## 2.8 Arxitekturanın Təhlükəsizlik Xülasəsi

| Qat | Kimin əlçatanlığı var | Niyə vacibdir |
|---|---|---|
| **Frontend** | Hər kəs (brauzer) | İstifadəçi məlumatı buradan daxil olur |
| **Backend** | Yalnız HTTP sorğuları ilə | Bütün biznes qaydaları burada yoxlanılır |
| **Database** | Yalnız backend | Birbaşa əlçatanlıq yoxdur; brauzer bazaya çata bilmir |
| **.env** | Yalnız server | Gizli açarlar — koddan ayrıdır, public repoda yoxdur |

Bu 3-qatlı quruluş özü artıq bir **security boundary** (təhlükəsizlik sərhədi) yaradır. Lakin quruluşun özü kifayət deyil — hər qatın daxilindəki kod da düzgün yazılmalıdır. Növbəti bölmələrdə həmin kodların analizi aparılacaq.

---

*Növbəti bölmədə verilənlər bazası sxeminin daha dərin analizi və istifadəçi məlumatlarının necə saxlandığı araşdırılacaq.*
