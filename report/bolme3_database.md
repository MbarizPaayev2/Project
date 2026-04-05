# Bölmə 3 — Verilənlər Bazası Sxeminin Dərin Analizi

**Fənn:** Web Təhlükəsizliyi  
**Tələbə:** [Ad Soyad]  
**Kurs:** II kurs  
**Tarix:** Aprel 2026

---

## 3.1 Verilənlər Bazası Nədir və Niyə PostgreSQL?

Hər veb tətbiq istifadəçi məlumatlarını bir yerdə saxlamalıdır. Məsələn, bir istifadəçi qeydiyyatdan keçəndə onun adı, e-poçtu və parolu yadda qalmalıdır ki, növbəti dəfə daxil ola bilsin. Bu məlumatları saxlayan sistem — verilənlər bazasıdır (database).

Bu layihədə **PostgreSQL** istifadə edilib. PostgreSQL dünyada ən etibarlı açıq mənbəli (open-source) relational verilənlər bazası sayılır. Onu MySQL-dən fərqləndirən bir neçə xüsusiyyət var:

- Daha güclü məlumat bütövlüyü (data integrity) qaydaları
- ACID tranzaksiya dəstəyi (Atomicity, Consistency, Isolation, Durability)
- JSON, massiv, zaman dilimi kimi mürəkkəb data tipləri

Layihənin `requirements.txt` faylında PostgreSQL ilə əlaqə üçün `psycopg2-binary` kitabxanası göstərilib:

```
psycopg2-binary>=2.9.9
```

Bu kitabxana Python kodunun PostgreSQL-ə SQL sorğuları göndərməsinə imkan verir.

---

## 3.2 Cədvəl Sxeminin Tam Analizi

Layihədə yalnız bir cədvəl var — `users`. Bu cədvəl `database/schema.sql` faylında təyin edilib:

```sql
-- database/schema.sql (tam fayl)
-- Yalnız giriş / qeydiyyat üçün minimal sxem (PostgreSQL)
-- Tətbiq işə düşəndə də CREATE TABLE edilir; əl ilə: psql "$DATABASE_URL" -f database/schema.sql

CREATE TABLE IF NOT EXISTS users (
    id            BIGSERIAL    PRIMARY KEY,
    email         TEXT         UNIQUE NOT NULL,
    password_hash TEXT         NOT NULL,
    full_name     TEXT,
    created_at    TIMESTAMPTZ  DEFAULT NOW()
);
```

Bu 5 sütunun hər birini ayrıca izah edək.

---

### 3.2.1 id — BIGSERIAL PRIMARY KEY

```sql
id BIGSERIAL PRIMARY KEY
```

Bu sütun hər istifadəçiyə unikal nömrə verir: 1, 2, 3, 4...

**BIGSERIAL** — bu tip iki şeyi eyni anda edir:
1. Avtomatik artan tam ədəd yaradır (auto-increment)
2. Böyük aralıqda işləyir: 1-dən 9,223,372,036,854,775,807-ə qədər (9.2 kvintilyon)

Standart `SERIAL` tip maksimum 2.1 milyard (2,147,483,647) olar. Kiçik layihələr üçün kifayətdir, amma böyük sistemlər üçün `BIGSERIAL` daha etibarlıdır. Bu layihədə bəlkə heç 100 istifadəçi olmayacaq, amma peşəkar vərdiş olaraq `BIGSERIAL` seçilmişdir.

**PRIMARY KEY** — bu məhdudiyyət iki qaydanı eyni anda tətbiq edir:
- `UNIQUE` — heç iki sətir eyni `id`-yə sahib ola bilməz
- `NOT NULL` — `id` boş ola bilməz

`id` sütunu **tətbiqin daxili identifikatorudur** — istifadəçiyə göstərilmir, yalnız backend kodunda session-da saxlanılır:

```python
# backend/app.py — 205-ci sətir
session["user_id"] = row["id"]
```

Session-da e-poçt əvəzinə `id` saxlamaq daha düzgündür: istifadəçi e-poçtunu dəyişdirə bilər, amma `id` heç vaxt dəyişmir.

---

### 3.2.2 email — TEXT UNIQUE NOT NULL

```sql
email TEXT UNIQUE NOT NULL
```

Bu sütun istifadəçinin elektron poçt ünvanını saxlayır.

**TEXT** — PostgreSQL-də mətn tipidir. `VARCHAR(255)` kimi uzunluq limiti yoxdur — istənilən uzunluqda mətn saxlaya bilər. Lakin backend kodunda uzunluq ayrıca yoxlanılır:

```python
# backend/app.py — 97-ci sətir
if len(email) > 254 or len(password) > 256:
    return False, "E-poçt və ya parol çox uzundur."
```

254 simvol limiti RFC 5321 standartından gəlir — internet e-poçt protokoluna görə e-poçt ünvanı maksimum 254 simvol ola bilər.

**UNIQUE** — eyni e-poçtla iki qeydiyyat mümkün deyil. Əgər kimsə artıq `ali@mail.com` ilə qeydiyyatdan keçibsə, ikinci cəhd bazada belə xəta yaradır:

```python
# backend/app.py — 149-150-ci sətir
except psycopg2.IntegrityError:
    return False, "Bu e-poçt artıq qeydiyyatdan keçib."
```

PostgreSQL `IntegrityError` atır — Python kodu bu xətanı tutur və istifadəçiyə aydın mesaj göstərir.

**NOT NULL** — e-poçt sahəsi boş ola bilməz. Əgər backend kodu hansısa səhv nəticəsində boş e-poçt göndərsə belə, baza qəbul etməyəcək — bu **ikinci müdafiə xəttidir** (defense in depth).

E-poçtlar bazaya yazılmazdan əvvəl kiçik hərflərə çevrilir:

```python
# backend/app.py — 174-cü sətir (register)
ok_ins, err = user_insert(email.lower(), pw_hash, full_name)

# backend/app.py — 184-cü sətir (login)
email = (data.get("email") or "").strip().lower()
```

Bu niyə vacibdir? Çünki `Ali@Mail.com` və `ali@mail.com` texniki olaraq eyni e-poçtdur. `.lower()` olmadan istifadəçi böyük hərflə qeydiyyatdan keçib kiçik hərflə daxil ola bilməzdi. Sorğu zamanı da `lower()` istifadə edilir:

```python
# backend/app.py — 108-ci sətir
cur.execute(
    "SELECT id, email, password_hash, full_name FROM users WHERE lower(email) = %s",
    (email_lower,),
)
```

`WHERE lower(email) = %s` — bazadakı e-poçtu da kiçik hərfə çevirib müqayisə edir.

---

### 3.2.3 password_hash — TEXT NOT NULL

```sql
password_hash TEXT NOT NULL
```

Bu sütun istifadəçinin parolunun **hash-lənmiş versiyasını** saxlayır. Xam parol (plain-text password) bazaya **heç vaxt** yazılmır.

Sütunun adı özü bunu vurğulayır — `password` yox, `password_hash`. Bu, kod oxuyan hər kəsə aydın signal verir: burada düz parol yoxdur.

**Hash nədir?** Hash — mətnin bir-tərəfli riyazi çevrilməsidir. "Sifre123" parolu hash-ləndikdə belə bir şey alınır:

```
scrypt:32768:8:1$MjQ1NjI0$c8f7a1b9e3d4...   (çox uzun, təxminən 150 simvol)
```

Hash-in xüsusiyyətləri:
- Eyni parol həmişə eyni hash verir
- Hash-dən orijinal parolu bərpa etmək **praktiki olaraq mümkün deyil** (one-way function)
- Bir simvol dəyişəndə hash tamamilə fərqli olur

Qeydiyyat zamanı hash belə yaranır:

```python
# backend/app.py — 173-cü sətir
pw_hash = generate_password_hash(password)
```

`generate_password_hash` funksiyası Werkzeug kitabxanasındandır və standart olaraq **PBKDF2-SHA256** alqoritmini işlədir. Bu alqoritm:
- Parola **salt** əlavə edir (hər hash üçün unikal təsadüfi bayt)
- Hash-i minlərlə dəfə təkrarlayır (iteration) — bu, brute-force hücumu çox yavaşladır
- Salt sayəsində iki istifadəçi eyni parolu seçsə belə, bazadakı hash-lər fərqli olur

Giriş zamanı hash müqayisəsi belə aparılır:

```python
# backend/app.py — 199-ci sətir
pw_ok = bool(ph) and check_password_hash(str(ph), password)
```

`check_password_hash` — istifadəçinin daxil etdiyi parolu hash-ləyir və bazadakı hash ilə müqayisə edir. Əgər eynidir — parol düzgündür.

**Niyə bu vacibdir?**

Əgər haker bazaya daxil olsa (SQL injection, server hack və s.), o, `password_hash` sütununu görəcək. Amma bu hash-dən orijinal parolu bərpa edə bilməyəcək. Müqayisə üçün:

Təhlükəli yanaşma (bu layihədə istifadə EDİLMİR):
```sql
-- YANLIŞ: password düz saxlanılır
CREATE TABLE users (
    email TEXT,
    password TEXT    -- ← haker bazanı əlsə, bütün parolları oxuyar
);
```

Təhlükəsiz yanaşma (bu layihədə istifadə EDİLİR):
```sql
-- DÜZGÜN: yalnız hash saxlanılır
CREATE TABLE users (
    email TEXT,
    password_hash TEXT   -- ← haker bazanı əlsə belə, parolları bilməz
);
```

---

### 3.2.4 full_name — TEXT

```sql
full_name TEXT
```

Bu sütun istifadəçinin adını saxlayır. Digər sütunlardan fərqli olaraq burada `NOT NULL` yoxdur — yəni bu sahə boş (NULL) ola bilər.

Lakin backend kodu girişdə bunu yoxlayır:

```python
# backend/app.py — 163-164-cü sətir
if not full_name or len(full_name) < 2:
    return jsonify({"ok": False, "error": "Ad ən azı 2 simvol olmalıdır."}), 400
```

Yəni backend boş ad qəbul etmir, amma baza icazə verir. Bu ikiqat yanaşma belədir: əgər gələcəkdə başqa bir yolla (məsələn admin paneli) istifadəçi əlavə etmək lazım olsa, ad sahəsi məcburi olmasın.

Frontend-də qeydiyyat formasında bu sahə belə göstərilir:

```html
<!-- frontend/register.html — 32-35-ci sətir -->
<label for="reg-name">Ad, soyad</label>
<input type="text" id="reg-name" name="full_name"
       autocomplete="name" placeholder="Şəxsiyyət sənədindəki kimi" />
<span class="auth-hint">Ən azı 2 simvol.</span>
```

---

### 3.2.5 created_at — TIMESTAMPTZ DEFAULT NOW()

```sql
created_at TIMESTAMPTZ DEFAULT NOW()
```

Bu sütun istifadəçinin qeydiyyat tarixini və vaxtını saxlayır.

**TIMESTAMPTZ** — "timestamp with time zone" deməkdir. Yəni yalnız tarih və vaxt deyil, həm də saat qurşağı saxlanılır. Məsələn:

```
2026-04-05 01:45:00+04:00    ← Bakı vaxtı (UTC+4)
```

Bu niyə vacibdir? Əgər server ABŞ-da, istifadəçi Azərbaycanda olarsa, `TIMESTAMP` (time zone olmadan) doğru vaxtı göstərməyəcək. `TIMESTAMPTZ` isə vaxtı həmişə düzgün çevirir.

**DEFAULT NOW()** — əgər `INSERT` sorğusunda `created_at` dəyəri verilməsə, PostgreSQL avtomatik olaraq cari vaxtı yazır. Backend kodunda bu sahə ümumiyyətlə göndərilmir:

```python
# backend/app.py — 142-ci sətir
cur.execute(
    "INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s)",
    (email_lower, password_hash, full_name),
)
```

Gördüyünüz kimi `INSERT`-də yalnız 3 sütun var: `email`, `password_hash`, `full_name`. `id` və `created_at` PostgreSQL tərəfindən avtomatik doldurulur.

**Təhlükəsizlik baxımından** `created_at` bir **audit trail** (izləmə izi) funksiyası daşıyır. Əgər şübhəli hesab yaradılsa, yaranma vaxtını bilmək təhqiqat üçün faydalıdır.

İstifadəçi məlumatı qaytarılanda `created_at` ISO 8601 formatına çevrilir:

```python
# backend/app.py — 130-131-ci sətir
if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
    d["created_at"] = d["created_at"].isoformat()
```

Bu format — `"2026-04-05T01:45:00+04:00"` — beynəlxalq standartdır və bütün proqramlaşdırma dilləri tərəfindən rahat oxunur.

---

## 3.3 Cədvəlin Avtomatik Yaradılması

Tətbiq ilk dəfə işə düşəndə `users` cədvəlinin mövcud olub-olmadığını yoxlamaq lazımdır. Bunu əl ilə SQL çalışdırmaq əvəzinə, backend kodu bunu avtomatik edir:

```python
# backend/app.py — 54-70-ci sətir
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
```

`CREATE TABLE IF NOT EXISTS` — bu SQL ifadəsi belə işləyir:
- Əgər `users` cədvəli **yoxdursa** — yaradır
- Əgər `users` cədvəli **artıq varsa** — heç nə etmir, xəta vermir

