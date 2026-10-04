// ============================================================================
// داشبورد اصلی — منطق ناوبری + همه‌ی بخش‌های فاز ۱
// ============================================================================

if (!Auth.isLoggedIn()) location.href = "/index.html";

let CURRENT_USER = null;
let CURRENT_SETTINGS = null;
let CHAT_SESSION_ID = null;

// ---------------------------------------------------------------------------
// ناوبری بین بخش‌ها
// ---------------------------------------------------------------------------
const Nav = {
  go(viewName) {
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    document.querySelectorAll(".nav-item[data-view]").forEach((n) => n.classList.remove("active"));

    const view = document.getElementById(`view-${viewName}`);
    if (view) view.classList.add("active");
    const navItem = document.querySelector(`.nav-item[data-view="${viewName}"]`);
    if (navItem) navItem.classList.add("active");

    if (viewName === "overview") loadOverview();
    if (viewName === "ai-settings") loadProviderSettings();
    if (viewName === "knowledge") loadDocuments();
    if (viewName === "rag-prompt") loadRagPromptSettings();
    if (viewName === "widget") loadWidgetSection();
  },
};

document.querySelectorAll(".nav-item[data-view]").forEach((item) => {
  item.addEventListener("click", () => Nav.go(item.dataset.view));
});

// ---------------------------------------------------------------------------
// راه‌اندازی اولیه
// ---------------------------------------------------------------------------
async function init() {
  try {
    CURRENT_USER = await apiCall("/api/auth/me");
  } catch (err) {
    return; // apiCall خودش در صورت 401 ریدایرکت می‌کند
  }

  document.getElementById("sidebarUserName").textContent = CURRENT_USER.org_name || CURRENT_USER.username;
  document.getElementById("sidebarUserRole").textContent = CURRENT_USER.role === "admin" ? "مدیر سیستم" : "کاربر";
  document.getElementById("avatarInitial").textContent = (CURRENT_USER.org_name || CURRENT_USER.username)[0].toUpperCase();

  document.getElementById("accUsername").value = CURRENT_USER.username;
  document.getElementById("accOrgName").value = CURRENT_USER.org_name || "—";
  document.getElementById("accRole").value = CURRENT_USER.role === "admin" ? "مدیر سیستم" : "کاربر عادی";

  if (CURRENT_USER.role === "admin") {
    document.getElementById("adminNavGroup").style.display = "block";
  }

  if (CURRENT_USER.impersonated_by || Auth.hasStashedAdmin()) {
    const banner = document.getElementById("impersonationBanner");
    banner.style.display = "flex";
    document.getElementById("impersonationText").textContent =
      `⚠️ شما در حالت جانمایی، به‌جای کاربر «${CURRENT_USER.username}» وارد شده‌اید.`;
  }

  await loadOverview();
}

document.getElementById("goToAdminBtn").addEventListener("click", () => (location.href = "/admin.html"));
document.getElementById("exitImpersonationBtn").addEventListener("click", () => {
  Auth.restoreAdminToken();
  location.href = "/admin.html";
});
document.getElementById("logoutBtn").addEventListener("click", () => {
  Auth.clear();
  localStorage.removeItem("rag_saas_admin_token_stash");
  location.href = "/index.html";
});

// ---------------------------------------------------------------------------
// خانه / نمای کلی
// ---------------------------------------------------------------------------
async function loadOverview() {
  try {
    const [summary, settings] = await Promise.all([
      apiCall("/api/dashboard/summary"),
      apiCall("/api/settings"),
    ]);
    document.getElementById("ovDocCount").textContent = summary.document_count;
    document.getElementById("ovChunkCount").textContent = summary.chunk_count;
    document.getElementById("ovMessageCount").textContent = summary.message_count;
    document.getElementById("ovPlaygroundSessions").textContent = summary.playground_session_count;
    document.getElementById("ovWidgetSessions").textContent = summary.widget_session_count;
    document.getElementById("ovProvider").textContent = summary.provider_label;
    const widgetStatus = document.getElementById("ovWidgetStatus");
    widgetStatus.className = summary.widget_online ? "badge badge-success" : "badge badge-muted";
    widgetStatus.innerHTML = summary.widget_online
      ? '<span class="badge-dot"></span> فعال'
      : 'غیرفعال';
    CURRENT_SETTINGS = settings;
  } catch (err) {
    toastError(err);
  }
}

