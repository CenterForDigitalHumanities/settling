# Martha M. Hamilton Documents — Archive Schema

This schema governs how each image in the source folder is described and how the
images are grouped into abstracted documents. All reader sub-agents must return
strict JSON in this shape.

Source folder: `C:\Users\cubap\LesTrouves\Martha M. Hamilton Documents`

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
      "title": "Short title",
      "documentType": "arbitration-exhibit",
      "subject": "Who/what it concerns",
      "date": "YYYY or approx date or unknown",
      "pageCount": 2,
      "confidence": "high",
      "notes": "Brief summary / why grouped this way",
      "pages": [
        {
          "imageFile": "00037A57-A636-46C7-8FEC-7954417D9EBE_1_105_c.jpeg",
          "pageNumber": 1,
          "pageKind": "content",
          "transcript": "Full transcription of visible text"
        }
      ]
    }
  ]
}
```

`pageKind` values: `content`, `cover`, `divider`, `table-photo`, `photograph`, `blank`, `partial`.

`confidence` values: `high`, `medium`, `low`.

Group consecutive images that appear to be the same document into one document
objects, preserving order. Separate them into different documents when the
content clearly changes to a different item (different header, different
document, obvious new exhibit). Include empty `table-photo` separators inside the
document `pages` array where they appear between the real pages.
