# Roadmap — Ortho Board Study Guide

This is the master tracker and procedure for building the interactive
subspecialty study guide. It is written for future Claude Code sessions (and
the maintainer) so each session can pick up one subspecialty and finish it
without re-deriving the pipeline.

## What this project is

Turn two source files into an interactive, subspecialty-organized study guide
of **high-yield, sourced facts** — the topics needed to answer the Royal
College (Canadian) orthopaedic exam recall questions, **without reproducing the
questions themselves.**

- `2025 National Consensus-3.xlsx` — recall question bank, 2003–2025 (~4,810 rows).
- `Ortho Review ... 2Ed.pdf` — 1,028-page textbook, already subspecialty-organized
  and already carrying an inline `[Journal ...]` citation on nearly every fact.

**Core idea:** the textbook is the distilled, sourced content; the question bank
tells us which topics are high-yield and how often they recur. Synthesis =
map tested topics → subspecialty → pull the matching sourced textbook content →
supplement gaps from the journal source list.

## Site design (current edition)

The site adopts the **editorial, frequency-ranked** design of
`Ortho_Board_Study_Guide_2020-2025.html` (a single-file guide a web session
generated from the same recall data), refactored into a **multi-file** site:

- `docs/index.html` — shell: a sticky two-row nav at the very top (subspecialty
  links on the first row, the `Filter` band with search `#q` and the "5+ only"
  toggle `#hy` on the second), then the masthead with the exam-wide "most
  heavily tested" ranking strip, then the sections and the "How this was built"
  appendix (`#method`).
- `docs/assets/styles.css` — the template's CSS **verbatim** (+ a small block
  for dimmed unbuilt-nav items). Google-Fonts `<link>` loads in the user's
  browser; system fonts are the fallback.
- `docs/assets/app.js` — loads each fragment listed in `manifest.json`, injects
  them, fills nav counts / section stats, and wires search + toggle + nav
  highlighting.
- `docs/content/manifest.json` — `[{key,title,q,file,status,order}]`;
  `status:"deep"` = rebuilt, `"todo"` = not yet built (dimmed in nav).
- `docs/sections/<key>.html` — one fragment per subspecialty = a
  `<section class="sub-sec" id="<key>">` of `<article class="topic bN"
  data-n data-search>` cards. **Band `bN` and `data-n` (question count) drive
  the high-yield highlighting** the user cares about.

The original single-file `Ortho_Board_Study_Guide_2020-2025.html` stays at the
repo root as the provenance record for the per-topic frequency data (question
counts, bands and sitting years). All 12 sections have now been mined from it;
it remains the reference if a card's `data-n` or year strings need checking.

## Status

| Subspecialty | Key | Status |
|---|---|---|
| **Basic Science** | `basic-science` | ✅ **55 cards; top 21 deep; all sub-bulleted** |
| **Anatomy** | `anatomy` | ✅ **18 cards; all deep; all sub-bulleted** |
| **Oncology** | `oncology` | ✅ **27 cards; top 11 deep; all sub-bulleted** |
| **Hand & Wrist** | `hand-and-wrist` | ✅ **24 cards; top 13 deep; all sub-bulleted** |
| **Elbow** | `elbow` | ✅ **16 cards; top 14 deep; all sub-bulleted** |
| **Shoulder** | `shoulder` | ✅ **21 cards; top 12 deep; all sub-bulleted** |
| **Foot & Ankle** | `foot-and-ankle` | ✅ **28 cards; top 12 deep; all sub-bulleted** |
| **Lower Extremity Recon** | `lower-extremity-recon` | ✅ **17 cards; top 10 deep; all sub-bulleted** |
| **Paediatrics** | `paediatrics` | ✅ **49 cards; top 20 deep; all sub-bulleted** |
| **Spine** | `spine` | ✅ **23 cards; top 12 deep; all sub-bulleted** |
| **Sports** | `sports` | ✅ **14 cards; all deep; all sub-bulleted** |
| **Trauma** | `trauma` | ✅ **26 cards; top 14 deep; all sub-bulleted** |

**All 12 subspecialties are rebuilt** — 318 topic cards, 44 inline SVG figures,
covering all 1,247 recalled questions from 2020–2025. Every card is
sub-bulleted and carries its own reference list.