// ---------------------------------------------------------------------------
// اتصال مدل هوش مصنوعی
// ---------------------------------------------------------------------------
let DISCOVERED_CUSTOM_MODELS = [];

function fillModelSelect(selectEl, models, selected) {
  selectEl.innerHTML = "";
  (models || []).forEach((m) => {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    if (m === selected) opt.selected = true;
    selectEl.appendChild(opt);
  });
  selectEl.disabled = !(models && models.length);
}

function setProviderMode(useDefault) {
  const checkbox = document.getElementById("useDefaultProviderChk");
  checkbox.checked = useDefault;

  document.getElementById("defaultProviderInfo").style.display = useDefault ? "block" : "none";
  document.getElementById("customProviderPanel").style.display = useDefault ? "none" : "block";
  document.getElementById("defaultProviderModeBtn").classList.toggle("active", useDefault);
  document.getElementById("customProviderModeBtn").classList.toggle("active", !useDefault);

  const badge = document.getElementById("providerStatusBadge");
  badge.textContent = useDefault ? "مدل‌های آماده" : "API اختصاصی";
  badge.className = `badge ${useDefault ? "badge-success" : "badge-accent"}`;
}

document.getElementById("defaultProviderModeBtn").addEventListener("click", () => setProviderMode(true));
document.getElementById("customProviderModeBtn").addEventListener("click", () => setProviderMode(false));

document.getElementById("discoverModelsBtn").addEventListener("click", async () => {
  const btn = document.getElementById("discoverModelsBtn");
  const status = document.getElementById("modelDiscoveryStatus");
  const baseUrl = document.getElementById("baseUrlInput").value.trim();
  const apiKey = document.getElementById("apiKeyInput").value.trim();
  const savedKey = Boolean(CURRENT_SETTINGS && CURRENT_SETTINGS.api_key_set);

  if (!baseUrl) return toast("Base URL را وارد کن.", "error");
  if (!apiKey && !savedKey) return toast("API Key را وارد کن.", "error");

  btn.disabled = true;
  btn.textContent = "در حال دریافت…";
  status.textContent = "در حال خواندن /models سرویس…";
  try {
    const result = await apiCall("/api/settings/discover-models", {
      method: "POST",
      body: { base_url: baseUrl, ...(apiKey ? { api_key: apiKey } : {}) },
    });
    DISCOVERED_CUSTOM_MODELS = result.models || [];
    const currentChat = document.getElementById("customChatModelSelect").value;
    const currentEmbedding = document.getElementById("customEmbeddingModelSelect").value;
    fillModelSelect(document.getElementById("customChatModelSelect"), DISCOVERED_CUSTOM_MODELS, currentChat);
    fillModelSelect(document.getElementById("customEmbeddingModelSelect"), DISCOVERED_CUSTOM_MODELS, currentEmbedding);
    status.textContent = `${DISCOVERED_CUSTOM_MODELS.length} مدل پیدا شد.`;
    status.className = "field-hint discovery-status success-text";
    toast("لیست مدل‌ها دریافت شد.", "success");
  } catch (err) {
    DISCOVERED_CUSTOM_MODELS = [];
    fillModelSelect(document.getElementById("customChatModelSelect"), [], "");
    fillModelSelect(document.getElementById("customEmbeddingModelSelect"), [], "");
    status.textContent = err.message;
    status.className = "field-hint discovery-status error-text";
  } finally {
    btn.disabled = false;
    btn.textContent = "دریافت مدل‌ها";
  }
});

