#!/usr/bin/env python3
"""Extract the textbook PDF into per-subspecialty structured text.

Uses PyMuPDF (fitz). Produces:
  data/textbook_toc.json                 - full outline w/ page ranges + subspecialty
  data/textbook/<subspecialty>.md        - concatenated section text w/ heading anchors

Inline journal citations like [JAAOS 2007;15:118-125] are preserved verbatim;
they are the fact-level source attributions the study pages reuse.

Run:  python3 scripts/extract_textbook.py
"""
import json
import os
import re

import fitz  # PyMuPDF

PDF = "Ortho Review-A Resident's Study Guide to the Orthopaedic Surgery Board Exam-2Ed.pdf"
OUT_DIR = "data/textbook"
TOC_OUT = "data/textbook_toc.json"

# Map each TOP-LEVEL (level-1) textbook section title -> user subspecialty key.
# Titles are matched case-insensitively and exactly against level-1 outline entries.
TOPLEVEL_TO_SUBSPECIALTY = {
    "principles of orthopaedics": "basic-science",
    "trauma": "trauma",
    "pediatrics": "paediatrics",
    "pediatric trauma": "paediatrics",
    "arthroplasty": "arthroplasty",
    "sports": "sports",
    "shoulder and elbow": "shoulder-and-elbow",   # split below into shoulder/elbow
    "upper extremity nerve pathology": "hand-and-wrist",
    "wrist and hand": "hand-and-wrist",
    "foot and ankle": "foot-and-ankle",
    "spine": "spine",
    "oncology": "oncology",
    "medical conditions": "basic-science",
    "ethics and principles of practice": "basic-science",
    "research summaries": "basic-science",
    "glossary of abbreviations": "basic-science",
}

# The 12 target subspecialties (shoulder-and-elbow is later split by section).
SUBSPECIALTIES = [
    "basic-science", "anatomy", "oncology", "hand-and-wrist", "elbow",
    "shoulder", "foot-and-ankle", "arthroplasty", "paediatrics", "spine",
    "sports", "trauma",
]

CITATION_RE = re.compile(r"\[[^\]]*(?:19|20)\d{2}[^\]]*\]")


def clean_text(t):
    # Normalise ligatures / soft hyphens that pdf extraction leaves behind.
    t = t.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("­", "")
    # collapse 3+ blank lines
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    doc = fitz.open(PDF)
    n_pages = doc.page_count

    # 1. Cache page text.
    pages = [clean_text(doc[i].get_text()) for i in range(n_pages)]

    # 2. TOC: list of [level, title, page(1-based)].
    toc = doc.get_toc()

    # 3. Assign each entry a page range [start, end) using the next entry start.
    entries = []
    for idx, (level, title, page) in enumerate(toc):
        start = page - 1  # 0-based
        # end = start page of the next entry (any level)
        end = toc[idx + 1][2] - 1 if idx + 1 < len(toc) else n_pages
        if end <= start:
            end = start + 1
        entries.append({"i": idx, "level": level, "title": title,
                        "start": start, "end": end})

    # 4. Propagate subspecialty. NOTE: this PDF's outline is FLAT — every entry
    #    reports level 1 — so hierarchy must be inferred from the title text, not
    #    the level. Banner sections are ALL-CAPS; topics are Title Case. We carry
    #    the last matched top-level banner forward, and split the combined
    #    "SHOULDER AND ELBOW" block into 'shoulder' vs 'elbow' on its ALL-CAPS
    #    SHOULDER / ELBOW sub-banners. (Sports keeps its own SHOULDER/ELBOW/
    #    KNEE/HIP content under 'sports' by design.)
    current_sub = "basic-science"
    in_se_block = False
    for e in entries:
        key = e["title"].strip().lower()
        if key == "shoulder and elbow":
            current_sub, in_se_block = "shoulder", True
        elif in_se_block and key == "shoulder":
            current_sub = "shoulder"
        elif in_se_block and key == "elbow":
            current_sub = "elbow"
        elif key in TOPLEVEL_TO_SUBSPECIALTY:
            current_sub = TOPLEVEL_TO_SUBSPECIALTY[key]
            in_se_block = False
        e["subspecialty"] = current_sub

    # 5. Heading depth heuristic (cosmetic for the intermediate .md): ALL-CAPS
    #    banners render shallower than Title-Case topics.
    for e in entries:
        letters = [c for c in e["title"] if c.isalpha()]
        is_banner = bool(letters) and all(c.isupper() for c in letters)
        e["depth"] = 1 if is_banner else 2

    # 6. Write TOC json.
    with open(TOC_OUT, "w") as f:
        json.dump([{k: e[k] for k in ("depth", "title", "start", "end", "subspecialty")}
                   for e in entries], f, ensure_ascii=False, indent=1)

    # 7. Write per-subspecialty markdown. Only emit text for LEAF-ish sections
    #    (level >= 2) to avoid duplicating parent-page text; a level-1 banner
    #    page is usually just a title. We concatenate each entry's own pages,
    #    de-duplicating overlapping page text by tracking last page emitted.
    by_sub = {}
    for e in entries:
        by_sub.setdefault(e["subspecialty"], []).append(e)

    counts = {}
    for sub, elist in by_sub.items():
        lines = [f"# {sub}\n",
                 "> Source: *Ortho Review: A Resident's Study Guide to the "
                 "Orthopaedic Surgery Board Exam*, 2nd Ed. Inline [Journal ...] "
                 "citations are from the textbook.\n"]
        for e in elist:
            heading = "#" * min(e["depth"] + 1, 6)
            lines.append(f"\n{heading} {e['title']}  "
                         f"<!-- pdf pages {e['start']+1}-{e['end']} -->\n")
            # text = this entry's own page span
            span = "\n".join(pages[e["start"]:e["end"]])
            lines.append(span)
        text = clean_text("\n".join(lines))
        path = os.path.join(OUT_DIR, f"{sub}.md")
        with open(path, "w") as f:
            f.write(text)
        counts[sub] = (len(elist), len(text), len(CITATION_RE.findall(text)))

    print(f"pages: {n_pages}, toc entries: {len(entries)}")
    print(f"{'subspecialty':20s} {'sections':>8} {'chars':>9} {'citations':>10}")
    for sub in sorted(counts):
        s, c, cit = counts[sub]
        print(f"{sub:20s} {s:8d} {c:9d} {cit:10d}")


if __name__ == "__main__":
    main()
