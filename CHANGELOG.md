# Changelog

Unreleased. No case has completed the section 14.3 sign-off checklist, so none of this
is usable with learners.

---

## The debrief opens twice, and the clock's ending actually ends the case

**The debrief now starts with a verdict and nothing else.** One line: *All Critical Actions
Achieved!*, *Critical Actions Missed*, or *Case Failed*; under it the halt or arrest reason
where there is one; under that the critical actions that were completed, by name, with no
teaching note attached. Then replay, **Reveal Case Answers**, and choose a different case.
Everything the debrief used to open with, the missed list, the domain table, the handoff
verdict, the notes, is the answer key, and a resident who wants to run the case again before
reading the answers had to scroll past all of it to reach the replay button. Reveal replaces
the screen in place with the full debrief.

A run that halted on a harmful action is presented as *Case Failed* alongside the arrest
rather than being scored against the critical actions. A resident who did all six and then
gave something that stopped the case should not be met with a congratulation over a halt
reason.

**Two sections are gone.** *Blocked attempts* carried teaching that had already happened, in
the interface, at the moment the prerequisite refused the action and said why. *Independent
versus prompted* read as a scoreboard, and the same fact survives as a `prompted` pill on the
action it belongs to. Both are still folded; only the sections are gone.

**In the section that remains**, "Critical actions" is set at 24px and the missed list, now
headed "Non-Critical Missed Actions", at 19px, and every listed action is indented 20px so
the headings read as headings rather than as the first line of the list. The new heading is
recorded in the design document with a note that it does not describe the list's contents:
the list holds critical actions that were not satisfied. That is the author's label, kept as
specified, and flagged rather than silently corrected.

**A case that arrests on the clock now ends.** This is a real defect, not a refinement. Since
time-guarded transitions landed, a case could author `allow_time_to_terminal`, reach its
terminal phase, and then simply keep running: the nurse said her line, the monitor fell to the
phase's vitals, and nothing ended, because `halted` means a harmful action and `complete`
means a handoff and this was neither. In the meningococcaemia case that showed as a patient
sitting at 44/24 with the clock still counting.

The fold now derives a third ending, `failed`, from the phase table, carrying the phase, its
entry time and its authored `timeout_reason`. The interface waits five seconds
(`SHARED.ending.terminalGraceSeconds`) before showing the debrief, so the arrest is something
the resident watches happen rather than something a debrief informs them of. Those five
seconds sit below the validator's 30-second floor on `after_seconds` on purpose: that floor
governs how long a resident has to act, and by then the phase has no exits.

Nothing in the engine names a phase and nothing in a case implements an ending. Eight new
case-agnostic assertions cover it, and they run against all three packs.

---

## The case waits for you, and does not let you throw it away by accident

**A window nobody is looking at pauses the case**, on either signal the browser gives:
`visibilitychange` for a hidden tab or a minimised window, `blur` for a window still on
screen with the focus somewhere else. Time away is accumulated and subtracted from the case
clock, so it freezes rather than jumping. That matters more than it sounds: the clock is
wall-clock time and the deadlines a case authors are claims about how long a patient
tolerates something, so charging a resident for minutes spent in another window made those
claims false. **It never resumes on its own.** Coming back to a case that ran without you is
worse than coming back to one that waited, so resuming is a deliberate click on an overlay,
and the sound stops and starts with it through the scene mechanism the debrief already used.

**Refresh and back now ask first.** The run is the only copy; there is no server and nothing
is stored. Keyboard refresh and the back button are interceptable and raise the simulator's
own dialog. **A click on the browser's own reload control is not**, and this is worth
stating plainly rather than hiding: the only hook there is `beforeunload`, whose wording no
browser has let a page choose for over a decade. That path gets the native dialog, the two
look different, and every technique that claims otherwise either fails silently or blocks
the main thread. The back guard falls back to returning to the case list if there is nothing
behind the page, so a resident who asks to leave is never left looking at the case they
asked to leave.

**The heartbeat anchor moved from A5 to A6** on the author's instruction. The mapping is
unchanged and only the anchor moved, so a patient at 88 percent now sits at 880 Hz where he
sat at 440. The cost is recorded beside the setting: the beat is now inside the band the ear
is most sensitive to, so it carries further and is more tiring across a case.

**Nothing sounds outside a running case.** The scene gate was already stopping the room; it
now stops the heartbeat too, checked in `sync()` rather than only in `setScene`, because
`sync()` runs sixty times a second and would otherwise restart the chain on the next frame.

