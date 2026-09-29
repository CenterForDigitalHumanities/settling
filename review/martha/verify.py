# -*- coding: utf-8 -*-
"""Post-write verification of the reorganised Martha catalog.

Usage: python verify.py [--source=<Ashley's ordered folder>]
Without --source the byte-for-byte comparison against Ashley's originals is
skipped; every other check still runs.
"""
import json, os, re, struct, sys, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import order_table as ot
import rotations

MAR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(MAR))
IMG = os.path.join(MAR, "images")
d = json.load(open(os.path.join(MAR, "master-data.json"), encoding="utf-8"))
docs = d["documents"]
ok = True

def bad(msg):
    global ok
    ok = False
    print("FAIL", msg)

print("docs", len(docs), "pages", sum(len(x["pages"]) for x in docs))

# 1. every referenced image exists; every page has a transcript
for x in docs:
    for p in x["pages"]:
        f = os.path.join(IMG, p["imageFile"])
        if not os.path.isfile(f):
            bad("missing image %s (%s)" % (p["imageFile"], x["docId"]))
        if not (p.get("transcript") or "").strip():
            bad("empty transcript %s p%s" % (x["docId"], p["pageNumber"]))

def sortkey(y):
    m = re.search(r"(\d+)", y[0])
    return (0 if y[0].startswith("Martha") else 1 if y[0].startswith("Unfiled") else 2,
            int(m.group(1)) if m else 999)


# 2. folder order is numeric and matches the curated table
want = [f for f, _ in sorted(ot.FOLDERS, key=sortkey)]
got = [x["folder"] for x in docs]
if want != got:
    bad("folder order\n  want %s\n  got  %s" % (want, got))
if [x["docId"] for x in docs] != ["DOC-%03d" % i for i in range(1, 30)]:
    bad("docId sequence")

# 3. page numbers are 1..n contiguous per doc
for x in docs:
    if [p["pageNumber"] for p in x["pages"]] != list(range(1, len(x["pages"]) + 1)):
        bad("page numbering %s" % x["docId"])
    if x["pageCount"] != len(x["pages"]):
        bad("pageCount %s" % x["docId"])

# 4. curated sequence preserved exactly
for x, (folder, spec) in zip(docs, sorted(ot.FOLDERS, key=sortkey)):
    seq = [p["imageFile"][:8].upper() if not p["imageFile"].startswith("martha11")
           else "NEW:pg" + p["imageFile"][11] for p in x["pages"]]
    if seq != spec["pages"]:
        bad("sequence drift in %s\n  want %s\n  got  %s" % (folder, spec["pages"], seq))
    if x["orderBasis"] != spec["basis"]:
        bad("basis drift in %s" % folder)

# 5. rotations: the 5 upright re-scans must be absent, and every value must be a
#    right angle. Individual angles are editorial data and change with the evidence, so
#    no specific page's angle is asserted here; check 12 owns the invariants that couple
#    the table to the transcripts and to the files on disk.
sys.path.insert(0, MAR)
from rotations import ROTATIONS
for k in ("486E2B93", "55DA5D5D", "17A709FB", "2C3188B8", "3C9351ED", "B32F08FD", "B559737D", "D33544E8", "3B9C8F5A"):
    if k in ROTATIONS:
        bad("stale rotation entry %s" % k)
for k, v in ROTATIONS.items():
    if v is None:
        bad("None rotation value remains in %s" % k)
    elif v % 90:
        bad("rotation %s is %s, not a multiple of 90" % (k, v))

# 6. Ashley's 6 re-scans + 4 new scans are byte-identical to her originals
def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()

ASH, _pending_path = None, False
_args = sys.argv[1:]
for _i, _a in enumerate(_args):
    if _pending_path:
        ASH, _pending_path = _a, False
    elif _a.startswith("--source="):
        ASH = _a[len("--source="):]
    elif _a == "--source":
        # Both spellings mean the same thing to someone typing it. Accepting only
        # --source=PATH made `--source <path>` fall through to the SKIP branch with
        # exit 0, so the byte check looked like it had run when it never had.
        _pending_path = True
    else:
        # An unrecognised argument must not be swallowed either.
        print("ERROR unrecognised argument %r (expected --source=PATH)" % _a)
        sys.exit(2)
