/*
 * ویجت چت هوشمند — Prismo
 *
 * قابل جاسازی در هر صفحه:
 * <script
 *   src="https://YOUR_HOST/widget.js"
 *   data-widget-id="..."
 *   data-api-base="https://YOUR_HOST"
 *   data-theme="auto"
 *   async>
 * </script>
 *
 * بدون وابستگی و با Shadow DOM اجرا می‌شود تا با استایل سایت میزبان تداخل نکند.
 */
(function () {
  "use strict";

  function ensureWidgetFont() {
    var href = "https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&display=swap";
    if (document.querySelector('link[data-qz-widget-font="vazirmatn"]')) return;
    var link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    link.setAttribute("data-qz-widget-font", "vazirmatn");
    document.head.appendChild(link);
  }

  function boot() {
    ensureWidgetFont();
    var thisScript =
      document.currentScript ||
      (function () {
        var scripts = document.getElementsByTagName("script");
        for (var i = scripts.length - 1; i >= 0; i--) {
          if (scripts[i].getAttribute("data-widget-id")) return scripts[i];
        }
        return null;
      })();

    if (!thisScript) {
      console.error("[Prismo widget] Widget script tag not found.");
      return;
    }

    var WIDGET_ID = thisScript.getAttribute("data-widget-id");
    var API_BASE = (
      thisScript.getAttribute("data-api-base") ||
      new URL(thisScript.src, window.location.href).origin
    ).replace(/\/+$/, "");
    var POSITION = thisScript.getAttribute("data-position") || "bottom-left";
    var THEME = thisScript.getAttribute("data-theme") || "auto";
    var LANGUAGE = (thisScript.getAttribute("data-language") || "fa").toLowerCase().indexOf("en") === 0 ? "en" : "fa";
    var I18N = {
      fa: { open: "باز کردن گفتگو", close: "بستن", input: "پیامت رو بنویس…", send: "ارسال", footer: "ساخته‌شده با Prismo", pending: "در حال پاسخ…", stopped: "پاسخ متوقف شد.", noReply: "پاسخی دریافت نشد.", serviceError: "این سرویس در حال حاضر موقتاً در دسترس نیست.", loadError: "خطا در بارگذاری ویجت", retry: "تلاش دوباره", serverError: "خطایی در سرویس رخ داد.", offline: "ارتباط با سرویس برقرار نشد.", petLabel: "حیوان خانگی ویجت — برای محبت کلیک کن", settingsUnavailable: "تنظیمات ویجت دریافت نشد. اتصال سرور را بررسی کنید.", title: "دستیار هوشمند", welcome: "سلام! چطور می‌تونم کمکتون کنم؟" },
      en: { open: "Open chat", close: "Close", input: "Type your message…", send: "Send", footer: "Powered by Prismo", pending: "Responding…", stopped: "Response stopped.", noReply: "No response received.", serviceError: "This service is temporarily unavailable.", loadError: "Widget loading error", retry: "Retry", serverError: "A service error occurred.", offline: "Could not connect to the service.", petLabel: "Widget pet — click to show some love", settingsUnavailable: "Widget settings could not be loaded. Check the server connection.", title: "Smart Assistant", welcome: "Hello! How can I help you?" }
    };
    var T = function (key) { return I18N[LANGUAGE][key] || key; };

    // Vercel serverless can finish an SSE response without delivering the text deltas.
    // Match the dashboard: use ordinary JSON in Vercel, and retain live streaming locally.
    var PRISMO_IS_VERCEL_RUNTIME = true;
    var runtimeController = typeof AbortController !== "undefined" ? new AbortController() : null;
    var runtimeTimeout = runtimeController ? setTimeout(function () { runtimeController.abort(); }, 3000) : null;
    var RUNTIME_READY = fetch(API_BASE + "/api/runtime", {
      cache: "no-store",
      headers: { "Accept": "application/json" },
      signal: runtimeController ? runtimeController.signal : undefined
    }).then(function (response) {
      if (!response.ok) throw new Error("Runtime detection failed");
      return response.json();
    }).then(function (runtime) {
      PRISMO_IS_VERCEL_RUNTIME = Boolean(runtime && runtime.vercel);
      return { vercel: PRISMO_IS_VERCEL_RUNTIME };
    }).catch(function () {
      // Fail closed to the more reliable non-streaming path if runtime detection fails.
      PRISMO_IS_VERCEL_RUNTIME = true;
      return { vercel: true };
    }).finally(function () {
      if (runtimeTimeout) clearTimeout(runtimeTimeout);
    });

    if (!WIDGET_ID) {
      console.error("[Prismo widget] data-widget-id is missing.");
      return;
    }

    var keySuffix = WIDGET_ID + "_" + window.location.origin;
    var STORAGE_SESSION_KEY = "qz_widget_session_" + btoa(unescape(encodeURIComponent(keySuffix))).replace(/[^a-zA-Z0-9]/g, "").slice(0, 80);
    var STORAGE_VISITOR_KEY = "qz_widget_visitor_" + WIDGET_ID;

    function getVisitorLabel() {
      try {
        var value = localStorage.getItem(STORAGE_VISITOR_KEY);
        if (!value) {
          value = "visitor_" + Math.random().toString(36).slice(2, 10);
          localStorage.setItem(STORAGE_VISITOR_KEY, value);
        }
        return value;
      } catch (e) {
        return "visitor_anon";
      }
    }

    function getSessionId() {
      try { return localStorage.getItem(STORAGE_SESSION_KEY) || null; } catch (e) { return null; }
    }

    function setSessionId(id) {
      try {
        if (id) localStorage.setItem(STORAGE_SESSION_KEY, id);
      } catch (e) { /* noop */ }
    }

    function normalizeQuickText(value) {
      return String(value || "")
        .toLowerCase()
        .replace(/[يى]/g, "ی").replace(/ك/g, "ک")
        .replace(/[ۀة]/g, "ه")
        .replace(/[\u{1F1E6}-\u{1FAFF}\u2600-\u27BF]/gu, " ")
        .replace(/[\u200d\ufe0f]/g, " ")
        .replace(/[!؟?،.,؛;]+/g, " ")
        .replace(/\s+/g, " ").trim();
    }

    var QUICK_RESPONSES_FA = {
      "سلام": "سلام! خوشحالم می‌بینمت. چه کمکی از دستم برمیاد؟", "درود": "سلام! خوشحالم می‌بینمت. چه کمکی از دستم برمیاد؟", "hi": "سلام! خوشحالم می‌بینمت. چه کمکی از دستم برمیاد؟", "hello": "سلام! خوشحالم می‌بینمت. چه کمکی از دستم برمیاد؟",
      "خوبی": "مرسی که پرسیدی 😊 خوبم و آماده‌ام کمکت کنم. تو چطوری؟", "حالت چطوره": "مرسی که پرسیدی 😊 خوبم و آماده‌ام کمکت کنم. تو چطوری؟", "حالت خوبه": "مرسی که پرسیدی 😊 خوبم و آماده‌ام کمکت کنم. تو چطوری؟", "چطوری": "مرسی که پرسیدی 😊 خوبم و آماده‌ام کمکت کنم. تو چطوری؟", "چه خبر": "مرسی که پرسیدی 😊 خوبم و آماده‌ام کمکت کنم. تو چطوری؟", "ممنون": "خواهش می‌کنم 🌱", "مرسی": "خواهش می‌کنم 🌱", "متشکرم": "خواهش می‌کنم 🌱", "خداحافظ": "خداحافظ! هر وقت خواستی من اینجام.", "فعلا": "خداحافظ! هر وقت خواستی من اینجام.", "بای": "خداحافظ! هر وقت خواستی من اینجام."
    };
    var QUICK_RESPONSES_EN = {
      "سلام": "Hello! 👋 Nice to see you. How can I help?", "درود": "Hello! 👋 Nice to see you. How can I help?", "hi": "Hello! 👋 Nice to see you. How can I help?", "hello": "Hello! 👋 Nice to see you. How can I help?",
      "خوبی": "Thanks for asking 😊 I’m doing well and ready to help. How are you?", "حالت چطوره": "Thanks for asking 😊 I’m doing well and ready to help. How are you?", "حالت خوبه": "Thanks for asking 😊 I’m doing well and ready to help. How are you?", "چطوری": "Thanks for asking 😊 I’m doing well and ready to help. How are you?", "چه خبر": "Thanks for asking 😊 I’m doing well and ready to help. How are you?", "ممنون": "You’re welcome 🌱", "مرسی": "You’re welcome 🌱", "متشکرم": "You’re welcome 🌱", "خداحافظ": "Goodbye! 👋 I’ll be here whenever you need me.", "فعلا": "Goodbye! 👋 I’ll be here whenever you need me.", "بای": "Goodbye! 👋 I’ll be here whenever you need me.", "bye": "Goodbye! 👋 I’ll be here whenever you need me."
    };

    function getQuickReply(text) {
      var source = LANGUAGE === "en" ? QUICK_RESPONSES_EN : QUICK_RESPONSES_FA;
      return source[normalizeQuickText(text)] || null;
    }

    function fetchJson(url, options, timeoutMs) {
      var controller = typeof AbortController !== "undefined" ? new AbortController() : null;
      var timer = controller && timeoutMs > 0 ? setTimeout(function () { controller.abort(); }, timeoutMs) : null;
      var request = Object.assign({}, options || {});
      if (controller) request.signal = controller.signal;

      return fetch(url, request).then(function (response) {
        return response.text().catch(function () { return ""; }).then(function (raw) {
          var data = {};
          try { data = raw ? JSON.parse(raw) : {}; } catch (_) {
            data = raw ? { detail: raw.slice(0, 400) } : {};
          }
          if (!response.ok) {
            var message = data && (data.detail || data.message) ? (data.detail || data.message) : T("serverError");
            var err = new Error(message);
            err.status = response.status;
            err.responseText = raw || "";
            throw err;
          }
          return data;
        });
      }).finally(function () {
        if (timer) clearTimeout(timer);
      });
    }

    // استریم (SSE) با fetch؛ اگر مرورگر/سرور پشتیبانی نکند، فراخوان به حالت غیراستریم برمی‌گردد
    var FALLBACK_STATUSES = [404, 405, 415, 501];

    function streamChat(url, payload, handlers, idleMs) {
      if (!(window.ReadableStream && window.TextDecoder && window.AbortController)) {
        var unsupported = new Error("stream unsupported");
        unsupported.status = 501;
        return Promise.reject(unsupported);
      }
      var controller = new AbortController();
      var timer = null;
      function arm() {
        clearTimeout(timer);
        if (idleMs > 0) timer = setTimeout(function () { controller.abort(); }, idleMs);
      }
      arm();
      return fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "text/event-stream", "X-QZ-Language": LANGUAGE },
        body: JSON.stringify(payload),
        signal: controller.signal
      }).then(function (res) {
        var type = res.headers.get("Content-Type") || "";
        if (!res.ok || type.indexOf("text/event-stream") === -1 || !res.body) {
          return res.json().catch(function () { return {}; }).then(function (data) {
            var err = new Error(data && data.detail ? data.detail : T("serverError"));
            err.status = res.ok ? 415 : res.status;
            throw err;
          });
        }
        var reader = res.body.getReader();
        var decoder = new TextDecoder("utf-8");
        var buffer = "";

        function handleFrame(frame) {
          var event = "message";
          var lines = frame.split("\n");
          var dataParts = [];
          for (var i = 0; i < lines.length; i++) {
            if (lines[i].indexOf("event:") === 0) event = lines[i].slice(6).trim();
            else if (lines[i].indexOf("data:") === 0) dataParts.push(lines[i].slice(5).replace(/^ /, ""));
          }
          if (!dataParts.length) return;
          var data = {};
          try { data = JSON.parse(dataParts.join("\n")); } catch (e) { return; }
          if (event === "meta" && handlers.meta) handlers.meta(data);
          else if (event === "delta" && handlers.delta) handlers.delta(data.t || "");
          else if (event === "reset" && handlers.reset) handlers.reset(data);
          else if (event === "error") {
            var err = new Error(data.message || "STREAM_RETRY");
            err.streamError = true;
            err.retry = data.retry !== false;
            err.partial = Boolean(data.partial);
            throw err;
          }
        }

        function pump() {
          return reader.read().then(function (r) {
            if (r.done) {
              if (buffer.trim()) handleFrame(buffer);
              return;
            }
            arm();
            buffer += decoder.decode(r.value, { stream: true });
            var idx;
            while ((idx = buffer.indexOf("\n\n")) !== -1) {
              var frame = buffer.slice(0, idx);
              buffer = buffer.slice(idx + 2);
              handleFrame(frame);
            }
            return pump();
          });
        }
        return pump();
      }).finally(function () { clearTimeout(timer); });
    }

    var host = document.createElement("div");
    host.id = "qz-widget-host-" + WIDGET_ID;
    host.style.all = "initial";
    document.body.appendChild(host);
    var root = host.attachShadow({ mode: "open" });

    var POSITION_LOCKED = thisScript.hasAttribute("data-position");
    var IS_PREVIEW = thisScript.getAttribute("data-preview") === "1";
    var sideRule = "left:22px;right:auto;";
    host.setAttribute("data-side", POSITION === "bottom-right" ? "right" : "left");
    var LIGHT_VARS = "--qz-panel:#ffffff;--qz-stream:#f5f7fb;--qz-border:#e6e7eb;--qz-text:#1e2633;--qz-muted:#7e8896;--qz-bubble:#f9fafb;";
    var DARK_VARS = "--qz-panel:#1a2332;--qz-stream:#0f1623;--qz-border:rgba(255,255,255,.08);--qz-text:#e6ebf2;--qz-muted:#8a93a3;--qz-bubble:#141d2b;";
    var THEME_VARS = {
      light: LIGHT_VARS,
      dark: DARK_VARS,
      ocean: "--qz-panel:#082032;--qz-stream:#061725;--qz-border:rgba(94,234,212,.18);--qz-text:#e6fffb;--qz-muted:#8fb4b3;--qz-bubble:#0b2d3f;",
      forest: "--qz-panel:#12231a;--qz-stream:#0b1811;--qz-border:rgba(134,239,172,.16);--qz-text:#e7f8ec;--qz-muted:#9db7a5;--qz-bubble:#183021;",
      sunset: "--qz-panel:#2b1720;--qz-stream:#1c1015;--qz-border:rgba(253,186,116,.18);--qz-text:#fff0e4;--qz-muted:#cdb1a4;--qz-bubble:#3a202a;",
      lavender: "--qz-panel:#211b35;--qz-stream:#141023;--qz-border:rgba(216,180,254,.18);--qz-text:#f5efff;--qz-muted:#b9aeca;--qz-bubble:#2b2247;",
      mono: "--qz-panel:#171717;--qz-stream:#101010;--qz-border:#303030;--qz-text:#f1f1f1;--qz-muted:#a0a0a0;--qz-bubble:#202020;"
    };
    var themeVars = THEME_VARS[THEME] || THEME_VARS.dark;
    var themeRule = ".qz-panel{" + themeVars + "}";

    var style = document.createElement("style");
    style.textContent =
      ":host{all:initial;font-family:'Vazirmatn',Tahoma,Arial,sans-serif;}*{box-sizing:border-box;font-family:'Vazirmatn',Tahoma,Arial,sans-serif;}" +
      ".qz-bubble{position:fixed;bottom:22px;" + sideRule + "width:60px;height:60px;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;" +
      "box-shadow:0 12px 35px rgba(0,0,0,.24);z-index:2147483000;border:none;transition:transform .18s ease,box-shadow .18s ease;}" +
      ".qz-bubble:hover{transform:translateY(-2px) scale(1.04);box-shadow:0 16px 38px rgba(0,0,0,.28);}" +
      ".qz-bubble{color:var(--qz-on-accent,#ffffff);}.qz-bubble svg{width:26px;height:26px;}" +
      ".qz-panel{position:fixed;bottom:96px;" + sideRule + "width:370px;max-width:calc(100vw - 24px);height:min(540px,calc(100vh - 170px));max-height:none;" +
      "background:var(--qz-panel,#1a2332);border:1px solid var(--qz-border,#e6e7eb);border-radius:22px;box-shadow:0 28px 80px rgba(20,8,48,.38);" +
      "display:none;flex-direction:column;overflow:hidden;z-index:2147483000;direction:" + (LANGUAGE === "en" ? "ltr" : "rtl") + ";color:var(--qz-text,#e6ebf2);" +
      "}.qz-panel.open{display:flex;}" +
      ".qz-head{padding:15px 17px;display:flex;align-items:center;justify-content:space-between;color:var(--qz-on-accent,#ffffff);flex-shrink:0;}" +
      ".qz-head-title{display:flex;align-items:center;gap:9px;font-weight:700;font-size:14.5px;}" +
      ".qz-head-dot{width:8px;height:8px;border-radius:50%;background:#2fb344;box-shadow:0 0 0 3px rgba(74,222,128,.3);}" +
      ".qz-close{background:rgba(127,127,127,.22);border:none;color:var(--qz-on-accent,#ffffff);width:30px;height:30px;border-radius:50%;cursor:pointer;font-size:15px;line-height:1;}" +
      ".qz-stream{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;background:var(--qz-stream,#0f1623);scrollbar-width:thin;scrollbar-color:var(--qz-accent,#1ABB9C) transparent;}" +
      ".qz-stream::-webkit-scrollbar{width:8px}.qz-stream::-webkit-scrollbar-track{background:transparent}.qz-stream::-webkit-scrollbar-thumb{background:rgba(128,138,154,.32);border-radius:999px;border:2px solid transparent;background-clip:padding-box}.qz-stream::-webkit-scrollbar-thumb:hover{background:var(--qz-accent,#1ABB9C);background-clip:padding-box}" +
      ".qz-msg{max-width:84%;padding:10px 14px;border-radius:15px;font-size:13.5px;line-height:1.8;white-space:pre-wrap;word-break:break-word;}" +
      ".qz-msg.bot{align-self:flex-start;background:var(--qz-bubble,#141d2b);border:1px solid var(--qz-border,#e6e7eb);border-bottom-right-radius:5px;}" +
      ".qz-msg.user{align-self:flex-end;color:var(--qz-on-accent,#ffffff);border-bottom-left-radius:5px;}" +
      ".qz-msg.error{align-self:center;background:rgba(214,69,69,.12);color:#d64545;font-size:12.5px;text-align:center;}" +
      ".qz-msg.pending{opacity:.55;}" +
      ".qz-msg.streaming::after{content:'';display:inline-block;width:6px;height:1em;margin-right:3px;vertical-align:text-bottom;background:var(--qz-accent,#1ABB9C);border-radius:2px;animation:qzblink .9s steps(2,start) infinite;}@keyframes qzblink{to{visibility:hidden;}}" +
      ".qz-foot{display:flex;gap:8px;padding:12px;border-top:1px solid var(--qz-border,#e6e7eb);background:var(--qz-panel,#1a2332);flex-shrink:0;align-items:flex-end;}" +
      ".qz-input{flex:1;resize:none;border:1px solid var(--qz-border,#e6e7eb);background:transparent;color:var(--qz-text,#e6ebf2);border-radius:18px;" +
      "padding:10px 14px;font-size:13.5px;outline:none;max-height:90px;min-height:42px;line-height:1.5;font-family:inherit;}" +
      ".qz-input:focus{border-color:var(--qz-accent,#1ABB9C);}" +
      ".qz-send{width:40px;height:40px;border-radius:50%;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;color:var(--qz-on-accent,#ffffff);}" +
      ".qz-send:disabled{opacity:.55;cursor:not-allowed;}" +
      ".qz-send svg{width:16px;height:16px;}" +
      ".qz-footer-tag{text-align:center;font-size:10.5px;color:var(--qz-muted,#8a93a3);padding:6px 0 10px;background:var(--qz-panel,#1a2332);}" +
      ":host([data-side=right]) .qz-bubble,:host([data-side=right]) .qz-panel,:host([data-side=right]) .qz-teaser{right:22px;left:auto;}" +
      ".qz-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:2px;}" +
      ".qz-chip{border:1px solid var(--qz-accent,#1ABB9C);background:transparent;color:var(--qz-text,#e6ebf2);border-radius:999px;padding:5px 12px;font-size:12px;cursor:pointer;transition:background .15s;}" +
      ".qz-chip:hover{background:var(--qz-accent,#1ABB9C);color:var(--qz-on-accent,#ffffff);}" +
      ".qz-teaser{position:fixed;bottom:92px;left:22px;max-width:230px;padding:10px 14px;border-radius:16px 16px 16px 4px;font-size:13px;line-height:1.7;cursor:pointer;direction:" + (LANGUAGE === "en" ? "ltr" : "rtl") + ";" +
      "background:var(--qz-panel,#1a2332);color:var(--qz-text,#e6ebf2);border:1px solid var(--qz-border,#e6e7eb);box-shadow:0 14px 40px rgba(20,8,48,.3);z-index:2147483000;display:none;animation:qzpop .3s ease;}" +
      ".qz-teaser.show{display:block;}.qz-teaser.high{bottom:140px;}" +
      "@keyframes qzpop{from{opacity:0;transform:translateY(8px) scale(.96);}to{opacity:1;transform:none;}}" +
      ".qz-petlane{position:fixed;display:none;height:52px;left:22px;right:auto;bottom:calc(96px + min(540px,calc(100vh - 170px)) - 4px);width:370px;max-width:calc(100vw - 24px);z-index:2147483000;pointer-events:none;direction:ltr;}" +
      ":host([data-side=right]) .qz-petlane{right:22px;left:auto;}" +
      ".qz-petlane.show{display:block;}" +
      ".qz-pet{position:absolute;left:0;bottom:0;width:64px;height:48px;padding:0;border:0;background:transparent;cursor:pointer;pointer-events:auto;transition:transform .17s linear;image-rendering:pixelated;filter:drop-shadow(0 0 1px rgba(255,255,255,.75));}" +
      ".qz-pet svg{display:block;width:64px;height:48px;shape-rendering:crispEdges;}" +
      ".qz-pet.hop svg{animation:qzhop .5s ease;}@keyframes qzhop{40%{transform:translateY(-12px);}}" +
      ".qz-heart{position:absolute;bottom:44px;width:21px;height:18px;pointer-events:none;animation:qzheart 1.15s ease-out forwards;}" +
      "@keyframes qzheart{from{opacity:1;transform:translateY(0) scale(.8);}to{opacity:0;transform:translateY(-48px) scale(1.25);}}" +
      "@media (prefers-reduced-motion:reduce){.qz-pet,.qz-pet svg,.qz-heart,.qz-teaser{animation:none!important;transition:none!important;}}" +
      "@media (max-width:480px){.qz-panel{width:calc(100vw - 12px);max-width:none;right:6px;left:6px;bottom:84px;height:min(540px,calc(100vh - 158px));}.qz-bubble{bottom:16px;right:16px;left:auto;}.qz-petlane{left:6px;right:6px;width:auto;max-width:none;bottom:calc(84px + min(540px,calc(100vh - 158px)) - 4px);}.qz-teaser{left:auto;right:16px;bottom:84px;}}" +
      themeRule;
    root.appendChild(style);

    var bubble = document.createElement("button");
    bubble.className = "qz-bubble";
    bubble.type = "button";
    bubble.setAttribute("aria-label", T("open"));
    bubble.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>';
    root.appendChild(bubble);

    var panel = document.createElement("div");
    panel.className = "qz-panel";
    panel.setAttribute("aria-hidden", "true");
    panel.innerHTML =
      '<div class="qz-head"><div class="qz-head-title"><span class="qz-head-dot"></span><span class="qz-title-text">' + T("title") + '</span></div><button class="qz-close" type="button" aria-label="' + T("close") + '">✕</button></div>' +
      '<div class="qz-stream" role="log" aria-live="polite"></div>' +
      '<div class="qz-foot"><textarea class="qz-input" rows="1" placeholder="' + T("input") + '"></textarea><button class="qz-send" type="button" aria-label="' + T("send") + '"><svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg></button></div>' +
      '<div class="qz-footer-tag">' + T("footer") + '</div>';
    root.appendChild(panel);

    var stream = panel.querySelector(".qz-stream");
    var input = panel.querySelector(".qz-input");
    var sendBtn = panel.querySelector(".qz-send");
    var closeBtn = panel.querySelector(".qz-close");
    var titleEl = panel.querySelector(".qz-title-text");
    var widgetColor = "#1ABB9C";
    var isSending = false;

    // متن روی رنگ اصلی ویجت (طلایی/زرد روشن → متن تیره، بنفش/تیره → متن سفید)
    function readableOn(hex) {
      var n = parseInt(hex.slice(1), 16);
      var r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
      var lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
      return lum > 0.62 ? "#2b1d00" : "#ffffff";
    }

    function applyColor(color) {
      widgetColor = /^#[0-9a-f]{6}$/i.test(color || "") ? color : "#1ABB9C";
      var onColor = readableOn(widgetColor);
      root.host.style.setProperty("--qz-accent", widgetColor);
      root.host.style.setProperty("--qz-on-accent", onColor);
      bubble.style.background = widgetColor;
      panel.querySelector(".qz-head").style.background =
        "linear-gradient(90deg," + widgetColor + ",color-mix(in srgb," + widgetColor + " 78%,#000))";
      sendBtn.style.background = widgetColor;
      var userMsgs = stream.querySelectorAll(".qz-msg.user");
      for (var i = 0; i < userMsgs.length; i++) userMsgs[i].style.background = widgetColor;
    }

    function addMessage(role, text) {
      var el = document.createElement("div");
      el.className = "qz-msg " + role;
      if (role === "user") el.style.background = widgetColor;
      el.textContent = text || "";
      stream.appendChild(el);
      stream.scrollTop = stream.scrollHeight;
      return el;
    }

    function togglePanel(open) {
      var isOpen = open !== undefined ? open : !panel.classList.contains("open");
      panel.classList.toggle("open", isOpen);
      panel.setAttribute("aria-hidden", isOpen ? "false" : "true");
      if (isOpen) { input.focus(); hideTeaser(); }
      if (typeof syncPetLane === "function") syncPetLane();
    }

    function sendMessage(overrideText) {
      var text = (typeof overrideText === "string" ? overrideText : input.value).trim();
      if (!text || isSending) return;

      input.value = "";
      input.style.height = "42px";
      hideQuickReplies();
      addMessage("user", text);
      var chatUrl = API_BASE + "/public/widget/" + encodeURIComponent(WIDGET_ID) + "/chat";
      var pending = addMessage("bot", T("pending"));
      pending.classList.add("pending");
      isSending = true;

      var quickReply = getQuickReply(text);
      if (quickReply) {
        pending.classList.remove("pending", "streaming");
        pending.textContent = quickReply;
        isSending = false;
        sendBtn.disabled = false;
        petReact("happy");
        var quickPayload = { message: text, session_id: getSessionId(), visitor_label: getVisitorLabel() };
        fetch(chatUrl, {
          method: "POST", headers: {"Content-Type":"application/json", "Cache-Control":"no-cache"},
          body: JSON.stringify(quickPayload), cache: "no-store", keepalive: true
        }).then(function (r) { return r.json().catch(function () { return {}; }); })
          .then(function (d) { if (d && d.session_id) setSessionId(d.session_id); })
          .catch(function () {});
        return;
      }

      sendBtn.disabled = true;
      petReact("think");
      var payload = { message: text, session_id: getSessionId(), visitor_label: getVisitorLabel() };
      var fullText = "";
      var raf = null;

      function paint() {
        raf = null;
        pending.textContent = fullText;
        stream.scrollTop = stream.scrollHeight;
      }

      RUNTIME_READY.then(function (runtime) {
        if (runtime.vercel) {
          // Same reliable JSON path used by the dashboard on Vercel; no SSE token
          // framing/proxy behavior can corrupt or silently drop the generated answer.
          return fetchJson(chatUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Cache-Control": "no-cache", "X-QZ-Language": LANGUAGE },
            body: JSON.stringify(payload),
            cache: "no-store"
          }, 0).then(function (data) {
            setSessionId(data.session_id);
            fullText = typeof data.reply === "string" ? data.reply : "";
          });
        }

        return streamChat(chatUrl + "/stream", payload, {
          meta: function (d) { setSessionId(d.session_id); },
          reset: function () {
            fullText = "";
            pending.textContent = "";
            pending.classList.remove("pending");
            pending.classList.add("streaming");
            if (raf !== null) { cancelAnimationFrame(raf); raf = null; }
          },
          delta: function (piece) {
            if (!fullText) { pending.classList.remove("pending"); pending.classList.add("streaming"); }
            fullText += piece;
            if (raf === null) raf = requestAnimationFrame(paint);
          }
        }, 0).catch(function (err) {
          // قطع/خطای SSE را به کاربر نشان نده؛ همان پیام را به صورت یک‌جا
          // دوباره می‌فرستیم. این مسیر timeout ندارد تا پاسخ‌های طولانی قطع نشوند.
          if (!fullText && (err && (err.streamError || err.status === undefined || FALLBACK_STATUSES.indexOf(err.status) !== -1))) {
            payload.session_id = getSessionId();
            return fetchJson(chatUrl, {
              method: "POST",
              headers: { "Content-Type": "application/json", "Cache-Control": "no-cache", "X-QZ-Language": LANGUAGE },
              body: JSON.stringify(payload),
              cache: "no-store"
            }, 0).then(function (data) {
              setSessionId(data.session_id);
              fullText = typeof data.reply === "string" ? data.reply : "";
            });
          }
          throw err;
        });
      }).then(function () {
        if (raf !== null) cancelAnimationFrame(raf);
        pending.classList.remove("pending", "streaming");
        pending.textContent = fullText || T("noReply");
      }).catch(function (err) {
        if (raf !== null) cancelAnimationFrame(raf);
        pending.classList.remove("streaming");
        // متن‌های داخلی Abort/SSE هرگز مستقیم به کاربر نمایش داده نمی‌شوند.
        var internal = err && (err.message === "متوقف شد." || err.message === "STREAM_RETRY" || err.name === "AbortError");
        var message = internal ? "" : (err && err.message ? err.message : T("offline"));
        if (fullText) {
          pending.textContent = fullText;
        } else if (message) {
          pending.remove();
          addMessage("error", message);
        } else {
          pending.remove();
        }
        petReact("sad");
      }).finally(function () {
        isSending = false;
        sendBtn.disabled = false;
      });
    }

