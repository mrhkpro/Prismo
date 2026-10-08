(function () {
  "use strict";

  const STORAGE_KEY = "qz_theme";
  const root = document.documentElement;
  const THEMES = ["light", "dark", "ocean", "forest", "sunset", "lavender", "mono"];

  function getInitialTheme() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return THEMES.includes(saved) ? saved : "dark";
    } catch (_) {
      return "dark";
    }
  }

  function setTheme(theme, persist) {
    const next = THEMES.includes(theme) ? theme : "dark";
    root.dataset.theme = next;
    document.dispatchEvent(new CustomEvent("qz-theme-change", { detail: { theme: next } }));
    if (persist) {
      try { localStorage.setItem(STORAGE_KEY, next); } catch (_) {}
    }
    const btn = document.getElementById("themeToggle");
    if (!btn) return;
    const isLight = next === "light";
    btn.innerHTML = isLight
      ? '<span aria-hidden="true">☾</span><span>حالت تیره</span>'
      : '<span aria-hidden="true">☼</span><span>حالت روشن</span>';
    btn.setAttribute("aria-label", isLight ? "فعال‌کردن حالت تیره" : "فعال‌کردن حالت روشن");
    btn.title = btn.getAttribute("aria-label");
  }

  window.QZTheme = { set: setTheme, get: () => root.dataset.theme || getInitialTheme(), themes: THEMES.slice() };

  function ensureToggle() {
    // داشبورد 2.7 مدیریت تم را به «تنظیمات» منتقل کرده و نباید دکمه‌ی شناور بسازد.
    if (document.body && document.body.hasAttribute("data-theme-settings-center")) return;
    let btn = document.getElementById("themeToggle");
    if (!btn) {
      btn = document.createElement("button");
      btn.id = "themeToggle";
      btn.type = "button";
      btn.className = "theme-toggle";
      document.body.appendChild(btn);
    }
    btn.addEventListener("click", function () {
      setTheme(root.dataset.theme === "light" ? "dark" : "light", true);
    });
    setTheme(root.dataset.theme || getInitialTheme(), false);
  }

  root.dataset.theme = getInitialTheme();
  if (document.body) ensureToggle();
  else document.addEventListener("DOMContentLoaded", ensureToggle, { once: true });
})();