**"Giving of ceftriaxone" is fixed, and so are the two defects underneath it.** Doses are
not implemented, so `{dose}` is dropped from the narration template, and dropping the word
while leaving the grammar around it produced a dangling preposition. The slot is now removed
together with whatever joins it to the name, in both directions. Fixing that exposed the
second: display names are Title Case because they are buttons, and lowercasing them
wholesale turned "1L" into "1l", "IV" into "iv" and "Ringer's" into a common noun. Only
ordinary Title Case tokens are lowered now, so units, acronyms and proper nouns survive. And
the third: templates that lead with the name produced sentences starting in lower case.

---

## The room has a sound, and it stops when the case does

**Ward ambience loops under everything at a very low level while a case is running.** The
author supplied the recording; a build step cuts a 45-second loop from a steady stretch of
it, crossfades the tail onto the head with an equal-power curve so the seam is continuous
in level as well as in sample value, and peak-normalises it so the gain figure in the audio
module is against a known reference rather than against whatever that particular recording
happened to be. `engine/assets/make-ambience.py` records all three decisions; the source
recording is kept beside it so the loop can be recut.

**It is the room rather than the patient or the nurse**, so it is gated on neither the
monitor nor anything clinical. It runs from Begin to the debrief and is silent everywhere
else: the welcome screen, the splash of a case chosen and not started, and the debrief
itself. That last one is the requirement worth stating as a rule. A debrief is reading
rather than resuscitating, and a room still humming under a learner reading about what they
missed is the interface failing to notice the case is over. `AUDIO.setScene` is the whole
mechanism, called at four sites, and the suite asserts against the built file that all four
survive, because losing one would be silent in every other test.

**It changes design 8.4b, and for the better.** The room is no longer silent before a
monitor is attached. What is missing then is the MONITOR's sound, which is the whole of the
point that gating was making, and a ward that fell silent until somebody attached a monitor
was the less truthful half of it.

**Nothing depends on it.** It is decoded once from base64 in the page, looped as a buffer
with loop points set inside the mp3 encoder padding so the seam cannot click, and every
failure path ends in a silent room rather than an error: a case must never fail to start
because a decoder disliked an mp3. A checkout without `engine/ambience.txt` builds a
working simulator that is 360 KB smaller, which matters because it is now by far the
largest single asset in the file. The build went from 1.8 MB to 2.2 MB.

**The second heart sound is effectively off**, at 0.001, on the author's instruction: the
beat reads as one sound rather than as lub-dub. It is left in the graph at a level nobody
will hear rather than removed, because it is also what sets the spacing the first sound is
heard against, and because restoring it is then one number rather than a structural change.

---

## One dose is a trial, two is a treatment

**Flags can be granted on the Nth administration.** `flags_set_repeat` on a case action
takes a flag, an `after_administrations` count of at least two, and an optional `counter`.
It is the one exception to section 15's rule that flags are permanent from the first dose,
and it exists for the case whose lesson **is** the redose: an act that produces a partial
response the first time and works the second. AFRVR is that case. A single dose of any
rate-controlling agent now takes twenty-two beats off the ventricular rate and changes
nothing else; the phase turns over on the second.

**The counter is the clinical judgement in it.** Left to default it counts the act, so a
sibling covered through `also_covers` adds to the same tally. Named explicitly, several
separate case actions share one tally, which is what AFRVR does: digoxin, amiodarone,
metoprolol, esmolol, propranolol and diltiazem all count toward `rate_control_doses`,
because two attempts at atrioventricular nodal blockade are two attempts whichever drugs
they were. Two actions granting one flag at different totals is silent and the validator
warns.

**Nothing counts doses in the condition language and nothing will**, for the same reason
time does not: the per-key review matrix has to stay finite. A case reads the count only
through the flag.

**Follow-ups gained `satisfied_when`.** `satisfied_by` is set membership and cannot express
"again": an obligation to repeat a dose is created by the first dose and is discharged by
it, because the action that would satisfy it is already in the taken set. A condition can
say what a list cannot. One of the two is now mandatory, because a follow-up with neither
is an obligation the debrief reports as open however the resident plays.

**`narration_addendum` became `nurse_alert`**, and is emitted on its own nurse kind. It is
coloured and it goes into the running chart, because the moment such a line matters is
half a minute after it was said, when the resident is deciding whether the drug worked and
the nurse's banner has moved on. It is not a prompt: no slot, no trill, said on the action
rather than on a deadline, and said again on a redose.

**Every nurse line now makes a sound.** A prompt keeps its trill; everything else gets a
short soft cue. A line nobody was looking at is a line nobody read, and the banner is not
where a resident's eyes are. The two are exclusive, and repeats inside 250 ms are dropped
so a submitted basket does not fire a burst of clicks.