/*PETS-BEGIN*/
var PET_SPRITES = {"dog":{"body":["................","...........KK...","..K.......KDDK..",".KBK.....KDDBBK.",".KBBKKKKKKBBBBBK","..KBBBBBBBBBKBBK","..KBBBBBBBBBBBLK","..KBLLLLBBBBKPPK","..KBLLLLBBBBKKK."],"legs":{"a":["..KBK..KBK.KBK..","..KBK..KBK.KBK..","..KKK..KKK.KKK.."],"b":["...KBK.KBK..KBK.","...KBK.KBK..KBK.","...KKK.KKK..KKK."],"i":["..KBK...KBK.....","..KBK...KBK.....","..KKK...KKK....."]}},"cat":{"body":["..........K...K.",".........KBK.KBK",".........KBBBBBK",".K.......KBKBKBK","KBK......KBBBPBK","KBBKKKKKKKBBBBK.",".KBBBBBBBBBBBK..",".KBDBDBDBBBBBK..",".KBBBBBBBBBBBK.."],"legs":{"a":[".KBK..KBK.KBK...",".KBK..KBK.KBK...",".KKK..KKK.KKK..."],"b":["..KBK.KBK..KBK..","..KBK.KBK..KBK..","..KKK.KKK..KKK.."],"i":[".KBK...KBK......",".KBK...KBK......",".KKK...KKK......"]}},"raccoon":{"body":["..........K...K.",".........KBK.KBK","KLK......KBBBBBK","KDK......KKWKWKK","KLK......KWWPWWK","KDKKKKKKKKBBBBK.",".KLBBBBBBBBBBK..",".KDBBBBBBBBBBK..","..KKBBBBBBBBBK.."],"legs":{"a":["...KDK..KDK.KDK.","...KDK..KDK.KDK.","...KKK..KKK.KKK."],"b":["....KDK.KDK..KDK","....KDK.KDK..KDK","....KKK.KKK..KKK"],"i":["...KDK...KDK....","...KDK...KDK....","...KKK...KKK...."]}}};
/*PETS-END*/

    function shadeHex(hex, f) {
      var n = parseInt(hex.slice(1), 16);
      function ch(v) { return Math.max(0, Math.min(255, Math.round(v * f))); }
      return "rgb(" + ch((n >> 16) & 255) + "," + ch((n >> 8) & 255) + "," + ch(n & 255) + ")";
    }
    function tintHex(hex, f) {
      var n = parseInt(hex.slice(1), 16);
      function ch(v) { return Math.round(v + (255 - v) * f); }
      return "rgb(" + ch((n >> 16) & 255) + "," + ch((n >> 8) & 255) + "," + ch(n & 255) + ")";
    }
    var petSvgCache = {};
    function petSvg(name, frame, color) {
      var key = name + "|" + frame + "|" + color;
      if (petSvgCache[key]) return petSvgCache[key];
      var spec = PET_SPRITES[name] || PET_SPRITES.dog;
      var rows = spec.body.concat(spec.legs[frame] || spec.legs.i);
      var palette = { K: "#2b1d3a", B: color, D: shadeHex(color, 0.68), L: tintHex(color, 0.62), P: "#f472b6", W: "#ffffff" };
      var rects = "";
      for (var y = 0; y < rows.length; y++) {
        var x = 0;
        while (x < rows[y].length) {
          var c = rows[y].charAt(x);
          if (c === ".") { x++; continue; }
          var run = 1;
          while (x + run < rows[y].length && rows[y].charAt(x + run) === c) run++;
          rects += '<rect x="' + x + '" y="' + y + '" width="' + run + '" height="1" fill="' + palette[c] + '"/>';
          x += run;
        }
      }
      var out = '<svg viewBox="0 0 16 12" aria-hidden="true">' + rects + "</svg>";
      petSvgCache[key] = out;
      return out;
    }
    var DEFAULT_PET_COLORS = { dog: "#C98A4B", cat: "#9696A5", raccoon: "#808090" };
    var extras = { pet_enabled: false, pet: "dog", pet_color: "#C98A4B", teaser_enabled: false, quick_replies: [] };
    var lane = document.createElement("div");
    lane.className = "qz-petlane";
    lane.innerHTML = '<button class="qz-pet" type="button"></button>';
    lane.querySelector('.qz-pet').setAttribute('aria-label', T('petLabel'));
    root.appendChild(lane);
    var petEl = lane.querySelector(".qz-pet");

    var teaser = document.createElement("div");
    teaser.className = "qz-teaser";
    root.appendChild(teaser);

    var pet = { x: 0, dir: 1, mode: "rest", frame: 0, walkLeft: 0, timer: null, shown: "" };
    var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function petDraw(frame) {
      var key = extras.pet + "|" + frame + "|" + extras.pet_color;
      if (pet.shown !== key) { petEl.innerHTML = petSvg(extras.pet, frame, extras.pet_color); pet.shown = key; }
      petEl.style.transform = "translateX(" + Math.round(pet.x) + "px) scaleX(" + pet.dir + ")";
    }

    function petPerched() { return !panel.classList.contains("open"); }

    function petTick() {
      if (!extras.pet_enabled || petPerched()) return;
      var laneW = lane.clientWidth || 300;
      var petW = 64;
      if (pet.mode === "walk" && !reduceMotion) {
        pet.x += pet.dir * 6;
        var maxX = Math.max(0, laneW - petW);
        if (pet.x <= 0) { pet.x = 0; pet.dir = 1; }
        if (pet.x >= maxX) { pet.x = maxX; pet.dir = -1; }
        pet.frame = pet.frame ? 0 : 1;
        pet.walkLeft -= 170;
        if (pet.walkLeft <= 0) pet.mode = "rest";
        petDraw(pet.frame ? "a" : "b");
      } else {
        // وایساده؛ تا وقتی کاربر نوازشش نکرده همان‌جا می‌ماند
        petDraw("i");
      }
    }

    function petStartWalking() {
      if (!panel.classList.contains("open")) return;
      pet.mode = "walk";
      pet.walkLeft = 12000 + Math.random() * 6000;
    }

    function petStart() {
      if (pet.timer || !extras.pet_enabled) return;
      pet.timer = setInterval(petTick, 170);
      petTick();
    }
    function petStop() {
      if (pet.timer) { clearInterval(pet.timer); pet.timer = null; }
    }

    var petLoveLevel = 0;
    var petHopBusy = false;
    var HEART_COLORS = ["#d6336c", "#f59f00", "#ae3ec9", "#1ABB9C", "#066fd1"];
    function petHearts() {
      petLoveLevel = (petLoveLevel + 1) % HEART_COLORS.length;
      var color = HEART_COLORS[petLoveLevel];
      var h = document.createElement("span");
      h.className = "qz-heart";
      h.innerHTML = '<svg viewBox="0 0 7 6" shape-rendering="crispEdges"><path fill="' + color + '" d="M1 0h2v1h1V0h2v1h1v2H6v1H5v1H4v1H3V5H2V4H1V3H0V1h1z"/><path fill="#fff" opacity=".7" d="M1 1h1v1H1z"/></svg>';
      var laneW = lane.clientWidth || 300;
      h.style.left = Math.max(0, Math.min(laneW - 21, pet.x + 20)) + "px";
      lane.appendChild(h);
      setTimeout(function () { h.remove(); }, 1250);
    }

    petEl.addEventListener("click", function (e) {
      e.stopPropagation();
      if (!extras.pet_enabled || petHopBusy) return;
      petHopBusy = true;
      petHearts();
      petEl.classList.remove("hop");
      void petEl.offsetWidth;
      petEl.classList.add("hop");
      petStartWalking();
      setTimeout(function () {
        petHopBusy = false;
        petEl.classList.remove("hop");
      }, 520);
    });

    function petReact(kind) {
      // حیوان فقط با کلیک کاربر می‌پرد؛ پاسخ مدل دیگر باعث پرش خودکار نمی‌شود.
      if (!extras.pet_enabled) return;
      if (kind === "think") return;
    }

    function syncPetLane() {
      var on = !!extras.pet_enabled;
      var open = panel.classList.contains("open");
      lane.classList.toggle("show", on && open);
      if (!on || !open) { petStop(); return; }
      pet.shown = "";
      petStart();
      petStartWalking();
      petTick();
    }

    document.addEventListener("visibilitychange", function () {
      if (document.hidden) petStop(); else if (extras.pet_enabled && panel.classList.contains("open")) petStart();
    });

    // ---- پاسخ‌های سریع ----
    var chipsEl = null;
    function hideQuickReplies() {
      if (chipsEl) { chipsEl.remove(); chipsEl = null; }
    }
    function renderQuickReplies() {
      hideQuickReplies();
      var list = extras.quick_replies && extras.quick_replies.length
        ? extras.quick_replies
        : (LANGUAGE === "en" ? ["Hello 👋", "How are you?", "How can you help?"] : ["سلام 👋", "حالت چطوره؟", "چه کمکی می‌تونی بکنی؟"]);
      if (!list.length || stream.querySelectorAll(".qz-msg.user").length) return;
      chipsEl = document.createElement("div");
      chipsEl.className = "qz-chips";
      list.forEach(function (label) {
        var chip = document.createElement("button");
        chip.type = "button";
        chip.className = "qz-chip";
        chip.textContent = label;
        chip.addEventListener("click", function () { sendMessage(label); });
        chipsEl.appendChild(chip);
      });
      stream.appendChild(chipsEl);
      stream.scrollTop = stream.scrollHeight;
    }

    // ---- پیام تیزر بالای دکمه ----
    var TEASER_KEY = "qz_teaser_" + WIDGET_ID;
    var teaserTimer = null;
    function hideTeaser() { teaser.classList.remove("show"); clearTimeout(teaserTimer); }
    function maybeShowTeaser(text) {
      hideTeaser();
      if (!extras.teaser_enabled || !text || panel.classList.contains("open")) return;
      try { if (!IS_PREVIEW && sessionStorage.getItem(TEASER_KEY)) return; } catch (e) { /* noop */ }
      teaserTimer = setTimeout(function () {
        if (panel.classList.contains("open")) return;
        teaser.textContent = text.length > 110 ? text.slice(0, 107) + "…" : text;
        teaser.classList.toggle("high", !!extras.pet_enabled);
        teaser.classList.add("show");
        try { sessionStorage.setItem(TEASER_KEY, "1"); } catch (e) { /* noop */ }
        teaserTimer = setTimeout(hideTeaser, 9000);
      }, IS_PREVIEW ? 600 : 2500);
    }
    teaser.addEventListener("click", function () { hideTeaser(); togglePanel(true); });

    var welcomeText = "";
    var welcomeEl = null;

    function applyExtras(next, opts) {
      var n = next || {};
      extras = {
        pet_enabled: !!n.pet_enabled,
        pet: PET_SPRITES[n.pet] ? n.pet : "dog",
        pet_color: /^#[0-9a-f]{6}$/i.test(n.pet_color || "") ? n.pet_color : (DEFAULT_PET_COLORS[n.pet] || "#C98A4B"),
        teaser_enabled: !!n.teaser_enabled,
        quick_replies: Array.isArray(n.quick_replies) ? n.quick_replies.slice(0, 4) : []
      };
      if (!POSITION_LOCKED && (n.position === "bottom-right" || n.position === "bottom-left")) {
        host.setAttribute("data-side", n.position === "bottom-right" ? "right" : "left");
      }
      syncPetLane();
      renderQuickReplies();
      if (!(opts && opts.silent)) maybeShowTeaser(welcomeText);
    }

    // پیش‌نمایش زنده داخل داشبورد: تغییرات بدون ذخیره‌شدن روی ویجت اعمال می‌شود
    if (IS_PREVIEW) {
      window.addEventListener("message", function (event) {
        if (event.origin !== window.location.origin || !event.data || !event.data.qzPreview) return;
        var d = event.data.qzPreview;
        if (typeof d.title === "string") titleEl.textContent = d.title || "دستیار هوشمند";
        if (typeof d.welcome === "string") { welcomeText = d.welcome; if (welcomeEl) welcomeEl.textContent = d.welcome; }
        if (d.color) applyColor(d.color);
        if (d.extras) applyExtras(d.extras, { silent: !d.showTeaser });
      });
    }

    bubble.addEventListener("click", function () { togglePanel(); });
    closeBtn.addEventListener("click", function () { togglePanel(false); });
    sendBtn.addEventListener("click", function () { sendMessage(); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    input.addEventListener("input", function () {
      input.style.height = "42px";
      input.style.height = Math.min(input.scrollHeight, 90) + "px";
    });

    applyColor(widgetColor);

    fetchJson(API_BASE + "/public/widget/" + encodeURIComponent(WIDGET_ID) + "/config?lang=" + LANGUAGE, { headers: { "X-QZ-Language": LANGUAGE } }, 12000)
      .then(function (cfg) {
        titleEl.textContent = cfg.title || T("title");
        applyColor(cfg.color);
        if (!cfg.online) {
          addMessage("error", T("serviceError"));
          input.disabled = true;
          sendBtn.disabled = true;
          return;
        }
        welcomeText = cfg.welcome_message || T("welcome");
        welcomeEl = addMessage("bot", welcomeText);
        applyExtras(cfg.extras || {});
      })
      .catch(function (err) {
        // خطای config نباید ویجت را از DOM حذف کند؛ کاربر باید علت را ببیند و
        // بتواند دوباره تلاش کند. این مسیر همچنین مانع خطاهای مبهم «text content
        // در دسترس نیست» در iframe/preview می‌شود.
        titleEl.textContent = T("loadError");
        addMessage("error", (err && err.message) || "تنظیمات ویجت دریافت نشد. اتصال سرور را بررسی کنید.");
        input.disabled = true;
        sendBtn.disabled = true;
        var retry = document.createElement("button");
        retry.type = "button";
        retry.textContent = T("retry");
        retry.style.cssText = "margin:0 14px 12px;padding:8px 12px;border:1px solid var(--qz-border,#e6e7eb);border-radius:12px;background:transparent;color:var(--qz-text,#e6ebf2);cursor:pointer;";
        retry.addEventListener("click", function () { location.reload(); });
        panel.appendChild(retry);
        console.error("[Prismo widget] Failed to load widget settings:", err);
      });
  }

  if (document.body) boot();
  else document.addEventListener("DOMContentLoaded", boot, { once: true });
})();