async function loadProviderSettings() {
  try {
    const s = await apiCall("/api/settings");
    CURRENT_SETTINGS = s;

    document.getElementById("baseUrlInput").value = s.base_url || "";
    const apiInput = document.getElementById("apiKeyInput");
    apiInput.value = "";
    apiInput.placeholder = s.api_key_set
      ? "•••••••• (کلید ذخیره شده — برای تغییر دوباره وارد کن)"
      : "sk-...";
    document.getElementById("apiKeyStatusHint").textContent = s.api_key_set
      ? "کلید ذخیره شده است؛ برای امنیت نمایش داده نمی‌شود."
      : "کلیدی ذخیره نشده است.";

    fillModelSelect(document.getElementById("chatModelSelect"), s.default_chat_models, s.chat_model);
    fillModelSelect(document.getElementById("embeddingModelSelect"), s.default_embedding_models, s.embedding_model);
    fillModelSelect(document.getElementById("battleModelA"), s.default_chat_models, s.default_chat_models[0]);
    fillModelSelect(document.getElementById("battleModelB"), s.default_chat_models, s.default_chat_models[1] || s.default_chat_models[0]);

    const isDefault = s.use_default_provider;
    setProviderMode(isDefault);

    DISCOVERED_CUSTOM_MODELS = [];
    fillModelSelect(document.getElementById("customChatModelSelect"), [], s.chat_model);
    fillModelSelect(document.getElementById("customEmbeddingModelSelect"), [], s.embedding_model);
    document.getElementById("modelDiscoveryStatus").textContent = isDefault
      ? ""
      : "برای نمایش مدل‌های این سرویس، روی «دریافت مدل‌ها» بزن.";
    document.getElementById("modelDiscoveryStatus").className = "field-hint discovery-status";
  } catch (err) {
    toastError(err);
  }
}

async function saveProvider(payload, successMessage, reload = true) {
  await apiCall("/api/settings", { method: "PUT", body: payload });
  toast(successMessage, "success");
  if (reload) await loadProviderSettings();
}

document.getElementById("saveProviderBtn").addEventListener("click", async () => {
  const btn = document.getElementById("saveProviderBtn");
  btn.disabled = true;
  try {
    await saveProvider(
      {
        use_default_provider: true,
        chat_model: document.getElementById("chatModelSelect").value,
        embedding_model: document.getElementById("embeddingModelSelect").value,
      },
      "اتصال آماده ذخیره شد."
    );
  } catch (err) {
    toastError(err);
  } finally {
    btn.disabled = false;
  }
});

document.getElementById("saveCustomProviderBtn").addEventListener("click", async () => {
  const btn = document.getElementById("saveCustomProviderBtn");
  const baseUrl = document.getElementById("baseUrlInput").value.trim();
  const apiKey = document.getElementById("apiKeyInput").value.trim();
  const chatModel = document.getElementById("customChatModelSelect").value;
  const embeddingModel = document.getElementById("customEmbeddingModelSelect").value;

  if (!baseUrl) return toast("Base URL را وارد کن.", "error");
  if (!apiKey && !(CURRENT_SETTINGS && CURRENT_SETTINGS.api_key_set)) return toast("API Key را وارد کن.", "error");
  if (!chatModel) return toast("ابتدا لیست مدل‌های سرویس را دریافت کن.", "error");

  btn.disabled = true;
  try {
    const payload = {
      use_default_provider: false,
      base_url: baseUrl,
      chat_model: chatModel,
      embedding_model: embeddingModel || chatModel,
    };
    if (apiKey) payload.api_key = apiKey;
    await saveProvider(payload, "اتصال API اختصاصی ذخیره شد.");
  } catch (err) {
    toastError(err);
  } finally {
    btn.disabled = false;
  }
});

async function testSelectedProvider(btn, useDefault) {
  btn.disabled = true;
  const oldText = btn.textContent;
  btn.textContent = "در حال بررسی…";
  try {
    const result = await apiCall("/api/settings/provider-diagnostics", { method: "GET" });
    const status = [
      result.message || "",
      result.base_url ? `Base URL: ${result.base_url}` : "",
      result.model ? `مدل: ${result.model}` : "",
      result.dns && result.dns.length ? `DNS: ${result.dns.join(", ")}` : "DNS: resolve نشد",
      result.status_code ? `HTTP: ${result.status_code}` : "",
      result.error_type ? `نوع خطا: ${result.error_type}` : "",
      `زمان: ${result.elapsed_ms}ms`,
    ].filter(Boolean).join("\n");
    toast(status, result.ok ? "success" : "error");
  } catch (err) {
    toastError(err);
  } finally {
    btn.disabled = false;
    btn.textContent = oldText;
  }
}

