# Making a clock into something the case can read

Design v0.8. One change, and three things found while making it.

Kept for what was rejected. The current behaviour is in `docs/system-design-v2.md`
sections 2.6 through 2.9, 13.1 and 17, and in `docs/case-authoring-requirements.md`
sections 6.1 through 6.6. This file is not a source of truth for how the system behaves.

---

## 1. The problem v0.7 left behind

v0.7 let an action move a vital for a fixed time. Playing it, the mechanism is
convincing: the saturation climbs, holds, and falls back. Authoring against it, it is
half a mechanism. `duration_seconds` moved a number on a screen and nothing else. No
transition could fire when the drug stopped working, no tag could flip, no consultant
could say something different, no prompt could be guarded on it, because nothing in the
condition language could see it.

So the case whose lesson is a closing window, which is most of the cases anyone would
want to author with a clock, was still unauthorable. What could be authored was a case
where a number went up and came down while the case sat still, which teaches that the
monitor is decorative.

**Decision.** A case action may grant a flag with a duration. When the duration lapses
the fold removes the flag and re-checks transitions.

The re-check is the load-bearing half. Without it a case could author "when the drug is
no longer acting, deteriorate" and the transition would fire only when the resident next
pressed something, which is not a bug that reads as a bug: it reads as the simulator
being flaky, and it would be found by a physician reviewer rather than by a test.

---

## 2. Why a flag, and not any of the alternatives

### Rejected: a new predicate, `drug D acting`

Narrower, and it would have cost a grammar change, a review-matrix column, its own
validator rules and its own place in every document, to express one thing. A flag that
expires is the existing flag, the existing predicate, the existing matrix and the
existing rules with a deadline attached. Section 4 of the design is untouched, which is
the test anything added here has to pass: the condition language projecting over phase,
flags and study state is what keeps the per-key matrix finite, and a matrix a physician
can read is the only reason any of this is reviewable.

### Rejected: making `duration_seconds` on a vital effect set a flag implicitly

Tempting, because it removes the two-places problem, and wrong because it makes a display
concern silently create clinical state. An author writing a cosmetic thirty-second blip
would have been given a flag they did not ask for and did not name, and the flag would
appear in the review matrix as a thing the reviewer has to account for.

The explicit pairing is one extra line and says what it does:

```json
"flags_set_timed": [{"flag": "nitrate_acting", "duration_seconds": 30}],
"vital_effects": [{"vital": "oxygen_saturation", "delta": 5,
                   "key": "nitrate_spo2", "while": "flag nitrate_acting set"}]
```

### Rejected: letting the fold narrate a lapse

A nurse line on every expiry would be a free deterioration warning attached to a mechanism
whose whole point is that the resident is not being told. It would also break the section
2.2 rule that prompt text may not describe a trajectory, since the one place a nurse may
do that is the narration on a transition, which is exactly where a case that wants the
resident told should put it.

### Rejected: a flag that can be cleared by an action

"Stop the drip" already works, through a `while` guard on a flag the stop action sets. A
second removal mechanism would have given two ways to express one thing and two ways for
them to disagree.

---

## 3. How grants combine, and why each rule is what it is

A flag is shared state and more than one action can write it, so the interesting part is
not one grant but two.

**A permanent grant absorbs a timed one, in either order.** A drip that is running is
running; a bolus of the same drug must not schedule its removal, and starting a drip after
a bolus must not leave the bolus's deadline standing. The validator warns when a flag is
granted both ways, because it is usually right and always invisible.

**A timed grant extends to the later deadline.** The earlier expiry event still arrives,
sees a later grant standing, and does nothing. So a resident who redoses two seconds
before the deadline is not overtaken by it, which is the behaviour a resident would expect
and the opposite of what a naive "latest grant replaces" would give.

**A lapse costs nothing.** No timeline entry, no score, no nurse line. It is a thing that
stopped being true while the resident was doing something else, and charging for it would
make the mechanism a trap rather than a lesson, which is the same line section 1 draws
around time-guarded transitions.

