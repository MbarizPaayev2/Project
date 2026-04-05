# Bölmə 4 — Backend Təhlükəsizlik Analizi

**Fənn:** Web Təhlükəsizliyi  
**Tələbə:** [Ad Soyad]  
**Kurs:** II kurs  
**Tarix:** Aprel 2026

---

## 4.1 Parol Hashing — Kriptoqrafik Qorunma

### 4.1.1 Problem: Niyə Parolları Düz Saxlamaq Olmaz?

Təsəvvür edək ki, verilənlər bazasında parollar açıq şəkildə saxlanılır:

```
id | email           | password
---+-----------------+----------
1  | ali@mail.com    | Sifre123
2  | aysel@mail.com  | Qizilgul99
```

Bu halda üç ciddi risk yaranır:
- Verilənlər bazasını idarə edən şəxs (DBA, developer) bütün parolları görə bilər
- Haker bazaya daxil olsa, bütün istifadəçilərin parollarını dərhal oxuyar
- İnsanlar eyni parolu bir neçə saytda istifadə edir — bir saytın bazası sızarsa, digər saytlardakı hesablar da təhlükədədir

Bu layihədə parollar **heç vaxt** açıq saxlanılmır. Əvəzinə hash-lənmiş versiyası yazılır.

### 4.1.2 Hashing Necə İşləyir?

Hash funksiyası — giriş mətnini sabit uzunluqlu, oxunmaz bir string-ə çevirən bir-tərəfli riyazi funksiyadır. "Bir-tərəfli" o deməkdir ki, hash-dən orijinal mətni bərpa etmək praktiki olaraq mümkün deyil.

Qeydiyyat zamanı parolun hash-lənməsi:

```python
# backend/app.py — 15-ci sətir (import)
from werkzeug.security import check_password_hash, generate_password_hash

# backend/app.py — 173-cü sətir (qeydiyyat funksiyası içində)
pw_hash = generate_password_hash(password)
```

`generate_password_hash("Sifre123")` çağırıldıqda nə baş verir:

```
Giriş:  "Sifre123"
Çıxış:  "scrypt:32768:8:1$MjQ1NjI0Nzg$a4f8c2e1b7d3..."
         ↑               ↑               ↑
         alqoritm adı    salt            hash dəyəri
```

Bu nəticə üç hissədən ibarətdir:

1. **Alqoritm identifikatoru** (`scrypt:32768:8:1`) — hansı alqoritm və parametrlərlə hash-ləndiyi. Werkzeug-un son versiyaları scrypt istifadə edir, köhnə versiyaları PBKDF2-SHA256. Hər ikisi sənaye standartıdır.

2. **Salt** (`MjQ1NjI0Nzg`) — hər hash üçün yaradılan unikal təsadüfi dəyər. Salt niyə lazımdır? Əgər iki istifadəçi eyni parolu seçsə:

Salt olmadan (təhlükəli):
```
ali@mail.com    → hash("Sifre123") = abc123...
aysel@mail.com  → hash("Sifre123") = abc123...   ← EYNİ!
```

Haker hash-lərin eyni olduğunu görərdi və bilərdi ki, parollar eynidir. Bir parolu tapsa, ikisini də bilmiş olardı.

Salt ilə (təhlükəsiz — bu layihədə belə):
```
ali@mail.com    → hash("Sifre123" + salt_1) = x7f9a2...
aysel@mail.com  → hash("Sifre123" + salt_2) = k3m8b1...   ← FƏRQLI!
```

Eyni parollar belə fərqli hash-lər verir. Haker heç biri haqqında məlumat ala bilmir.

3. **Hash dəyəri** — alqoritm, parol və salt birləşdirilərək hesablanmış nəticə.

### 4.1.3 Giriş Zamanı Hash Müqayisəsi

İstifadəçi giriş etdikdə daxil etdiyi parol bazadakı hash ilə müqayisə edilir:

```python
# backend/app.py — 197-201-ci sətir
ph = row.get("password_hash")
try:
    pw_ok = bool(ph) and check_password_hash(str(ph), password)
except (TypeError, ValueError):
    pw_ok = False
```

