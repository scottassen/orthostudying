/* Multi-file loader + interactions for the board-review site.
 * Loads per-subspecialty HTML fragments (template card markup) listed in
 * content/manifest.json, injects them, then wires the template's search,
 * "5+ only" toggle and IntersectionObserver nav highlighting over the
 * assembled DOM. Nav is built from the manifest so unbuilt sections show
 * dimmed and the whole thing updates as sections are added.
 */
(function () {
  "use strict";

  var navLinks = document.getElementById("nav-links");
  var sectionsEl = document.getElementById("sections");
  var foBuilt = document.getElementById("fo-built");

  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;"); }

  function buildNav(man) {
    var built = 0;
    man.subspecialties.forEach(function (sp) {
      var isBuilt = sp.status && sp.status !== "todo";
      if (isBuilt) built++;
      var count = '<span class="nav-n">' + sp.q + "</span>";
      if (isBuilt) {
        var a = document.createElement("a");
        a.href = "#" + sp.key;
        a.innerHTML = esc(sp.title) + count;
        navLinks.appendChild(a);
      } else {
        var s = document.createElement("span");
        s.className = "nav-todo";
        s.title = "Not yet built in this edition";
        s.innerHTML = esc(sp.title) + count;
        navLinks.appendChild(s);
      }
    });
    if (foBuilt) foBuilt.querySelector("b").textContent = built;
    syncNavFade();
  }

  // The link strip carries a right-edge fade so a truncated row reads as
  // scrollable. Drop it when everything already fits.
  function syncNavFade() {
    if (!navLinks) return;
    navLinks.classList.toggle("no-fade", navLinks.scrollWidth <= navLinks.clientWidth + 2);
  }

  // Keep anchor jumps clear of the sticky nav, whatever height it ends up.
  function syncScrollPadding() {
    var nav = document.querySelector(".nav");
    if (nav) document.documentElement.style.scrollPaddingTop = (nav.offsetHeight + 14) + "px";
  }

  function loadFragments(man) {
    var built = man.subspecialties
      .filter(function (sp) { return sp.status && sp.status !== "todo"; })
      .sort(function (a, b) { return a.order - b.order; });
    return Promise.all(built.map(function (sp) {
      return fetch("sections/" + sp.file, { cache: "no-cache" })
        .then(function (r) { return r.ok ? r.text() : ""; })
        .then(function (html) { return { order: sp.order, html: html }; })
        .catch(function () { return { order: sp.order, html: "" }; });
    })).then(function (parts) {
      parts.sort(function (a, b) { return a.order - b.order; });
      sectionsEl.innerHTML = parts.map(function (p) { return p.html; }).join("\n");
    });
  }

  /* Fill each section's .sec-stats from its own cards if left empty, and
   * compute the "tested 5x or more" tally. */
  function fillSectionStats() {
    [].slice.call(document.querySelectorAll(".sub-sec")).forEach(function (sec) {
      var stats = sec.querySelector(".sec-stats");
      if (!stats || stats.dataset.auto !== "1") return;
      var cards = sec.querySelectorAll(".topic");
      var q = 0, hi = 0;
      cards.forEach(function (c) {
        var n = +c.dataset.n || 0;
        q += n; if (n >= 5) hi++;
      });
      stats.innerHTML =
        "<span><b>" + q + "</b> questions</span>" +
        "<span><b>" + cards.length + "</b> topics</span>" +
        "<span><b>" + hi + "</b> tested 5&#215; or more</span>";
    });
  }

  function wireInteractions() {
    var q = document.getElementById("q"),
        hy = document.getElementById("hy"),
        cards = [].slice.call(document.querySelectorAll(".topic")),
        secs = [].slice.call(document.querySelectorAll(".sub-sec")),
        nohits = document.getElementById("nohits"),
        method = document.getElementById("method"),
        methodLink = document.getElementById("method-link"),
        onlyHY = false;

    function apply() {
      var term = (q.value || "").trim().toLowerCase(), shown = 0;
      cards.forEach(function (c) {
        var hay = c.dataset.search || c.textContent.toLowerCase();
        var okT = !term || hay.indexOf(term) > -1;
        var okN = !onlyHY || (+c.dataset.n) >= 5;
        var ok = okT && okN;
        c.classList.toggle("hidden", !ok);
        if (ok) shown++;
      });
      secs.forEach(function (s) {
        s.classList.toggle("hidden", !s.querySelector(".topic:not(.hidden)"));
      });
      if (nohits) nohits.classList.toggle("hidden", shown > 0);
      // the methodology appendix is not a topic — hide it while filtering
      if (method) method.classList.toggle("hidden", !!term || onlyHY);
      if (methodLink) methodLink.classList.toggle("hidden", !!term || onlyHY);
    }
    // The page is ~445,000px tall; a smooth scroll to the appendix would
    // take an age, so jump straight there.
    if (methodLink && method) methodLink.addEventListener("click", function (e) {
      e.preventDefault();
      var nav = document.querySelector(".nav");
      var top = method.getBoundingClientRect().top + window.scrollY - ((nav ? nav.offsetHeight : 0) + 14);
      window.scrollTo({ top: top, behavior: "auto" });
    });

    if (q) q.addEventListener("input", apply);
    if (hy) hy.addEventListener("click", function () {
      onlyHY = !onlyHY;
      hy.setAttribute("aria-pressed", onlyHY);
      hy.textContent = onlyHY ? "All topics" : "5+ only";
      apply();
    });

    var links = [].slice.call(document.querySelectorAll(".nav a"));
    if (window.IntersectionObserver && links.length) {
      var obs = new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (e.isIntersecting) {
            links.forEach(function (a) {
              a.classList.toggle("on", a.getAttribute("href") === "#" + e.target.id);
            });
          }
        });
      }, { rootMargin: "-96px 0px -70% 0px" });
      secs.forEach(function (s) { obs.observe(s); });
    }
  }

  fetch("content/manifest.json", { cache: "no-cache" })
    .then(function (r) { return r.json(); })
    .then(function (man) {
      if (man.title) document.title = man.title;
      buildNav(man);
      return loadFragments(man);
    })
    .then(function () {
      fillSectionStats();
      wireInteractions();
      syncScrollPadding();
      syncNavFade();
      window.addEventListener("resize", function () {
        syncScrollPadding();
        syncNavFade();
      });
    })
    .catch(function () {
      sectionsEl.innerHTML =
        '<p style="padding:40px 0;color:var(--sig);font-family:var(--f-mono)">' +
        "Could not load content. If viewing locally, serve over HTTP (see README).</p>";
    });
})();
