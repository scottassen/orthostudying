#!/usr/bin/env python3
"""Extract embedded clinical images from the xlsx and map each to its anchor.

Writes:
  data/images/imageN.<ext>     - the raw image
  data/images/anchors.json     - {image_file: {sheet, cell_row, cell_col}}

The OCR/description sidecars (imageN.txt) are authored separately by reading
each image with the vision-capable Read tool (poppler/tesseract are not
installed in this environment).

Run:  python3 scripts/extract_images.py
"""
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET

XLSX = "2025 National Consensus-3.xlsx"
OUT = "data/images"

NS_XDR = "{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}"
NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_PR = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def sheet_titles(z):
    """Map sheetN.xml -> worksheet title using workbook.xml + rels order."""
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid_to_target = {r.get("Id"): r.get("Target") for r in rels}
    out = {}
    for s in wb.find(f"{ns}sheets"):
        rid = s.get(f"{NS_R}id")
        target = rid_to_target.get(rid, "")
        m = re.search(r"sheet(\d+)\.xml", target)
        if m:
            out[f"sheet{m.group(1)}.xml"] = s.get("name")
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    z = zipfile.ZipFile(XLSX)
    titles = sheet_titles(z)
    anchors = {}

    # 1. Extract raw media.
    media = [n for n in z.namelist() if n.startswith("xl/media/")]
    for m in media:
        data = z.read(m)
        fname = os.path.basename(m)
        with open(os.path.join(OUT, fname), "wb") as f:
            f.write(data)

    # 2. For each worksheet, follow rels -> drawing -> image + anchor cell.
    for sheet_xml, title in titles.items():
        rel_path = f"xl/worksheets/_rels/{sheet_xml}.rels"
        if rel_path not in z.namelist():
            continue
        rels = ET.fromstring(z.read(rel_path))
        draw_targets = [r.get("Target") for r in rels
                        if "drawing" in (r.get("Target") or "")]
        for dt in draw_targets:
            dpath = "xl/" + dt.replace("../", "")
            if dpath not in z.namelist():
                continue
            # drawing rels: embed rId -> media file
            drel_path = os.path.join(os.path.dirname(dpath), "_rels",
                                     os.path.basename(dpath) + ".rels")
            embed_map = {}
            if drel_path in z.namelist():
                drel = ET.fromstring(z.read(drel_path))
                for r in drel:
                    embed_map[r.get("Id")] = os.path.basename(r.get("Target") or "")
            dxml = ET.fromstring(z.read(dpath))
            for anchor in list(dxml):
                frm = anchor.find(f"{NS_XDR}from")
                blip = anchor.find(f".//{NS_A}blip")
                if frm is None or blip is None:
                    continue
                rid = blip.get(f"{NS_R}embed")
                img_file = embed_map.get(rid)
                if not img_file:
                    continue
                row = frm.find(f"{NS_XDR}row")
                colc = frm.find(f"{NS_XDR}col")
                anchors[img_file] = {
                    "sheet": title,
                    "cell_row": (int(row.text) + 1) if row is not None else None,
                    "cell_col": (int(colc.text) + 1) if colc is not None else None,
                }

    with open(os.path.join(OUT, "anchors.json"), "w") as f:
        json.dump(anchors, f, ensure_ascii=False, indent=1)

    print(f"extracted {len(media)} media files")
    print(f"mapped {len(anchors)} anchored images:")
    for img, a in sorted(anchors.items()):
        print(f"  {img}: {a['sheet']} row {a['cell_row']} col {a['cell_col']}")
    unmapped = sorted(set(os.path.basename(m) for m in media) - set(anchors))
    if unmapped:
        print(f"unmapped media (decorative/duplicated): {unmapped}")


if __name__ == "__main__":
    main()