`check_password_hash` necə işləyir:
1. Bazadakı hash-dən salt-ı çıxarır
2. İstifadəçinin daxil etdiyi parolu eyni salt ilə hash-ləyir
3. Yeni hesablanmış hash-i bazadakı hash ilə müqayisə edir
4. Eynidir? → `True`. Fərqlidir? → `False`.

Diqqət çəkən nöqtələr:

- `bool(ph)` — əgər `password_hash` sahəsi boş və ya `None`-dursa, müqayisəyə keçmir. Bu, bazada qeyri-adi vəziyyəti (boş hash) tutmaq üçündür.
- `str(ph)` — `password_hash` dəyərini açıq şəkildə string-ə çevirir. Bəzi hallarda bazadan gələn dəyər fərqli tip ola bilər.
- `try/except (TypeError, ValueError)` — əgər hash formatı pozulubsa (məsələn, bazada manual dəyişiklik edilmişdisə), proqram çökmür, sadəcə `False` qaytarır.

### 4.1.4 Timing Attack-a Qarşı Qorunma

`check_password_hash` funksiyası **constant-time comparison** (sabit zamanlı müqayisə) istifadə edir. Bu nə deməkdir?

Adi string müqayisəsi belə işləyir:
```
"abc123" == "abc456"
 a=a ✓   b=b ✓   c=c ✓   1≠4 ✗ → STOP
 3 müqayisə → qısa vaxt
```

```
"abc123" == "xyz789"
 a≠x ✗ → STOP
 1 müqayisə → daha qısa vaxt
```

Haker sorğunun nə qədər vaxt aldığını ölçərək hansi baytların düzgün olduğunu təxmin edə bilər. Bu, **timing attack** adlanır.

Constant-time müqayisə isə **həmişə bütün baytları müqayisə edir** — nəticədən asılı olmayaraq eyni vaxt sərf edir. `check_password_hash` daxilən Werkzeug-un `hmac.compare_digest()` funksiyasını istifadə edir ki, bu da Python-un C dilində yazılmış sabit zamanlı müqayisə funksiyasıdır.

### 4.1.5 Parol Gücü Doğrulaması

Parolun hash-lənməsindən əvvəl gücü yoxlanılır:

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

Bu yoxlamanın şərtləri:

| Şərt | Nümunə (rədd) | Nümunə (qəbul) |
|---|---|---|
| Minimum 8 simvol | `abc12` (5 simvol) | `Sifre123` (8 simvol) |
| Ən azı bir hərf | `12345678` (yalnız rəqəm) | `Sifre123` (S,i,f,r,e var) |
| Ən azı bir rəqəm | `Sifreabi` (yalnız hərf) | `Sifre123` (1,2,3 var) |

`any()` funksiyası Python-da iterasiyanın içindən hər hansı bir elementin şərtə uyğun olub olmadığını yoxlayır. `any(c.isalpha() for c in pw)` — parolun hər simvolunu yoxlayır, ən azı biri hərfdirsə `True` qaytarır.

Bu yoxlama həm backend-də (burada), həm də frontend-də (auth.js-də `parolQeydiyyat` funksiyası) aparılır — **Defense in Depth** prinsipi. Frontend yoxlaması istifadəçiyə tez cavab vermək üçündür (UX), backend yoxlaması isə əsl güvənlik üçündür — çünki haker JavaScript yoxlamasını asanlıqla keçə bilər (brauzerin developer tools-u ilə).

---

## 4.2 SQL Injection Qorunması

### 4.2.1 SQL Injection Nədir?

SQL Injection (SQLi) — OWASP Top 10-un A03 kateqoriyasında yer alan ən təhlükəli veb zəifliklərindən biridir. Haker istifadəçi giriş sahəsinə xüsusi SQL kodu yazaraq verilənlər bazasını manipulyasiya edir.

Təhlükəli bir nümunə (bu layihədə istifadə EDİLMİR):

```python
# ❌ YANLIŞ — heç vaxt belə yazmayın:
email = request.form["email"]
cur.execute("SELECT * FROM users WHERE email = '" + email + "'")
```

Əgər istifadəçi e-poçt sahəsinə bunu yazarsa:

```
' OR '1'='1' --
```

SQL sorğusu belə olardı:

```sql
SELECT * FROM users WHERE email = '' OR '1'='1' --'
```

Bu sorğu **bütün istifadəçiləri** qaytarar — çünki `'1'='1'` həmişə doğrudur. `--` isə qalan hissəni şərh (comment) edir. Haker heç bir parol bilmədən sistemə giriş əldə edə bilər.

Daha təhlükəli variant:
```
'; DROP TABLE users; --
```

Bu, `users` cədvəlini tamamilə silər.

### 4.2.2 Bu Layihədə Qorunma: Parametrized Query

Bu layihədə **bütün SQL sorğuları parametrized query ilə yazılıb**. Bu, SQL injection-un ən etibarlı həll yoludur.

Giriş zamanı e-poçtun axtarılması:

```python
# backend/app.py — 107-110-cu sətir
cur.execute(
    "SELECT id, email, password_hash, full_name FROM users WHERE lower(email) = %s",
    (email_lower,),
)
```

Qeydiyyat zamanı yeni istifadəçinin yazılması:

```python
# backend/app.py — 141-144-cü sətir
cur.execute(
    "INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s)",
    (email_lower, password_hash, full_name),
)
```

Health check sorğusu:

```python
# backend/app.py — 233-cü sətir
cur.execute("SELECT 1")
```

Bütün hallarda `%s` placeholder istifadə edilir və dəyərlər ayrıca tuple (dəmət) ilə ötürülür.

### 4.2.3 Parametrized Query Necə Qoruyur?

`psycopg2` kitabxanası parametrized query-ni belə emal edir:

1. SQL şablonu (`"SELECT ... WHERE email = %s"`) ayrıca PostgreSQL-ə göndərilir
2. Dəyər (`email_lower`) ayrıca göndərilir
3. PostgreSQL dəyəri **mətn (data) kimi** qəbul edir, **kod (SQL) kimi yox**

Əgər istifadəçi e-poçt sahəsinə `' OR '1'='1' --` yazarsa:

Parametrized query ilə (bu layihədə):
```sql
SELECT ... WHERE lower(email) = ''' OR ''1''=''1'' --'
-- PostgreSQL bunu düz MƏTN kimi müqayisə edir
-- Heç bir injection baş vermir
-- Sadəcə belə bir e-poçt tapılmır → NULL qaytarılır
```

String birləşdirmə ilə (bu layihədə İSTİFADƏ EDİLMİR):
```sql
SELECT ... WHERE email = '' OR '1'='1' --'
-- PostgreSQL bunu SQL KODU kimi icra edir
-- Bütün sətirləri qaytarır!
```

Fərq budur: parametrized query-də istifadəçinin yazdığı **heç vaxt SQL kodu kimi icra edilmir**, yalnız data kimi müalicə olunur.

### 4.2.4 Bütün Sorğuların Auditi

Layihədəki bütün SQL sorğularını yoxlayaq:

| Sorğu | Fayl/Sətir | Parametrized? |
|---|---|---|
| `CREATE TABLE IF NOT EXISTS users (...)` | app.py:58 | Parametr yoxdur (statik DDL) — OK |
| `SELECT ... WHERE lower(email) = %s` | app.py:108 | Bəli ✓ |
| `SELECT ... WHERE id = %s` | app.py:121 | Bəli ✓ |
| `INSERT INTO users ... VALUES (%s, %s, %s)` | app.py:142 | Bəli ✓ |
| `SELECT 1` | app.py:233 | Parametr yoxdur (statik) — OK |

Nəticə: Layihədə **heç bir SQL injection riski yoxdur**. Bütün dinamik dəyərlər parametr kimi ötürülür.

---

## 4.3 Input Validation — Giriş Doğrulaması

### 4.3.1 E-poçt Doğrulaması

```python
# backend/app.py — 79-83-cü sətir
def validate_email(email: str) -> bool:
    email = (email or "").strip()
    if len(email) < 5 or "@" not in email or "." not in email.split("@")[-1]:
        return False
    return True
```

Bu funksiya üç şeyi yoxlayır:

