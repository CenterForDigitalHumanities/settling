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

Six rules learned the hard way, all encoded below:
  * Assert WHERE an edit landed. "020E073B" is the first key of both ROTATIONS and
    ROTATION_BASIS, so anchoring on it silently mutated the wrong dict and produced two
    plausible, false results.
  * Assert the mutation happened at all, and that the run did not raise. A traceback is
    not a FAIL; it is a broken harness. Check 5 accepts any multiple of 90, so the legal
    value 270 once reached a bare dict subscript and died with a KeyError and no verdict.
  * Assert WHICH check fired, and never let the interpreter cache a mutation. A verdict
    alone cannot tell a stale import from a real failure: CPython validates a .pyc from the
    source mtime in whole seconds plus its byte length, so two same-length mutations in the
    same second run the previous case's module. Each case therefore carries the message it
    expects, and run() sets PYTHONDONTWRITEBYTECODE.
  * An assertion is only as good as the information in what it asserts. Four cases here
    failed on one verify.py line that interpolated only the page id, so all four printed
    byte-identical text and the check was vacuous; the message now quotes the rejected
    basis. Where a case has no message to match (the PASS cases), the only defence left is
    that no stale import can happen at all.
  * Prefer an executable invariant to a warning comment. The first version of this file
     carried a "DO NOT REORDER" note whose stated REASON was wrong: it named rot=360 as the
     hazard. It is not one. Case 20's only ADJACENT equal-length neighbour is case 19, which
     expects PASS while case 20 expects FAIL, and case 21 is 10,056 so the rule cannot pair
     them either. blind_adjacent() below enforces the real rule -- ADJACENT cases, equal byte
     length, equal expected verdict -- so it cannot be misread. Adjacency is one of the three
     conditions and not shorthand for a two-clause rule: four non-adjacent pairs in this file
     do share a length and a verdict, and a guard that dropped adjacency would refuse the file
     as it stands. A revision of it also required j's want to be inside i's want and called
     that conservative. It was the reverse: see its docstring.
  * A correction is not finished until every home of the claim is corrected, including the home
    the correction points at. Rounds sixteen, seventeen and eighteen were that defect three times,
    so stale_prose() below now fails the run on a fixed list of phrasings that were true here once
    and are false now. It is a ratchet, not a proof: it can only re-block wording that has already
    been wrong, so a first-time error still needs a reader. Its scope is this module alone. The PR
    body still carries all seven phrasings, and that is deliberate: there they are a record of what
    was said and when it was found false, not a description of the present file. The rule, sharpened
    a round later than it should have been: a count in the PRESENT tense of a living artifact is
    stale by construction, because the edit that reports the staleness is itself an edit to the thing
    counted; a count pinned to a frozen revision is a fact and may be stated. So every figure here
    names its revision. In body v17 the assertion was 17 occurrences while the text held 21, and the
    sentence carrying the number sat inside the section that had just added four of them. A figure
    needs its noun and its revision before it needs its source, and a bare tuple needs the key order
    it is read in: two machines counted the seven phrases, agreed digit for digit and on the total,
    and both described the digits as being in list order when they were in table order, because a
    sum cannot see a permutation and neither side printed the phrase beside its count. A tuple's
    label must be produced by the same object that produced the tuple: one machine printed the true
    list order out of the live module and published the table order beside the same digits
    forty-three seconds later, so displaying the truth is not checking against it. Where two
    columns have a defined relationship, assert it per row -- a provenance grid that put last-true
    and first-false on the same commit twice disagreed in a way that looked like data, and a
    constant-column check cannot see that. A census of timings needs the word census, or a reader
    takes its low edge for a floor. And a figure whose subject is anything another machine can
    change needs a fetch, not a re-reading: a remote-tracking ref is an artifact with a timestamp.
    Nothing
    checks the body, so a green run is not coverage of it. The control in
    main() proves the filter can see but cannot prove the audit still runs, so a CI step outside
    this module injects a retired phrase into a copy of this file and requires the copy to refuse
    to run. What neither can see is the deletion of that step, which is what a diff is for.
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


