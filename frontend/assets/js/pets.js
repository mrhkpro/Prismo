// نمونه‌ی کوچک حیوان‌های پیکسلی برای انتخابگر داشبورد.
// بلوک PETS-BEGIN/END باید با همان بلوک داخل widget.js یکی باشد (تست قرارداد این را چک می‌کند).
(function () {
  "use strict";
  /*PETS-BEGIN*/
  var PET_SPRITES = {"dog":{"body":["................","...........KK...","..K.......KDDK..",".KBK.....KDDBBK.",".KBBKKKKKKBBBBBK","..KBBBBBBBBBKBBK","..KBBBBBBBBBBBLK","..KBLLLLBBBBKPPK","..KBLLLLBBBBKKK."],"legs":{"a":["..KBK..KBK.KBK..","..KBK..KBK.KBK..","..KKK..KKK.KKK.."],"b":["...KBK.KBK..KBK.","...KBK.KBK..KBK.","...KKK.KKK..KKK."],"i":["..KBK...KBK.....","..KBK...KBK.....","..KKK...KKK....."]}},"cat":{"body":["..........K...K.",".........KBK.KBK",".........KBBBBBK",".K.......KBKBKBK","KBK......KBBBPBK","KBBKKKKKKKBBBBK.",".KBBBBBBBBBBBK..",".KBDBDBDBBBBBK..",".KBBBBBBBBBBBK.."],"legs":{"a":[".KBK..KBK.KBK...",".KBK..KBK.KBK...",".KKK..KKK.KKK..."],"b":["..KBK.KBK..KBK..","..KBK.KBK..KBK..","..KKK.KKK..KKK.."],"i":[".KBK...KBK......",".KBK...KBK......",".KKK...KKK......"]}},"raccoon":{"body":["..........K...K.",".........KBK.KBK","KLK......KBBBBBK","KDK......KKWKWKK","KLK......KWWPWWK","KDKKKKKKKKBBBBK.",".KLBBBBBBBBBBK..",".KDBBBBBBBBBBK..","..KKBBBBBBBBBK.."],"legs":{"a":["...KDK..KDK.KDK.","...KDK..KDK.KDK.","...KKK..KKK.KKK."],"b":["....KDK.KDK..KDK","....KDK.KDK..KDK","....KKK.KKK..KKK"],"i":["...KDK...KDK....","...KDK...KDK....","...KKK...KKK...."]}}};
  /*PETS-END*/

  var DEFAULT_COLORS = { dog: "#C98A4B", cat: "#9696A5", raccoon: "#808090" };
  var LABELS = { dog: "سگ", cat: "گربه", raccoon: "راکون" };

  function clamp(v) { return Math.max(0, Math.min(255, Math.round(v))); }
  function rgb(hex) { var n = parseInt(hex.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
  function shade(hex, f) { var c = rgb(hex); return "rgb(" + clamp(c[0] * f) + "," + clamp(c[1] * f) + "," + clamp(c[2] * f) + ")"; }
  function tint(hex, f) { var c = rgb(hex); return "rgb(" + clamp(c[0] + (255 - c[0]) * f) + "," + clamp(c[1] + (255 - c[1]) * f) + "," + clamp(c[2] + (255 - c[2]) * f) + ")"; }

  function svg(name, frame, color, px) {
    var spec = PET_SPRITES[name] || PET_SPRITES.dog;
    var rows = spec.body.concat(spec.legs[frame] || spec.legs.i);
    var palette = { K: "#2b1d3a", B: color, D: shade(color, 0.68), L: tint(color, 0.62), P: "#f472b6", W: "#ffffff" };
    var rects = "";
    rows.forEach(function (row, y) {
      var x = 0;
      while (x < row.length) {
        var c = row.charAt(x);
        if (c === ".") { x++; continue; }
        var run = 1;
        while (x + run < row.length && row.charAt(x + run) === c) run++;
        rects += '<rect x="' + x + '" y="' + y + '" width="' + run + '" height="1" fill="' + palette[c] + '"/>';
        x += run;
      }
    });
    var size = px || 4;
    return '<svg viewBox="0 0 16 12" width="' + 16 * size + '" height="' + 12 * size + '" shape-rendering="crispEdges" aria-hidden="true">' + rects + "</svg>";
  }

  window.QzPets = { names: Object.keys(PET_SPRITES), labels: LABELS, defaultColors: DEFAULT_COLORS, svg: svg, sprites: PET_SPRITES };
})();