1. `len(email) < 5` — ən qısa mümkün e-poçt `a@b.c` (5 simvol). Bundan qısa e-poçt ola bilməz.
2. `"@" not in email` — hər e-poçtda `@` işarəsi olmalıdır.
3. `"." not in email.split("@")[-1]` — `@` işarəsindən sonrakı hissədə (domain) nöqtə olmalıdır. `ali@mailcom` düzgün deyil, `ali@mail.com` düzgündür.

`email.split("@")[-1]` necə işləyir:
```
"ali@mail.com".split("@")  →  ["ali", "mail.com"]
                    [-1]    →  "mail.com"
"." in "mail.com"           →  True ✓
```

`.strip()` — mətnin əvvəlindəki və sonundakı boşluqları silir. İstifadəçi təsadüfən `" ali@mail.com "` yazarsa, bu düzəldilir.

`(email or "")` — əgər `email` parametri `None` olaraq gəlibsə, boş stringə çevirir. `None.strip()` xəta verərdi, amma `"".strip()` sadəcə `""` qaytarır.

Bu yoxlama **sadə bir doğrulamadır** — tam RFC 5322 standartına uyğun e-poçt validasiyası deyil. Məsələn, `ali@.com` buradan keçər amma real e-poçt deyil. Lakin bu layihə üçün kifayətdir — mürəkkəb regex validasiyalar öz problemlərini gətirir (RFC-yə tam uyğun regex 6000+ simvoldur).

### 4.3.2 Input Bounds Checking (Hədd Yoxlaması)

```python
# backend/app.py — 96-101-ci sətir
def login_input_bounds(email: str, password: str) -> Tuple[bool, Optional[str]]:
    if len(email) > 254 or len(password) > 256:
        return False, "E-poçt və ya parol çox uzundur."
    if "\x00" in email or "\x00" in password:
        return False, "Yanlış simvol."
    return True, None
```

Bu funksiya iki təhlükəli vəziyyətin qarşısını alır:

**1. Çox uzun giriş (Denial of Service riski):**

Əgər haker 10 milyon simvolluq string göndərərsə, hash funksiyası çox vaxt sərf edər — server yavaşlar. `email > 254` və `password > 256` limitləri bunu qarşısını alır.

254 limiti RFC 5321 standartından gəlir — internet protokolunda e-poçt ünvanı maksimum 254 oktet ola bilər. 256 parol limiti isə ağlabatan bir hədddir — daha uzun parol praktikada lazım olmur.

Frontend-də də eyni limitlər HTML atributları ilə tətbiq edilir:

```html
<!-- frontend/login.html — 37-ci sətir -->
<input ... maxlength="254" />

<!-- frontend/login.html — 49-cu sətir -->
<input ... maxlength="256" />
```

Amma HTML `maxlength` atributu güvənlik tədbi deyil — developer tools ilə asanlıqla silinə bilər. **Backend yoxlaması** həqiqi müdafiədir.

**2. Null Byte Injection:**

```python
if "\x00" in email or "\x00" in password:
    return False, "Yanlış simvol."
```

`\x00` — null bayt, yəni ASCII cədvəlindəki 0 nömrəli simvol. Bu simvol C dilində string-in sonunu bildirir. Bəzi proqramlar (xüsusilə fayl sistemi əməliyyatları) null baytı string sonu kimi qəbul edir, bu isə manipulyasiyaya yol açır.

Məsələn, fayl adı kontekstində:
```
"document.pdf\x00.exe"
```
Bəzi sistemlər bunu `document.pdf` kimi görər, amma əslində `.exe` faylıdır. Bu layihədə e-poçt və parolda null baytın olması mənasız olduğu üçün bloklanır.

### 4.3.3 Qeydiyyat Zamanı Tam Doğrulama Axını

Qeydiyyat endpoint-ində doğrulamalar zəncirvari tətbiq edilir — birinci keçməyən doğrulama proses dayandırır:

