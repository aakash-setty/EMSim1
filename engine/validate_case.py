#!/usr/bin/env python3
"""
Validator and review-matrix generator for the EM case simulator.

Implements the structural checks listed in section 14.1 of
case-authoring-requirements.md and section 13 of system-design-v2.md,
plus the per-key review matrix described in section 14.2.

Case-agnostic: contains no clinical knowledge and no case names.
"""
import json
import re, itertools, sys, os
from collections import defaultdict

# --------------------------------------------------------------------------
# Condition language: five predicates, AND / OR / NOT, one level of grouping
# --------------------------------------------------------------------------

class ParseError(Exception):
    pass


class Atom:
    def __init__(self, kind, ident):
        self.kind, self.ident = kind, ident       # kind in phase/flag/ordered/resulted/action

    def key(self):
        return (self.kind, self.ident)

    def __repr__(self):
        return f"{self.kind}:{self.ident}"


class Not:
    def __init__(self, x): self.x = x


class BinOp:
    def __init__(self, op, l, r): self.op, self.l, self.r = op, l, r


def tokenize(s):
    out, buf = [], ""
    for ch in s:
        if ch in "()":
            if buf.strip():
                out.extend(buf.split())
            buf = ""
            out.append(ch)
        else:
            buf += ch
    if buf.strip():
        out.extend(buf.split())
    return out


class Parser:
    def __init__(self, tokens):
        self.t, self.i, self.max_depth, self.depth = tokens, 0, 0, 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def eat(self, expect=None):
        tok = self.peek()
        if tok is None:
            raise ParseError("unexpected end of condition")
        if expect and tok != expect:
            raise ParseError(f"expected {expect!r}, found {tok!r}")
        self.i += 1
        return tok

    def parse(self):
        node = self.expr()
        if self.i != len(self.t):
            raise ParseError(f"trailing tokens: {self.t[self.i:]}")
        return node

    def expr(self):
        node = self.term()
        while self.peek() == "OR":
            self.eat()
            node = BinOp("OR", node, self.term())
        return node

    def term(self):
        node = self.factor()
        while self.peek() == "AND":
            self.eat()
            node = BinOp("AND", node, self.factor())
        return node

    def factor(self):
        tok = self.peek()
        if tok == "NOT":
            self.eat()
            return Not(self.factor())
        if tok == "(":
            self.eat("(")
            self.depth += 1
            self.max_depth = max(self.max_depth, self.depth)
            node = self.expr()
            self.depth -= 1
            self.eat(")")
            return node
        return self.predicate()

    def predicate(self):
        tok = self.eat()
        if tok == "phase":
            self.eat("is")
            return Atom("phase", self.eat())
        if tok == "flag":
            ident = self.eat()
            self.eat("set")
            return Atom("flag", ident)
        if tok == "study":
            ident = self.eat()
            kw = self.eat()
            if kw not in ("ordered", "resulted"):
                raise ParseError(f"study predicate must be ordered/resulted, found {kw!r}")
            return Atom(kw, ident)
        if tok == "action":
            ident = self.eat()
            self.eat("taken")
            return Atom("action", ident)
        raise ParseError(f"unrecognised predicate opener {tok!r} "
                         f"(permitted: phase / flag / study / action)")


def parse_condition(s):
    p = Parser(tokenize(s))
    node = p.parse()
    return node, p.max_depth


def atoms_of(node, acc=None):
    acc = [] if acc is None else acc
    if isinstance(node, Atom):
        acc.append(node)
    elif isinstance(node, Not):
        atoms_of(node.x, acc)
    elif isinstance(node, BinOp):
        atoms_of(node.l, acc); atoms_of(node.r, acc)
    return acc


def evaluate(node, assign):
    """assign: dict mapping ('phase', id)/('flag', id)/('ordered', id)/... -> bool"""
    if isinstance(node, Atom):
        return assign.get(node.key(), False)
    if isinstance(node, Not):
        return not evaluate(node.x, assign)
    if node.op == "AND":
        return evaluate(node.l, assign) and evaluate(node.r, assign)
    return evaluate(node.l, assign) or evaluate(node.r, assign)


# --------------------------------------------------------------------------
# Load and merge
# --------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))


sys.path.insert(0, HERE)
from paths import resolve_pack, catalog_path

PACK = resolve_pack(sys.argv)


def _load(path):
    if path and os.path.exists(path):
        with open(path) as f:
            return json.load(f), path
    return None, None


def load_catalog():
    return _load(catalog_path("action-catalog.json"))


def load_binding():
    return _load(PACK.binding)


def build_case():
    with open(PACK.case) as f:
        return json.load(f)


# --------------------------------------------------------------------------
# Collect every rule list in the case, uniformly
# --------------------------------------------------------------------------

def collect_rule_lists(case):
    """Returns list of (key_path, rules, requires_unconditional_default)."""
    out = []

    for a in case["case_actions"]:
        out.append((f"action_tag/{a['catalog_id']}", a["tag"], True))

    ck = case["content_keys"]
    for k, rules in ck["exam"].items():
        if k == "authoring_note":
            continue
        out.append((f"exam/{k}", rules, True))
    if "general_status" in ck:
        out.append(("general_status", ck["general_status"]["rules"], True))
    for group in ("labs", "imaging"):
        for k, v in ck[group].items():
            if k == "authoring_note":
                continue
            out.append((f"{group}/{k}", v["rules"], True))
    for k, rules in ck["consultants"].items():
        if k == "authoring_note":
            continue
        out.append((f"consultant/{k}", rules, True))

    iv = case["interview"]
    out.append(("interview/out_of_scope_fallback", iv["out_of_scope_fallback"], True))
    for t in iv["topics"]:
        out.append((f"interview_topic/{t['topic']}", t["answer"], True))
    # global answer rules are prepended to every topic and are guards, not a key
    out.append(("interview/global_answer_rules", iv["global_answer_rules"], False))

    return out