document.getElementById("testConnectionBtn").addEventListener("click", function () {
  testSelectedProvider(this, true);
});
document.getElementById("testCustomConnectionBtn").addEventListener("click", async function () {
  const btn = this;
  const baseUrl = document.getElementById("baseUrlInput").value.trim();
  const apiKey = document.getElementById("apiKeyInput").value.trim();
  const chatModel = document.getElementById("customChatModelSelect").value;
  if (!baseUrl) return toast("Base URL را وارد کن.", "error");
  if (!chatModel) return toast("ابتدا مدل چت را انتخاب کن.", "error");
  if (!apiKey && !(CURRENT_SETTINGS && CURRENT_SETTINGS.api_key_set)) return toast("API Key را وارد کن.", "error");

  btn.disabled = true;
  const oldText = btn.textContent;
  btn.textContent = "در حال بررسی…";
  try {
    const result = await apiCall("/api/settings/test-custom-connection", {
      method: "POST",
      body: { base_url: baseUrl, chat_model: chatModel, ...(apiKey ? { api_key: apiKey } : {}) },
    });
    toast(result.message, result.ok ? "success" : "error");
  } catch (err) {
    toastError(err);
  } finally {
    btn.disabled = false;
    btn.textContent = oldText;
  }
});

// ---------------------------------------------------------------------------
// حالت Battle
// ---------------------------------------------------------------------------
document.getElementById("runBattleBtn").addEventListener("click", async () => {
  const prompt = document.getElementById("battlePrompt").value.trim();
  if (!prompt) return toast("یک پرامپت بنویس.", "error");

  const btn = document.getElementById("runBattleBtn");
  btn.disabled = true;
  const resultsBox = document.getElementById("battleResults");
  resultsBox.style.display = "grid";
  resultsBox.innerHTML = `<div class="battle-side">در حال دریافت پاسخ…</div><div class="battle-side">در حال دریافت پاسخ…</div>`;

  try {
    const res = await apiCall("/api/playground/battle", {
      method: "POST",
      body: {
        prompt,
        model_a: document.getElementById("battleModelA").value,
        model_b: document.getElementById("battleModelB").value,
      },
    });
    resultsBox.innerHTML = [res.side_a, res.side_b]
      .map(
        (side) => `
      <div class="battle-side">
        <div class="model-name">${escapeHtml(side.model)}</div>
        <div class="reply-text">${side.error ? `<span style="color:var(--danger)">${escapeHtml(side.error)}</span>` : escapeHtml(side.reply)}</div>
        <div class="timing">⏱ ${side.elapsed_ms}ms</div>
      </div>`
      )
      .join("");
  } catch (err) {
    toastError(err);
    resultsBox.style.display = "none";
  } finally {
    btn.disabled = false;
  }
});

// ---------------------------------------------------------------------------
// دانشنامه
// ---------------------------------------------------------------------------
let EDITING_DOC_ID = null;

async function loadDocuments() {
  try {
    const docs = await apiCall("/api/knowledge/documents");
    const list = document.getElementById("docList");
    const empty = document.getElementById("docEmptyState");
    if (docs.length === 0) {
      list.innerHTML = "";
      empty.style.display = "block";
      return;
    }
    empty.style.display = "none";
    list.innerHTML = docs
      .map(
        (d) => `
      <div class="doc-row" data-id="${d.id}">
        <div class="info">
          <div class="title">${escapeHtml(d.title)}</div>
          <div class="meta">${d.chunk_count} تکه · بروزرسانی ${formatDate(d.updated_at)}</div>
        </div>
        <div class="actions">
          <button class="icon-btn" onclick="editDocument(${d.id})" title="ویرایش">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
          </button>
          <button class="icon-btn danger" onclick="deleteDocument(${d.id})" title="حذف">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          </button>
        </div>
      </div>`
      )
      .join("");
  } catch (err) {
    toastError(err);
  }
}

function openDocModal(title, docTitle = "", docContent = "") {
  document.getElementById("docModalTitle").textContent = title;
  document.getElementById("docTitleInput").value = docTitle;
  document.getElementById("docContentInput").value = docContent;
  document.getElementById("docModal").classList.add("show");
}
function closeDocModal() {
  document.getElementById("docModal").classList.remove("show");
  EDITING_DOC_ID = null;
}
document.getElementById("addDocBtn").addEventListener("click", () => {
  EDITING_DOC_ID = null;
  openDocModal("افزودن سند جدید");
});
document.getElementById("closeDocModalBtn").addEventListener("click", closeDocModal);
document.getElementById("docModal").addEventListener("click", (e) => {
  if (e.target.id === "docModal") closeDocModal();
});

