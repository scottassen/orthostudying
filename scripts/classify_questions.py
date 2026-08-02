#!/usr/bin/env python3
"""Classify each question into one of the 12 subspecialties.

Strategy (the year sheets carry no subspecialty tag):
  1. Strong signal: the Controversial sheet's explicit `topic_hint` column.
  2. Keyword scoring: curated high-signal keyword lists per subspecialty, plus
     distinctive words harvested from the textbook TOC topic titles.
  3. Assign the best-scoring subspecialty; record confidence = top score and
     the margin over the runner-up. Low-margin / zero-score rows are flagged
     for manual review.

Reads   : data/questions.json, data/questions_recent.json, data/textbook_toc.json
Writes  : same files, each record gains {subspecialty, subspecialty_confidence}
          data/classification_review.json  (low-confidence rows to eyeball)
          prints a distribution summary

Run:  python3 scripts/classify_questions.py
"""
import json
import re
from collections import Counter

SUBS = ["basic-science", "anatomy", "oncology", "hand-and-wrist", "elbow",
        "shoulder", "foot-and-ankle", "arthroplasty", "paediatrics", "spine",
        "sports", "trauma"]

# Map the textbook_toc subspecialty keys onto our 12 (they already align, but
# shoulder/elbow are separate and there is no textbook 'anatomy' section).
TOC_SUB_MAP = {s: s for s in SUBS}

