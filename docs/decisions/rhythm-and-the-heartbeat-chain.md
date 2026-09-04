# Making the heartbeat uneven

Design v0.9. One change, and three things found while making it.

Kept for what was rejected. The current behaviour is in `docs/system-design-v2.md`
section 8.5 and in `docs/case-authoring-requirements.md` section 6.0a. This file is not a
source of truth for how the system behaves.

---

## 1. The problem

The third case is atrial fibrillation. Its ECG report says the R-R intervals are
irregularly irregular, its cardiovascular examination says the first heart sound varies in
intensity from beat to beat, its whole management turns on recognising the rhythm, and the
monitor beat a metronome. A resident could hear a perfectly even beat while reading that
the rhythm was uneven, and the sound was the more immediate of the two.

That is the same class of defect as a nurse prompt describing a trajectory over static
vitals, and it has the same property: no validator can see it, because each half is
correct on its own.

**Decision.** A phase may declare a `rhythm` from a closed vocabulary. The audio module
reads it. Nothing else changes.

---

## 2. Why a phase field, and not any of the alternatives

### Rejected: deriving it from the diagnosis

The obvious shortcut, and it puts clinical knowledge in `engine/`. The engine would have
had to hold a map from diagnosis catalog ids to rhythms, which is an appropriateness
judgement of exactly the kind section 3 of the design keeps out of the catalog and out of
the engine. It also fails on the first case that needs it: a patient can be in a rhythm
the final diagnosis does not name, and this one is in atrial fibrillation in the phase
where the case's diagnosis is still unknown to everybody including the resident.

### Rejected: a boolean, `irregular: true`

Cheaper to write and wrong at the first extension. Bigeminy, trigeminy and Wenckebach are
regularly irregular: they have a period, and a listener locks onto them. A boolean would
have collapsed two audibly different things into one and there would have been no
non-breaking way to separate them later. A named vocabulary costs one string and leaves
the door open.

### Rejected: putting it in `appearance`

`appearance` is the fixed set of values the visual renderer computes a patient from, and
authoring section 6 says so and tells authors to escalate rather than add to it. A rhythm
drives neither pixels nor one of the six numbers. It sits beside both.

### Rejected: a per-case audio configuration

A case could have carried its own jitter parameters. That would have made the sound of a
rhythm a case-level clinical claim, so two cases could have disagreed about what atrial
fibrillation sounds like, and each would have had to be reviewed separately. The
parameters are global and the case chooses only which of two names applies.

---

## 3. The interval model, and the one thing that had to be got right

Intervals are drawn as a shifted exponential, `mean * (s + (1 - s) * Exp(1))`.

**The mean has to be preserved exactly, not approximately.** The monitor shows a heart
rate. If the average of the sounded intervals is not that rate, the case is showing one
number and sounding another, and a resident counting the beat against the display would be
right to think the simulator was broken. `E[Exp(1)] = 1`, so the expectation is the
authored interval with no correction term. That is the whole reason for this shape rather
than, say, a uniform or a Gaussian jitter with a clamp.

**The floor is enforced by raising `s`, not by clamping the draw.** This was the first
version's mistake and it is not visible without doing the arithmetic. A fixed 240 ms floor
applied as `Math.max` after the draw pushes about a third of the beats at 220 bpm up onto
the floor, and every one of those is an interval that should have been shorter, so the
mean drifts above the authored rate exactly where the rate matters most. Raising `s`
instead narrows the distribution and leaves the mean untouched. It also happens to be the
physiologically right direction, since the interval distribution really is compressed at
high ventricular rates by concealed conduction into the atrioventricular node, but the
reason for the change was arithmetic and the physiology was a bonus rather than the
argument.

**The floor doubles as a collision guarantee.** The second sound of a beat sits 160 ms
behind the first. No interval below about 200 ms could exist without one beat's dub
landing on the next beat's lub, which sounds like a fault rather than like a fast rhythm.
At 240 ms there is no possible collision, and the test suite asserts it rather than
trusting it.