**The three levels moved into one block and were rebalanced by ear**, the cue doubled and
the heartbeat halved on the author's instruction after playing a case. They are exposed on
the audio module, because the balance between them is a decision and a decision nothing can
check is a decision that drifts. The figures are not a ranking: peak gain is not perceived
loudness, and a long low thump at 0.15 sits under two short high components at 0.11. The
suite asserts the invariants instead, which are that the second heart sound stays under the
first, that a cue cannot be masked by a beat landing on it, and that nothing dominates.

---

## Reports state findings, not conclusions

**A note addressed to the reviewing physician was being printed to the learner.** A
laboratory payload's `comment` is rendered under the result. AFRVR's natriuretic peptide
carried an assay caveat written for the reviewer in that field, so a resident was told to
distrust a number they had just been handed. Reviewer-addressed notes belong in `verify`,
which nothing renders and which the catalog's own defaults already use for exactly this.

**AFRVR's imaging reports lost their interpretation lines and about two thirds of their
length.** An editorial decision in the case rather than an engine change, recorded here
because the argument generalises. A report that ends "interpretation: cardiogenic pulmonary
oedema" has done the work the case exists to set; the reasoning belongs in the debrief note
for that study, where a learner meets it after committing to an answer. And length in a
report reads as importance, so a long report about a negative study actively misleads. The
tracing went from about a hundred words to forty-three, the cardiac ultrasound from a
hundred and twenty to forty-six.

---

## Four fixes from playing the third case

**A covered sibling lit up the covering action's button.** The other half of the coverage
defect below, and introduced by its fix: recording the covering action in `taken` made the
debrief score correctly and made the action grid draw digoxin as already given to a
resident who had pressed metoprolol. There are now two sets, and the difference between
them is the whole point. **`taken`** is which buttons were pressed and is what the grid
reads. **`satisfied`** is what has been accomplished, `taken` plus the covering action of
anything performed through an also_covers group, and is what the debrief, the follow-up
satisfiers, the prompt suppression and `action X taken` read. `evalCond` degrades to
`taken` where `satisfied` is absent, so a hand-built state still resolves.

**`narration_override` never existed.** Authoring section 9.1 has promised it since v0.2
and nothing read the field, so a case that authored one got the catalog line and no error.
Implemented, together with **`narration_addendum`**, a second nurse line said straight
after the catalog's own. The addendum is the field a case wants when it has authored a
delay: a resident who pushes a drug and watches an unchanged number will reasonably
conclude it did not work and push another, and one line from the nurse prevents it.

**The soft floor on a timed transition was firing on the wrong pattern.** The 60-second
warning is a fairness rule, and fairness is about things that happen TO a resident: a
deterioration on inaction, or an unguarded natural history. A delayed consequence of an
action they took has nothing to prevent and no reflex to test, so warning that a drug acts
too quickly is not a fairness question. Scoped to negative-guard and unguarded rules, the
same way the mandatory-prompt rule already was. The hard 30-second floor is unchanged and
applies to everything.

**The monitor read `min` with a superscript minus one.** It now reads `/minute`.

---

## The heartbeat can be uneven

**A phase may declare a `rhythm`.** `regular`, which is the default and is bit-identical to
what came before, or `irregularly_irregular`, which draws every R-R interval independently
so there is no period for the ear to lock onto. It exists because the third case is atrial
fibrillation: its ECG report said the rhythm was irregularly irregular, its examination
said the first heart sound varied beat to beat, its entire management turned on
recognising the rhythm, and the monitor beat a metronome. Sound was the more immediate of
the two channels and it was saying the wrong thing.

The vocabulary is closed and global. **The engine holds no association between a rhythm and
a diagnosis**, in the same way the catalog holds no appropriateness judgement about a drug;
a case chooses a name and nothing else. A boolean was rejected because regularly irregular
rhythms are a real and audibly different third thing, and deriving the rhythm from the
diagnosis was rejected because it would have put clinical knowledge in `engine/`.

Intervals are a shifted exponential, `mean * (s + (1 - s) * Exp(1))`. **The mean is
preserved exactly**, which matters more than it sounds: the monitor shows a heart rate, and
if the average sounded interval were not that rate the case would be showing one number and
sounding another. The refractory fraction is raised where a fixed floor would be breached
rather than the draw being clamped, because clamping would push a third of the beats at 220
bpm onto the floor and move the mean off the authored rate. The floor also guarantees no
beat's second sound can land on the next beat's first, which the suite asserts rather than
assumes.

**The beat is now a self-rescheduling chain rather than a fixed interval**, each beat
reading the current vitals and choosing its successor's delay. The rate quantisation that
existed to stop a five-second ramp restarting the interval three hundred times is gone with
it, because there is nothing left to restart, and the tempo now follows the ramp exactly
rather than in two-beat-per-minute steps. Both earlier cases sound the same, slightly
smoother across a phase change.

