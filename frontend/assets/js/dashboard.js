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
  const identity = document.querySelectorAll("#sidebarUserName, #sidebarUserRole");
  Skel.toggle(identity, true);
  try {
    CURRENT_USER = await apiCall("/api/auth/me");
  } catch (err) {
    Skel.toggle(identity, false);
    return; // apiCall خودش در صورت 401 ریدایرکت می‌کند
  }
  Skel.toggle(identity, false);

  document.getElementById("sidebarUserName").textContent = CURRENT_USER.org_name || CURRENT_USER.username;
  document.getElementById("sidebarUserRole").textContent = CURRENT_USER.role === "admin" ? "مدیر سیستم" : "کاربر";
  document.getElementById("avatarInitial").textContent = (CURRENT_USER.org_name || CURRENT_USER.username)[0].toUpperCase();
  const topAvatar = document.getElementById("topbarAvatar");
  if (topAvatar) topAvatar.textContent = document.getElementById("avatarInitial").textContent;

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
  const overviewValues = document.querySelectorAll("#view-overview .stat-card .value");
  Skel.toggle(overviewValues, true);
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
  } finally {
    Skel.toggle(overviewValues, false);
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

document.querySelectorAll("#view-ai-settings [data-aitab]").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#view-ai-settings [data-aitab]").forEach((b) => b.classList.toggle("active", b === btn));
    document.getElementById("aitab-connect").classList.toggle("active", btn.dataset.aitab === "connect");
    document.getElementById("aitab-battle").classList.toggle("active", btn.dataset.aitab === "battle");
  });
});

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
    status.className = "status-line success-text";
    toast("لیست مدل‌ها دریافت شد.", "success");
  } catch (err) {
    DISCOVERED_CUSTOM_MODELS = [];
    fillModelSelect(document.getElementById("customChatModelSelect"), [], "");
    fillModelSelect(document.getElementById("customEmbeddingModelSelect"), [], "");
    status.textContent = err.message;
    status.className = "status-line error-text";
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
    document.getElementById("modelDiscoveryStatus").className = "status-line";
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
  const list = document.getElementById("docList");
  const empty = document.getElementById("docEmptyState");
  if (!list.children.length) {
    empty.style.display = "none";
    list.innerHTML = Skel.rows(3, 64);
  }
  try {
    const docs = await apiCall("/api/knowledge/documents");
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

// دوبار کلیک روی «ویرایش»/«حذف» فقط یک‌بار اجرا می‌شود؛ بعد از بسته‌شدن، کلیک بعدی دوباره کار می‌کند
function editDocument(id) {
  return once(`edit-doc:${id}`, () => editDocumentImpl(id));
}
function deleteDocument(id) {
  return once(`delete-doc:${id}`, () => deleteDocumentImpl(id));
}

async function editDocumentImpl(id) {
  if (document.getElementById("docModal").classList.contains("show")) return;
  try {
    const doc = await apiCall(`/api/knowledge/documents/${id}`);
    EDITING_DOC_ID = id;
    openDocModal("ویرایش سند", doc.title, doc.content);
  } catch (err) {
    toastError(err);
  }
}

async function deleteDocumentImpl(id) {
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

// ---------------------------------------------------------------------------
// ایمپورت فایل (PDF، Word، Excel، PowerPoint، ...) → متن → دانشنامه
// ---------------------------------------------------------------------------
const importList = document.getElementById("importList");
let IMPORT_BUSY = false;

function addImportRow(name) {
  const row = document.createElement("div");
  row.className = "import-row";
  row.innerHTML = `<span class="import-name"></span><span class="import-state"></span>`;
  row.querySelector(".import-name").textContent = name;
  importList.prepend(row);
  const state = row.querySelector(".import-state");
  return {
    set(text, kind) {
      state.textContent = text;
      row.dataset.kind = kind || "";
    },
    done() { setTimeout(() => row.classList.add("fade"), 6000); setTimeout(() => row.remove(), 6800); },
  };
}

async function importFiles(fileList) {
  const files = Array.from(fileList || []);
  if (!files.length) return;
  if (IMPORT_BUSY) return toast("ایمپورت قبلی هنوز تمام نشده است.", "error");
  IMPORT_BUSY = true;
  const dz = document.getElementById("docDropzone");
  dz.classList.add("busy");

  let imported = 0;
  try {
    try {
      await Lazy.script("/assets/js/extract.js?v=2.5.0");
    } catch (err) {
      return toastError(err);
    }
    for (const file of files) {
      const row = addImportRow(file.name);
      try {
        row.set("در حال خواندن…", "work");
        const { title, text } = await FileExtract.extract(file, (page, total) => row.set(`خواندن صفحه ${page} از ${total}…`, "work"));

        // فقط یک فایل کوچک: متن را برای بازبینی در همان ویرایشگر باز کن (رفتار قبلیِ آپلود TXT)
        if (files.length === 1 && text.length <= 60000) {
          row.set("آماده‌ی بازبینی", "ok");
          EDITING_DOC_ID = null;
          openDocModal("افزودن سند جدید", title, text);
          row.done();
          continue;
        }

        const parts = FileExtract.splitForUpload(text);
        for (let i = 0; i < parts.length; i++) {
          row.set(parts.length > 1 ? `ایندکس بخش ${i + 1} از ${parts.length}…` : "در حال ایندکس‌کردن…", "work");
          const docTitle = parts.length > 1 ? `${title} (بخش ${i + 1} از ${parts.length})` : title;
          await apiCall("/api/knowledge/documents", { method: "POST", timeoutMs: 90000, body: { title: docTitle.slice(0, 200), content: parts[i] } });
          imported += 1;
        }
        row.set(parts.length > 1 ? `✓ ${parts.length} بخش اضافه شد` : "✓ اضافه شد", "ok");
        row.done();
      } catch (err) {
        row.set(err && err.message ? err.message : "ناموفق", "error");
      }
    }
  } finally {
    IMPORT_BUSY = false;
    dz.classList.remove("busy");
    if (imported) {
      toast(`${imported} سند به دانشنامه اضافه شد.`, "success");
      loadDocuments();
    }
  }
}

const uploadInput = document.getElementById("uploadFileInput");
uploadInput.addEventListener("change", (e) => {
  importFiles(e.target.files);
  e.target.value = "";
});

const dropzone = document.getElementById("docDropzone");
dropzone.addEventListener("click", () => uploadInput.click());
dropzone.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); uploadInput.click(); } });
["dragenter", "dragover"].forEach((ev) =>
  dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.add("over"); })
);
["dragleave", "drop"].forEach((ev) =>
  dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.remove("over"); })
);
dropzone.addEventListener("drop", (e) => importFiles(e.dataTransfer && e.dataTransfer.files));

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
let CHAT_ABORT = null;