Bu yanaşma **idempotent** adlanır — neçə dəfə çalışdırsan da eyni nəticəni verir. Tətbiq hər yenidən başlayanda bu funksiya çağırılır:

```python
# backend/app.py — 73-76-cı sətir
try:
    init_db()
except Exception as ex:
    print("DB init:", ex)
```

`try/except` bloku — əgər verilənlər bazası hələ hazır deyilsə (məsələn, PostgreSQL servisi başlamamışsa), tətbiq çökmür, yalnız konsolda "DB init: connection refused" kimi mesaj yazılır.

---

## 3.4 Verilənlər Bazası Bağlantısı

Hər API sorğusunda yeni bir bağlantı açılır:

```python
# backend/app.py — 47-51-ci sətir
def get_db():
    import psycopg2
    from psycopg2.extras import RealDictCursor

    return psycopg2.connect(_effective_database_url(), cursor_factory=RealDictCursor)
```

**RealDictCursor** — PostgreSQL-dən gələn sətirləri Python dictionary (lüğət) formatında qaytarır. Fərqi belədir:

Standart cursor ilə:
```python
row = cur.fetchone()
# row = (1, "ali@mail.com", "scrypt:...", "Əli Həsənov", datetime(...))
# row[0] = id, row[1] = email   ← indeks nömrəsi ilə
```

RealDictCursor ilə:
```python
row = cur.fetchone()
# row = {"id": 1, "email": "ali@mail.com", "password_hash": "scrypt:...", ...}
# row["email"] = "ali@mail.com"   ← sütun adı ilə
```

İkinci variant kodu daha oxunaqlı edir — `row[1]` əvəzinə `row["email"]` yazmaq koddaki xətaları azaldır.

Bağlantı URL-i mühitə görə tənzimlənir:

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

Bu funksiya nə edir:
1. `DATABASE_URL`-i hissələrə ayırır (host, port, database adı və s.)
2. Əgər tətbiq Vercel cloud platformasında işləyirsə — `sslmode=require` əlavə edir
3. Bu, bazaya olan bağlantının **şifrələnmiş** (encrypted) olmasını tələb edir
4. Lokal mühitdə isə URL olduğu kimi qalır

Cloud mühitdə SSL olmadan verilənlər bazası bağlantısı şifrələnməmiş olur — şəbəkə trafikini izləyən biri SQL sorğularını və cavablarını oxuya bilər. `sslmode=require` bunu qarşısını alır.

---

## 3.5 Verilənlər Bazasından Məlumat Oxuma

Layihədə iki oxuma funksiyası var:

### İstifadəçini e-poçta görə tapmaq (giriş zamanı):

```python
# backend/app.py — 104-114-cü sətir
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
```

Bu funksiyanın diqqət çəkən cəhətləri:

1. `%s` — parametrized query (SQL injection-a qarşı qorunma). Burada `%s` Python-un string formatting operatoru deyil — psycopg2-nin xüsusi placeholder-idir. Dəyər ayrıca tuple ilə ötürülür: `(email_lower,)`. Bu, dəyərin SQL-ə birbaşa birləşdirilmədiyini, əksinə ayrıca parametr kimi  göndərildiyini bildirir.

2. `WHERE lower(email) = %s` — həm bazadakı e-poçtu, həm də daxil edilən e-poçtu kiçik hərfə çevirir. Case-insensitive axtarış.

3. `fetchone()` — yalnız bir nəticə qaytarır. `UNIQUE` məhdudiyyəti olduğu üçün onsuz da ən çox bir nəticə ola bilər.

4. `dict(row) if row else None` — əgər istifadəçi tapılmadısa `None`, tapıldısa dictionary qaytarır.

5. `conn.close()` — bağlantı funksiyanın sonunda bağlanır. Bu vacibdir: bağlanmayan bağlantılar (connection leak) zamanla serverin resurslarını tükəndirir.

### İstifadəçinin açıq məlumatını almaq (session yoxlaması zamanı):

```python
# backend/app.py — 117-132-ci sətir
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
```

Bu funksiyanın `user_get_by_email`-dən əsas fərqi: **`password_hash` sütunu seçilmir**. Yalnız `id`, `email`, `full_name`, `created_at` qaytarılır. Bu prinsip **Minimum Privilege** (ən az imtiyaz) adlanır — bir funksiya yalnız ehtiyacı olan məlumatı almalıdır. Parol hash-i istifadəçiyə göstərilməməlidir.