### Rejected: modelling correlation between consecutive intervals

Real R-R series in atrial fibrillation are not perfectly independent. Adding correlation
would have been unwarranted: the case is not measured against a rhythm strip, nobody can
hear a lag-1 autocorrelation, and it would have turned an authored teaching parameter into
something that looks like a model and would then be believed as one.

### Rejected: a seeded generator, so every playthrough sounds identical

Tempting for reproducibility and wrong for the thing being taught. The point of an
irregularly irregular rhythm is that it has no pattern, and a resident replaying a case
should not be able to learn its beat. Reproducibility is preserved where it is actually
needed, which is the test suite, by asserting the distribution over a large sample rather
than a particular sequence.

---

## 4. The loop had to be rebuilt, and that fixed something else

The beat was a `setInterval` with a fixed period, torn down and rebuilt whenever a
quantised rate or saturation changed. The quantisation existed because a five-second ramp
changes the raw values on every frame, and rescheduling three hundred times over five
seconds restarted the interval on each pass and sounded like stumbling.

An uneven rhythm cannot be a fixed period at all, so the loop is now a chain of
`setTimeout` calls, each beat reading the current vitals and choosing its own successor's
delay. **The quantisation went with it**, and so did the last place the beat could
stutter: there is nothing left to restart. A side effect is that the tempo now follows the
ramp exactly rather than in two-beat-per-minute steps, which is a small improvement to
both earlier cases and was not the reason for the change.

The hazards of a self-scheduling chain are the ones worth naming, because none of them
shows up in a unit of arithmetic:

- **Double scheduling.** Two chains running against each other sound like a subtly doubled
  beat and nothing else. `beatTimer !== null` is the single source of truth for whether a
  beat is pending, there is no second flag to fall out of step with it, and the test suite
  asserts that at most one timer is ever queued while sixty renders a second are firing.
- **Catch-up bursts.** A background tab throttles timers to about a second. A chain that
  compensated for lost time would fire a volley of beats the moment the tab returned. It
  schedules forward from now and makes no attempt to catch up.
- **Restart on every render.** `sync()` is called sixty times a second and now only starts
  a stopped chain or stops a running one. It reads nothing else.

## 5. Three defects found on the way

**A `const` declared inside a direct `eval` does not leak.** The test harness evaluates
blocks cut out of the built file, and `engine.js` had always worked because its top-level
declarations are `function`s. `audio.js` binds itself with `const AUDIO = ...`, so the
harness saw nothing and reported it as a missing fence. The block now hands the binding
back explicitly. Worth recording because the next module extracted this way will hit it.

**The lub-dub gap was fixed at 160 ms regardless of rate.** At 220 beats per minute, which
the validator permits, the interval is 273 ms and the second sound plus its decay ran to
270. That was already true before this change and nobody had authored a case fast enough
to hear it. The gap is now compressed at short intervals, which changes nothing at any
rate either earlier case authors.

**The trace was drawing P waves.** The ECG trace is decorative and its own comment says so,
and it was going to draw six evenly spaced complexes with a P wave in front of each one on
a monitor whose sound had just been made uneven. It follows the same field now: uneven
spacing, no P wave, deterministic per rate so it does not shimmer. It is still decorative,
and the note in section 8.5 says so, because the temptation to read six beats off a screen
as the six beats being heard is real.

---

## 6. What this does not do

- It does not model a rhythm. Every parameter is authored and the provenance note in
  `SHARED.audio.rhythm` says so in those words.
- It does not enter the condition language, for the same reason vitals do not. Nothing can
  branch on the rhythm, and the per-key review matrix is unchanged in shape.
- It does not vary within a phase. The rhythm is a property of the phase, so a case whose
  patient converts needs a phase to convert into, exactly as one whose patient becomes
  hypotensive does.
- It carries no information a deaf resident cannot get. The ECG report and the
  cardiovascular examination both state the rhythm in words, and section 8.5's constraint
  that nothing may depend on sound alone still holds.