```python
# backend/app.py — 156-178-ci sətir
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    password2 = data.get("password_confirm") or ""
    full_name = (data.get("full_name") or "").strip()

    # Doğrulama 1: Ad uzunluğu
    if not full_name or len(full_name) < 2:
        return jsonify({"ok": False, "error": "Ad ən azı 2 simvol olmalıdır."}), 400

    # Doğrulama 2: E-poçt formatı
    if not validate_email(email):
        return jsonify({"ok": False, "error": "E-poçt düzgün deyil."}), 400

    # Doğrulama 3: Parol gücü
    ok, msg = validate_password_strength(password)
    if not ok:
        return jsonify({"ok": False, "error": msg}), 400

    # Doğrulama 4: Parol təsdiqləmə
    if password != password2:
        return jsonify({"ok": False, "error": "Parollar üst-üstə düşmür."}), 400

    # Bütün doğrulamalar keçdi → hash-lə və bazaya yaz
    pw_hash = generate_password_hash(password)
    ok_ins, err = user_insert(email.lower(), pw_hash, full_name)
    ...
```

Bu **early return pattern** (erkən qayıtma nümunəsi) adlanır — xəta tapılan kimi funksiya dərhal qayıdır, lazımsız əməliyyatlar icra edilmir. Bu, həm performans (hash hesablamaq bahadır, niyə yanlış məlumat üçün hesablayasan?), həm oxunaqlıq baxımından yaxşı praktikadır.

`request.get_json(silent=True) or {}` — bu ifadədə:
- `get_json(silent=True)` — sorğunun body-sini JSON kimi oxuyur. `silent=True` — əgər JSON formatı yanlışdırsa xəta atmır, `None` qaytarır
- `or {}` — əgər `None` gəlibsə (JSON yanlışsa və ya body boşdursa), boş dictionary istifadə et
- Bu sayədə `data.get("email")` xəta vermir — boş dictionary-dən `.get()` sadəcə `None` qaytarır

---

## 4.4 Session İdarəetməsi

### 4.4.1 Session Nədir?

HTTP protokolu **stateless** (vəziyyətsiz) protokoldur — hər sorğu müstəqildir, server əvvəlki sorğunu "yadda saxlamır". Lakin giriş sistemi üçün server bilməlidir ki, "bu sorğunu göndərən şəxs artıq daxil olub." Bu problemi **session** mexanizmi həll edir.

Session belə işləyir:
1. İstifadəçi uğurlu daxil olur
2. Server bir session yaradır və unikal identifikator (session ID) verir
3. Bu ID brauzərə **cookie** kimi göndərilir
4. Brauzer hər növbəti sorğuda bu cookie-ni avtomatik göndərir
5. Server cookie-yə baxıb istifadəçini tanıyır

### 4.4.2 Secret Key — Session Açarı

```python
# backend/app.py — 34-cü sətir
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)
```

Flask session-ları **imzalayır** (sign). Cookie dəyişdirilsə, imza uyğun gəlməz və Flask bunu rədd edir. İmza üçün `secret_key` lazımdır.

`os.environ.get("FLASK_SECRET_KEY")` — `.env` faylından oxuyur. Əgər orada yoxdursa:

`os.urandom(24)` — əməliyyat sisteminin kriptoqrafik təsadüfi ədəd generatorundan 24 bayt (192 bit) alır. Bu kifayət qədər güclüdür, lakin bir problemi var: server hər yenidən başlayanda yeni açar yaranır və **bütün mövcud session-lar etibarsız olur** — istifadəçilər çıxış etmiş olur. Buna görə production-da `.env`-dən sabit açar oxunmalıdır.

### 4.4.3 Session Yaradılması (Login)

```python
# backend/app.py — 205-208-ci sətir
session["user_id"] = row["id"]
session["email"] = row["email"]
u = user_get_public(row["id"])
return jsonify({"ok": True, "message": "Xoş gəldiniz!", "user": u})
```

Flask `session` obyekti — Python dictionary kimi işləyir. `session["user_id"] = 42` yazdıqda Flask bu dəyəri:
1. JSON-a çevirir
2. `secret_key` ilə HMAC imzası hesablayır
3. Base64 ilə kodlayır
4. `Set-Cookie` başlığı ilə brauzərə göndərir

