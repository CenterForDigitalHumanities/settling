"""Behavioural matrix for verify.py -- the guard that guards the guard.

verify.py asserts claims about the rotation table. Those assertions are themselves
unverified unless something tests them, and through round seven the checks that were
supposed to protect the table demonstrably did not (restoring a disproved rotation passed
clean, and check 12(d) actively HID it by moving the off-diagonal count from 2 to 1).
Every case below is a claim about behaviour; a mismatch means a check is not what its
comment says it is.

It mutates nothing in the working tree. The whole review/ subtree is copied into a temp
directory first -- verify.py resolves REPO as two levels above itself and reads the
published martha.html / martha-audit.html from it, so a bare copy of review/martha/ would
crash rather than fail -- so this is safe to run beside a dirty checkout and safe in CI.

    python check_matrix.py

Exit code is 0 only if every case behaves as expected AND none of them crashed.

Two rules learned the hard way, both encoded below:
  * Assert WHERE an edit landed. "020E073B" is the first key of both ROTATIONS and
    ROTATION_BASIS, so anchoring on it silently mutated the wrong dict and produced two
    plausible, false results.
  * Assert the mutation happened at all, and that the run did not raise. A traceback is
    not a FAIL; it is a broken harness. Check 5 accepts any multiple of 90, so the legal
    value 270 once reached a bare dict subscript and died with a KeyError and no verdict.
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))          # .../review/martha
REVIEW = os.path.dirname(HERE)                              # .../review
ROT_FILENAME = "rotations.py"

# Ashley's hand-ordered set. Only the two --source cases that need real files use these,
# and they are skipped when absent (CI, or any machine without the download).
ORDERED = r"U:\Downloads\Martha M. Hamilton Documents (ordered)\Martha M. Hamilton Documents"
# The ORIGINAL download, one directory over. Its GUID files are byte-identical to
# origin/main and landscape, so pointing --source here is the realistic operator error.
ORIGINAL = r"U:\Downloads\Martha M. Hamilton Documents"

# 04894C59 is DOC-011 p2: applied rotation -90, i.e. CSS 270.
PROBE = "04894C59"
ROT_ANCHOR = '    "5C74254C": 0,'


def set_rot(s, key, val):
    """Change an existing ROTATIONS value. Asserts the substitution landed."""
    head, sep, body = s.partition("ROTATIONS = {")
    assert sep, "ROTATIONS header not found"
    new_body, n = re.subn(r'"%s":\s*-?\d+' % key, '"%s": %s' % (key, val), body, count=1)
    assert n == 1, "rotation key %s not found inside ROTATIONS" % key
    out = head + sep + new_body
    assert '"%s": %s' % (key, val) in out.split("ROTATIONS = {")[1].split("}")[0], \
        "rotation edit landed outside ROTATIONS"
    return out


def add_rot(s, val):
    out = s.replace(ROT_ANCHOR, '    "C04781D1": %s,\n' % val + ROT_ANCHOR, 1)
    assert out != s, "rot anchor miss"
    return out


def add_basis(s, basis):
    """Insert into ROTATION_BASIS specifically -- see the module docstring."""
    head, sep, tail = s.partition("ROTATION_BASIS = {\n")
    assert sep, "ROTATION_BASIS header not found"
    out = head + sep + '    "C04781D1": %r,\n' % basis + tail
    assert '"C04781D1"' in out.split("ROTATION_BASIS = {")[1], "basis landed outside ROTATION_BASIS"
    return out


def set_basis(s, key, basis):
    head, sep, body = s.partition("ROTATION_BASIS = {")
    assert sep, "ROTATION_BASIS header not found"
    new_body, n = re.subn(r'"%s":\s*"[^"]*"' % key, '"%s": "%s"' % (key, basis), body, count=1)
    assert n == 1, "basis key %s not found inside ROTATION_BASIS" % key
    out = head + sep + new_body
    assert '"%s": "%s"' % (key, basis) in out.split("ROTATION_BASIS = {")[1], "basis edit landed wrong"
    return out


# (label, mutation, expected verdict). "ceiling" cases are EXPECTED TO PASS: they record
# what the guard cannot reject, so a future tightening has to update them deliberately
# rather than discovering the change as a surprise.
CASES = [
    ("clean", lambda s: s, "PASS"),
    # --- a basis must exist, and be a known kind ---
    ("+90, no basis", lambda s: add_rot(s, "90"), "FAIL"),
    ("+90, bare 'ocr'", lambda s: add_basis(add_rot(s, "90"), "ocr"), "FAIL"),
    ("basis, no rotation", lambda s: add_basis(s, "ocr: 1 match"), "FAIL"),
    ("bogus basis kind", lambda s: set_basis(s, "2E37B36F", "vibes: volume 529.5 at 270"), "FAIL"),
    # --- a digit is not a measurement ---
    ("digit stripped to 'ocr'", lambda s: set_basis(s, PROBE, "ocr"), "FAIL"),
    ("'ocr: 9'", lambda s: set_basis(s, PROBE, "ocr: 9"), "FAIL"),
    ("'ocr: see note 1'", lambda s: set_basis(s, PROBE, "ocr: see note 1"), "FAIL"),
    ("'ocr: settled in round 8'", lambda s: set_basis(s, PROBE, "ocr: settled in round 8"), "FAIL"),
    # --- the cited angle must be the applied rotation ---
    ("cites 90, applied -90", lambda s: set_basis(s, PROBE, "ocr: 143 matches at 90, 0 elsewhere"), "FAIL"),
    ("cites no angle at all", lambda s: set_basis(s, PROBE, "ocr: 143 matches, 0 elsewhere"), "FAIL"),
    ("cites 270, applied -90", lambda s: set_basis(s, PROBE, "ocr: 143 matches at 270, 0 elsewhere"), "PASS"),
    # --- the pinned unverified set cannot be emptied by typing a number ---
    ("75C37361 faked to ocr", lambda s: set_basis(s, "75C37361", "ocr: 40 matches at 270"), "FAIL"),
    ("75C37361 bare 'unverified'", lambda s: set_basis(s, "75C37361", "unverified"), "PASS"),
    ("all ocr downgraded", lambda s: s.replace(': "ocr', ': "unverified'), "FAIL"),
    ("+90 'unverified: trust me'", lambda s: add_basis(add_rot(s, "90"), "unverified: trust me"), "FAIL"),
    # --- angle aliasing: the table holds CSS degrees, so any spelling of the same turn
    #     is the same rotation. These are the cases that used to raise KeyError. ---
    ("rot=270, basis cites 270", lambda s: set_basis(set_rot(s, PROBE, "270"), PROBE, "ocr: 143 matches at 270"), "PASS"),
    ("rot=270, basis cites -90", lambda s: set_basis(set_rot(s, PROBE, "270"), PROBE, "ocr: 143 matches at -90"), "PASS"),
    ("rot=-270, basis cites 270", lambda s: set_basis(set_rot(s, PROBE, "-270"), PROBE, "ocr: 143 matches at 270"), "FAIL"),
    ("rot=360, basis cites 270", lambda s: set_basis(set_rot(s, PROBE, "360"), PROBE, "ocr: 143 matches at 270"), "FAIL"),
    ("rot=45, basis cites 270", lambda s: set_basis(set_rot(s, PROBE, "45"), PROBE, "ocr: 143 matches at 270"), "FAIL"),
    # --- the ceiling: specific, plausible, self-attested. Nothing rejects these. ---
    ("+90 'ocr: 999 matches at 90'", lambda s: add_basis(add_rot(s, "90"), "ocr: 999 matches at 90"), "PASS"),
    ("'ocr: 999 matches at 270'", lambda s: set_basis(s, PROBE, "ocr: 999 matches at 270"), "PASS"),
]

# (label, argv, expected rc, expected substring, needs U: drive)
ARG_CASES = [
    ("no flag", [], 0, "SKIP byte-for-byte", False),
    ("--source= correct", ["--source=" + ORDERED], 0, "verified 10 copied images", True),
    ("--source correct (space)", ["--source", ORDERED], 0, "verified 10 copied images", True),
    ("--source= wrong folder (exists)", ["--source=" + ORIGINAL], 1, "FAIL", True),
    ("--source nonexistent", ["--source=" + os.path.join(os.sep, "nope", "nothere"), ], 2, "not a directory", False),
    ("--source with no value", ["--source"], 2, "needs a path", False),
    ("typo flag", ["--src=" + ORDERED], 2, "unrecognised argument", False),
    # Explicitly empty is a documented opt-out, not a silent no-run: SKIP is printed.
    ("--source= (empty)", ["--source="], 0, "SKIP byte-for-byte", False),
]


def run(sandbox, args):
    p = subprocess.run([sys.executable, "verify.py"] + args, cwd=sandbox,
                       capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    if "Traceback" in out:
        verdict = "CRASH"
    elif "ALL CHECKS PASSED" in out:
        verdict = "PASS"
    elif "FAILURES" in out:
        verdict = "FAIL"
    else:
        verdict = "SILENT"  # neither passed, failed, nor crashed: it did not run
    return p.returncode, out, verdict


def main():
    sandbox = tempfile.mkdtemp(prefix="martha-check-matrix-")
    try:
        # REPO resolves to `sandbox`, so sandbox/review/*.html must exist for checks 10/11.
        work = os.path.join(sandbox, "review", "martha")
        shutil.copytree(REVIEW, os.path.join(sandbox, "review"),
                        ignore=shutil.ignore_patterns("__pycache__", "*.bak", ".git"))
        rot_path = os.path.join(work, ROT_FILENAME)
        with io.open(rot_path, encoding="utf-8-sig") as f:
            pristine = f.read()

        fails = 0
        print("== rotation guard matrix ==")
        for label, mutate, expect in CASES:
            text = mutate(pristine)
            if text == pristine and label != "clean":
                print("%-30s HARNESS MISS (no change made)" % label)
                fails += 1
                continue
            with io.open(rot_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            rc, out, verdict = run(work, [])
            if verdict != expect:
                fails += 1
            detail = next((ln[5:110].strip() for ln in out.splitlines() if ln.startswith("FAIL ")), "")
            if verdict == "CRASH":
                detail = next((ln.strip() for ln in out.splitlines() if ln.strip()), "")
            print("%s%-32s expect=%-5s got=%-5s %s" % (
                "MISMATCH " if verdict != expect else "ok       ", label, expect, verdict, detail))

        print("\n== argument matrix ==")
        with io.open(rot_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(pristine)
        for label, args, want_rc, want_text, needs_u in ARG_CASES:
            if needs_u and not (os.path.isdir(ORDERED) and os.path.isdir(ORIGINAL)):
                print("%-32s SKIP (needs the U: download)" % label)
                continue
            rc, out, verdict = run(work, args)
            # A run that did not compare must never claim that it did.
            false_claim = ("verified 10 copied images" in out
                           and want_text != "verified 10 copied images")
            ok = rc == want_rc and want_text in out and not false_claim
            if not ok:
                fails += 1
            print("%s%-32s rc=%s(want %s) %s%s" % (
                "ok      " if ok else "MISMATCH", label, rc, want_rc,
                "" if want_text in out else "missing %r " % want_text,
                "  FALSE CLAIM" if false_claim else ""))

        # The sandbox must be left exactly as found, or the matrix proves nothing.
        with io.open(rot_path, encoding="utf-8-sig") as f:
            assert f.read() == pristine, "sandbox rotations.py not restored"
        rc, out, verdict = run(work, [])
        print("\nsandbox clean run: %s" % verdict)
        if verdict != "PASS":
            fails += 1
        print("cases: %d rotation, %d argument -- mismatches: %d"
              % (len(CASES), len(ARG_CASES), fails))
        return 1 if fails else 0
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
