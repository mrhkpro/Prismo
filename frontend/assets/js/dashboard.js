// ============================================================================
// داشبورد اصلی — منطق ناوبری + همه‌ی بخش‌های فاز ۱
// ============================================================================

if (!Auth.isLoggedIn()) location.href = "/index.html";

let CURRENT_USER = null;
let CURRENT_SETTINGS = null;
let SAVED_CHAT_MODELS = [];
let SAVED_EMBEDDING_MODELS = [];
let CHAT_SESSION_ID = null;

// Serverless Vercel: prefer the bounded JSON RAG route over provider SSE.
// Local instances re-enable streaming after /api/runtime confirms they are local.
let PRISMO_IS_VERCEL_RUNTIME = true;
const PRISMO_RUNTIME_CONTROLLER = new AbortController();
const PRISMO_RUNTIME_TIMEOUT = setTimeout(() => PRISMO_RUNTIME_CONTROLLER.abort(), 3000);
const PRISMO_RUNTIME_READY = fetch("/api/runtime", {
  cache: "no-store",
  headers: { Accept: "application/json" },
  signal: PRISMO_RUNTIME_CONTROLLER.signal,
}).then(async (response) => {
  if (!response.ok) throw new Error("Runtime detection failed");
  const runtime = await response.json();
  PRISMO_IS_VERCEL_RUNTIME = Boolean(runtime.vercel);
  return runtime;
}).catch(() => ({ vercel: true })).finally(() => clearTimeout(PRISMO_RUNTIME_TIMEOUT));

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
    if (viewName === "settings" && window.QZSettings) window.QZSettings.apply();
    if (window.QZSettings && window.QZSettings.get("rememberView")) {
      try { sessionStorage.setItem("qz_last_view", viewName); } catch (_) {}
    }
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
  document.getElementById("sidebarUserRole").textContent = window.QZI18n ? window.QZI18n.t(CURRENT_USER.role === "admin" ? "مدیر سیستم" : "کاربر") : (CURRENT_USER.role === "admin" ? "مدیر سیستم" : "کاربر");
  document.getElementById("avatarInitial").textContent = (CURRENT_USER.org_name || CURRENT_USER.username)[0].toUpperCase();
  const topAvatar = document.getElementById("topbarAvatar");
  if (topAvatar) topAvatar.textContent = document.getElementById("avatarInitial").textContent;

  document.getElementById("accUsername").value = CURRENT_USER.username;
  document.getElementById("accOrgName").value = CURRENT_USER.org_name || "—";
  document.getElementById("accRole").value = window.QZI18n ? window.QZI18n.t(CURRENT_USER.role === "admin" ? "مدیر سیستم" : "کاربر عادی") : (CURRENT_USER.role === "admin" ? "مدیر سیستم" : "کاربر عادی");
  document.getElementById("accDisplayName").textContent = CURRENT_USER.org_name || CURRENT_USER.username;
  document.getElementById("accDisplayRole").textContent = window.QZI18n ? window.QZI18n.t(CURRENT_USER.role === "admin" ? "مدیر سیستم" : "کاربر") : CURRENT_USER.role;
  document.getElementById("accAvatar").textContent = (CURRENT_USER.org_name || CURRENT_USER.username)[0].toUpperCase();

  if (CURRENT_USER.role === "admin") {
    document.getElementById("adminNavGroup").style.display = "block";
  }

  if (CURRENT_USER.impersonated_by || Auth.hasStashedAdmin()) {
    const banner = document.getElementById("impersonationBanner");
    banner.style.display = "flex";
    document.getElementById("impersonationText").textContent =
      `⚠️ شما در حالت جانمایی، به‌جای کاربر «${CURRENT_USER.username}» وارد شده‌اید.`;
  }

  // Do not load every dashboard section on boot. Open only the remembered section;
  // this keeps Supabase startup to one authenticated request plus one section request.
  let initialView = "overview";
  try {
    const remembered = window.QZSettings && window.QZSettings.get("rememberView") ? sessionStorage.getItem("qz_last_view") : null;
    if (remembered && document.getElementById(`view-${remembered}`)) initialView = remembered;
  } catch (_) {}
  Nav.go(initialView);
}

