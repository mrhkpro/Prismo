(function () {
  const tabs = document.querySelectorAll(".auth-tab");
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");
  const authTitle = document.getElementById("authTitle");
  const authSub = document.getElementById("authSub");
  const errorBox = document.getElementById("authError");

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.classList.add("show");
  }
  function clearError() {
    errorBox.classList.remove("show");
    errorBox.textContent = "";
  }

  // Keep login/register fast: a stored bearer token redirects without extra requests.
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

  const googleLoginBtn = document.getElementById("googleLoginBtn");
  if (googleLoginBtn) {
    function base64Url(bytes) {
      let binary = "";
      bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
      return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
    }

    async function createPkcePair() {
      if (!window.crypto || !crypto.getRandomValues || !crypto.subtle) {
        throw new Error("مرورگر برای ورود امن گوگل آماده نیست؛ لطفاً از مرورگر به‌روز و HTTPS استفاده کنید.");
      }
      const random = new Uint8Array(48);
      crypto.getRandomValues(random);
      const verifier = base64Url(random);
      const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
      return { verifier, challenge: base64Url(new Uint8Array(digest)) };
    }

    function googleRedirectUri() {
      const host = window.location.hostname.toLowerCase();
      const localHost = host === "localhost" || host === "127.0.0.1" || host === "::1";
      // Hosted Vercel OAuth always returns to the canonical production site.
      // A Vercel preview must not fall back to localhost when it is not in the Supabase allow-list.
      const hostedOrigin = host === "rag-widget-beta.vercel.app"
        ? window.location.origin
        : (host.endsWith(".vercel.app") ? "https://rag-widget-beta.vercel.app" : window.location.origin);
      const origin = localHost ? window.location.origin : hostedOrigin;
      return `${origin.replace(/\/$/, "")}/auth-callback.html`;
    }

    googleLoginBtn.addEventListener("click", async () => {
      clearError();
      const wasDisabled = googleLoginBtn.disabled;
      googleLoginBtn.disabled = true;
      try {
        const supabaseUrl = (window.PRISMO_SUPABASE_URL || "https://zvscwdqipjdoyauwkmpa.supabase.co").replace(/\/$/, "");
        const redirectUri = googleRedirectUri();
        const { verifier, challenge } = await createPkcePair();
        // The verifier is browser-session-only and never appears in the URL or request logs.
        sessionStorage.setItem("prismo_google_pkce_verifier", verifier);
        sessionStorage.setItem("prismo_google_pkce_redirect_uri", redirectUri);
        sessionStorage.setItem("prismo_google_pkce_started_at", String(Date.now()));

        const params = new URLSearchParams({
          provider: "google",
          redirect_to: redirectUri,
          code_challenge: challenge,
          code_challenge_method: "s256",
        });
        location.assign(`${supabaseUrl}/auth/v1/authorize?${params.toString()}`);
      } catch (err) {
        showError(err.message || "شروع ورود گوگل ناموفق بود.");
        googleLoginBtn.disabled = wasDisabled;
      }
    });
  }

})();