if _pending_path:
    print("ERROR --source needs a path")
    sys.exit(2)
if not ASH:
    # Includes --source= with an empty value, which is treated as "no source" rather than
    # "source that does not exist". Deliberate: an explicit empty flag reads like an
    # intentional opt-out, and it prints SKIP so the run never claims a comparison it
    # skipped. A non-empty but bad path is the dangerous case and errors below.
    print("SKIP byte-for-byte check (pass --source=<Ashley's ordered folder>)")
elif not os.path.isdir(ASH):
    # A bad path used to SKIP with exit 0 like the no-flag case. Ashley keeps two folders
    # side by side and only "...Documents (ordered)" holds her re-scans, so a wrong path
    # is the realistic mistake and it has to be loud.
    print("ERROR --source path is not a directory: %s" % ASH)
    print("       Ashley's re-scans are in 'Martha M. Hamilton Documents (ordered)'.")
    sys.exit(2)
else:
    pairs = [("martha11-pg1.jpeg", "Arbitation Procedures pg 1.jpeg"), ("martha11-pg3.jpeg", "Arbitation Procedures pg 3.jpeg"),
             ("martha11-pg4.jpeg", "Arbitation Procedures pg 4.jpeg"), ("martha11-pg6.jpeg", "Arbitation Procedures pg 6.jpeg")]
    for pre in ("486E2B93", "55DA5D5D", "17A709FB", "2C3188B8", "3C9351ED", "C04781D1"):
        for root, dn, fn in os.walk(ASH):
            for f in fn:
                if f.upper().startswith(pre):
                    pairs.append((os.path.basename(os.path.join(root, f)), f))
    byte_ok = True
    for repo_name, ash_name in pairs:
        src = os.path.join(ASH, ash_name)
        if not os.path.isfile(src):
            src = next((os.path.join(r, f) for r, _, fs in os.walk(ASH) for f in fs if f == ash_name), None)
        a = os.path.join(IMG, repo_name)
        if not os.path.isfile(a):
            bad("not in repo: %s" % repo_name)
            byte_ok = False
        elif src is None:
            # Ashley keeps two folders side by side, "...Documents" and "...Documents
            # (ordered)", and only the latter holds her re-scans. Pointing --source at the
            # wrong one is the realistic mistake, and it used to raise TypeError out of
            # md5(None) -- on the martha11 pairs first, so the crash arrived before any
            # of the six GUID comparisons that would have passed. Name the file instead.
            bad("not found under --source: repo copy %s has no Ashley original %r; "
                "is --source the (ordered) folder?" % (repo_name, ash_name))
            byte_ok = False
        elif md5(a) != md5(src):
            bad("bytes differ from Ashley's original: %s" % repo_name)
            byte_ok = False
    # Only when every comparison actually held. The line used to print unconditionally,
    # so a run reporting "FAIL bytes differ" was followed on the next line by a
    # "verified ... byte-for-byte" that was not true.
    if byte_ok:
        print("verified %d copied images byte-for-byte against Ashley's files" % len(pairs))

# 7. HTML: docs appear in catalog order
h = open(os.path.join(REPO, "review", "martha.html"), encoding="utf-8").read()
ids = re.findall(r'<article class="doc" id="(DOC-\d+)"', h)
if ids != ["DOC-%03d" % i for i in range(1, 30)]:
    bad("HTML doc order wrong: %s" % ids[:3])
for needle in ("Martha 1", "Martha 27", "Unfiled", "Not filed", "not-asserted", "internal-pagination"):
    if needle not in h:
        bad("HTML missing %r" % needle)
print("HTML doc order OK; %d cards; %d bytes" % (len(ids), len(h)))
a = open(os.path.join(REPO, "review", "martha-audit.html"), encoding="utf-8").read()
if len(re.findall(r'<article class="martha-card"', a)) != 29:
    bad("audit card count")

# 8. provenance completeness
nf = [x for x in docs if x["folder"].startswith("Not filed")][0]
if not all(p.get("notFiledReason") for p in nf["pages"]):
    bad("Not filed page missing a reason")