document.getElementById("goToAdminBtn").addEventListener("click", () => (location.href = "/admin.html"));
document.getElementById("exitImpersonationBtn").addEventListener("click", () => {
  Auth.restoreAdminToken();
  location.href = "/admin.html";
});
document.getElementById("logoutBtn").addEventListener("click", async () => {
  const button = document.getElementById("logoutBtn");
  button.disabled = true;
  try { await apiCall("/api/auth/logout", { method: "POST", auth: false, timeoutMs: 5000 }); } catch (_) {}
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
    const summary = await apiCall("/api/dashboard/summary");
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
let DISCOVERED_EMBEDDING_MODELS = [];
let DISCOVERED_CUSTOM_MODEL_INFO = Object.create(null);

function formatOpenRouterPrice(value) {
  const price = Number(value);
  if (!Number.isFinite(price) || price < 0) return null;
  const perMillion = price * 1_000_000;
  return `$${perMillion.toLocaleString("en-US", { maximumFractionDigits: 4 })}`;
}

function modelOptionLabel(modelId, info = null) {
  if (!info) return modelId;
  const name = info.name && info.name !== modelId ? `${info.name} (${modelId})` : modelId;
  let priceLabel = "قیمت نامشخص";
  if (info.price_tier === "free") {
    priceLabel = "رایگان";
  } else if (info.price_tier === "paid") {
    const inputPrice = formatOpenRouterPrice(info.prompt_price);
    const outputPrice = formatOpenRouterPrice(info.completion_price);
    if (inputPrice !== null && outputPrice !== null) {
      priceLabel = `${inputPrice}/${outputPrice} دلار به‌ازای هر ۱M توکن (ورودی/خروجی)`;
    } else {
      priceLabel = "پولی";
    }
  }
  const contextLabel = info.context_length
    ? ` · زمینه ${Number(info.context_length).toLocaleString("en-US")}`
    : "";
  return `${name} · ${priceLabel}${contextLabel}`;
}

function fillModelSelect(selectEl, models, selected, modelInfoById = null) {
  selectEl.innerHTML = "";
  (models || []).forEach((model) => {
    const modelId = typeof model === "string" ? model : model && model.id;
    if (!modelId) return;
    const opt = document.createElement("option");
    opt.value = modelId;
    opt.textContent = modelOptionLabel(modelId, modelInfoById && modelInfoById[modelId]);
    if (modelId === selected) opt.selected = true;
    selectEl.appendChild(opt);
  });
  selectEl.disabled = !(models && models.length);
}

function savedModelDeleteButton(kind, entry) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "saved-model-delete-btn";
  button.setAttribute("aria-label", savedChatModelsText(
    `حذف مدل ${entry.model_id}`,
    `Delete model ${entry.model_id}`
  ));
  button.title = savedChatModelsText("حذف این مدل", "Delete this model");
  button.innerHTML = '<span aria-hidden="true">×</span><span class="saved-model-delete-label"></span>';
  button.querySelector(".saved-model-delete-label").textContent = savedChatModelsText("حذف", "Delete");
  button.addEventListener("click", () => deleteSavedModel(kind, entry, button));
  return button;
}

async function deleteSavedModel(kind, entry, button) {
  if (!entry || !entry.model_id || button.disabled) return;
  const isEmbedding = kind === "embedding";
  const params = new URLSearchParams({ model_id: entry.model_id });
  if (isEmbedding) params.set("base_url", entry.base_url || "");
  const endpoint = isEmbedding ? "/api/settings/saved-embedding-models" : "/api/settings/saved-chat-models";
  button.disabled = true;
  button.classList.add("is-deleting");
  button.textContent = savedChatModelsText("در حال حذف…", "Deleting…");
  try {
    await apiCall(`${endpoint}?${params.toString()}`, { method: "DELETE" });
    if (isEmbedding) {
      SAVED_EMBEDDING_MODELS = SAVED_EMBEDDING_MODELS.filter((item) =>
        !(item.model_id === entry.model_id && (item.base_url || "").replace(/\/$/, "") === (entry.base_url || "").replace(/\/$/, ""))
      );
      renderSavedModelList("savedEmbeddingModelsList", "savedEmbeddingModelsCount", SAVED_EMBEDDING_MODELS, "embedding");
    } else {
      SAVED_CHAT_MODELS = SAVED_CHAT_MODELS.filter((item) => item.model_id !== entry.model_id);
      renderSavedChatModels(SAVED_CHAT_MODELS);
      refreshBattleModelOptions();
    }
    toast(savedChatModelsText("مدل از فهرست ذخیره‌شده حذف شد.", "Saved model deleted."), "success");
  } catch (err) {
    toastError(err);
    button.disabled = false;
    button.classList.remove("is-deleting");
    button.innerHTML = '<span aria-hidden="true">×</span><span class="saved-model-delete-label"></span>';
    button.querySelector(".saved-model-delete-label").textContent = savedChatModelsText("حذف", "Delete");
  }
}

function refreshBattleModelOptions() {
  if (!CURRENT_SETTINGS) return;
  const settings = CURRENT_SETTINGS;
  const models = [...new Set(settings.default_chat_models || [])];
  SAVED_CHAT_MODELS.forEach((entry) => {
    if (entry && entry.model_id && !models.includes(entry.model_id)) models.push(entry.model_id);
  });
  // Keep the active custom model selectable even if its reusable saved profile
  // was deleted; deleting a profile must not silently change the active config.
  const activeCustom = !settings.use_default_provider && settings.chat_model ? settings.chat_model : "";
  if (activeCustom && !models.includes(activeCustom)) models.push(activeCustom);
  const selectA = document.getElementById("battleModelA");
  const selectB = document.getElementById("battleModelB");
  const oldA = selectA.value;
  const oldB = selectB.value;
  const fallbackA = (settings.default_chat_models || [])[0] || models[0] || "";
  const fallbackB = activeCustom || (settings.default_chat_models || [])[1] || fallbackA;
  fillModelSelect(selectA, models, models.includes(oldA) ? oldA : fallbackA);
  fillModelSelect(selectB, models, models.includes(oldB) ? oldB : fallbackB);
}

function renderSavedModelList(listId, countId, models, kind = "embedding") {
  const list = document.getElementById(listId);
  const count = document.getElementById(countId);
  if (!list || !count) return;
  list.replaceChildren();
  const unique = new Map();
  (models || []).forEach((entry) => {
    if (!entry || !entry.model_id) return;
    const key = `${entry.model_id}\u0000${entry.base_url || ""}`;
    if (!unique.has(key)) unique.set(key, entry);
  });
  count.textContent = String(unique.size).replace(/[0-9]/g, (digit) => "۰۱۲۳۴۵۶۷۸۹"[Number(digit)]);
  if (!unique.size) {
    const empty = document.createElement("div");
    empty.className = "saved-models-empty-card compact-empty";
    const copy = document.createElement("span");
    copy.textContent = window.QZI18n ? window.QZI18n.t("هنوز مدلی ذخیره نشده است.") : "هنوز مدلی ذخیره نشده است.";
    empty.appendChild(copy);
    list.appendChild(empty);
    return;
  }
  unique.forEach((entry) => {
    const card = document.createElement("article");
    card.className = "saved-model-pill saved-embedding-model-card";
    card.setAttribute("role", "listitem");
    const info = document.createElement("div");
    info.className = "saved-model-pill-info";
    const modelName = document.createElement("strong");
    modelName.textContent = entry.model_id;
    info.appendChild(modelName);
    if (entry.base_url) {
      const provider = document.createElement("small");
      try { provider.textContent = new URL(entry.base_url).host; }
      catch (_) { provider.textContent = entry.base_url; }
      provider.title = entry.base_url;
      info.appendChild(provider);
    }
    card.append(info, savedModelDeleteButton(kind, entry));
    list.appendChild(card);
  });
}

function setProviderMode(useDefault) {
  const checkbox = document.getElementById("useDefaultProviderChk");
  if (checkbox) checkbox.checked = useDefault;
  document.getElementById("defaultProviderInfo").style.display = useDefault ? "block" : "none";
  document.getElementById("customProviderPanel").style.display = useDefault ? "none" : "block";
  const savedChatPanel = document.getElementById("savedChatModelsDetails");
  if (savedChatPanel) savedChatPanel.style.display = useDefault ? "none" : "block";

  const defaultButton = document.getElementById("defaultProviderModeBtn");
  const customButton = document.getElementById("customProviderModeBtn");
  defaultButton.classList.toggle("active", useDefault);
  customButton.classList.toggle("active", !useDefault);
  defaultButton.setAttribute("aria-pressed", String(useDefault));
  customButton.setAttribute("aria-pressed", String(!useDefault));

  // There is one action area after both model selectors. Show only the actions
  // belonging to the chosen chat source, without duplicating controls beside
  // the fields where they interrupt the selection flow.
  ["saveProviderBtn", "testConnectionBtn"].forEach((id) => {
    document.getElementById(id).style.display = useDefault ? "inline-flex" : "none";
  });
  ["saveCustomProviderBtn", "testCustomConnectionBtn"].forEach((id) => {
    document.getElementById(id).style.display = useDefault ? "none" : "inline-flex";
  });

  const badge = document.getElementById("providerStatusBadge");
  badge.textContent = useDefault ? "چت آماده" : "چت اختصاصی";
  badge.className = `badge ${useDefault ? "badge-success" : "badge-accent"}`;
}

function setEmbeddingProviderMode(useDefault) {
  document.getElementById("defaultEmbeddingProviderPanel").style.display = useDefault ? "block" : "none";
  document.getElementById("customEmbeddingProviderPanel").style.display = useDefault ? "none" : "block";
  const savedEmbeddingPanel = document.getElementById("savedEmbeddingModelsDetails");
  if (savedEmbeddingPanel) savedEmbeddingPanel.style.display = useDefault ? "none" : "block";
  const defaultButton = document.getElementById("embeddingDefaultProviderModeBtn");
  const customButton = document.getElementById("embeddingCustomProviderModeBtn");
  defaultButton.classList.toggle("active", useDefault);
  customButton.classList.toggle("active", !useDefault);
  defaultButton.setAttribute("aria-pressed", String(useDefault));
  customButton.setAttribute("aria-pressed", String(!useDefault));
}

const aiTabButtons = Array.from(document.querySelectorAll("#view-ai-settings [data-aitab]"));
function activateAiTab(btn, moveFocus = false) {
  aiTabButtons.forEach((candidate) => {
    const active = candidate === btn;
    candidate.classList.toggle("active", active);
    candidate.setAttribute("aria-selected", String(active));
    candidate.tabIndex = active ? 0 : -1;
  });
  document.getElementById("aitab-connect").classList.toggle("active", btn.dataset.aitab === "connect");
  document.getElementById("aitab-battle").classList.toggle("active", btn.dataset.aitab === "battle");
  if (moveFocus) btn.focus();
}
aiTabButtons.forEach((btn, index) => {
  btn.addEventListener("click", () => activateAiTab(btn));
  btn.addEventListener("keydown", (event) => {
    let nextIndex = index;
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") nextIndex = (index + 1) % aiTabButtons.length;
    else if (event.key === "Home") nextIndex = 0;
    else if (event.key === "End") nextIndex = aiTabButtons.length - 1;
    else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      activateAiTab(btn);
      return;
    } else return;
    event.preventDefault();
    activateAiTab(aiTabButtons[nextIndex], true);
  });
});

document.getElementById("defaultProviderModeBtn").addEventListener("click", () => setProviderMode(true));
document.getElementById("customProviderModeBtn").addEventListener("click", () => setProviderMode(false));
document.getElementById("embeddingDefaultProviderModeBtn").addEventListener("click", () => setEmbeddingProviderMode(true));
document.getElementById("embeddingCustomProviderModeBtn").addEventListener("click", () => setEmbeddingProviderMode(false));

