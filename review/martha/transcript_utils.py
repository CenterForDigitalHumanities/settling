#!/usr/bin/env python3
"""Shared helpers for extracting tabular runs and representative quotes from transcripts."""
import re

# Lines/patterns that indicate a transcript page began as a partially-visible scan
SCAN_MARKERS = (
    "CONFIDENTIAL INFORMATION UNDER",
    "PREPARED FOR SETTLEMENT PURPOSES",
    "[rotated",
    "[illegible]",
    "[...",
    "ACTIVITY FROM",
    "INCLUDES",
    "EXCLUDES",
)


def split_cells(line):
    """Split a transcript line into logical cells by 2+ spaces or a vertical bar."""
    cells = re.split(r"\s{2,}|\s*\|\s*", line.strip())
    return [c for c in cells if c]


def extract_tables(transcript):
    """Return a list of table runs (each a list of lines) detected in a transcript."""
    lines = transcript.split("\n")
    blocks = []
    cur = []
    for ln in lines:
        if not ln.strip():
            if cur:
                blocks.append(cur)
                cur = []
            continue
        cur.append(ln)
    if cur:
        blocks.append(cur)

    tables = []
    for block in blocks:
        cell_counts = [len(split_cells(ln)) for ln in block]
        multi = sum(1 for c in cell_counts if c >= 2)
        if len(block) >= 3 and multi >= 2 and multi >= len(block) * 0.5:
            tables.append(block)
    return tables


def strip_tables(transcript):
    """Return the transcript with tabular blocks removed, so the columns aren't
    shown twice (once as a formatted table, once inside the raw text)."""
    lines = transcript.split("\n")
    blocks = []
    cur = []
    for ln in lines:
        if not ln.strip():
            if cur:
                blocks.append(cur)
                cur = []
            continue
        cur.append(ln)
    if cur:
        blocks.append(cur)

    kept = []
    for block in blocks:
        cell_counts = [len(split_cells(ln)) for ln in block]
        multi = sum(1 for c in cell_counts if c >= 2)
        is_table = len(block) >= 3 and multi >= 2 and multi >= len(block) * 0.5
        if is_table:
            # Keep the block's surrounding blank-line separation only if it reads
            # as a section heading; otherwise drop the whole block.
            first = block[0].strip()
            # A single short label line (e.g. a section title) may precede a table;
            # drop it too, since it's usually the table's caption.
            if len(split_cells(first)) == 1 and len(block) > 1:
                continue
            continue
        kept.extend(block)

    return "\n".join(kept)


# Patterns that mark a row as a total / average summary row (not an item row)
_TOTAL_RE = re.compile(r"^\s*(total|all|avg\.?|average)\b", re.I)


def _modal_width(rows):
    """Most common row width across the block (ties broken toward the larger width)."""
    from collections import Counter
    counts = Counter(len(r) for r in rows)
    if not counts:
        return 1
    best = max(counts.items(), key=lambda kv: (kv[1], kv[0]))
    return best[0]


def _pad(row, width):
    """Pad a row to `width` cells so short rows align over the table columns.

    Rows that are shorter than the modal width are left-padded (blank cell first)
    by default. This matches the common layout where a column header (e.g. 'MALE |
    FEMALE') sits over the value columns while the first column is a row-label
    column with no header text. A right-pad is used only when the short row is
    clearly a spanned caption (title) row rather than a column header.
    """
    row = list(row)
    if len(row) < width:
        pad = width - len(row)
        row = [""] * pad + row
    return row[:width]


def _is_total_row(row):
    first = (row[0] or "").strip() if row else ""
    return bool(_TOTAL_RE.match(first))


def _is_item_row(row):
    """A data row generally has a leading label that is not a total/average marker."""
    return not _is_total_row(row)


def tables_to_html(block):
    """Render a detected table block as an HTML <table>.

    Improvements over naive rendering:
      - Merge consecutive leading header lines so a two-line header (e.g. 'MALE |
        FEMALE' over 'count | %') becomes one <thead> row.
      - Left-pad header rows so a row-label column with no header text (the blank
        cell on the left) aligns correctly.
      - Send TOTAL / AVG. rows to a <tfoot> so they read as summary rows.
      - Drop phantom header-only fragments that contain no real data rows.
    """
    rows = [split_cells(ln) for ln in block]
    if not rows:
        return ""

    width = _modal_width(rows)

    full_rows = [r for r in rows if len(r) >= width]
    if len(full_rows) <= 1:
        return ""

    # ----- Gather leading header lines (rows narrower than a data row are labels). -----
    # A row is a *unit* header if it contains only unit markers (count, %, #, dashes/underscores)
    # rather than real data — these belong in the <thead> with the label header above them.
    def _is_unit_row(cells):
        non_blank = [c for c in cells if c and c.strip()]
        if not non_blank:
            return True
        for c in non_blank:
            t = c.strip().lower()
            if re.match(r"^(count|#|%|no\.?|number|avg|___+|---+|\.+|[0-9]+%?)$", t):
                continue
            return False
        return True

    header_lines = []
    body_start = 0
    for i, r in enumerate(rows):
        is_below_full = len(r) < width
        if i == 0 or ((is_below_full or _is_unit_row(r)) and not _is_total_row(rows[i]) and len(r) >= 1):
            header_lines.append(r)
            body_start = i + 1
        else:
            break

    if not header_lines:
        header_lines = [rows[0]]
        body_start = 1

    # Merge header lines cell-by-cell (each line contributes one cell column-aligned).
    header_cells = header_lines[0]
    for extra in header_lines[1:]:
        merged = []
        for a, b in zip(header_cells + [""] * width, _pad(extra, width)):
            # Combine; if both have text, join with a line break.
            merged.append((a + " " + b).strip() if a and b else (a or b))
        header_cells = merged
    header_cells = _pad(header_cells, width)

    thead_html = "<thead><tr>" + "".join(
        "<th>%s</th>" % html_escape(c) for c in header_cells
    ) + "</tr></thead>"

    body_rows = rows[body_start:]

    tbody = []
    tfoot = []
    for r in body_rows:
        padded = _pad(r, width)
        if _is_total_row(padded):
            tfoot.append(padded)
        else:
            tbody.append(padded)

    def rows_html(rlist):
        parts = []
        for r in rlist:
            cells = "".join("<td>%s</td>" % html_escape(c) for c in r)
            parts.append("<tr>%s</tr>" % cells)
        return "".join(parts)

    tbody_html = "<tbody>" + rows_html(tbody) + "</tbody>" if tbody else ""
    tfoot_html = "<tfoot>" + rows_html(tfoot) + "</tfoot>" if tfoot else ""

    return '<div class="table-block"><table>%s%s%s</table></div>' % (thead_html, tbody_html, tfoot_html)


def html_escape(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def representative_quote(transcript, max_len=180):
    """Extract a short representative quote from the visible text of a page."""
    text = transcript
    # Drop scan-marker noise lines
    kept = []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s:
            continue
        if any(m.lower() in s.lower() for m in SCAN_MARKERS):
            continue
        kept.append(s)
    joined = " ".join(kept)
    # Trim bracketed annotations
    joined = re.sub(r"\[[^\]]*\]", " ", joined)
    joined = re.sub(r"\s{2,}", " ", joined).strip()
    if not joined:
        return ""
    # Try to end on a sentence boundary near max_len
    if len(joined) <= max_len:
        return joined
    cut = joined[:max_len]
    last_sentence = cut.rfind(". ")
    if last_sentence > 40:
        return cut[: last_sentence + 1]
    last_space = cut.rfind(" ")
    return cut[:last_space] + "…"
