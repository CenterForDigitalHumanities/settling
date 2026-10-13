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
type_rows = []
type_max = max(type_counts.values()) if type_counts else 1
for t in sorted(type_counts, key=lambda k: (-type_counts[k], k)):
    c = type_counts[t]
    pct = round(c / total_docs * 100)
    type_rows.append(
        f"""<div class="hbar">
          <div class="hbar-label">{esc(t)} <span class="hbar-count">{c} ({pct}%)</span></div>
          <div class="hbar-track"><div class="hbar-fill" style="width:{round(c/type_max*100)}%"></div></div>
        </div>"""
    )

n = max(conf_counts.values()) if conf_counts else 1
conf_rows = []
for label in ("high", "medium", "low"):
    c = conf_counts.get(label, 0)
    conf_rows.append(
        f"""<div class="hbar">
          <div class="hbar-label">{esc(label)} <span class="hbar-count">{c} ({round(c/total_docs*100) if total_docs else 0}%)</span></div>
          <div class="hbar-track"><div class="hbar-fill" style="width:{round(c/n*100)}%"></div></div>
        </div>"""
    )

on = max(order_conf_counts.values()) if order_conf_counts else 1
order_conf_rows = []
for label in ("high", "mixed", "medium"):
    c = order_conf_counts.get(label, 0)
    order_conf_rows.append(
        f"""<div class="hbar">
          <div class="hbar-label">{esc(label)} <span class="hbar-count">{c} ({round(c/total_docs*100) if total_docs else 0}%)</span></div>
          <div class="hbar-track"><div class="hbar-fill" style="width:{round(c/on*100)}%"></div></div>
        </div>"""
    )

name_terms = [
    "Martha", "Hamilton", "Mayer", "Skrzycki", "Walsh", "Mintz", "Mufson",
    "Farhi", "Fromson", "Yang", "Grimaldi", "Bluestein", "Chandler",
    "Chandrasekaran", "Crenshaw", "Knight", "O'Harrow", "Pearlstein",
    "Hilzenrath", "Leibovich", "Ifill", "Graham", "Bradlee", "Harwood",
    "Swoboda", "Behr", "Juan Williams", "Demby", "Wilkinson",
]
mentions = Counter()
for d in docs:
    hay = (d["title"] + " " + d["subject"] + " " + d["notes"]).lower()
    for term in name_terms:
        if term.lower() in hay:
            mentions[term] += 1
top_names = [t for t, c in mentions.most_common(18) if c >= 2]
name_chips = "".join(f'<span class="chip">{esc(t)}</span>' for t in top_names)

year_buckets = Counter()
for d in docs:
    dt = d["date"].lower()
    if dt in ("", "unknown"):
        year_buckets["Unknown"] += 1
        continue
    m = re.search(r"\b(19\d\d|20\d\d)\b", dt)
    if m:
        year_buckets[int(m.group(1))] += 1
    else:
        year_buckets["Undated"] += 1
years_sorted = sorted([y for y in year_buckets if isinstance(y, int)])
year_labels = ", ".join(str(y) for y in years_sorted)


def rot_inline(rot):
    """Inline transform for a rotated thumbnail.

    The element is absolutely centred in its box, so the translate has to
    precede the rotate or the swapped image sits off-centre.
    """
    return f' style="transform: translate(-50%, -50%) rotate({rot}deg)"' if rot else ""


def page_figure(d, p):
    """Thumbnail beside a transcript page, opening the lightbox on that page.

    The reading report is laid out page by page, so the image belongs next to
    the text it came from rather than in a separate strip.
    """
    rot = rotation_for(p["imageFile"])
    rot_cls = " page-fig-rotated" if rot else ""
    return (
        f'<button class="page-fig" data-open-lightbox="{esc(d["docId"])}" '
        f'data-open-page="{p["pageNumber"]}" '
        f'aria-label="View {esc(d["docId"])} page {p["pageNumber"]} of {d["pageCount"]} as an image">'
        f'<img class="page-fig-img{rot_cls}" src="{IMG_BASE}{esc(p["imageFile"])}" '
        f'alt="" loading="lazy"{rot_inline(rot)}></button>'
    )


