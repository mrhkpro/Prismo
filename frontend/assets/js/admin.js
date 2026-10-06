// ============================================================================
// پنل مدیریت — فاز ۲: RBAC، داشبورد آمار، مدیریت کاربران، بازرسی، امنیت
// ============================================================================

if (!Auth.isLoggedIn()) location.href = "/index.html";

let ADMIN_USER = null;

const Nav = {
  go(viewName) {
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    document.querySelectorAll(".nav-item[data-view]").forEach((n) => n.classList.remove("active"));
    document.getElementById(`view-${viewName}`)?.classList.add("active");
    document.querySelector(`.nav-item[data-view="${viewName}"]`)?.classList.add("active");

    if (viewName === "stats") loadStats();
    if (viewName === "users") loadUsers();
    if (viewName === "conversations") loadConversations();
    if (viewName === "security") loadFlags();
  },
};
document.querySelectorAll(".nav-item[data-view]").forEach((item) => {
  item.addEventListener("click", () => Nav.go(item.dataset.view));
});
document.getElementById("backToDashboardBtn").addEventListener("click", () => (location.href = "/dashboard.html"));

async function init() {
  try {
    ADMIN_USER = await apiCall("/api/auth/me");
  } catch (err) {
    return;
  }
  if (ADMIN_USER.role !== "admin") {
    location.href = "/dashboard.html";
    return;
  }
  document.getElementById("sidebarUserName").textContent = ADMIN_USER.username;
  document.getElementById("avatarInitial").textContent = ADMIN_USER.username[0].toUpperCase();
  const topAvatar = document.getElementById("topbarAvatar");
  if (topAvatar) topAvatar.textContent = document.getElementById("avatarInitial").textContent;
  await loadStats();
  startSecurityWatch();
}

// ---------------------------------------------------------------------------
// آمار کلان
// ---------------------------------------------------------------------------
async function loadStats() {
  try {
    const s = await apiCall("/api/admin/stats");
    document.getElementById("statsGrid").innerHTML = `
      <div class="stat-card"><div class="label">کل کاربران</div><div class="value">${s.total_users}</div></div>
      <div class="stat-card"><div class="label">کاربران فعال</div><div class="value success">${s.active_users}</div></div>
      <div class="stat-card"><div class="label">کاربران مسدود</div><div class="value danger">${s.blocked_users}</div></div>
      <div class="stat-card"><div class="label">مدیران سیستم</div><div class="value gold">${s.admin_users}</div></div>
      <div class="stat-card"><div class="label">اسناد دانشنامه</div><div class="value accent">${s.total_documents}</div></div>
      <div class="stat-card"><div class="label">تکه‌های ایندکس‌شده</div><div class="value">${s.total_chunks}</div></div>
      <div class="stat-card"><div class="label">کل نشست‌های گفت‌وگو</div><div class="value">${s.total_sessions}</div></div>
      <div class="stat-card"><div class="label">کل پیام‌ها</div><div class="value">${s.total_messages}</div></div>
      <div class="stat-card"><div class="label">نشست‌های ویجت عمومی</div><div class="value accent">${s.widget_sessions}</div></div>
      <div class="stat-card"><div class="label">نشست‌های آزمایشگاه تست</div><div class="value">${s.playground_sessions}</div></div>
      <div class="stat-card"><div class="label">پیام‌های علامت‌گذاری‌شده</div><div class="value danger">${s.flagged_messages}</div></div>
      <div class="stat-card"><div class="label">مواردِ بررسی‌نشده</div><div class="value danger">${s.unresolved_flags}</div></div>
    `;
  } catch (err) {
    toastError(err);
  }
}

