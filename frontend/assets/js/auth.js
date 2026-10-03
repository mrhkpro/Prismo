(function () {
  // اگر از قبل وارد شده، مستقیم برو داشبورد
  if (Auth.isLoggedIn()) {
    location.href = "/dashboard.html";
    return;
  }

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
})();