# Curated high-signal keywords. Order matters only for tie-breaking via WEIGHTS.
KEYWORDS = {
    "paediatrics": [
        "child", "pediatric", "paediatric", "infant", "adolescent", "physis",
        "physeal", "scfe", "slipped capital", "perthes", "ddh", "dysplasia of the hip",
        "clubfoot", "tarsal coalition", "blount", "cerebral palsy", "osteogenesis imperfecta",
        "rickets", "scoliosis", "supracondylar", "salter", "nonaccidental",
        "non-accidental", "child abuse", "apophys", "tibial spine", "genu var",
        "genu valg", "in-toeing", "intoeing", "skeletally immature", "growth plate",
        "year-old boy", "year-old girl", "yo boy", "yo girl", "leg length discrepancy",
    ],
    "oncology": [
        "tumor", "tumour", "sarcoma", "osteosarcoma", "chondrosarcoma", "ewing",
        "metasta", "enchondroma", "osteochondroma", "giant cell tumor", "gct",
        "aneurysmal bone cyst", "unicameral", "fibrous dysplasia", "chordoma",
        "myeloma", "lymphoma", "biopsy", "enneking", "pvns", "lipoma", "chondroblastoma",
        "nonossifying fibroma", "osteoid osteoma", "osteoblastoma", "adamantinoma",
        "soft tissue mass", "malignant", "benign lesion", "staging", "margins",
        "desmoid", "melorheostosis", "wide resection",
    ],
    "spine": [
        "spine", "spinal", "cervical", "lumbar", "thoracolumbar", "vertebra",
        "disc herniation", "radiculopathy", "myelopathy", "stenosis", "spondylo",
        "scoliosis", "kyphosis", "cauda equina", "odontoid", "atlas", "axis",
        "hangman", "acdf", "laminectomy", "fusion", "opll", "cord injury",
        "central cord", "brown-sequard", "ankylosing spond", "pedicle screw",
        "cervical spine", "burst fracture", "chance fracture",
    ],
    "arthroplasty": [
        "arthroplasty", "tka", "tha", "total knee", "total hip", "revision",
        "periprosthetic", "prosthetic joint infection", "pji", "polyethylene",
        "osteolysis", "aseptic loosening", "uka", "unicompartmental", "resurfacing",
        "acetabular component", "femoral stem", "liner", "dair", "vancouver",
        "metal on metal", "ceramic", "constraint", "hip resurfacing", "corrosion",
        "trunnion", "protrusio", "pelvic discontinuity",
    ],
    "sports": [
        "acl", "pcl", "mcl", "lcl", "meniscus", "meniscal", "cartilage", "chondral",
        "osteochondritis", "patellar instability", "labral", "labrum", "fai",
        "femoroacetabular", "rotator cuff", "slap", "shoulder instability",
        "bankart", "hill-sachs", "hill sachs", "dislocation of the shoulder",
        "return to play", "hamstring", "quadriceps tendon", "posterolateral corner",
        "microfracture", "aclr", "graft", "hip arthroscopy", "snapping hip",
        "throwing", "internal impingement", "ulnar collateral ligament",
        "tennis elbow", "lateral epicondylitis",
    ],
    "shoulder": [
        "glenohumeral", "reverse total shoulder", "rtsa", "total shoulder arthroplasty",
        "cuff tear arthropathy", "adhesive capsulitis", "frozen shoulder",
        "glenoid", "proximal humerus arthroplasty", "teres minor", "scapula",
        "acromioclavicular", "clavicle",
    ],
    "elbow": [
        "elbow", "olecranon", "coronoid", "radial head", "distal biceps",
        "terrible triad", "capitellum", "monteggia", "total elbow arthroplasty",
        "posterolateral rotatory", "epicondyle",
    ],
    "hand-and-wrist": [
        "wrist", "hand", "scaphoid", "carpal", "scapholunate", "lunate",
        "kienbock", "trapezio", "cmc", "dupuytren", "trigger finger", "mallet",
        "flexor tendon", "distal radius", "druj", "tfcc", "metacarpal", "phalan",
        "thumb", "boutonniere", "swan neck", "de quervain", "carpal tunnel",
        "cubital tunnel", "ulnar nerve", "median nerve", "radial nerve",
        "pronator", "digit", "finger", "bennett", "rolando",
    ],
    "foot-and-ankle": [
        "hallux", "bunion", "bunionette", "hammertoe", "lesser toe", "midfoot",
        "hindfoot", "forefoot", "achilles", "plantar fasci", "morton",
        "peroneal tendon", "posterior tibial tendon", "pttd", "flatfoot",
        "cavovarus", "charcot", "diabetic foot", "ankle instability",
        "osteochondral lesion of the talus", "olt", "turf toe", "subtalar",
        "triple arthrodesis", "ankle arthritis", "hallux rigidus", "metatarsal",
        "lisfranc", "calcaneus", "talus", "navicular", "syndesmosis", "ankle fracture",
    ],
    "trauma": [
        "fracture", "nonunion", "malunion", "compartment syndrome", "open fracture",
        "external fixation", "intramedullary nail", "im nail", "orif", "gustilo",
        "damage control", "fat embolism", "polytrauma", "pelvic ring", "acetabular fracture",
        "tibial plateau", "pilon", "femoral shaft", "subtrochanteric", "intertrochanteric",
        "hip fracture", "humeral shaft", "gunshot", "amputation", "dislocation",
        "morel-lavallee", "syndesmotic", "plate", "screw fixation", "traction",
    ],
    "basic-science": [
        "biomechanics", "bone healing", "fracture healing", "collagen", "cartilage biology",
        "stress-strain", "elastic modulus", "wolff", "osteoblast", "osteoclast",
        "vitamin d", "calcium", "pth", "bisphosphonate", "statistics", "sensitivity",
        "specificity", "study design", "power", "biofilm", "antibiotic", "nsaid",
        "gait", "somite", "embryo", "healing", "osteoporosis", "paget", "metabolic bone",
        "coagulation", "tourniquet", "electrocautery", "immunology", "biologic",
        "rheumatoid arthritis", "consent", "ethics", "capacity", "confidentiality",
    ],
    "anatomy": [
        "surgical approach", "approach to the", "internervous plane", "hoppenfeld",
        "safe zone", "at risk during", "nerve at risk", "interval between",
        "landmark", "innervation", "blood supply to", "arterial supply",
    ],
}

# Subspecialties that are broad "catch-alls"; down-weight so specific wins ties.
WEIGHTS = {s: 1.0 for s in SUBS}
WEIGHTS["trauma"] = 0.85          # "fracture"/"dislocation" appear everywhere
WEIGHTS["basic-science"] = 0.9
WEIGHTS["anatomy"] = 1.2          # rare, high-signal phrases -> boost