const SEND_ICON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>';
const STOP_ICON = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="5" y="5" width="14" height="14" rx="2"></rect></svg>';

function renderChatSources(sources) {
  const sourcesList = document.getElementById("sourcesList");
  if (!sources || sources.length === 0) {
    sourcesList.innerHTML = `<span class="cell-muted">منبعی از دانشنامه پیدا نشد.</span>`;
    return;
  }
  sourcesList.innerHTML = sources
    .map(
      (s) => `
    <div class="source-item">
      <div class="score">${escapeHtml(s.document_title)} · شباهت ${(s.score * 100).toFixed(1)}٪</div>
      <div class="snippet">${escapeHtml(s.text.slice(0, 220))}${s.text.length > 220 ? "…" : ""}</div>
    </div>`
    )
    .join("");
}

function showChatError(bubble, err) {
  const requestId = err && err.requestId ? `\nشناسه درخواست: ${err.requestId}` : "";
  const message = `${err && err.message ? err.message : String(err)}${requestId}`;
  if (bubble.dataset.hasText === "1") {
    // متنِ نیمه‌کاره را نگه می‌داریم و خطا را زیرش می‌نویسیم
    const note = document.createElement("div");
    note.className = "chat-note";
    note.textContent = message;
    bubble.appendChild(note);
  } else {
    bubble.textContent = message;
    bubble.style.color = "var(--danger)";
  }
}