The ECG trace follows the same field: unevenly spaced complexes and no P wave, deterministic
per rate so it does not shimmer. It is still decorative and the note says so.

**Every parameter here is a teaching choice and none is measured**, and the provenance note
in `SHARED.audio.rhythm` says so in those words. No case models a rhythm.

Three things turned up on the way. A `const` declared inside a direct `eval` does not leak
into the calling scope the way `engine.js`'s function declarations do, so the test harness
saw no audio module and reported a missing fence; the block hands its binding back
explicitly now. The lub-dub gap was a fixed 160 ms, which at the 220 bpm the validator
permits would have put one beat's second sound on the next beat's first, and no case had
been fast enough to expose it. And the decorative trace was about to draw P waves next to
an uneven beat.

See `docs/decisions/rhythm-and-the-heartbeat-chain.md`.

---

## Third case: AFRVR, and eight engine defects it found

**A third case pack.** `cases/AFRVR/`: atrial fibrillation with a rapid ventricular
response in a man with a previously undiagnosed reduced ejection fraction, drafted from a
real physician seed rather than the other way round. It is the first pack whose
AUTHOR-ONLY fields mostly came from an author, and the first to carry a `_SEED.md` that
records what did and did not.

The case is built around one decision: the standard treatment for the visible problem is
contraindicated by an invisible one that takes a minute with an ultrasound probe to find.
It uses all five tag tiers, two coverage groups on critical actions, two time-guarded
deterioration transitions, two delayed-consequence transitions, and a vital effect
authored as four staged steps so a number climbs over a minute rather than jumping.

**It found eight defects, seven of them older than the case.** Each is in `engine/` and
none names a case.

*`discouraged` was scored by nothing.* The fifth tag tier was defined in the specification,
authored by MGCA on thirty-one tag rules, recorded on the timeline, and then read by
nothing at all: the debrief surfaced critical, recommended, harmful and the neutral traps,
so a discouraged action produced no output. A tier that carries no weight is the defect
the tier was added to fix. It now has its own debrief section.

*A covered sibling did not satisfy the covering action's expectation.* `also_covers` gave
a sibling the covering action's tag, flags and note, so it advanced the case and could not
escape a harmful tag, and then the debrief reported the critical action as missed because
`st.taken` recorded the button that was pressed. A resident who gave Ringer's in MGCA was
told they had not given fluid. Coverage is the case asserting the two acts are the same
act, and recording both is what that assertion means.

*A `guard_true` transition scheduled no deadline of its own.* Deadlines were pushed at
phase entry, where a guard_true guard is usually still false, so the rule could only ever
fire on the resident's next action. A case authoring "this drug takes a minute to work"
left a resident who gave the drug and then waited watching nothing happen. Now scheduled
at phase entry when the guard already holds, and at the moment it first holds otherwise.
`sim_runner.py` had the mirror-image bug: it measured guard_true deadlines from phase entry
in `wait()` while handling them correctly in `due()`.

*The validator warned about stranded prompts that were not stranded.* Any timed exit in a
phase was treated as the phase's earliest end, including a `guard_true` one whose clock has
a different origin entirely. Nine wrong warnings on this case. A validator that cries wolf
trains authors to skim it.

*The case-agnostic engine suite hard-coded a case id.* Its equivalence-group assertion
inserted `iv_access_peripheral`, which is CHFE's id for the line, so in any other pack the
line was never inserted, every intravenous group member was blocked by its prerequisite
rather than halting, and the assertion failed for a reason unrelated to what it tests.

*The debrief could not name an act, only a drug.* `expectation_label` was added, so a case
that scores "rate control" as one act through a coverage group can say so instead of
telling a resident who gave amiodarone that they completed "Digoxin bolus".

*A diagnosis could only be right or wrong.* Dispositions have had
`acceptable_with_qualification` since the reference case. Diagnoses had not, so a case
whose formulation has two halves marked the other half incorrect. `alternative_diagnoses`
now takes the same verdict and the debrief shows "defensible".

*Section 14.2c's artifact had no tool.* The deterioration timeline is required for any case
using a time-guarded transition and MGCA's was written by hand, which means it could
disagree with the case file silently. `engine/deterioration_timeline.py` generates it: every
timed exit with its guard and preceding prompts, the do-nothing trajectory with vitals at
each hop, and every narration line against the vitals it introduces. Run against this case
it immediately found two narration lines that contradicted the monitor.

**Catalog 0.2-draft.** Three entries added to Meds - Cardiac on author instruction and
marked `source: author-supplied, not in screenshots`: **Digoxin bolus**, **Apixaban** and
**Enoxaparin**. Before this the catalog held no rate-control agent for a patient in whom
calcium channel blockade is contraindicated, and no anticoagulant but heparin. Apixaban and
enoxaparin are in `NON_IV`, so neither requires vascular access. There is deliberately no
anticoagulation equivalence group, and `equivalence_groups` now says why.