async function editDocument(id) {
  try {
    const doc = await apiCall(`/api/knowledge/documents/${id}`);
    EDITING_DOC_ID = id;
    openDocModal("ویرایش سند", doc.title, doc.content);
  } catch (err) {
    toastError(err);
  }
}

async function deleteDocument(id) {
  if (!confirm("این سند حذف شود؟ این کار قابل بازگشت نیست.")) return;
  try {
    await apiCall(`/api/knowledge/documents/${id}`, { method: "DELETE" });
    toast("سند حذف شد.", "success");
    loadDocuments();
  } catch (err) {
    toastError(err);
  }
}

document.getElementById("clearKbBtn").addEventListener("click", async () => {
  if (!confirm("همه‌ی اسناد دانشنامه حذف شوند؟ این کار قابل بازگشت نیست.")) return;
  try {
    await apiCall("/api/knowledge/documents", { method: "DELETE" });
    toast("دانشنامه پاک شد.", "success");
    loadDocuments();
  } catch (err) {
    toastError(err);
  }
});

document.getElementById("saveDocBtn").addEventListener("click", async () => {
  const title = document.getElementById("docTitleInput").value.trim();
  const content = document.getElementById("docContentInput").value.trim();
  if (!title || !content) return toast("عنوان و محتوا را پر کن.", "error");

  const btn = document.getElementById("saveDocBtn");
  btn.disabled = true;
  btn.textContent = "در حال ایندکس‌کردن…";
  try {
    if (EDITING_DOC_ID) {
      await apiCall(`/api/knowledge/documents/${EDITING_DOC_ID}`, { method: "PUT", body: { title, content } });
      toast("سند بروزرسانی شد.", "success");
    } else {
      await apiCall("/api/knowledge/documents", { method: "POST", body: { title, content } });
      toast("سند اضافه و ایندکس شد.", "success");
    }
    closeDocModal();
    loadDocuments();
  } catch (err) {
    toastError(err);
  } finally {
    btn.disabled = false;
    btn.textContent = "ذخیره و ایندکس‌کردن";
  }
});

document.getElementById("uploadTxtInput").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    EDITING_DOC_ID = null;
    openDocModal("افزودن سند جدید", file.name.replace(/\.txt$/i, ""), reader.result);
  };
  reader.readAsText(file, "utf-8");
  e.target.value = "";
});

// ---------------------------------------------------------------------------
// شخصی‌سازی رفتار RAG و پرامپت
// ---------------------------------------------------------------------------
async function loadRagPromptSettings() {
  try {
    const s = await apiCall("/api/settings");
    CURRENT_SETTINGS = s;
    document.getElementById("systemPromptInput").value = s.system_prompt;
    document.getElementById("temperatureRange").value = s.temperature;
    document.getElementById("temperatureValue").textContent = s.temperature;
    document.getElementById("topKRange").value = s.top_k;
    document.getElementById("topKValue").textContent = s.top_k;
    document.getElementById("similarityThresholdRange").value = s.similarity_threshold;
    document.getElementById("similarityThresholdValue").textContent = s.similarity_threshold;
  } catch (err) {
    toastError(err);
  }
}

document.getElementById("temperatureRange").addEventListener("input", (e) => {
  document.getElementById("temperatureValue").textContent = e.target.value;
});
document.getElementById("topKRange").addEventListener("input", (e) => {
  document.getElementById("topKValue").textContent = e.target.value;
});
document.getElementById("similarityThresholdRange").addEventListener("input", (e) => {
  document.getElementById("similarityThresholdValue").textContent = e.target.value;
});

document.getElementById("saveRagPromptBtn").addEventListener("click", async () => {
  const btn = document.getElementById("saveRagPromptBtn");
  btn.disabled = true;
  try {
    await apiCall("/api/settings", {
      method: "PUT",
      body: {
        system_prompt: document.getElementById("systemPromptInput").value,
        temperature: parseFloat(document.getElementById("temperatureRange").value),
        top_k: parseInt(document.getElementById("topKRange").value, 10),
        similarity_threshold: parseFloat(document.getElementById("similarityThresholdRange").value),
      },
    });
    toast("رفتار دستیار ذخیره شد.", "success");
  } catch (err) {
    toastError(err);
  } finally {
    btn.disabled = false;
  }
});

// ---------------------------------------------------------------------------
// آزمایشگاه تست: تب‌ها
// ---------------------------------------------------------------------------
document.querySelectorAll("#view-test-lab .tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#view-test-lab .tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll("#view-test-lab .tab-pane").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
  });
});