// مسیر اصلی: استریم تکه‌تکه (مثل ChatGPT)
async function chatViaStream(message, selectedModel, bubble) {
  let text = "";
  let frame = null;
  const paint = () => {
    frame = null;
    bubble.textContent = text;
    const stream = document.getElementById("chatStream");
    stream.scrollTop = stream.scrollHeight;
  };
  CHAT_ABORT = new AbortController();
  try {
    await apiStream("/api/playground/chat/stream", {
      signal: CHAT_ABORT.signal,
      body: { message, session_id: CHAT_SESSION_ID, ...(selectedModel ? { model: selectedModel } : {}) },
      onMeta: (meta) => {
        CHAT_SESSION_ID = meta.session_id;
        document.getElementById("activeChatModelBadge").textContent = meta.model || selectedModel || "—";
        renderChatSources(meta.sources);
      },
      onDelta: (piece) => {
        if (!text) {
          bubble.classList.remove("pending");
          bubble.dataset.hasText = "1";
        }
        text += piece;
        if (frame === null) frame = requestAnimationFrame(paint);
      },
    });
  } finally {
    if (frame !== null) cancelAnimationFrame(frame);
    if (text) bubble.textContent = text;
    bubble.classList.remove("streaming");
    CHAT_ABORT = null;
  }
}

// مسیر پشتیبان: یک‌جا (برای سروری که استریم ندارد)
async function chatViaRequest(message, selectedModel, bubble) {
  const res = await apiCall("/api/playground/chat", {
    method: "POST",
    timeoutMs: 90000,
    body: { message, session_id: CHAT_SESSION_ID, ...(selectedModel ? { model: selectedModel } : {}) },
  });
  CHAT_SESSION_ID = res.session_id;
  bubble.textContent = res.reply;
  bubble.classList.remove("pending");
  document.getElementById("activeChatModelBadge").textContent = res.model || selectedModel || "—";
  renderChatSources(res.sources);
}