// ---------------------------------------------------------------------------
// مدیریت کاربران
// ---------------------------------------------------------------------------
async function loadUsers() {
  const search = document.getElementById("userSearchInput").value.trim();
  try {
    const users = await apiCall(`/api/admin/users${search ? `?search=${encodeURIComponent(search)}` : ""}`);
    document.getElementById("usersTableBody").innerHTML = users
      .map((u) => {
        const statusBadge = u.is_active
          ? `<span class="badge badge-success"><span class="badge-dot"></span>فعال</span>`
          : `<span class="badge badge-danger"><span class="badge-dot"></span>مسدود</span>`;
        const roleBadge = u.role === "admin"
          ? `<span class="badge badge-gold">ادمین</span>`
          : `<span class="badge badge-muted">کاربر</span>`;
        return `
        <tr>
          <td><div style="font-weight:600;">${escapeHtml(u.org_name || u.username)}</div><div class="cell-muted">@${escapeHtml(u.username)}</div></td>
          <td>${roleBadge}</td>
          <td>${statusBadge}</td>
          <td>${u.document_count}</td>
          <td>${u.session_count}</td>
          <td class="cell-muted">${formatDate(u.created_at)}</td>
          <td>
            <div style="display:flex; gap:6px;">
              <button class="icon-btn" title="بازرسی" onclick="inspectUser(${u.id})">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
              </button>
              <button class="icon-btn" title="${u.is_active ? "مسدودسازی" : "رفع مسدودیت"}" onclick="toggleBlock(${u.id}, ${u.is_active})">
                ${u.is_active
                  ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>`
                  : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 9.9-1"></path></svg>`}
              </button>
              <button class="icon-btn" title="ورود به‌جای کاربر" onclick="impersonate(${u.id})">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
              </button>
            </div>
          </td>
        </tr>`;
      })
      .join("");
  } catch (err) {
    toastError(err);
  }
}
document.getElementById("userSearchBtn").addEventListener("click", loadUsers);
document.getElementById("userSearchInput").addEventListener("keydown", (e) => { if (e.key === "Enter") loadUsers(); });

async function toggleBlock(userId, isCurrentlyActive) {
  const action = isCurrentlyActive ? "block" : "unblock";
  if (isCurrentlyActive && !confirm("این کاربر مسدود شود؟ دسترسی او به پنل و ویجتش بلافاصله قطع می‌شود.")) return;
  try {
    await apiCall(`/api/admin/users/${userId}/${action}`, { method: "POST" });
    toast(isCurrentlyActive ? "کاربر مسدود شد." : "مسدودیت کاربر رفع شد.", "success");
    loadUsers();
  } catch (err) {
    toastError(err);
  }
}

async function impersonate(userId) {
  if (!confirm("وارد حساب این کاربر شوی؟ می‌تونی بعداً به پنل ادمین برگردی.")) return;
  try {
    const res = await apiCall(`/api/admin/users/${userId}/impersonate`, { method: "POST" });
    Auth.stashAdminTokenAndSwitch(res.access_token);
    location.href = "/dashboard.html";
  } catch (err) {
    toastError(err);
  }
}

async function changeRole(userId, newRole) {
  try {
    await apiCall(`/api/admin/users/${userId}/role`, { method: "POST", body: { role: newRole } });
    toast("نقش کاربر تغییر کرد.", "success");
    loadUsers();
    document.getElementById("userModal").classList.remove("show");
  } catch (err) {
    toastError(err);
  }
}

async function inspectUser(userId) {
  try {
    const safe = (path, fallback) => apiCall(path).catch((e) => { toastError(e); return fallback; });
    const [detail, docs, sessions] = await Promise.all([
      apiCall(`/api/admin/users/${userId}`),
      safe(`/api/admin/users/${userId}/documents`, []),
      safe(`/api/admin/users/${userId}/sessions`, []),
    ]);

    document.getElementById("userModalTitle").textContent = `بازرسی: ${detail.org_name || detail.username}`;
    document.getElementById("userModalBody").innerHTML = `
      <div class="grid-2" style="margin-bottom:18px;">
        <div class="field"><label>نام کاربری</label><input type="text" value="@${escapeHtml(detail.username)}" disabled></div>
        <div class="field"><label>نقش فعلی</label><input type="text" value="${detail.role === "admin" ? "مدیر سیستم" : "کاربر عادی"}" disabled></div>
      </div>
      <div class="grid-2" style="margin-bottom:18px;">
        <div class="field"><label>ارائه‌دهنده‌ی مدل</label><input type="text" value="${detail.use_default_provider ? "مدل رایگان آماده" : "اتصال اختصاصی (" + (detail.api_key_set ? "کلید ثبت‌شده" : "بدون کلید") + ")"}" disabled></div>
        <div class="field"><label>مدل چت / امبدینگ</label><input type="text" value="${escapeHtml(detail.chat_model)} / ${escapeHtml(detail.embedding_model)}" disabled></div>
      </div>
      <div class="field"><label>پرامپت سیستمی اختصاصی کاربر</label><textarea disabled style="min-height:90px;">${escapeHtml(detail.system_prompt)}</textarea></div>

      <div class="divider"></div>
      <div class="panel-title" style="font-size:15px;">اسناد دانشنامه (${docs.length})</div>
      <div class="doc-list" style="margin-bottom:18px;">
        ${docs.length === 0
          ? `<div class="cell-muted">سندی ثبت نشده.</div>`
          : docs.map((d) => `<div class="doc-row"><div class="info"><div class="title">${escapeHtml(d.title)}</div><div class="meta">${d.chunk_count} تکه</div></div></div>`).join("")}
      </div>

      <div class="panel-title" style="font-size:15px;">نشست‌های گفت‌وگو (${sessions.length})</div>
      <div class="doc-list" style="margin-bottom:22px;">
        ${sessions.length === 0
          ? `<div class="cell-muted">نشستی ثبت نشده.</div>`
          : sessions.slice(0, 30).map((s) => `
            <div class="doc-row">
              <div class="info">
                <div class="title">${s.source === "widget" ? "ویجت عمومی" : "آزمایشگاه تست"} ${s.has_flag ? "🚩" : ""}</div>
                <div class="meta">${s.message_count} پیام · ${formatDate(s.created_at)}</div>
              </div>
              <button class="btn btn-sm btn-soft" onclick="viewSession('${s.id}')">مشاهده</button>
            </div>`).join("")}
      </div>

      <div style="display:flex; gap:10px; flex-wrap:wrap;">
        ${detail.role === "admin"
          ? `<button class="btn btn-soft" onclick="changeRole(${detail.id}, 'user')">تنزل به کاربر عادی</button>`
          : `<button class="btn btn-soft" onclick="changeRole(${detail.id}, 'admin')">ارتقا به ادمین</button>`}
        <button class="btn btn-ghost" onclick="impersonate(${detail.id})">ورود به‌جای این کاربر</button>
      </div>
    `;
    document.getElementById("userModal").classList.add("show");
  } catch (err) {
    toastError(err);
  }
}
document.getElementById("closeUserModalBtn").addEventListener("click", () => document.getElementById("userModal").classList.remove("show"));
document.getElementById("userModal").addEventListener("click", (e) => { if (e.target.id === "userModal") e.currentTarget.classList.remove("show"); });

// ---------------------------------------------------------------------------
// گزارش مکالمات
// ---------------------------------------------------------------------------
let CURRENT_CONV_SOURCE = "";
document.querySelectorAll('#view-conversations .tab-btn').forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll('#view-conversations .tab-btn').forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    CURRENT_CONV_SOURCE = btn.dataset.source;
    loadConversations();
  });
});

async function loadConversations() {
  try {
    const qs = CURRENT_CONV_SOURCE ? `?source=${CURRENT_CONV_SOURCE}` : "";
    const sessions = await apiCall(`/api/admin/conversations${qs}`);
    document.getElementById("conversationsTableBody").innerHTML = sessions.length
      ? sessions
          .map(
            (s) => `
        <tr>
          <td class="mono cell-muted">${s.id.slice(0, 8)}…</td>
          <td>${s.source === "widget" ? '<span class="badge badge-accent">ویجت</span>' : '<span class="badge badge-muted">آزمایشگاه</span>'}</td>
          <td class="cell-muted">${escapeHtml(s.visitor_label || "—")}</td>
          <td>${s.message_count} ${s.has_flag ? '<span class="badge badge-danger" style="margin-right:6px;">🚩 مشکوک</span>' : ""}</td>
          <td class="cell-muted">${formatDate(s.created_at)}</td>
          <td><button class="btn btn-sm btn-soft" onclick="viewSession('${s.id}')">مشاهده</button></td>
        </tr>`
          )
          .join("")
      : `<tr><td colspan="6"><div class="empty-state">هنوز مکالمه‌ای ثبت نشده.</div></td></tr>`;
  } catch (err) {
    toastError(err);
  }
}

async function viewSession(sessionId) {
  try {
    const messages = await apiCall(`/api/admin/sessions/${sessionId}/messages`);
    document.getElementById("sessionModalBody").innerHTML = messages
      .map(
        (m) => `
      <div class="chat-msg ${m.role === "user" ? "user" : "bot"}" style="${m.is_flagged ? "border:1px solid var(--danger);" : ""}">
        ${escapeHtml(m.content)}
        ${m.is_flagged ? `<div style="font-size:11px; margin-top:6px; opacity:0.85;">🚩 ${escapeHtml(m.flag_reason || "")}</div>` : ""}
      </div>`
      )
      .join("");
    document.getElementById("sessionModal").classList.add("show");
  } catch (err) {
    toastError(err);
  }
}
document.getElementById("closeSessionModalBtn").addEventListener("click", () => document.getElementById("sessionModal").classList.remove("show"));
document.getElementById("sessionModal").addEventListener("click", (e) => { if (e.target.id === "sessionModal") e.currentTarget.classList.remove("show"); });

// ---------------------------------------------------------------------------
// نظارت امنیتی: هشدار زنده، خلاصه، فهرست هشدارها
// ---------------------------------------------------------------------------
const SEVERITY_LABELS = { critical: "بحرانی", high: "بالا", medium: "متوسط" };
const SOURCE_LABELS = { widget: "ویجت عمومی", playground: "آزمایشگاه تست" };
const SEEN_KEY = "qz_sec_seen";
const DISMISS_KEY = "qz_sec_dismissed";
let SEC_SUMMARY = null;
let SEC_TIMER = null;

function seenId() { try { return Number(sessionStorage.getItem(SEEN_KEY) || 0); } catch (_) { return 0; } }
function setSeenId(id) { try { sessionStorage.setItem(SEEN_KEY, String(id)); } catch (_) { /* noop */ } }
function dismissedId() { try { return Number(sessionStorage.getItem(DISMISS_KEY) || 0); } catch (_) { return 0; } }

function renderSecurityBadge(summary) {
  const badge = document.getElementById("unresolvedBadge");
  if (!badge) return;
  if (summary.unresolved_total > 0) {
    badge.style.display = "inline-flex";
    badge.textContent = summary.unresolved_total;
    badge.classList.toggle("pulse", summary.critical > 0);
  } else {
    badge.style.display = "none";
  }
}

function renderSecurityBanner(summary) {
  const banner = document.getElementById("securityBanner");
  if (!banner) return;
  const latest = summary.latest;
  const onSecurityPage = document.getElementById("view-security").classList.contains("active");
  // بنر فقط برای موارد بحرانی؛ اگر ادمین همین مورد را بسته یا صفحه‌ی امنیت باز است، نمایش داده نمی‌شود
  if (summary.critical === 0 || !latest || onSecurityPage || dismissedId() >= latest.id) {
    banner.hidden = true;
    return;
  }
  const who = `@${escapeHtml(latest.owner_username)}${latest.source ? ` · ${escapeHtml(SOURCE_LABELS[latest.source] || latest.source)}` : ""}`;
  banner.innerHTML = `
    <span class="security-banner-icon">⚠</span>
    <div class="security-banner-text">
      <strong>${summary.critical} هشدار بحرانی بررسی‌نشده</strong>
      <span>آخرین: ${escapeHtml(latest.label)} — ${who}</span>
    </div>
    <div class="security-banner-actions">
      <button class="btn btn-sm btn-danger" id="bannerOpenBtn">بررسی</button>
      <button class="icon-btn" id="bannerCloseBtn" aria-label="بستن">✕</button>
    </div>`;
  banner.hidden = false;
  document.getElementById("bannerOpenBtn").addEventListener("click", () => Nav.go("security"));
  document.getElementById("bannerCloseBtn").addEventListener("click", () => {
    try { sessionStorage.setItem(DISMISS_KEY, String(latest.id)); } catch (_) { /* noop */ }
    banner.hidden = true;
  });
}

async function refreshSecuritySummary(options = {}) {
  try {
    const summary = await apiCall("/api/admin/security/summary");
    const previous = SEC_SUMMARY;
    SEC_SUMMARY = summary;
    renderSecurityBadge(summary);
    renderSecurityBanner(summary);
    renderSecurityTiles(summary);
    // اعلان زنده: فقط وقتی هشدار بحرانیِ تازه‌ای نسبت به آخرین دیده‌شده آمده و کاربر در صفحه‌ی امنیت نیست
    const latest = summary.latest;
    if (!options.silent && previous && latest && latest.severity === "critical" && latest.id > seenId()
        && !document.getElementById("view-security").classList.contains("active")) {
      toast(`⚠ ${latest.label} — @${latest.owner_username}`, "error");
    }
    if (latest && document.getElementById("view-security").classList.contains("active")) setSeenId(latest.id);
    return summary;
  } catch (_) {
    return null; // خطای لحظه‌ای شبکه نباید مزاحم ادمین شود
  }
}

function startSecurityWatch() {
  refreshSecuritySummary({ silent: true });
  if (SEC_TIMER) return;
  SEC_TIMER = setInterval(() => { if (!document.hidden) refreshSecuritySummary(); }, 30000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) refreshSecuritySummary(); });
}

function renderSecurityTiles(summary) {
  const box = document.getElementById("securityTiles");
  if (!box) return;
  box.innerHTML = `
    <div class="stat-card"><div class="label">هشدار بحرانی</div><div class="value danger">${summary.critical}</div></div>
    <div class="stat-card"><div class="label">هشدار با شدت بالا</div><div class="value gold">${summary.high}</div></div>
    <div class="stat-card"><div class="label">شدت متوسط</div><div class="value">${summary.medium}</div></div>
    <div class="stat-card"><div class="label">تلاش برای گرفتن سیستم‌پرامپت</div><div class="value accent">${summary.prompt_extraction}</div></div>`;
}

let CURRENT_FLAG_FILTER = "unresolved";
let CURRENT_SEVERITY = "";
document.querySelectorAll("#view-security .tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#view-security .tab-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    CURRENT_FLAG_FILTER = btn.dataset.resolved;
    loadFlags();
  });
});
document.querySelectorAll("#severityFilter .seg-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#severityFilter .seg-btn").forEach((b) => b.classList.toggle("active", b === btn));
    CURRENT_SEVERITY = btn.dataset.severity;
    loadFlags();
  });
});

function flagCardHtml(f) {
  const who = `@${escapeHtml(f.owner_username)}${f.owner_org_name ? ` (${escapeHtml(f.owner_org_name)})` : ""}`;
  const where = SOURCE_LABELS[f.source] || f.source || "";
  const visitor = f.visitor_label ? ` · بازدیدکننده ${escapeHtml(f.visitor_label)}` : "";
  const codes = (f.codes || []).map((c) => `<span class="code-chip">${escapeHtml(c)}</span>`).join("");
  return `
    <article class="alert-card sev-${f.severity} ${f.resolved ? "resolved" : ""}" data-flag-id="${f.id}">
      <header class="alert-head">
        <span class="sev-badge sev-${f.severity}">${SEVERITY_LABELS[f.severity] || f.severity}</span>
        <strong class="alert-title">${escapeHtml(f.label)}</strong>
        <span class="alert-time">${formatDateTime(f.created_at)}</span>
      </header>
      <div class="alert-who">
        <span>کاربر: <b>${who}</b></span>
        ${where ? `<span>منبع: <b>${escapeHtml(where)}</b>${visitor}</span>` : ""}
        ${f.owner_is_active === false ? '<span class="badge badge-danger">مسدود</span>' : ""}
        ${f.resolved ? '<span class="badge badge-success">بررسی‌شده</span>' : ""}
      </div>
      <blockquote class="alert-quote">${escapeHtml(f.content)}</blockquote>
      <div class="alert-codes">${codes}</div>
      <div class="alert-actions">
        <button class="btn btn-sm btn-soft" data-act="view" data-session="${escapeHtml(f.session_id)}">مشاهده‌ی گفت‌وگو</button>
        ${f.owner_is_active !== false ? `<button class="btn btn-sm btn-danger" data-act="block" data-user="${f.owner_id}">مسدودکردن کاربر</button>` : ""}
        ${!f.resolved ? `<button class="btn btn-sm btn-ghost" data-act="resolve" data-id="${f.id}">بررسی شد</button>` : ""}
      </div>
    </article>`;
}

function skeletonCards(n) {
  return Array.from({ length: n }, () => `<div class="skeleton skel-row" style="height:150px;margin-bottom:12px;"></div>`).join("");
}

async function loadFlags() {
  const box = document.getElementById("flagsList");
  box.innerHTML = skeletonCards(3);
  try {
    const params = new URLSearchParams();
    if (CURRENT_FLAG_FILTER === "unresolved") params.set("resolved", "false");
    if (CURRENT_SEVERITY) params.set("severity", CURRENT_SEVERITY);
    const qs = params.toString() ? `?${params}` : "";
    const [flags] = await Promise.all([apiCall(`/api/admin/security/flags${qs}`), refreshSecuritySummary({ silent: true })]);
    if (flags.length === 0) {
      box.innerHTML = `<div class="empty-state"><div class="icon">🛡️</div><div class="title">موردی برای بررسی نیست</div></div>`;
      return;
    }
    box.innerHTML = flags.map(flagCardHtml).join("");
  } catch (err) {
    box.innerHTML = "";
    toastError(err);
  }
}

// یک شنونده‌ی واحد برای دکمه‌های کارت‌ها (رویدادِ مفوض) — بدون onclick درون‌خطی
document.getElementById("flagsList").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-act]");
  if (!btn) return;
  if (btn.dataset.act === "view") viewSession(btn.dataset.session);
  else if (btn.dataset.act === "resolve") resolveFlag(Number(btn.dataset.id));
  else if (btn.dataset.act === "block") blockFlaggedUser(Number(btn.dataset.user));
});

async function resolveFlag(id) {
  try {
    await apiCall(`/api/admin/security/flags/${id}/resolve`, { method: "POST" });
    toast("مورد به‌عنوان بررسی‌شده علامت‌گذاری شد.", "success");
    loadFlags();
  } catch (err) {
    toastError(err);
  }
}

async function blockFlaggedUser(userId) {
  if (!confirm("این کاربر مسدود شود؟ دسترسی او به پنل و ویجتش بلافاصله قطع می‌شود.")) return;
  try {
    await apiCall(`/api/admin/users/${userId}/block`, { method: "POST" });
    toast("کاربر مسدود شد.", "success");
    loadFlags();
  } catch (err) {
    toastError(err);
  }
}

// ---------------------------------------------------------------------------
// ابزارهای کمکی
// ---------------------------------------------------------------------------
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}
function formatDateTime(iso) {
  try { return new Date(iso).toLocaleString("fa-IR", { dateStyle: "short", timeStyle: "short" }); } catch (_) { return iso; }
}
function formatDate(iso) {
  try { return new Date(iso).toLocaleDateString("fa-IR"); } catch (_) { return iso; }
}

init();
