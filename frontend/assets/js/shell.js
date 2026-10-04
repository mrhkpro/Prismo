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
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();