Bu funksiya `/api/me` endpoint-ində işlədilir:

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

Əgər session-dakı `user_id` bazada artıq mövcud deyilsə (məsələn, hesab siliniblsə), session təmizlənir — **stale session** (köhnəlmiş session) problemi həll edilir.

---

## 3.6 Verilənlər Bazasına Məlumat Yazmaq

Yeni istifadəçi yazmaq üçün bir funksiya var:

```python
# backend/app.py — 135-152-ci sətir
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
```

**`conn.commit()`** niyə lazımdır? PostgreSQL-də dəyişikliklər avtomatik yazılmır. `cur.execute()` sorğunu icra edir, amma `commit()` çağırılana qədər bu dəyişiklik müvəqqətidir (transaction). Əgər `commit()` olmadan `conn.close()` olsa, dəyişiklik itər. Bu, tranzaksiya bütövlüyünü qoruyur — əgər çoxlu dəyişiklik edəndə biri uğursuz olarsa, hamısını geri almaq (rollback) mümkündür.

**İstisna idarəetməsi (Exception Handling):**

`IntegrityError` — yalnız `UNIQUE` məhdudiyyəti pozulanda atılır. Yəni eyni e-poçtla ikinci qeydiyyat. Backend bu xətanı tutur və "Bu e-poçt artıq qeydiyyatdan keçib" mesajı ilə əvəzləyir. İstifadəçi heç vaxt çiy PostgreSQL xəta mesajını görmir — bu həm UX, həm də təhlükəsizlik üçün doğrudur (server daxili detalları gizlə).

`Exception as ex` — gözlənilməyən bütün digər xətaları tutur (bağlantı kəsilməsi, disk problemi və s.). `str(ex)` xətanı string kimi qaytarır.

---

## 3.7 Verilənlər Bazası Sağlamlıq Yoxlaması

Backend-də verilənlər bazasının işləyib-işləmədiyini yoxlamaq üçün xüsusi endpoint var:

```python
# backend/app.py — 228-238-ci sətir
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
```

`SELECT 1` — ən sadə SQL sorğusudur. Heç bir cədvələ müraciət etmir, yalnız "bazaya qoşula bilirəmmi?" sualını cavablandırır. Əgər bağlantı uğursuzsa, HTTP 503 (Service Unavailable) qaytarılır.

Bu tip endpointlər **monitoring** və **load balancer** sistemlərində istifadə olunur — server sağlamdırsa trafik ona yönləndirilir, deyilsə başqa serverə keçirilir.

---

## 3.8 Təhlükəsizlik Qiymətləndirməsi

### Müsbət cəhətlər:

| Xüsusiyyət | Nə qoruyur |
|---|---|
| `password_hash` sütunu | Xam parollar bazada yoxdur |
| `UNIQUE` email | Eyni e-poçtla iki hesab yaranmır |
| `NOT NULL` məhdudiyyətləri | Boş kritik sahələr yazıla bilmir |
| Parametrized query (`%s`) | SQL injection-a qarşı qorunma |
| `user_get_public`-da hash qaytarılmır | İstifadəçiyə lazımsız həssas məlumat göstərilmir |
| `.lower()` e-poçt normallaması | Case-sensitivity problemlərinin qarşısını alır |
| `IntegrityError` tutulması | DB xətaları istifadəçiyə açıq göstərilmir |

### Məhdudiyyətlər və tövsiyələr:

| Məsələ | Risk | Tövsiyə |
|---|---|---|
| Connection pool yoxdur | Hər sorğuda yeni bağlantı açılır; yüksək trafik zamanı performans problemi | `psycopg2.pool.SimpleConnectionPool` istifadə et |
| `conn.close()` finally blokunda deyil | Əgər `commit()` xəta versə, bağlantı açıq qalar | `with` statement və ya `try/finally` işlət |
| İndeks yoxdur (email üçün) | `UNIQUE` avtomatik indeks yaradır, amma `lower(email)` üçün ayrıca functional index lazımdır | `CREATE INDEX idx_users_email_lower ON users (lower(email))` |
| Silinmiş hesablar üçün mexanizm yoxdur | `DELETE` yoxdur, yalnız `INSERT` və `SELECT` | Soft delete (`is_deleted` boolean sütunu) əlavə et |

---

*Növbəti bölmədə backend kodunun təhlükəsizlik analizi — parol hashing, SQL injection qorunması, session idarəetməsi — ətraflı araşdırılacaq.*
