# Vitals you have to obtain, and effects that belong to actions

Design v0.7. Four changes went in together because three of them are the same change
seen from different sides: the interface had been asserting things the resident had not
earned, and a phase had been carrying work that belongs to an action.

Kept for what was rejected. The current behaviour is in `docs/system-design-v2.md`
sections 2.6, 3.1, 8.3, 8.4b and 13.1, and in `docs/case-authoring-requirements.md`
sections 6.1 and 6.2. This file is not a source of truth for how the system behaves.

---

## 1. The monitor is dark until someone attaches it

**Decision.** Vitals and the heartbeat appear only after an action carrying the catalog
capability `reveals_vitals` has been taken. In the shipped catalog that is
`attach_monitor` and nothing else.

**Why.** Attaching a monitor was a recommended action whose consequence the resident
could not perceive. An action with no perceptible consequence is one a learner is
entitled to skip, and skipping it cost nothing, so the tag was decoration. Worse, the
numbers were on screen before anyone had done anything to obtain them, which teaches
that vitals are a property of having arrived in a room. They are a property of having
put equipment on a patient. A resident who has not done that should be looking at the
patient.

### Rejected: gate on the case flag `on_monitor`

Both cases already set a flag when the monitor is attached, and the fold could have read
it in one line. Rejected because `engine/` would then have named a flag that a case
happens to define. A case could rename it and silently disable the gate, or set it from
an unrelated action and silently enable it. The capability is a property of the act, so
it is a catalog field, and the engine asks the catalog rather than the case. The engine
test asserts that exactly one action carries it, which is the check that stops a second
route appearing later without anyone deciding it should.

### Rejected: show the vitals greyed, or behind a "not monitored" label

A second visual state for "there is a number but you cannot see it" implies the number
is being withheld from the resident by the interface, which invites reading the layout
for information. The dash is already the interface's word for "no number here", used for
an unauthored vital in a half-written case, and a reader is not helped by two kinds of
nothing.

### Rejected: silence the nurse's prompt tone as well

The instruction was "vitals and therefore sound off", and the heartbeat is the only
sound derived from vitals. The prompt trill is a person speaking. Silencing it would
have made the first prompt of every case inaudible to a resident who had not yet
attached anything, which is exactly the resident the prompt exists for.

**Accepted cost.** The sound control now has four states rather than three, because
sound can be on while the room is silent. It says "Sound on, no monitor" rather than
"Sound on", since a control that claims to be working over silence reads as a fault.

---

## 2. Vital effects belong to actions, not to phases

**Decision.** An action may carry `vital_effects`: a delta on one authored vital, with
an optional duration, an optional guard, and a key that decides what does not stack.

**Why.** A phase is entered once and holds. It cannot express thirty seconds, it cannot
express an effect that ends when the drip is stopped, and it cannot express a drug that
changes the patient without changing the number being watched. All three are ordinary
clinical facts, and all three were unauthorable.

### Rejected: extra phases

The thirty-second nitrate excursion as a phase pair means a phase for "nitrate acting"
and a transition back out of it on a timer, per drug, per route, multiplied by whatever
else is running. Phases are the unit the review matrix enumerates and the unit a
physician reviews. Doubling them to express a transient makes the artifact a physician
reads worse in order to make one number move, and the transitions would not compose:
two drugs acting at once needs a phase for the pair.

### Rejected: putting vitals in the condition language

Everything in this design that keeps the review matrix reviewable follows from the
condition language projecting over phase, flags and study state alone. Time was kept out
of it in v0.6 for that reason and vitals are kept out for the same one. A case cannot
author "if the saturation is below 90". If it needs that, it needs a phase, and a phase
is exactly the thing a reviewer can see.

### Rejected: effects that ramp, titrate, or depend on dose

Doses are not implemented anywhere in the product; `{dose}` is dropped from narration
rather than faked. An effect that varied with a dose would be the first place in the
system where a number the resident cannot enter changes what they see.

### Rejected: summing repeat administrations

Two clicks of the same drug summing to twice the effect is not true of any drug in the
catalog, and it makes a resident who double-clicks a button better at resuscitation.
Effects sharing a key collapse to the most recent, so a repeat refreshes. The key
defaults to the action id and is written explicitly where two routes reach the same
drug, which is the same obligation a harmful tag has and fails the same way when it is
forgotten.

### Rejected: applying effects in terminal phases

`halted` and `case_complete` author the numbers a reader is left looking at. An effect
still running would edit the ending, and a halt card reading 77 percent because a mask
was on would disagree with the arrest it describes.

**Accepted cost, and it is the real one.** Effects are display and audio only, exactly
as the phase-boundary ramp already was. A blood gas ordered while a nitrate is acting
reports the phase's authored numbers, and the monitor beside it disagrees for up to
thirty seconds. This is the inconsistency v0.5 accepted for the five-second ramp,
reachable in one more way and for longer. The alternative is a state layer whose vitals
move continuously, which breaks result freezing and makes every rule that reads a phase
read a moving target.

---

## 3. What this did to CHFE, which is not a mechanical change

Rebasing is forced: if positive pressure adds three points and the phase reached by
applying positive pressure also raises the saturation, the resident sees both.
`stabilizing` and `improving` therefore came down from 93 and 96 to the arrival value of
87, so the only durable oxygenation gain in the case is the mask, and diuresis supplies
none at all.

**This changes what the case teaches, and the change was made deliberately.** A resident
who reaches for the diuretic first now watches the saturation not move while the heart
rate, pressure and respiratory rate all improve. That is the case's second learning
objective, sequencing positive pressure and vasodilation ahead of diuresis, expressed as
behaviour rather than as a sentence in the debrief.

**It is also a clinical claim, and it is the weakest one here.** Real diuresis in a
patient four kilograms above dry weight does improve oxygenation, over a longer horizon
than this eight-minute case covers. The case now says it improves nothing. That is
defensible for the horizon being simulated and it is an approximation, and it is the
kind of thing a reviewing physician should be given the chance to reject. It belongs in
the review packet rather than only here.

The deltas themselves, three points and five points, are teaching choices. No trial
supports a figure. They are recorded as notes on the effects.

---

## 4. Two smaller changes made in the same pass

**A question the patient did not understand is no longer a chart entry.** When the
matcher finds no topic, the case's `out_of_scope_fallback` answers. The exchange stays
on the History tab, where the resident can see which phrasing failed and try again, and
it does not enter the chart. A chart is a record of what was learned about the patient;
three repetitions of "I don't know what you mean" bury the history that was taken. The
readout already recorded the matched topic and is null exactly when the fallback
answered, so this is one test rather than a comparison against the fallback text.
Rejected: rendering it in a muted style instead, which keeps the noise and adds a
style.

**The Stabilization group opens by default, and filtering now opens groups immediately.**
The first is one entry in a new `defaultExpanded` map: the three acts that begin any
resuscitation, one of which now gates the monitor, should not be behind a click.

The second was a pre-existing defect found while testing the first. Filtering added the
matched groups to the expanded set *after* the markup had been built, so a filter set in
one stroke showed collapsed headers until something else repainted the tab, and the set
kept every group that had ever matched, so clearing the box left the accordion open on
groups the learner had never touched. A filter now forces its surviving groups open for
as long as it is set and mutates nothing, so clearing it leaves the tab as the learner
had it.
