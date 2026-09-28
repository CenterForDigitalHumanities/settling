# Martha M. Hamilton Documents — Archive Schema

This schema governs how each image in the source folder is described and how the
images are grouped into abstracted documents. All reader sub-agents must return
strict JSON in this shape.

Source folder (original scans): `review/martha/images/` in this repository.
Ordered collection (defines the catalog): `U:\Downloads\Martha M. Hamilton Documents (ordered)\Martha M. Hamilton Documents` —
Ashley Hamilton's own grouping of the scans into numbered folders.

## Rules for reading

- Use ONLY your vision. Do NOT run OCR scripts, Tesseract, or any image-processing
  command-line tool. You may turn the image mentally / describe orientation, and
  note when text is rotated (e.g. sideways) so a human can rotate it.
- Transcribe each page as accurately as you can. Never invent content. If a
  passage is illegible, unreadable, or too blurry, record
  `"transcript": "[illegible]"` or describe only what is visible (headings,
  structure) and set `confidence: "low"`.
- Do NOT fabricate names, dates, numbers, or claims.
- Some images are near-empty photos of blank/damaged table surfaces — these are
  usually "sepia page" separators between scans of the same document. Record them
  as `pageKind: "table-photo"` and note they contain no legible content.

## Classifications (documentType)

Pick the best fit:
- `arbitration-exhibit` — arbitration/legal exhibit or settlement material
- `memo` — internal office memo (The Post, etc.)
- `letter` — correspondence
- `report` — salary/compensation analysis or narrative report
- `newspaper-clipping` — printed news article
- `photograph` — a photo, not a document
- `other` — anything else; describe in `notes`

## Output JSON shape (top-level clients array)

```json
{
  "documents": [
    {
      "id": "DOC-001",
      "folder": "Martha 1",
      "order": 1,
      "orderBasis": "internal-pagination",
      "title": "Short title",
      "documentType": "arbitration-exhibit",
      "subject": "Who/what it concerns",
      "date": "YYYY or approx date or unknown",
      "pageCount": 2,
      "confidence": "high",
      "orderConfidence": "high",
      "notes": "Brief summary / why grouped this way",
      "previousDocIds": ["DOC-012", "DOC-056"],
      "pages": [
        {
          "imageFile": "00037A57-A636-46C7-8FEC-7954417D9EBE_1_105_c.jpeg",
          "pageNumber": 1,
          "pageKind": "content",
          "transcript": "Full transcription of visible text",
          "transcriptionConfidence": "high",
          "orderBasis": "internal-pagination",
          "previousDocId": "DOC-012",
          "sourceFilename": "Martha 1/486E2B93-....jpeg",
          "supersedes": "B559737D-....jpeg",
          "notFiledReason": "only for pages in the Not filed group"
        }
      ]
    }
  ],
  "supersededPages": []
}
```

`pageKind` values: `content`, `cover`, `divider`, `table-photo`, `photograph`, `blank`, `partial`.

Two confidence fields, deliberately separate:

| field | on | rates | values |
| --- | --- | --- | --- |
| `confidence` | document | how reliably the text could be transcribed | `high`, `medium`, `low` |
| `orderConfidence` | document | how firmly the page sequence is evidenced | `high`, `mixed`, `medium` |

`confidence` is the original schema's meaning and is inherited from the document's least
legible page. `orderConfidence` is derived from the pages' `orderBasis` (see below).

## Catalog structure and order

The catalog mirrors Ashley Hamilton's ordered collection rather than the order the
scans happened to be read in. **One folder is one document**, and the image files
inside it are that document's pages, in sequence.

- `documents` is emitted in catalog order and `build_reports.py` must not re-sort it.
- `docId` runs `DOC-001`…`DOC-029` following the folder number.
- `folder` is Ashley's folder name; `order` is its 1-based position in the catalog.
- Pages Ashley left loose in the folder root form the `Unfiled` document; payload
  pages with no counterpart in her set form the `Not filed` document. Both come last.
- `previousDocIds` / `previousDocId` point back at the pre-reorganisation catalogue,
  which grouped pages by what appeared to be one item rather than by folder. Because
  Ashley's folders are thematic, one old document can be split across several
  folders and one folder can gather pages from several old documents.
- `sourceFilename` records Ashley's own filename where it differs from the stored
  image name. It is the provenance link for pages she renamed or re-scanned; identity
  was established by content hash, never by filename.
- `supersedes` / `supersededPages` record pages removed from the catalogue because
  Ashley supplied a better scan of the same page. The old files stay on disk.

### `orderBasis`

How much the page sequence inside a document can be trusted:

| value | meaning |
| --- | --- |
| `explicit` | Ashley's own filename states the page number. |
| `internal-pagination` | Printed page numbers or unbroken paragraph numbering on the pages fix the sequence. |
| `content-sequence` | Pages of one physical document, rejoined by continuity of the text. |
| `editorial-alphabetical` | Our arrangement, by comparator surname. |
| `editorial-chronological` | Our arrangement, by dates written on the pages. |
| `not-asserted` | The grouping is Ashley's; the sequence within it is ours and makes no claim about her intent. |

Ashley encoded folder membership, not page order, so only `explicit` and
`internal-pagination` may be presented as her ordering.

`orderBasis` is recorded **per page** as well as per document. A document's own value is
the label its folder was given; where the evidence only covers part of the folder, the
weaker pages carry their own value and the document is rated `orderConfidence: "mixed"`.
Downgrades are declared in `order_table.py` as `page_basis={pageNumber: basis}` so the
curated table stays the single source of truth. A document is `high` when every page is
`explicit` or `internal-pagination`, `mixed` when only some are, and `medium` when none
are. Do not let every page simply copy the folder value &mdash; a uniform copy carries no
information and will contradict the notes.

Grouping follows Ashley's folders, not a judgement about where one item ends: every
folder is exactly one document, and every image in it is a page of that document.
Do not split a folder across documents or merge two folders, even when the content
looks like separate items &mdash; that is what her folder names are for. Keep empty
`table-photo` separators inside the document `pages` array where they appear between
the real pages.

### Scripts

| file | role |
| --- | --- |
| `order_table.py` | the curated page order for each folder, with its `orderBasis` |
| `titles.py` | title, type, subject, date and notes per document; not-filed reasons |
| `build_reports.py` | renders `martha.html` and `martha-audit.html` from `master-data.json` |
| `build_master.py` | one-shot migration that produced the current `master-data.json` (provenance only) |
| `verify.py` | re-runnable checks on the catalogue and reports |
