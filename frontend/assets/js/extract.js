// تبدیل فایل‌های مختلف به متن ساده — کاملاً داخل مرورگر (بدون آپلود فایل به سرور)
// بنابراین محدودیت حجم بدنه‌ی درخواست در Vercel برای فایل‌های بزرگ مشکلی ایجاد نمی‌کند.
// کتابخانه‌ی سنگین PDF فقط وقتی لازم شود (کاربر PDF انتخاب کند) بارگذاری می‌شود.
(function () {
  "use strict";

  const PDFJS_URL = "/assets/vendor/pdfjs/pdf.min.js?v=5.6.205";
  const PDFJS_WORKER_URL = "/assets/vendor/pdfjs/pdf.worker.min.js?v=5.6.205";

  const PLAIN_EXTENSIONS = ["txt", "md", "markdown", "log", "csv", "tsv", "json", "xml", "yaml", "yml", "ini", "srt", "vtt", "tex", "text"];
  const ZIP_EXTENSIONS = ["docx", "pptx", "xlsx", "odt", "ods", "odp", "epub"];
  const OTHER_EXTENSIONS = ["pdf", "html", "htm", "rtf"];
  const ALL_EXTENSIONS = [...PLAIN_EXTENSIONS, ...ZIP_EXTENSIONS, ...OTHER_EXTENSIONS];

  const MAX_FILE_BYTES = 60 * 1024 * 1024;

  class ExtractError extends Error {}

  function extensionOf(name) {
    const m = /\.([A-Za-z0-9]+)$/.exec(name || "");
    return m ? m[1].toLowerCase() : "";
  }

  function baseName(name) {
    return (name || "سند").replace(/\.[A-Za-z0-9]+$/, "").trim() || "سند";
  }

  // ---------------------------------------------------------------- متن ساده
  async function decodeText(buffer) {
    const bytes = new Uint8Array(buffer);
    if (bytes[0] === 0xff && bytes[1] === 0xfe) return new TextDecoder("utf-16le").decode(bytes.subarray(2));
    if (bytes[0] === 0xfe && bytes[1] === 0xff) return new TextDecoder("utf-16be").decode(bytes.subarray(2));
    try {
      return new TextDecoder("utf-8", { fatal: true }).decode(bytes).replace(/^\uFEFF/, "");
    } catch (_) {
      // فایل‌های قدیمی فارسی معمولاً Windows-1256 هستند
      try { return new TextDecoder("windows-1256").decode(bytes); } catch (__) { return new TextDecoder("latin1").decode(bytes); }
    }
  }

  function htmlToText(html) {
    const doc = new DOMParser().parseFromString(html, "text/html");
    doc.querySelectorAll("script, style, noscript, template, head").forEach((n) => n.remove());
    doc.querySelectorAll("br").forEach((n) => n.replaceWith("\n"));
    doc.querySelectorAll("p, div, li, tr, h1, h2, h3, h4, h5, h6, section, article, pre, blockquote").forEach((n) => n.append("\n"));
    doc.querySelectorAll("td, th").forEach((n) => n.append(" | "));
    return (doc.body ? doc.body.textContent : doc.documentElement.textContent) || "";
  }

  function rtfToText(rtf) {
    return rtf
      .replace(/\\'([0-9a-f]{2})/gi, (_, h) => String.fromCharCode(parseInt(h, 16)))
      .replace(/\\u(-?\d+)\??/g, (_, n) => String.fromCharCode(n < 0 ? Number(n) + 65536 : Number(n)))
      .replace(/\{\\\*[^{}]*\}/g, "")
      .replace(/\\(par|line)\b ?/g, "\n")
      .replace(/\\tab\b ?/g, "\t")
      .replace(/\\[a-z]+-?\d* ?/gi, "")
      .replace(/[{}]/g, "");
  }

  // ---------------------------------------------------------------- ZIP کوچک
  async function inflateRaw(bytes) {
    if (typeof DecompressionStream === "undefined") {
      throw new ExtractError("مرورگر شما از باز کردن این نوع فایل پشتیبانی نمی‌کند؛ مرورگر را به‌روز کنید یا فایل را PDF/TXT کنید.");
    }
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
    return new Uint8Array(await new Response(stream).arrayBuffer());
  }

  function readZipDirectory(buffer) {
    const view = new DataView(buffer);
    let eocd = -1;
    for (let i = buffer.byteLength - 22; i >= Math.max(0, buffer.byteLength - 66000); i--) {
      if (view.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
    }
    if (eocd < 0) throw new ExtractError("فایل خراب است یا فرمت ZIP/Office معتبر نیست.");
    const count = view.getUint16(eocd + 10, true);
    let offset = view.getUint32(eocd + 16, true);
    const entries = new Map();
    const decoder = new TextDecoder("utf-8");
    for (let n = 0; n < count; n++) {
      if (view.getUint32(offset, true) !== 0x02014b50) break;
      const method = view.getUint16(offset + 10, true);
      const compSize = view.getUint32(offset + 20, true);
      const nameLen = view.getUint16(offset + 28, true);
      const extraLen = view.getUint16(offset + 30, true);
      const commentLen = view.getUint16(offset + 32, true);
      const localOffset = view.getUint32(offset + 42, true);
      const name = decoder.decode(new Uint8Array(buffer, offset + 46, nameLen));
      entries.set(name, { method, compSize, localOffset });
      offset += 46 + nameLen + extraLen + commentLen;
    }
    return entries;
  }

  async function readZipEntry(buffer, entries, name) {
    const entry = entries.get(name);
    if (!entry) return null;
    const view = new DataView(buffer);
    const nameLen = view.getUint16(entry.localOffset + 26, true);
    const extraLen = view.getUint16(entry.localOffset + 28, true);
    const start = entry.localOffset + 30 + nameLen + extraLen;
    const raw = new Uint8Array(buffer, start, entry.compSize);
    const data = entry.method === 0 ? raw : entry.method === 8 ? await inflateRaw(raw) : null;
    if (!data) throw new ExtractError("روش فشرده‌سازی این فایل پشتیبانی نمی‌شود.");
    return new TextDecoder("utf-8").decode(data);
  }

  function parseXml(text) {
    const doc = new DOMParser().parseFromString(text, "application/xml");
    if (doc.getElementsByTagName("parsererror").length) throw new ExtractError("ساختار داخلی فایل قابل خواندن نیست.");
    return doc;
  }

  function elementsByLocal(root, localName) {
    return Array.from(root.getElementsByTagName("*")).filter((el) => el.localName === localName);
  }

  function childrenByLocal(el, localName) {
    return Array.from(el.children).filter((c) => c.localName === localName);
  }

  // ---------------------------------------------------------------- DOCX
  function wordParagraph(p) {
    let out = "";
    p.querySelectorAll("*").forEach((el) => {
      if (el.localName === "t") out += el.textContent;
      else if (el.localName === "tab") out += "\t";
      else if (el.localName === "br" || el.localName === "cr") out += "\n";
    });
    return out;
  }

  async function docxToText(buffer) {
    const entries = readZipDirectory(buffer);
    const xml = await readZipEntry(buffer, entries, "word/document.xml");
    if (!xml) throw new ExtractError("این فایل Word معتبر نیست.");
    const body = elementsByLocal(parseXml(xml), "body")[0];
    const lines = [];
    const walk = (parent) => {
      Array.from(parent.children).forEach((node) => {
        if (node.localName === "p") lines.push(wordParagraph(node));
        else if (node.localName === "tbl") {
          childrenByLocal(node, "tr").forEach((tr) => {
            const cells = childrenByLocal(tr, "tc").map((tc) => childrenByLocal(tc, "p").map(wordParagraph).join(" ").trim());
            lines.push(cells.join(" | "));
          });
        } else if (node.localName === "sdt" || node.localName === "sdtContent") walk(node);
      });
    };
    walk(body);
    return lines.join("\n");
  }

  // ---------------------------------------------------------------- PPTX
  async function pptxToText(buffer) {
    const entries = readZipDirectory(buffer);
    const slides = Array.from(entries.keys())
      .filter((n) => /^ppt\/slides\/slide\d+\.xml$/.test(n))
      .sort((a, b) => parseInt(a.match(/(\d+)\.xml$/)[1], 10) - parseInt(b.match(/(\d+)\.xml$/)[1], 10));
    const out = [];
    for (let i = 0; i < slides.length; i++) {
      const doc = parseXml(await readZipEntry(buffer, entries, slides[i]));
      const paragraphs = elementsByLocal(doc, "p").map((p) => elementsByLocal(p, "t").map((t) => t.textContent).join("")).filter((t) => t.trim());
      if (paragraphs.length) out.push(`--- اسلاید ${i + 1} ---\n${paragraphs.join("\n")}`);
    }
    return out.join("\n\n");
  }

  // ---------------------------------------------------------------- XLSX
  function columnIndex(ref) {
    const letters = /^[A-Z]+/.exec(ref || "");
    if (!letters) return 0;
    return letters[0].split("").reduce((acc, ch) => acc * 26 + ch.charCodeAt(0) - 64, 0) - 1;
  }

  async function xlsxToText(buffer) {
    const entries = readZipDirectory(buffer);
    const shared = [];
    const sharedXml = await readZipEntry(buffer, entries, "xl/sharedStrings.xml");
    if (sharedXml) {
      elementsByLocal(parseXml(sharedXml), "si").forEach((si) => {
        shared.push(elementsByLocal(si, "t").map((t) => t.textContent).join(""));
      });
    }
    // ترتیب و نام شیت‌ها از workbook.xml
    let sheetFiles = [];
    const wbXml = await readZipEntry(buffer, entries, "xl/workbook.xml");
    const relsXml = await readZipEntry(buffer, entries, "xl/_rels/workbook.xml.rels");
    if (wbXml && relsXml) {
      const rels = new Map(elementsByLocal(parseXml(relsXml), "Relationship").map((r) => [r.getAttribute("Id"), r.getAttribute("Target")]));
      sheetFiles = elementsByLocal(parseXml(wbXml), "sheet").map((s) => {
        const rid = s.getAttribute("r:id") || s.getAttributeNS("http://schemas.openxmlformats.org/officeDocument/2006/relationships", "id");
        let target = rels.get(rid) || "";
        target = target.replace(/^\//, "");
        return { name: s.getAttribute("name") || "", path: target.startsWith("xl/") ? target : `xl/${target}` };
      });
    }
    if (!sheetFiles.length) {
      sheetFiles = Array.from(entries.keys()).filter((n) => /^xl\/worksheets\/sheet\d+\.xml$/.test(n)).sort().map((p, i) => ({ name: `Sheet${i + 1}`, path: p }));
    }
    const out = [];
    for (const sheet of sheetFiles) {
      const xml = await readZipEntry(buffer, entries, sheet.path);
      if (!xml) continue;
      const rows = [];
      elementsByLocal(parseXml(xml), "row").forEach((row) => {
        const cells = [];
        childrenByLocal(row, "c").forEach((c) => {
          const type = c.getAttribute("t");
          let value = "";
          if (type === "s") value = shared[parseInt((childrenByLocal(c, "v")[0] || {}).textContent, 10)] || "";
          else if (type === "inlineStr") value = elementsByLocal(c, "t").map((t) => t.textContent).join("");
          else value = (childrenByLocal(c, "v")[0] || {}).textContent || "";
          cells[columnIndex(c.getAttribute("r"))] = value;
        });
        const line = Array.from(cells, (v) => v || "").join(" | ").replace(/(\s*\|\s*)+$/, "").trim();
        if (line) rows.push(line);
      });
      if (rows.length) out.push(`## ${sheet.name}\n${rows.join("\n")}`);
    }
    return out.join("\n\n");
  }

  // ---------------------------------------------------------------- OpenDocument
  async function odfToText(buffer) {
    const entries = readZipDirectory(buffer);
    const xml = await readZipEntry(buffer, entries, "content.xml");
    if (!xml) throw new ExtractError("این فایل OpenDocument معتبر نیست.");
    const doc = parseXml(xml);
    const lines = [];
    const textOf = (el) => Array.from(el.childNodes).map((n) => {
      if (n.nodeType === 3) return n.textContent;
      if (n.localName === "tab") return "\t";
      if (n.localName === "line-break") return "\n";
      if (n.localName === "s") return " ";
      return textOf(n);
    }).join("");
    const walk = (parent) => {
      Array.from(parent.children).forEach((node) => {
        if (node.localName === "p" || node.localName === "h") lines.push(textOf(node));
        else if (node.localName === "table-row") {
          const cells = childrenByLocal(node, "table-cell").map((cell) => elementsByLocal(cell, "p").map(textOf).join(" ").trim());
          const line = cells.join(" | ").replace(/(\s*\|\s*)+$/, "").trim();
          if (line) lines.push(line);
        } else walk(node);
      });
    };
    const body = elementsByLocal(doc, "body")[0];
    if (body) walk(body);
    return lines.join("\n");
  }

  // ---------------------------------------------------------------- EPUB
  async function epubToText(buffer) {
    const entries = readZipDirectory(buffer);
    const pages = Array.from(entries.keys()).filter((n) => /\.(xhtml|html|htm)$/i.test(n)).sort();
    const out = [];
    for (const name of pages) out.push(htmlToText(await readZipEntry(buffer, entries, name)));
    return out.join("\n\n");
  }

  // ---------------------------------------------------------------- PDF
  let pdfjsPromise = null;
  function loadPdfJs() {
    if (!pdfjsPromise) {
      pdfjsPromise = import(PDFJS_URL).then((lib) => {
        lib.GlobalWorkerOptions.workerSrc = new URL(PDFJS_WORKER_URL, location.href).href;
        return lib;
      });
      pdfjsPromise.catch(() => { pdfjsPromise = null; });
    }
    return pdfjsPromise;
  }

  async function pdfToText(buffer, onProgress) {
    const pdfjs = await loadPdfJs();
    const task = pdfjs.getDocument({ data: new Uint8Array(buffer), isEvalSupported: false });
    let pdf;
    try {
      pdf = await task.promise;
    } catch (err) {
      if (err && err.name === "PasswordException") throw new ExtractError("این PDF رمز دارد؛ نسخه‌ی بدون رمز را بارگذاری کن.");
      throw new ExtractError("PDF خراب است یا قابل خواندن نیست.");
    }
    const pages = [];
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      let line = "";
      const lines = [];
      content.items.forEach((item) => {
        line += item.str;
        if (item.hasEOL) { lines.push(line); line = ""; }
        else if (item.str && !/\s$/.test(item.str)) line += " ";
      });
      if (line.trim()) lines.push(line);
      pages.push(lines.map((l) => l.replace(/[ \t]+/g, " ").trim()).filter(Boolean).join("\n"));
      page.cleanup();
      if (onProgress) onProgress(i, pdf.numPages);
    }
    await pdf.destroy();
    return pages.filter(Boolean).join("\n\n");
  }

  // ---------------------------------------------------------------- نقطه‌ی ورود
  function normalize(text) {
    return String(text || "")
      .replace(/\r\n?/g, "\n")
      .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "")
      .replace(/[ \t]+\n/g, "\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  async function extract(file, onProgress) {
    const ext = extensionOf(file.name);
    if (["doc", "xls", "ppt"].includes(ext)) {
      throw new ExtractError(`فرمت قدیمی .${ext} پشتیبانی نمی‌شود؛ فایل را به .${ext}x یا PDF ذخیره کن.`);
    }
    if (!ALL_EXTENSIONS.includes(ext)) {
      throw new ExtractError(`فرمت «${ext || "نامشخص"}» پشتیبانی نمی‌شود. فرمت‌های مجاز: PDF، Word، Excel، PowerPoint، OpenDocument، EPUB، HTML، RTF، CSV، JSON، TXT و Markdown.`);
    }
    if (file.size > MAX_FILE_BYTES) throw new ExtractError("حجم فایل بیشتر از ۶۰ مگابایت است.");

    const buffer = await file.arrayBuffer();
    let text;
    if (ext === "pdf") text = await pdfToText(buffer, onProgress);
    else if (ext === "docx") text = await docxToText(buffer);
    else if (ext === "pptx") text = await pptxToText(buffer);
    else if (ext === "xlsx") text = await xlsxToText(buffer);
    else if (["odt", "ods", "odp"].includes(ext)) text = await odfToText(buffer);
    else if (ext === "epub") text = await epubToText(buffer);
    else if (ext === "html" || ext === "htm") text = htmlToText(await decodeText(buffer));
    else if (ext === "rtf") text = rtfToText(await decodeText(buffer));
    else if (ext === "json") {
      const raw = await decodeText(buffer);
      try { text = JSON.stringify(JSON.parse(raw), null, 2); } catch (_) { text = raw; }
    } else if (ext === "xml") {
      const raw = await decodeText(buffer);
      try { text = elementsByLocal(parseXml(raw), "*").length ? parseXml(raw).documentElement.textContent : raw; } catch (_) { text = raw; }
    } else text = await decodeText(buffer);

    text = normalize(text);
    if (!text) {
      throw new ExtractError(ext === "pdf"
        ? "متنی در این PDF پیدا نشد؛ احتمالاً اسکن/تصویری است. نسخه‌ی متنی (قابل انتخاب) را بارگذاری کن."
        : "متنی در این فایل پیدا نشد.");
    }
    return { title: baseName(file.name), text, kind: ext };
  }

  // متن‌های خیلی بزرگ را به چند سند کوچک‌تر تقسیم می‌کند تا ایندکس هر سند داخل زمان مجاز سرور تمام شود
  function splitForUpload(text, maxChars) {
    const limit = maxChars || 60000;
    if (text.length <= limit) return [text];
    const parts = [];
    let current = "";
    const flush = () => { if (current.trim()) parts.push(current.trim()); current = ""; };
    text.split(/\n{2,}/).forEach((block) => {
      while (block.length > limit) {
        flush();
        parts.push(block.slice(0, limit));
        block = block.slice(limit);
      }
      if (current.length + block.length + 2 > limit) flush();
      current += (current ? "\n\n" : "") + block;
    });
    flush();
    return parts;
  }

  window.FileExtract = {
    extract,
    splitForUpload,
    ExtractError,
    accept: ALL_EXTENSIONS.map((e) => "." + e).join(","),
    extensions: ALL_EXTENSIONS,
  };
})();