sup = {s["replacedBy"] for s in d["supersededPages"]}
if sup != {"martha11-pg%d.jpeg" % n for n in (1, 3, 4, 6)}:
    bad("supersededPages mapping")
ren = sum(1 for x in docs for p in x["pages"] if p.get("sourceFilename"))
print("pages carrying Ashley's source filename:", ren, "(expect 18 = 8 renamed + 6 re-scans + 4 new)")
if ren != 18:
    bad("sourceFilename count")

# 9. order basis is genuinely per-page, and the two confidence fields stay distinct
BASES = set(d["ordering"]["basisVocabulary"])
STRONG = {"explicit", "internal-pagination"}
for x in docs:
    for p in x["pages"]:
        if p.get("orderBasis") not in BASES:
            bad("unknown page orderBasis %r (%s p%s)" % (p.get("orderBasis"), x["docId"], p["pageNumber"]))
        if p.get("transcriptionConfidence") not in ("high", "medium", "low"):
            bad("missing page transcriptionConfidence (%s p%s)" % (x["docId"], p["pageNumber"]))
    if x.get("orderConfidence") not in ("high", "mixed", "medium"):
        bad("bad orderConfidence %s" % x["docId"])
    bases = [p["orderBasis"] for p in x["pages"]]
    want_oc = "high" if all(b in STRONG for b in bases) else ("mixed" if any(b in STRONG for b in bases) else "medium")
    if x["orderConfidence"] != want_oc:
        bad("orderConfidence %s: want %s got %s" % (x["docId"], want_oc, x["orderConfidence"]))
    ranks = {"high": 0, "medium": 1, "low": 2}
    want_c = max((p["transcriptionConfidence"] for p in x["pages"]), key=lambda c: ranks[c])
    if x["confidence"] != want_c:
        bad("confidence %s: want %s got %s" % (x["docId"], want_c, x["confidence"]))

# The defect this guards: a uniform copy of the folder value carries no information.
echo = sum(1 for x in docs for p in x["pages"] if p["orderBasis"] == x["orderBasis"])
if echo == sum(len(x["pages"]) for x in docs):
    bad("every page just echoes its folder's orderBasis - per-page basis is not doing any work")
print("pages whose basis differs from their folder's label:",
      sum(len(x["pages"]) for x in docs) - echo, "(expect 14)")

# The specific downgrades, and the order_table overrides that produce them, must agree.
EXPECT = {"DOC-007": {n: "not-asserted" for n in range(3, 15)},
          "DOC-016": {1: "not-asserted"},
          "DOC-024": {4: "not-asserted"}}
for did, over in EXPECT.items():
    x = next(y for y in docs if y["docId"] == did)
    for p in x["pages"]:
        want_b = over.get(p["pageNumber"], x["orderBasis"])
        if p["orderBasis"] != want_b:
            bad("%s p%s basis: want %s got %s" % (did, p["pageNumber"], want_b, p["orderBasis"]))
    if x["orderConfidence"] != "mixed":
        bad("%s should be orderConfidence=mixed" % did)
for folder, spec in ot.FOLDERS:
    for n, b in spec.get("page_basis", {}).items():
        x = next(y for y in docs if y["folder"] == folder)
        if x["pages"][n - 1]["orderBasis"] != b:
            bad("order_table page_basis %s p%s not applied" % (folder, n))

# Two docs keep fully evidenced order; the transcription ratings must not have been lost.
if [x["docId"] for x in docs if x["orderConfidence"] == "high"] != ["DOC-005", "DOC-011"]:
    bad("orderConfidence=high set changed")
if not any(x["confidence"] == "low" for x in docs):
    bad("no low-confidence transcription remains - collapsing 148 docs into 29 dropped the reading ratings")

# 10. no machine-specific paths in the committed data
sf = d.get("sourceFolder", "")
if "\\" in sf or "/" in sf or re.match(r"^[A-Za-z]:", sf):
    bad("sourceFolder is an absolute path, not a display name: %r" % sf)