def doc_card(idx, d):
    strong_pages = sum(1 for p in d["pages"] if p.get("orderBasis") in STRONG_BASES)
    basis_label = d.get("orderBasis", "")
    if d.get("orderConfidence") == "mixed":
        basis_label = "%s (%d of %d pages)" % (basis_label, strong_pages, len(d["pages"]))
    pages_html = []
    for p in d["pages"]:
        transcript = p["transcript"].strip()
        tables = tables_html(transcript)
        # Show only the prose (non-tabular) part as raw text, so the columns
        # aren't duplicated by both the formatted table and the transcript.
        prose = strip_tables(transcript)
        t_html = esc(prose).replace("\n", "<br>")
        prov = []
        if p.get("orderBasis") and p["orderBasis"] != d["orderBasis"]:
            prov.append("<span class='basisdown'>order not asserted here: %s</span>" % esc(p["orderBasis"]))
        if p.get("sourceFilename"):
            prov.append("Ashley's file: <code>%s</code>" % esc(p["sourceFilename"]))
        if p.get("supersedes"):
            prov.append("replaces <code>%s</code>" % esc(p["supersedes"]))
        if p.get("notFiledReason"):
            prov.append("<span class='notfiled'>Not filed by Ashley: %s</span>" % esc(p["notFiledReason"]))
        prov_html = ('<div class="page-prov">%s</div>' % " &middot; ".join(prov)) if prov else ""
        pages_html.append(
            f"""<div class="page">
              <div class="page-head">
                  {page_figure(d, p)}
                  <span class="page-num">p. {esc(p['pageNumber'])}</span>
                <span class="page-kind">{esc(p['pageKind'])}</span>
                <code class="page-file">{esc(p['imageFile'])}</code>
              </div>
              {prov_html}
              {tables}
              <div class="page-transcript">{t_html}</div>
            </div>"""
        )
    return f"""<article class="doc" id="{esc(d['docId'])}">
      <details>
        <summary>
          <div class="doc-head">
            <span class="doc-id">{esc(d['docId'])}<br>{esc(d.get('folder', ''))}</span>
            <div class="doc-title-and-meta">
              <h3>{esc(d['title'])}</h3>
              <div class="doc-meta">
                <span class="badge type">{esc(d['documentType'])}</span>
                <span class="badge order" title="Why these pages are together in this order">{esc(basis_label)}</span>
                <span class="badge orderconf {esc(d.get('orderConfidence', ''))}" title="How firmly the page order is evidenced">{esc(d.get('orderConfidence', ''))} order</span>
                <span class="badge conf {esc(d['confidence'])}" title="How reliably the text could be read">{esc(d['confidence'])} read</span>
                <span class="meta-item">{esc(d['date'])}</span>
                <span class="meta-item">{d['pageCount']} page{'s' if d['pageCount'] != 1 else ''}</span>
              </div>
            </div>
            <button class="view-img-btn" data-open-lightbox="{esc(d['docId'])}" title="View the original images" aria-label="View original images for {esc(d['title'])}">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg> View images
            </button>
          </div>
        </summary>
        <div class="doc-body">
          <p class="doc-subject"><strong>Subject:</strong> {esc(d['subject'])}</p>
          {f'<p class="doc-notes"><strong>Notes:</strong> {esc(d["notes"])}</p>' if d.get('notes') else ''}
          <div class="pages">{''.join(pages_html)}</div>
        </div>
      </details>
    </article>"""


doc_cards = "\n".join(doc_card(i, d) for i, d in enumerate(docs))

