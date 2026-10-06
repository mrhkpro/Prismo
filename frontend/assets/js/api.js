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

async function apiCall(path, { method = "GET", body = null, auth = true, timeoutMs = 30000 } = {}) {
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
    const error = new Error(typeof message === "string" ? message : JSON.stringify(message));
    error.status = res.status;
    error.requestId = res.headers.get("X-Request-ID") || (data && data.request_id) || null;
    throw error;
  }
  return data;
}

// ---------------------------------------------------------------------------
// استریم (SSE روی fetch): meta → delta → done / error
// ---------------------------------------------------------------------------
// خطاهایی که یعنی «سرور استریم ندارد» و فراخوان می‌تواند به نسخه‌ی غیراستریم برگردد
const STREAM_FALLBACK_STATUSES = [404, 405, 415, 501];

async function apiStream(path, { body, onMeta, onDelta, signal, auth = true, idleTimeoutMs = 90000 } = {}) {
  const headers = { "Content-Type": "application/json", Accept: "text/event-stream" };
  if (auth) {
    const token = Auth.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  // اگر مدت زیادی هیچ تکه‌ای نیامد، اتصال را قطع می‌کنیم (پروکسی/مدل گیر کرده)
  const controller = new AbortController();
  if (signal) signal.addEventListener("abort", () => controller.abort(), { once: true });
  let idleTimer = null;
  const armIdle = () => {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => controller.abort(), idleTimeoutMs);
  };

  let res;
  try {
    armIdle();
    res = await fetch(path, { method: "POST", headers, body: JSON.stringify(body || {}), signal: controller.signal });
  } catch (err) {
    clearTimeout(idleTimer);
    if (err && err.name === "AbortError") {
      const e = new Error(signal && signal.aborted ? "متوقف شد." : "پاسخ سرور بیش از حد طول کشید.");
      e.aborted = Boolean(signal && signal.aborted);
      throw e;
    }
    throw new Error("ارتباط با سرور برقرار نشد.");
  }

  if (res.status === 401) {
    clearTimeout(idleTimer);
    Auth.clear();
    if (!location.pathname.endsWith("index.html") && location.pathname !== "/") location.href = "/index.html";
    throw new Error("نشست شما منقضی شده؛ دوباره وارد شوید.");
  }

  const contentType = res.headers.get("Content-Type") || "";
  if (!res.ok || !contentType.includes("text/event-stream") || !res.body) {
    clearTimeout(idleTimer);
    let data = null;
    try { data = await res.json(); } catch (_) { /* بدنه‌ی خالی */ }
    const detail = data && data.detail ? data.detail : `خطا (${res.status})`;
    const error = new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    error.status = res.ok ? 415 : res.status;
    error.requestId = res.headers.get("X-Request-ID") || (data && data.request_id) || null;
    throw error;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let gotDelta = false;
  let finished = false;

  const handleFrame = (frame) => {
    let event = "message";
    const dataLines = [];
    frame.split("\n").forEach((line) => {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).replace(/^ /, ""));
    });
    if (!dataLines.length) return;
    let data = {};
    try { data = JSON.parse(dataLines.join("\n")); } catch (_) { return; }
    if (event === "meta" && onMeta) onMeta(data);
    else if (event === "delta") { gotDelta = true; if (onDelta) onDelta(data.t || ""); }
    else if (event === "done") finished = true;
    else if (event === "error") {
      const e = new Error(data.message || "خطا در دریافت پاسخ.");
      e.partial = Boolean(data.partial);
      e.streamError = true;
      throw e;
    }
  };

  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      armIdle();
      buffer += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        handleFrame(frame);
      }
    }
    if (buffer.trim()) handleFrame(buffer);
  } catch (err) {
    if (err && err.name === "AbortError") {
      const e = new Error(signal && signal.aborted ? "متوقف شد." : "پاسخ سرور بیش از حد طول کشید.");
      e.aborted = Boolean(signal && signal.aborted);
      e.partial = gotDelta;
      throw e;
    }
    throw err;
  } finally {
    clearTimeout(idleTimer);
  }
  return { finished, gotDelta };
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