document.getElementById("discoverModelsBtn").addEventListener("click", async () => {
  const btn = document.getElementById("discoverModelsBtn");
  const status = document.getElementById("modelDiscoveryStatus");
  const baseUrl = document.getElementById("baseUrlInput").value.trim();
  const apiKey = document.getElementById("apiKeyInput").value.trim();
  const savedKey = Boolean(CURRENT_SETTINGS && CURRENT_SETTINGS.api_key_set);

  if (!baseUrl) return toast("Chat Base URL را وارد کن.", "error");
  if (!apiKey && !savedKey) return toast("Chat API Key را وارد کن.", "error");

  btn.disabled = true;
  btn.textContent = "در حال دریافت…";
  status.textContent = "در حال دریافت کاتالوگ مدل‌های چت…";
  status.className = "status-line";
  try {
    // Discover chat models separately. Embedding probes can involve dozens of
    // provider calls and are now only performed when the user selects a custom
    // embedding source and presses its dedicated discovery button.
    const result = await apiCall("/api/settings/discover-models", {
      method: "POST",
      body: {
        base_url: baseUrl,
        ...(apiKey ? { api_key: apiKey } : {}),
        discover_embeddings: false,
      },
    });
    const modelCatalog = Array.isArray(result.model_catalog) ? result.model_catalog : [];
    DISCOVERED_CUSTOM_MODEL_INFO = Object.create(null);
    modelCatalog.forEach((entry) => {
      if (entry && entry.id) DISCOVERED_CUSTOM_MODEL_INFO[entry.id] = entry;
    });
    const isOpenRouter = /(^|\.)openrouter\.ai$/i.test(new URL(baseUrl).hostname);
    DISCOVERED_CUSTOM_MODELS = result.chat_models || result.models || [];
    const currentChat = document.getElementById("customChatModelSelect").value;
    fillModelSelect(document.getElementById("customChatModelSelect"), DISCOVERED_CUSTOM_MODELS, currentChat, DISCOVERED_CUSTOM_MODEL_INFO);
    const truncNote = result.chat_candidates_truncated
      ? ` (از مجموع ${result.total_models_found || "؟"} مدل، ${result.chat_candidates_probed || 0} مدل چت تست شد؛ برای سرعت، فقط بخش منتخب کاتالوگ probe شده است)`
      : "";
    if (isOpenRouter && modelCatalog.length) {
      const freeCount = Number(result.free_chat_models_count || 0);
      const paidCount = Number(result.paid_chat_models_count || 0);
      const knownCount = freeCount + paidCount;
      const unknownCount = Math.max(0, DISCOVERED_CUSTOM_MODELS.length - knownCount);
      status.textContent = `کاتالوگ OpenRouter دریافت شد: ${result.total_models_found || modelCatalog.length} مدل در کل • ${DISCOVERED_CUSTOM_MODELS.length} مدل چت قابل انتخاب (${freeCount} رایگان، ${paidCount} پولی${unknownCount ? `، ${unknownCount} با قیمت نامشخص` : ""}). انتخاب embedding جداگانه انجام می‌شود.`;
      status.className = "status-line success-text";
      toast("فهرست مدل‌های چت دریافت شد.", "success");
    } else if (DISCOVERED_CUSTOM_MODELS.length) {
      status.textContent = `${DISCOVERED_CUSTOM_MODELS.length} مدل چت پاسخ‌گو تأیید شد.${truncNote} مدل embedding را جداگانه انتخاب یا کشف کن.`;
      status.className = "status-line success-text";
      toast("فهرست مدل‌های چت دریافت شد.", "success");
    } else {
      status.textContent = "هیچ مدل چتی پیدا نشد. Base URL، کلید API و مجوزهای سرویس را بررسی کن.";
      status.className = "status-line error-text";
      toast("مدل چت قابل استفاده پیدا نشد.", "error");
    }
  } catch (err) {
    DISCOVERED_CUSTOM_MODELS = [];
    DISCOVERED_CUSTOM_MODEL_INFO = Object.create(null);
    fillModelSelect(document.getElementById("customChatModelSelect"), [], "");
    status.textContent = err.message;
    status.className = "status-line error-text";
  } finally {
    btn.disabled = false;
    btn.textContent = "دریافت مدل‌های چت";
  }
});

document.getElementById("discoverEmbeddingModelsBtn").addEventListener("click", async () => {
  const btn = document.getElementById("discoverEmbeddingModelsBtn");
  const status = document.getElementById("embeddingModelDiscoveryStatus");
  const embeddingBaseUrl = document.getElementById("embeddingBaseUrlInput").value.trim();
  const embeddingApiKey = document.getElementById("embeddingApiKeyInput").value.trim();
  const savedKey = Boolean(CURRENT_SETTINGS && CURRENT_SETTINGS.embedding_api_key_set);
  const chatUsesCustomProvider = document.getElementById("customProviderModeBtn").classList.contains("active");
  const savedChatKey = Boolean(CURRENT_SETTINGS && CURRENT_SETTINGS.api_key_set);

  if (!embeddingBaseUrl) return toast("Embedding Base URL را وارد کن.", "error");
  if (!embeddingApiKey && !savedKey && !(chatUsesCustomProvider && savedChatKey)) return toast("Embedding API Key را وارد کن.", "error");

  btn.disabled = true;
  btn.textContent = "در حال دریافت…";
  status.textContent = "در حال بررسی ابعاد مدل‌های Embedding…";
  status.className = "status-line";
  try {
    const result = await apiCall("/api/settings/discover-embedding-models", {
      method: "POST",
      body: {
        base_url: embeddingBaseUrl,
        ...(embeddingApiKey ? { api_key: embeddingApiKey } : {}),
      },
    });
    DISCOVERED_EMBEDDING_MODELS = result.embedding_models || [];
    const currentEmbedding = document.getElementById("customEmbeddingModelSelect").value;
    fillModelSelect(document.getElementById("customEmbeddingModelSelect"), DISCOVERED_EMBEDDING_MODELS, currentEmbedding);
    const dims = (CURRENT_SETTINGS && CURRENT_SETTINGS.embedding_dimensions) || "";
    const truncNote = result.embedding_candidates_truncated
      ? ` (از مجموع ${result.total_models_found || "؟"} مدل، ${result.embedding_candidates_probed || 0} مدل آزمایش شد)`
      : "";
    if (DISCOVERED_EMBEDDING_MODELS.length) {
      status.textContent = `${DISCOVERED_EMBEDDING_MODELS.length} مدل embedding با بُعد ${dims} تأیید شد.${truncNote}`;
      status.className = "status-line success-text";
      toast("مدل‌های embedding سازگار پیدا شد.", "success");
    } else {
      status.textContent = `هیچ مدل embedding سازگار با بُعد ${dims} پیدا نشد.${truncNote}`;
      status.className = "status-line error-text";
      toast("مدل embedding سازگار پیدا نشد.", "error");
    }
  } catch (err) {
    status.textContent = err.message;
    status.className = "status-line error-text";
  } finally {
    btn.disabled = false;
    btn.textContent = "دریافت مدل‌های Embedding";
  }
});

function savedChatModelsText(fa, en) {
  if (window.QZI18n && typeof window.QZI18n.t === "function") {
    const translated = window.QZI18n.t(fa);
    if (translated !== fa) return translated;
  }
  if (window.QZSettings && typeof window.QZSettings.isEnglish === "function" && window.QZSettings.isEnglish()) {
    return en || fa;
  }
  return fa;
}

