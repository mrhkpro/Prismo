(function () {
  "use strict";

  const KEY = "qz_database_mode";
  const labels = { supabase: "Supabase", local: "کاملاً محلی" };

  function current() {
    try { return localStorage.getItem(KEY); } catch (_) { return null; }
  }

  function save(mode) {
    if (!["supabase", "local"].includes(mode)) return;
    try { localStorage.setItem(KEY, mode); } catch (_) {}
    document.documentElement.dataset.databaseMode = mode;
    window.dispatchEvent(new CustomEvent("qz-database-mode-change", { detail: { mode } }));
  }

  function ensureStyle() {
    if (document.getElementById("qzDatabaseModeStyle")) return;
    const style = document.createElement("style");
    style.id = "qzDatabaseModeStyle";
    style.textContent = `
      .qz-db-overlay{position:fixed;inset:0;z-index:99999;display:grid;place-items:center;padding:20px;background:rgba(15,22,35,.72);backdrop-filter:blur(8px);font-family:Vazirmatn,Tahoma,sans-serif;direction:rtl}
      .qz-db-box{width:min(680px,100%);background:#fff;border:1px solid #e6e7eb;border-radius:8px;box-shadow:0 28px 80px rgba(15,22,35,.25);padding:28px;color:#1e2633}
      .qz-db-title{font-size:21px;font-weight:800;margin:0 0 8px}.qz-db-sub{color:#626d7d;line-height:1.8;margin:0 0 20px}
      .qz-db-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.qz-db-card{appearance:none;text-align:right;border:1px solid #e6e7eb;background:#f9fafb;border-radius:6px;padding:18px;cursor:pointer;transition:.16s}.qz-db-card:hover{border-color:#1ABB9C;transform:translateY(-1px);box-shadow:0 7px 20px rgba(26,187,156,.12)}.qz-db-card.active{border-color:#1ABB9C;box-shadow:0 0 0 3px rgba(26,187,156,.12);background:#fff}.qz-db-card[disabled]{opacity:.45;cursor:not-allowed;transform:none;box-shadow:none}.qz-db-card strong{display:block;font-size:15px;margin-bottom:6px}.qz-db-card small{display:block;color:#7e8896;line-height:1.8}.qz-db-foot{margin-top:18px;font-size:12px;color:#7e8896}
      @media(max-width:640px){.qz-db-grid{grid-template-columns:1fr}.qz-db-box{padding:20px}}
    `;
    document.head.appendChild(style);
  }

  async function fetchRuntime() {
    try {
      const res = await fetch("/api/runtime", { headers: { Accept: "application/json" } });
      if (!res.ok) return null;
      return await res.json();
    } catch (_) { return null; }
  }

  async function ready() {
    const runtime = await fetchRuntime();
    const forced = runtime && runtime.database_mode ? runtime.database_mode : "auto";
    const stored = current();
    let mode = stored || (runtime && runtime.database ? runtime.database : null) || "local";

    if (forced !== "auto") mode = forced === "supabase" ? "supabase" : "local";
    save(mode);

    // اولین ورود انتخاب می‌گیرد؛ بعد از آن همان profile حفظ می‌شود.
    if (stored || forced !== "auto") return mode;

    ensureStyle();
    const overlay = document.createElement("div");
    overlay.className = "qz-db-overlay";
    overlay.innerHTML = `
      <div class="qz-db-box" role="dialog" aria-modal="true" aria-labelledby="qzDbTitle">
        <h2 class="qz-db-title" id="qzDbTitle">داده‌ها را کجا نگه داریم؟</h2>
        <p class="qz-db-sub">برای این اجرا انتخاب کن از Supabase استفاده شود یا همه‌چیز کاملاً روی همین سیستم بماند.</p>
        <div class="qz-db-grid">
          <button class="qz-db-card" data-mode="supabase" type="button"><strong>Supabase</strong><small>برای استقرارهای Vercel و دیتابیس PostgreSQL مناسب است.</small></button>
          <button class="qz-db-card" data-mode="local" type="button"><strong>کاملاً محلی</strong><small>SQLite داخلی و سریع، بدون نیاز به Supabase.</small></button>
        </div>
        <div class="qz-db-foot">این انتخاب روی همین مرورگر ذخیره می‌شود.</div>
      </div>`;
    document.body.appendChild(overlay);
    return new Promise((resolve) => {
      overlay.querySelectorAll(".qz-db-card").forEach((card) => {
        card.addEventListener("click", () => {
          const selected = card.dataset.mode;
          save(selected);
          overlay.remove();
          resolve(selected);
        });
      });
    });
  }

  window.QzDatabaseMode = { current, save, ready, label: (mode) => labels[mode] || mode };
})();
