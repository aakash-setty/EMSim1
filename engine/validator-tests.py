#!/usr/bin/env python3
"""
Negative tests for the case validator. Case-agnostic.

    python3 engine/validator-tests.py [cases/CHFE]

A validator rule that has never fired is a rule nobody has run, and the rules are the
only thing standing between a future case author and a mechanic that fails silently.
Every check here takes a real case that passes cleanly, breaks it in ONE specific way,
and asserts the rule that is supposed to catch it says so.

The case is loaded, mutated in memory and thrown away. Nothing on disk is touched, and
the review matrix is not regenerated, because run_checks does not write it.

A test that expects a message reports the message it got when it fails, since a rule
that fires with wrong wording is as unhelpful as one that does not fire.
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = [sys.argv[0]] + ([sys.argv[1]] if len(sys.argv) > 1 else [])
import validate_case as V                                   # noqa: E402

BASE = V.build_case()
FIRST_PHASE = BASE["phases"][0]["id"]
FAILS = []
COUNT = 0


def run(mutate):
    case = copy.deepcopy(BASE)
    mutate(case)
    return V.run_checks(case)


def act(case, cid=None):
    """A state-changing case action to hang a mechanic on, by id or the first one."""
    for a in case["case_actions"]:
        if cid and a["catalog_id"] == cid:
            return a
        if not cid and a.get("state_changing") is not False and not a["catalog_id"].startswith(
                ("exam_", "interview_topic_")):
            return a
    raise SystemExit("no usable case action")


def expect(name, mutate, needle, where="errors"):
    global COUNT
    COUNT += 1
    errors, warnings, notes = run(mutate)
    pool = {"errors": errors, "warnings": warnings, "notes": notes}[where]
    hit = [m for m in pool if needle in m]
    if hit:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        print(f"       expected {where} containing {needle!r}")
        for m in pool[:6]:
            print(f"       got: {m}")
        FAILS.append(name)


def expect_clean(name, mutate, needle, where="errors"):
    """The rule must NOT fire. Guards against a rule that shouts at correct authoring."""
    global COUNT
    COUNT += 1
    errors, warnings, notes = run(mutate)
    pool = {"errors": errors, "warnings": warnings, "notes": notes}[where]
    hit = [m for m in pool if needle in m]
    if hit:
        print(f"  FAIL {name}")
        for m in hit[:3]:
            print(f"       unexpected {where[:-1]}: {m}")
        FAILS.append(name)
    else:
        print(f"  ok   {name}")


print("=" * 70)
print(f"VALIDATOR NEGATIVE TESTS  ({os.path.basename(V.PACK.case)})")
print("=" * 70)

# The premise. Everything below asserts that ONE change breaks ONE rule, which is only
# meaningful if the unmutated case is clean.
e0, w0, n0 = V.run_checks(copy.deepcopy(BASE))
COUNT += 1
if e0:
    print("  FAIL the unmutated case is clean")
    for m in e0[:5]:
        print(f"       {m}")
    FAILS.append("baseline clean")
else:
    print("  ok   the unmutated case is clean")

print("\n-- rule V: vital effects --")
expect("an unknown vital is rejected",
       lambda c: act(c).__setitem__("vital_effects",
                                    [{"vital": "cardiac_output", "delta": 3}]),
       "is not one of")
expect("a non-numeric delta is rejected",
       lambda c: act(c).__setitem__("vital_effects",
                                    [{"vital": "heart_rate", "delta": "a lot"}]),
       "not a number")
expect("a zero delta warns",
       lambda c: act(c).__setitem__("vital_effects",
                                    [{"vital": "heart_rate", "delta": 0}]),
       "delta is 0", "warnings")
expect("a negative duration is rejected",
       lambda c: act(c).__setitem__("vital_effects",
                                    [{"vital": "heart_rate", "delta": 3,
                                      "duration_seconds": -5}]),
       "expected a positive number")
expect("a negative onset is rejected",
       lambda c: act(c).__setitem__("vital_effects",
                                    [{"vital": "heart_rate", "delta": 3,
                                      "onset_seconds": -1}]),
       "at or above zero")
expect("a duration that does not outlast its onset is rejected",
       lambda c: act(c).__setitem__("vital_effects",
                                    [{"vital": "heart_rate", "delta": 3,
                                      "onset_seconds": 60, "duration_seconds": 30}]),
       "would never act")
expect("an unparseable while condition is rejected",
       lambda c: act(c).__setitem__("vital_effects",
                                    [{"vital": "heart_rate", "delta": 3,
                                      "while": "flag AND AND"}]),
       "unparseable while condition")
expect("one key on two different vitals is rejected",
       lambda c: act(c).__setitem__("vital_effects",
                                    [{"vital": "heart_rate", "delta": 3, "key": "k"},
                                     {"vital": "respiratory_rate", "delta": 3, "key": "k"}]),
       "is already used for vital")
expect("an effect on a non-state-changing action is rejected",
       lambda c: act(c).update({"state_changing": False,
                                "vital_effects": [{"vital": "heart_rate", "delta": 3}]}),
       "can never be recorded")
expect("an unguarded effect that leaves the plausible range warns",
       lambda c: act(c).__setitem__("vital_effects",
                                    [{"vital": "oxygen_saturation", "delta": 40}]),
       "leaves the plausible range", "warnings")
expect_clean("a guarded effect is not warned about, since its phases may be unreachable",
             lambda c: act(c).__setitem__("vital_effects",
                                          [{"vital": "oxygen_saturation", "delta": 40,
                                            "while": "phase is " + FIRST_PHASE}]),
             "leaves the plausible range", "warnings")

print("\n-- rule W: expiring flags --")


def timed(c, **kw):
    a = act(c)
    tf = {"flag": "probe_flag", "duration_seconds": 30}
    tf.update(kw)
    a["flags_set_timed"] = [tf]
    return a


expect("a flag that is not a bare identifier is rejected",
       lambda c: timed(c, flag="probe flag"), "not a bare identifier")
expect("a missing duration is rejected",
       lambda c: timed(c, duration_seconds=None), "expected a positive number")
expect("a zero duration is rejected",
       lambda c: timed(c, duration_seconds=0), "expected a positive number")
expect("granting the same flag permanently on the same action is rejected",
       lambda c: timed(c).__setitem__("flags_set",
                                      list(act(c).get("flags_set") or []) + ["probe_flag"]),
       "absorbs a timed one")
expect("a timed flag on a non-state-changing action is rejected",
       lambda c: timed(c).__setitem__("state_changing", False), "never granted")
expect("a timed flag nothing reads warns",
       lambda c: timed(c), "nothing in this case reads flag", "warnings")


def timed_and_read(c):
    """Grant a timed flag and have a transition read it, which is the intended shape."""
    timed(c)
    ph = next(p for p in c["phases"] if p["id"] == FIRST_PHASE)
    tgt = next(p for p in c["phases"] if p["id"] != FIRST_PHASE and not p.get("terminal"))
    ph.setdefault("transitions", []).insert(
        0, {"when": "NOT flag probe_flag set AND flag probe_flag set", "to": tgt["id"]})


expect_clean("a timed flag a transition reads is not warned about",
             timed_and_read, "nothing in this case reads flag", "warnings")
def timed_in_tag(c):
    """A tag that reads an expiring flag: legal, and a trap the expectation set cannot see."""
    a = timed(c)
    a["tag"] = [{"when": "flag probe_flag set", "value": "recommended"},
                {"when": None, "value": "critical"}]


expect("a tag that reads an expiring flag warns about the expectation set",
       timed_in_tag, "fixed on entry to that phase", "warnings")
expect_clean("a transition that reads an expiring flag does not draw that warning",
             timed_and_read, "fixed on entry to that phase", "warnings")
expect("a flag granted both timed here and permanently elsewhere warns",
       lambda c: (timed_and_read(c),
                  c["case_actions"][-1].__setitem__(
                      "flags_set",
                      list(c["case_actions"][-1].get("flags_set") or []) + ["probe_flag"]))[0],
       "stops expiring", "warnings")

print("\n-- rule N: the arrival handover --")
expect("a saturation in the handover that contradicts the starting phase warns",
       lambda c: c["patient"].__setitem__(
           "arrival_handover", "Sixty-five year old man, short of breath for days. "
                               "He was 62% on arrival."),
       "just contradicted", "warnings")
expect_clean("a saturation that agrees with the starting phase does not warn",
             lambda c: c["patient"].__setitem__(
                 "arrival_handover",
                 "Sixty-five year old man, short of breath for days. He is holding %d%% on six "
                 "litres." % c["phases"][0]["vitals"]["oxygen_saturation"]),
             "just contradicted", "warnings")

print("\n-- rules that predate this pass, spot-checked --")
expect("a condition naming an unsettable flag is rejected",
       lambda c: act(c).__setitem__("tag", [{"when": "flag never_set_anywhere set",
                                             "value": "neutral"},
                                            {"when": None, "value": "neutral"}]),
       "is not set by any action")
expect("an implausible vital is rejected",
       lambda c: c["phases"][0]["vitals"].__setitem__("temperature_c", 96.0),
       "outside plausible range")

print("\n-- flags granted on a repeat dose --")


def repeat(c, also_first=False, **kw):
    """Hang a repeat-granted flag on whichever action this pack offers."""
    a = act(c)
    spec = {"flag": "second_dose_in", "after_administrations": 2}
    spec.update(kw)
    a["flags_set_repeat"] = [spec]
    if also_first:
        a["flags_set"] = list(a.get("flags_set") or []) + [spec["flag"]]
    return a


expect("a repeat count below two is rejected",
       lambda c: repeat(c, after_administrations=1),
       "at least 2")
expect("a non-integer repeat count is rejected",
       lambda c: repeat(c, after_administrations="two"),
       "at least 2")
expect("a repeat flag that is not a bare identifier is rejected",
       lambda c: repeat(c, flag="second dose"),
       "not a bare identifier")
expect("a counter that is not a bare identifier is rejected",
       lambda c: repeat(c, counter="rate control"),
       "counter")
# The silent one. A flag also in flags_set is granted on the first administration, so the
# count never takes effect and the case looks like it works.
expect("a repeat flag that is also granted on the first dose is rejected",
       lambda c: repeat(c, also_first=True),
       "would never take effect")
expect("a repeat flag nothing reads is warned about",
       lambda c: repeat(c), "nothing in this case reads flag", "warnings")

print("\n-- follow-ups --")
expect("a follow-up nothing can discharge is rejected",
       lambda c: [c["follow_ups"][0].pop("satisfied_by", None),
                  c["follow_ups"][0].pop("satisfied_when", None)],
       "nothing can discharge it")
expect_clean("a follow-up satisfied only by a condition passes",
             lambda c: (c["follow_ups"][0].pop("satisfied_by", None),
                        c["follow_ups"][0].__setitem__("satisfied_when", "flag iv_access set")),
             "nothing can discharge it")

print("\n-- rhythm --")
# An unknown value would fall back to a regular beat and say nothing, which in a case
# whose teaching point is the rhythm is the monitor giving the wrong answer out loud.
expect("an unknown rhythm is rejected",
       lambda c: c["phases"][0].__setitem__("rhythm", "irregular"),
       "is not one of")
expect("a rhythm that is not a string is rejected",
       lambda c: c["phases"][0].__setitem__("rhythm", True),
       "is not one of")
# The inverse. Both permitted values, and the absence of the field, have to pass, or the
# rule would break every case written before the field existed. Rule V's range check
# shipped warning on correct authoring once; the inverse case is written down as a test
# for the same reason.
expect_clean("regular passes",
             lambda c: c["phases"][0].__setitem__("rhythm", "regular"), "rhythm")
expect_clean("irregularly_irregular passes",
             lambda c: c["phases"][0].__setitem__("rhythm", "irregularly_irregular"), "rhythm")
expect_clean("a phase with no rhythm at all passes",
             lambda c: c["phases"][0].pop("rhythm", None), "rhythm")

print("\n-- image results (v0.11) --")

MEDIA_DIR = os.path.join(V.PACK.dir, "media")
MEDIA_IDS = sorted(
    os.path.splitext(n)[0] for n in (os.listdir(MEDIA_DIR) if os.path.isdir(MEDIA_DIR) else [])
    if os.path.splitext(n)[1].lower() in (".jpg", ".jpeg", ".png", ".webp", ".gif"))


def imaging_rule(c):
    """The first authored imaging rule in this pack, which is what an image replaces."""
    for k, block in c["content_keys"]["imaging"].items():
        if k == "authoring_note":
            continue
        return block["rules"][0]
    raise SystemExit("no imaging rule")


def img(c, **kw):
    v = {"kind": "image", "abnormal": True, "image": "no_such_image", "caption": "Tracing"}
    v.update(kw)
    imaging_rule(c)["value"] = v
    return v


# The id is the whole payload. Without it the interface has nothing to open, and the
# result would render as an empty frame rather than as an error anyone could act on.
expect("an image payload with no id is rejected",
       lambda c: img(c, image=None), "names no image")
# The one that would ship. The case validates, the build runs, and the gap only appears
# when a resident orders the study and gets a placeholder instead of a tracing.
expect("an image naming a file the pack does not contain is rejected",
       lambda c: img(c), "is not in")
expect("an image payload that also carries report text is rejected",
       lambda c: img(c, report="Sinus tachycardia."), "the picture and nothing else")
expect("an image payload that also carries components is rejected",
       lambda c: img(c, components=[{"label": "QRS", "value": "132 ms",
                                     "reference_range": "< 120 ms", "abnormal": True}]),
       "the picture and nothing else")
expect("an image with no caption warns",
       lambda c: img(c, caption=None), "nothing to title it with", "warnings")
expect("an image payload that omits abnormal is rejected",
       lambda c: imaging_rule(c).__setitem__(
           "value", {"kind": "image", "image": "no_such_image", "caption": "Tracing"}),
       "omits abnormal")
if MEDIA_IDS:
    # The inverse, and the reason it is here: rule V shipped once warning on correct
    # authoring. A pack that does carry media has to pass with its own file named.
    expect_clean("an image naming a file the pack does contain passes",
                 lambda c: img(c, image=MEDIA_IDS[0]), "is not in")
    expect_clean("that same image draws no caption warning",
                 lambda c: img(c, image=MEDIA_IDS[0]), "nothing to title it with", "warnings")
else:
    print("  --   this pack carries no media, so the passing case is not exercised here")

print("\n-- the summary's inputs and the handoff's diagnoses (v0.9) --")
expect("a key topic that is not a topic is rejected",
       lambda c: c["interview"].__setitem__("key_topics", ["no_such_topic"]),
       "not a topic in this case")
expect_clean("key topics drawn from the bank pass",
             lambda c: c["interview"].__setitem__("key_topics", [c["interview"]["topics"][0]["topic"]]),
             "key_topics")
expect("a key exam that is not a case action is rejected",
       lambda c: c["debrief_configuration"].__setitem__("key_exams", ["exam_nowhere"]),
       "not a case action")
expect("a key exam that is not an exam is rejected",
       lambda c: c["debrief_configuration"].__setitem__("key_exams", [act(c)["catalog_id"]]),
       "is not an exam")
expect("an additional diagnosis outside the diagnosis catalog is rejected",
       lambda c: c["handoff"].__setitem__("additional_diagnoses",
                                          [{"catalog_id": "dx_made_up", "explanation": "x"}]),
       "not in the diagnosis catalog")
expect("the correct diagnosis repeated as an additional one is rejected",
       lambda c: c["handoff"].__setitem__("additional_diagnoses",
           [{"catalog_id": c["handoff"]["correct_diagnosis"]["catalog_id"], "explanation": "x"}]),
       "list it once")
expect("an additional diagnosis with no explanation warns",
       lambda c: c["handoff"].__setitem__("additional_diagnoses",
                                          [{"catalog_id": "dx_hypokalemia"}]),
       "has no explanation", where="warnings")
# A delayed consequence of the resident's own action may act in ten seconds; a
# deterioration on inaction may not. Both directions, so the scoping cannot drift.
def _consequence(c, n):
    ph = c["phases"][0]
    a = act(c)
    a.setdefault("flags_set", []).append("vt_probe_flag")
    ph["transitions"].insert(0, {"when": "flag vt_probe_flag set", "to": c["phases"][1]["id"],
                                 "after_seconds": n, "measured_from": "guard_true"})
expect_clean("a ten-second consequence of the resident's own action passes",
             lambda c: _consequence(c, 10), "below the")
expect("a four-second consequence is a button and is rejected",
       lambda c: _consequence(c, 4), "below the 5s floor")
expect("a ten-second deterioration on inaction is still rejected",
       lambda c: c["phases"][0]["transitions"].insert(0,
           {"when": "NOT flag iv_access set", "to": c["phases"][1]["id"], "after_seconds": 10}),
       "below the 30s floor")

print(f"\n  {COUNT} checks, " + (f"{len(FAILS)} FAILURES" if FAILS else "all passed"))
sys.exit(1 if FAILS else 0)
