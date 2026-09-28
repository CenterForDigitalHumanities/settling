# Curated folder -> page-order table. Keys are the first 8 chars of the payload
# imageFile. "NEW:<n>" are Ashley's four brand-new arbitration re-scans.
# basis values:
#   explicit              - Ashley's own filename encodes the page number
#   internal-pagination   - printed page numbers / paragraph continuity in the scans
#   content-sequence      - pages of one physical document split across her folders
#   editorial-alphabetical- arranged by comparator/subject name (my arrangement)
#   editorial-chronological- arranged by date (my arrangement)
#   not-asserted          - grouping only; page order is ours, no claim about intent
#
# Optional "page_basis" downgrades individual pages below the folder's label when the
# folder's evidence only covers part of it (e.g. a numbered document whose tail sheets
# carry no numbering). "rescans" lists GUID prefixes Ashley re-scanned at higher
# resolution, which build_master.py uses to assert the pre-migration baseline.

FOLDERS = [
    ("Martha 1", dict(basis="editorial-chronological", title="", pages=[
        "3208105C", "2ADEBF18", "71B00413"])),
    ("Martha 2", dict(basis="not-asserted", title="", pages=[
        "A0E6387C", "562BE275"])),
    ("Martha 3", dict(basis="not-asserted", title="", pages=[
        "9A931AA6", "D337D813", "5E0626DD"])),
    ("Martha 4", dict(basis="not-asserted", title="", pages=[
        "705804F1", "84E1D431"])),
    ("Martha 5", dict(basis="internal-pagination", title="", pages=[
        "4236E93D", "8EF47E16", "32386A42", "10049231", "8FED28BA", "41CA6664",
        "45B75226", "BA1BD3FA", "DAD81785", "7BC3D189", "B03EEE55", "B27174D5",
        "65597FED", "05357027"])),
    ("Martha 6", dict(basis="not-asserted", title="", pages=[
        "03AF6102", "341A593E", "2AED39B4", "32765112", "5551063C", "5144DD97",
        "7903878F", "E6982426", "97EC57F6", "D95CD1E3", "F5CFB9BC"])),
    # Cover and numbered introduction are on the document's own pagination; the twelve
    # response sheets behind them carry no reliable numbering, so their order is ours.
    ("Martha 7", dict(basis="internal-pagination", title="", page_basis={n: "not-asserted" for n in range(3, 15)}, pages=[
        "C21A73F5", "3544C530", "C4FAD717", "DFEF0E89", "24230EBA", "348882EF",
        "14184033", "437C1B9C", "48C061FC", "709B688A", "95A0AAF9", "AA658104",
        "CCAD4C37", "E68F7CC5"])),
    ("Martha 8", dict(basis="not-asserted", title="", pages=[
        "A224D886", "49FB1A98"])),
    ("Martha 9", dict(basis="editorial-chronological", title="", pages=[
        "6C631833", "020E073B", "3E9114EE", "EDB55A73", "3B62EA88", "86353EBE",
        "C8993692", "2E37B36F"])),
    ("Martha 10", dict(basis="not-asserted", title="", rescans=["486E2B93", "55DA5D5D"],
        pages=["486E2B93", "55DA5D5D"])),
    ("Martha 11", dict(basis="explicit", title="", pages=[
        "NEW:pg1", "04894C59", "NEW:pg3", "NEW:pg4", "44F2AF4E", "NEW:pg6"])),
    ("Martha 12", dict(basis="not-asserted", title="", rescans=["17A709FB", "2C3188B8"],
        pages=["17A709FB", "2C3188B8"])),
    # Introduction page first, then comparator profiles in surname order; pages of a
    # single physical memo are kept adjacent (DOC-081, -103, -029, -144, -057).
    ("Martha 13", dict(basis="editorial-alphabetical", title="", pages=[
        "8A487FB7", "C5D410D0", "CA3AAEF8", "12C7BE9B", "DD507B03", "F3D7FF05",
        "EF2EEF16", "FCA955EA", "59D0D86A", "5EE72AFD", "059E7A9D", "CC6094DE",
        "1D1D985E", "27C69022", "3797394B", "37CDAE9F", "3977853B", "353EF589",
        "52FB2ADD", "90637975", "942109F5", "E98AB91F", "00037A57", "8226C5EB",
        "C15F1F2D", "698EDC6B", "FB52E474", "87165334", "3DDC7B34"])),
    ("Martha 14", dict(basis="not-asserted", title="", pages=[
        "ADBCDF62", "F2E17762"])),
    ("Martha 15", dict(basis="not-asserted", title="", pages=[
        "36C7EEB3", "3E305A17"])),
    # The three contract pages are fixed by their printed numbers (29, 30, 34); placing
    # the request memo ahead of them is our editorial call, not the document's order.
    ("Martha 16", dict(basis="internal-pagination", title="", page_basis={1: "not-asserted"}, pages=[
        "19ECFDC6", "979C7D06", "845A7ECA", "31969D00"])),
    ("Martha 17", dict(basis="not-asserted", title="", pages=[
        "0250A525", "1153867E", "15DBC894", "17427AFB", "1EFF2199", "22CF0B38",
        "2AB62984", "32D005AE", "5285A12E", "7D515688", "85E272CF", "885E3AB1",
        "943BF788", "CC4A6D61", "FB914AB6", "FEE99965"])),
    ("Martha 18", dict(basis="content-sequence", title="", pages=[
        "42E20208", "4AFB1E91", "895DDE75", "23FAC1D1", "F8C28029"])),
    ("Martha 19", dict(basis="content-sequence", title="", pages=[
        "BF7FD77A", "7D8E158D"])),
    ("Martha 20", dict(basis="not-asserted", title="", rescans=["3C9351ED"],
        pages=["3ECFFF9F", "3C9351ED"])),
    ("Martha 21", dict(basis="editorial-chronological", title="", pages=[
        "4E570377", "E47BB939", "0AC1D8FD"])),
    ("Martha 22", dict(basis="content-sequence", title="", pages=[
        "62E6E6D8", "120DE6EE"])),
    ("Martha 23", dict(basis="content-sequence", title="", pages=[
        "E3136FCF", "20CC7734", "1781CF24"])),
    # Pages 1-3 follow the memo's own numbering; the handwritten notes page is placed
    # last by us, so its position is not asserted as the document's.
    ("Martha 24", dict(basis="internal-pagination", title="", rescans=["C04781D1"],
        page_basis={4: "not-asserted"},
        pages=["5637EF0F", "2D71B907", "EDB712D1", "C04781D1"])),
    ("Martha 25", dict(basis="content-sequence", title="", pages=[
        "8DBBE865", "EA9F9F76"])),
    ("Martha 26", dict(basis="not-asserted", title="", pages=[
        "3D979199", "8703632A"])),
    ("Martha 27", dict(basis="content-sequence", title="", pages=[
        "64358739", "8F83CDBC"])),
    ("Unfiled (loose in folder root)", dict(basis="not-asserted", title="", pages=[
        "0FD65793", "1263D13C", "47440AD3", "70501C13", "D60E9961", "3FCCF507"])),
    ("Not filed (absent from Ashley's set)", dict(basis="not-asserted", title="", pages=[
        "CDA2FC15", "099DFA73", "2E5C18E8", "75C37361", "5C74254C", "6EC7CCC7",
        "16E4B4BA", "24990590", "317C80E9", "C83CBACF", "C94FDE4B", "ED565C0F"])),
]

# Payload pages Ashley did not file because she re-scanned them herself. They are
# not shown in the catalog; each is recorded as supersededBy provenance on the
# Martha 11 page that replaces it.

# Ashley's four brand-new scans -> the payload page whose transcript they inherit
NEW_SCANS = {
    "NEW:pg1": ("B559737D", "Arbitation Procedures pg 1.jpeg"),
    "NEW:pg3": ("D33544E8", "Arbitation Procedures pg 3.jpeg"),
    "NEW:pg4": ("B32F08FD", "Arbitation Procedures pg 4.jpeg"),
    "NEW:pg6": ("3B9C8F5A", "Arbitation Procedures pg 6.jpeg"),
}