Brauzərdə cookie belə görünür:
```
session=eyJ1c2VyX2lkIjo0MiwiZW1haWwiOiJhbGlAbWFpbC5jb20ifQ.ZxYkLw.abc123signature
```

Bu cookie-nin üç hissəsi var: məlumat + vaxt damğası + imza. İmza olmadan cookie-nin dəyişdirilməsi mümkün deyil.

### 4.4.4 Session Yoxlaması (/api/me)

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

Bu endpoint üç vəziyyəti idarə edir:

1. **Session yoxdur** (`"user_id" not in session`): İstifadəçi hələ daxil olmayıb. `logged_in: False` qaytarılır.

2. **Session var, amma bazada istifadəçi yoxdur** (`not u`): Bu baş verə bilər əgər hesab siliniblsə amma session hələ aktividir. Bu halda session təmizlənir (`session.clear()`) — bu **stale session** probleminin həllidir.

3. **Session var, istifadəçi bazada var**: Normal vəziyyət. İstifadəçi məlumatı qaytarılır.

`user_get_public` funksiyası `password_hash` qaytarmır — yəni session yoxlaması zamanı belə parol hash-i heç vaxt HTTP cavabında görünmür.

### 4.4.5 Session Silinməsi (Logout)

```python
# backend/app.py — 211-214-cü sətir
@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})
```

`session.clear()` — session-dakı bütün məlumatları silir. Bu, brauzərdəki cookie-ni dərhal silmir (brauzer cookie-ni lokal olaraq saxlayır), amma serverdə artıq bu session tanınmır — imza etibarsız olur.

Frontend-də logout belə çağırılır:

```javascript
// frontend/logged-in.html — 51-54-cü sətir
document.getElementById("btn-logout").addEventListener("click", function () {
  fetch("/api/logout", { method: "POST", credentials: "same-origin" }).then(function () {
    window.location.href = "login.html";
  });
});
```

`credentials: "same-origin"` — session cookie-nin sorğu ilə göndərilməsini təmin edir. Bu olmadan Flask hansı session-ı silməli olduğunu bilməzdi.

### 4.4.6 Session Təhlükəsizliyi — Mövcud Risklər

Bu layihədəki session mexanizminin güclü və zəif tərəfləri:

| Aspekt | Vəziyyət | İzahat |
|---|---|---|
| İmzalama | ✅ Güclü | `secret_key` ilə HMAC imzası; cookie dəyişdirilə bilməz |
| Session fixation | ✅ Qismən | `session.clear()` ilə çıxışda təmizlənir |
| HTTPS | ⚠️ Yoxdur | Cookie açıq HTTP ilə göndərilir; man-in-the-middle ilə oğurlana bilər |
| Secure flag | ⚠️ Yoxdur | Cookie `Secure` atributu olmadan HTTP-dən də göndərilir |
| HttpOnly flag | ✅ Var | Flask cookie-ləri default olaraq `HttpOnly` yaradır — JavaScript oxuya bilməz |
| SameSite | ⚠️ Təyin edilməyib | CSRF riskini artıra bilər |
| Expiration | ⚠️ Yoxdur | Session müddətsiz aktiv qalır — timeout tətbiq edilməyib |

---

## 4.5 Path Traversal Qorunması

### 4.5.1 Path Traversal Nədir?

Path Traversal (Directory Traversal) — haker URL vasitəsilə serverdə icazə verilməyən fayllara çatmağa çalışır. Məsələn:

```
http://localhost:5000/../../etc/passwd
http://localhost:5000/../backend/app.py
http://localhost:5000/../.env
```

Əgər server bu sorğuları yoxlamadan cavablandırsa, haker `.env` faylını (verilənlər bazası parolu!) və ya serverin konfiqurasiya fayllarını oxuya bilər.

### 4.5.2 Bu Layihədə Qorunma