# (label, mutation, expected verdict, required substring of the FAIL line).
#
# The fourth field exists because asserting only the verdict is not enough. A stale module
# import, or a check that fails for an unrelated reason, both print FAIL, and the exit code
# cannot tell them apart. "rot=45" is the example that is live in this file right now: it
# expects FAIL and gets FAIL, but from check 5 ("not a multiple of 90"), not from the angle
# cross-check the case is named after. The message pins WHICH guard fired. PASS cases carry
# "" because there is no failure line to match.
#
# "ceiling" cases are EXPECTED TO PASS: they record what the guard cannot reject, so a
# future tightening has to update them deliberately rather than discovering the change as a
# surprise.
#
# ORDER MATTERS, AND blind_adjacent() BELOW ENFORCES IT RATHER THAN DESCRIBING IT.
# A stale import is only possible between ADJACENT cases whose mutated rotations.py has the
# same byte length AND which expect the same verdict. That is the whole rule, and it does not
# pick the case an earlier version of this comment blamed: rot=360 (case 20) is confusable with
# nothing ADJACENT, because its only equal-length neighbour (case 19, both 10,057 bytes) expects
# PASS while it expects FAIL. Case 21 is 10,056, so the rule cannot pair it with case 20 at all.
# Adjacency is load-bearing and the file depends on it: four NON-adjacent pairs share a length and
# a verdict -- 9/20 (both FAIL at 10,057, and neither want contains the other) plus 17/19, 17/23
# and 19/23 (all PASS at 10,057) -- and a stale import cannot cross the gap between them because
# only the immediately preceding module was just written. Move case 9 beside case 20 and
# blind_adjacent() refuses the run: `MISMATCH blind adjacency rot=360, basis cites 270 -> 'ocr:
# settled in round 8' at 10057 bytes`, rc 1, zero cases executed.
#
# The rule is a guard on a guard, not a live constraint on the product, but the two guards it
# sits behind are NOT symmetric and only one of them is asserted:
#   * PYTHONDONTWRITEBYTECODE (run()) is the one that actually prevents the write. Delete it
#     and the per-case purge still leaves every verdict correct, while all 31 cases report
#     WROTE BYTECODE and the run exits 1. Loudly correct.
#   * purge_caches() (main()) is what makes the first case's cache check mean anything, since
#     without a purge the check can only ask "has a cache appeared yet". Delete it, leave the
#     env line in place, and nothing is written, nothing flags, and the run exits 0 -- so its
#     absence is invisible to every assertion in this file. The purge and the ordering guard
#     the same event from two directions -- the purge tries to make it impossible, the ordering
#     makes it loud when it happens anyway -- and only the ordering is checked.
# So: the env line is load-bearing for correctness and watched; the purge is load-bearing for
# attribution and unwatched.
#
# The ordering is the third defence, and it is not decoration. Measured on the one adjacent
# equal-length pair this file actually contains (cases 19 and 20, rot=270-cites--90 then
# rot=360, both 10,057 bytes), both defences off: the collision happens exactly when the two
# writes land in the same whole second, and all such trials ran the PREVIOUS case's module, so
# rot=360 reported PASS when it must FAIL. The biconditional has never been violated, so the
# collision rate IS the same-second rate. Three independent 24-trial batches on two machines
# measured 9, 10 and 11 of 24. Between a third and a half of attempts, governed by machine load,
# and nothing about the check itself keeps it down -- so no single figure in that range should be
# quoted as "the" rate, including the three above.
#
# No rate quoted from one box is worth anything on another, and none of them is worth anything
# without its instrument. With both defences removed, counted by parsing expect=/got= and
# cross-checked against the harness's own "WRONG GUARD" note, two back-to-back batches of 8
# replays here gave 5 and 1 wrong verdicts; the reviewing machine gave 4 and 2, and had reported
# 2 in 6 earlier. Four numbers, no two equal, always the same case: rot=360 reporting PASS when
# it must FAIL. The two counters are not one measurement read twice -- msg_ok is `want in fired`
# while ok additionally requires `verdict == expect and not wrote`, so WRONG GUARD can fire on a
# line whose verdict column is correct. Their agreeing on every replay of both batches is a
# result, not a tautology. An earlier revision of this line claimed 0 in 6 here; it does not
# reproduce, and the spread above replaces it. The reviewing machine's 2 in 6 was checked against
# its own transcript rather than against this repo, which is the only way a number attributed to
# a person can be verified: grepping an artefact cannot settle provenance. The rate is a property
# of load, not of the check, and what the ordering buys is not a low rate -- it is a loud failure
# on every occasion the rate is paid.
#
# An earlier report claimed 0 wrong verdicts in 12 runs. It lived in the PR body, not in this
# file, and it measured nothing: its counter kept lines containing both "MISMATCH" and
# "verdict=", and no line this harness prints has ever contained "verdict=" (grep the file: the
# verdict column is labelled, as `got=`, and never as `verdict=`). It returned 0 on a working sandbox and
# on a crashing one alike. That sandbox was separately broken -- REPO resolved to the wrong parent
# -- but a broken sandbox is not why the count was 0, because it would have printed 23 got=CRASH
# lines and exited 1, the loudest failure in this file, and the counter would still have seen
# none. A number is worth exactly what its filter can observe.
#
# With the shipped ordering that event is a visible verdict mismatch. Put the two PASS cases
# side by side instead, which is how this file shipped through round twelve, and it is silent.
# The reorder converts an invisible failure into a loud one; it does not prevent the stale
# import, and only the env line does that.
CASES = [
    ("clean", lambda s: s, "PASS", ""),
    # --- a basis must exist, and be a known kind ---
    ("+90, no basis", lambda s: add_rot(s, "90"), "FAIL",
     "applies +90 but ROTATION_BASIS records no reason"),
     ("+90, bare 'ocr'", lambda s: add_basis(add_rot(s, "90"), "ocr"), "FAIL",
      "C04781D1 claims an OCR basis but records no measurement: 'ocr'."),
    ("basis, no rotation", lambda s: add_basis(s, "ocr: 1 match"), "FAIL",
     "records a basis for a rotation that is not applied"),
    ("bogus basis kind", lambda s: set_basis(s, "2E37B36F", "vibes: volume 529.5 at 270"), "FAIL",
     "has unrecognised basis"),
    # --- a digit is not a measurement ---
    # Each of these four mutates the SAME page, so before verify.py quoted the rejected
    # basis back they printed byte-identical FAIL lines and the assertion below could not
    # tell one from another. The want strings now name the page and the value, which is what
    # makes a stale import on these cases visible.
    ("digit stripped to 'ocr'", lambda s: set_basis(s, PROBE, "ocr"), "FAIL",
     "04894C59 claims an OCR basis but records no measurement: 'ocr'."),
    ("'ocr: 9'", lambda s: set_basis(s, PROBE, "ocr: 9"), "FAIL",
     "04894C59 claims an OCR basis but records no measurement: 'ocr: 9'"),
    ("'ocr: see note 1'", lambda s: set_basis(s, PROBE, "ocr: see note 1"), "FAIL",
     "04894C59 claims an OCR basis but records no measurement: 'ocr: see note 1'"),
    ("'ocr: settled in round 8'", lambda s: set_basis(s, PROBE, "ocr: settled in round 8"), "FAIL",
     "04894C59 claims an OCR basis but records no measurement: 'ocr: settled in round 8'"),
    # --- the cited angle must be the applied rotation ---
    ("cites 90, applied -90", lambda s: set_basis(s, PROBE, "ocr: 143 matches at 90, 0 elsewhere"),
     "FAIL", "cites angle(s) [90] but the applied rotation is -90"),
    ("cites no angle at all", lambda s: set_basis(s, PROBE, "ocr: 143 matches, 0 elsewhere"),
     "FAIL", "cites angle(s) none"),
    ("cites 270, applied -90", lambda s: set_basis(s, PROBE, "ocr: 143 matches at 270, 0 elsewhere"),
     "PASS", ""),
    # --- the pinned unverified set cannot be emptied by typing a number ---
    # These three fail on one message, so verify.py prints the set it found as well as the
    # one it expected; without that the three want strings could not be told apart.
    ("75C37361 faked to ocr", lambda s: set_basis(s, "75C37361", "ocr: 40 matches at 270"), "FAIL",
     "expected ['75C37361'], found []"),
    ("75C37361 bare 'unverified'", lambda s: set_basis(s, "75C37361", "unverified"), "PASS", ""),
    ("all ocr downgraded", lambda s: s.replace(': "ocr', ': "unverified'), "FAIL",
     "found ['020E073B', '04894C59'"),
    ("+90 'unverified: trust me'", lambda s: add_basis(add_rot(s, "90"), "unverified: trust me"),
     "FAIL", "found ['75C37361', 'C04781D1']"),
    # --- angle aliasing: the table holds CSS degrees, so any spelling of the same turn
    #     is the same rotation. These are the cases that used to raise KeyError.
    #     The FAIL case sits between the two PASS cases on purpose: cases 17, 19 and 23 are the
    #     three PASS cases at 10,057 bytes (there are seven PASS cases in all, at five distinct
    #     lengths), and blind_adjacent() refuses the run whenever any two equal-length
    #     same-verdict cases are placed side by side. ---
    ("rot=270, basis cites 270",
     lambda s: set_basis(set_rot(s, PROBE, "270"), PROBE, "ocr: 143 matches at 270"), "PASS", ""),
    ("rot=-270, basis cites 270",
     lambda s: set_basis(set_rot(s, PROBE, "-270"), PROBE, "ocr: 143 matches at 270"), "FAIL",
     "applied rotation is -270, which is CSS -270 / 90"),
    ("rot=270, basis cites -90",
     lambda s: set_basis(set_rot(s, PROBE, "270"), PROBE, "ocr: 143 matches at -90"), "PASS", ""),
    ("rot=360, basis cites 270",
     lambda s: set_basis(set_rot(s, PROBE, "360"), PROBE, "ocr: 143 matches at 270"), "FAIL",
     "applied rotation is +360, which is CSS 0 / 360"),
    # Reaching the cross-check with an illegal angle is impossible: check 5 rejects 45
    # first. Labelled for what it actually asserts.
    ("rot=45 (check 5, not the cross-check)",
     lambda s: set_basis(set_rot(s, PROBE, "45"), PROBE, "ocr: 143 matches at 270"), "FAIL",
     "is 45, not a multiple of 90"),
    # --- the ceiling: specific, plausible, self-attested. Nothing rejects these. ---
    ("+90 'ocr: 999 matches at 90'", lambda s: add_basis(add_rot(s, "90"), "ocr: 999 matches at 90"),
     "PASS", ""),
    ("'ocr: 999 matches at 270'", lambda s: set_basis(s, PROBE, "ocr: 999 matches at 270"),
     "PASS", ""),
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
    # PYTHONDONTWRITEBYTECODE is load-bearing, not hygiene. CPython validates a .pyc from
    # the source's mtime truncated to WHOLE SECONDS plus its byte length. Two adjacent
    # mutations of identical length inside the same second therefore make the second case
    # import the first case's module. Cases 19 and 20 (rot=270-cites--90 then rot=360, both
    # 10,057 bytes) are exactly that pair; the two rot=270 cases are NOT, since case 18 sits
    # between them. A full run makes 32 verify.py invocations (23 rotation cases, 8 argument cases,
    # one final clean run). Fifteen timed runs in five batches on two machines through `df3a18c`
    # span 20.2-23.1s, so every one of them is under a second per invocation at either divisor,
    # 31 cases or 32 invocations. That bound is the load-bearing fact and the only timing claim
    # made here. The span above is a CENSUS of those fifteen runs, not a range of what the harness
    # does, and it is already known to under-describe it: at `16bcc31` a third machine produced
    # 15.29-15.66s, 4.6-4.9s below the lower edge, and a later batch on the census machine itself
    # produced 23.53-25.69s, which is entirely above the upper edge. All eight runs still clear the
    # bound. A span quoted without that warning reads as a floor, which is the opposite of a bound.
    # Unpinned ranges rot in place for the same reason -- the batch that widened the upper bound ran
    # on the machine that had earlier reported 0.4% spread, and per-batch spread across the five is
    # 0.4%, 2.3%, 4.0%, 10.6% and 1.4%. Which end of a census one run lands on is variance, not
    # evidence about the machine, so the census is kept only for the spreads.
    # Two writes therefore share a whole second on a
    # substantial minority of attempts --
    # measured, not assumed -- which is far too often to rely on. A stale PASS where PASS is
    # expected is invisible in the output; a stale FAIL
    # prints the PREVIOUS case's message and looks like the right guard fired. Writing no
    # bytecode removes the whole class.
    p = subprocess.run([sys.executable, "verify.py"] + args, cwd=sandbox,
                       capture_output=True, text=True,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
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


def caches_in(work):
    """Any __pycache__ under the sandbox. Non-empty means bytecode reached the disk."""
    return [os.path.join(dp, dn) for dp, dns, _ in os.walk(work) for dn in dns
            if dn == "__pycache__"]


def purge_caches(work):
    """Delete any __pycache__ under the sandbox and report how many directories went."""
    found = caches_in(work)
    for d in found:
        shutil.rmtree(d, ignore_errors=True)
    return len(found)


def blind_adjacent(pristine):
    """Adjacent cases between which a stale import is physically possible. Computed, not
    described in prose -- an earlier version of this comment described it and got the danger
    wrong, naming a case that is confusable with nothing adjacent.

    Two more facts decide it, given adjacency, without running anything:

      * the mutated rotations.py must be the same number of bytes, or CPython rewrites the
        .pyc rather than reusing it (mtime alone is not enough -- it is truncated to whole
        seconds and a full run makes 32 verify.py invocations, each under a second -- timed in
        run());
      * the expected verdicts must agree, since a PASS run never satisfies a FAIL case.

    Nothing else may be required, and an earlier revision also required j's want to be
    contained in i's want. That test was backwards. The loop in main() asserts
    `want in fired` for every FAIL case, so i's want is BY CONSTRUCTION a substring of i's
    output; if wj is in wi then wj is in fired_i, which is precisely the condition under which
    a stale import on j reports ok. Extra text in i's message therefore cannot rescue a pair
    the substring test let through -- it could only ever hide blindness, never invent it.
    Measured on the shipped file, and on a copy with two injected equal-length FAIL
    mutations whose wants are unrelated: the old predicate flags 0 and 0, the new one flags 0
    and 1. The substring test cost nothing today and hid a real case later.

    Neither surviving clause is redundant, and they fail at different edges. Drop the
    byte-length test and 12 adjacent pairs are flagged: the eleven FAIL/FAIL adjacencies
    2/3 3/4 4/5 5/6 6/7 7/8 8/9 9/10 10/11 15/16 20/21, plus the ceiling PASS pair 22/23.
    Drop the verdict test and exactly 1 is: 19/20, both 10,057 bytes, one PASS and one FAIL.
    """
    blind = []
    for (li, mi, ei, wi), (lj, mj, ej, wj) in zip(CASES, CASES[1:]):
        ni, nj = len(mi(pristine).encode("utf-8")), len(mj(pristine).encode("utf-8"))
        if ni == nj and ei == ej:
            blind.append((li, lj, nj))
    return blind


# Prose that was true somewhere in this file's history and is false now. Rounds sixteen, seventeen
# and eighteen were the same defect three times -- a correction reached some copies of a claim and
# not the copy the corrected copy points at -- and grep finds every home at review time but none of
# them at the next rewrite. This list is the only version of that check which survives the rewrite.
# Entries are underscore-encoded so that the list cannot match itself.
RETIRED_PROSE = [
    "nothing_more",                               # bullet 5, dropped in ab8e7aa
    "Two_facts_decide",                           # blind_adjacent, dropped in round 18
    "never_labelled",                             # the column prints `got=`
    "0_wrong_verdicts_in_6_replays",              # measured 5 and 1 here, 4 and 2 there
    "equal-length_neighbours_expect_PASS",        # case 20 has ONE equal-length neighbour
    "is_confusable_with_nothing.",                # adjacency is a condition, not shorthand
    "differs_from_every_equal-length_neighbour",  # true once, replaced by a false paraphrase
]


def stale_prose(own):
    """[(entry, line)] for every retired phrasing still present in this module's own text.

    A guard on the guards: it audits the descriptions, which nothing else does. It reads this
    file rather than rotations.py, so it is independent of the sandbox and of every mutation
    below, and it runs before either exists.
    """
    hits = []
    for entry in RETIRED_PROSE:
        phrase = entry.replace("_", " ")
        for i, line in enumerate(own.splitlines(), 1):
            if phrase in line:
                hits.append((entry, i))
    return hits


def main():
    # The ratchet has to be able to fail, so it gets the same treatment as the other two defences:
    # make it blind and check that something shouts. An emptied RETIRED_PROSE and a broken decode
    # both leave stale_prose() returning [] for any input at all, which is a green run built on a
    # filter that cannot see -- the dead filter this list exists to stop, arriving inside the
    # stopper. The probe is built FROM the list rather than written as a literal, because a file
    # containing any retired phrase in order to test the guard would trip the guard on itself --
    # which is exactly what the first version of this comment did.
    if not RETIRED_PROSE:
        print("MISMATCH retired-prose ratchet is empty: nothing is being guarded")
        return 1
    probe = "\n".join(entry.replace("_", " ") for entry in RETIRED_PROSE)
    invisible = set(RETIRED_PROSE) - set(entry for entry, _ in stale_prose(probe))
    if invisible:
        print("MISMATCH stale_prose is a dead filter: %d of %d entries invisible: %s"
              % (len(invisible), len(RETIRED_PROSE), ", ".join(sorted(invisible))))
        return 1

    # Fail before a sandbox exists. A stale description of a guard is the defect this file exists
    # to prevent, and every verdict printed below would be read under it.
    own_path = globals().get("__file__")
    if not own_path:
        print("MISMATCH cannot audit prose: __file__ is unset")
        return 1
    with io.open(own_path, encoding="utf-8-sig") as f:
        retired = stale_prose(f.read())
    if retired:
        for entry, ln in retired:
            print("MISMATCH retired prose at L%d: %s" % (ln, entry))
        print("cases: %d rotation, %d argument -- mismatches: %d"
              % (len(CASES), len(ARG_CASES), len(retired)))
        return 1

    sandbox = tempfile.mkdtemp(prefix="martha-check-matrix-")
    try:
        # REPO resolves to `sandbox`, so sandbox/review/*.html must exist for checks 10/11.
        work = os.path.join(sandbox, "review", "martha")
        shutil.copytree(REVIEW, os.path.join(sandbox, "review"),
                        ignore=shutil.ignore_patterns("__pycache__", "*.bak", ".git"))
        rot_path = os.path.join(work, ROT_FILENAME)
        with io.open(rot_path, encoding="utf-8-sig") as f:
            pristine = f.read()

        for label, _m, expect, want in CASES:
            assert expect != "FAIL" or want, "FAIL case %r has no message to assert" % label

        # The ordering rule, enforced. If a reorder makes two adjacent cases indistinguishable
        # then a stale import between them is invisible, so stop rather than print verdicts
        # that cannot be attributed.
        blind = blind_adjacent(pristine)
        if blind:
            for li, lj, n in blind:
                print("MISMATCH blind adjacency %s -> %s at %d bytes" % (li, lj, n))
            print("cases: %d rotation, %d argument -- mismatches: %d"
                  % (len(CASES), len(ARG_CASES), len(blind)))
            return 1

        fails = 0
        print("== rotation guard matrix ==")
        for label, mutate, expect, want in CASES:
            text = mutate(pristine)
            if text == pristine and label != "clean":
                print("%-30s HARNESS MISS (no change made)" % label)
                fails += 1
                continue
            with io.open(rot_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            with io.open(rot_path, encoding="utf-8") as f:
                assert f.read() == text, "mutation did not land: %s" % label
            # Purge BEFORE the run, not only check after. Clearing whatever the previous case
            # left means this case cannot import a stale module, so a cache found afterwards is
            # unambiguously this case's own write. Checking only afterwards asked "has a cache
            # appeared yet", which is why the first case was once reported as stale.
            purge_caches(work)
            rc, out, verdict = run(work, [])
            wrote = caches_in(work)
            # Match the whole line, not the printed excerpt, so truncation cannot invent a
            # mismatch.
            fired = next((ln[5:].strip() for ln in out.splitlines() if ln.startswith("FAIL ")), "")
            msg_ok = (not want) or (want in fired)
            ok = (verdict == expect) and msg_ok and not wrote
            if not ok:
                fails += 1
            # Report every diagnosis. Folding them into one variable hid WRONG GUARD behind
            # the cache note, so the specific failure disappeared exactly when the mechanism
            # was broken -- the same silence this whole file is about.
            notes = []
            if not msg_ok:
                notes.append("WRONG GUARD (want %r)" % want)
            if wrote:
                notes.append("WROTE BYTECODE (%s)"
                             % ", ".join(os.path.relpath(c, work) for c in wrote))
            shown = fired if verdict != "CRASH" else next(
                (ln.strip() for ln in out.splitlines() if ln.strip()), "")
            print("%s%-40s expect=%-5s got=%-5s %s%s" % (
                "MISMATCH " if not ok else "ok       ", label, expect, verdict,
                "; ".join(notes) + (" " if notes else ""), shown[:110]))


        print("\n== argument matrix ==")
        with io.open(rot_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(pristine)
        for label, args, want_rc, want_text, needs_u in ARG_CASES:
            if needs_u and not (os.path.isdir(ORDERED) and os.path.isdir(ORIGINAL)):
                print("%-32s SKIP (needs the U: download)" % label)
                continue
            purge_caches(work)
            rc, out, verdict = run(work, args)
            wrote = caches_in(work)
            # A run that did not compare must never claim that it did.
            false_claim = ("verified 10 copied images" in out
                           and want_text != "verified 10 copied images")
            ok = rc == want_rc and want_text in out and not false_claim and not wrote
            if not ok:
                fails += 1
            flags = ""
            if false_claim:
                flags += "  FALSE CLAIM"
            if wrote:
                flags += "  WROTE BYTECODE"
            print("%s%-32s rc=%s(want %s) %s%s" % (
                "ok      " if ok else "MISMATCH", label, rc, want_rc,
                "" if want_text in out else "missing %r " % want_text, flags))

        # The sandbox must be left exactly as found, or the matrix proves nothing.
        with io.open(rot_path, encoding="utf-8-sig") as f:
            assert f.read() == pristine, "sandbox rotations.py not restored"
        purge_caches(work)
        rc, out, clean = run(work, [])
        print("\nsandbox clean run: %s" % clean)
        if clean != "PASS":
            fails += 1

        # Aggregate belt, deliberately last and after a purge, so anything it finds was written
        # by the run above. Bytecode on disk means PYTHONDONTWRITEBYTECODE was not inherited:
        # the per-case purge would hide that from the matrix by deleting the evidence, so this
        # is the check on the mechanism rather than on a verdict.
        caches = caches_in(work)
        if caches:
            fails += 1
            print("MISMATCH bytecode written (%s): PYTHONDONTWRITEBYTECODE not inherited"
                  % ", ".join(os.path.relpath(c, work) for c in caches))
        print("cases: %d rotation, %d argument -- mismatches: %d"
              % (len(CASES), len(ARG_CASES), fails))
        return 1 if fails else 0
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
