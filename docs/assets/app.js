/* App: tabs, lazy markdown loading, collapsible topics, global search. */
(function () {
  "use strict";

  var manifest = null;
  var cache = {};            // key -> { html, text, sections:[{title, plain}] }
  var active = null;
  var els = {
    tabs: document.getElementById("tabs"),
    content: document.getElementById("content"),
    search: document.getElementById("search"),
    title: document.getElementById("site-title"),
    subtitle: document.getElementById("site-subtitle"),
    progress: document.getElementById("progress"),
    themeToggle: document.getElementById("theme-toggle"),
  };

  /* ---------- theme ---------- */
  function initTheme() {
    var saved = localStorage.getItem("ortho-theme");
    var theme = saved || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
    els.themeToggle.addEventListener("click", function () {
      var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("ortho-theme", next);
    });
  }

  /* ---------- content transform ----------
   * Turn rendered HTML into topic cards: each <h2> starts a collapsible <details>
   * that holds everything up to the next <h2>. Everything before the first <h2>
   * (intro/legend) stays as a plain block.
   */
  function buildCards(rawHtml) {
    var tmp = document.createElement("div");
    tmp.innerHTML = rawHtml;
    var out = document.createElement("div");
    var nodes = Array.prototype.slice.call(tmp.childNodes);
    var current = null, currentBody = null;
    var sections = [];

    nodes.forEach(function (node) {
      if (node.nodeType === 1 && node.tagName === "H1") {
        return; // page title handled in header/tab
      }
      if (node.nodeType === 1 && node.tagName === "H2") {
        var details = document.createElement("details");
        details.className = "topic";
        details.open = false;
        var summary = document.createElement("summary");
        summary.innerHTML = node.innerHTML;
        details.appendChild(summary);
        currentBody = document.createElement("div");
        currentBody.className = "topic-body";
        details.appendChild(currentBody);
        out.appendChild(details);
        current = details;
        sections.push({ title: node.textContent, el: details });
      } else if (current && currentBody) {
        currentBody.appendChild(node);
      } else {
        out.appendChild(node); // pre-first-topic intro
      }
    });
    return { el: out, sections: sections };
  }

  function loadContent(sp) {
    if (cache[sp.key]) return Promise.resolve(cache[sp.key]);
    return fetch("content/" + sp.file, { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.text() : Promise.reject(r.status); })
      .then(function (md) {
        var html = window.MD.render(md);
        var built = buildCards(html);
        var rec = {
          html: html, built: built,
          plain: built.el.textContent.toLowerCase(),
          sections: built.sections,
        };
        cache[sp.key] = rec;
        return rec;
      })
      .catch(function () {
        var rec = { missing: true };
        cache[sp.key] = rec;
        return rec;
      });
  }

  function renderTab(sp) {
    active = sp.key;
    Array.prototype.forEach.call(els.tabs.children, function (b) {
      b.classList.toggle("active", b.dataset.key === sp.key);
    });
    els.content.innerHTML = '<p class="loading">Loading ' + sp.title + "…</p>";
    loadContent(sp).then(function (rec) {
      els.content.innerHTML = "";
      if (rec.missing) {
        els.content.innerHTML =
          '<div class="placeholder"><h2>' + sp.emoji + " " + sp.title + "</h2>" +
          "<p>This subspecialty page hasn't been built yet.</p>" +
          "<p class=\"muted\">Content is generated subspecialty-by-subspecialty — see " +
          "<code>ROADMAP.md</code>. <strong>Foot &amp; Ankle</strong> is the completed sample.</p></div>";
        applySearch();
        return;
      }
      els.content.appendChild(rec.built.el);
      applySearch();
      els.content.scrollTop = 0;
      window.scrollTo(0, 0);
    });
  }

  function buildTabs() {
    manifest.subspecialties.forEach(function (sp) {
      var b = document.createElement("button");
      b.className = "tab" + (sp.status === "done" ? " ready" : "");
      b.dataset.key = sp.key;
      b.innerHTML = '<span class="tab-emoji">' + sp.emoji + "</span>" +
                    '<span class="tab-label">' + sp.title + "</span>" +
                    (sp.status === "done" ? '<span class="dot" title="Complete"></span>'
                                          : '<span class="dot todo" title="Not built yet"></span>');
      b.addEventListener("click", function () { renderTab(sp); });
      els.tabs.appendChild(b);
    });
    var done = manifest.subspecialties.filter(function (s) { return s.status === "done"; }).length;
    els.progress.textContent = done + " / " + manifest.subspecialties.length + " subspecialties complete";
  }

  /* ---------- search ----------
   * Filters topic cards within the ACTIVE tab, and shows a cross-subspecialty
   * hit count. Matching text is not destructively highlighted (keeps markup
   * intact); cards without a match are hidden and non-matches auto-collapse.
   */
  var searchTimer = null;
  function applySearch() {
    var q = els.search.value.trim().toLowerCase();
    var cards = els.content.querySelectorAll("details.topic");
    var shown = 0;
    cards.forEach(function (card) {
      if (!q) { card.style.display = ""; card.open = false; shown++; return; }
      var hay = card.textContent.toLowerCase();
      var match = hay.indexOf(q) !== -1;
      card.style.display = match ? "" : "none";
      card.open = match;
      if (match) shown++;
    });
    // cross-subspecialty tally
    var banner = document.getElementById("search-banner");
    if (!q) { if (banner) banner.remove(); return; }
    var others = [];
    manifest.subspecialties.forEach(function (sp) {
      if (sp.key === active) return;
      var rec = cache[sp.key];
      if (rec && !rec.missing && rec.plain.indexOf(q) !== -1) others.push(sp);
    });
    if (!banner) {
      banner = document.createElement("div");
      banner.id = "search-banner";
      banner.className = "search-banner";
      els.content.insertBefore(banner, els.content.firstChild);
    }
    var msg = shown + " topic" + (shown === 1 ? "" : "s") + " here";
    if (others.length) {
      msg += " · also in: " + others.map(function (sp) {
        return '<a href="#" data-key="' + sp.key + '">' + sp.emoji + " " + sp.title + "</a>";
      }).join(", ");
    }
    banner.innerHTML = "🔎 " + msg;
    banner.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        var sp = manifest.subspecialties.find(function (s) { return s.key === a.dataset.key; });
        renderTab(sp);
      });
    });
  }

  function initSearch() {
    els.search.addEventListener("input", function () {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(applySearch, 120);
    });
    // preload built ("done") content so cross-subspecialty search works;
    // unbuilt pages have no content to search and are skipped (avoids 404 noise)
    manifest.subspecialties.forEach(function (sp) {
      if (sp.status === "done") loadContent(sp);
    });
  }

  /* ---------- boot ---------- */
  fetch("content/manifest.json", { cache: "no-cache" })
    .then(function (r) { return r.json(); })
    .then(function (m) {
      manifest = m;
      els.title.textContent = m.title.split("—")[0].trim() || m.title;
      els.subtitle.textContent = m.subtitle || "";
      document.title = m.title;
      initTheme();
      buildTabs();
      initSearch();
      // open the first completed subspecialty, else the first tab
      var first = m.subspecialties.find(function (s) { return s.status === "done"; })
                || m.subspecialties[0];
      renderTab(first);
    })
    .catch(function (e) {
      els.content.innerHTML = '<p class="loading">Failed to load manifest. ' +
        "If viewing locally, serve the folder over HTTP (see README).</p>";
    });
})();
