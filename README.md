# Orthopaedic Board Review — High-Yield Study Guide

An interactive, subspecialty-organized study guide for the Royal College
(Canadian) orthopaedic surgery exam. It distils the **topics tested** in the
2003–2025 national consensus recall bank into concise, **sourced** high-yield
facts — organized one page per subspecialty. **The exam questions themselves are
never reproduced;** only the topics they test, with a lookup-able citation on
every major fact.

The site uses an **editorial, frequency-ranked** format: each topic is a card
whose question count and color-coded left border show how heavily it was tested
(2020–2025), with a "5+ only" high-yield filter, live search, collapsible
references, and inline SVG figures. Each high-yield subtopic is written as its
own small, heavily-referenced research synthesis.

## View it

- **Interactive site:** the `docs/` folder is a self-contained static site. Once
  GitHub Pages is enabled (Settings → Pages → Deploy from a branch → `/docs`),
  it is browsable online. Locally (must be served over HTTP — the shell fetches
  content fragments):
  ```
  cd docs && python3 -m http.server
  # open http://localhost:8000
  ```
- **Per-subspecialty content on GitHub:** each subspecialty is an HTML fragment
  under [`docs/sections/`](docs/sections/) — e.g. the deep sample
  [`foot-and-ankle.html`](docs/sections/foot-and-ankle.html).
- `Ortho_Board_Study_Guide_2020-2025.html` (repo root) is the original
  single-file template this design is based on — a useful reference for the other
  subspecialties' frequency data until each is rebuilt.

## Status

**Foot & Ankle** is the first fully rebuilt section: its top 12 highest-yield
topics are deep, multi-reference syntheses (with figures); the remaining lower-
frequency F&A topics are carried over from the template. The other 11
subspecialties are not yet rebuilt in this edition — see **[ROADMAP.md](ROADMAP.md)**
for the status table and the per-subspecialty build recipe.

## How it's built

Two source files (the `.xlsx` recall bank and the `.pdf` textbook) are converted
into machine-readable data under [`data/`](data/), then distilled into the
subspecialty pages. The textbook is already subspecialty-organized and carries
inline journal citations, so it is the sourcing backbone; the question bank
determines which topics are high-yield (⭐ = tested in ≥10 separate sittings).

Regenerate the converted data (idempotent):
```
pip install openpyxl pymupdf cffi
python3 scripts/convert_excel.py       # questions -> data/questions*.json
python3 scripts/extract_images.py      # embedded clinical images -> data/images/
python3 scripts/extract_textbook.py    # textbook -> data/textbook/<subspecialty>.md
python3 scripts/classify_questions.py  # tag each question with a subspecialty
```

## Layout

```
docs/                 # GitHub Pages site (editorial, frequency-ranked)
  index.html          #   shell: masthead, nav, search, "5+ only", ranking strip
  assets/             #   styles.css (from template), app.js (fragment loader)
  content/manifest.json  # subspecialty list + build status + question counts
  sections/           #   one HTML fragment per subspecialty (template card markup)
data/                 # machine-readable converted sources (committed)
  questions*.json     #   normalized recall bank
  textbook/           #   textbook text chunked by subspecialty, citations preserved
  textbook_toc.json   #   outline -> page ranges + subspecialty
  images/             #   extracted clinical images + descriptions
scripts/              # reproducible conversion pipeline
ROADMAP.md            # status tracker + per-subspecialty build recipe + gotchas
```

## Sources

Primary backbone: *Ortho Review: A Resident's Study Guide to the Orthopaedic
Surgery Board Exam* (2nd Ed.). Gaps supplemented from the exam's recommended
high-impact journals and references — JBJS, JOT, JAAOS, Bone & Joint Journal,
CORR, AJSM, Arthroscopy, J Arthroplasty, Global Spine Journal, J Hand Surgery
(Am), JSES, Foot & Ankle International, J Pediatric Orthopaedics, J Surgical
Oncology, Injury; Campbell's, Miller's, Rockwood & Green/Wilkins, Tachdjian,
Rothman-Simeone, Green's, Rockwood & Matsen, Morrey, Coughlin & Mann, Dahlin;
plus OKU, Orthobullets, AO Surgery Reference, OTA Core Curriculum, POSNA,
ASSH/ASES/AOFAS/AAHKS/NASS-AO Spine/MSTS, and Canadian (COA) guidance.

> Educational summary for personal exam preparation. Facts are attributed to
> their sources for further reading; consult the primary sources and current
> guidelines for clinical decisions.
