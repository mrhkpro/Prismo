(function () {
  "use strict";

  const STORAGE_KEY = "qz_theme";
  const root = document.documentElement;
  const THEMES = ["light", "dark", "ocean", "forest", "sunset", "lavender", "mono", "nord", "amber", "rose"];

  function isAdminDarkOnly() {
    return Boolean(document.body && document.body.hasAttribute("data-admin-dark-only"));
  }

  function getInitialTheme() {
    if (isAdminDarkOnly()) return "dark";
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return THEMES.includes(saved) ? saved : "dark";
    } catch (_) {
      return "dark";
    }
  }

  function setTheme(theme, persist) {
    const next = isAdminDarkOnly() ? "dark" : (THEMES.includes(theme) ? theme : "dark");
    root.dataset.theme = next;
    if (persist) {
      try { localStorage.setItem(STORAGE_KEY, next); } catch (_) {}
    }
    document.dispatchEvent(new CustomEvent("qz-theme-change", { detail: { theme: next } }));
    const btn = document.getElementById("themeToggle");
    if (!btn) return;
    const isLight = next === "light";
    btn.innerHTML = isLight
      ? '<span aria-hidden="true">☾</span><span>حالت تیره</span>'
      : '<span aria-hidden="true">☼</span><span>حالت روشن</span>';
    btn.setAttribute("aria-label", isLight ? "فعال‌کردن حالت تیره" : "فعال‌کردن حالت روشن");
    btn.title = btn.getAttribute("aria-label");
  }

  window.QZTheme = {
    set: setTheme,
    get: () => THEMES.includes(root.dataset.theme) ? root.dataset.theme : getInitialTheme(),
    themes: THEMES.slice(),
  };

  document.addEventListener("qz-theme-change", function (event) {
    const activeTheme = event && event.detail && THEMES.includes(event.detail.theme) ? event.detail.theme : getInitialTheme();
    document.querySelectorAll("[data-theme-preset]").forEach(function (el) {
      const active = el.dataset.themePreset === activeTheme;
      el.classList.toggle("active", active);
      el.setAttribute("aria-pressed", active ? "true" : "false");
    });
  });

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