for f in (os.path.join(REPO, "review", "martha.html"), os.path.join(REPO, "review", "martha-audit.html")):
    body = open(f, encoding="utf-8").read()
    if re.search(r"[A-Za-z]:\\\\|[A-Za-z]:\\Users|[A-Za-z]:\\Downloads", body):
        bad("absolute local path leaked into %s" % os.path.basename(f))
print("sourceFolder:", repr(sf))

# 11. every image the reports reference must resolve under the site's <base href="/settling/">
SRC_RE = re.compile(r'src="(review/martha/images/([^"]+))"')
OTHER_SRC = re.compile(r'src="((?!review/martha/images/|assets/|https?:)[^"]*images/[^"]+)"')
report_path = os.path.join(REPO, "review", "martha.html")
audit_path = os.path.join(REPO, "review", "martha-audit.html")
for f in (report_path, audit_path):
    body = open(f, encoding="utf-8").read()
    name = os.path.basename(f)
    if OTHER_SRC.search(body):
        bad("%s: image src not under review/martha/images/ - breaks <base href> resolution" % name)
    for src, _ in SRC_RE.findall(body):
        if not os.path.isfile(os.path.join(REPO, src.replace("/", os.sep))):
            bad("%s: referenced image missing on disk: %s" % (name, src))
# Coverage of the *rendered* page, not just the data: a report with no image for a
# page it transcribes is not auditable, and checks 1-10 cannot see that.
expected = {p["imageFile"] for x in docs for p in x["pages"]}
for label, f in (("martha.html", report_path), ("martha-audit.html", audit_path)):
    ref = {n for _, n in SRC_RE.findall(open(f, encoding="utf-8").read())}
    gap = expected - ref
    if gap:
        bad("%s imaged %d of %d pages, missing: %s" % (label, len(expected) - len(gap), len(expected), sorted(gap)[:5]))
    print("%s: %d of %d pages imaged" % (label, len(expected) - len(gap), len(expected)))

# 12. rotation. The decision lives in three places at once - rotations.py, the
#     JPEG's own pixel dimensions, and prose inside the transcript - and nothing
#     reconciled them, so a page could render sideways while its own text said
#     otherwise. Two of the 167 did.
MARKER_RE = re.compile(r"\[[^\]]*rotat[^\]]*\]", re.I)


def jpeg_dims(path):
    """(w, h) from the start-of-frame marker. Stdlib only; CI has no image library."""
    data = open(path, "rb").read()
    if data[:2] != b"\xff\xd8":
        return None
    i, n = 2, len(data)
    while i < n - 4:
        if data[i] != 0xFF:
            i += 1
            continue
        m = data[i + 1]
        if m == 0x01 or m == 0xD8 or m == 0xD9 or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def jpeg_exif_orientation(path):
    """EXIF tag 0x0112, or 1 when absent. No image library needed.

    Layout: FFD8 | FFE1 | len(2) | "Exif\\0\\0" | TIFF header, so the TIFF block
    starts at byte 12 and every offset inside it is relative to that point.
    """
    data = open(path, "rb").read()
    i, n = 2, len(data)
    while i + 4 <= n:
        if data[i] != 0xFF:
            return 1
        marker = data[i + 1]
        if marker == 0xE1 and data[i + 4:i + 10] == b"Exif\x00\x00":
            seg = data[i + 10:]
            endian = "<" if seg[0:2] == b"II" else ">"
            ifd = struct.unpack(endian + "I", seg[4:8])[0]
            count = struct.unpack(endian + "H", seg[ifd:ifd + 2])[0]
            for e in range(count):
                off = ifd + 2 + e * 12
                if off + 12 > len(seg):
                    break
                if struct.unpack(endian + "H", seg[off:off + 2])[0] == 0x0112:
                    return struct.unpack(endian + "H", seg[off + 8:off + 10])[0]
            return 1
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return 1


