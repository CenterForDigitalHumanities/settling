"""Corrections to bracketed editorial notes about image rotation.

Eleven pages carry a note that no longer matches what the catalog does with the image.
Ten tell the reader the page is sideways while the catalog applies no rotation to it;
that is not a contradiction in the data so much as a fossil - the note was written
against an earlier photograph of the same page, and the migration swapped in an upright
image without touching the prose. The eleventh is the reverse: the note and the table
agreed with each other, and both were wrong.

Each case was settled by OCR at all four angles, scoring the recovered words against the
page's own transcription. The four distinct histories are recorded in the comments
because they carry different information:

  A  Ashley re-scanned the page but kept the original GUID filename, so the shipped
     bytes differ from the baseline while the name does not. The baseline bytes were
     1024x768 landscape; hers are 768x1024 portrait.
  B  Ashley re-scanned the page and gave it a human name, superseding the old entry.
  C  The file has never been replaced. The note was inaccurate when it was written.
  D  The rotation entry itself is removed, because the note was written to justify it.

Only the rotation claim is removed. Anything else a note carried - a torn corner, a
cut-off heading, uncertainty about grid attribution - is a statement about the page
and is preserved verbatim.
"""

UPRIGHT = "[Superseded scan was photographed sideways; this image is upright. "
NEVER = "[Top of sheet cut off.]"

# imageFile -> (exact note as transcribed, replacement)
TRANSCRIPT_NOTES = {
    # A - GUID retained, bytes replaced by Ashley's upright re-scan
    "486E2B93-6B1D-452E-9EAB-67B6D01AE729_1_105_c.jpeg": (
        "[Image rotated 90 degrees; text reads sideways]",
        UPRIGHT + "Text reads sideways in the earlier photograph.]"),
    "55DA5D5D-5ED9-4278-B278-6E50CEDD2D89_1_105_c.jpeg": (
        "[image rotated 90 degrees]",
        UPRIGHT.rstrip(" ") + "]"),
    "17A709FB-9839-4458-96EF-766DCC0CBE49_1_105_c.jpeg": (
        "[page rotated sideways in the photo]",
        UPRIGHT.rstrip(" ") + "]"),
    "2C3188B8-CE09-4735-8C2B-521DD2F66367_1_105_c.jpeg": (
        "[image rotated 90\u00b0 counterclockwise in the photo; rotate clockwise to "
        "read. Hand-inked grid \u2014 presented as a list of labels since cell-by-cell "
        "row attribution is uncertain]",
        UPRIGHT + "Hand-inked grid \u2014 presented as a list of labels since "
        "cell-by-cell row attribution is uncertain]"),
    "3C9351ED-3037-4D20-A6CB-7F3557B0C815_1_105_c.jpeg": (
        "[Rotated 90 degrees sideways]",
        UPRIGHT.rstrip(" ") + "]"),

    # B - Ashley's martha11-pgN re-scans, superseding the arbitration pages
    "martha11-pg1.jpeg": ("[Image rotated 90 degrees.]", UPRIGHT.rstrip(" ") + "]"),
    "martha11-pg3.jpeg": ("[Page rotated 90 degrees in the photo]", UPRIGHT.rstrip(" ") + "]"),
    "martha11-pg4.jpeg": (
        "[Image rotated 90\u00b0; text reads sideways. Page opens mid-paragraph:]",
        UPRIGHT + "Page opens mid-paragraph:]"),
    "martha11-pg6.jpeg": ("[Rotated 90 degrees sideways]", UPRIGHT.rstrip(" ") + "]"),

    # C - never replaced, so the note described this very file and was wrong
    "0250A525-57E4-477A-B043-8D12FF78FCB4_1_105_c.jpeg": (
        "[rotated 90 degrees; top of sheet cut off]",
        NEVER),

    # D - the rotation itself was wrong, not just the prose. The +90 entry was added
    #     during the migration because Ashley's re-scan is a landscape file, i.e. from
    #     the shape heuristic this change set elsewhere disproved. At the angle that was
    #     applied, OCR recovers literally nothing; at 0 degrees it recovers the only
    #     readable text on the page, including two words from its own transcript. An
    #     independent projection test scores it strongly horizontal. See rotations.py.
    "C04781D1-50B5-4597-8901-850756CE32E6_1_105_c.jpeg": (
        "[Photograph rotated; two handwritten sheets on 'The Washington Post / "
        "memorandum' letterhead, plus edge of a typed page beneath.]",
        "[Two handwritten sheets on 'The Washington Post / memorandum' letterhead, "
        "plus edge of a typed page beneath. Upright as scanned: the letterhead and "
        "the typed fragments read horizontally.]"),
}