function renderSavedChatModels(models, loadError = null) {
  const list = document.getElementById("savedChatModelsList");
  const count = document.getElementById("savedChatModelsCount");
  if (!list || !count) return;

  list.replaceChildren();
  const unique = new Map();
  (models || []).forEach((entry) => {
    if (!entry || !entry.model_id) return;
    const key = `${entry.model_id}\u0000${entry.base_url || ""}`;
    if (!unique.has(key)) unique.set(key, entry);
  });
  count.textContent = String(unique.size).replace(/[0-9]/g, (digit) => "۰۱۲۳۴۵۶۷۸۹"[Number(digit)]);

  if (loadError) {
    const state = document.createElement("div");
    state.className = "saved-chat-models-error-card";
    state.setAttribute("role", "alert");
    const icon = document.createElement("span");
    icon.className = "saved-chat-models-error-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "!";
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = savedChatModelsText("فهرست مدل‌های ذخیره‌شده بارگذاری نشد.", "Saved models could not be loaded.");
    const message = document.createElement("p");
    message.textContent = loadError;
    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "saved-chat-models-retry";
    retry.textContent = savedChatModelsText("تلاش دوباره", "Retry");
    retry.addEventListener("click", loadSavedChatModels);
    copy.append(title, message, retry);
    state.append(icon, copy);
    list.appendChild(state);
    return;
  }

  if (!unique.size) {
    const empty = document.createElement("div");
    empty.className = "saved-models-empty-card";
    const icon = document.createElement("span");
    icon.className = "saved-models-empty-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "+";
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = savedChatModelsText("هنوز مدلی ذخیره نشده است.", "No chat models saved yet.");
    const tip = document.createElement("p");
    tip.textContent = savedChatModelsText(
      "Base URL و API Key را وارد کن، مدل‌ها را دریافت کن و سپس تنظیمات را ذخیره کن.",
      "Enter a Base URL and API key, discover the models, then save the settings."
    );
    copy.append(title, tip);
    empty.append(icon, copy);
    list.appendChild(empty);
    return;
  }

  unique.forEach((entry) => {
    const card = document.createElement("article");
    card.className = "saved-chat-model-card";
    card.setAttribute("role", "listitem");

    const top = document.createElement("div");
    top.className = "saved-chat-model-card-top";
    const icon = document.createElement("span");
    icon.className = "saved-chat-model-card-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "AI";
    const name = document.createElement("strong");
    name.className = "saved-chat-model-card-name";
    name.textContent = entry.model_id;
    const badge = document.createElement("span");
    badge.className = "saved-chat-model-card-badge";
    badge.textContent = savedChatModelsText("ذخیره‌شده", "Saved");
    top.append(icon, name, badge);
    card.appendChild(top);

    if (entry.base_url) {
      const provider = document.createElement("div");
      provider.className = "saved-chat-model-card-provider";
      const label = document.createElement("span");
      label.textContent = savedChatModelsText("سرویس", "Provider");
      const url = document.createElement("code");
      url.title = entry.base_url;
      try {
        const parsed = new URL(entry.base_url);
        url.textContent = parsed.host + (parsed.pathname !== "/" ? parsed.pathname.replace(/\/$/, "") : "");
      } catch (_) {
        url.textContent = entry.base_url;
      }
      provider.append(label, url);
      card.appendChild(provider);
    }
    const actions = document.createElement("div");
    actions.className = "saved-chat-model-card-actions";
    actions.appendChild(savedModelDeleteButton("chat", entry));
    card.appendChild(actions);
    list.appendChild(card);
  });
}

async function loadSavedChatModels() {
  let loadError = null;
  try {
    SAVED_CHAT_MODELS = await apiCall("/api/settings/saved-chat-models");
    if (!Array.isArray(SAVED_CHAT_MODELS)) SAVED_CHAT_MODELS = [];
  } catch (err) {
    SAVED_CHAT_MODELS = [];
    loadError = err && err.message ? err.message : savedChatModelsText("خطا در دریافت فهرست مدل‌ها.", "Could not load saved models.");
  }
  renderSavedChatModels(SAVED_CHAT_MODELS, loadError);
}

async function loadSavedEmbeddingModels() {
  try {
    SAVED_EMBEDDING_MODELS = await apiCall("/api/settings/saved-embedding-models");
    if (!Array.isArray(SAVED_EMBEDDING_MODELS)) SAVED_EMBEDDING_MODELS = [];
  } catch (_) {
    SAVED_EMBEDDING_MODELS = [];
  }
  renderSavedModelList("savedEmbeddingModelsList", "savedEmbeddingModelsCount", SAVED_EMBEDDING_MODELS, "embedding");
}

async function loadProviderSettings() {
  try {
    const s = await apiCall("/api/settings");
    CURRENT_SETTINGS = s;
    await Promise.all([loadSavedChatModels(), loadSavedEmbeddingModels()]);
    const savedBattleA = document.getElementById("battleModelA").value;
    const savedBattleB = document.getElementById("battleModelB").value;

    document.getElementById("baseUrlInput").value = s.base_url || "";
    const apiInput = document.getElementById("apiKeyInput");
    apiInput.value = "";
    apiInput.placeholder = s.api_key_set ? "•••••••• (کلید ذخیره شده — برای تغییر دوباره وارد کن)" : "sk-...";
    document.getElementById("apiKeyStatusHint").textContent = s.api_key_set
      ? "کلید چت ذخیره شده است؛ برای امنیت نمایش داده نمی‌شود."
      : "کلید چت ذخیره نشده است.";

    document.getElementById("embeddingBaseUrlInput").value = s.embedding_base_url || "";
    const embeddingKeyInput = document.getElementById("embeddingApiKeyInput");
    embeddingKeyInput.value = "";
    embeddingKeyInput.placeholder = s.embedding_api_key_set ? "•••••••• (کلید ذخیره شده — برای تغییر دوباره وارد کن)" : "sk-...";
    document.getElementById("embeddingApiKeyStatusHint").textContent = s.embedding_api_key_set
      ? "کلید embedding ذخیره شده است؛ برای امنیت نمایش داده نمی‌شود."
      : "برای embedding اختصاصی کلید وارد کن؛ اگر endpoint و کلید چت یکی هستند، می‌توان از کلید چت هم استفاده کرد.";

    const chatUsesDefault = Boolean(s.use_default_provider);
    const embeddingUsesDefault = s.embedding_use_default_provider == null
      ? chatUsesDefault
      : Boolean(s.embedding_use_default_provider);
    setProviderMode(chatUsesDefault);
    setEmbeddingProviderMode(embeddingUsesDefault);

    fillModelSelect(document.getElementById("chatModelSelect"), s.default_chat_models, chatUsesDefault ? s.chat_model : (s.default_chat_models || [])[0]);
    fillModelSelect(document.getElementById("embeddingModelSelect"), s.default_embedding_models, embeddingUsesDefault ? s.embedding_model : (s.default_embedding_models || [])[0]);

    const battleModels = [...new Set(s.default_chat_models || [])];
    SAVED_CHAT_MODELS.forEach((entry) => {
      if (entry && entry.model_id && !battleModels.includes(entry.model_id)) battleModels.push(entry.model_id);
    });
    const savedCustomModel = !chatUsesDefault && s.chat_model ? s.chat_model : "";
    if (savedCustomModel && !battleModels.includes(savedCustomModel)) battleModels.push(savedCustomModel);
    const fallbackA = (s.default_chat_models || [])[0] || battleModels[0] || "";
    const fallbackB = savedCustomModel || (s.default_chat_models || [])[1] || fallbackA;
    fillModelSelect(document.getElementById("battleModelA"), battleModels, battleModels.includes(savedBattleA) ? savedBattleA : fallbackA);
    fillModelSelect(document.getElementById("battleModelB"), battleModels, battleModels.includes(savedBattleB) ? savedBattleB : fallbackB);

    fillModelSelect(document.getElementById("customChatModelSelect"), !chatUsesDefault && s.chat_model ? [s.chat_model] : [], s.chat_model);
    fillModelSelect(document.getElementById("customEmbeddingModelSelect"), !embeddingUsesDefault && s.embedding_model ? [s.embedding_model] : [], s.embedding_model);
    DISCOVERED_CUSTOM_MODELS = [];
    DISCOVERED_EMBEDDING_MODELS = [];
    DISCOVERED_CUSTOM_MODEL_INFO = Object.create(null);
    document.getElementById("modelDiscoveryStatus").textContent = chatUsesDefault ? "" : "برای دریافت مدل‌های چت این اتصال، روی «دریافت مدل‌های چت» بزن.";
    document.getElementById("modelDiscoveryStatus").className = "status-line";
    document.getElementById("embeddingModelDiscoveryStatus").textContent = embeddingUsesDefault ? "" : "برای یافتن مدل embedding سازگار، روی «دریافت مدل‌های Embedding» بزن.";
    document.getElementById("embeddingModelDiscoveryStatus").className = "status-line";
  } catch (err) {
    toastError(err);
  }
}

async function saveProvider(payload, successMessage, reload = true) {
  await apiCall("/api/settings", { method: "PUT", body: payload });
  if (successMessage) toast(successMessage, "success");
  if (reload) await loadProviderSettings();
}