report_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <base href="/">
  <script>if (location.protocol === 'file:') {{ var s = location.href.split('/'); s.pop(); s.pop(); document.querySelector('base').href = s.join('/') + '/'; }}</script>
  <title>Martha M. Hamilton Documents — Archive Report</title>
  <meta name="description" content="Organized catalog and transcription of the Martha M. Hamilton document collection">
  <meta name="generated" content="true">
  <meta name="robots" content="noindex, nofollow">
  <link rel="icon" href="favicon.ico" type="image/x-icon">
  <link rel="manifest" href="site.webmanifest">
  <link rel="stylesheet" href="styles.css">
  <link rel="stylesheet" href="review/martha-review.css">
  <script src="assets/js/Components.js" defer></script>
  <script>window.__MARTHA__ = {{ documents: {REGISTRY_JSON} }};</script>
  <script src="review/martha-review.js" defer></script>
  <style>
    .report-hero {{ padding: 48px 0 24px; }}
    .report-stats {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 16px; margin: 24px 0;
    }}
    .stat-card {{ background: var(--paper-soft); border: 1px solid var(--rule); padding: 18px; text-align: center; border-radius: 6px; }}
    .stat-card .num {{ font-family: var(--serif-display); font-size: 2.4rem; color: var(--accent-red); line-height: 1; }}
    .stat-card .lbl {{ font-family: var(--sans); font-size: .82rem; text-transform: uppercase; letter-spacing: .05em; color: var(--ink-muted); margin-top: 6px; }}
    .report-section {{ margin: 40px 0; }}
    .report-section > h2 {{ font-family: var(--serif-display); font-size: 1.9rem; color: var(--ink); border-bottom: 1px solid var(--rule-strong); padding-bottom: 10px; margin-bottom: 18px; }}
    .hbar {{ margin: 10px 0; }}
    .hbar-label {{ font-family: var(--sans); font-size: .9rem; color: var(--ink-soft); display: flex; justify-content: space-between; margin-bottom: 4px; }}
    .hbar-count {{ color: var(--ink-muted); font-size: .8rem; }}
    .hbar-track {{ background: var(--rule); height: 12px; border-radius: 6px; overflow: hidden; }}
    .hbar-fill {{ background: var(--accent-red); height: 100%; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }}
    .chip {{ font-family: var(--sans); font-size: .85rem; background: var(--paper-soft); border: 1px solid var(--rule); padding: 4px 10px; border-radius: 999px; color: var(--ink-soft); }}
    .doc {{ border: 1px solid var(--rule); background: var(--paper-soft); border-radius: 6px; margin-bottom: 12px; overflow: hidden; }}
    .doc details > summary {{ display:flex; align-items:center; justify-content:space-between; gap:14px; cursor:pointer; list-style:none; padding: 14px 18px; }}
    .doc details > summary::-webkit-details-marker {{ display: none; }}
    .doc details > summary > .doc-head {{ flex:1; }}
    .doc details > summary::before {{ content: "\\25B8 "; color: var(--accent-red); }}
    .doc details[open] > summary::before {{ content: "\\25BE "; }}
    .doc-head {{ display: flex; gap: 14px; align-items: flex-start; }}
    .doc-id {{ font-family: var(--sans); font-size: .8rem; color: var(--accent-red-dark); font-weight: 600; padding-top: 3px; white-space: nowrap; }}
    .doc-title-and-meta {{ flex: 1; min-width: 0; }}
    .doc-title-and-meta h3 {{ font-family: var(--serif-body); font-size: 1.12rem; color: var(--ink); margin: 0 0 6px; }}
    .view-img-btn {{
      flex-shrink: 0;
      align-self: flex-start;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-family: var(--sans);
      font-size: .78rem;
      font-weight: 600;
      padding: 5px 10px;
      border-radius: 5px;
      border: 1px solid var(--rule-strong);
      background: var(--surface);
      color: var(--ink-soft);
      cursor: pointer;
      white-space: nowrap;
      transition: border-color .15s, color .15s, background .15s;
    }}
    .view-img-btn:hover {{ border-color: var(--accent-red); color: var(--accent-red-dark); }}
    .doc-meta {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-family: var(--sans); }}
    .badge {{ font-size: .72rem; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: .03em; }}
    .badge.type {{ background: var(--accent-red); color: #fff; }}
    .badge.order {{ background: var(--paper); color: var(--ink-muted); border: 1px solid var(--rule-strong); text-transform: none; letter-spacing: 0; font-style: italic; }}
    .badge.conf.high {{ background: #e4efe0; color: #3a5a36; }}
    .badge.conf.medium {{ background: #f4ead0; color: #7a5c1e; }}
    .badge.conf.low {{ background: #f3e0dd; color: #8a2a26; }}
    .badge.orderconf.high {{ background: #e0eaf3; color: #2c4d6e; }}
    .badge.orderconf.mixed {{ background: #e9e3f2; color: #55406e; }}
    .badge.orderconf.medium {{ background: #eceff1; color: #55606a; }}
    .meta-item {{ color: var(--ink-muted); font-size: .85rem; }}
    .doc-body {{ padding: 0 18px 18px; border-top: 1px solid var(--rule); }}
    .doc-subject, .doc-notes {{ margin: 14px 0; font-size: .95rem; }}
    .pages {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; margin-top: 14px; }}
    .page {{ background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 14px; }}
    .page-head {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; font-family: var(--sans); }}
    .page-num {{ font-weight: 600; color: var(--accent-red-dark); }}
    .page-kind {{ font-size: .72rem; text-transform: uppercase; color: var(--ink-muted); background: var(--paper); border: 1px solid var(--rule); padding: 1px 6px; border-radius: 4px; }}
    .page-file {{ font-size: .7rem; color: var(--ink-muted); word-break: break-all; }}
    .page-fig {{ position: relative; flex: 0 0 auto; width: 46px; height: 61px; padding: 0; border: 1px solid var(--rule-strong); border-radius: 4px; background: var(--paper); cursor: pointer; overflow: hidden; align-self: flex-start; }}
    .page-fig img {{ display: block; width: 100%; height: 100%; object-fit: cover; }}
    .page-fig img.page-fig-rotated {{ position: absolute; left: 50%; top: 50%; width: 61px; height: 46px; object-fit: contain; }}
    .page-fig:hover, .page-fig:focus-visible {{ border-color: var(--accent-rose); }}
    .page-prov {{ font-family: var(--sans); font-size: .74rem; color: var(--ink-muted); margin: -4px 0 10px; }}
    .page-prov code {{ font-size: .72rem; }}
    .page-prov .notfiled {{ color: #8a2a26; }}
.page-prov .basisdown {{ color: #55406e; font-style: italic; }}
    .page-transcript {{ font-family: var(--serif-body); font-size: .9rem; color: var(--ink-soft); white-space: normal; line-height: 1.55; margin-top: 10px; }}
    .page-transcript:empty::before {{ content: "[no text transcribed]"; color: var(--ink-muted); font-style: italic; }}
    .note-block {{ background: var(--paper-soft); border-left: 4px solid var(--accent-rose); padding: 16px 20px; font-size: .95rem; }}
    .legend p {{ margin: 8px 0; font-size: .92rem; }}
    code {{ font-family: 'SFMono-Regular', Consolas, monospace; font-size: .82em; background: var(--paper); padding: 1px 4px; border-radius: 3px; }}
  </style>
</head>
<body>
  <settling-release-banner></settling-release-banner>
  <settling-nav></settling-nav>

  <header class="report-hero">
    <div class="container">
      <h1>Martha M. Hamilton Documents</h1>
      <p class="subtitle">Archive report and transcription catalog — {esc(source_name)}</p>
      <p class="legend"><a href="review/martha-audit.html">Open the thumbnail audit page →</a></p>
    </div>
  </header>

  <main class="container">
    <section class="report-section">
      <div class="report-stats">
        <div class="stat-card"><div class="num">{total_docs}</div><div class="lbl">Documents</div></div>
        <div class="stat-card"><div class="num">{total_pages}</div><div class="lbl">Photos / Pages</div></div>
        <div class="stat-card"><div class="num">{order_conf_counts.get('high', 0)}</div><div class="lbl">Order fully evidenced</div></div>
        <div class="stat-card"><div class="num">{page_basis_counts.get('not-asserted', 0)}</div><div class="lbl">Pages ordered by us</div></div>
        <div class="stat-card"><div class="num">{kind_counts.get('table-photo', 0)}</div><div class="lbl">Blank separators</div></div>
        <div class="stat-card"><div class="num">{type_counts.get('arbitration-exhibit',0)}</div><div class="lbl">Arbitration exhibits</div></div>
      </div>
    </section>

    <section class="report-section note-block">
      <h2>How to read this report</h2>
      <p>The catalog follows the order Ashley Hamilton gave these documents. Each numbered folder in
        <em>{esc(source_name)}</em> is catalogued as one <em>document</em>, and the image files inside it are that
        document's pages, in sequence. Folders appear in numeric order; pages Ashley left loose in the folder root are
        grouped as <strong>Unfiled</strong>, and the handful of scanned pages that do not appear in her ordered set are
        grouped as <strong>Not filed</strong>, each with its reason recorded. Both groups come last.</p>
      <p>Each document carries an <em>order basis</em> saying how much the page sequence can be trusted:
        {basis_summary}. Only <code>explicit</code> and <code>internal-pagination</code> mean the order is written on the
        pages themselves; <code>not-asserted</code> means the grouping is Ashley's but the sequence within it is ours.
        The basis is recorded <strong>per page</strong>, because a folder is often only partly evidenced: where a page's
        basis is weaker than its document's label, the page says so in its own provenance line. A document rated
        <strong>mixed order</strong> has some firmly evidenced pages and some that are not &mdash; check the pages before
        trusting the sequence.</p>
      <p>The transcriptions themselves were produced by reading each photograph with human-style
        visual inspection — no OCR software was used. Where the images are separated by blank or damaged "table surface"
        photos, those separators are preserved in place as <code>table-photo</code> pages.</p>
      <p>Separately from the order, every document carries a <em>reading</em> confidence rating
        (<strong>high</strong> / <strong>medium</strong> / <strong>low</strong>) describing how reliably its text could be
        transcribed; a multi-page document is rated by its least legible page.
        Passages that could not be read are marked <code>[illegible]</code> rather than guessed, because accuracy matters
        more than completeness for archival material. Text that is rotated sideways is noted in the transcript.</p>
      <p>Where pages contain columnar data — salary tables, newsroom headcounts, pay gaps — the values are
        rendered as <strong>tables</strong> to preserve the rows and figures. Click <strong>“View images”</strong>
        on any document to see the original scans, and expand a document to read its full transcription.</p>
    </section>

    <section class="report-section">
      <h2>Contents by type</h2>
      {''.join(type_rows)}
    </section>

    <section class="report-section">
      <h2>Order confidence</h2>
      <p class="legend">How firmly each document's page sequence is evidenced by Ashley's filenames or the documents' own
        pagination. <strong>mixed</strong> means part of the folder is evidenced and part is our arrangement.</p>
      {''.join(order_conf_rows)}
    </section>

    <section class="report-section">
      <h2>Reading confidence</h2>
      <p class="legend">How reliably each document's text could be transcribed from the scans, rated by its least legible page.</p>
      {''.join(conf_rows)}
    </section>

    <section class="report-section">
      <h2>Key figures referenced</h2>
      <p class="legend">People named repeatedly across the collection, based on titles, subjects and notes.
        This is a convenience index for navigation, not an exhaustive list.</p>
      <div class="chips">{name_chips}</div>
    </section>

    <section class="report-section">
      <h2>Date coverage</h2>
      <p>Known years appearing across the collection: <strong>{esc(year_labels)}</strong>.</p>
    </section>

    <section class="report-section">
      <h2>Document catalog</h2>
      <p class="legend">Click any document to expand its full transcription. Files are named by the source image filenames.</p>
      {doc_cards}
    </section>
  </main>

  <settling-footer></settling-footer>
</body>
</html>"""

with open(REPORT_OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(report_content)

print(f"Wrote {REPORT_OUT}")
print(f"Docs: {total_docs}, Pages: {total_pages}")

# ---------------- Audit page (thumbnails) ----------------
def first_page_image(d):
    for p in d["pages"]:
        if p["pageKind"] == "content" or p["pageKind"] == "cover":
            return p["imageFile"]
    return d["pages"][0]["imageFile"] if d["pages"] else ""


def doc_summary(d):
    """Short summary from subject, fall back to notes/title."""
    s = (d.get("subject") or "").strip()
    if len(s) > 240:
        s = s[:240].rstrip() + "…"
    return s or d.get("notes", "")


def doc_quote(d):
    """Representative quote from the first readable page."""
    for p in d["pages"]:
        q = representative_quote(p["transcript"])
        if q:
            return q
    return ""


def page_strip(d):
    """Per-page thumbnails so every page of a folder-document stays reachable.

    The card's hero image is one page; this strip is the rest of the evidence.
    Each thumb opens the lightbox directly on its own page.
    """
    if len(d["pages"]) < 2:
        return ""
    cells = []
    for p in d["pages"]:
        rot = rotation_for(p["imageFile"])
        rot_cls = " page-thumb-rotated" if rot else ""
        kind = p["pageKind"] if p.get("pageKind") in ("content", "cover") else "secondary"
        cells.append(
            f'<button class="page-thumb {kind}" data-open-lightbox="{esc(d["docId"])}" '
            f'data-open-page="{p["pageNumber"]}" '
            f'aria-label="Open {esc(d["docId"])} page {p["pageNumber"]} of {d["pageCount"]} ({esc(p.get("pageKind", ""))})">'
            f'<span class="page-thumb-box">'
            f'<img class="page-thumb-img{rot_cls}" src="{IMG_BASE}{esc(p["imageFile"])}" '
            f'alt="" loading="lazy"{rot_inline(rot)}></span>'
            f'<span class="page-thumb-n">{p["pageNumber"]}</span></button>'
        )
    return (
        f'<div class="page-strip" role="group" aria-label="Pages of {esc(d["title"])}">'
        f'<span class="page-strip-label">{d["pageCount"]} pages</span>'
        f'<div class="page-strip-scroll">{"".join(cells)}</div></div>'
    )


audit_cards = []
for d in docs:
    img = first_page_image(d)
    img_rot = rotation_for(d["pages"][0]["imageFile"]) if d["pages"] else 0
    rot_cls = " martha-thumb-rotated" if img_rot else ""
    # The shared class swaps the 3:4 bounding box; the angle itself varies per scan.
    rot_style = f' style="transform: rotate({img_rot}deg)"' if img_rot else ""
    thumb = (
        f'<img class="martha-thumb{rot_cls}"{rot_style} src="{IMG_BASE}{esc(img)}" alt="Preview of {esc(d["title"])}" loading="lazy" '
        f'onerror="this.outerHTML=`<div class=&quot;martha-thumb-fallback&quot;>No preview</div>`">'
        if img
        else '<div class="martha-thumb-fallback">No image</div>'
    )
    quote = doc_quote(d)
    quote_html = f'<blockquote class="martha-quote">“{esc(quote)}”</blockquote>' if quote else ""
    summary = doc_summary(d)
    audit_cards.append(f"""<article class="martha-card" id="{esc(d['docId'])}">
      <button class="martha-preview-btn" data-open-lightbox="{esc(d['docId'])}" aria-label="View {esc(d['title'])} full pages">
        {thumb}
        <span class="martha-card-body">
          <span class="martha-card-title">{esc(d['title'])}</span>
          <span class="martha-card-summary">{esc(summary)}</span>
          {quote_html}
          <span class="martha-card-meta">
            <span class="badge type">{esc(d['documentType'])}</span>
            <span class="badge order">{esc(d.get('folder', ''))}</span>
            <span class="badge orderconf {esc(d.get('orderConfidence', ''))}" title="How firmly the page order is evidenced">{esc(d.get('orderConfidence', ''))} order</span>
            <span class="badge conf {esc(d['confidence'])}" title="How reliably the text could be read">{esc(d['confidence'])} read</span>
            <span class="meta-item">{d['pageCount']} pg</span>
          </span>
        </span>
      </button>
      {page_strip(d)}
      <button class="otr-btn" data-mark-otr="{esc(d['docId'])}">Off the record</button>
    </article>""")

audit_cards_html = "\n".join(audit_cards)

audit_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <base href="/">
  <script>if (location.protocol === 'file:') {{ var s = location.href.split('/'); s.pop(); s.pop(); document.querySelector('base').href = s.join('/') + '/'; }}</script>
  <title>Martha M. Hamilton Documents — Audit</title>
  <meta name="description" content="Thumbnail audit of the Martha M. Hamilton document collection for review">
  <meta name="generated" content="true">
  <meta name="robots" content="noindex, nofollow">
  <link rel="icon" href="favicon.ico" type="image/x-icon">
  <link rel="manifest" href="site.webmanifest">
  <link rel="stylesheet" href="styles.css">
  <link rel="stylesheet" href="review/martha-review.css">
  <script src="assets/js/Components.js" defer></script>
  <script>window.__MARTHA__ = {{ documents: {REGISTRY_JSON} }};</script>
  <script src="review/martha-review.js" defer></script>
  <style>
    .audit-hero {{ padding: 40px 0 12px; }}
    .audit-toolbar {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin: 18px 0 26px; }}
    .audit-filter {{ font-family: var(--sans); font-size: .85rem; padding: 7px 12px; border: 1px solid var(--rule-strong); border-radius: 5px; background: var(--surface); color: var(--ink-soft); }}
    .audit-count {{ font-family: var(--sans); font-size: .85rem; color: var(--ink-muted); }}
    .martha-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 18px; }}
    .martha-card {{ position: relative; border: 1px solid var(--rule); border-radius: 8px; background: var(--paper-soft); overflow: hidden; display: flex; flex-direction: column; }}
    .martha-card .martha-preview-btn {{ flex: 1; display: flex; flex-direction: column; }}
    .martha-card-body {{ display: flex; flex-direction: column; gap: 8px; padding: 14px; }}
    .martha-card-title {{ font-family: var(--serif-body); font-weight: 600; font-size: .98rem; color: var(--ink); line-height: 1.35; }}
    .martha-card-summary {{ font-family: var(--sans); font-size: .82rem; color: var(--ink-soft); line-height: 1.5; }}
    .martha-quote {{ font-size: .85rem; font-style: italic; color: var(--ink-muted); border-left: 3px solid var(--accent-rose); padding-left: 10px; margin: 0 0 4px; line-height: 1.5; }}
    .martha-card-meta {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; font-family: var(--sans); margin-top: 4px; }}
    .martha-card .otr-btn {{ position: absolute; top: 10px; right: 10px; z-index: 2; background: rgba(255,255,255,.92); }}
    .page-strip {{ display: flex; align-items: center; gap: 9px; padding: 2px 14px 13px; }}
    .page-strip-label {{ font-family: var(--sans); font-size: .68rem; letter-spacing: .05em; text-transform: uppercase; color: var(--ink-muted); white-space: nowrap; }}
    .page-strip-scroll {{ display: flex; gap: 5px; overflow-x: auto; padding: 1px; scrollbar-width: thin; }}
    .page-strip-scroll[data-more="1"] {{ -webkit-mask-image: linear-gradient(to right, #000 calc(100% - 22px), transparent); mask-image: linear-gradient(to right, #000 calc(100% - 22px), transparent); }}
    .page-thumb {{ flex: 0 0 auto; width: 32px; padding: 0; border: 1px solid var(--rule-strong); border-radius: 4px; background: var(--paper); cursor: pointer; overflow: hidden; }}
    .page-thumb-box {{ display: block; position: relative; width: 100%; height: 43px; overflow: hidden; }}
    .page-thumb img {{ display: block; width: 100%; height: 100%; object-fit: cover; }}
    .page-thumb img.page-thumb-rotated {{ position: absolute; left: 50%; top: 50%; width: 43px; height: 32px; object-fit: contain; }}
    .page-thumb-n {{ display: block; font-family: var(--sans); font-size: .6rem; line-height: 1.5; color: var(--ink-soft); border-top: 1px solid var(--rule); }}
    .page-thumb.secondary img {{ filter: grayscale(1) contrast(.9); opacity: .62; }}
    .page-thumb:hover, .page-thumb:focus-visible {{ border-color: var(--accent-rose); }}
    .page-thumb:hover .page-thumb-n, .page-thumb:focus-visible .page-thumb-n {{ color: var(--ink); }}
    .martha-card.is-redacted .page-strip {{ display: none; }}
    .martha-card.is-redacted .martha-preview-btn {{ opacity: .55; }}
    .martha-card.is-redacted:after {{ content: "OFF THE RECORD"; position: absolute; top: 10px; left: 10px; background: var(--accent-red); color: #fff; font-family: var(--sans); font-size: .68rem; letter-spacing: .05em; padding: 3px 8px; border-radius: 4px; z-index: 2; }}
    .martha-empty {{ font-family: var(--sans); color: var(--ink-muted); padding: 40px 0; text-align: center; }}
    a.back-link {{ font-family: var(--sans); font-size: .9rem; }}
  </style>
</head>
<body>
  <settling-release-banner></settling-release-banner>
  <settling-nav></settling-nav>

  <header class="audit-hero">
    <div class="container">
      <h1>Martha M. Hamilton Documents</h1>
      <p class="subtitle">Thumbnail audit — {total_docs} documents · {total_pages} pages</p>
      <p class="legend"><a class="back-link" href="review/martha.html">Open the full report →</a></p>
    </div>
  </header>

  <main class="container">
    <div class="audit-toolbar">
      <input class="audit-filter" id="audit-filter" type="search" placeholder="Filter by title, subject, type…" aria-label="Filter documents">
      <span class="audit-count" id="audit-count">{total_docs} shown</span>
    </div>

    <div class="martha-grid" id="martha-grid">
      {audit_cards_html}
    </div>
  </main>

  <settling-footer></settling-footer>

  <script>
    (function () {{
      const grid = document.getElementById('martha-grid')
      const filter = document.getElementById('audit-filter')
      const countEl = document.getElementById('audit-count')
      const cards = Array.from(grid.querySelectorAll('.martha-card'))
      filter.addEventListener('input', () => {{
        const q = filter.value.trim().toLowerCase()
        let shown = 0
        cards.forEach((c) => {{
          const hay = c.textContent.toLowerCase()
          const match = !q || hay.includes(q)
          c.style.display = match ? '' : 'none'
          if (match) shown++
        }})
        countEl.textContent = shown + ' shown'
      }})
      // Keep card redacted state in sync
      document.addEventListener('martha:redacted-changed', () => {{
        cards.forEach((c) => c.classList.toggle('is-redacted', window.__MARTHA_OTR__ && window.__MARTHA_OTR__[c.id]))
      }})
      // Fade a page strip only while more thumbs remain off to the right.
      const strips = Array.from(grid.querySelectorAll('.page-strip-scroll'))
      const syncStrip = (el) => {{
        const more = el.scrollLeft + el.clientWidth < el.scrollWidth - 2
        el.dataset.more = more ? '1' : ''
      }}
      strips.forEach((el) => {{
        syncStrip(el)
        el.addEventListener('scroll', () => syncStrip(el), {{ passive: true }})
      }})
      window.addEventListener('resize', () => strips.forEach(syncStrip))
      filter.addEventListener('input', () => requestAnimationFrame(() => strips.forEach(syncStrip)))
    }})()
  </script>
</body>
</html>"""

with open(AUDIT_OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(audit_content)

print(f"Wrote {AUDIT_OUT}")
print(f"Audit cards: {len(audit_cards)}")
