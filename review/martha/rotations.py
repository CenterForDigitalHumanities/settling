# Rotation map for sideways-scanned archive images.
# Keyed by the first 8 chars of the image filename (the GUID prefix).
# value = CSS rotation in degrees to apply so the document reads at its natural angle.
# -90 means counterclockwise 90 (rotate(-90deg)); the predominant direction for this
# collection where the page's top edge sits at the right of the photo.
#
# Determined by visual inspection of each image. Only images that are genuinely
# sideways are listed; upright images are intentionally omitted.

ROTATIONS = {
    "020E073B": -90,  # DOC-002 newsroom staff table
    "04894C59": -90,  # DOC-005 settlement agreement p.2
    "3E9114EE": -90,  # DOC-010 newsroom census
    "44F2AF4E": -90,  # DOC-015 arbitration procedures p.5
    "49FB1A98": -90,  # DOC-019 Guild newsletter
    "6C631833": -90,  # DOC-035 newsroom census (confirmed)
    "86353EBE": -90,  # DOC-049 1996 newsroom staff
    "A224D886": 90,   # DOC-069 Guild newsletter (confirmed +90)
    "C04781D1": 90,   # Hamilton's handwritten notes (Ashley's re-scan is landscape)
    "C8993692": -90,  # DOC-081 1997 newsroom totals
    "CDA2FC15": 90,   # DOC-085 newspaper (confirmed +90)
    "EDB55A73": -90,  # DOC-100 newsroom staff
    "3B62EA88": -90,  # DOC-145 statistical sheet
    "75C37361": -90,  # DOC-040 continuation (badly rotated)
    "5C74254C": 0,    # DOC-030 table-photo sep (no content)
    #
    # Removed when Ashley's ordered set was adopted, because her file replaced the
    # repo copy and hers is already upright (verified by correlating each pair):
    #   486E2B93, 55DA5D5D (Swoboda memos), 17A709FB, 2C3188B8 (1995 tallies),
    #   3C9351ED (Unit News). Also dropped as dead: B32F08FD, B559737D, D33544E8,
    #   3B9C8F5A — the arbitration-procedure pages her re-scans superseded.
}