**The out-of-scope arm finally has enough questions to mean something, and the answer is
bad.** `AFRVR-matcher-eval-questions.json` carries thirty out-of-scope questions, which is
the floor authoring section 10.6 sets and which neither earlier pack meets. Nineteen of the
thirty receive a confident, specific, wrong answer. In scope the case returns 31 of 47
held-out phrasings with nine wrong topics on management-changing topics. This is the
strongest evidence yet for section 10.6's suggestion that a larger variant space trades
out-of-scope rejection for recall: 570 variants across 38 topics is more than either
earlier case and more surface for a spurious lexical match to land on.

---

## System design v0.8, authoring requirements v0.7

**Flags can expire, and this is the change that matters.** v0.7 gave a vital effect a
`duration_seconds`, which moved a number on a screen and nothing else: no condition could
see it, so "the drug stopped working" was a rendering event rather than a clinical one and
a case whose lesson is a closing window was still unauthorable.

A case action may now grant a flag with a duration through `flags_set_timed`. When the
clock passes it the fold removes the flag and **re-checks transitions**, so a case can
author "when the drug is no longer acting, and nothing else was done, deteriorate" and
have it fire with the resident sitting still. Everything in the condition language reads
it, which is the point: one mechanism, and tags, prompts, prerequisites, transitions,
consultant tiers and content keys all see it without any of them being touched. Section 4
is unchanged, which is the test any addition here has to pass.

Grants combine by three rules, all of them because a flag is shared state more than one
action can write: a permanent grant absorbs a timed one in either order; a timed grant
extends to the later deadline, so a repeat dose refreshes rather than shortening; a lapse
is not an action, costs nothing, and appears in no timeline.

**Vital effects gained `onset_seconds`,** so a drug can take time to work and not only
time to stop. It and `duration_seconds` are both measured from the administration, which
is one rule rather than two, and the validator refuses a duration that does not outlast
its onset and prints every effect's window as a note.

**Design 2.8 and authoring 6.4 are the part a future author needs.** Four constructs now
touch time or move a number, and the failure mode is not that one is broken but that an
author reaches for the wrong one. They are set out side by side against the question that
separates them, which is what else in the case has to know, with worked examples of the
choice. Design 2.9 and authoring 6.5 state plainly what none of them can do: no dose
dependence, no condition can test a vital, results never see an effect, and content keys
never vary with the clock.

**The chart reads newest first, and carries what the nurse asked for.** The panel is read
during the case to answer "what just happened", and oldest-first put that answer at the
far end of a growing scroller, or at the bottom of the last column in the expanded
multi-column layout, which is the hardest place on it to find.

Her line is the only thing in the interface that is overwritten rather than added to, so a
resident working in a tab lost every prompt they were not looking at. Prompts and
deterioration narrations now enter the chart; the four kinds that would have doubled an
existing row do not. A blocked attempt gained the prerequisite message as its body, which
had lived only in the header line that scrolls away.

**The debrief says what was acting and for how long.** Timed mechanics are the one thing a
resident cannot reconstruct from the chart, because nothing is entered at the moment
something wears off. Rendered only when the case uses them.

**The splash screen shows the arrival vitals,** read from the first authored phase. A
handover artifact, not the monitor: static, no cosmetic variance, on a pale panel rather
than in the monitor's dark, and with no caption saying they are not live, since the
heading is past tense and the dark monitor a few seconds later says the rest.

**CHFE's EMS handover now reports the saturation** ("still only holding 87% on six litres
by nasal cannula"), and validator rule N was rewritten to allow it. The rule used to warn
about any vital sign in a handover because the monitor carried the same numbers and would
contradict them within a minute; that reason stopped being true when the monitor was gated
on being attached. The blanket warning is now a note, and in its place is the check the
old rule was really aiming at: a saturation quoted in the handover that disagrees with the
one the case starts from.

Rationale record: `docs/decisions/timed-mechanics.md`.

Sections changed: design 0, 2.6, 2.7, 2.8, 2.9, 12, 13.1, 13.1a, 17. Authoring 0, 6.2,
6.3, 6.4, 6.5, 6.6, 14.3.

## engine/

**`engine.js`: the flag grant ledger.** `st.flagGrants` records, per flag, whether an
action has granted it permanently and the latest deadline any timed grant runs to; the
flag is removed only when no live grant remains. A `flag_expire` event joins the same
schedule as prompts, results and deadlines, and re-checks transitions when it fires.
`st.flagExpiries` is what the debrief and the tests read.

