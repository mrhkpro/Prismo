(function () {
  "use strict";

  const STORAGE_KEY = "qz_theme";
  const root = document.documentElement;

  function getInitialTheme() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved === "light" || saved === "dark" ? saved : "dark";
    } catch (_) {
      return "dark";
    }
  }

  function setTheme(theme, persist) {
    const next = theme === "light" ? "light" : "dark";
    root.dataset.theme = next;
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

  function ensureToggle() {
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
