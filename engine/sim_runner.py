#!/usr/bin/env python3
"""Scenario runner. Case-agnostic.

Walks a case through the paths listed in its pack's `<PREFIX>-scenarios.json` to
confirm the phase machine, prerequisites and halting behave as authored. This is a
sanity check on the case file, not an implementation of the engine.

    python3 engine/sim_runner.py [cases/CHFE]
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_case import parse_condition, evaluate, atoms_of
from paths import resolve_pack

PACK = resolve_pack(sys.argv)
case = json.load(open(PACK.case))
ACTIONS = {a["catalog_id"]: a for a in case["case_actions"]}
PHASES = {p["id"]: p for p in case["phases"]}
START = case["phases"][0]["id"]


class Run:
    def __init__(self):
        self.phase, self.flags, self.taken = START, set(), set()
        self.ordered, self.resulted, self.log = set(), set(), []

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
        before = self.phase
        for t in PHASES[self.phase].get("transitions", []):
            if t.get("when") and evaluate(parse_condition(t["when"])[0], self.assign()):
                self.phase = t["to"]
                break
        moved = f"   [{before} -> {self.phase}]" if before != self.phase else ""
        self.log.append(f"  {aid} ({tag}){moved}")
        return "ok"


def scenario(name, steps, expect_phase):
    r = Run()
    print(f"\n--- {name} ---")
    for s in steps:
        r.do(s)
    for line in r.log:
        print(line)
    ok = r.phase == expect_phase
    print(f"  final phase: {r.phase}   expected: {expect_phase}   {'PASS' if ok else 'FAIL'}")
    return ok


SCEN = json.load(open(PACK.scenarios))
results = [scenario(s["name"], s["steps"], s["expect_phase"]) for s in SCEN["scenarios"]]

print(f"\n{sum(results)}/{len(results)} scenarios passed")
sys.exit(0 if all(results) else 1)