// --- تست گفت‌وگوی RAG ---
function appendChatMsg(role, text) {
  const stream = document.getElementById("chatStream");
  const el = document.createElement("div");
  el.className = `chat-msg ${role === "user" ? "user" : "bot"}`;
  el.textContent = text;
  stream.appendChild(el);
  stream.scrollTop = stream.scrollHeight;
  return el;
}

let CHAT_REQUEST_ACTIVE = false;

async function sendChatMessage() {
  if (CHAT_REQUEST_ACTIVE) return;
  const input = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendChatBtn");
  const message = input.value.trim();
  if (!message) return;

  CHAT_REQUEST_ACTIVE = true;
  sendBtn.disabled = true;
  input.value = "";
  appendChatMsg("user", message);
  const pending = appendChatMsg("bot", "در حال آماده‌سازی پاسخ…");
  pending.classList.add("pending");

  try {
    // همیشه مدل فعلی تنظیمات را صریحاً به backend می‌فرستیم تا تغییر مدل
    // فقط در UI نماند و همان درخواست با مدل انتخاب‌شده اجرا شود.
    const selectedModel = CURRENT_SETTINGS && CURRENT_SETTINGS.chat_model
      ? CURRENT_SETTINGS.chat_model
      : undefined;

    const res = await apiCall("/api/playground/chat", {
      method: "POST",
      timeoutMs: 90000,
      body: { message, session_id: CHAT_SESSION_ID, ...(selectedModel ? { model: selectedModel } : {}) },
    });
    CHAT_SESSION_ID = res.session_id;
    pending.textContent = res.reply;
    pending.classList.remove("pending");

    const modelBadge = document.getElementById("activeChatModelBadge");
    modelBadge.textContent = res.model || selectedModel || "—";

    const sourcesList = document.getElementById("sourcesList");
    if (res.sources.length === 0) {
      sourcesList.innerHTML = `<span class="cell-muted">منبعی از دانشنامه پیدا نشد.</span>`;
    } else {
      sourcesList.innerHTML = res.sources
        .map(
          (s) => `
        <div class="source-item">
          <div class="score">${escapeHtml(s.document_title)} · شباهت ${(s.score * 100).toFixed(1)}٪</div>
          <div class="snippet">${escapeHtml(s.text.slice(0, 220))}${s.text.length > 220 ? "…" : ""}</div>
        </div>`
        )
        .join("");
    }
  } catch (err) {
    const requestId = err && err.requestId ? `\nشناسه درخواست: ${err.requestId}` : "";
    pending.textContent = `${err && err.message ? err.message : String(err)}${requestId}`;
    pending.classList.remove("pending");
    pending.style.color = "var(--danger)";
  } finally {
    CHAT_REQUEST_ACTIVE = false;
    sendBtn.disabled = false;
  }
}
document.getElementById("sendChatBtn").addEventListener("click", sendChatMessage);
document.getElementById("chatInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendChatMessage();
  }
});
document.getElementById("newSessionBtn").addEventListener("click", async () => {
  const oldSession = CHAT_SESSION_ID;
  CHAT_SESSION_ID = null;
  try {
    if (oldSession) {
      await apiCall(`/api/playground/sessions/${encodeURIComponent(oldSession)}`, { method: "DELETE" });
    }
  } catch (err) {
    toastError(err);
  } finally {
    document.getElementById("chatStream").innerHTML = `<div class="chat-msg bot">گفت‌وگوی جدید شروع شد. سؤالت را بپرس.</div>`;
    document.getElementById("sourcesList").innerHTML = `<span class="cell-muted">هنوز سؤالی پرسیده نشده.</span>`;
  }
});

