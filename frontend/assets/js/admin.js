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
  await loadStats();
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
    const badge = document.getElementById("unresolvedBadge");
    if (s.unresolved_flags > 0) {
      badge.style.display = "inline-flex";
      badge.textContent = s.unresolved_flags;
    } else {
      badge.style.display = "none";
    }
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
// نظارت امنیتی (Prompt Injection Watch)
// ---------------------------------------------------------------------------
let CURRENT_FLAG_FILTER = "unresolved";
document.querySelectorAll('#view-security .tab-btn').forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll('#view-security .tab-btn').forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    CURRENT_FLAG_FILTER = btn.dataset.resolved;
    loadFlags();
  });
});

async function loadFlags() {
  try {
    const qs = CURRENT_FLAG_FILTER === "unresolved" ? "?resolved=false" : "";
    const flags = await apiCall(`/api/admin/security/flags${qs}`);
    const box = document.getElementById("flagsList");
    if (flags.length === 0) {
      box.innerHTML = `<div class="empty-state"><div class="icon">🛡️</div><div class="title">موردی برای بررسی نیست</div></div>`;
      return;
    }
    box.innerHTML = flags
      .map(
        (f) => `
      <div class="flag-row ${f.resolved ? "resolved" : ""}">
        <div class="meta"><span>@${escapeHtml(f.owner_username)} · ${formatDate(f.created_at)}</span>${f.resolved ? '<span class="badge badge-success">بررسی‌شده</span>' : ""}</div>
        <div class="reason">${escapeHtml(f.flag_reason || "")}</div>
        <div>${escapeHtml(f.content)}</div>
        ${!f.resolved ? `<button class="btn btn-sm btn-soft" style="margin-top:10px;" onclick="resolveFlag(${f.id})">علامت‌گذاری به‌عنوان بررسی‌شده</button>` : ""}
      </div>`
      )
      .join("");
  } catch (err) {
    toastError(err);
  }
}

async function resolveFlag(id) {
  try {
    await apiCall(`/api/admin/security/flags/${id}/resolve`, { method: "POST" });
    toast("مورد به‌عنوان بررسی‌شده علامت‌گذاری شد.", "success");
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
function formatDate(iso) {
  try { return new Date(iso).toLocaleDateString("fa-IR"); } catch (_) { return iso; }
}

init();
