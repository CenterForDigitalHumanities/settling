# Rotation map for sideways-scanned archive images.
# Keyed by the first 8 chars of the image filename (the GUID prefix).
# value = CSS rotation in degrees to apply so the document reads at its natural angle.
# -90 means counterclockwise 90 (rotate(-90deg)); the predominant direction for this
# collection, where the page's top edge sits at the right of the photo.
#
# HOW THESE WERE ESTABLISHED
#
# Not by visual inspection. That claim in the previous version of this header was not
# recoverable, and three entries were wrong. Each value below was set by running OCR
# (easyocr, CPU) on the image at all four angles and picking the winner. Two metrics,
# the second decisive:
#
#   1. volume   sum of len(text) * confidence over detections above 0.30 confidence.
#   2. matching how many OCR words of 4+ letters appear in that page's own transcript,
#      which the catalog already holds. A wrong angle recovers fluent junk; the right
#      angle recovers the page's real text. Matching is what separates "readable" from
#      "readable AS THIS PAGE".
#
# Sign convention: CSS rotate(theta) is clockwise, PIL Image.rotate(theta) is
# counter-clockwise, so emulating CSS theta is im.rotate(-theta, expand=True).
# A table value of -90 is therefore the angle reported as "270" below.
#
# Only images that are genuinely sideways are listed; upright images are omitted.
# One entry, 75C37361, could not be settled by OCR at all and is marked UNVERIFIED. Do
# not read that as confirmed -- it carries forward the previous value because nothing can
# beat it, not because anything checked it. It needs a human eye. C04781D1 was the other
# such candidate; on re-measurement its applied angle recovered 6 characters against 82
# at 0 degrees, so its rotation has been removed.
#
# This is offline evidence only. easyocr costs minutes per pass on CPU, so it cannot run
# in CI; verify.py check 12 enforces the invariants that are pure data.

