/* Minimal, dependency-free Markdown renderer.
 * Supports the subset used by this project's content:
 *   # .. ###### headings, - / * unordered lists (nested by indent),
 *   1. ordered lists, > blockquotes, --- rules, **bold**, *italic*,
 *   `code`, [text](url), and paragraphs. Content is authored by us
 *   (not user input), so no sanitisation beyond HTML-escaping text.
 */
(function (global) {
  "use strict";

  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function inline(text) {
    var t = esc(text);
    // links [text](url)
    t = t.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, function (_, label, url) {
      return '<a href="' + url + '" target="_blank" rel="noopener">' + label + "</a>";
    });
    // bold then italic then code
    t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    t = t.replace(/(^|[^*])\*([^*]+)\*(?!\*)/g, "$1<em>$2</em>");
    t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
    return t;
  }

  function indentOf(line) {
    var m = line.match(/^(\s*)/);
    return m ? m[1].replace(/\t/g, "    ").length : 0;
  }

  function render(md) {
    var lines = md.replace(/\r\n/g, "\n").split("\n");
    var html = [];
    var i = 0;

    // list stack: each {type:'ul'|'ol', indent:n}
    var listStack = [];
    function closeListsTo(indent) {
      while (listStack.length && listStack[listStack.length - 1].indent >= indent) {
        html.push("</" + listStack.pop().type + ">");
      }
    }
    function closeAllLists() { closeListsTo(-1); }

    var paraBuf = [];
    function flushPara() {
      if (paraBuf.length) {
        html.push("<p>" + inline(paraBuf.join(" ")) + "</p>");
        paraBuf = [];
      }
    }

    var quoteBuf = [];
    function flushQuote() {
      if (quoteBuf.length) {
        html.push("<blockquote>" + inline(quoteBuf.join(" ")) + "</blockquote>");
        quoteBuf = [];
      }
    }

    for (; i < lines.length; i++) {
      var raw = lines[i];
      var line = raw.replace(/\s+$/, "");
      var trimmed = line.trim();

      // blank line
      if (trimmed === "") { flushPara(); flushQuote(); closeAllLists(); continue; }

      // strip HTML comments (used as page-anchors in content)
      if (/^<!--/.test(trimmed) && /-->$/.test(trimmed)) { continue; }

      // horizontal rule
      if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
        flushPara(); flushQuote(); closeAllLists();
        html.push("<hr />"); continue;
      }

      // heading
      var h = trimmed.match(/^(#{1,6})\s+(.*)$/);
      if (h) {
        flushPara(); flushQuote(); closeAllLists();
        var lvl = h[1].length;
        // strip trailing " <!-- ... -->" already handled; strip trailing #s
        var txt = h[2].replace(/\s+#+\s*$/, "");
        html.push("<h" + lvl + ">" + inline(txt) + "</h" + lvl + ">");
        continue;
      }

      // blockquote
      var bq = trimmed.match(/^>\s?(.*)$/);
      if (bq) { flushPara(); closeAllLists(); quoteBuf.push(bq[1]); continue; }
      else { flushQuote(); }

      // list item (ul or ol)
      var ind = indentOf(raw);
      var ul = trimmed.match(/^[-*+]\s+(.*)$/);
      var ol = trimmed.match(/^(\d+)[.)]\s+(.*)$/);
      if (ul || ol) {
        flushPara();
        var type = ul ? "ul" : "ol";
        var itemText = ul ? ul[1] : ol[2];
        // manage nesting by indent
        closeListsTo(ind + 1);
        var top = listStack[listStack.length - 1];
        if (!top || top.indent < ind) {
          html.push("<" + type + ">");
          listStack.push({ type: type, indent: ind });
        } else if (top.type !== type) {
          html.push("</" + listStack.pop().type + ">");
          html.push("<" + type + ">");
          listStack.push({ type: type, indent: ind });
        }
        html.push("<li>" + inline(itemText) + "</li>");
        continue;
      }

      // plain paragraph text
      closeAllLists();
      paraBuf.push(trimmed);
    }

    flushPara(); flushQuote(); closeAllLists();
    return html.join("\n");
  }

  global.MD = { render: render, inline: inline, esc: esc };
})(window);
