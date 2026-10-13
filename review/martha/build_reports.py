#!/usr/bin/env python3
"""Generate review/martha.html and review/martha-audit.html from master data."""
import json
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.dirname(os.path.dirname(HERE))

sys.path.insert(0, HERE)
from transcript_utils import extract_tables, tables_to_html, representative_quote, strip_tables
from rotations import ROTATIONS

MASTER = os.path.join(HERE, "master-data.json")
# Bases that assert a sequence the material itself evidences; see martha-schema.md.
STRONG_BASES = ("explicit", "internal-pagination")
REPORT_OUT = os.path.join(SITE_ROOT, "review", "martha.html")
AUDIT_OUT = os.path.join(SITE_ROOT, "review", "martha-audit.html")
# Image paths are relative to the site's <base href="/">. In the served
# repo the scans live at review/martha/images/<file>, so from the base that is
# "review/martha/images/". The inline base-rewrite on file:// keeps this correct
# for local preview too.
IMG_BASE = "review/martha/images/"


def rotation_for(image_file):
    """CSS degrees for a scan; unknown or blank entries read as upright."""
    return ROTATIONS.get(image_file[:8], 0) or 0


with open(MASTER, encoding="utf-8") as fh:
    data = json.load(fh)
# Catalog order is the order of the list: one document per folder in Ashley
# Hamilton's ordered collection, numbered by folder. Do not re-sort.
docs = data["documents"]
total_docs = len(docs)
total_pages = sum(len(d["pages"]) for d in docs)
source_name = data["sourceFolder"].replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]

from collections import Counter
type_counts = Counter(d["documentType"] for d in docs)
conf_counts = Counter(d["confidence"] for d in docs)
order_conf_counts = Counter(d.get("orderConfidence", "") for d in docs)
page_basis_counts = Counter(p.get("orderBasis", "") for d in docs for p in d["pages"])
kind_counts = Counter()
for d in docs:
    for p in d["pages"]:
        kind_counts[p["pageKind"]] += 1


basis_counts = Counter(d.get("orderBasis", "") for d in docs)
basis_summary = " · ".join(
    "<code>%s</code> (%d)" % (b, c) for b, c in sorted(basis_counts.items(), key=lambda kv: -kv[1])
)


def esc(t):
    if t is None:
        return ""
    if not isinstance(t, str):
        t = str(t)
    return html.escape(t)


def tables_html(transcript):
    """Render all detected table blocks in a transcript."""
    blocks = extract_tables(transcript)
    if not blocks:
        return ""
    return "".join(tables_to_html(b) for b in blocks)


# Embedded document registry for the page's JS (filenames per doc).
registry = [
    {
        "docId": d["docId"],
        "title": d["title"],
        "folder": d.get("folder", ""),
        "documentType": d["documentType"],
        "confidence": d["confidence"],
        "pages": [
            {
                "imageFile": p["imageFile"],
                "pageNumber": p["pageNumber"],
                "rotation": rotation_for(p["imageFile"]),
            }
            for p in d["pages"]
        ],
    }
    for d in docs
]

REGISTRY_JSON = json.dumps(registry, ensure_ascii=False)

# ---------------- Full report page ----------------
... (rest of file unchanged)