def collect_all_conditions(case):
    """Returns list of (location, condition_string)."""
    conds = []
    for path, rules, _ in collect_rule_lists(case):
        for i, r in enumerate(rules):
            if r.get("when"):
                conds.append((f"{path}[{i}]", r["when"]))

    for ph in case["phases"]:
        for i, t in enumerate(ph.get("transitions", [])):
            if t.get("when"):
                conds.append((f"transition/{ph['id']}[{i}]", t["when"]))

    for a in case["case_actions"]:
        for i, p in enumerate(a.get("prerequisites", []) or []):
            if p.get("when"):
                conds.append((f"prereq/{a['catalog_id']}[{i}]", p["when"]))
        pr = a.get("prompt")
        if pr and pr.get("guard"):
            conds.append((f"prompt_guard/{a['catalog_id']}", pr["guard"]))

    for f in case["follow_ups"]:
        if f.get("applies_when"):
            conds.append((f"followup/{f['id']}", f["applies_when"]))

    return conds


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def run_checks(case):
    errors, warnings, notes = [], [], []

    phase_ids = {p["id"] for p in case["phases"]}
    action_ids = {a["catalog_id"] for a in case["case_actions"]}
    settable_flags = set()
    timed_flags = {}          # flag -> [(action id, duration)], grants that lapse
    perm_flags = set()        # flags some action grants for good
    for a in case["case_actions"]:
        settable_flags.update(a.get("flags_set", []) or [])
        perm_flags.update(a.get("flags_set", []) or [])
        for tf in (a.get("flags_set_timed") or []):
            f = tf.get("flag")
            if isinstance(f, str) and f:
                settable_flags.add(f)
                timed_flags.setdefault(f, []).append((a["catalog_id"], tf.get("duration_seconds")))

    ck = case["content_keys"]
    study_ids = set()
    for group in ("labs", "imaging"):
        study_ids.update(k for k in ck[group] if k != "authoring_note")
    study_ids.add("ecg_12_lead")

    # -- L: predicate whitelist + parse + nesting depth ---------------------
    parsed = {}
    for loc, cond in collect_all_conditions(case):
        try:
            node, depth = parse_condition(cond)
            parsed[loc] = node
            if depth > 1:
                errors.append(f"[nesting] {loc}: grouping depth {depth} exceeds the one level permitted")
        except ParseError as e:
            errors.append(f"[condition] {loc}: {e}  ->  {cond!r}")
            continue

        # -- B: referenced ids exist
        for at in atoms_of(node):
            if at.kind == "phase" and at.ident not in phase_ids:
                errors.append(f"[ref] {loc}: unknown phase {at.ident!r}")
            elif at.kind == "flag" and at.ident not in settable_flags:
                errors.append(f"[ref] {loc}: flag {at.ident!r} is not set by any action in this case")
            elif at.kind in ("ordered", "resulted") and at.ident not in study_ids:
                errors.append(f"[ref] {loc}: unknown study {at.ident!r}")
            elif at.kind == "action" and at.ident not in action_ids:
                errors.append(f"[ref] {loc}: unknown action {at.ident!r}")

    # -- A: unconditional default last -------------------------------------
    for path, rules, needs_default in collect_rule_lists(case):
        if not rules:
            errors.append(f"[default] {path}: empty rule list")
            continue
        if needs_default and rules[-1].get("when") is not None:
            errors.append(f"[default] {path}: last rule is guarded; every content key must end "
                          f"in an unconditional default")
        for i, r in enumerate(rules[:-1]):
            if r.get("when") is None:
                errors.append(f"[default] {path}[{i}]: unconditional rule before the end shadows "
                              f"every rule after it")

    # -- C/D: phase reachability and satisfiable transitions ----------------
    start = case["phases"][0]["id"]
    reach, frontier = {start}, [start]
    by_id = {p["id"]: p for p in case["phases"]}
    while frontier:
        cur = frontier.pop()
        for t in by_id[cur].get("transitions", []):
            if t["to"] not in reach:
                if t["to"] not in phase_ids:
                    errors.append(f"[ref] transition/{cur}: unknown destination {t['to']!r}")
                    continue
                reach.add(t["to"]); frontier.append(t["to"])

    harm_capable = any(
        any(r.get("value") == "harmful" for r in a["tag"]) for a in case["case_actions"]
    )
    if harm_capable:
        reach.add("halted")   # entered outside the transition graph, per section 5

    for p in case["phases"]:
        if p["id"] not in reach:
            errors.append(f"[reach] phase {p['id']!r} is unreachable")
        if not p.get("terminal") and not p.get("transitions"):
            errors.append(f"[reach] non-terminal phase {p['id']!r} has no transition")

    # -- E: every critical action reachable --------------------------------
    for a in case["case_actions"]:
        crit_phases = []
        for r in a["tag"]:
            if r.get("value") != "critical":
                continue
            if r.get("when") is None:
                crit_phases.append(None)
            else:
                crit_phases.extend(at.ident for at in atoms_of(parse_condition(r["when"])[0])
                                   if at.kind == "phase")
        for cp in crit_phases:
            if cp is not None and cp not in reach:
                errors.append(f"[reach] {a['catalog_id']} is critical in unreachable phase {cp!r}")


    # -- T: time-guarded transitions (design 2.1a, authoring 5.1) -----------
    # Six rules. Each is a lesson from a way a deterioration on a clock can become a
    # trap rather than a lesson, so the reasoning is in the message, not only the rule.
    FLOOR_ERROR, FLOOR_WARN, PROMPT_LEAD = 30, 60, 20

    def guard_flags(tr):
        """Flags the guard requires to be UNSET for this transition to fire."""
        out = set()
        w = tr.get("when") or ""
        try:
            node, _ = parse_condition(w)
        except ParseError:
            return out
        for at in atoms_of(node):
            if at.kind == "flag":
                out.add(at.ident)
        return out if "NOT" in w.upper() else set()

    def prompts_in_phase(phase):
        """(action id, flags it sets, first deadline) for prompts that can fire here."""
        out = []
        for a in case["case_actions"]:
            pr = a.get("prompt")
            if not pr:
                continue
            assign = {("phase", phase): True}
            tag = None
            for r in a["tag"]:
                if r.get("when") is None or evaluate(parse_condition(r["when"])[0], assign):
                    tag = r["value"]
                    break
            if tag != "critical":
                continue
            if pr.get("guard") and not evaluate(parse_condition(pr["guard"])[0], assign):
                continue
            sets = set(a.get("flags_set") or [])
            sets.update(tf["flag"] for tf in (a.get("flags_set_timed") or [])
                        if isinstance(tf.get("flag"), str))
            out.append((a["catalog_id"], sets, pr["deadline_seconds"],
                        (pr.get("escalation") or {}).get("deadline_seconds", pr["deadline_seconds"])))
        return out

    time_edges = []
    for ph in case["phases"]:
        timed = [t for t in ph.get("transitions", []) if "after_seconds" in t]
        for i, tr in enumerate(ph.get("transitions", [])):
            if "after_seconds" not in tr:
                continue
            loc = f"{ph['id']}/transitions[{i}]"
            n = tr["after_seconds"]

            if not isinstance(n, int) or n < FLOOR_ERROR:
                errors.append(f"[time] {loc}: after_seconds {n!r} is below the {FLOOR_ERROR}s "
                              f"floor. A deterioration the resident could not plausibly have "
                              f"prevented tests reflexes, not medicine")
            elif n < FLOOR_WARN:
                warnings.append(f"[time] {loc}: after_seconds {n} is under {FLOOR_WARN}s")

            mf = tr.get("measured_from", "phase_entry")
            if mf not in ("phase_entry", "guard_true"):
                errors.append(f"[time] {loc}: measured_from {mf!r} is not phase_entry or guard_true")
            if mf == "guard_true" and tr.get("when") is None:
                errors.append(f"[time] {loc}: measured_from guard_true requires a guard")

            for f in ("narration", "debrief_note", "author_rationale"):
                if not tr.get(f):
                    errors.append(f"[time] {loc}: missing {f}")

            if tr.get("when") is None and not tr.get("unguarded_rationale"):
                errors.append(f"[time] {loc}: a transition nothing can prevent is a scripted "
                              f"trajectory and needs an unguarded_rationale")

            dest = next((x for x in case["phases"] if x["id"] == tr["to"]), None)
            if dest is None:
                continue
            if dest.get("terminal"):
                if not tr.get("allow_time_to_terminal"):
                    errors.append(f"[time] {loc}: ends the case on the clock without "
                                  f"allow_time_to_terminal. Ending a case because nothing was "
                                  f"done is the strongest statement this system makes and must "
                                  f"never happen because a phase id was reused")
                elif not tr.get("terminal_opt_in_rationale"):
                    errors.append(f"[time] {loc}: allow_time_to_terminal without a rationale")
                if tr["to"] == "halted":
                    errors.append(f"[time] {loc}: a time-driven ending must not reuse the shared "
                                  f"halted phase, which carries a harmful action's halt reason. "
                                  f"Attributing an omission to a commission teaches the learner "
                                  f"something false about their own run")
            elif not dest.get("transitions"):
                errors.append(f"[time] {loc}: destination {tr['to']!r} has no exit")

            gf = guard_flags(tr)
            for f in gf:
                if f not in settable_flags:
                    errors.append(f"[time] {loc}: guard names flag {f!r}, which no action sets")
                    continue
                helpers = [x for x in prompts_in_phase(ph["id"])
                           if f in x[1] and x[2] <= n - PROMPT_LEAD]
                if not helpers:
                    any_p = [x for x in prompts_in_phase(ph["id"]) if f in x[1]]
                    if any_p:
                        errors.append(f"[time] {loc}: fires at {n}s on flag {f!r}, but the only "
                                      f"prompt that sets it is at {min(x[2] for x in any_p)}s, "
                                      f"less than {PROMPT_LEAD}s of lead")
                    else:
                        errors.append(f"[time] {loc}: fires at {n}s on flag {f!r} and no action "
                                      f"prompting in this phase sets it. A deterioration nobody "
                                      f"was warned about is a trap rather than a lesson")
            time_edges.append((ph["id"], tr["to"]))

        # Only a deadline measured from PHASE ENTRY can strand a prompt, because prompt
        # deadlines are measured from phase entry too. A guard_true rule's clock starts
        # when its guard first holds, which is usually later and may never happen, so
        # comparing a prompt's deadline against it warns about prompts that fire
        # perfectly well. A validator that cries wolf trains authors to skim it.
        entry_timed = [t for t in timed if (t.get("measured_from") or "phase_entry") == "phase_entry"]
        if entry_timed:
            earliest = min(t["after_seconds"] for t in entry_timed)
            for aid, _flags, first, last in prompts_in_phase(ph["id"]):
                if first >= earliest:
                    warnings.append(f"[time] {aid} prompts at {first}s in {ph['id']!r}, which has "
                                    f"a time-guarded exit at {earliest}s, so it can never fire")
                elif last >= earliest:
                    warnings.append(f"[time] {aid} escalates at {last}s in {ph['id']!r}, which "
                                    f"has a time-guarded exit at {earliest}s")

    adj = {}
    for a, b in time_edges:
        adj.setdefault(a, set()).add(b)
    seen, stack = set(), []

    def _cycle(node):
        if node in stack:
            errors.append("[time] cycle composed only of time edges: "
                          + " -> ".join(stack[stack.index(node):] + [node])
                          + ". A loop with no resident involvement is a case that plays itself")
            return
        if node in seen:
            return
        seen.add(node); stack.append(node)
        for nxt in adj.get(node, ()):
            _cycle(nxt)
        stack.pop()

    for node in list(adj):
        _cycle(node)

    # -- F: harmful tags carry a halt reason
    for a in case["case_actions"]:
        if any(r.get("value") == "harmful" for r in a["tag"]) and not a.get("halt_reason"):
            errors.append(f"[halt] {a['catalog_id']}: tag can evaluate to harmful but no halt_reason")
        if a.get("halt_reason") and not any(r.get("value") == "harmful" for r in a["tag"]):
            warnings.append(f"[halt] {a['catalog_id']}: has a halt_reason but tag never evaluates harmful")

    # -- G: prerequisites --------------------------------------------------
    setters = defaultdict(set)
    for a in case["case_actions"]:
        for fl in a.get("flags_set", []) or []:
            setters[fl].add(a["catalog_id"])

    dep = defaultdict(set)
    for a in case["case_actions"]:
        for i, p in enumerate(a.get("prerequisites", []) or []):
            if not p.get("failure_message"):
                errors.append(f"[prereq] {a['catalog_id']}[{i}]: no failure message")
            if not p.get("when"):
                errors.append(f"[prereq] {a['catalog_id']}[{i}]: no condition")
                continue
            node, _ = parse_condition(p["when"])
            for at in atoms_of(node):
                if at.kind == "flag":
                    if not setters[at.ident]:
                        errors.append(f"[prereq] {a['catalog_id']}: required flag {at.ident!r} "
                                      f"is not settable by any action")
                    dep[a["catalog_id"]].update(setters[at.ident])

    # cycle detection over the prerequisite dependency graph
    WHITE, GREY, BLACK = 0, 1, 2
    colour = defaultdict(int)

    def visit(n, stack):
        colour[n] = GREY
        for m in dep.get(n, ()):
            if colour[m] == GREY:
                errors.append(f"[prereq] circular prerequisite chain: {' -> '.join(stack + [m])}")
            elif colour[m] == WHITE:
                visit(m, stack + [m])
        colour[n] = BLACK

    for n in list(dep):
        if colour[n] == WHITE:
            visit(n, [n])

    # -- H: follow-ups complete --------------------------------------------
    for f in case["follow_ups"]:
        for field in ("applies_when", "deadline_seconds", "nurse_prompt", "debrief_note"):
            if not f.get(field):
                errors.append(f"[followup] {f['id']}: missing {field}")
        trig = f["triggered_by"]
        for t in ([trig] if isinstance(trig, str) else trig):
            if t not in action_ids:
                errors.append(f"[followup] {f['id']}: triggered_by unknown action {t!r}")
        for s in f.get("satisfied_by", []):
            if s not in action_ids:
                errors.append(f"[followup] {f['id']}: satisfied_by unknown action {s!r}")

    # -- I: time-sensitive critical actions have deadline and prompt text ---
    for a in case["case_actions"]:
        pr = a.get("prompt")
        if not pr:
            continue
        if not pr.get("deadline_seconds"):
            errors.append(f"[prompt] {a['catalog_id']}: prompt with no deadline")
        if not pr.get("text"):
            errors.append(f"[prompt] {a['catalog_id']}: deadline with no prompt text")
        esc = pr.get("escalation")
        if esc and (not esc.get("deadline_seconds") or not esc.get("text")):
            errors.append(f"[prompt] {a['catalog_id']}: incomplete escalation")
        if esc and esc.get("deadline_seconds", 0) <= pr.get("deadline_seconds", 0):
            errors.append(f"[prompt] {a['catalog_id']}: escalation deadline not after first deadline")

    # -- K: debrief notes ---------------------------------------------------
    for a in case["case_actions"]:
        if not a.get("debrief_note"):
            warnings.append(f"[debrief] {a['catalog_id']}: no debrief note (will inherit the generic one)")

    # -- J: vitals plausibility (catches transcription slips) ---------------
    RANGES = {"heart_rate": (20, 220), "systolic_bp": (40, 260), "diastolic_bp": (20, 160),
              "respiratory_rate": (4, 60), "oxygen_saturation": (50, 100), "temperature_c": (28.0, 43.0)}
    for p in case["phases"]:
        v = p["vitals"]
        # A terminal phase may legitimately record arrest: zero is a real value there,
        # not a transcription slip.
        arrest_ok = bool(p.get("terminal"))
        for k, (lo, hi) in RANGES.items():
            if k not in v or v[k] is None:
                errors.append(f"[vitals] {p['id']}: {k} not authored")
            elif not isinstance(v[k], (int, float)):
                errors.append(f"[vitals] {p['id']}: {k} is {v[k]!r}, not a number")
            elif arrest_ok and v[k] == 0 and k != "temperature_c":
                pass
            elif not (lo <= v[k] <= hi):
                errors.append(f"[vitals] {p['id']}: {k}={v[k]} outside plausible range {lo}-{hi}")
        sbp, dbp = v.get("systolic_bp"), v.get("diastolic_bp")
        if (isinstance(sbp, (int, float)) and isinstance(dbp, (int, float))
                and sbp <= dbp and not (arrest_ok and sbp == 0)):
            errors.append(f"[vitals] {p['id']}: systolic not above diastolic")
        ap = p["appearance"]
        for lvl in ("distress_level", "alertness_level"):
            val = ap.get(lvl)
            if val is None:
                errors.append(f"[vitals] {p['id']}: {lvl} not authored")
            elif not (isinstance(val, int) and 0 <= val <= 3):
                errors.append(f"[vitals] {p['id']}: {lvl} is {val!r}, expected 0 to 3")
        if ap.get("pupil_size") not in ("small", "normal", "large"):
            errors.append(f"[vitals] {p['id']}: bad pupil_size")
        if ap.get("pupil_reactivity") not in ("reactive", "sluggish", "fixed"):
            errors.append(f"[vitals] {p['id']}: bad pupil_reactivity")

    # -- V: vital effects (design 2.3, authoring 5.2) -----------------------
    # Six rules, and the reason for each is that the mechanism is easy to author into
    # a trap. An effect is invisible in the review matrix, which enumerates what a key
    # resolves to in a phase and knows nothing about the clock, so anything the matrix
    # cannot show has to be caught here or it is not caught at all.
    VITAL_KEYS = set(RANGES)
    fx_keys = {}
    windows = []
    for a in case["case_actions"]:
        for i, fx in enumerate(a.get("vital_effects") or []):
            loc = f"[vital_effect] {a['catalog_id']}[{i}]"
            if fx.get("vital") not in VITAL_KEYS:
                errors.append(f"{loc}: vital {fx.get('vital')!r} is not one of {sorted(VITAL_KEYS)}")
            if not isinstance(fx.get("delta"), (int, float)) or isinstance(fx.get("delta"), bool):
                errors.append(f"{loc}: delta is {fx.get('delta')!r}, not a number")
            elif fx["delta"] == 0:
                warnings.append(f"{loc}: delta is 0, so the effect does nothing")
            ons = fx.get("onset_seconds")
            if ons is not None and (not isinstance(ons, (int, float)) or isinstance(ons, bool)
                                    or ons < 0):
                errors.append(f"{loc}: onset_seconds is {ons!r}, expected a number of seconds "
                              f"at or above zero")
                ons = None
            dur = fx.get("duration_seconds")
            if dur is not None and (not isinstance(dur, (int, float)) or isinstance(dur, bool)
                                    or dur <= 0):
                errors.append(f"{loc}: duration_seconds is {dur!r}, expected a positive number")
                dur = None
            # Both windows are measured from the administration, so a duration that does
            # not outlast its onset is an effect that never acts. This is the mistake the
            # single-origin rule makes possible, so it is checked rather than explained.
            if ons is not None and dur is not None and dur <= ons:
                errors.append(f"{loc}: duration_seconds {dur} does not outlast onset_seconds "
                              f"{ons}; both are measured from the administration, so this "
                              f"effect would never act")
            elif ons is not None or dur is not None:
                windows.append(f"{a['catalog_id']}/{fx.get('vital')} acts "
                               f"{ons or 0}s to {dur if dur is not None else 'the end'}s "
                               f"after each administration")
            if fx.get("while"):
                try:
                    parse_condition(fx["while"])
                except Exception as e:
                    errors.append(f"{loc}: unparseable while condition: {e}")
            # Two actions sharing a key do not stack, which is the point of a key, but
            # two actions sharing a key on DIFFERENT vitals silently discard one of them.
            key = fx.get("key") or a["catalog_id"]
            prev = fx_keys.get(key)
            if prev and prev != fx.get("vital"):
                errors.append(f"{loc}: key {key!r} is already used for vital {prev!r}")
            fx_keys[key] = fx.get("vital")
        # An effect on an action that is not state-changing never fires: the fold
        # returns before it records one.
        if a.get("vital_effects") and a.get("state_changing") is False:
            errors.append(f"[vital_effect] {a['catalog_id']}: state_changing is false, "
                          f"so the effect can never be recorded")
    if windows:
        notes.append("vital effect windows: " + "; ".join(windows))

    # -- W: expiring flags (design 2.7, authoring 6.3) ----------------------
    # A flag that lapses is the only way a case can react to something wearing off, so
    # the failure modes are all silent: the flag is never read, or it can never expire
    # because something else grants it for good, or it expires and nothing is authored
    # to notice. The first two are checkable and are checked here.
    cond_flags = set()
    tag_flags = set()
    for _loc, _cond in collect_all_conditions(case):
        try:
            _node, _ = parse_condition(_cond)
        except ParseError:
            continue
        here = {at.ident for at in atoms_of(_node) if at.kind == "flag"}
        cond_flags.update(here)
        if _loc.startswith("action_tag/"):
            tag_flags.update(here)

    for a in case["case_actions"]:
        own_perm = set(a.get("flags_set") or [])
        for i, tf in enumerate(a.get("flags_set_timed") or []):
            loc = f"[timed_flag] {a['catalog_id']}[{i}]"
            f = tf.get("flag")
            if not isinstance(f, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", f or ""):
                errors.append(f"{loc}: flag {f!r} is not a bare identifier; the condition "
                              f"grammar splits on whitespace and could not name it")
                continue
            d = tf.get("duration_seconds")
            if not isinstance(d, (int, float)) or isinstance(d, bool) or d <= 0:
                errors.append(f"{loc}: duration_seconds is {d!r}, expected a positive number")
            if f in own_perm:
                errors.append(f"{loc}: {f!r} is also in this action's flags_set, which grants "
                              f"it permanently; a permanent grant absorbs a timed one, so the "
                              f"duration would never take effect")
            if a.get("state_changing") is False:
                errors.append(f"{loc}: state_changing is false, so the flag is never granted")
            if f not in cond_flags:
                warnings.append(f"{loc}: nothing in this case reads flag {f!r}. A flag that "
                                f"expires and that no transition, tag, prompt guard, "
                                f"prerequisite or content rule tests changes nothing at all")
    # The critical-action expectation is computed once, on entry to a phase, from the tag
    # each action resolves to at that instant. A tag that reads a flag which later
    # EXPIRES therefore flips without the expectation flipping with it: the action can
    # become critical in the middle of a phase and never appear in the debrief's missed
    # list. Permanent flags have a milder version of this and always have, but they only
    # ever move one way, so a timed flag is where it actually bites.
    for f in sorted(timed_flags):
        if f in tag_flags:
            warnings.append(f"[timed_flag] a clinical tag reads {f!r}, which expires. Tags are "
                            f"re-resolved whenever an action is taken, but the set of CRITICAL "
                            f"actions a phase expects is fixed on entry to that phase, so an "
                            f"action that becomes critical because this flag lapsed will not be "
                            f"listed as missed. Put the consequence on a transition instead")

    for f, grants in timed_flags.items():
        if f in perm_flags:
            other = [a["catalog_id"] for a in case["case_actions"] if f in (a.get("flags_set") or [])]
            warnings.append(f"[timed_flag] {f!r} is granted with a duration by "
                            f"{', '.join(g[0] for g in grants)} and permanently by "
                            f"{', '.join(other)}. Once the permanent grant is taken the flag "
                            f"stops expiring, and nothing on screen says so")
    if timed_flags:
        notes.append("expiring flags: " + "; ".join(
            f"{f} ({', '.join(str(g[1]) + 's from ' + g[0] for g in gs)})"
            for f, gs in sorted(timed_flags.items())))

    # An effect whose baseline plus delta leaves the plausible range in some phase is
    # almost always a phase that was never rebased when the effect was added.
    #
    # This is checked only for UNGUARDED effects. A `while` condition can make a phase
    # unreachable for the effect -- CHFE's nitrate effect is guarded on NOT intubated
    # and so cannot reach either ventilator phase -- and deciding that statically means
    # deciding reachability, which this validator does not do anywhere else either.
    # Guarded effects are reported as a note saying the check was not made, rather than
    # as a warning that is wrong most of the time. A rule that cries wolf gets ignored,
    # and this one exists to catch exactly the mistake an author makes once.
    unchecked = []
    for a in case["case_actions"]:
        for fx in (a.get("vital_effects") or []):
            k = fx.get("vital")
            if k not in VITAL_KEYS or not isinstance(fx.get("delta"), (int, float)):
                continue
            if fx.get("while"):
                unchecked.append(f"{a['catalog_id']}/{k}")
                continue
            lo, hi = RANGES[k]
            for ph in case["phases"]:
                if ph.get("terminal"):
                    continue          # terminal phases are exempt from effects
                base = ph["vitals"].get(k)
                if isinstance(base, (int, float)) and not (lo <= base + fx["delta"] <= hi):
                    warnings.append(
                        f"[vital_effect] {a['catalog_id']}: {k} {base}{fx['delta']:+g} in phase "
                        f"{ph['id']} leaves the plausible range {lo}-{hi}; the effect is "
                        f"clamped, so the phase baseline is probably not the unsupported one")
    if unchecked:
        notes.append(f"vital effects with a while guard, range not checked against every "
                     f"phase: {', '.join(sorted(set(unchecked)))}")

    # -- N: result payload shape (action catalog default_result_contract) ---
    def check_payload(where, v):
        if isinstance(v, str):
            errors.append(f"{where}: result is a prose string; authored results must be "
                          f"structured payloads (kind/components/abnormal)")
            return
        if not isinstance(v, dict) or "kind" not in v:
            errors.append(f"{where}: result payload has no kind")
            return
        if "abnormal" not in v:
            errors.append(f"{where}: result payload omits abnormal "
                          f"(catalog rule: ERROR when an authored result overrides a default "
                          f"but omits abnormal)")
        if v["kind"] in ("panel", "value"):
            comps = v.get("components")
            if not comps:
                errors.append(f"{where}: {v['kind']} payload has no components")
                return
            for c in comps:
                for field in ("label", "value", "reference_range"):
                    if field not in c:
                        errors.append(f"{where}: component {c.get('label','?')} missing {field}")
                if "abnormal" not in c:
                    errors.append(f"{where}: component {c.get('label','?')} omits abnormal")
            if v.get("abnormal") != any(c.get("abnormal") for c in comps):
                errors.append(f"{where}: payload-level abnormal disagrees with its components")
        elif v["kind"] == "report":
            if not v.get("report"):
                errors.append(f"{where}: report payload has no report text")
        else:
            errors.append(f"{where}: unknown payload kind {v['kind']!r}")

    for group in ("labs", "imaging"):
        for k, block in case["content_keys"][group].items():
            if k == "authoring_note":
                continue
            for i, r in enumerate(block["rules"]):
                check_payload(f"{group}/{k}[{i}]", r["value"])

    def check_finding(where, v, want_kind):
        if isinstance(v, str):
            errors.append(f"{where}: finding is a prose string; it must be a "
                          f"{want_kind} payload with an abnormal flag")
            return
        if not isinstance(v, dict) or v.get("kind") != want_kind:
            errors.append(f"{where}: expected kind {want_kind}, found {v.get('kind') if isinstance(v, dict) else type(v).__name__}")
            return
        if "abnormal" not in v:
            errors.append(f"{where}: omits abnormal")
        if not v.get("findings"):
            errors.append(f"{where}: has no findings text")

    for k, rules in case["content_keys"]["exam"].items():
        if k == "authoring_note":
            continue
        for i, r in enumerate(rules):
            check_finding(f"exam/{k}[{i}]", r["value"], "exam_findings")

    gs = case["content_keys"].get("general_status")
    if not gs:
        errors.append("no general_status content key; the catalog renders a general status line "
                      "above the exam list and it needs a case rule list or it falls to the default")
    else:
        for i, r in enumerate(gs["rules"]):
            check_finding(f"general_status[{i}]", r["value"], "general_status")

    # numeric plausibility of the abnormal flags. The renderer must not recompute,
    # but the validator can, and a mis-set flag is invisible everywhere else.
    def numeric(x):
        try:
            return float(str(x).replace(",", ""))
        except ValueError:
            return None

    def parse_range(txt):
        t = str(txt).split(";")[0].strip()
        m = re.match(r"^(-?[\d.]+)\s*(?:-|to)\s*(-?[\d.]+)", t)
        if m:
            return float(m.group(1)), float(m.group(2))
        m = re.match(r"^(?:under|below|less than|<)\s*(-?[\d.]+)", t, re.I)
        if m:
            return None, float(m.group(1))
        m = re.match(r"^(?:over|above|greater than|>)\s*(-?[\d.]+)", t, re.I)
        if m:
            return float(m.group(1)), None
        return None, None

    flag_mismatch = 0
    for group in ("labs",):
        for k, block in case["content_keys"][group].items():
            if k == "authoring_note":
                continue
            for i, r in enumerate(block["rules"]):
                v = r["value"]
                if not isinstance(v, dict):
                    continue
                for c in v.get("components", []):
                    n = numeric(c.get("value"))
                    lo, hi = parse_range(c.get("reference_range", ""))
                    if n is None or (lo is None and hi is None):
                        continue
                    out_of_range = (lo is not None and n < lo) or (hi is not None and n > hi)
                    if out_of_range != bool(c.get("abnormal")):
                        flag_mismatch += 1
                        warnings.append(
                            f"{group}/{k}[{i}] {c['label']}: value {c['value']} against range "
                            f"'{c['reference_range']}' but abnormal={c.get('abnormal')}. "
                            f"Check the flag or the range.")
    if not flag_mismatch:
        notes.append("abnormal flags agree with every parseable reference range")

    # -- O: action catalog binding ------------------------------------------
    catalog, cat_path = load_catalog()
    binding, bind_path = load_binding()
    if catalog is None:
        warnings.append("action-catalog.json not found; catalog checks skipped")
    elif binding is None:
        warnings.append("case-catalog-binding.json not found; binding checks skipped")
    else:
        E = {x["id"]: x for x in catalog["entries"]}
        rows = {r["case_id"]: r for r in binding["rows"]}
        unmatched, blocking = [], []
        for a in case["case_actions"]:
            cid = a["catalog_id"]
            row = rows.get(cid)
            if row is None:
                errors.append(f"action {cid} has no row in the catalog binding")
                continue
            if row["status"] == "unmatched":
                unmatched.append(cid)
                if (row.get("note") or "").startswith("BLOCKING"):
                    blocking.append(cid)
                continue
            if row["catalog_id"] not in E:
                errors.append(f"binding for {cid} points at {row['catalog_id']}, "
                              f"which is not in the catalog")
        for cid in blocking:
            errors.append(f"action {cid} has no catalog entry and the case cannot run without it: "
                          f"{rows[cid]['note']}")
        soft = [c for c in unmatched if c not in blocking]
        if soft:
            warnings.append(f"{len(soft)} case actions have no catalog entry and are playable only "
                            f"because the prototype renders unbound actions: {', '.join(sorted(soft))}")
        notes.append(f"catalog binding: {binding['counts']} against catalog "
                     f"{catalog['catalog_version']}")

        # duplicate targets: two case actions bound to one catalog entry
        seen = {}
        for cid, row in rows.items():
            t = row["catalog_id"]
            if t:
                seen.setdefault(t, []).append(cid)
        for t, cids in seen.items():
            if len(cids) > 1:
                warnings.append(f"catalog entry {t} is bound by {len(cids)} case actions "
                                f"({', '.join(cids)}); the interface offers one button for "
                                f"actions the case scores differently")

        # catalog rule: a study named in a transition or tagged critical but not authored
        authored = set()
        for group in ("labs", "imaging"):
            authored |= {k for k in case["content_keys"][group] if k != "authoring_note"}
        named = set()
        for _loc, cstr in collect_all_conditions(case):
            try:
                atoms = atoms_of(parse_condition(cstr)[0])
            except Exception:
                continue          # already reported by the grammar check above
            for at in atoms:
                if at.kind in ("ordered", "resulted"):
                    named.add(at.ident)
        for a in case["case_actions"]:
            if any(r.get("value") == "critical" for r in a["tag"]):
                if a["catalog_id"] in {x["id"] for x in catalog["entries"]
                                       if x["category"] == "investigation"} or \
                   a["catalog_id"].startswith(("labs_", "cxr", "ecg", "ct_", "echo", "pocus")):
                    named.add(a["catalog_id"])
        for s in sorted(named - authored):
            row = rows.get(s)
            target = row["catalog_id"] if row else None
            has_default = bool(target and E.get(target, {}).get("default_result"))
            warnings.append(
                f"study {s} is named in a condition or tagged critical but the case authors no "
                f"result for it; it will "
                + (f"silently return the catalog default for {target}"
                   if has_default else "return nothing"))

    # -- P0: every catalog condition must parse in the section 4 grammar -----
    if catalog:
        badconds = {}
        for x in catalog["entries"]:
            for p in x.get("default_prerequisites") or []:
                try:
                    parse_condition(p["when"])
                except Exception as exc:
                    badconds.setdefault(p["when"], [str(exc), []])[1].append(x["id"])
        for cstr, (msg, who) in badconds.items():
            errors.append(f"catalog prerequisite {cstr!r} does not parse in the section 4 grammar "
                          f"({msg}); used by {len(who)} entries including {who[0]}")

    # -- P1: exam set is closed, and every exam carries a default ------------
    if catalog:
        cat_exams = {x["id"] for x in catalog["entries"] if x["category"] == "exam"}
        case_exams = {k for k in case["content_keys"]["exam"] if k != "authoring_note"}
        stray = sorted(case_exams - cat_exams)
        if stray:
            errors.append(f"case authors exam findings for manoeuvres that do not exist in the "
                          f"catalog: {stray}. The catalog states the 14 exam entries are the "
                          f"complete set, so these findings are unreachable.")
        no_default = sorted(x["id"] for x in catalog["entries"]
                            if x["category"] == "exam" and not x.get("default_result"))
        if no_default:
            errors.append(f"catalog exams with no default_result: {no_default}; a manoeuvre the "
                          f"case does not author would return nothing")
        if not stray and not no_default:
            notes.append(f"exam set closed: {len(case_exams)} of {len(cat_exams)} manoeuvres "
                         f"authored, the rest inherit catalog defaults")
        if "general_status_default" not in catalog:
            warnings.append("catalog has no general_status_default; the line above the exam list "
                            "has no fallback")

    # -- P: catalog default coverage ----------------------------------------
    if catalog:
        missing = [x["id"] for x in catalog["entries"]
                   if x["category"] == "investigation" and not x.get("default_result")]
        if missing:
            errors.append(f"catalog investigations with no default_result: {missing}")
        else:
            notes.append(f"catalog: all "
                         f"{sum(1 for x in catalog['entries'] if x['category']=='investigation')} "
                         f"investigations carry a default_result")

    # -- M: interview coverage ---------------------------------------------
    iv = case["interview"]
    for t in iv["topics"]:
        n = len(t.get("variants", []))
        if n < 10:
            warnings.append(f"[interview] {t['topic']}: {n} paraphrase variants, section 10.1 asks for 10-20")
    neg = [t["topic"] for t in iv["topics"] if t.get("pertinent_negative")]
    notes.append(f"pertinent negatives authored as explicit denials: {len(neg)} ({', '.join(neg)})")
    notes.append(f"interview topics: {len(iv['topics'])}; total paraphrase variants: "
                 f"{sum(len(t['variants']) for t in iv['topics'])}")

    # -- alertness gating coverage -----------------------------------------
    gated = set()
    for r in iv["global_answer_rules"]:
        node, _ = parse_condition(r["when"])
        gated.update(at.ident for at in atoms_of(node) if at.kind == "phase")
    for p in case["phases"]:
        al = p["appearance"].get("alertness_level")
        if isinstance(al, int) and al >= 2 and not p.get("terminal") and p["id"] not in gated:
            errors.append(f"[interview] phase {p['id']!r} has alertness "
                          f"{p['appearance']['alertness_level']} but is not covered by a global answer rule")

    # -- N: arrival and the two-sentence handover (section 3.2) -------------
    # The handover is the only history the learner is given without asking for it,
    # so its length is a clinical constraint rather than a style preference. The
    # Patient tab used to print the whole background; it is gone, and everything
    # not in these two sentences now has to be elicited.
    ar = (case.get("metadata") or {}).get("arrival") or {}
    mode = str(ar.get("mode", "")).lower()
    if mode not in ("ems", "triage"):
        if any(k in mode for k in ("ambulance", "walk", "transfer", "police")):
            warnings.append(f"[arrival] mode {ar.get('mode')!r} uses the pre-0.5 vocabulary; "
                            f"use 'ems' or 'triage'. The reader normalises it, but new cases "
                            f"should author the new values")
        else:
            errors.append("[arrival] metadata.arrival.mode must be 'ems' or 'triage'; it selects "
                          "the heading above the handover")

    loc = ar.get("location")
    if loc not in ("resuscitation_bay", "trauma_bay", "patient_room"):
        errors.append("[arrival] metadata.arrival.location must be one of resuscitation_bay, "
                      "trauma_bay, patient_room; without it the splash screen shows no arrival line")

    h = (case.get("patient") or {}).get("arrival_handover")
    if not h or str(h).startswith("TODO"):
        errors.append("[arrival] patient.arrival_handover is required; it is the only history "
                      "the learner is given without asking")
    else:
        h = str(h).strip()
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", h) if s.strip()]
        if len(sentences) > 2:
            errors.append(f"[arrival] arrival_handover is {len(sentences)} sentences; "
                          f"section 3.2 allows two")
        if len(h.split()) > 45:
            warnings.append(f"[arrival] arrival_handover is {len(h.split())} words; two sentences "
                            f"of handover is usually under 40")
        # Until v0.7 this warned about any vital sign in the handover, on the grounds
        # that the monitor carried the same numbers and would contradict them within a
        # minute. That reason stopped being true when the monitor was gated on being
        # attached: a handover is now the ONLY place a resident gets a number before
        # they have put equipment on the patient, and a crew reporting what they
        # measured is what a handover is. So the blanket warning is a note.
        #
        # What is still worth catching is the contradiction the old rule was really
        # aiming at: a saturation quoted in the handover that disagrees with the one the
        # case starts from. That is checkable, and it is a genuine authoring slip.
        quoted = re.findall(r"(\d{2,3})\s*(?:%|percent)", h, re.I)
        if quoted or re.search(r"\bsats?\b", h, re.I):
            notes.append("arrival_handover quotes vital signs. Since the monitor is dark until "
                         "it is attached this is often the right call, but write them as what "
                         "was measured on the way in, not as a live reading: nothing updates them")
        start_spo2 = (case["phases"][0].get("vitals") or {}).get("oxygen_saturation")
        if quoted and isinstance(start_spo2, (int, float)):
            if not any(int(q) == int(start_spo2) for q in quoted):
                warnings.append(f"[arrival] arrival_handover quotes {', '.join(quoted)} percent "
                                f"but the case starts at {start_spo2}. A resident who attaches a "
                                f"monitor will read a number the handover just contradicted")
        notes.append(f"arrival: {mode or 'unset'} to {loc or 'unset'}; handover "
                     f"{len(sentences)} sentence(s), {len(h.split())} words")

    return errors, warnings, notes


# --------------------------------------------------------------------------
# Per-key review matrix (section 14.2)
# --------------------------------------------------------------------------

# Declared mutually exclusive / impossible combinations, labelled not trusted.
def implausible(assign_desc):
    flags = assign_desc["flags"]
    if flags.get("nitro_stopped") and not flags.get("nitro_infusion_running"):
        return "nitro_stopped without an infusion running"
    if flags.get("post_intubation_sedation") and not flags.get("intubated"):
        return "post-intubation sedation without intubation"
    return None


MAX_ROWS = 96


def payload_summary(v):
    """One-line rendering of a structured result payload for the review matrix."""
    if v.get("kind") in ("exam_findings", "general_status"):
        txt = v.get("findings", "")
        return ("ABNORMAL: " if v.get("abnormal") else "normal: ") + \
               (txt[:70] + ("..." if len(txt) > 70 else ""))
    if v.get("kind") == "report":
        txt = v.get("report", "")
        return ("ABNORMAL: " if v.get("abnormal") else "normal: ") + \
               (txt[:70] + ("..." if len(txt) > 70 else ""))
    bits = []
    for c in v.get("components", []):
        b = f"{c['label']} {c['value']}{(' ' + c['unit']) if c.get('unit') else ''}"
        if c.get("abnormal"):
            b = "**" + b + "**"
        bits.append(b)
    return "; ".join(bits)


def build_matrix(case):
    lines = []
    for path, rules, needs_default in collect_rule_lists(case):
        atoms = []
        for r in rules:
            if r.get("when"):
                atoms.extend(atoms_of(parse_condition(r["when"])[0]))
        phases = sorted({a.ident for a in atoms if a.kind == "phase"})
        flags = sorted({a.ident for a in atoms if a.kind == "flag"})
        studies = sorted({a.ident for a in atoms if a.kind in ("ordered", "resulted")})
        acts = sorted({a.ident for a in atoms if a.kind == "action"})

        lines.append(f"\n### `{path}`\n")
        if not (phases or flags or studies or acts):
            lines.append("Single unconditional rule; nothing to enumerate.\n")
            continue

        phase_space = (phases + ["«any other phase»"]) if phases else ["«any phase»"]
        combos = list(itertools.product(
            phase_space,
            *[[False, True] for _ in flags],
            *[["not_ordered", "pending", "resulted"] for _ in studies],
            *[[False, True] for _ in acts]))

        if len(combos) > MAX_ROWS:
            lines.append(f"_{len(combos)} combinations, exceeds the {MAX_ROWS}-row display cap. "
                         f"Axes: phases={phase_space}, flags={flags}, studies={studies}, actions={acts}._\n")
            combos = combos[:MAX_ROWS]

        header = (["phase"] + flags + studies + acts + ["resolves to", "reachable?"])
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "---|" * len(header))

        for c in combos:
            i = 0
            ph = c[i]; i += 1
            fl = {}
            for f in flags:
                fl[f] = c[i]; i += 1
            st = {}
            for s in studies:
                st[s] = c[i]; i += 1
            ac = {}
            for a in acts:
                ac[a] = c[i]; i += 1

            assign = {}
            for p in phases:
                assign[("phase", p)] = (p == ph)
            for f, v in fl.items():
                assign[("flag", f)] = v
            for s, v in st.items():
                assign[("ordered", s)] = v in ("pending", "resulted")
                assign[("resulted", s)] = v == "resulted"
            for a, v in ac.items():
                assign[("action", a)] = v

            hit = None
            for idx, r in enumerate(rules):
                if r.get("when") is None:
                    hit = (idx, "default"); break
                if evaluate(parse_condition(r["when"])[0], assign):
                    hit = (idx, r["when"]); break
            resolved = f"rule {hit[0]} ({hit[1]})" if hit else "**NO RULE MATCHES**"
            if hit is not None:
                rv = rules[hit[0]].get("value")
                if isinstance(rv, dict):
                    resolved += " &rarr; " + payload_summary(rv)

            why = implausible({"flags": fl})
            row = ([ph] + ["yes" if fl[f] else "no" for f in flags]
                   + [st[s] for s in studies]
                   + ["yes" if ac[a] else "no" for a in acts]
                   + [resolved, ("not reachable: " + why) if why else "plausible"])
            lines.append("| " + " | ".join(str(x) for x in row) + " |")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------