```python
# backend/app.py — 241-256-cı sətir
@app.route("/", defaults={"path": "login.html"})
@app.route("/<path:path>")
def serve_file(path):
    # Qorunma 1: API sorğuları burada işlənmir
    if path.startswith("api/"):
        return "Tapılmadı", 404

    # Qorunma 2: Yalnız icazə verilmiş fayl tipləri
    allowed = {".html", ".css", ".js", ".jpg", ".jpeg", ".png", ".ico", ".svg"}

    # Qorunma 3: Path traversal yoxlaması
    safe_path = (FRONTEND_DIR / path).resolve()
    try:
        safe_path.relative_to(FRONTEND_DIR.resolve())
    except ValueError:
        return "Forbidden", 403

    # Qorunma 4: Fayl mövcudluğu
    if not safe_path.is_file():
        return "Tapılmadı", 404

    # Qorunma 5: Uzantı yoxlaması
    if safe_path.suffix.lower() not in allowed:
        return "Forbidden", 403

    return send_from_directory(FRONTEND_DIR, path)
```

Hər qorunma qatını nümunə ilə izah edək:

**Qorunma 1 — API marşrutlarının filtri:**
```python
if path.startswith("api/"):
    return "Tapılmadı", 404
```
Bu, `api/` ilə başlayan yolların statik fayl servisi tərəfindən işlənməsinin qarşısını alır. API endpoint-ləri ayrıca `@app.route()` dekoratoru ilə idarə edilir.

**Qorunma 2 — İcazə verilmiş uzantılar:**
```python
allowed = {".html", ".css", ".js", ".jpg", ".jpeg", ".png", ".ico", ".svg"}
```
Python `set` (çoxluq) istifadə edilib — axtarış `O(1)` vaxtda olur (siyahıda `O(n)` olardı). Yalnız bu 8 tip faylı servis etmək olar. Əgər serverdə `.py`, `.env`, `.sql` faylları olsa da, brauzerdən onlara çatmaq mümkün deyil.

**Qorunma 3 — Path traversal bloku (ən əsas qorunma):**
```python
safe_path = (FRONTEND_DIR / path).resolve()
try:
    safe_path.relative_to(FRONTEND_DIR.resolve())
except ValueError:
    return "Forbidden", 403
```

Bu necə işləyir — nümunə ilə:

Normal sorğu (`login.html`):
```
FRONTEND_DIR = D:\project\frontend
path = "login.html"
safe_path = (D:\project\frontend / "login.html").resolve()
          = D:\project\frontend\login.html
safe_path.relative_to(D:\project\frontend)  →  OK ✓
```

Hücum cəhdi (`../../.env`):
```
FRONTEND_DIR = D:\project\frontend
path = "../../.env"
safe_path = (D:\project\frontend / "../../.env").resolve()
          = D:\.env    ← frontend qovluğunun XARICINDA!
safe_path.relative_to(D:\project\frontend)  →  ValueError! ✗
→ return "Forbidden", 403
```

`.resolve()` — yolun içindəki `..` (bir qovluq yuxarı) simvollarını həll edir və **tam mütləq yolu** qaytarır. Simvolik linkləri (symlink) də açır.

`.relative_to()` — nəticə yolun `FRONTEND_DIR` qovluğunun **alt qovluğu** olub-olmadığını yoxlayır. Əgər xaricdədirsə `ValueError` atır.

Bu iki addım birlikdə **çox güclü qorunma** təmin edir — haker hansı `../` kombinasiyasını yazsa da, `frontend/` qovluğundan kənara çıxa bilməz.

**Qorunma 4 — Fayl mövcudluğu:**
```python
if not safe_path.is_file():
    return "Tapılmadı", 404
```
Əgər istənilən fayl mövcud deyilsə, 404 qaytarılır. Bu həm normal "tapılmadı" halını, həm də qovluq axtarışı cəhdlərini bloklayır (`.is_file()` qovluqlar üçün `False` qaytarır).

**Qorunma 5 — Uzantı yoxlaması:**
```python
if safe_path.suffix.lower() not in allowed:
    return "Forbidden", 403
```
`.suffix` — faylın uzantısını qaytarır (`.html`, `.py` və s.). `.lower()` — böyük hərf cəhdlərini bloklayır (`.PY`, `.Env`). Əgər uzantı icazə verilmiş siyahıda yoxdursa — 403 qaytarılır.

---

## 4.6 Generic Error Mesajları — User Enumeration Qorunması

### 4.6.1 User Enumeration Nədir?

