# -*- coding: utf-8 -*-
"""Post-write verification of the reorganised Martha catalog.

Usage: python verify.py [--source=<Ashley's ordered folder>]
Without --source the byte-for-byte comparison against Ashley's originals is
skipped; every other check still runs.
"""
import json, os, re, sys, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import order_table as ot

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

# 5. rotations: the 5 upright re-scans must be absent, C04781D1 must be +90
sys.path.insert(0, MAR)
from rotations import ROTATIONS
for k in ("486E2B93", "55DA5D5D", "17A709FB", "2C3188B8", "3C9351ED", "B32F08FD", "B559737D", "D33544E8", "3B9C8F5A"):
    if k in ROTATIONS:
        bad("stale rotation entry %s" % k)
if ROTATIONS.get("C04781D1") != 90:
    bad("C04781D1 rotation should be +90")
if any(v is None for v in ROTATIONS.values()):
    bad("None rotation value remains")

# 6. Ashley's 6 re-scans + 4 new scans are byte-identical to her originals
ASH = next((a[len("--source="):] for a in sys.argv if a.startswith("--source=")), None)
def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()
if not ASH or not os.path.isdir(ASH):
    print("SKIP byte-for-byte check (pass --source=<Ashley's ordered folder>)")
else:
    pairs = [("martha11-pg1.jpeg", "Arbitation Procedures pg 1.jpeg"), ("martha11-pg3.jpeg", "Arbitation Procedures pg 3.jpeg"),
             ("martha11-pg4.jpeg", "Arbitation Procedures pg 4.jpeg"), ("martha11-pg6.jpeg", "Arbitation Procedures pg 6.jpeg")]
    for pre in ("486E2B93", "55DA5D5D", "17A709FB", "2C3188B8", "3C9351ED", "C04781D1"):
        for root, dn, fn in os.walk(ASH):
            for f in fn:
                if f.upper().startswith(pre):
                    pairs.append((os.path.basename(os.path.join(root, f)), f))
    for repo_name, ash_name in pairs:
        src = os.path.join(ASH, ash_name)
        if not os.path.isfile(src):
            src = next((os.path.join(r, f) for r, _, fs in os.walk(ASH) for f in fs if f == ash_name), None)
        a, b = os.path.join(IMG, repo_name), src
        if not os.path.isfile(a):
            bad("not in repo: %s" % repo_name)
        elif md5(a) != md5(b):
            bad("bytes differ from Ashley's original: %s" % repo_name)
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

print("\nALL CHECKS PASSED" if ok else "\nFAILURES ABOVE")
sys.exit(0 if ok else 1)
