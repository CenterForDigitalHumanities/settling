# -*- coding: utf-8 -*-
"""One-shot migration that produced the folder-organised master-data.json.

This is provenance, not a maintenance tool. It reads the PRE-reorganisation
master-data.json (GUID-ordered, 148 documents) and rewrites it as 29
folder-documents, so running it against the already-migrated file fails.
To replay it, restore the original first:

    git show <commit-before-reorg>:review/martha/master-data.json > master-data.json
    python build_master.py --source=<Ashley's ordered folder> [--write]

Dry-run by default; --write copies images into ./images and rewrites
master-data.json, leaving the previous version at master-data.json.bak.

The curated decisions live in order_table.py (page order within each folder)
and titles.py (titles, dates, not-filed reasons). verify.py checks the result
and is safe to re-run.
"""
import hashlib
import json
import os
import re
import shutil
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import order_table as ot
import titles as tt

MAR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(MAR))
IMGDIR = os.path.join(MAR, "images")
MASTER = os.path.join(MAR, "master-data.json")
GUID = re.compile(r"^([0-9A-Fa-f]{8})")

WRITE = "--write" in sys.argv
_src = [a for a in sys.argv if a.startswith("--source=")]
if not _src:
    sys.exit("pass --source=<path to Ashley's ordered folders> "
             "(e.g. --source=\"U:\\Downloads\\Martha M. Hamilton Documents (ordered)\")")
ASHLEY = _src[0][len("--source="):]


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


payload = json.load(open(MASTER, encoding="utf-8"))
if "reorganized" in payload:
    sys.exit("master-data.json is already folder-organised; this migration expects "
             "the pre-reorganisation file. Restore it from git before replaying.")
pages = {}          # prefix -> dict(page, doc)
by_md5 = {}         # repo image md5 -> prefix
for d in payload["documents"]:
    for p in d["pages"]:
        pre = p["imageFile"][:8].upper()
        pages[pre] = {"page": p, "doc": d}
        by_md5[md5(os.path.join(IMGDIR, p["imageFile"]))] = pre

# ---- walk Ashley's ordered folders -------------------------------------
ashley_files = []   # (folder, filename, path)
for root, dirnames, filenames in os.walk(ASHLEY):
    dirnames[:] = [x for x in dirnames if x != "__MACOSX"]
    rel = os.path.relpath(root, ASHLEY)
    folder = "Unfiled (loose in folder root)" if rel == "." else rel.split(os.sep)[0]
    for fn in filenames:
        if fn.startswith("._") or fn == ".DS_Store":
            continue
        if not fn.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        ashley_files.append((folder, fn, os.path.join(root, fn)))

resolve = {}        # prefix -> (ashley_folder, ashley_filename, ashley_path, class)
newscans = {}       # "NEW:pgN" -> (ashley_filename, ashley_path)
for folder, fn, path in ashley_files:
    h = md5(path)
    stem = GUID.match(os.path.splitext(fn)[0])
    if h in by_md5:
        pre = by_md5[h]
        resolve[pre] = (folder, fn, path, "A" if (stem and stem.group(1).upper() == pre) else "B")
    elif stem and stem.group(1).upper() in pages:
        resolve[stem.group(1).upper()] = (folder, fn, path, "C")
    else:
        newscans[fn] = (folder, path)

print("ashley files:", len(ashley_files), "| resolved:", len(resolve), "| new:", len(newscans))
print("classes:", Counter(v[3] for v in resolve.values()))

# map the 4 brand-new arbitration scans onto their slot keys
SLOT = {"NEW:pg1": "Arbitation Procedures pg 1.jpeg", "NEW:pg3": "Arbitation Procedures pg 3.jpeg",
        "NEW:pg4": "Arbitation Procedures pg 4.jpeg", "NEW:pg6": "Arbitation Procedures pg 6.jpeg"}
NEWNAME = {"NEW:pg1": "martha11-pg1.jpeg", "NEW:pg3": "martha11-pg3.jpeg",
           "NEW:pg4": "martha11-pg4.jpeg", "NEW:pg6": "martha11-pg6.jpeg"}
for slot, fn in SLOT.items():
    assert fn in newscans, (slot, fn, sorted(newscans))

# ---- copy images --------------------------------------------------------
copies = []
for slot, fn in SLOT.items():
    copies.append((newscans[fn][1], os.path.join(IMGDIR, NEWNAME[slot]), "new arbitration re-scan"))
for pre, (folder, fn, path, cls) in resolve.items():
    if cls == "C":
        copies.append((path, os.path.join(IMGDIR, pages[pre]["page"]["imageFile"]), "higher-res re-scan"))