User Enumeration — haker sistemdə hansı e-poçtların qeydiyyatlı olduğunu öyrənməyə çalışır. Əgər xəta mesajları fərqlidirsə:

```
"ali@mail.com" → "Parol səhvdir"        ← haker bilir: bu e-poçt bazadadır!
"yoxbele@x.com" → "İstifadəçi tapılmadı"  ← haker bilir: bu e-poçt yoxdur
```

Haker minlərlə e-poçt sınayaraq real hesabların siyahısını yarada bilər. Sonra yalnız real hesablara brute-force hücumu edər.

### 4.6.2 Bu Layihədə Qorunma

Giriş zamanı iki fərqli vəziyyətdə **eyni xəta mesajı** qaytarılır:

```python
# backend/app.py — 193-203-cü sətir

# Vəziyyət 1: E-poçt bazada yoxdur
row = user_get_by_email(email)
if row is None:
    return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401

# Vəziyyət 2: E-poçt var, amma parol yanlışdır
ph = row.get("password_hash")
try:
    pw_ok = bool(ph) and check_password_hash(str(ph), password)
except (TypeError, ValueError):
    pw_ok = False
if not pw_ok:
    return jsonify({"ok": False, "error": "E-poçt və ya parol səhvdir."}), 401
```

Hər iki halda:
- Eyni mesaj: `"E-poçt və ya parol səhvdir."`
- Eyni HTTP status kodu: `401`

Haker cavabdan hansı halın baş verdiyini ayırd edə bilmir.

Lakin burada incə bir nöqtə var: **qeydiyyat zamanı** `"Bu e-poçt artıq qeydiyyatdan keçib"` mesajı qaytarılır:

```python
# backend/app.py — 149-150-ci sətir
except psycopg2.IntegrityError:
    return False, "Bu e-poçt artıq qeydiyyatdan keçib."
```

Bu, qeydiyyat forması vasitəsilə user enumeration-a imkan verir. Tam qorunma üçün qeydiyyatda da ümumi mesaj (məsələn, "Əgər bu e-poçt qeydiyyatlı deyilsə, təlimatlar göndəriləcək") istifadə edilməlidir. Lakin kiçik layihələrdə bu qəbulediləcək bir kompromisdir — UX (istifadəçi təcrübəsi) baxımından istifadəçi qeydiyyatda niyə uğursuz olduğunu bilməlidir.

---

## 4.7 Xülasə: Backend Təhlükəsizlik Matris

| Mexanizm | Qoruyur | Güc | Qeyd |
|---|---|---|---|
| Parol Hashing (scrypt/PBKDF2) | Parol oğurluğu | 🟢 Güclü | Salt + iteration; sənaye standartı |
| Parametrized Query | SQL Injection | 🟢 Güclü | Bütün sorğular parametrized |
| E-poçt doğrulaması | Yanlış formatda giriş | 🟡 Orta | Sadə yoxlama, tam RFC uyğunluğu yoxdur |
| Parol gücü doğrulaması | Zəif parollar | 🟡 Orta | 8 simvol + hərf + rəqəm; xüsusi simvol tələb etmir |
| Input bounds check | DoS, null byte injection | 🟢 Güclü | 254/256 limit; \x00 bloku |
| Session imzalama | Session dəyişdirmə | 🟢 Güclü | HMAC imzası; HttpOnly cookie |
| Path Traversal qorunması | Fayl oğurluğu | 🟢 Güclü | resolve() + relative_to() + uzantı filtri |
| Generic xəta mesajları | User Enumeration | 🟡 Orta | Login-da var; register-da qismən |
| CSRF qorunması | Cross-Site Request Forgery | 🔴 Yoxdur | Token və ya SameSite yoxdur |
| Rate Limiting | Brute-force hücum | 🔴 Yoxdur | Limitsiz giriş cəhdi mümkündür |
| Security Headers | Clickjacking, XSS, MIME sniffing | 🔴 Yoxdur | CSP, X-Frame-Options yoxdur |

---

*Növbəti bölmədə frontend kodunun təhlükəsizlik analizi — client-side doğrulama, XSS qorunması, Fetch API istifadəsi — ətraflı araşdırılacaq.*