**Four reference appendices** (256 entries) are ported verbatim from
`Ortho_Board_Study_Guide_2020-2025-2.html`, the later template revision that
introduced them: `appendix-genetics` (83), `appendix-views` (52),
`appendix-angles` (64) and `appendix-osteotomies` (57). They are
`<section class="sub-sec appendix">` fragments holding one `table.ref-tbl`
each — no `.topic` cards — so they carry `"kind": "appendix"` in the manifest.
app.js groups their nav links behind an "Appendices" divider, filters their
rows on search, and hides them under "5+ only" (a question-frequency filter
that cannot apply to them).

Note: that same template revision also has larger subspecialty sections than
the first one (notably Paediatrics and Trauma). Its topic set is identical —
318 cards, same keys — so only the appendices were taken; the rebuilt
subspecialty sections in `docs/sections/` are unaffected.

Future work is deepening rather than building: the remaining "carried" cards
(the lower-frequency cards in Foot & Ankle, Paediatrics, Basic Science,
Oncology, Hand & Wrist, Shoulder, Spine and Trauma that still sit at ~4
references) can be brought up to the 8–12 reference standard using the same
per-card recipe below.

## Per-subspecialty recipe (the procedure)

For subspecialty `<key>`:

1. **Start from the template.** In `Ortho_Board_Study_Guide_2020-2025.html`, the
   `<section id="<key>">` already has every topic as a card with its **band,
   `data-n` (question count) and "X of 7 sittings"/year strings** — this is the
   frequency/highlighting data. Reuse it verbatim as the skeleton.
2. **Pick the deep set:** the ~10–15 highest-`data-n` topics. These get rebuilt;
   lower-frequency cards are carried over from the template so the section stays
   whole.
3. **Synthesise each deep topic** into ~8–14 points (with `<b>` high-yield
   highlights and `<ul class="sub">` sub-bullets) + **~8–12 references**, merging:
   the template's points + sourced facts from `data/textbook/<key>.md` (and
   `data/textbook/trauma.md` etc. — **follow the questions, not just the
   section**; regional fractures live under trauma) + landmark and **Canadian**
   evidence. Each subtopic is its own small research synthesis, not a translation.
4. **Figures:** reuse the template's SVGs for that section (extract the
   `<figure class="fig">…</figure>` blocks and inline them via a `<!--FIG:x-->`
   placeholder + a small python assembler, as done for F&A). Add new SVGs only
   if worthwhile — they are context-expensive.
5. **Assemble** `docs/sections/<key>.html`: `<section>` header (hardcode
   `sec-stats` or set `data-auto="1"` to let JS compute) + deep cards + verbatim
   cards, ordered by `data-n` descending. **Never include verbatim question text.**
6. **Flip status** to `deep` in `docs/content/manifest.json` and this table.
7. **Verify** (below), commit, push.

Context tip: keep big SVG/verbatim blocks out of your working context — stage
them to scratch with a script and assemble on disk (see the F&A build).

### House style: every card is sub-bulleted
**All cards — deep AND carried-over — use the same shape:** each top-level
`<li>` is a short **bold lead-in** naming the concept, followed by a nested
`<ul class="sub">` that splits the facts one per bullet. Keep classifications
and lists (Sanders I–IV, Hawkins, Wagner, Young-Burgess, Gustilo, Pauwels…) as
clean one-item-per-line sub-lists. Preserve `<b>` high-yield highlights.
The template's cards arrive as one dense line of prose — **they must be
converted**, not pasted as-is.

Context tip for the conversion: append the carried cards to the section file
first, then replace each `<ul class="points">…` line **by line number with a
small python script**. That keeps the long prose out of your working context
and preserves headers, figures and `<details class="refs">` automatically.

### Definition of done (per subspecialty section)
- Deep topics have ~8–12 references each; every major point is defensible.
- No verbatim exam question text anywhere (concepts + teaching points only).
- Bands/`data-n` preserved from the template so highlighting + "5+ only" work.
- **Every card sub-bulleted per the house style above** (verify: card count ==
  count of cards containing a `ul.sub`; zero `<ul class="points"><li>` remain).
- Balanced tags (`<ul>`/`</ul>`, `<li>`/`</li>`) — check before committing.
- Renders in the site (nav link active, cards/figures/refs show, search finds it).

## Data reference

