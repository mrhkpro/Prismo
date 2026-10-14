// قالب مشترک داشبورد و پنل ادمین: سایدبار جمع‌شونده/کشویی + breadcrumb
(function () {
  "use strict";
  var body = document.body;
  var RAIL_KEY = "qz_rail";
  var isMobile = function () { return window.matchMedia("(max-width: 900px)").matches; };

  // متن‌های خام منو را داخل span می‌گذاریم تا در حالت rail بتوان آن‌ها را پنهان کرد
  function wrapLabels() {
    document.querySelectorAll(".sidebar .nav-item, .sidebar .brand").forEach(function (el) {
      Array.prototype.slice.call(el.childNodes).forEach(function (node) {
        if (node.nodeType === 3 && node.textContent.trim()) {
          var span = document.createElement("span");
          span.className = el.classList.contains("brand") ? "brand-text" : "nav-label";
          span.textContent = node.textContent.trim();
          node.replaceWith(span);
        }
      });
      var label = el.querySelector(".nav-label");
      if (label && !el.title) el.title = label.textContent;
    });
  }

  function currentLabel() {
    var active = document.querySelector(".nav-item[data-view].active .nav-label");
    return active ? active.textContent : "";
  }

  function syncCrumb() {
    var crumb = document.getElementById("crumbCurrent");
    var label = currentLabel();
    if (crumb && label) crumb.textContent = label;
  }

  function closeDrawer() { body.classList.remove("sidebar-open"); }

  function init() {
    wrapLabels();
    try { if (localStorage.getItem(RAIL_KEY) === "1") body.classList.add("sidebar-rail"); } catch (_) {}

    var toggle = document.getElementById("sidebarToggle");
    if (toggle) {
      toggle.addEventListener("click", function () {
        if (isMobile()) {
          body.classList.toggle("sidebar-open");
        } else {
          var on = body.classList.toggle("sidebar-rail");
          try { localStorage.setItem(RAIL_KEY, on ? "1" : "0"); } catch (_) {}
        }
      });
    }

    var scrim = document.getElementById("sidebarScrim");
    if (scrim) scrim.addEventListener("click", closeDrawer);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeDrawer(); });
    document.querySelectorAll(".sidebar .nav-item").forEach(function (item) {
      item.addEventListener("click", closeDrawer);
    });

    // breadcrumb همیشه از روی گزینه‌ی فعال منو ساخته می‌شود (بدون وابستگی به Nav.go)
    syncCrumb();
    var observer = new MutationObserver(syncCrumb);
    document.querySelectorAll(".nav-item[data-view]").forEach(function (item) {
      observer.observe(item, { attributes: true, attributeFilter: ["class"] });
    });
    initGlobalAdminThreatAlert();
  }

  // Persistent alert for administrators while they are on the normal dashboard.
  // The server endpoint is admin-only, so regular users never receive flag data.
  function initGlobalAdminThreatAlert() {
    if (!(window.location.pathname || "").endsWith("/dashboard.html")) return;
    if (typeof apiCall !== "function") return;
    try { if (typeof Auth === "undefined" || !Auth.isLoggedIn()) return; } catch (_) { return; }

    var panel = document.createElement("aside");
    panel.className = "global-threat-alert";
    panel.hidden = true;
    panel.setAttribute("role", "status");
    panel.setAttribute("aria-live", "polite");

    var icon = document.createElement("span");
    icon.className = "global-threat-alert-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "!";
    var content = document.createElement("div");
    content.className = "global-threat-alert-content";
    var title = document.createElement("strong");
    title.className = "global-threat-alert-title";
    var detail = document.createElement("span");
    detail.className = "global-threat-alert-detail";
    var meta = document.createElement("span");
    meta.className = "global-threat-alert-meta";
    content.append(title, detail, meta);
    var action = document.createElement("button");
    action.type = "button";
    action.className = "global-threat-alert-action";
    action.addEventListener("click", function () { window.location.href = "/admin.html#security"; });
    panel.append(icon, content, action);
    document.body.appendChild(panel);

    var denied = false, inFlight = false, timer = null;
    function refresh() {
      if (denied || inFlight || document.hidden) return;
      inFlight = true;
      apiCall("/api/admin/security/summary", { timeoutMs: 7000 }).then(function (summary) {
        var total = Number(summary && summary.unresolved_total) || 0;
        if (total <= 0) { panel.hidden = true; return; }
        var critical = Number(summary.critical) || 0;
        var high = Number(summary.high) || 0;
        var medium = Number(summary.medium) || 0;
        var latest = summary.latest || {};
        var severity = critical ? "critical" : high ? "high" : "medium";
        var english = (localStorage.getItem("qz_language") || "fa").toLowerCase().startsWith("en");
        panel.dataset.severity = severity;
        title.textContent = english
          ? (critical ? critical + " critical security alert(s)" : high ? high + " high-severity alert(s)" : "Security alerts need review")
          : (critical ? critical + " هشدار بحرانی بررسی‌نشده" : high ? high + " هشدار امنیتی با شدت بالا" : "هشدارهای امنیتی نیاز به بررسی دارند");
        detail.textContent = latest.label
          ? String(latest.label) + (latest.owner_username ? " · @" + String(latest.owner_username) : "")
          : (english ? "Review suspicious activity from chat or the widget." : "فعالیت مشکوک در چت یا ویجت شناسایی شده است.");
        meta.textContent = english
          ? total + " unresolved · " + high + " high · " + medium + " medium"
          : total + " مورد بررسی‌نشده · " + high + " شدید · " + medium + " متوسط";
        action.textContent = english ? "Review alerts" : "بررسی هشدارها";
        panel.hidden = false;
      }).catch(function (error) {
        if (error && error.status === 403) {
          denied = true;
          panel.remove();
          if (timer) clearInterval(timer);
        }
      }).finally(function () { inFlight = false; });
    }
    refresh();
    timer = setInterval(refresh, 25000);
    document.addEventListener("visibilitychange", function () { if (!document.hidden) refresh(); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();