**The one trap that could not be designed out.** The set of critical actions a phase
expects is computed once, on entry to that phase. A tag that reads an expiring flag will
re-resolve correctly on every action but the expectation will not follow it, so an action
that becomes critical because a flag lapsed is never listed as missed. Recomputing the
expectation set continuously was rejected: it would mean the debrief's "missed" list
depends on when you look at it, and a resident could be credited or not for the same run
depending on the moment it ended. The validator warns and points the author at a
transition instead.

---

## 4. Three defects found on the way, two of them older than this change

**Completion was recorded per call site.** `st.complete` was set after the
`checkTransitions` call in `applyLog` and nowhere else, so a case authoring a time-guarded
transition into `case_complete` reached the phase without the run being marked complete.
The validator explicitly permits that transition, with `allow_time_to_terminal`, so it was
reachable. Every new kind of timed event would have reopened the same hole. Moved into
`enterPhase`.

**The engine test harness held a stale action map.** `selectCase` builds a new actions
object on every call, and the suite binds every packed case in turn before rebinding the
one under test. A reference captured at the top of the file therefore pointed at the first
pack's map for the whole run. Every value read off it agreed with the live map, so nothing
ever failed, and the staleness surfaced only when a test tried to write to it. Rebound in
`bind()`.

**A validator rule that shouts at correct authoring is worse than no rule.** Rule N warned
about any vital sign in an arrival handover, on the grounds that the monitor carried the
same numbers and would contradict them within a minute. That stopped being true in v0.7,
when the monitor became dark until attached: the handover is now often the only number a
resident has before they put equipment on the patient, which is what a handover is. The
blanket warning is a note, and the check that replaced it is the one the old rule was
really aiming at, which is a quoted saturation that disagrees with the phase the case
starts from.

This is also why `validator-tests.py` exists, and why half of its checks assert that a
rule does **not** fire. A validator that cries wolf trains authors to skim it, after which
it protects nothing. Rule V's range check would have shipped doing exactly that, warning
on CHFE's guarded nitrate effect on every run, if the inverse case had not been written
down as a test.

---

## 5. Testing a mechanic no case uses

Neither shipped case authors an expiring flag or an onset. A mechanic no case uses is a
mechanic nobody has run, and shipping one on the strength of having read the code is how
the next author discovers it does not work.

So the engine harness authors one: it installs a synthetic action and a synthetic
transition on the loaded case, exercises them, removes them, and asserts at the end that
it left the case as it found it. That covers the lapse, the refresh on redose, permanent
absorption in both orders, an effect guarded on a lapsing flag, onset, duration measured
from the administration rather than from onset, the clamp at both ends, and the thing the
whole change exists for: a transition firing at the moment of the lapse with no further
action taken.

**Rejected: authoring the mechanic into CHFE to test it.** Giving CHFE a nitrate that
wears off with a clinical consequence is a change to what the case teaches, and it would
have been made to satisfy a test rather than because a physician decided the case should
teach it. Test coverage is not a reason to edit clinical content.

---

## 6. The arrival vitals on the splash

**Decision.** The case card shows the first phase's vitals before Begin.

This sits next to v0.7's gating of the monitor and does not undo it. A handover is
numbers somebody else measured before the resident arrived; the two sentences of EMS
handover on the History tab are the same thing in prose, and CHFE's now names the
saturation for exactly that reason. What the resident still has to earn is the current
number and the trend, which is what a monitor is and what attaching one buys.

So the strip is styled as figures on a pale panel rather than in the monitor's dark, is
static, and carries none of the cosmetic variance the monitor adds.

**Rejected: a caption saying the numbers are not live.** It was written and then removed
on the author's instruction, and the instruction was right. The heading is past tense and
the dark monitor a few seconds later says the rest. A resident who has to be told in a
sentence that a number from before they walked in is not a live reading has been handed
the lesson instead of learning it, which is the same argument that took the background
narrative off this card in v0.5.