async function sendChatMessage() {
  const sendBtn = document.getElementById("sendChatBtn");
  if (CHAT_REQUEST_ACTIVE) {
    // دکمه در حالت «توقف» است
    if (CHAT_ABORT) CHAT_ABORT.abort();
    return;
  }
  const input = document.getElementById("chatInput");
  const message = input.value.trim();
  if (!message) return;

  CHAT_REQUEST_ACTIVE = true;
  sendBtn.innerHTML = STOP_ICON;
  sendBtn.title = "توقف پاسخ";
  input.value = "";
  appendChatMsg("user", message);
  const bubble = appendChatMsg("bot", "در حال آماده‌سازی پاسخ…");
  bubble.classList.add("pending", "streaming");

  // همیشه مدل فعلی تنظیمات را صریحاً به backend می‌فرستیم
  const selectedModel = CURRENT_SETTINGS && CURRENT_SETTINGS.chat_model ? CURRENT_SETTINGS.chat_model : undefined;

  try {
    try {
      await chatViaStream(message, selectedModel, bubble);
    } catch (err) {
      if (err && err.aborted) {
        // کاربر خودش متوقف کرد: متن تا اینجا می‌ماند
        if (bubble.dataset.hasText !== "1") bubble.textContent = "پاسخ متوقف شد.";
        bubble.classList.remove("pending");
      } else if (err && STREAM_FALLBACK_STATUSES.includes(err.status) && bubble.dataset.hasText !== "1") {
        await chatViaRequest(message, selectedModel, bubble);
      } else {
        throw err;
      }
    }
  } catch (err) {
    bubble.classList.remove("pending");
    showChatError(bubble, err);
  } finally {
    CHAT_REQUEST_ACTIVE = false;
    CHAT_ABORT = null;
    bubble.classList.remove("streaming");
    sendBtn.innerHTML = SEND_ICON;
    sendBtn.title = "ارسال";
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
// ---------------------------------------------------------------------------
// ویجت‌ساز: ظاهر، حیوان خانگی، گفت‌وگو، پیش‌نمایش زنده و کد جاسازی
// ---------------------------------------------------------------------------
const WIDGET_SWATCHES = ["#8B5CF6", "#EAB308", "#F59E0B", "#EC4899", "#14B8A6", "#3B82F6", "#22C55E", "#EF4444"];
const PET_SWATCHES = {
  dog: ["#C98A4B", "#8A5A2B", "#E8C9A0", "#3A3A44", "#F2F2F2"],
  cat: ["#9696A5", "#E0A030", "#3A3A44", "#F2F2F2", "#F4B6C2"],
  raccoon: ["#808090", "#6B5A4A", "#3A3A44", "#B8B8C4"],
};

let LAST_WIDGET_ID = null;
let WIDGET_BASELINE = "";
let EMBED_TEMPLATE = "";
let EMBED_THEME = "auto";
let PREVIEW_TIMER = null;

const widgetEl = (id) => document.getElementById(id);

function readWidgetForm() {
  const quick = Array.from(document.querySelectorAll("#quickInputs input")).map((i) => i.value.trim()).filter(Boolean);
  const activePos = document.querySelector("#widgetPositionSeg .seg-btn.active");
  const activePet = document.querySelector("#petGrid .pet-card.active");
  return {
    title: widgetEl("widgetTitleInput").value.trim(),
    welcome: widgetEl("widgetWelcomeInput").value.trim(),
    color: widgetEl("widgetColorInput").value,
    extras: {
      pet_enabled: widgetEl("petEnabledChk").checked,
      pet: activePet ? activePet.dataset.pet : "dog",
      pet_color: widgetEl("petColorInput").value,
      position: activePos ? activePos.dataset.pos : "bottom-left",
      teaser_enabled: widgetEl("teaserChk").checked,
      quick_replies: quick.slice(0, 4),
    },
  };
}

function updateWidgetDirty() {
  const dirty = JSON.stringify(readWidgetForm()) !== WIDGET_BASELINE;
  const hint = widgetEl("widgetDirtyHint");
  hint.textContent = dirty ? "تغییرات ذخیره‌نشده" : "";
  hint.className = "status-line" + (dirty ? " error-text" : "");
}

// تغییرات فرم را همان لحظه (حتی بدون ذخیره) به ویجت داخل پیش‌نمایش می‌فرستیم
function pushWidgetPreview(showTeaser) {
  clearTimeout(PREVIEW_TIMER);
  PREVIEW_TIMER = setTimeout(() => {
    const frame = widgetEl("widgetPreviewFrame");
    if (!frame || !frame.contentWindow || !LAST_WIDGET_ID) return;
    const f = readWidgetForm();
    frame.contentWindow.postMessage(
      { qzPreview: { title: f.title, welcome: f.welcome, color: f.color, extras: f.extras, showTeaser: Boolean(showTeaser) } },
      window.location.origin
    );
  }, 120);
}

function onWidgetFormChange(showTeaser) {
  updateWidgetDirty();
  pushWidgetPreview(showTeaser);
}

function renderSwatches(containerId, colors, inputId) {
  const box = widgetEl(containerId);
  const input = widgetEl(inputId);
  box.innerHTML = colors
    .map((c) => `<button type="button" class="swatch" data-color="${c}" style="background:${c}" title="${c}" aria-label="${c}"></button>`)
    .join("");
  box.querySelectorAll(".swatch").forEach((btn) => {
    btn.addEventListener("click", () => {
      input.value = btn.dataset.color;
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });
  });
}

function renderPetGrid(selected, color) {
  const grid = widgetEl("petGrid");
  if (!window.QzPets) return;
  grid.innerHTML = QzPets.names
    .map(
      (name) => `
    <button type="button" class="pet-card${name === selected ? " active" : ""}" data-pet="${name}" role="radio" aria-checked="${name === selected}">
      <span class="pet-thumb">${QzPets.svg(name, "i", color, 4)}</span>
      <span class="pet-name">${QzPets.labels[name]}</span>
    </button>`
    )
    .join("");
  grid.querySelectorAll(".pet-card").forEach((card) => {
    card.addEventListener("click", () => {
      const previous = grid.querySelector(".pet-card.active");
      const prevName = previous ? previous.dataset.pet : "dog";
      const colorInput = widgetEl("petColorInput");
      // اگر کاربر رنگ دلخواه نگذاشته بود، رنگ پیش‌فرض حیوان تازه را بگذار
      if (colorInput.value.toLowerCase() === QzPets.defaultColors[prevName].toLowerCase()) {
        colorInput.value = QzPets.defaultColors[card.dataset.pet];
      }
      renderPetGrid(card.dataset.pet, colorInput.value);
      renderSwatches("petSwatches", PET_SWATCHES[card.dataset.pet], "petColorInput");
      onWidgetFormChange(false);
    });
  });
}

function setWidgetPosition(pos) {
  document.querySelectorAll("#widgetPositionSeg .seg-btn").forEach((b) => b.classList.toggle("active", b.dataset.pos === pos));
}

function setWidgetPreviewLoading(on) {
  const wrap = widgetEl("widgetPreviewWrap");
  if (wrap) wrap.classList.toggle("skeleton", on);
}

function renderWidgetPreview(widgetId) {
  const frame = widgetEl("widgetPreviewFrame");
  if (!frame) return;
  LAST_WIDGET_ID = widgetId;
  const theme = document.documentElement.dataset.theme === "light" ? "light" : "dark";
  frame.src = `/widget-preview.html?widget_id=${encodeURIComponent(widgetId)}&theme=${theme}&v=${Date.now()}`;
}

// پیش‌نمایش بعد از هر بار لود، آخرین مقدارهای فرم را (حتی ذخیره‌نشده) دوباره می‌گیرد
widgetEl("widgetPreviewFrame").addEventListener("load", () => {
  setWidgetPreviewLoading(false);
  pushWidgetPreview(true);
});

// اگر کاربر تم سایت را عوض کرد، پیش‌نمایش ویجت هم با همان تم دوباره ساخته می‌شود
document.addEventListener("qz-theme-change", () => {
  if (LAST_WIDGET_ID) renderWidgetPreview(LAST_WIDGET_ID);
});

function renderEmbedCode() {
  if (!EMBED_TEMPLATE) return;
  const code = EMBED_TEMPLATE.replaceAll("__BASE_URL__", window.location.origin).replace(/data-theme="[^"]*"/, `data-theme="${EMBED_THEME}"`);
  widgetEl("embedCodeBox").textContent = code;
}

async function loadWidgetSection() {
  try {
    setWidgetPreviewLoading(true);
    const [cfg, embed] = await Promise.all([
      apiCall("/api/widget/config"),
      apiCall("/api/widget/embed-code"),
      Lazy.script("/assets/js/pets.js?v=2.5.0").catch(() => null), // اگر نیامد، فقط انتخابگر حیوان خالی می‌ماند
    ]);
    const ex = cfg.extras || {};
    const pet = ex.pet || "dog";
    widgetEl("widgetTitleInput").value = cfg.widget_title;
    widgetEl("widgetWelcomeInput").value = cfg.widget_welcome_message;
    widgetEl("widgetColorInput").value = cfg.widget_color;
    renderSwatches("widgetSwatches", WIDGET_SWATCHES, "widgetColorInput");
    setWidgetPosition(ex.position || "bottom-left");
    widgetEl("petEnabledChk").checked = Boolean(ex.pet_enabled);
    widgetEl("petColorInput").value = ex.pet_color || (window.QzPets ? QzPets.defaultColors[pet] : "#C98A4B");
    widgetEl("petOptions").classList.toggle("disabled", !ex.pet_enabled);
    renderSwatches("petSwatches", PET_SWATCHES[pet] || PET_SWATCHES.dog, "petColorInput");
    renderPetGrid(pet, widgetEl("petColorInput").value);
    widgetEl("teaserChk").checked = Boolean(ex.teaser_enabled);
    const quickInputs = document.querySelectorAll("#quickInputs input");
    quickInputs.forEach((input, i) => (input.value = (ex.quick_replies || [])[i] || ""));

    WIDGET_BASELINE = JSON.stringify(readWidgetForm());
    updateWidgetDirty();
    if (cfg.extras_available === false) {
      const hint = widgetEl("widgetDirtyHint");
      hint.textContent = "ذخیره‌ی حیوان خانگی و پاسخ‌های سریع نیاز به یک‌بار اجرای migration شماره‌ی ۰۰۲ دارد.";
    }

    EMBED_TEMPLATE = embed.embed_code_template;
    renderEmbedCode();
    renderWidgetPreview(cfg.widget_id);
  } catch (err) {
    setWidgetPreviewLoading(false);
    toastError(err);
  }
}

// --- رویدادهای فرم ---
document.querySelectorAll("#widgetTabs .tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#widgetTabs .tab-btn").forEach((b) => b.classList.toggle("active", b === btn));
    document.querySelectorAll("#view-widget .widget-controls .tab-pane").forEach((p) => p.classList.toggle("active", p.id === `wtab-${btn.dataset.wtab}`));
  });
});
["widgetTitleInput", "widgetWelcomeInput", "widgetColorInput", "petColorInput"].forEach((id) =>
  widgetEl(id).addEventListener("input", () => {
    if (id === "petColorInput") {
      const active = document.querySelector("#petGrid .pet-card.active");
      renderPetGrid(active ? active.dataset.pet : "dog", widgetEl("petColorInput").value);
    }
    onWidgetFormChange(false);
  })
);
widgetEl("petEnabledChk").addEventListener("change", () => {
  widgetEl("petOptions").classList.toggle("disabled", !widgetEl("petEnabledChk").checked);
  onWidgetFormChange(false);
});
widgetEl("teaserChk").addEventListener("change", () => onWidgetFormChange(widgetEl("teaserChk").checked));
document.querySelectorAll("#quickInputs input").forEach((i) => i.addEventListener("input", () => onWidgetFormChange(false)));
document.querySelectorAll("#widgetPositionSeg .seg-btn").forEach((btn) =>
  btn.addEventListener("click", () => {
    setWidgetPosition(btn.dataset.pos);
    onWidgetFormChange(false);
  })
);
document.querySelectorAll("#embedThemeSeg .seg-btn").forEach((btn) =>
  btn.addEventListener("click", () => {
    EMBED_THEME = btn.dataset.embedTheme;
    document.querySelectorAll("#embedThemeSeg .seg-btn").forEach((b) => b.classList.toggle("active", b === btn));
    renderEmbedCode();
  })
);

widgetEl("refreshWidgetPreviewBtn").addEventListener("click", () => {
  if (LAST_WIDGET_ID) renderWidgetPreview(LAST_WIDGET_ID);
});

widgetEl("saveWidgetBtn").addEventListener("click", async () => {
  const form = readWidgetForm();
  if (!form.title || !form.welcome) return toast("عنوان و پیام خوش‌آمدگویی نمی‌توانند خالی باشند.", "error");
  const btn = widgetEl("saveWidgetBtn");
  btn.disabled = true;
  try {
    await apiCall("/api/widget/config", {
      method: "PUT",
      body: { widget_title: form.title, widget_welcome_message: form.welcome, widget_color: form.color, extras: form.extras },
    });
    WIDGET_BASELINE = JSON.stringify(readWidgetForm());
    updateWidgetDirty();
    toast("تنظیمات ویجت ذخیره شد.", "success");
  } catch (err) {
    toastError(err);
  } finally {
    btn.disabled = false;
  }
});

widgetEl("copyEmbedBtn").addEventListener("click", async () => {
  const text = widgetEl("embedCodeBox").textContent;
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