**`engine.js`: completion is recorded in one place.** Pre-existing defect found while
adding the above. `st.complete` was set after the `checkTransitions` call in `applyLog`
only, so a case authoring a time-guarded transition into `case_complete` reached the phase
without the run ever being marked complete, and every new kind of timed event reopened the
same hole. It now lives in `enterPhase`.

**`engine-tests.js`: the action map is rebound rather than captured.** Pre-existing
defect. `selectCase` builds a new actions object on every call and the suite binds every
packed case in turn, so a reference taken at the top of the file pointed at the first
pack's map for the rest of the run. Everything read off it agreed with the live map, so
nothing failed and the staleness was invisible until a test tried to write to it.

**`engine-tests.js`: mechanics no case uses yet are exercised anyway.** The harness
installs a synthetic action and a synthetic transition on the loaded case, runs the
assertions, and removes them, asserting at the end that it left the case as it found it.
Expiring flags, onset, refresh-on-redose, permanent absorption in both orders, the clamp
at 0 and 100, and a transition firing on a lapse with no further action taken, plus the chart's ordering, its nurse-kind filter and the vocabulary that
filter depends on. 163 checks against each case, up from 136.

**`validator-tests.py` is new.** Negative tests for the validator: break a clean case one
way, assert the rule fires, throw the copy away. Half the checks are the inverse, that a
rule must NOT fire on correct authoring, and that half is the one that matters over time,
since a validator that shouts at a legitimate case teaches authors to ignore it. 26 checks
against each case. It is what found the stale action map.

**`validate_case.py`: rule W, and rule N rewritten.** Rule W covers expiring flags: bare
identifier, positive duration, no permanent grant of the same flag on the same action,
state-changing, and something in the case actually reads the flag. It warns when a flag is
granted with a duration by one action and permanently by another, and when a clinical tag
reads an expiring flag, since the critical-action expectation is fixed at phase entry and
will not follow the tag.

**`ui.js`: arrival vitals on the splash, and a debrief block for timed mechanics.**

---

## System design v0.7, authoring requirements v0.6

**The monitor is dark until the resident attaches one.** Vitals and the heartbeat appear
only after an action carrying the action catalog's new `reveals_vitals` capability has
been taken, which is `attach_monitor` and nothing else. Before that every cell reads a
dash and the room is silent. Attaching a monitor had been a recommended action with no
perceptible consequence, which is an action a learner is entitled to skip; the numbers
were on screen before anyone had done anything to obtain them.

This is display gating only. The fold computes the vitals from the first second, every
transition and every result is unaffected, and no case can move the gate or switch it
off, because the capability is a catalog field rather than a case flag. The nurse's
prompt tone is not gated: it is a person speaking rather than equipment.

**An action may move a vital.** `vital_effects` on a case action adds a delta to one
authored vital for as long as the effect is acting, with an optional `duration_seconds`,
an optional `while` guard in the ordinary condition language, and a `key` that decides
what does not stack. A phase is entered once and holds, so it could not express thirty
seconds, could not express an effect that ends when the drip is stopped, and could not
express a drug that changes the patient without changing the number being watched.

Vitals do not enter the condition language, for the reason time does not: the per-key
review matrix stays reviewable only while every rule projects over phase, flags and
study state. Effects are display and audio only, exactly as the phase-boundary ramp
already was, and carry the same accepted inconsistency: a result freezes at the phase's
authored numbers while the monitor beside it shows the effect.

**CHFE's oxygenation arc was rebased, and this changes what the case teaches.**
`stabilizing` and `improving` come down from 93 and 96 to the arrival value of 87, so
positive pressure supplies the only durable gain (+3, while not intubated), a nitrate
supplies a five-point excursion for thirty seconds from either route on one shared key,
and furosemide supplies none. A resident who reaches for the diuretic first watches the
saturation not move while the heart rate, pressure and respiratory rate improve. That is
the case's second learning objective made mechanical. It is also an approximation over
an eight-minute horizon and a reviewing physician should be given the chance to reject
it.

**A question the patient did not understand is no longer a chart entry.** The fallback
answer stays on the History tab, where the resident can see which phrasing failed, and
does not enter the running chart. Case-agnostic: the readout already recorded the
matched topic and is null exactly when the fallback answered.

**The nurse has a face.** A portrait sits to the left of her line in the header. It is
the only picture of a person in the interface: the patient stays a silhouette used as a
CSS mask, because a drawn patient face would assert an appearance the case did not
author, and nothing clinical is read off the nurse. The portrait sits outside the violet
voice rule rather than inside it, because that rule marks speech and marks the same
thing in the chart feed where there is no portrait; the picture answers who and the rule
answers what. `engine/nurse-avatar.txt`, 240px square quantised to 96 colours, 32 KB,
with the source kept in `engine/assets/` and the crop command in `build_simulator.py`.