def main():
    case = build_case()
    errors, warnings, notes = run_checks(case)

    print("=" * 70)
    print("VALIDATOR (section 14.1 / system design section 13)")
    print("=" * 70)
    for n in notes:
        print(f"  note:    {n}")
    for w in warnings:
        print(f"  WARNING: {w}")
    for e in errors:
        print(f"  ERROR:   {e}")
    print(f"\n  {len(errors)} errors, {len(warnings)} warnings")

    matrix = ("# Per-key review matrix\n\n"
              f"Generated by `engine/validate_case.py` from `{os.path.basename(PACK.case)}`, "
              "per section 14.2 of the authoring requirements.\n\n"
              "For each key this enumerates every combination of the flags, studies, phases and "
              "actions appearing in **that key's own rule list**, and shows which rule the key "
              "resolves to. Study predicates take three values. Combinations that cannot occur in "
              "a real run are labelled rather than filtered.\n\n"
              "This is the artifact the reviewing physician reads. The failure it is designed to "
              "surface is a missing rule falling through to a default that is clinically wrong in "
              "that situation, which raises no error anywhere else.\n\n"
              "For lab, imaging and exam keys the resolved payload is shown inline. **Bold** "
              "components are the ones the author flagged abnormal, which are the ones the "
              "interface renders in red. A component that reads abnormal to you but is not bold "
              "is a display defect that no other check will catch.\n"
              + build_matrix(case))
    with open(PACK.matrix, "w") as f:
        f.write(matrix)

    print(f"  wrote {os.path.basename(PACK.matrix)} to {PACK.dir}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
