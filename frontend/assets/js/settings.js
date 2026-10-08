/* مرکز تنظیمات محلی کوازار 2.7 */
(function () {
  "use strict";

  var SETTINGS_KEY = "qz_site_settings_v27";
  var LANGUAGE_KEY = "qz_language";
  var THEME_KEY = "qz_theme";
  var root = document.documentElement;
  var body = document.body;

  var defaults = {
    language: "fa",
    theme: "dark",
    streaming: true,
    autoScroll: true,
    responseSound: false,
    reducedMotion: false,
    compactSidebar: false,
    highContrast: false,
    rememberView: true,
    rememberRail: true,
  };

  var dict = {
    "خانه":"Home", "فاز اول":"Core", "اتصال مدل هوش مصنوعی":"AI model connection", "دانشنامه":"Knowledge base", "شخصی‌سازی رفتار":"Behavior & RAG", "آزمایشگاه تست":"Test lab", "ویجت و کد امبد":"Widget & embed", "تنظیمات":"Settings", "مدیریت":"Administration", "پنل ادمین":"Admin panel",
    "حساب من":"My account", "مدیر سیستم":"System admin", "کاربر":"User", "سیستم آماده":"System ready", "قدم بعدی چیه؟":"What’s next?", "افزودن سند به دانشنامه":"Add a knowledge document", "تست گفت‌وگو با RAG":"Test RAG chat", "گرفتن کد ویجت":"Get widget code",
    "سلام 👋":"Hello 👋", "یک نگاه سریع به وضعیت دستیار هوشمند و دانشنامه‌ات":"A quick look at your AI assistant and knowledge base", "اسناد دانشنامه":"Knowledge documents", "تکه‌های ایندکس‌شده":"Indexed chunks", "پیام‌های ثبت‌شده":"Logged messages", "نشست‌های آزمایشگاه":"Lab sessions", "نشست‌های ویجت":"Widget sessions", "ارائه‌دهنده‌ی مدل":"Model provider", "وضعیت سرویس":"Service status", "وضعیت فعلی ویجت و حساب کاربری را از API داشبورد می‌خوانیم.":"Current widget and account status from the dashboard API.", "فعال":"Active", "غیرفعال":"Offline",
    "مدل هوش مصنوعی":"AI models", "یک اتصال انتخاب کن و مدل‌ها را تنظیم کن.":"Choose a connection and configure your models.", "اتصال":"Connection", "مقایسه‌ی مدل‌ها":"Model battle", "منبع مدل":"Model source", "مدل‌های رایگان آماده یا API سازگار با OpenAI.":"Ready-to-use models or an OpenAI-compatible API.", "مدل‌های آماده":"Ready models", "رایگان آماده":"Ready-to-use", "API اختصاصی":"Custom API", "مدل چت":"Chat model", "مدل Embedding":"Embedding model", "ذخیره":"Save", "تست اتصال":"Test connection", "Base URL":"Base URL", "API Key":"API key", "دریافت مدل‌ها":"Discover models", "مدل embedding سازگار با پروژه پیدا نشد.":"No compatible embedding model was found.",
    "دانشنامه (Knowledge Base)":"Knowledge base", "اسناد و اطلاعاتی که دستیار هوشمند تو، پاسخ‌ها را از روی آن‌ها می‌سازد.":"Documents and information your assistant uses to answer.", "افزودن سند جدید":"Add document", "آپلود فایل":"Upload file", "حذف کامل دانشنامه":"Clear knowledge base", "فایل‌ها را اینجا رها کن یا کلیک کن":"Drop files here or click", "افزودن سند جدید بزن تا اولین سندت را وارد کنی.":"Add your first document.",
    "شخصی‌سازی رفتار دستیار":"Assistant behavior", "نقش، لحن و پارامترهای بازیابی از دانشنامه را تنظیم کن.":"Tune the role, tone, and retrieval parameters.", "پرامپت سیستمی (نقش و لحن دستیار)":"System prompt (role & tone)", "Temperature (میزان خلاقیت پاسخ)":"Temperature (creativity)", "Top-K (تعداد تکه‌ی بازیابی‌شده از دانشنامه)":"Top-K (retrieved chunks)", "Similarity Threshold (حداقل شباهت)":"Similarity threshold", "ذخیره‌ی تنظیمات":"Save settings",
    "آزمایشگاه تست داخلی":"Internal test lab", "قبل از انتشار ویجت، پاسخ‌گویی و RAG را همین‌جا امتحان کن.":"Test RAG and responses here before publishing the widget.", "گفت‌وگوی جدید":"New chat", "جست‌وجوی معنایی (Playground)":"Semantic search (Playground)", "تست گفت‌وگو":"Chat test", "یک سؤال درباره‌ی دانشنامه‌ات بپرس.":"Ask a question about your knowledge base.", "منابع بازیابی‌شده":"Retrieved sources", "هنوز سؤالی پرسیده نشده.":"No question asked yet.", "شروع گفت‌وگوی جدید":"Start new chat", "جست‌وجو":"Search", "نتیجه‌ای یافت نشد":"No results found",
    "ویجت و کد جاسازی":"Widget & embed", "ظاهر و رفتار ویجت را تنظیم کن؛ پیش‌نمایش سمت چپ همان لحظه عوض می‌شود.":"Configure the widget; the live preview updates instantly.", "ظاهر":"Appearance", "حیوان خانگی":"Pet", "گفت‌وگو":"Chat", "عنوان ویجت":"Widget title", "پیام خوش‌آمدگویی":"Welcome message", "رنگ اصلی":"Primary color", "محل ویجت روی صفحه":"Widget position", "پایین چپ":"Bottom left", "پایین راست":"Bottom right", "حیوان خانگی پیکسلی":"Pixel pet", "رنگ حیوان":"Pet color", "پیام تیزر":"Teaser message", "پاسخ‌های سریع (حداکثر ۴ مورد)":"Quick replies (max 4)", "ذخیره‌ی تغییرات":"Save changes", "پیش‌نمایش زنده":"Live preview", "ویجت واقعی؛ حتی قبل از ذخیره.":"Real widget preview, even before saving.", "بازنشانی":"Reset", "کد جاسازی":"Embed code", "کپی کد":"Copy code", "خودکار":"Auto", "روشن":"Light", "تیره":"Dark",
    "حساب کاربری":"Account", "اطلاعات حساب همین‌جا مدیریت می‌شود؛ نام و آیکونت همچنان پایین منوی کناری است.":"Manage your account here; your name and avatar stay at the bottom of the sidebar.", "نام کاربری":"Username", "نام سازمان":"Organization", "نقش":"Role", "وضعیت":"Status", "خروج از حساب":"Sign out",
    "مرکز کنترل":"Control center", "ذخیره محلی":"Saved locally", "تنظیمات سایت":"Site settings", "زبان، ظاهر، رفتار پاسخ‌ها، تجربه کاربری و حساب را از یکجا کنترل کن.":"Control language, appearance, response behavior, UX, and your account in one place.", "زبان و جهت صفحه":"Language & direction", "با انتخاب English، رابط کاربری کاملاً چپ‌چین می‌شود.":"Choosing English switches the interface to left-to-right.", "فارسی":"Persian", "راست‌چین":"Right to left", "Left to right":"Left to right", "رنگ و حال‌وهوای محیط":"Theme & atmosphere", "۷ پوسته‌ی آماده با ذخیره‌سازی فوری.":"Seven ready-made themes with instant saving.", "روشن کلاسیک":"Classic light", "تیره کلاسیک":"Classic dark", "اقیانوس":"Ocean", "جنگل":"Forest", "غروب":"Sunset", "لاوندر":"Lavender", "مینیمال":"Minimal",
    "رفتار پاسخ":"Response behavior", "این گزینه مستقیماً روی چت داخلی داشبورد اعمال می‌شود.":"These options directly affect the dashboard chat.", "نمایش تکه‌تکه‌ی پاسخ":"Stream the answer", "پاسخ مدل هم‌زمان با رسیدن توکن‌ها نمایش داده شود.":"Show the response as tokens arrive.", "اسکرول خودکار گفتگو":"Auto-scroll chat", "هنگام دریافت پاسخ، پایین گفتگو را دنبال کند.":"Keep the latest response in view.", "هشدار صوتی پایان پاسخ":"Response sound", "بعد از تمام شدن پاسخ، یک صدای کوتاه پخش شود.":"Play a short sound when a response finishes.",
    "تجربه کاربری":"User experience", "جزئیاتی که روی سرعت حس‌شده و کار با پنل اثر می‌گذارند.":"Small controls that affect perceived speed and usability.", "حالت کم‌تحرک":"Reduced motion", "انیمیشن‌ها و حرکت‌های غیرضروری را کاهش می‌دهد.":"Reduce non-essential motion.", "سایدبار فشرده":"Compact sidebar", "منوی کناری را به حالت آیکونی کوچک می‌کند.":"Use an icon-only sidebar.", "کنتراست بیشتر":"High contrast", "مرزها و متن‌های کم‌رنگ را خواناتر می‌کند.":"Increase borders and muted text contrast.",
    "حافظه و حریم تجربه":"Local preferences", "تنظیمات شخصی این مرورگر در همین دستگاه ذخیره می‌شوند.":"Personal preferences are stored locally on this device.", "بازگردانی آخرین بخش":"Remember last section", "پس از ورود دوباره، همان بخش قبلی باز شود.":"Reopen the last section after signing in.", "بازگردانی اندازه منو":"Remember sidebar", "وضعیت باز/بسته بودن سایدبار حفظ شود.":"Remember the sidebar size/state.", "بازنشانی تنظیمات سایت":"Reset site settings",
  };

  function read() {
    try { return Object.assign({}, defaults, JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}")); } catch (_) { return Object.assign({}, defaults); }
  }
  function save(next) {
    try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(next)); } catch (_) {}
  }
  var state = read();

  function currentTheme() {
    try { return localStorage.getItem(THEME_KEY) || state.theme || "dark"; } catch (_) { return state.theme || "dark"; }
  }

  function setTheme(theme, persist) {
    var allowed = ["light", "dark", "ocean", "forest", "sunset", "lavender", "mono"];
    if (allowed.indexOf(theme) === -1) theme = "dark";
    root.dataset.theme = theme;
    state.theme = theme;
    if (persist) { try { localStorage.setItem(THEME_KEY, theme); } catch (_) {} save(state); }
    document.dispatchEvent(new CustomEvent("qz-theme-change", { detail: { theme: theme } }));
    document.querySelectorAll(".theme-preset").forEach(function (el) { el.classList.toggle("active", el.dataset.themePreset === theme); });
  }

  var reverseDict = {};
  Object.keys(dict).forEach(function (key) { reverseDict[dict[key]] = key; });
  function textNodeReplace(text) {
    return state.language === "en" ? (dict[text] || text) : (reverseDict[text] || text);
  }
  var translationObserver = null;
  var isTranslating = false;

  function translateNode(node) {
    if (!node) return;
    var walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    var source = state.language === "en" ? dict : reverseDict;
    var updates = [];
    while (walker.nextNode()) {
      var n = walker.currentNode;
      var value = n.nodeValue.trim();
      if (value && source[value]) updates.push([n, source[value]]);
    }
    updates.forEach(function (x) { x[0].nodeValue = x[1]; });
    if (node === document.body || node === document.documentElement) {
      document.querySelectorAll("input[placeholder], textarea[placeholder], [title]").forEach(function (el) {
        if (el.placeholder && source[el.placeholder]) el.placeholder = source[el.placeholder];
        if (el.title && source[el.title]) el.title = source[el.title];
      });
    }
    document.documentElement.lang = state.language === "en" ? "en" : "fa";
    document.documentElement.dir = state.language === "en" ? "ltr" : "rtl";
    body.classList.toggle("qz-ltr", state.language === "en");
  }
  function restorePersian() { translateNode(document.body); }
  function setLanguage(lang, persist) {
    state.language = lang === "en" ? "en" : "fa";
    if (persist) { try { localStorage.setItem(LANGUAGE_KEY, state.language); } catch (_) {} save(state); }
    // Pause DOM observation while translating. Otherwise every text mutation
    // schedules another full-body translation and the language switch can freeze.
    if (translationObserver) translationObserver.disconnect();
    isTranslating = true;
    try {
      translateNode(document.body);
    } finally {
      isTranslating = false;
      if (translationObserver) translationObserver.observe(document.body, { childList: true, subtree: true, characterData: true });
    }
    document.querySelectorAll("[data-language]").forEach(function (el) { el.classList.toggle("active", el.dataset.language === state.language); });
    document.dispatchEvent(new CustomEvent("qz-language-change", { detail: { language: state.language } }));
  }

  function playDoneSound() {
    if (!state.responseSound || !window.AudioContext) return;
    try {
      var ctx = new AudioContext();
      var osc = ctx.createOscillator(); var gain = ctx.createGain();
      osc.frequency.value = 740; gain.gain.value = 0.035;
      osc.connect(gain); gain.connect(ctx.destination); osc.start(); osc.stop(ctx.currentTime + 0.08);
      osc.onended = function () { ctx.close(); };
    } catch (_) {}
  }

  function setCompactSidebar(on) {
    body.classList.toggle("sidebar-rail", !!on);
    if (state.rememberRail) { try { localStorage.setItem("qz_rail", on ? "1" : "0"); } catch (_) {} }
  }

  function bindSwitch(id, key, handler) {
    var el = document.getElementById(id); if (!el) return;
    el.checked = !!state[key];
    el.addEventListener("change", function () { state[key] = el.checked; save(state); if (handler) handler(el.checked); updateBadge(); });
  }

  function updateBadge() {
    var badge = document.getElementById("settingsSavedBadge");
    if (badge) badge.textContent = state.language === "en" ? "Saved locally" : "ذخیره محلی";
  }

  function initControls() {
    document.querySelectorAll("[data-theme-preset]").forEach(function (el) { el.addEventListener("click", function () { setTheme(el.dataset.themePreset, true); }); });
    document.querySelectorAll("[data-language]").forEach(function (el) { el.addEventListener("click", function () { setLanguage(el.dataset.language, true); }); });
    bindSwitch("settingStreaming", "streaming");
    bindSwitch("settingAutoScroll", "autoScroll");
    bindSwitch("settingResponseSound", "responseSound");
    bindSwitch("settingReducedMotion", "reducedMotion", function (on) { body.classList.toggle("qz-reduced-motion", on); });
    bindSwitch("settingCompactSidebar", "compactSidebar", setCompactSidebar);
    bindSwitch("settingHighContrast", "highContrast", function (on) { body.classList.toggle("qz-high-contrast", on); });
    bindSwitch("settingRememberView", "rememberView");
    bindSwitch("settingRememberRail", "rememberRail");
    var reset = document.getElementById("resetSiteSettingsBtn");
    if (reset) reset.addEventListener("click", function () {
      state = Object.assign({}, defaults); save(state); try { localStorage.removeItem(THEME_KEY); } catch (_) {}
      location.reload();
    });
  }

  translationObserver = new MutationObserver(function (mutations) {
    if (isTranslating || !mutations || state.language === "fa") return;
    mutations.forEach(function (m) {
      if (m.type === "childList") {
        m.addedNodes.forEach(function (n) {
          if (n.nodeType === 1) translateNode(n);
          else if (n.nodeType === 3 && n.nodeValue.trim()) {
            var source = state.language === "en" ? dict : reverseDict;
            var value = n.nodeValue.trim();
            if (source[value]) n.nodeValue = source[value];
          }
        });
      } else if (m.type === "characterData" && m.target && m.target.nodeValue) {
        var source = state.language === "en" ? dict : reverseDict;
        var value = m.target.nodeValue.trim();
        if (value && source[value]) m.target.nodeValue = source[value];
      }
    });
  });
  translationObserver.observe(document.body, { childList: true, subtree: true, characterData: true });

  window.QZSettings = {
    get: function (key) { return state[key]; },
    state: function () { return Object.assign({}, state); },
    setTheme: setTheme,
    setLanguage: setLanguage,
    playDoneSound: playDoneSound,
    translate: function (text) { return state.language === "en" ? textNodeReplace(text) : text; },
    apply: function () {
      setTheme(currentTheme(), false);
      body.classList.toggle("qz-reduced-motion", !!state.reducedMotion);
      body.classList.toggle("qz-high-contrast", !!state.highContrast);
      if (state.compactSidebar) setCompactSidebar(true);
      try { if (localStorage.getItem(LANGUAGE_KEY) === "en") state.language = "en"; } catch (_) {}
      setLanguage(state.language, false);
      updateBadge();
    }
  };

  window.addEventListener("qz-response-complete", playDoneSound);

  function init() { initControls(); QZSettings.apply(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true }); else init();
})();