# (a) A transcript that tells the reader the image is sideways is a hard claim
#     about the shipped pixels, so the table must rotate it. The converse is NOT
#     required: not every rotated page carries a marker, because the markers were
#     written page by page and only some of them mention it.
for x in docs:
    for p in x["pages"]:
        if MARKER_RE.search(p.get("transcript") or ""):
            if not (rotations.ROTATIONS.get(p["imageFile"][:8], 0) or 0):
                bad("%s p%s transcript claims a rotated image but ROTATIONS has no entry"
                    % (x["docId"], p["pageNumber"]))

# (b) rotation_for() keys on the first 8 characters of the filename, and Ashley's
#     human names collide inside that window: martha11-pg1/pg3/pg4/pg6 all read
#     "martha11", so one key would silently rotate four different pages.
by_prefix = {}
for x in docs:
    for p in x["pages"]:
        by_prefix.setdefault(p["imageFile"][:8], set()).add(p["imageFile"])
for k in rotations.ROTATIONS:
    if len(by_prefix.get(k, ())) > 1:
        bad("ROTATIONS key %s is ambiguous, matches %s" % (k, sorted(by_prefix[k])))
    if k not in by_prefix:
        bad("ROTATIONS key %s matches no catalog page" % k)

# (c) EXIF orientation must be neutral. A baked-in 6 or 8 makes the browser rotate
#     the image before our own rotation is applied, so the two would stack.
for x in docs:
    for p in x["pages"]:
        e12 = jpeg_exif_orientation(os.path.join(IMG, p["imageFile"]))
        if e12 != 1:
            bad("%s p%s carries EXIF orientation %s; the pixel dimensions the table "
                "was keyed against are not what the browser displays"
                % (x["docId"], p["pageNumber"], e12))

# (d) File shape against rotation presence: reported, not failed. Both off-diagonal
#     shapes occur here and only one of them is a defect. DOC-009 p8 is a landscape
#     file with no entry and does read sideways (missing -90). DOC-029 p1 is a
#     portrait file with +90 and also reads sideways. Shape cannot decide
#     orientation, so it only points a human at pages worth reading.
sideways = []
for x in docs:
    for p in x["pages"]:
        dims = jpeg_dims(os.path.join(IMG, p["imageFile"]))
        if not dims:
            bad("%s p%s is not a readable JPEG" % (x["docId"], p["pageNumber"]))
            continue
        landscape, rot = dims[0] > dims[1], (rotations.ROTATIONS.get(p["imageFile"][:8], 0) or 0)
        if landscape and not rot:
            sideways.append("%s p%s %s %dx%d landscape, no rotation"
                            % (x["docId"], p["pageNumber"], p["imageFile"][:8], dims[0], dims[1]))
        elif rot and not landscape:
            sideways.append("%s p%s %s %dx%d portrait, rotated %+d"
                            % (x["docId"], p["pageNumber"], p["imageFile"][:8],
                               dims[0], dims[1], rot))
print("rotation: %d table entries, %d pages rotated, %d shape/rotation off-diagonal"
      % (sum(1 for v in rotations.ROTATIONS.values() if v),
         sum(1 for x in docs for p in x["pages"]
             if (rotations.ROTATIONS.get(p["imageFile"][:8], 0) or 0)), len(sideways)))
for s in sideways:
    print("   CHECK BY READING:", s)

# (e) Every applied rotation must record why. 12(a) only enforces transcript => rotation,
#     so before this a rotation could be restored from the shape heuristic this branch
#     disproved, pass every other check, and ship a sideways page. It is also invisible to
#     12(d): a landscape file WITH a rotation sits on that check's diagonal, so the report
#     that is meant to catch shape-driven rotations actively hides this regression.
#     Zero-valued entries apply nothing and need no basis.
BASIS_KINDS = ("ocr", "unverified")
# A "measurement" means a number attached to one of the two quantities the four-angle
# test actually reports. Requiring merely a digit was too weak: "ocr: 9",
# "ocr: see note 1" and "ocr: settled in round 8" all passed, which is a citation
# shape rather than a result.
MEASUREMENT_RE = re.compile(r"\b\d[\d.]*\s+(?:transcript\s+)?matches\b|\bvolume\s+\d", re.I)
ANGLE_RE = re.compile(r"\bat\s+(-?\d{1,3})\b")


