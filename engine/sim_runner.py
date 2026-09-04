#!/usr/bin/env python3
"""Scenario runner. Case-agnostic.

Walks a case through the paths listed in its pack's `<PREFIX>-scenarios.json` to
confirm the phase machine, prerequisites and halting behave as authored. This is a
sanity check on the case file, not an implementation of the engine.

    python3 engine/sim_runner.py [cases/CHFE]

A step is an action id, or {"wait": 120} to advance the case clock, which is how a
scenario exercises a time-guarded transition (design 2.1a).
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_case import parse_condition, evaluate, atoms_of
from paths import resolve_pack

PACK = resolve_pack(sys.argv)
case = json.load(open(PACK.case))
ACTIONS = {a["catalog_id"]: a for a in case["case_actions"]}

# also_covers: one case action claiming several catalog entries so its tag, halt reason
# and note apply to every route to the same act. The engine resolves this in
# buildActions; without it here a scenario step naming a covered sibling looked like an
# unknown action, which meant equivalence-group coverage could not be tested at all.
COVERS = {}
try:
    _binding = json.load(open(PACK.binding))
    for _r in _binding.get("rows", []):
        for _extra in (_r.get("also_covers") or []):
            COVERS[_extra] = _r["case_id"]
except (OSError, ValueError):
    pass
PHASES = {p["id"]: p for p in case["phases"]}
START = case["phases"][0]["id"]


class Run:
    def __init__(self):
        self.phase, self.flags, self.taken = START, set(), set()
        self.ordered, self.resulted, self.log = set(), set(), []
        # v0.6. The clock only matters to time-guarded transitions, so it advances by a
        # nominal cost per action and by explicit waits in the scenario.
        self.t, self.entry_t, self.guard_true = 0, 0, {}
        # v0.9. Administrations per counter, for flags a case grants only on the Nth dose.
        self.admin = {}

    def assign(self):
        d = {}
        for p in PHASES:
            d[("phase", p)] = (p == self.phase)
        for f in self.flags:
            d[("flag", f)] = True
        for s in self.ordered:
            d[("ordered", s)] = True
        for s in self.resulted:
            d[("resulted", s)] = True
        for a in self.taken:
            d[("action", a)] = True
        return d

    def tag_of(self, aid):
        for r in ACTIONS[aid]["tag"]:
            if r.get("when") is None or evaluate(parse_condition(r["when"])[0], self.assign()):
                return r["value"]
        return "neutral"

    def do(self, aid):
        aid = COVERS.get(aid, aid)        # a covered sibling acts as its covering action
        self.t += 8                       # nominal cost of an action on the case clock
        if PHASES[self.phase].get("terminal"):
            self.log.append(f"  {aid} not applied: the case has ended")
            return "over"
        if aid not in ACTIONS:
            # A step naming an action the case does not hold is silently discarded by
            # the engine: not applied, not blocked, not logged. That is how a shadowed
            # action sat in a scenario file passing for the wrong reason.
            self.log.append(f"  UNKNOWN ACTION {aid}: not in this case")
            return "unknown"
        act = ACTIONS[aid]
        for p in act.get("prerequisites") or []:
            if not evaluate(parse_condition(p["when"])[0], self.assign()):
                self.log.append(f"  BLOCKED {aid}: \"{p['failure_message']}\"")
                return "blocked"
        tag = self.tag_of(aid)
        if tag == "harmful":
            self.phase = "halted"
            self.log.append(f"  {aid} -> HARMFUL, case halted")
            self.log.append(f"     halt reason: {act['halt_reason'][:90]}...")
            return "halted"
        self.taken.add(aid)
        self.flags.update(act.get("flags_set", []) or [])
        # A flag granted only once an act has been performed enough times. The counter
        # defaults to the action, so a case that wants several routes to count toward one
        # total has to say so, exactly as the engine requires.
        for fr in act.get("flags_set_repeat") or []:
            key = fr.get("counter") or aid
            self.admin[key] = self.admin.get(key, 0) + 1
            if self.admin[key] >= fr.get("after_administrations", 2):
                self.flags.add(fr["flag"])
        before = self.phase
        self.step_transitions()
        moved = f"   [{before} -> {self.phase}]" if before != self.phase else ""
        self.log.append(f"  {aid} ({tag}){moved}")
        return "ok"

    def due(self, tr, idx):
        if "after_seconds" not in tr:
            return True
        if tr.get("measured_from", "phase_entry") == "guard_true":
            k = (self.phase, idx)
            self.guard_true.setdefault(k, self.t)
            return self.t - self.guard_true[k] >= tr["after_seconds"]
        return self.t - self.entry_t >= tr["after_seconds"]

    def step_transitions(self):
        """One evaluation of the ordered list. First match wins. A time-guarded rule
        matches only when due."""
        for i, tr in enumerate(PHASES[self.phase].get("transitions", [])):
            if not tr.get("when"):
                continue
            if not evaluate(parse_condition(tr["when"])[0], self.assign()):
                continue
            if not self.due(tr, i):
                continue
            if tr["to"] != self.phase:
                self.phase = tr["to"]
                self.entry_t = self.t
                return tr
            return None
        return None

    def wait(self, seconds):
        """Advance the clock, firing any deadline that comes due on the way."""
        target = self.t + seconds
        while self.t < target:
            if PHASES[self.phase].get("terminal"):
                self.t = target
                return
            pending = []
            for i, tr in enumerate(PHASES[self.phase].get("transitions", [])):
                if "after_seconds" not in tr or not tr.get("when"):
                    continue
                if not evaluate(parse_condition(tr["when"])[0], self.assign()):
                    continue
                # guard_true rules are timed from the moment the guard first held, not
                # from phase entry. Measuring both from entry made the runner skip past
                # a delayed consequence, or fire it early, depending on the ordering.
                if tr.get("measured_from", "phase_entry") == "guard_true":
                    k = (self.phase, i)
                    self.guard_true.setdefault(k, self.t)
                    gap = tr["after_seconds"] - (self.t - self.guard_true[k])
                else:
                    gap = tr["after_seconds"] - (self.t - self.entry_t)
                if gap >= 0:
                    pending.append(gap)
            if not pending or self.t + min(pending) > target:
                self.t = target
                return
            self.t += min(pending)
            before = self.phase
            fired = self.step_transitions()
            if fired:
                self.log.append(f"  [clock {self.t}s] {before} -> {self.phase}"
                                f"   ({fired['after_seconds']}s deadline expired)")
            else:
                return


def scenario(name, steps, expect_phase):
    r = Run()
    unknown = []
    print(f"\n--- {name} ---")
    for s in steps:
        if isinstance(s, dict) and "wait" in s:
            r.wait(int(s["wait"]))
            continue
        if r.do(s) == "unknown":
            unknown.append(s)
    for line in r.log:
        print(line)
    ok = r.phase == expect_phase and not unknown
    if unknown:
        print(f"  UNKNOWN ACTIONS: {', '.join(unknown)}")
    print(f"  final phase: {r.phase}   expected: {expect_phase}   {'PASS' if ok else 'FAIL'}")
    return ok


SCEN = json.load(open(PACK.scenarios))
results = [scenario(s["name"], s["steps"], s["expect_phase"]) for s in SCEN["scenarios"]]

print(f"\n{sum(results)}/{len(results)} scenarios passed")
sys.exit(0 if all(results) else 1)