async function saveSelectedProvider(button) {
  const chatUsesDefault = document.getElementById("defaultProviderModeBtn").classList.contains("active");
  const embeddingUsesDefault = document.getElementById("embeddingDefaultProviderModeBtn").classList.contains("active");
  const baseUrl = document.getElementById("baseUrlInput").value.trim();
  const apiKey = document.getElementById("apiKeyInput").value.trim();
  const embeddingBaseUrl = document.getElementById("embeddingBaseUrlInput").value.trim();
  const embeddingApiKey = document.getElementById("embeddingApiKeyInput").value.trim();
  const chatModel = chatUsesDefault
    ? document.getElementById("chatModelSelect").value
    : document.getElementById("customChatModelSelect").value;
  const embeddingModel = embeddingUsesDefault
    ? document.getElementById("embeddingModelSelect").value
    : document.getElementById("customEmbeddingModelSelect").value;

  if (!chatUsesDefault) {
    if (!baseUrl) return toast("Chat Base URL را وارد کن.", "error");
    if (!apiKey && !(CURRENT_SETTINGS && CURRENT_SETTINGS.api_key_set)) return toast("Chat API Key را وارد کن.", "error");
    if (!chatModel) return toast("ابتدا مدل‌های چت را دریافت و یک مدل انتخاب کن.", "error");
  }
  if (embeddingUsesDefault) {
    if (!embeddingModel) return toast("یک مدل embedding آماده انتخاب کن.", "error");
  } else {
    if (!embeddingBaseUrl) return toast("Embedding Base URL را وارد کن.", "error");
    const savedEmbeddingKey = Boolean(CURRENT_SETTINGS && CURRENT_SETTINGS.embedding_api_key_set);
    const savedChatKey = Boolean(CURRENT_SETTINGS && CURRENT_SETTINGS.api_key_set);
    if (!embeddingApiKey && !savedEmbeddingKey && (chatUsesDefault || (!apiKey && !savedChatKey))) {
      return toast("Embedding API Key را وارد کن.", "error");
    }
    if (!embeddingModel) return toast("ابتدا مدل‌های embedding را دریافت و مدلی سازگار انتخاب کن.", "error");
  }

  const payload = {
    use_default_provider: chatUsesDefault,
    embedding_use_default_provider: embeddingUsesDefault,
    // Keep a saved custom embedding endpoint/key when temporarily switching to
    // the ready embedding source; only set the separate-provider flag in custom mode.
    ...(!embeddingUsesDefault ? { separate_embedding_provider: true } : {}),
    chat_model: chatModel,
    embedding_model: embeddingModel,
  };
  if (baseUrl) payload.base_url = baseUrl;
  if (apiKey) payload.api_key = apiKey;
  if (!embeddingUsesDefault && embeddingBaseUrl) payload.embedding_base_url = embeddingBaseUrl;
  if (!embeddingUsesDefault && embeddingApiKey) payload.embedding_api_key = embeddingApiKey;

  button.disabled = true;
  const oldText = button.textContent;
  button.textContent = "در حال ذخیره…";
  try {
    // Preserve the previously active custom model before the single active
    // settings row is overwritten by a newly selected model/provider.
    if (CURRENT_SETTINGS && !CURRENT_SETTINGS.use_default_provider && CURRENT_SETTINGS.chat_model && CURRENT_SETTINGS.base_url) {
      const previousModel = CURRENT_SETTINGS.chat_model;
      const previousBaseUrl = CURRENT_SETTINGS.base_url;
      const changingProfile = chatUsesDefault || previousModel !== chatModel || previousBaseUrl !== baseUrl;
      if (changingProfile) {
        await apiCall("/api/settings/saved-chat-models", {
          method: "POST",
          body: { model_id: previousModel, base_url: previousBaseUrl },
        });
      }
    }
    // Persist the chosen model profile first. If the saved-model table is not
    // present in Supabase, stop here with an actionable error instead of showing
    // a successful settings toast and failing afterwards.
    if (!chatUsesDefault && chatModel && baseUrl) {
      await apiCall("/api/settings/saved-chat-models", {
        method: "POST",
        body: { model_id: chatModel, base_url: baseUrl, ...(apiKey ? { api_key: apiKey } : {}) },
      });
    }
    await saveProvider(payload, null, false);
    if (!embeddingUsesDefault && embeddingModel && (embeddingBaseUrl || baseUrl)) {
      // Save the exact selected embedding profile. Do not reconstruct it from
      // CURRENT_SETTINGS: the just-selected provider may differ from the old one.
      await apiCall("/api/settings/saved-embedding-models", {
        method: "POST",
        body: {
          model_id: embeddingModel,
          base_url: embeddingBaseUrl || baseUrl,
          ...((embeddingApiKey || apiKey) ? { api_key: embeddingApiKey || apiKey } : {}),
        },
      });
    }
    await loadProviderSettings();
    toast("تنظیمات ذخیره شد؛ مدل اختصاصی هم به فهرست مدل‌های ذخیره‌شده اضافه شد.", "success");
  } catch (err) {
    toastError(err);
  } finally {
    button.disabled = false;
    button.textContent = oldText;
  }
}