**Stabilization opens by default.** One entry in a new `defaultExpanded` map, so the
three acts that begin a resuscitation, one of which now gates the monitor, are not
behind a click. A **Nursing** group was added below it in the catalog with droplet,
contact and airborne precautions, warming measures and cooling measures. Author-supplied
rather than transcribed; each sets a flag of its own name and asserts nothing clinical.

Rationale record, including everything rejected:
`docs/decisions/monitor-gating-and-vital-effects.md`.

Sections changed: design 0, 2.6, 3.1, 8.3, 8.4b, 8.5, 12, 13.1. Authoring 0, 6.1, 6.2,
14.3.

## engine/

**`engine.js`: monitoring and vital effects in the fold.** `st.monitoring` is set the
first time an action carrying `reveals_vitals` is taken. `st.vitalFx` records one entry
per administration of an effect-bearing action; `activeEffects` reduces those to what is
acting now, one per key, and `effectiveVitals` adds them to the phase baseline and
clamps. Terminal phases are exempt. Nothing schedules an expiry, so an effect lapses
correctly on replay from any starting point.

**`ui.js`: the ramp now tracks the effective vitals.** The re-arm test is the target
itself rather than the phase id, because an effect changes the numbers without changing
the phase, so an effect starting or lapsing travels over five seconds exactly as a phase
change does. Vital cells and the trace are gated on `ST.monitoring`. The chart feed
drops speech readouts with no matched topic. `expandedOf` seeds from
`SHARED.defaultExpanded`.

**`ui.js`: a filter now opens its groups on the same render.** Pre-existing defect. The
expansion was applied after the markup was built, so it landed one render late, and it
mutated the expanded set, so clearing the filter left groups open that the learner had
never opened. A filter now forces its surviving groups open while it is set and mutates
nothing.

**`audio.js`: the heartbeat is the monitor's sound.** Silent until `ST.monitoring`, and
derived from `ST.vitals` so a transient rise in saturation is heard as well as seen. The
prompt trill is unchanged.

**`validate_case.py`: rule V.** Vital named, delta numeric, duration positive, `while`
parses, no key shared across two vitals, no effect on a non-state-changing action. The
rebasing check warns only for unguarded effects and reports guarded ones as a note,
because deciding whether a guard makes a phase unreachable is deciding reachability.

**`engine-tests.js`:** monitor gating, vital effects, interview readout shape, and the
`defaultExpanded` and `groupOrder` maps naming groups that exist. 136 checks against each
case, up from 91 and 118.

## catalog/

**`reveals_vitals` on `attach_monitor`**, and a **Nursing** group of five entries under
Stabilization. 295 entries, up from 290.

---

## System design v0.6, authoring requirements v0.5

**Time-guarded phase transitions.** A transition rule may carry `after_seconds` and fires
when the deadline passes with its guard still true. This removes the invariant that an
untreated patient never changes, which had made a category of case unauthorable:
meningococcal sepsis, anaphylaxis, status epilepticus, tension pneumothorax, an untreated
occlusive infarct. The previous workaround was to hang the deterioration on some action
the resident might take, which attributes an omission to a commission.

Time does not enter the condition language and will not. It lives in a named field on one
kind of rule, so content keys, tags, prerequisites and interview answers still project
over phase, flags and study state, and the per-key review matrix is unchanged in shape.
That was the design constraint, not a happy accident.

Three patterns are supported: deterioration on inaction with a negative guard, a delayed
consequence of an action through `measured_from: "guard_true"`, and scheduled natural
history with no guard at all.

Deterioration deadlines are deliberately not scaled by difficulty. Scaling them would
make hard mode more forgiving at the same time as the later prompts make it less
forgiving, and the mode would stop meaning anything.

Rationale record, including everything rejected: `docs/decisions/time-driven-transitions.md`.

Sections changed: design 0, 2, 4, 5, 7, 10, 11, 13, 14, 15, 17. Authoring 0, 3.1, 3.3, 4,
5, 9, 10.6, 13, 14, 15, 16.

## engine/

**`engine.js`: time-guarded transitions in the fold.** Two new pieces of fold state, a
`checkTransitions` that consults a deadline, deadlines scheduled as derived events
alongside prompts and results, and a `deadline` case in `applyEvent`. A rule without
`after_seconds` behaves exactly as before, so CHFE is unaffected. A new nurse utterance
kind, `deterioration`, carries the transition's narration; it is the only place in the
system where a nurse line may describe a trajectory, and putting it on its own channel
keeps the no-trajectory assertion on prompts valid. A new `timeFires` record lets the
debrief name which deadline expired rather than only that the patient ended up somewhere
bad.