Regenerate everything with the scripts in `scripts/` (idempotent):

```
python3 scripts/convert_excel.py       # -> data/questions.json, questions_recent.json
python3 scripts/extract_images.py      # -> data/images/*, anchors.json
python3 scripts/extract_textbook.py    # -> data/textbook_toc.json, data/textbook/<sub>.md
python3 scripts/classify_questions.py  # adds subspecialty to question JSON; classification_review.json
```

**`data/questions.json` / `questions_recent.json`** — one record per question:
`id, year, sheet, q_number, question, options, consensus_answer, evidence,
topic_hint, repeat_of, has_image, row, subspecialty, subspecialty_confidence,
subspecialty_margin`.

**`data/images/`** — 15 extracted clinical images + `anchors.json` (image→cell)
+ `image_descriptions.json` (modality, description, tested_topic, subspecialty).
Several "images" are Orthobullets/journal screenshots pasted as evidence, not films.

**`data/textbook/<sub>.md`** — textbook text chunked by outline heading, inline
citations preserved. **Heading page-spans can lag the content by a page** (topics
cross PDF page boundaries), so read the body, not just the nearest heading.

**`data/textbook_toc.json`** — every outline heading with `depth, title, start,
end, subspecialty`.

**`data/classification_review.json`** — low-confidence classifications to sanity-check.

## Known gaps & notes

- **No dedicated "anatomy" section in the textbook** — resolved. Anatomy and
  surgical approaches are embedded across the other textbook sections, so the
  `anatomy` fragment was sourced primarily from **Hoppenfeld, deBoer & Buckley's
  *Surgical Exposures in Orthopaedics*** plus the primary anatomic literature
  (Gautier/Ganz on the MFCA, Letournel, Seebacher, Blair & Botte, Lanz, Hettrich)
  rather than from `data/textbook/*.md`. All 18 cards are deep as a result, and
  the section carries 7–11 references per card.
- **Oncology has very few inline textbook citations** (~7) — that section uses a
  different reference style. Expect to supplement heavily from Dahlin's *Bone
  Tumors*, Enneking principles, MSTS, and *J Surgical Oncology*.
- **Subspecialty classification is a heuristic** (keyword + textbook-title based).
  Broad terms ("fracture", "dislocation") are down-weighted. Always sanity-check
  a subspecialty's pulled questions before writing (Foot & Ankle, for example,
  legitimately pulls fracture topics that physically live in the trauma chapter).
- **Prioritization = recent consensus years (2018–2025) + Controversial.** Older
  years are converted and available for recurrence counts but don't set priority.

## Environment gotchas

- System `cryptography` is broken until `pip install cffi` (imports fail with
  `_cffi_backend` otherwise). `pdfminer.six` and `openpyxl` then work.
- **PyMuPDF (`pip install pymupdf`, import `fitz`)** is the reliable PDF tool
  here — gives TOC-with-page-numbers + clean text. `pdftoppm`/poppler is NOT
  installed, so the Read tool cannot render PDF pages (it can render the 15
  extracted PNG/JPG images with vision).
- **The PDF outline is FLAT** — every entry reports `level 1`. Hierarchy is
  inferred from ALL-CAPS banners vs Title-Case topics (see `extract_textbook.py`).
- Runtime **CDNs are blocked by the agent proxy** in this environment. The site
  uses no runtime JS CDNs; the only CDN reference is the Google-Fonts `<link>`,
  which fails silently here but loads in the user's browser (system-font
  fallbacks cover it). Do not rely on any CDN in the sandbox.

## The site

- `docs/` is the GitHub Pages root. `index.html` (shell) + `assets/app.js`
  load per-subspecialty fragments from `docs/sections/*.html` listed in
  `docs/content/manifest.json`. Fragments are directly viewable on GitHub.
- To view locally: `cd docs && python3 -m http.server` then open
  `http://localhost:8000` (must be served over HTTP — `fetch` fails on `file://`).
- Verify with headless Chromium: `require('/opt/node22/lib/node_modules/playwright')`,
  `executablePath:'/opt/pw-browsers/chromium'` (see the F&A build for a script).
- To enable Pages: repo **Settings → Pages → Source: Deploy from a branch →
  Branch: `main` (or the working branch) / folder: `/docs`.** (A human toggles
  this once.)
