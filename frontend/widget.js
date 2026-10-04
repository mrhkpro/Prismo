/*
 * ویجت چت هوشمند — کوازار
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

  function boot() {
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
      console.error("[کوازار ویجت] تگ اسکریپت پیدا نشد.");
      return;
    }

    var WIDGET_ID = thisScript.getAttribute("data-widget-id");
    var API_BASE = (
      thisScript.getAttribute("data-api-base") ||
      new URL(thisScript.src, window.location.href).origin
    ).replace(/\/+$/, "");
    var POSITION = thisScript.getAttribute("data-position") || "bottom-left";
    var THEME = thisScript.getAttribute("data-theme") || "auto";

    if (!WIDGET_ID) {
      console.error("[کوازار ویجت] data-widget-id تنظیم نشده است.");
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

    function fetchJson(url, options, timeoutMs) {
      var controller = typeof AbortController !== "undefined" ? new AbortController() : null;
      var timer = controller ? setTimeout(function () { controller.abort(); }, timeoutMs || 15000) : null;
      var request = Object.assign({}, options || {});
      if (controller) request.signal = controller.signal;

      return fetch(url, request).then(function (response) {
        return response.json().catch(function () { return {}; }).then(function (data) {
          if (!response.ok) {
            var message = data && data.detail ? data.detail : "خطایی در سرویس رخ داد.";
            var err = new Error(message);
            err.status = response.status;
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
        timer = setTimeout(function () { controller.abort(); }, idleMs || 60000);
      }
      arm();
      return fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
        body: JSON.stringify(payload),
        signal: controller.signal
      }).then(function (res) {
        var type = res.headers.get("Content-Type") || "";
        if (!res.ok || type.indexOf("text/event-stream") === -1 || !res.body) {
          return res.json().catch(function () { return {}; }).then(function (data) {
            var err = new Error(data && data.detail ? data.detail : "خطایی در سرویس رخ داد.");
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
          else if (event === "error") {
            var err = new Error(data.message || "خطا در دریافت پاسخ.");
            err.streamError = true;
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

    var sideRule = POSITION === "bottom-right" ? "right:22px;left:auto;" : "left:22px;right:auto;";
    var LIGHT_VARS = "--qz-panel:#ffffff;--qz-stream:#fffaf0;--qz-border:#efdca0;--qz-text:#2b2108;--qz-muted:#8a7638;--qz-bubble:#fff3c9;";
    var DARK_VARS = "--qz-panel:#130c26;--qz-stream:#0a0614;--qz-border:#34265f;--qz-text:#f5f1ff;--qz-muted:#9a8fc4;--qz-bubble:#1f1540;";
    var themeRule = THEME === "light"
      ? ".qz-panel{" + LIGHT_VARS + "}"
      : THEME === "dark"
        ? ".qz-panel{" + DARK_VARS + "}"
        : "@media (prefers-color-scheme: light){.qz-panel{" + LIGHT_VARS + "}}";

    var style = document.createElement("style");
    style.textContent =
      ":host{all:initial;}*{box-sizing:border-box;font-family:'Vazirmatn',Tahoma,Arial,sans-serif;}" +
      ".qz-bubble{position:fixed;bottom:22px;" + sideRule + "width:60px;height:60px;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;" +
      "box-shadow:0 12px 35px rgba(0,0,0,.24);z-index:2147483000;border:none;transition:transform .18s ease,box-shadow .18s ease;}" +
      ".qz-bubble:hover{transform:translateY(-2px) scale(1.04);box-shadow:0 16px 38px rgba(0,0,0,.28);}" +
      ".qz-bubble{color:var(--qz-on-accent,#fff);}.qz-bubble svg{width:26px;height:26px;}" +
      ".qz-panel{position:fixed;bottom:96px;" + sideRule + "width:370px;max-width:calc(100vw - 24px);height:540px;max-height:78vh;" +
      "background:var(--qz-panel,#130c26);border:1px solid var(--qz-border,#34265f);border-radius:22px;box-shadow:0 28px 80px rgba(20,8,48,.38);" +
      "display:none;flex-direction:column;overflow:hidden;z-index:2147483000;direction:rtl;color:var(--qz-text,#f5f1ff);" +
      "}.qz-panel.open{display:flex;}" +
      ".qz-head{padding:15px 17px;display:flex;align-items:center;justify-content:space-between;color:var(--qz-on-accent,#fff);flex-shrink:0;}" +
      ".qz-head-title{display:flex;align-items:center;gap:9px;font-weight:700;font-size:14.5px;}" +
      ".qz-head-dot{width:8px;height:8px;border-radius:50%;background:#4ade80;box-shadow:0 0 0 3px rgba(74,222,128,.3);}" +
      ".qz-close{background:rgba(127,127,127,.22);border:none;color:var(--qz-on-accent,#fff);width:30px;height:30px;border-radius:50%;cursor:pointer;font-size:15px;line-height:1;}" +
      ".qz-stream{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;background:var(--qz-stream,#0a0614);}" +
      ".qz-msg{max-width:84%;padding:10px 14px;border-radius:15px;font-size:13.5px;line-height:1.8;white-space:pre-wrap;word-break:break-word;}" +
      ".qz-msg.bot{align-self:flex-start;background:var(--qz-bubble,#1f1540);border:1px solid var(--qz-border,#34265f);border-bottom-right-radius:5px;}" +
      ".qz-msg.user{align-self:flex-end;color:var(--qz-on-accent,#fff);border-bottom-left-radius:5px;}" +
      ".qz-msg.error{align-self:center;background:rgba(214,69,69,.12);color:#d64545;font-size:12.5px;text-align:center;}" +
      ".qz-msg.pending{opacity:.55;}" +
      ".qz-msg.streaming::after{content:'';display:inline-block;width:6px;height:1em;margin-right:3px;vertical-align:text-bottom;background:var(--qz-accent,#8b5cf6);border-radius:2px;animation:qzblink .9s steps(2,start) infinite;}@keyframes qzblink{to{visibility:hidden;}}" +
      ".qz-foot{display:flex;gap:8px;padding:12px;border-top:1px solid var(--qz-border,#34265f);background:var(--qz-panel,#130c26);flex-shrink:0;align-items:flex-end;}" +
      ".qz-input{flex:1;resize:none;border:1px solid var(--qz-border,#34265f);background:transparent;color:var(--qz-text,#f5f1ff);border-radius:18px;" +
      "padding:10px 14px;font-size:13.5px;outline:none;max-height:90px;min-height:42px;line-height:1.5;font-family:inherit;}" +
      ".qz-input:focus{border-color:var(--qz-accent,#8b5cf6);}" +
      ".qz-send{width:40px;height:40px;border-radius:50%;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;color:var(--qz-on-accent,#fff);}" +
      ".qz-send:disabled{opacity:.55;cursor:not-allowed;}" +
      ".qz-send svg{width:16px;height:16px;}" +
      ".qz-footer-tag{text-align:center;font-size:10.5px;color:var(--qz-muted,#9a8fc4);padding:6px 0 10px;background:var(--qz-panel,#130c26);}" +
      "@media (max-width:480px){.qz-panel{width:calc(100vw - 12px);max-width:none;right:6px;left:6px;bottom:84px;height:min(540px,78vh);}.qz-bubble{bottom:16px;right:16px;left:auto;}}" +
      themeRule;
    root.appendChild(style);

    var bubble = document.createElement("button");
    bubble.className = "qz-bubble";
    bubble.type = "button";
    bubble.setAttribute("aria-label", "باز کردن گفتگو");
    bubble.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>';
    root.appendChild(bubble);

    var panel = document.createElement("div");
    panel.className = "qz-panel";
    panel.setAttribute("aria-hidden", "true");
    panel.innerHTML =
      '<div class="qz-head"><div class="qz-head-title"><span class="qz-head-dot"></span><span class="qz-title-text">دستیار هوشمند</span></div><button class="qz-close" type="button" aria-label="بستن">✕</button></div>' +
      '<div class="qz-stream" role="log" aria-live="polite"></div>' +
      '<div class="qz-foot"><textarea class="qz-input" rows="1" placeholder="پیامت رو بنویس…"></textarea><button class="qz-send" type="button" aria-label="ارسال"><svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg></button></div>' +
      '<div class="qz-footer-tag">ساخته‌شده با کوازار</div>';
    root.appendChild(panel);

    var stream = panel.querySelector(".qz-stream");
    var input = panel.querySelector(".qz-input");
    var sendBtn = panel.querySelector(".qz-send");
    var closeBtn = panel.querySelector(".qz-close");
    var titleEl = panel.querySelector(".qz-title-text");
    var widgetColor = "#8B5CF6";
    var isSending = false;

    // متن روی رنگ اصلی ویجت (طلایی/زرد روشن → متن تیره، بنفش/تیره → متن سفید)
    function readableOn(hex) {
      var n = parseInt(hex.slice(1), 16);
      var r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
      var lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
      return lum > 0.62 ? "#2b1d00" : "#ffffff";
    }

    function applyColor(color) {
      widgetColor = /^#[0-9a-f]{6}$/i.test(color || "") ? color : "#8B5CF6";
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
      if (isOpen) input.focus();
    }

    // نقطه‌های اتصال به قابلیت‌های بعدی (حیوان خانگی و پاسخ‌های سریع)
    function petReact() {}
    function hideQuickReplies() {}

    function sendMessage(overrideText) {
      var text = (typeof overrideText === "string" ? overrideText : input.value).trim();
      if (!text || isSending) return;

      input.value = "";
      input.style.height = "42px";
      hideQuickReplies();
      addMessage("user", text);
      var pending = addMessage("bot", "در حال پاسخ…");
      pending.classList.add("pending");
      isSending = true;
      sendBtn.disabled = true;
      petReact("think");

      var chatUrl = API_BASE + "/public/widget/" + encodeURIComponent(WIDGET_ID) + "/chat";
      var payload = { message: text, session_id: getSessionId(), visitor_label: getVisitorLabel() };
      var fullText = "";
      var raf = null;

      function paint() {
        raf = null;
        pending.textContent = fullText;
        stream.scrollTop = stream.scrollHeight;
      }

      streamChat(chatUrl + "/stream", payload, {
        meta: function (d) { setSessionId(d.session_id); },
        delta: function (piece) {
          if (!fullText) { pending.classList.remove("pending"); pending.classList.add("streaming"); }
          fullText += piece;
          if (raf === null) raf = requestAnimationFrame(paint);
        }
      }, 60000).catch(function (err) {
        if (!fullText && err && FALLBACK_STATUSES.indexOf(err.status) !== -1) {
          // سرور/مرورگر استریم ندارد → همان درخواست را یک‌جا بفرست
          payload.session_id = getSessionId();
          return fetchJson(chatUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          }, 30000).then(function (data) {
            setSessionId(data.session_id);
            fullText = data.reply || "پاسخی دریافت نشد.";
          });
        }
        throw err;
      }).then(function () {
        if (raf !== null) cancelAnimationFrame(raf);
        pending.classList.remove("pending", "streaming");
        pending.textContent = fullText || "پاسخی دریافت نشد.";
        petReact("happy");
      }).catch(function (err) {
        if (raf !== null) cancelAnimationFrame(raf);
        pending.classList.remove("streaming");
        var message = err && err.message ? err.message : "ارتباط با سرویس برقرار نشد.";
        if (fullText) {
          pending.textContent = fullText;
          addMessage("error", message);
        } else {
          pending.remove();
          addMessage("error", message);
        }
        petReact("sad");
      }).finally(function () {
        isSending = false;
        sendBtn.disabled = false;
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

    fetchJson(API_BASE + "/public/widget/" + encodeURIComponent(WIDGET_ID) + "/config", {}, 12000)
      .then(function (cfg) {
        titleEl.textContent = cfg.title || "دستیار هوشمند";
        applyColor(cfg.color);
        if (!cfg.online) {
          addMessage("error", "این سرویس در حال حاضر موقتاً در دسترس نیست.");
          input.disabled = true;
          sendBtn.disabled = true;
          return;
        }
        addMessage("bot", cfg.welcome_message || "سلام! چطور می‌تونم کمکتون کنم؟");
      })
      .catch(function (err) {
        bubble.style.display = "none";
        panel.remove();
        console.error("[کوازار ویجت] بارگذاری تنظیمات ناموفق بود:", err);
      });
  }

  if (document.body) boot();
  else document.addEventListener("DOMContentLoaded", boot, { once: true });
})();