**`engine.js`: a covered entry no longer prompts or is expected.** `also_covers` exists so
that a tag cannot be escaped by choosing a sibling agent. It was also handing the covered
entries the covering action's prompt and its critical expectation, so the four crystalloid
entries prompted four times for one act and consumed the whole per-phase prompt cap
between them. That was suppressing the glucocorticoid prompt in MGCA and leaving a
deterioration unwarned, which is precisely what the cap must never do. Covered entries now
keep the tag, the halt reason and the debrief note, and the covering action alone prompts
and is expected. This also removes three phantom entries from CHFE's omissions list.

**`validate_case.py`: the six time-transition rules.** A thirty-second floor, a mandatory
preceding prompt with twenty seconds of lead, an error on a prompt stranded past the exit,
an explicit opt-in before the clock may end a case, a ban on a time-driven ending reusing
the shared `halted` phase, and cycle detection over time edges. Ten seeded defects were
each caught.

**`sim_runner.py`: a clock, and equivalence groups.** A scenario step may be
`{"wait": 120}`. Steps naming a covered sibling now resolve through `also_covers`, which
they previously could not, so group coverage was untestable; CHFE gained three scenarios
walking the crystalloid siblings its harmful tag claims. A step naming an action the case
does not hold is now reported rather than silently discarded.

**`engine-tests.js`: updated for v0.6.** `mode changes only the prompts, not the phase`
asserted the phase was still the starting phase after 300 seconds of inaction, which was
only true while no case could deteriorate. It now asserts what it was for, that both modes
produce the same phase sequence. A new generic section walks the do-nothing path and
checks that every deterioration is preceded by a prompt that **actually fires**, which is
the thing the validator cannot see.

**`build_simulator.py` and `shell.html`: the welcome screen** replaces the case picker and
keeps the id `picker`, so `chooseCase`, `backToPicker` and the `[data-case]` delegation are
untouched. Seventy per cent hero, thirty per cent case board built as an ED tracking board:
aligned columns, a status bead, sticky group headers, search on `/`, chips generated from
the data, arrow keys and Enter. The splash gained a real back control at the top of the
card. Two new optional card fields, `metadata.complaint` and `metadata.category`, both
degrading. Three new build-time assets.

## cases/

**MGCA is new.** Meningococcaemia with septic shock, early DIC, acute kidney injury and
adrenal crisis from bilateral adrenal haemorrhage, in a 21-year-old woman. Six clinical
phases, 124 case actions, 41 interview topics with 492 variants, five time-guarded
transitions of which one is terminal. Written directly in catalog ids, so all 123 binding
rows are exact and none needs a clinical signature.

Seven clinically wrong resolutions were found by reading the review matrix, and none
raised an error anywhere: a cerebrospinal fluid glucose that was a normal ratio on one
path and frankly low on another, a platelet count that rose across a transition, the same
defect in the coagulation panel and the D-dimer, a creatinine that fell in minutes, a
cardiac ultrasound that recovered systolic function, a lumbar puncture permitted in the
vasopressor-dependent phase, and four consultants quoting arrival values in phases where
they differ.

**CHFE: the two non-invasive ventilation actions consolidated into `niv_bipap_cpap`.** They
both bound to one catalog entry, and because one entry resolves to one case action the
second was never in the action surface: its tag, its debrief note and its two references
were unreachable. The merged note carries both teaching points, including the one that was
lost, that bilevel and continuous pressure are equivalent here and that bilevel is often
preferred in the hypercapnic patient. This also fixed a scenario passing for the wrong
reason: it named `niv_bipap`, the engine discarded the step silently, and the scenario
reached `presentation` while expecting `stabilizing`.

## catalog/

`reference_case_id_map` still mapped both old NIV ids, in the generated catalog and in
`build_catalog.py`. Consolidated.

---

## Outstanding

- Section 14.3 sign-off on both cases. Neither is usable with learners.
- MGCA's interview matcher returns 22 of 37 held-out phrasings, with four wrong topics on
  topics that change management, and refuses only one of six out-of-scope questions. The
  fix is variant expansion written against fresh phrasings; the held-out set stays held
  out.
- The engine drops a log entry naming an action the pack does not hold without applying,
  blocking or logging it. `sim_runner.py` now reports it; the engine should refuse it.
- MGCA's `halted` phase and CHFE's are both alertness-gated terminal phases not named in
  their global interview rules. Unreachable today, a defect the moment either stops being
  terminal.
- Whether the clock should pause while a resident reads, and whether deterioration pacing
  should get a global multiplier. Design section 14, open decisions 9 and 10.