document.getElementById("saveProviderBtn").addEventListener("click", function () {
  saveSelectedProvider(this);
});
document.getElementById("saveCustomProviderBtn").addEventListener("click", function () {
  saveSelectedProvider(this);
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
      body: {
        base_url: baseUrl,
        chat_model: chatModel,
        embedding_model: document.getElementById("embeddingDefaultProviderModeBtn").classList.contains("active")
          ? document.getElementById("embeddingModelSelect").value
          : document.getElementById("customEmbeddingModelSelect").value,
        embedding_use_default_provider: document.getElementById("embeddingDefaultProviderModeBtn").classList.contains("active"),
        separate_embedding_provider: document.getElementById("embeddingCustomProviderModeBtn").classList.contains("active"),
        ...(document.getElementById("embeddingBaseUrlInput").value.trim() ? { embedding_base_url: document.getElementById("embeddingBaseUrlInput").value.trim() } : {}),
        ...(document.getElementById("embeddingApiKeyInput").value.trim() ? { embedding_api_key: document.getElementById("embeddingApiKeyInput").value.trim() } : {}),
        ...(apiKey ? { api_key: apiKey } : {}),
      },
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
  const modelA = document.getElementById("battleModelA").value;
  const modelB = document.getElementById("battleModelB").value;
  const waiting = window.QZI18n ? window.QZI18n.t("در حال دریافت پاسخ…") : "در حال دریافت پاسخ…";
  const modelNames = [modelA, modelB];
  resultsBox.style.display = "grid";
  resultsBox.innerHTML = modelNames.map((model, index) => {
    const side = index === 0 ? "a" : "b";
    return `<div class="battle-side">
      <div class="model-name">${escapeHtml(model)}</div>
      <div class="reply-text" id="battleReply${side.toUpperCase()}">${escapeHtml(waiting)}</div>
      <div class="timing" id="battleTiming${side.toUpperCase()}">—</div>
    </div>`;
  }).join("");

  const payload = { prompt, model_a: modelA, model_b: modelB };
  const updateSide = (side, data) => {
    const key = String(side || "").toUpperCase();
    const reply = document.getElementById(`battleReply${key}`);
    const timing = document.getElementById(`battleTiming${key}`);
    if (!reply || !timing) return;
    if (data.error) {
      if (reply.textContent === waiting) reply.textContent = "";
      const error = document.createElement("span");
      error.className = "battle-error";
      error.textContent = data.error;
      reply.appendChild(error);
    } else if (reply.textContent === waiting) {
      reply.textContent = "";
      if (!data.hasText) reply.textContent = window.QZI18n ? window.QZI18n.t("پاسخی دریافت نشد.") : "پاسخی دریافت نشد.";
    }
    if (typeof data.elapsed_ms === "number") timing.textContent = `⏱ ${data.elapsed_ms}ms`;
    reply.closest(".battle-side")?.classList.remove("is-streaming");
  };

  try {
    await apiStream("/api/playground/battle/stream", {
      body: payload,
      idleTimeoutMs: 0,
      onEvent(event, data) {
        if (event === "delta" && (data.side === "a" || data.side === "b")) {
          const reply = document.getElementById(`battleReply${data.side.toUpperCase()}`);
          if (reply) {
            if (reply.textContent === waiting) reply.textContent = "";
            reply.textContent += data.t || "";
          }
        } else if (event === "side_done" && (data.side === "a" || data.side === "b")) {
          const reply = document.getElementById(`battleReply${data.side.toUpperCase()}`);
          updateSide(data.side, { ...data, hasText: Boolean(reply && reply.textContent && reply.textContent !== waiting) });
        }
      },
    });
  } catch (err) {
    if (STREAM_FALLBACK_STATUSES.includes(err?.status)) {
      try {
        const res = await apiCall("/api/playground/battle", { method: "POST", body: payload });
        [res.side_a, res.side_b].forEach((side, index) => {
          const key = index === 0 ? "a" : "b";
          const reply = document.getElementById(`battleReply${key.toUpperCase()}`);
          if (reply) reply.textContent = side.error || side.reply || (window.QZI18n ? window.QZI18n.t("پاسخی دریافت نشد.") : "پاسخی دریافت نشد.");
          updateSide(key, { error: null, elapsed_ms: side.elapsed_ms, hasText: Boolean(side.reply) });
          if (side.error && reply) reply.textContent = side.error;
        });
      } catch (fallbackErr) {
        toastError(fallbackErr);
      }
    } else {
      toastError(err);
    }
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
  const progress = document.getElementById("docIndexProgress");
  if (progress) {
    progress.hidden = true;
    progress.classList.remove("error");
  }
  stopDocProgressEstimator();
  clearDocProgressTipTimer();
  DOC_PROGRESS_TOKEN += 1;
  DOC_PROGRESS_PERCENT = 0;
  DOC_PROGRESS_BASE_MESSAGE = "";
  DOC_PROGRESS_TIP_INDEX = 0;
  const progressBar = document.getElementById("docIndexProgressBar");
  const progressPercent = document.getElementById("docIndexProgressPercent");
  if (progressBar) progressBar.style.width = "0%";
  if (progressPercent) progressPercent.textContent = window.QZSettings && window.QZSettings.isEnglish() ? "0%" : "0٪";
  document.getElementById("docModal").classList.add("show");
}
function closeDocModal() {
  stopDocProgressEstimator();
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

const DOC_PROGRESS_TIPS = [
  "نکته: جست‌وجوی معنایی فقط دنبال کلمهٔ دقیق نمی‌گردد؛ مفهوم سؤال را هم در نظر می‌گیرد.",
  "یادآوری: بعد از ایندکس، پاسخ‌های تست و ویجت می‌توانند از همین دانشنامه استفاده کنند.",
  "نکته: هرچه متن سند منظم‌تر و بخش‌بندی‌شده‌تر باشد، بازیابی اطلاعات دقیق‌تر می‌شود.",
  "قابلیت جالب: مدل می‌تواند از چند بخش مرتبط سند، یک پاسخ یکپارچه بسازد.",
  "پشت صحنه: برای هر بخش، یک نمایش عددی ساخته می‌شود تا پیدا کردن اطلاعات مرتبط سریع شود.",
];
let DOC_PROGRESS_TIMER = null;
let DOC_PROGRESS_ESTIMATOR_TIMER = null;
let DOC_PROGRESS_ESTIMATOR_STARTED_AT = 0;
let DOC_PROGRESS_TIP_INDEX = 0;
let DOC_PROGRESS_TOKEN = 0;
let DOC_PROGRESS_PERCENT = 0;
let DOC_PROGRESS_BASE_MESSAGE = "";

function clearDocProgressTipTimer() {
  if (DOC_PROGRESS_TIMER) {
    clearTimeout(DOC_PROGRESS_TIMER);
    DOC_PROGRESS_TIMER = null;
  }
}

function stopDocProgressEstimator() {
  if (DOC_PROGRESS_ESTIMATOR_TIMER) {
    clearInterval(DOC_PROGRESS_ESTIMATOR_TIMER);
    DOC_PROGRESS_ESTIMATOR_TIMER = null;
  }
  DOC_PROGRESS_ESTIMATOR_STARTED_AT = 0;
}

function paintDocProgressPercent(percent) {
  const safePercent = Math.max(0, Math.min(100, Math.round(percent)));
  DOC_PROGRESS_PERCENT = safePercent;
  const percentEl = document.getElementById("docIndexProgressPercent");
  const bar = document.getElementById("docIndexProgressBar");
  const percentSymbol = window.QZSettings && window.QZSettings.isEnglish() ? "%" : "٪";
  if (percentEl) percentEl.textContent = `${safePercent}${percentSymbol}`;
  if (bar) bar.style.width = `${safePercent}%`;
}

function startDocProgressEstimator() {
  stopDocProgressEstimator();
  DOC_PROGRESS_ESTIMATOR_STARTED_AT = Date.now();
  DOC_PROGRESS_ESTIMATOR_TIMER = setInterval(() => {
    if (DOC_PROGRESS_PERCENT >= 100) {
      stopDocProgressEstimator();
      return;
    }
    const elapsedSeconds = Math.max(0, (Date.now() - DOC_PROGRESS_ESTIMATOR_STARTED_AT) / 1000);
    // Rise gradually while a batch is in-flight, then plateau below 90% until the server confirms completion.
    const estimated = Math.min(89, Math.floor(89 * (1 - Math.exp(-elapsedSeconds / 35))));
    if (estimated > DOC_PROGRESS_PERCENT) paintDocProgressPercent(estimated);
  }, 500);
}

function scheduleDocProgressTips() {
  clearDocProgressTipTimer();
  if (DOC_PROGRESS_PERCENT >= 100) return;
  const token = ++DOC_PROGRESS_TOKEN;
  DOC_PROGRESS_TIMER = setTimeout(() => {
    if (token !== DOC_PROGRESS_TOKEN || DOC_PROGRESS_PERCENT >= 100) return;
    const title = document.getElementById("docIndexProgressTitle");
    if (!title) return;
    DOC_PROGRESS_TIP_INDEX = (DOC_PROGRESS_TIP_INDEX + 1) % DOC_PROGRESS_TIPS.length;
    title.classList.add("swap");
    setTimeout(() => {
      if (token !== DOC_PROGRESS_TOKEN || DOC_PROGRESS_PERCENT >= 100) return;
      title.textContent = DOC_PROGRESS_TIPS[DOC_PROGRESS_TIP_INDEX];
      title.classList.remove("swap");
      DOC_PROGRESS_TIMER = setTimeout(() => {
        if (token !== DOC_PROGRESS_TOKEN || DOC_PROGRESS_PERCENT >= 100) return;
        title.classList.add("swap");
        setTimeout(() => {
          if (token !== DOC_PROGRESS_TOKEN || DOC_PROGRESS_PERCENT >= 100) return;
          title.textContent = DOC_PROGRESS_BASE_MESSAGE;
          title.classList.remove("swap");
          scheduleDocProgressTips();
        }, 220);
      }, 4200);
    }, 220);
  }, 5500);
}

function setDocIndexProgress(percent, message, error = false) {
  const host = document.getElementById("docIndexProgress");
  if (!host) return;
  const title = document.getElementById("docIndexProgressTitle");
  const percentEl = document.getElementById("docIndexProgressPercent");
  const bar = document.getElementById("docIndexProgressBar");
  const requestedPercent = Math.max(0, Math.min(100, Math.round(percent || 0)));
  const safePercent = requestedPercent >= 100
    ? 100
    : Math.max(DOC_PROGRESS_PERCENT, Math.min(99, requestedPercent));
  DOC_PROGRESS_PERCENT = safePercent;
  if (safePercent >= 100) stopDocProgressEstimator();
  DOC_PROGRESS_BASE_MESSAGE = message || "در حال پردازش سند…";
  host.hidden = false;
  host.classList.toggle("error", Boolean(error));
  if (title) {
    title.classList.remove("swap");
    title.textContent = DOC_PROGRESS_BASE_MESSAGE;
  }
  const percentSymbol = window.QZSettings && window.QZSettings.isEnglish() ? "%" : "٪";
  if (percentEl) percentEl.textContent = `${safePercent}${percentSymbol}`;
  if (bar) bar.style.width = `${safePercent}%`;
  DOC_PROGRESS_TOKEN += 1;
  scheduleDocProgressTips();
}


document.getElementById("saveDocBtn").addEventListener("click", async () => {
  const title = document.getElementById("docTitleInput").value.trim();
  const content = document.getElementById("docContentInput").value.trim();
  if (!title || !content) return toast("عنوان و محتوا را پر کن.", "error");

  const btn = document.getElementById("saveDocBtn");
  const closeBtn = document.getElementById("closeDocModalBtn");
  btn.disabled = true;
  if (closeBtn) closeBtn.disabled = true;

  try {
    if (EDITING_DOC_ID) {
      // ویرایش سند همان مسیر قبلی را حفظ می‌کند؛ این نوار مخصوص «افزودن سند جدید» است.
      btn.textContent = "در حال ذخیره…";
      await apiCall(`/api/knowledge/documents/${EDITING_DOC_ID}`, { method: "PUT", timeoutMs: 0, body: { title, content } });
      toast("سند بروزرسانی شد.", "success");
      closeDocModal();
      loadDocuments();
      return;
    }

    setDocIndexProgress(0, "در حال آماده‌سازی سند…");
    startDocProgressEstimator();
    btn.textContent = "در حال تبدیل و ایندکس…";

    await apiStream("/api/knowledge/documents/stream", {
      body: { title, content },
      idleTimeoutMs: 0,
      onMeta(data) {
        if (data && typeof data.progress === "number") {
          setDocIndexProgress(data.progress, data.message || "در حال ذخیره و ایندکس سند…");
        }
      },
    });

    setDocIndexProgress(100, "همه بخش‌های سند با موفقیت ذخیره شد؛ دانشنامه آماده است ✓");
    toast("سند اضافه و ایندکس شد.", "success");
    await new Promise((resolve) => setTimeout(resolve, 850));
    closeDocModal();
    loadDocuments();
  } catch (err) {
    stopDocProgressEstimator();
    setDocIndexProgress(DOC_PROGRESS_PERCENT, err && err.message ? err.message : "ایندکس سند ناموفق بود.", true);
    toastError(err);
  } finally {
    stopDocProgressEstimator();
    btn.disabled = false;
    if (closeBtn) closeBtn.disabled = false;
    btn.textContent = "ذخیره و ایندکس‌کردن";
  }
});


// ---------------------------------------------------------------------------
// ایمپورت فایل (PDF، Word، Excel، PowerPoint، ...) → متن → دانشنامه
// ---------------------------------------------------------------------------
function ensureOperationProgress(title = "در حال پردازش…") {
  const host = document.getElementById("operationProgress");
  const titleEl = host ? host.querySelector(".operation-progress-title") : null;
  const bar = host ? host.querySelector(".operation-progress-bar > span") : null;
  const percentEl = host ? host.querySelector(".operation-progress-percent") : null;
  const existing = {
    set(percent, label) {
      if (!host) return;
      host.hidden = false;
      if (titleEl) titleEl.textContent = label || title;
      if (bar) bar.style.width = `${Math.max(0, Math.min(100, percent))}%`;
      if (percentEl) percentEl.textContent = `${Math.round(percent)}${window.QZSettings && window.QZSettings.isEnglish() ? "%" : "٪"}`;
    },
    fail() { host?.classList.add("error"); },
    finish() { if (!host) return; setTimeout(() => { host.hidden = true; host.classList.remove("error"); }, 900); },
  };
  existing.set(0, title);
  return existing;
}

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
  const progress = ensureOperationProgress(`در حال وارد کردن ${files.length} فایل…`);
  let completedFiles = 0;
  try {
    try {
      await Lazy.script("/assets/js/extract.js?v=2.8.9");
    } catch (err) {
      return toastError(err);
    }
    for (const file of files) {
      const row = addImportRow(file.name);
      progress.set(Math.round((completedFiles / files.length) * 100), `در حال خواندن ${file.name}`);
      try {
        row.set("در حال خواندن…", "work");
        const { title, text } = await FileExtract.extract(file, (page, total) => {
          row.set(`خواندن صفحه ${page} از ${total}…`, "work");
          const base = (completedFiles / files.length) * 100;
          const share = total ? (page / total) * (100 / files.length) : 0;
          progress.set(Math.min(99, base + share), `خواندن ${file.name}`);
        });

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
          const base = (completedFiles / files.length) * 100;
          const share = ((i + 1) / parts.length) * (100 / files.length);
          progress.set(Math.min(99, base + share), `ایندکس ${file.name}`);
          await apiCall("/api/knowledge/documents", { method: "POST", timeoutMs: 0, body: { title: docTitle.slice(0, 200), content: parts[i] } });
          imported += 1;
        }
        const englishUI = !!(window.QZSettings && window.QZSettings.isEnglish());
        row.set(parts.length > 1
          ? (englishUI ? `✓ ${parts.length} sections added` : `✓ ${parts.length} بخش اضافه شد`)
          : (englishUI ? "✓ Added" : "✓ اضافه شد"), "ok");
        completedFiles += 1;
        progress.set(Math.round((completedFiles / files.length) * 100), `${completedFiles} از ${files.length} فایل انجام شد`);
        row.done();
      } catch (err) {
        row.set(err && err.message ? err.message : "ناموفق", "error");
        completedFiles += 1;
        progress.set(Math.round((completedFiles / files.length) * 100), `${completedFiles} از ${files.length} فایل`);
      }
    }
  } finally {
    progress.set(100, imported ? "پردازش همه فایل‌ها تمام شد" : "پردازش تمام شد");
    progress.finish();
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
    await loadSavedChatModels();
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
  el.dataset.runtimeMessage = "1";
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
  const requestId = err && err.requestId ? `\n${window.QZI18n ? window.QZI18n.t("شناسه درخواست:") : "Request ID:"} ${err.requestId}` : "";
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
  let gotDelta = false;
  let frame = null;
  const paint = () => {
    frame = null;
    bubble.textContent = text;
    const stream = document.getElementById("chatStream");
    if (!window.QZSettings || window.QZSettings.get("autoScroll") !== false) stream.scrollTop = stream.scrollHeight;
  };
  CHAT_ABORT = new AbortController();
  try {
    await apiStream("/api/playground/chat/stream", {
      signal: CHAT_ABORT.signal,
      body: { message, session_id: CHAT_SESSION_ID, ...(selectedModel ? { model: selectedModel } : {}) },
      onMeta: (meta) => {
        CHAT_SESSION_ID = meta.session_id;
        const badge = document.getElementById("activeChatModelBadge"); if (badge) { badge.textContent = meta.model || selectedModel || "—"; badge.hidden = !!(window.QZSettings && window.QZSettings.get("showModelBadge") === false); }
        renderChatSources(meta.sources);
      },
      onDelta: (piece) => {
        if (!text) {
          bubble.classList.remove("pending");
          bubble.dataset.hasText = "1";
        }
        gotDelta = true;
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
  return { text, gotDelta };
}

// مسیر پشتیبان: یک‌جا (برای سروری که استریم ندارد)
async function chatViaRequest(message, selectedModel, bubble, timeoutMs = 0) {
  const res = await apiCall("/api/playground/chat", {
    method: "POST",
    timeoutMs,
    body: { message, session_id: CHAT_SESSION_ID, ...(selectedModel ? { model: selectedModel } : {}) },
  });
  const reply = typeof res?.reply === "string" ? res.reply.trim() : "";
  if (!reply) {
    const message = "مدل پاسخ متنی برنگرداند. یک بار دیگر تلاش کنید؛ اگر تکرار شد، مدل دیگری را انتخاب یا اتصال API را بررسی کنید.";
    throw new Error(window.QZI18n ? window.QZI18n.t(message) : message);
  }
  CHAT_SESSION_ID = res.session_id;
  bubble.textContent = reply;
  bubble.dataset.hasText = "1";
  bubble.classList.remove("pending");
  const badge = document.getElementById("activeChatModelBadge"); if (badge) { badge.textContent = res.model || selectedModel || "—"; badge.hidden = !!(window.QZSettings && window.QZSettings.get("showModelBadge") === false); }
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
  sendBtn.title = window.QZI18n ? window.QZI18n.t("توقف پاسخ") : "Stop response";
  input.value = "";
  appendChatMsg("user", message);
  const bubble = appendChatMsg("bot", "در حال آماده‌سازی پاسخ…");
  bubble.classList.add("pending", "streaming");

  // همیشه مدل فعلی تنظیمات را صریحاً به backend می‌فرستیم
  const selectedModel = CURRENT_SETTINGS && CURRENT_SETTINGS.chat_model ? CURRENT_SETTINGS.chat_model : undefined;

  try {
    try {
      await PRISMO_RUNTIME_READY;
      if (PRISMO_IS_VERCEL_RUNTIME) {
        // Vercel serverless SSE can send metadata without a text delta. Use the
        // ordinary RAG JSON endpoint with a bounded timeout for this runtime.
        bubble.textContent = window.QZI18n ? window.QZI18n.t("در حال پاسخ…") : "در حال پاسخ…";
        await chatViaRequest(message, selectedModel, bubble, 65000);
      } else if (window.QZSettings && window.QZSettings.get("streaming") === false) {
        await chatViaRequest(message, selectedModel, bubble);
      } else {
        const streamResult = await chatViaStream(message, selectedModel, bubble);
        // اگر اتصال SSE برقرار شد ولی هیچ deltaای نرسید، فقط در همان حالت یک بار fallback می‌کنیم.
        if (streamResult && !streamResult.gotDelta && bubble.dataset.hasText !== "1") {
          await chatViaRequest(message, selectedModel, bubble);
        }
      }
    } catch (err) {
      if (err && err.aborted) {
        // توقف دستی، بدون تبدیل آن به خطای قرمز.
        if (bubble.dataset.hasText !== "1") bubble.textContent = "پاسخ متوقف شد.";
        bubble.classList.remove("pending");
      } else if (PRISMO_IS_VERCEL_RUNTIME || (window.QZSettings && window.QZSettings.get("streaming") === false)) {
        throw err;
      } else if (bubble.dataset.hasText !== "1" && (err?.streamError || STREAM_FALLBACK_STATUSES.includes(err?.status))) {
        // خطای خود Stream را مخفی می‌کنیم و مسیر معمولی را امتحان می‌کنیم.
        await chatViaRequest(message, selectedModel, bubble);
      } else if (bubble.dataset.hasText === "1") {
        // اگر بخشی از پاسخ آمده، آن را نگه می‌داریم و UI را با پیام خطا خراب نمی‌کنیم.
      } else {
        throw err;
      }
    }
  } catch (err) {
    bubble.classList.remove("pending");
    showChatError(bubble, err);
  } finally {
    if (bubble.dataset.hasText === "1" && !(bubble.classList.contains("pending"))) {
      document.dispatchEvent(new CustomEvent("qz-response-complete"));
    }
    CHAT_REQUEST_ACTIVE = false;
    CHAT_ABORT = null;
    bubble.classList.remove("streaming");
    sendBtn.innerHTML = SEND_ICON;
    sendBtn.title = "ارسال";
  }
}
document.getElementById("sendChatBtn").addEventListener("click", sendChatMessage);
document.getElementById("chatInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && (!window.QZSettings || window.QZSettings.get("chatEnterSend") !== false)) {
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
  const btn = widgetEl("saveWidgetBtn");
  btn.classList.toggle("has-changes", dirty);
  btn.title = dirty ? "تغییرات ذخیره‌نشده دارید" : "";
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
  const isEnglish = Boolean(window.QZSettings && window.QZSettings.isEnglish && window.QZSettings.isEnglish());
  const petLabels = isEnglish
    ? { dog: "Dog", cat: "Cat", raccoon: "Raccoon" }
    : QzPets.labels;
  grid.innerHTML = QzPets.names
    .map(
      (name) => `
    <button type="button" class="pet-card${name === selected ? " active" : ""}" data-pet="${name}" role="radio" aria-checked="${name === selected}">
      <span class="pet-thumb">${QzPets.svg(name, "i", color, 4)}</span>
      <span class="pet-name">${petLabels[name] || name}</span>
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
  const theme = document.documentElement.dataset.theme || "dark";
  const language = window.QZSettings && window.QZSettings.isEnglish && window.QZSettings.isEnglish() ? "en" : "fa";
  frame.src = `/widget-preview.html?widget_id=${encodeURIComponent(widgetId)}&theme=${encodeURIComponent(theme)}&language=${language}&v=${Date.now()}`;
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

document.addEventListener("qz-language-change", () => {
  if (CURRENT_SETTINGS) {
    const prompt = document.getElementById("systemPromptInput");
    if (prompt && (prompt.value === "تو یک دستیار هوشمند و مؤدب هستی. پاسخ‌ها را فقط بر اساس دانشنامه ارائه‌شده به کاربر بده. اگر پاسخ در دانشنامه نیست، صادقانه بگو اطلاعات کافی نداری و حدس نزن. پاسخ‌ها را کوتاه، دقیق و به زبان فارسی روان بنویس." || prompt.value === "You are a helpful and polite AI assistant. Answer only from the knowledge base provided to the user. If the answer is not in the knowledge base, say that you do not have enough information and do not guess. Keep answers concise, accurate, and natural in English.")) {
      prompt.value = window.QZSettings && window.QZSettings.isEnglish() ? "You are a helpful and polite AI assistant. Answer only from the knowledge base provided to the user. If the answer is not in the knowledge base, say that you do not have enough information and do not guess. Keep answers concise, accurate, and natural in English." : "تو یک دستیار هوشمند و مؤدب هستی. پاسخ‌ها را فقط بر اساس دانشنامه ارائه‌شده به کاربر بده. اگر پاسخ در دانشنامه نیست، صادقانه بگو اطلاعات کافی نداری و حدس نزن. پاسخ‌ها را کوتاه، دقیق و به زبان فارسی روان بنویس.";
    }
    if (window.QzPets && widgetEl("petGrid")) {
      const activePet = document.querySelector("#petGrid .pet-card.active");
      renderPetGrid(activePet ? activePet.dataset.pet : "dog", widgetEl("petColorInput").value);
    }
  }
  if (LAST_WIDGET_ID) renderWidgetPreview(LAST_WIDGET_ID);
  renderEmbedCode();
});

function renderEmbedCode() {
  if (!EMBED_TEMPLATE) return;
  const box = widgetEl("embedCodeBox");
  if (!box) return;
  const language = window.QZSettings && window.QZSettings.isEnglish && window.QZSettings.isEnglish() ? "en" : "fa";
  const code = EMBED_TEMPLATE.replaceAll("__BASE_URL__", window.location.origin).replaceAll("__LANGUAGE__", language).replace(/data-theme="[^"]*"/, `data-theme="${EMBED_THEME}"`);
  box.textContent = code;
}

async function loadWidgetSection() {
  const english = Boolean(window.QZSettings && window.QZSettings.isEnglish && window.QZSettings.isEnglish());
  const embedCodeBox = widgetEl("embedCodeBox");
  // .embed-code-box is intentionally excluded from the generic translation
  // observer because its final content is executable code. Localize its
  // initial loading label here instead of relying on DOM text translation.
  if (embedCodeBox) embedCodeBox.textContent = english ? "Loading…" : "در حال بارگذاری…";
  try {
    setWidgetPreviewLoading(true);
    const [cfg, embed] = await Promise.all([
      apiCall("/api/widget/config"),
      apiCall("/api/widget/embed-code"),
      Lazy.script("/assets/js/pets.js?v=2.8.9").catch(() => null), // اگر نیامد، فقط انتخابگر حیوان خالی می‌ماند
    ]);
    const ex = cfg.extras || {};
    const pet = ex.pet || "dog";
    const isEn = window.QZSettings && window.QZSettings.isEnglish && window.QZSettings.isEnglish();
    const defaultTitleFa = "دستیار هوشمند", defaultTitleEn = "Smart Assistant";
    const defaultWelcomeFa = "سلام! چطور می‌تونم کمکتون کنم؟", defaultWelcomeEn = "Hello! How can I help you?";
    widgetEl("widgetTitleInput").value = (cfg.widget_title === defaultTitleFa || cfg.widget_title === defaultTitleEn) ? (isEn ? defaultTitleEn : defaultTitleFa) : cfg.widget_title;
    widgetEl("widgetWelcomeInput").value = (cfg.widget_welcome_message === defaultWelcomeFa || cfg.widget_welcome_message === defaultWelcomeEn) ? (isEn ? defaultWelcomeEn : defaultWelcomeFa) : cfg.widget_welcome_message;
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
      toast("ذخیره‌ی حیوان خانگی و پاسخ‌های سریع نیاز به یک‌بار اجرای migration شماره‌ی ۰۰۲ دارد.", "error");
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
  const box = widgetEl("embedCodeBox");
  if (!box) return toast("بخش کد امبد در دسترس نیست.", "error");
  const text = box.textContent;
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
