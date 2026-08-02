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

## Status

| Subspecialty | Key | Status |
|---|---|---|
| Basic Science | `basic-science` | ☐ todo |
| Anatomy & Approaches | `anatomy` | ☐ todo (see note) |
| Trauma | `trauma` | ☐ todo |
| Paediatrics | `paediatrics` | ☐ todo |
| Adult Recon / Arthroplasty | `arthroplasty` | ☐ todo |
| Sports | `sports` | ☐ todo |
| Shoulder | `shoulder` | ☐ todo |
| Elbow | `elbow` | ☐ todo |
| Hand & Wrist | `hand-and-wrist` | ☐ todo |
| **Foot & Ankle** | `foot-and-ankle` | ✅ **done (sample/template)** |
| Spine | `spine` | ☐ todo |
| Oncology | `oncology` | ☐ todo |

Update this table and `docs/content/manifest.json` (`status: "done"`) when a
subspecialty page is finished.

## Per-subspecialty recipe (the procedure)

For subspecialty `<key>`:

1. **Pull tested topics.** From `data/questions_recent.json`, take rows where
   `subspecialty == "<key>"` (recent = 2018–2025 + Controversial, which drives
   prioritization). Cross-check `data/questions.json` for older recurrence.
2. **Cluster into topics** and count the number of **distinct exam sittings**
   each topic appears in. A topic tested in **≥10 sittings gets a ⭐** (high-yield).
   (See `scripts/`-style clustering in the git history of the Foot & Ankle build;
   a keyword-bucket script per subspecialty is the quickest way.)
3. **Pull sourced facts** from `data/textbook/<key>.md`. **Follow the questions,
   not just the section** — some tested topics live in a different textbook file
   (e.g. foot/ankle **fractures** are in `data/textbook/trauma.md`; nerve
   compressions may be in hand-and-wrist; spine oncology overlaps oncology).
4. **Distil** each topic to the crucial points needed to answer the tested
   questions. Keep the textbook's inline `[Journal ...]` citation on each fact
   (render it as `[Source: ...]`).
5. **Fill gaps** (topics tested but thin/absent in the textbook) from the journal
   source list in the project brief / `README.md`; cite explicitly. Flag any
   genuinely off-the-cuff fact.
6. **Write** `docs/content/<key>.md` using `docs/content/_TEMPLATE.md`. Add the
   `> Tested: <years>` line to every topic. **Never include verbatim question text.**
7. **Flip status** to `done` in `docs/content/manifest.json` and this table.
8. **Verify** (see below), commit, push.

### Definition of done (per subspecialty page)
- Every major bullet has a lookup-able `[Source: ...]`.
- No verbatim exam question text anywhere (topics + facts only).
- High-yield topics flagged with ⭐; each topic has a `> Tested:` year line.
- Renders correctly in the site (tab loads, collapsibles open, search finds it).

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

- **No dedicated "anatomy" section in the textbook.** Anatomy/surgical approaches
  are embedded across sections (esp. spine "Surgical Techniques", trauma
  approaches, and Hoppenfeld-style internervous planes). Build `anatomy` by
  harvesting approach/anatomy facts across `data/textbook/*.md` and the source
  list (Hoppenfeld's *Surgical Exposures*), driven by the ~38 anatomy-classified
  questions.
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
- Runtime **CDNs are blocked** by the agent proxy — the site vendors its own
  tiny markdown renderer (`docs/assets/md.js`); do not add CDN `<script>` tags.

## The site

- `docs/` is the GitHub Pages root (single-page app: tabs, collapsibles,
  client-side search across built pages). Content is `docs/content/<key>.md`,
  also directly viewable on GitHub for WIP.
- To view locally: `cd docs && python3 -m http.server` then open
  `http://localhost:8000` (it must be served over HTTP — `fetch` fails on `file://`).
- To enable Pages: repo **Settings → Pages → Source: Deploy from a branch →
  Branch: `main` (or the working branch) / folder: `/docs`.** (This is a repo
  setting a human must toggle once.)