// --- جست‌وجوی معنایی ---
async function runSemanticSearch() {
  const query = document.getElementById("searchQueryInput").value.trim();
  if (!query) return;
  const box = document.getElementById("searchResults");
  box.innerHTML = `<div class="cell-muted">در حال جست‌وجو…</div>`;
  try {
    const results = await apiCall("/api/playground/search", { method: "POST", body: { query, top_k: 6 } });
    if (results.length === 0) {
      box.innerHTML = `<div class="empty-state"><div class="icon">🔍</div><div class="title">نتیجه‌ای یافت نشد</div></div>`;
      return;
    }
    box.innerHTML = results
      .map(
        (r) => `
      <div class="search-result-row">
        <div class="head"><span class="doc-name">${escapeHtml(r.document_title)}</span><span class="score">${(r.score * 100).toFixed(1)}٪</span></div>
        <div>${escapeHtml(r.text.slice(0, 300))}${r.text.length > 300 ? "…" : ""}</div>
      </div>`
      )
      .join("");
  } catch (err) {
    box.innerHTML = "";
    toastError(err);
  }
}
document.getElementById("runSearchBtn").addEventListener("click", runSemanticSearch);
document.getElementById("searchQueryInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") runSemanticSearch();
});

// ---------------------------------------------------------------------------
// ویجت‌ساز
// ---------------------------------------------------------------------------
function renderWidgetPreview(title, welcome, color, widgetId) {
  // کارت توضیحی کوچک را با iframe واقعی عوض می‌کنیم تا خود widget.js هم تست شود.
  const frame = document.getElementById("widgetPreviewFrame");
  if (!frame) return;
  LAST_WIDGET_ID = widgetId;
  const theme = document.documentElement.dataset.theme === "light" ? "light" : "dark";
  frame.src = `/widget-preview.html?widget_id=${encodeURIComponent(widgetId)}&theme=${theme}&v=${Date.now()}`;
}

let LAST_WIDGET_ID = null;
// اگر کاربر تم سایت را عوض کرد، پیش‌نمایش ویجت هم با همان تم دوباره ساخته می‌شود
document.addEventListener("qz-theme-change", () => {
  if (LAST_WIDGET_ID) renderWidgetPreview(null, null, null, LAST_WIDGET_ID);
});

async function loadWidgetSection() {
  try {
    const cfg = await apiCall("/api/widget/config");
    document.getElementById("widgetTitleInput").value = cfg.widget_title;
    document.getElementById("widgetWelcomeInput").value = cfg.widget_welcome_message;
    document.getElementById("widgetColorInput").value = cfg.widget_color;
    renderWidgetPreview(cfg.widget_title, cfg.widget_welcome_message, cfg.widget_color, cfg.widget_id);

    const embed = await apiCall("/api/widget/embed-code");
    const code = embed.embed_code_template.replaceAll("__BASE_URL__", window.location.origin);
    document.getElementById("embedCodeBox").textContent = code;
  } catch (err) {
    toastError(err);
  }
}

document.getElementById("refreshWidgetPreviewBtn").addEventListener("click", () => loadWidgetSection());

document.getElementById("saveWidgetBtn").addEventListener("click", async () => {
  const title = document.getElementById("widgetTitleInput").value.trim();
  const welcome = document.getElementById("widgetWelcomeInput").value.trim();
  const color = document.getElementById("widgetColorInput").value;
  if (!title || !welcome) return toast("عنوان و پیام خوش‌آمدگویی نمی‌توانند خالی باشند.", "error");
  const btn = document.getElementById("saveWidgetBtn");
  btn.disabled = true;
  try {
    const saved = await apiCall("/api/widget/config", {
      method: "PUT",
      body: { widget_title: title, widget_welcome_message: welcome, widget_color: color },
    });
    const cfg = await apiCall("/api/widget/config");
    toast("ظاهر ویجت ذخیره شد.", "success");
    renderWidgetPreview(title, welcome, color, cfg.widget_id);
  } catch (err) {
    toastError(err);
  } finally {
    btn.disabled = false;
  }
});

document.getElementById("copyEmbedBtn").addEventListener("click", async () => {
  const text = document.getElementById("embedCodeBox").textContent;
  try {
    await navigator.clipboard.writeText(text);
    toast("کد کپی شد.", "success");
  } catch (_) {
    // clipboard در برخی contextها (مثل http محلی خاص) در دسترس نیست.
    const helper = document.createElement("textarea");
    helper.value = text;
    document.body.appendChild(helper);
    helper.select();
    document.execCommand("copy");
    helper.remove();
    toast("کد کپی شد.", "success");
  }
});

// ---------------------------------------------------------------------------
// ابزارهای کمکی
// ---------------------------------------------------------------------------
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}
function formatDate(iso) {
  try {
    return new Date(iso).toLocaleDateString("fa-IR");
  } catch (_) {
    return iso;
  }
}

init();