def css_turn_names(v):
    """Both spellings of one CSS turn, for the failure message."""
    return " / ".join(str(x) for x in sorted({v, v + (360 if v < 0 else -360)}))


# The table and the basis prose hold the SAME unit: CSS rotate() degrees. build_reports.py
# drops the table value straight into `transform: rotate(<n>deg)` and PIL appears nowhere
# in the repo -- PIL is only mentioned in rotations.py's header because the offline OCR
# test emulated CSS theta with im.rotate(-theta). So a basis may name the applied turn
# under any spelling of it (-90, 270 and 540 are one rotation), which is congruence mod
# 360 rather than a lookup table. A table was also a crash: check 5 accepts any multiple
# of 90, so the legal value 270 hit a bare subscript and died with a KeyError and no
# verdict at all.
for k, v in sorted(rotations.ROTATIONS.items()):
    if not v:
        continue
    basis = getattr(rotations, "ROTATION_BASIS", {}).get(k)
    if not basis:
        bad("ROTATIONS entry %s applies %+d but ROTATION_BASIS records no reason; "
            "settle it by the four-angle OCR test and record it, or remove the entry"
            % (k, v))
    elif not basis.startswith(BASIS_KINDS):
        bad("ROTATION_BASIS %s has unrecognised basis %r; must start with one of %s"
            % (k, basis, ", ".join(BASIS_KINDS)))
    elif basis.startswith("ocr") and not MEASUREMENT_RE.search(basis):
        # Without this the credential is the three characters "ocr": re-adding the
        # disproved C04781D1 rotation with a bare "ocr" basis passed every check. A
        # fabricated number is still possible, but it is diffable and checkable against
        # the per-entry comment, where a bare method word was neither.
        bad("ROTATION_BASIS %s claims an OCR basis but records no measurement; cite the "
            "transcript matches or volume that settled the angle" % k)
    elif basis.startswith("ocr"):
        # The basis must name the angle that actually won, so a justification cannot be
        # pasted onto a different rotation than the run that produced it. Every applied
        # rotation on this branch is -90 and every ocr basis cites 270, so this is
        # currently vacuous; it is what stops that from drifting silently.
        # Matching is by INTERSECTION, deliberately: honest prose cites the losing angles
        # too ("volume 529.5 at 270 vs 5.8 at 0"), so requiring every cited angle to be
        # the winner would reject true statements. The residual weakness is that this
        # establishes the right angle APPEARS in the basis, not that it won.
        cited = set(int(a) for a in ANGLE_RE.findall(basis))
        if not any(a % 360 == v % 360 for a in cited):
            bad("ROTATION_BASIS %s cites angle(s) %s but the applied rotation is %+d, "
                "which is CSS %s; the basis must name the angle that won"
                % (k, sorted(cited) or "none", v, css_turn_names(v)))
for k in getattr(rotations, "ROTATION_BASIS", {}):
    if not (rotations.ROTATIONS.get(k, 0) or 0):
        bad("ROTATION_BASIS key %s records a basis for a rotation that is not applied" % k)

unverified = [k for k, b in getattr(rotations, "ROTATION_BASIS", {}).items()
              if b.startswith("unverified")]
# Pin the set rather than just counting it, the way check 9 pins the orderConfidence=high
# docs. Without this the count above is a print statement, not an assertion: a restored
# rotation labelled "unverified: trust me" passed, and downgrading all thirteen settled
# bases to unverified passed too. "unverified" must be earned by a human looking at the
# page, so adding to this list has to be a deliberate, visible edit.
if sorted(unverified) != ["75C37361"]:
    bad("the unverified-rotation set changed; 75C37361 is the only entry awaiting a human "
        "eye, and settling another one needs its measurement recorded, not the label")
print("rotation basis: %d applied, %d recorded, %d unverified%s"
      % (sum(1 for v in rotations.ROTATIONS.values() if v),
         len(getattr(rotations, "ROTATION_BASIS", {})), len(unverified),
         (": " + ", ".join(sorted(unverified))) if unverified else ""))

print("\nALL CHECKS PASSED" if ok else "\nFAILURES ABOVE")
sys.exit(0 if ok else 1)
