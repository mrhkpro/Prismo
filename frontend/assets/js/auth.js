(async function () {
  const params = new URLSearchParams(location.search);
  const oauthResult = params.get("oauth");
  const oauthError = params.get("auth_error");

  const tabs = document.querySelectorAll(".auth-tab");
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");
  const authTitle = document.getElementById("authTitle");
  const authSub = document.getElementById("authSub");
  const errorBox = document.getElementById("authError");
  const googleButton = document.getElementById("googleLoginBtn");

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.classList.add("show");
  }
  function clearError() {
    errorBox.classList.remove("show");
    errorBox.textContent = "";
  }
  function isEnglish() {
    return !!(window.QZI18n && window.QZI18n.isEnglish && window.QZI18n.isEnglish());
  }
  function oauthErrorMessage(code) {
    const en = {
      google_not_configured: "Google sign-in is not configured on the server yet.",
      google_denied: "Google sign-in was cancelled.",
      google_state: "Google sign-in could not verify this request. Please try again.",
      google_exchange: "Google could not complete the secure sign-in exchange. Check the callback configuration.",
      google_profile: "Google did not return a verified profile.",
      google_blocked: "This account is disabled.",
      google_email_conflict: "This email is already linked to another account. Sign in using your previous method.",
      google_failed: "Google sign-in could not be completed. Please try again.",
    };
    const fa = {
      google_not_configured: "ورود با گوگل هنوز در سرور پیکربندی نشده است.",
      google_denied: "فرایند ورود با گوگل لغو شد.",
      google_state: "اعتبار درخواست ورود با گوگل تأیید نشد؛ دوباره تلاش کنید.",
      google_exchange: "تبادل امن کد ورود با گوگل ناموفق بود؛ تنظیمات callback را بررسی کنید.",
      google_profile: "پروفایل تأییدشده‌ای از گوگل دریافت نشد.",
      google_blocked: "این حساب کاربری غیرفعال است.",
      google_email_conflict: "این ایمیل به حساب دیگری متصل است؛ با روش قبلی وارد شوید.",
      google_failed: "ورود با گوگل کامل نشد؛ دوباره تلاش کنید.",
    };
    const dict = isEnglish() ? en : fa;
    return dict[code] || (isEnglish() ? "Google sign-in failed. Please try again." : "ورود با گوگل ناموفق بود؛ دوباره تلاش کنید.");
  }
  function cleanOAuthQuery() {
    params.delete("oauth");
    params.delete("auth_error");
    const query = params.toString();
    history.replaceState({}, document.title, location.pathname + (query ? `?${query}` : "") + location.hash);
  }

  // Google callback sets an HttpOnly cookie; verify that cookie by asking the API
  // before marking this browser as using cookie-backed auth and opening dashboard.
  if (oauthResult === "success") {
    try {
      await apiCallRaw("/api/auth/me", { method: "GET", auth: false, timeoutMs: 10000 });
      Auth.setCookieSession(true);
      cleanOAuthQuery();
      location.replace("/dashboard.html");
      return;
    } catch (_) {
      cleanOAuthQuery();
      showError(isEnglish() ? "Google sign-in returned, but the session could not be verified." : "از گوگل بازگشتید، اما نشست ورود تأیید نشد. دوباره تلاش کنید.");
    }
  } else if (oauthError) {
    cleanOAuthQuery();
    showError(oauthErrorMessage(oauthError));
  }

  // If an existing bearer or cookie-backed session is already present, preserve
  // the original fast redirect behaviour for both login and registration views.
  if (Auth.isLoggedIn()) {
    location.replace("/dashboard.html");
    return;
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      clearError();
      if (tab.dataset.tab === "login") {
        loginForm.style.display = "block";
        registerForm.style.display = "none";
        authTitle.textContent = "ورود به حساب";
        authSub.textContent = "برای ساخت و مدیریت ویجت‌هایت وارد شو";
      } else {
        loginForm.style.display = "none";
        registerForm.style.display = "block";
        authTitle.textContent = "ساخت حساب جدید";
        authSub.textContent = "چند ثانیه طول می‌کشد؛ همین حالا شروع کن";
      }
    });
  });

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearError();
    const submitBtn = loginForm.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    try {
      const data = await apiCall("/api/auth/login", {
        method: "POST",
        auth: false,
        body: {
          username: document.getElementById("loginUsername").value.trim(),
          password: document.getElementById("loginPassword").value,
        },
      });
      Auth.setToken(data.access_token);
      location.href = "/dashboard.html";
    } catch (err) {
      showError(err.message);
    } finally {
      submitBtn.disabled = false;
    }
  });

  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearError();
    const submitBtn = registerForm.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    try {
      const data = await apiCall("/api/auth/register", {
        method: "POST",
        auth: false,
        body: {
          username: document.getElementById("regUsername").value.trim(),
          password: document.getElementById("regPassword").value,
          org_name: document.getElementById("regOrgName").value.trim() || null,
        },
      });
      Auth.setToken(data.access_token);
      location.href = "/dashboard.html";
    } catch (err) {
      showError(err.message);
    } finally {
      submitBtn.disabled = false;
    }
  });

  if (googleButton) {
    googleButton.addEventListener("click", () => {
      clearError();
      googleButton.disabled = true;
      const label = googleButton.querySelector("span");
      if (label) label.textContent = isEnglish() ? "Redirecting to Google…" : "در حال انتقال به گوگل…";
      location.assign("/api/auth/google/start");
    });
  }
})();
