/* AEDIFICA — DATUM · ds.js
   Injects the shared topbar, nav and the mandatory non-authority disclaimer.
   Each page sets <body data-page="key"> and (optionally) data-base="" for path. */
(function () {
  var BASE = document.body.getAttribute("data-base") || "";
  var current = document.body.getAttribute("data-page") || "";

  var NAV = [
    ["index",          "00", "Hub"],
    ["foundations",    "01", "Foundations"],
    ["typography",     "02", "Typography"],
    ["color-states",   "03", "Color & States"],
    ["logo",           "04", "Logo"],
    ["iconography",    "05", "Iconography"],
    ["components",     "06", "Components"],
    ["report-a4",      "07", "Report A4"],
    ["data-contract",  "08", "Data Contract"],
    ["accessibility-qa","09","Accessibility / QA"],
    ["implementation", "10", "Implementation"]
  ];

  var WORDMARK = '<span class="ds-wordmark" style="font-size:22px"><span class="ae">\u00C6</span>DIFICA</span>';

  var navLinks = NAV.map(function (n) {
    var href = (n[0] === "index" ? "index.html" : n[0] + ".html");
    var cur = n[0] === current ? ' aria-current="page"' : "";
    return '<a href="' + BASE + href + '"' + cur + '><span class="num">' + n[1] + '</span>' + n[2] + '</a>';
  }).join("");

  var header =
    '<header class="ds-topbar"><div class="ds-topbar__row">' +
      '<a class="ds-brand" href="' + BASE + 'index.html">' + WORDMARK +
        '<span class="ds-brand__sub">Datum · design system</span>' +
      '</a>' +
      '<span class="ds-ver">v4 · 2026-05-31 · <b>VALIDATED 02A</b></span>' +
    '</div></header>' +
    '<nav class="ds-nav"><div class="ds-nav__row">' + navLinks + '</div></nav>';

  var disclaimer =
    '<footer class="ds-disclaimer"><div class="ds-disclaimer__row">' +
      '<span class="ds-disclaimer__claim"><b>Préparation sourcée par AEDIFICA. Pas une autorité.</b> L\u2019architecte reste responsable de la décision et du dépôt.</span>' +
      '<span class="ds-disclaimer__meta">AEDIFICA — Datum design system · v4<br>Direction 02A · radical Swiss · evidence-backed<br>© 2026 · source of truth, not a mockup</span>' +
    '</div></footer>';

  document.body.insertAdjacentHTML("afterbegin", header);
  document.body.insertAdjacentHTML("beforeend", disclaimer);
})();