ROTATIONS = {
    "020E073B": -90,  # DOC-009 newsroom staff table
    "04894C59": -90,  # DOC-011 settlement agreement p.2
    "3E9114EE": -90,  # DOC-009 newsroom census
    "44F2AF4E": -90,  # DOC-011 arbitration procedures p.5
    "49FB1A98": -90,  # DOC-008 Guild newsletter
    "6C631833": -90,  # DOC-009 newsroom census
    "86353EBE": -90,  # DOC-009 1996 newsroom staff
    "A224D886": -90,  # DOC-008 Guild newsletter. WAS +90. At 270: 1608 chars, 119
                      # words, 92 of them present in the page's own transcript
                      # (precision 0.77). At 90: 383 chars, 29 words, 0 transcript
                      # matches (precision 0.33). The +90 reading is OCR noise that
                      # happens to look like text; only -90 recovers this page.
    "C8993692": -90,  # DOC-009 1997 newsroom totals
    "EDB55A73": -90,  # DOC-009 newsroom staff
    "3B62EA88": -90,  # DOC-009 statistical sheet
    "CDA2FC15": -90,  # DOC-029 newspaper. WAS +90. At 270: 2422 chars, 246 words,
                      # 23 transcript matches. At 90: 172 chars, 12 words, 0 matches.
                      # The file is portrait (768x1024), which is what made a reviewer
                      # call this entry spurious -- but a portrait file can hold a
                      # sideways page, and this one does. Only the sign was wrong.
    "2E37B36F": -90,  # DOC-009 p8. WAS ABSENT ENTIRELY. At 270: 67 words at mean
                      # confidence 0.93 (volume 529.5). At 0: 0 words (volume 5.8), a
                      # 91x margin. Its seven sibling pages in the same folder are all
                      # -90. The transcript is "[illegible]", so transcript matching
                      # cannot help here and the confidence metric carries it alone.
    # C04781D1 (DOC-024 Hamilton's handwritten notes) is deliberately ABSENT. It carried
    # +90, which the migration added from a shape inference: Ashley's re-scan is a
    # landscape file, therefore the page must be sideways. That is the same heuristic this
    # change set disproved on CDA2FC15 from the opposite direction. Measured, bracketed
    # transcript notes excluded from the match set: at 90 degrees, 14 raw detections, 4
    # above 0.30 confidence, 6 characters, volume 3.3, zero transcript matches; at 0,
    # 82 characters, volume 38.4 and the only transcript match in the run. So the applied
    # angle was not silent -- it recovered a handful of junk characters -- but 0 degrees is
    # ~12x its volume and the only angle that reads as this page. An independent projection
    # test agrees it is strongly horizontal. The photo is of two loose handwritten sheets
    # plus the edge of a typed page, which is why no angle is clean. The transcript note
    # that asserted the rotation is corrected in transcript_notes.py.
    #
    # It is absent rather than present-and-zero purely as tidiness. A zero-valued key is
    # NOT rejected by check 12(b), which fails only on ambiguous keys and keys matching no
    # page; "5C74254C": 0 below is the counter-example, a deliberate zero-valued entry that
    # passes CI. What actually makes the removal safe is ROTATION_BASIS and check 12(e):
    # re-adding a rotation here without also recording why is now a build failure.
    "75C37361": -90,  # DOC-029 continuation. UNVERIFIED: the page is folded against a
                      # table edge and OCR returns 0-5 chars at every angle, which is
                      # consistent with this page's own transcript note. Kept at -90 on
                      # the strength of the previous value. Recorded for the human who
                      # checks it: 0 degrees scored marginally higher (3 chars vs 0),
                      # but 3 characters with no transcript match is noise, not signal,
                      # and unlike C04781D1 there is no independent method agreeing.
                      # This is the genuinely unresolved one. Needs a human eye.
    "5C74254C": 0,    # DOC-029 table-photo sep (no content to orient by)
    #
    # Removed when Ashley's ordered set was adopted, because her file replaced the
    # repo copy and hers is already upright. Verified two ways: the shipped bytes are
    # portrait where origin/main's were landscape under the same filename, and the
    # shipped copies OCR clean at 0 degrees:
    #   486E2B93, 55DA5D5D (Swoboda memos), 17A709FB, 2C3188B8 (1995 tallies),
    #   3C9351ED (Unit News).
    #
    # Also removed as dead -- superseded by her human-named re-scans of the same
    # arbitration-procedure pages, so no catalog image carries these prefixes:
    #   B32F08FD, B559737D, D33544E8, 3B9C8F5A.
    #
    # WARNING ON KEYING: rotation_for() matches on image_file[:8]. Ashley's human-named
    # files martha11-pg1/3/4/6 all share the prefix "martha11", so one key would
    # silently rotate four different pages. No such key exists; verify.py check 12(b)
    # fails the build if one is added.
}

# Why every rotation the table actually applies was chosen. verify.py check 12(e)
# requires an entry here for each one, and 12(f) requires each entry here to still be an
# applied rotation, so a basis cannot outlive the decision it justifies.
#
# This exists because check 12(a) only enforces transcript => rotation. Before it, a
# rotation could be restored to the table from the very shape heuristic this branch
# disproved, pass every check, and ship a sideways page. Zero-valued entries need no
# basis because they apply nothing.
#
# Vocabulary, validated by the check:
#   "ocr"        settled by the four-angle test in the header above
#   "unverified" carried forward from the previous catalog; nothing could decide it
ROTATION_BASIS = {
    "020E073B": "ocr",
    "04894C59": "ocr",
    "3E9114EE": "ocr",
    "44F2AF4E": "ocr",
    "49FB1A98": "ocr",
    "6C631833": "ocr",
    "86353EBE": "ocr",
    "A224D886": "ocr: 92 transcript matches at 270, 0 at 90",
    "C8993692": "ocr",
    "EDB55A73": "ocr",
    "3B62EA88": "ocr",
    "CDA2FC15": "ocr: 246 words / 23 matches at 270 vs 12 words / 0 at 90",
    "2E37B36F": "ocr: volume 529.5 at 270 vs 5.8 at 0",
    "75C37361": "unverified: 0-5 chars at every angle, needs a human eye",
}
