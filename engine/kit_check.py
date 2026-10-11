#!/usr/bin/env python3
"""Check the reading kit: the files an AI reads to build a case (docs/restructure-plan.md).

    python3 engine/kit_check.py            report and exit 1 on any error
    python3 engine/kit_check.py --strict   promote warnings to errors

Three checks, so that the kit stays small, true and complete as cases are added:

  1. Budget. The kit's size in tokens (bytes over four, a rough measure) must stay under
     BUDGET. A new case must not grow it: the only kit file that grows per case is the
     case index, by about one line.
  2. Cross-references. Every "section N.N" in the authoring requirements must name a
     heading that exists there. A wrong pointer sends a builder to the wrong rule.
  3. Counts. Nothing in the kit says how many packs or cases exist ("all four packs").
     Those statements go stale the day a case is added. A warning in generated files that
     carry a dated count, an error elsewhere under --strict.

  4. Generated files. docs/generated/*.md are what engine/gen_docs.py writes now, every
     field in every case file has a note in engine/field_notes.py, and every section the
     field reference points at exists. A field with no note is a field a builder cannot
     look up, which is how short_label went undocumented.

  5. Nothing per case in shared code. No file under engine/ or catalog/ holds a table keyed
     by a case prefix, or a path into a pack, except the three interview scripts that were
     frozen with the four older packs. Adding a case must touch only its own folder; this
     is the check that keeps it so.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# The kit. Order is the reading order in CLAUDE.md. Generated files are counted when present.
KIT = [
    "CLAUDE.md",
    "README.md",
    "docs/case-design-guide.md",
    "docs/case-authoring-requirements.md",
    "docs/generated/field-reference.md",
    "docs/generated/action-index.md",
    # docs/generated/diagnosis-index.md is generated for the lookup command and is not in
    # the kit: a builder needs a few diagnosis ids, found by `lookup.py diagnosis <word>`.
    # docs/generated/mechanism-index.md is a lookup (one example per mechanism), not a read.
    "docs/generated/case-index.md",
]
# The three scripts frozen with the older packs (docs/restructure-plan.md, "Frozen, and
# why") may name those packs and no other. Nothing else under engine/ or catalog/ may name
# any pack in code.
FROZEN_FILES = {
    "catalog/expand_interview_variants.py",
    "catalog/author_interview_facts.py",
    "catalog/author_interview_volunteers.py",
}
FROZEN_PACKS = {"AFRVR", "CHFE", "DIPH", "MGCA"}

# Set at the measured size plus headroom. 80,000 on 9 October 2026 (measured 79,000),
# lowered to 65,000 on 12 October after the authoring document was rewritten (measured
# 58,600). Lowered as steps land, never raised to make a check pass.
BUDGET = 65_000

COUNT_WORDS = r"(?:two|three|four|five|six|seven|eight|nine|ten|\d+)"
COUNT_PATTERNS = [
    re.compile(r"\b(?:all|the|every|these|those)\s+" + COUNT_WORDS + r"\s+(?:packs|cases)\b", re.I),
    re.compile(r"\b" + COUNT_WORDS + r"\s+(?:shipped\s+|existing\s+|current\s+)?(?:packs|cases)\b", re.I),
]
# Where count statements are checked: the kit, plus files a builder is sent to.
COUNT_FILES = [k for k in KIT if k != "docs/case-design-guide.md"] + [
    "cases/review/README.md", "engine/site-check/README.md"]
# The design guide is the owner's prose about what a case is ("two cases that follow it
# should look nothing alike"), not a statement about the library, so it is not checked.
# Lines that are allowed to mention a count: a heading of a results table, or a line that
# says the count is at a given date. Add sparingly.
COUNT_ALLOW = re.compile(r"\b(as of|on \d{1,2} \w+ 20\d\d|at the time of writing|of \d+ sampled)\b", re.I)


def tokens(path):
    return os.path.getsize(path) // 4


def headings(text):
    """Section numbers that exist: '5', '5.1', '6.0a', '14.2c'."""
    out = set()
    for m in re.finditer(r"^#{2,4}\s+(\d{1,2}(?:\.\d{1,2}[a-z]?)?)[.\s]", text, re.M):
        out.add(m.group(1))
    # Sub-sections written as a bold run-in heading: '**3.2 Patient and setting**'
    for m in re.finditer(r"^\*\*(\d{1,2}\.\d{1,2}[a-z]?)\s", text, re.M):
        out.add(m.group(1))
    return out


def references(text):
    """Section numbers the text points at, with the line they are on."""
    refs = []
    other = re.compile(r"(system design|design section|design \d|packet|review packet|spec|addendum)", re.I)
    for ln, line in enumerate(text.splitlines(), 1):
        if other.search(line):
            continue   # points into another document; not checked here
        # 'section 6.4', 'sections 7, 10 and 11', 'section 14.3, final item'
        for m in re.finditer(r"\b[Ss]ections?\s+(\d{1,2}(?:\.\d{1,2}[a-z]?)?)((?:\s*(?:,|and|or)\s*\d{1,2}(?:\.\d{1,2}[a-z]?)?)*)", line):
            refs.append((m.group(1), ln))
            for n in re.findall(r"\d{1,2}(?:\.\d{1,2}[a-z]?)?", m.group(2)):
                refs.append((n, ln))
        # '(6.4)' and '(see 11.2)': a dotted number in parentheses, not a version
        for m in re.finditer(r"\((?:see\s+)?(\d{1,2}\.\d{1,2}[a-z]?)\)", line):
            if not re.search(r"v" + re.escape(m.group(1)), line):
                refs.append((m.group(1), ln))
    return refs


def main():
    strict = "--strict" in sys.argv
    errors, warnings = [], []

    # 1. budget
    total = 0
    print(f"{'tokens':>8}  file")
    for rel in KIT:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            t = tokens(p); total += t
            print(f"{t:>8}  {rel}")
        else:
            print(f"{'absent':>8}  {rel}")
    print(f"{total:>8}  total, budget {BUDGET}")
    if total > BUDGET:
        errors.append(f"the kit is {total} tokens, over the budget of {BUDGET}")

    # 2. cross-references inside the authoring requirements, and from README and CLAUDE.md into it
    req_path = os.path.join(ROOT, "docs/case-authoring-requirements.md")
    req = open(req_path, encoding="utf-8").read()
    have = headings(req)
    for rel in ["docs/case-authoring-requirements.md", "README.md", "CLAUDE.md"]:
        p = os.path.join(ROOT, rel)
        text = open(p, encoding="utf-8").read()
        for num, ln in references(text):
            if rel != "docs/case-authoring-requirements.md":
                # only references that name the authoring document, or 'authoring N.N'
                line = text.splitlines()[ln - 1]
                if not re.search(r"authoring|requirements", line, re.I):
                    continue
            if num not in have:
                errors.append(f"{rel}:{ln}: points at section {num}, which is not a heading in the authoring requirements")

    # 2b. the generated files are current, every field has a note, and the field reference's
    #     section pointers name real headings
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(HERE, "gen_docs.py"), "--check"], capture_output=True, text=True)
    if r.returncode != 0:
        for line in r.stdout.splitlines():
            if line.startswith("ERROR"):
                errors.append("gen_docs: " + line[len("ERROR: "):])
    fr = os.path.join(ROOT, "docs/generated/field-reference.md")
    if os.path.exists(fr):
        for ln, line in enumerate(open(fr, encoding="utf-8").read().splitlines(), 1):
            m = re.match(r"\| `[^`]+` \| [^|]* \| [^|]* \| ([^|]*) \|", line)
            if m:
                sec = m.group(1).strip()
                if sec and sec not in have:
                    errors.append(f"docs/generated/field-reference.md:{ln}: section {sec} is not a heading in the authoring requirements (fix engine/field_notes.py)")

    # 3. counts
    for rel in COUNT_FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        for ln, line in enumerate(open(p, encoding="utf-8").read().splitlines(), 1):
            if COUNT_ALLOW.search(line):
                continue
            for pat in COUNT_PATTERNS:
                m = pat.search(line)
                if m:
                    warnings.append(f"{rel}:{ln}: states a count of packs or cases: {m.group(0)!r}")
                    break

    # 5. nothing per case in shared code
    sys.path.insert(0, HERE)
    from gen_docs import code_text
    from paths import list_packs
    packs = list_packs()
    for root in ["engine", "catalog"]:
        for dp, _, fs in os.walk(os.path.join(ROOT, root)):
            for f in sorted(fs):
                if not f.endswith((".py", ".js", ".mjs", ".sh")):
                    continue
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, ROOT)
                for ln, line in enumerate(code_text(p).splitlines(), 1):
                    for pk in packs:
                        pat = r"""["']%s["']\s*:|cases/%s\b|\b%s-[a-z-]+\.(?:json|md|js)\b""" % (pk, pk, pk)
                        if re.search(pat, line):
                            if rel in FROZEN_FILES and pk in FROZEN_PACKS:
                                continue
                            errors.append(f"{rel}:{ln}: names the pack {pk} in shared code (a case must touch only its own folder): {line.strip()[:80]!r}")

    if strict:
        errors += warnings; warnings = []
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("ERROR:", e)
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
