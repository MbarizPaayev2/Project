/* Minimal paket: yalnız giriş və qeydiyyat (SQLi lab yoxdur) */

(function () {
  var msgEl = document.getElementById("auth-message");
  var formLogin = document.getElementById("login-form");
  var formRegister = document.getElementById("register-form");

  function setAuthMsg(text, isError) {
    if (!msgEl) return;
    msgEl.textContent = text || "";
    if (!text) {
      msgEl.className = "form-msg form-grid--full-width";
      return;
    }
    msgEl.className =
      "form-msg form-grid--full-width is-visible " + (isError ? "form-msg--error" : "form-msg--ok");
  }

  function trim(s) {
    return (s || "").trim();
  }

  function fetchJsonApi(url, options) {
    return fetch(url, options).then(function (r) {
      return r.text().then(function (text) {
        var data;
        if (text) {
          try {
            data = JSON.parse(text);
          } catch (e) {
            data = { ok: false, error: "Server cavabı gözlənilməzdir (HTTP " + r.status + ")." };
          }
        } else {
          data = { ok: false, error: "Boş cavab (HTTP " + r.status + ")." };
        }
        return { status: r.status, data: data };
      });
    });
  }

  function emailDuzdur(email) {
    var e = trim(email);
    if (e.length < 5) return false;
    var at = e.indexOf("@");
    if (at < 1) return false;
    var dom = e.slice(at + 1);
    return dom.indexOf(".") >= 0;
  }

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

  function inputXeta(el, gostar) {
    if (!el) return;
    if (gostar) el.classList.add("input-error");
    else el.classList.remove("input-error");
  }

  if (formLogin) {
    var inEmail = document.getElementById("login-email");
    var inPw = document.getElementById("login-password");
    var emailHint = document.getElementById("login-email-hint");
    var relaxedEmail = document.getElementById("auth-relaxed-email");

    function emailHintYenile() {
      if (!emailHint) return;
      var v = trim(inEmail.value);
      var rel = relaxedEmail && relaxedEmail.checked;
      if (!v) {
        emailHint.textContent = "Düzgün e-poçt formatı";
        emailHint.className = "auth-hint";
        return;
      }
      if (!rel && !emailDuzdur(v)) {
        emailHint.textContent = "Xəta: düzgün e-poçt daxil edin (məs. ad@domain.com)";
        emailHint.className = "auth-hint auth-hint--error";
      } else {
        emailHint.textContent = rel ? "Korporativ / xüsusi format göndərilir" : "Düzgün e-poçt formatı";
        emailHint.className = "auth-hint";
      }
    }

    function emailXetaLogin() {
      var v = trim(inEmail.value);
      var rel = relaxedEmail && relaxedEmail.checked;
      inputXeta(inEmail, v.length > 0 && !rel && !emailDuzdur(v));
    }

    inEmail.addEventListener("input", function () {
      emailXetaLogin();
      emailHintYenile();
    });
    inEmail.addEventListener("blur", emailHintYenile);
    if (relaxedEmail) {
      relaxedEmail.addEventListener("change", function () {
        emailXetaLogin();
        emailHintYenile();
      });
    }
    inPw.addEventListener("input", function () {
      inputXeta(inPw, false);
    });

    formLogin.addEventListener("submit", function (e) {
      e.preventDefault();
      setAuthMsg("", false);
      var genisFormat = relaxedEmail && relaxedEmail.checked;
      var email = trim(inEmail.value);
      var pw = inPw.value;

      if (!genisFormat && !emailDuzdur(email)) {
        setAuthMsg("E-poçt düzgün deyil — nümunə@mail.com formatında olmalıdır.", true);
        inputXeta(inEmail, true);
        emailHintYenile();
        inEmail.focus();
        return;
      }
      if (genisFormat && !email) {
        setAuthMsg("E-poçt sahəsini doldurun.", true);
        inputXeta(inEmail, true);
        inEmail.focus();
        return;
      }
      if (!pw) {
        setAuthMsg("Parol yazın.", true);
        inputXeta(inPw, true);
        inPw.focus();
        return;
      }

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
    });
  }

  if (formRegister) {
    var rAd = document.getElementById("reg-name");
    var rEmail = document.getElementById("reg-email");
    var rPw = document.getElementById("reg-password");
    var rPw2 = document.getElementById("reg-password2");
    var relaxedReg = document.getElementById("auth-relaxed-email");
    var termsReg = document.getElementById("reg-terms");

    function emailXetaYenile() {
      if (!rEmail) return;
      var rel = relaxedReg && relaxedReg.checked;
      inputXeta(rEmail, trim(rEmail.value).length > 0 && !rel && !emailDuzdur(rEmail.value));
    }

    rAd.addEventListener("input", function () {
      var v = trim(rAd.value);
      inputXeta(rAd, v.length > 0 && v.length < 2);
    });
    rEmail.addEventListener("input", emailXetaYenile);
    if (relaxedReg) relaxedReg.addEventListener("change", emailXetaYenile);
    rPw.addEventListener("input", function () {
      var x = parolQeydiyyat(rPw.value);
      inputXeta(rPw, rPw.value.length > 0 && x !== "");
    });
    rPw2.addEventListener("input", function () {
      inputXeta(rPw2, rPw2.value && rPw2.value !== rPw.value);
    });

    formRegister.addEventListener("submit", function (e) {
      e.preventDefault();
      setAuthMsg("", false);

      var ad = trim(rAd.value);
      var genisReg = relaxedReg && relaxedReg.checked;
      var email = trim(rEmail.value);
      var pw = rPw.value;
      var pw2 = rPw2.value;

      if (ad.length < 2) {
        setAuthMsg("Ad və soyadı daxil edin (ən azı 2 simvol).", true);
        inputXeta(rAd, true);
        rAd.focus();
        return;
      }
      if (!genisReg && !emailDuzdur(email)) {
        setAuthMsg("Əlaqə e-poçtunu düzgün daxil edin.", true);
        inputXeta(rEmail, true);
        rEmail.focus();
        return;
      }
      if (genisReg && !email) {
        setAuthMsg("Elektron poçt ünvanınızı daxil edin.", true);
        inputXeta(rEmail, true);
        rEmail.focus();
        return;
      }
      if (termsReg && !termsReg.checked) {
        setAuthMsg("Davam etmək üçün şərtlərlə razılıq verin.", true);
        termsReg.focus();
        return;
      }
      var px = parolQeydiyyat(pw);
      if (px) {
        setAuthMsg(px, true);
        inputXeta(rPw, true);
        rPw.focus();
        return;
      }
      if (pw !== pw2) {
        setAuthMsg("Parol təkrarı ilkin parolla üst-üstə düşmür.", true);
        inputXeta(rPw2, true);
        rPw2.focus();
        return;
      }

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
    });
  }
})();