for src, dst, why in copies:
    same = md5(src) == md5(dst) if os.path.exists(dst) else False
    print(("  COPY" if not same else "  ok  "), why, "->", os.path.basename(dst))
    if WRITE and not same:
        shutil.copy2(src, dst)

# ---- assemble documents -------------------------------------------------
def num(name):
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else 999


folders = sorted(ot.FOLDERS, key=lambda x: (
    0 if x[0].startswith("Martha") else 1 if x[0].startswith("Unfiled") else 2,
    num(x[0])))

docs, prev_map = [], {}
for i, (folder, spec) in enumerate(folders, 1):
    meta = tt.META[folder]
    doc_id = "DOC-%03d" % i
    out_pages, prevs = [], set()
    for n, slot in enumerate(spec["pages"], 1):
        if slot.startswith("NEW:"):
            sup = tt.SUPERSEDES[slot]
            src = pages[sup]
            out_pages.append({
                "imageFile": NEWNAME[slot],
                "pageNumber": n,
                "pageKind": src["page"]["pageKind"],
                "transcript": src["page"]["transcript"],
                "sourceFilename": SLOT[slot],
                "orderBasis": spec["basis"],
                "previousDocId": src["doc"]["docId"],
                "supersedes": src["page"]["imageFile"],
                "provenance": "Ashley's re-scan of the page previously catalogued as %s; content verified identical by image correlation." % src["doc"]["docId"],
            })
            prevs.add(src["doc"]["docId"])
            continue
        pre = slot
        src = pages[pre]
        _, ashley_fn, _, cls = resolve.get(pre, (None, None, None, "absent"))
        page = dict(src["page"])
        page["pageNumber"] = n
        page["orderBasis"] = spec["basis"]
        page["previousDocId"] = src["doc"]["docId"]
        if cls in ("B", "C"):
            page["sourceFilename"] = ashley_fn
        if folder.startswith("Not filed"):
            page["notFiledReason"] = tt.NOT_FILED_REASONS[pre]
        prevs.add(src["doc"]["docId"])
        out_pages.append(page)
    docs.append({
        "docId": doc_id,
        "folder": folder,
        "order": i,
        "title": meta["title"],
        "documentType": meta["documentType"],
        "subject": meta["subject"],
        "date": meta["date"],
        "pageCount": len(out_pages),
        "confidence": "high" if spec["basis"] in ("explicit", "internal-pagination") else "medium",
        "notes": meta["notes"],
        "orderBasis": spec["basis"],
        "previousDocIds": sorted(prevs),
        "pages": out_pages,
    })

superseded = [{
    "imageFile": pages[p]["page"]["imageFile"],
    "previousDocId": pages[p]["doc"]["docId"],
    "replacedBy": NEWNAME[s],
    "reason": "Superseded by Ashley's higher-resolution re-scan; retained on disk, not shown in the catalog.",
} for s, p in tt.SUPERSEDES.items()]

out = {
    "generated": payload["generated"],
    "reorganized": "2026-09-28",
    "sourceFolder": ASHLEY,
    "imageArchive": "review/martha/images/",
    "totalDocuments": len(docs),
    "totalPages": sum(len(d["pages"]) for d in docs),
    "ordering": {
        "principle": "One document per folder in Ashley Hamilton's ordered collection; folder number sets catalog order; files inside a folder are its pages.",
        "unfiled": "Pages Ashley left loose in the folder root are grouped as Unfiled; pages with no counterpart in her set are grouped as Not filed. Both groups sit at the end.",
        "basisVocabulary": {
            "explicit": "Ashley's own filename states the page number.",
            "internal-pagination": "The document's own printed page numbers or paragraph numbering fix the sequence.",
            "content-sequence": "Pages of one physical document split across folders, rejoined by continuity of text.",
            "editorial-alphabetical": "Editorial arrangement by comparator surname.",
            "editorial-chronological": "Editorial arrangement by dates written on the pages.",
            "not-asserted": "Grouping only; the sequence is editorial and makes no claim about Ashley's intent.",
        },
    },
    "documents": docs,
    "supersededPages": superseded,
}

print("docs:", out["totalDocuments"], "pages:", out["totalPages"])
assert out["totalPages"] == 167, out["totalPages"]
assert len(docs) == 29
imgs = [p["imageFile"] for d in docs for p in d["pages"]]
assert len(imgs) == len(set(imgs)) == 167, (len(imgs), len(set(imgs)))
print("unique imageFiles:", len(set(imgs)))
if WRITE:
    shutil.copyfile(MASTER, MASTER + ".bak")
    with open(MASTER, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print("wrote master-data.json (previous copy at master-data.json.bak)")
else:
    print("(dry run; pass --write)")
