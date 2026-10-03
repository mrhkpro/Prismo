// لایه‌ی کمکی مشترک برای تماس با API + نوتیفیکیشن‌های toast
// در همه‌ی صفحات (index / dashboard / admin) استفاده می‌شود.

const TOKEN_KEY = "rag_saas_token";
const IMPERSONATE_STASH_KEY = "rag_saas_admin_token_stash";

const Auth = {
  getToken() { return localStorage.getItem(TOKEN_KEY); },
  setToken(t) { localStorage.setItem(TOKEN_KEY, t); },
  clear() { localStorage.removeItem(TOKEN_KEY); },
  isLoggedIn() { return !!localStorage.getItem(TOKEN_KEY); },

  // برای حالت «ورود به‌جای کاربر»: توکن فعلیِ ادمین را کنار می‌گذاریم تا بتوانیم برگردیم
  stashAdminTokenAndSwitch(newToken) {
    localStorage.setItem(IMPERSONATE_STASH_KEY, this.getToken());
    this.setToken(newToken);
  },
  hasStashedAdmin() { return !!localStorage.getItem(IMPERSONATE_STASH_KEY); },
  restoreAdminToken() {
    const stashed = localStorage.getItem(IMPERSONATE_STASH_KEY);
    if (stashed) {
      this.setToken(stashed);
      localStorage.removeItem(IMPERSONATE_STASH_KEY);
    }
  },
};

async function apiCall(path, { method = "GET", body = null, auth = true, timeoutMs = 25000 } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = Auth.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let res;
  const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
  const timeoutId = controller ? setTimeout(() => controller.abort(), timeoutMs) : null;
  try {
    res = await fetch(path, {
      method,
      headers,
      body: body !== null ? JSON.stringify(body) : undefined,
      signal: controller ? controller.signal : undefined,
    });
  } catch (networkErr) {
    if (networkErr && networkErr.name === "AbortError") {
      throw new Error("پاسخ سرور بیش از حد طول کشید. دوباره تلاش کنید.");
    }
    throw new Error("ارتباط با سرور برقرار نشد. مطمئن شوید بک‌اند در حال اجراست.");
  } finally {
    if (timeoutId) clearTimeout(timeoutId);
  }

  if (res.status === 401) {
    Auth.clear();
    if (!location.pathname.endsWith("index.html") && location.pathname !== "/") {
      location.href = "/index.html";
    }
    throw new Error("نشست شما منقضی شده؛ دوباره وارد شوید.");
  }

  if (res.status === 204) return null;

  let data = null;
  try { data = await res.json(); } catch (_) { /* بدنه‌ی خالی */ }

  if (!res.ok) {
    const message = (data && data.detail) ? data.detail : `خطا (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------
function ensureToastHost() {
  let host = document.querySelector(".toast-host");
  if (!host) {
    host = document.createElement("div");
    host.className = "toast-host";
    host.setAttribute("aria-live", "polite");
    host.setAttribute("aria-atomic", "true");
    document.body.appendChild(host);
  }
  return host;
}

function toast(message, type = "default") {
  const host = ensureToastHost();
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  host.appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

function toastError(err) {
  toast(err && err.message ? err.message : String(err), "error");
}