def build_toc_keywords():
    """Harvest distinctive title words from the textbook TOC per subspecialty."""
    toc = json.load(open("data/textbook_toc.json"))
    stop = set("the of and a an to in for with without on at is are all what which "
               "general approach approaches scenarios principles disease syndrome "
               "fracture fractures injury injuries tumor tumors lesion lesions".split())
    by_sub = {s: Counter() for s in SUBS}
    for e in toc:
        sub = TOC_SUB_MAP.get(e["subspecialty"])
        if sub is None:
            continue
        words = re.findall(r"[a-zA-Z][a-zA-Z\-]{4,}", e["title"].lower())
        for w in words:
            if w not in stop:
                by_sub[sub][w] += 1
    # keep words that are distinctive (appear for only one subspecialty)
    word_owners = {}
    for sub, ctr in by_sub.items():
        for w in ctr:
            word_owners.setdefault(w, set()).add(sub)
    toc_kw = {s: set() for s in SUBS}
    for w, owners in word_owners.items():
        if len(owners) == 1:
            toc_kw[next(iter(owners))].add(w)
    return toc_kw


def score(text, toc_kw):
    text = text.lower()
    scores = {s: 0.0 for s in SUBS}
    for sub, kws in KEYWORDS.items():
        for kw in kws:
            if kw in text:
                scores[sub] += WEIGHTS[sub] * (2 if len(kw) > 8 else 1)
    for sub, kws in toc_kw.items():
        for kw in kws:
            if re.search(r"\b" + re.escape(kw) + r"\b", text):
                scores[sub] += 0.5 * WEIGHTS[sub]
    return scores


TOPIC_HINT_MAP = {
    "peds": "paediatrics", "pediatric": "paediatrics", "trauma": "trauma",
    "sports": "sports", "spine": "spine", "onc": "oncology", "oncology": "oncology",
    "hand": "hand-and-wrist", "wrist": "hand-and-wrist", "shoulder": "shoulder",
    "elbow": "elbow", "foot": "foot-and-ankle", "ankle": "foot-and-ankle",
    "arthroplasty": "arthroplasty", "recon": "arthroplasty", "adult recon": "arthroplasty",
    "basic": "basic-science", "basic science": "basic-science", "anatomy": "anatomy",
}


def classify_record(r, toc_kw):
    # 1. explicit topic hint
    hint = (r.get("topic_hint") or "").strip().lower()
    if hint:
        for k, v in TOPIC_HINT_MAP.items():
            if k in hint:
                return v, 99.0, 99.0
    text = " ".join(filter(None, [r.get("question"), r.get("options"),
                                  r.get("evidence")]))
    scores = score(text, toc_kw)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_sub, top = ranked[0]
    runner = ranked[1][1]
    if top == 0:
        return "unclassified", 0.0, 0.0
    return top_sub, round(top, 2), round(top - runner, 2)


def process(path, toc_kw):
    recs = json.load(open(path))
    for r in recs:
        sub, conf, margin = classify_record(r, toc_kw)
        r["subspecialty"] = sub
        r["subspecialty_confidence"] = conf
        r["subspecialty_margin"] = margin
    json.dump(recs, open(path, "w"), ensure_ascii=False, indent=1)
    return recs


def main():
    toc_kw = build_toc_keywords()
    all_recs = process("data/questions.json", toc_kw)
    process("data/questions_recent.json", toc_kw)

    dist = Counter(r["subspecialty"] for r in all_recs)
    print("Full-set subspecialty distribution:")
    for s, n in dist.most_common():
        print(f"  {s:18s} {n}")

    low = [r for r in all_recs
           if r["subspecialty"] == "unclassified" or r["subspecialty_margin"] < 1.5]
    json.dump(low, open("data/classification_review.json", "w"),
              ensure_ascii=False, indent=1)
    print(f"\nlow-confidence / unclassified rows: {len(low)} "
          f"(-> data/classification_review.json)")


if __name__ == "__main__":
    main()
