# Drawing the rhythm the monitor is sounding

Design v0.16. One change, the beat clock it forced, and the authoring field it needed.

Kept for what was rejected. The current behaviour is in `docs/system-design-v2.md`
sections 8.4c and 8.5 and in `docs/case-authoring-requirements.md` section 6.0b. This file
is not a source of truth for how the system behaves.

---

## 1. The problem

The trace on the monitor was a static path: six complexes drawn once per phase, redrawn
when the rate or the rhythm changed, with a comment saying it was decorative and a note in
the design saying the beats on screen were not the beats being heard. The v0.9 work made
the beat uneven and made the path uneven to match, and left the note in place because the
path still did not move.

A resident looks at the monitor before anything else, and what they are looking for is
whether it is moving and what shape the complexes are. A picture that does not move is a
monitor that has frozen, and a picture that cannot show a wide complex beside a report
that says the QRS is 180 ms is the contradiction 6.0a describes, seen rather than heard.
DIPH is a case whose clock is the QRS; it had nothing on the wall to show it.

**Decision.** The monitor draws one lead live, at paper speed, with an erase bar, from the
same beat clock the heartbeat sounds. A phase may declare an `ecg` block saying what the
lead looks like. Nothing else changes.

---

## 2. The animation, and why it is that one

A bedside monitor does not scroll. The pen moves left to right, the newest sample is drawn
at the pen, a short blank gap runs ahead of it erasing the previous pass, and at the right
edge it starts again at the left. The last few seconds stay on the screen behind the gap.
That is what was asked for, and the reason it is the right choice rather than a
preference is that it leaves a beat that has just happened where it was: a resident who
heard something odd can look back at it. A scrolling strip carries it away.

### Rejected: scrolling the strip

Cheaper to implement (shift the canvas, draw one column) and it is what a printed strip
looks like. Rejected because it is not what the device being imitated does, and because a
scrolling picture draws the eye continuously in a way a sweeping pen does not, which
matters on a header that is on screen for a whole case.

### Rejected: redrawing the whole path every frame

An SVG path rewritten sixty times a second is the wrong tool for a picture that changes by
a pixel and a half per frame, and it makes the erase bar a special case. A canvas stroked
incrementally is one clear and one stroke per frame.

### Kept, and found the hard way: where the erase band starts

A band that starts at the pen, or one pixel behind it, wipes the antialiased edge of the
previous frame's end cap, and the new stroke's round cap does not quite cover it. The
result is a hairline gap at every frame boundary, which reads as a dashed line at the
slower rates. The band starts one pixel after the pen and the new stroke overdraws that
pixel. Recorded because it is invisible in code and obvious on the screen.

---

## 3. One clock, and why the audio had to give up its own

The heartbeat was a self-rescheduling chain in `audio.js`, carefully built in v0.9 so that
exactly one beat was ever pending and no render could restart it. The trace needed a beat
clock of its own, and the obvious move was to give it one.

Rejected, because two clocks drawing from the same distribution are two rhythms. For a
regular rhythm they drift; for an irregular one they are independent draws. A QRS a
quarter of a second from the beep it belongs to reads as a fault, and an emergency
physician is exactly the person who will notice. The only way two consumers can agree on
when a beat happens is for one clock to tell both.

**The chain moved to the monitor and the audio subscribes.** It runs whenever a case is
running and the patient is on a monitor, whether or not sound is on, because a resident
who has muted the room still has to see the rhythm. The audio decides only whether a beat
it is told about makes a noise, and it checks `on`, the context and the scene itself
rather than trusting the clock to have been told.

### Rejected: the audio keeps the chain and the trace listens

The chain in `audio.js` stops when sound is off or when no gesture has yet created an
audio context. The trace has to draw in both situations, so the clock cannot live behind
either condition. The trace's needs are the superset; the clock lives with the trace.

### Rejected: making the trace a pure function of time

Beats at integer values of a phase accumulator over the ramping rate, with the audio
computing the same function. Elegant for a regular rhythm and impossible for an irregular
one, where each interval is a draw, unless both sides shared a seeded generator, and the
v0.9 record already rejected a seeded generator because a resident replaying a case should
not be able to learn its beat.

### The lookahead, which is the one non-obvious part

A P wave precedes its QRS by the PR interval. If the trace learned of a beat when the beat
sounded, its P wave would already be in the past, drawn as baseline. So each beat books the
NEXT complex, one interval ahead, at the moment it draws the next interval. The first beat
of a chain is drawn without a P wave, since there was no earlier beat to book it from; a
complex booked ahead is shifted, never clipped, if its P would begin before the moment of
booking. On a pause the chain stops and any complex booked for a moment that has not come
is dropped, or it would be drawn on resume beside the restarted chain's first beat.

**What this costs.** The beep plays when the timer fires and the QRS was booked for the
ideal moment, so timer lateness shows as the beep trailing the QRS by a few milliseconds.
Under ordinary load that is well under anything a listener can place. A throttled
background tab would make it seconds, and a background tab pauses the case.

---

## 4. What a phase may say, and why it is that little

The vocabulary is the set of properties a single monitor lead shows and a resident reads
off it: P waves or not, how wide the QRS is, where the ST segment sits, how tall the T is,
the PR and the QTc, and the two patterns with no complexes. It was chosen by asking what
DIPH, AFRVR and a future arrest case would need to show, and stopping there.

### Rejected: extending `rhythm` with morphology-bearing names

`wide_complex_regular`, `ventricular_tachycardia` and the like. Rejected because timing
and appearance are separable: DIPH's seizing phase is a regular sinus rhythm with a
148 ms QRS, and a vocabulary that fused the two would need a name for every combination.
`rhythm` stays the timing; `ecg` is the picture.

### Rejected: naming rhythms at all

`"ecg": "atrial_fibrillation"` would be the shortest thing to write and it puts a map from
diagnoses to pictures in `engine/`, which is the line every prior decision holds. A case
says "no P waves, QRS 88 ms, irregularly irregular" and never says why, for the same reason
it says `irregularly_irregular` and never says atrial fibrillation.

### Rejected: per-case waveform parameters

A case could have carried its own amplitudes. Then two cases could disagree about what a
narrow complex looks like and each would have to be reviewed separately. The amplitudes
and the wide-complex blend are global, with a provenance note saying they are
stylisations, and a case chooses only the properties above.

### Rejected: a second lead, artefact, ectopy, f-waves

Each is a real thing a monitor shows and each is a claim a case would then be making.
None of the four packs needs one, and the seizing phase in DIPH, whose report mentions
both ectopics and movement artefact, says in its `verify` note that the monitor draws
neither. The field is closed; extending it is a decision, not an edit.

### Accepted: the wide complex is a stylisation

The blend from a narrow complex to a wide one follows the ECG generator project's
sodium-channel pattern in lead II: the initial r held short, the extra duration in a deep
broad terminal S drawn as a dome, the J point on its return limb, a discordant T. It was
tuned there to look like exemplar tracings and is not fitted to data. It is one shape of
wide complex among several a real patient might show, and `t_mv` and `st_mv` are the
author's way to move it. This is the weakest claim in the change and the provenance note
says so.

---

## 5. What was authored into the packs, and what needs a physician

Every live phase in every pack was authored from its own ECG report, and the figures are
that report's figures with that report's provenance. Every terminal phase is model output:
`halted` and `cardiac_arrest` phases author vitals and no tracing, so the packs draw a
slow, wide, P-less idioventricular rhythm for generic peri-arrest numbers. Each says in
`verify` that a reviewer who prefers asystole, or a converted sinus bradycardia, changes
one block. The review packets carry an addendum listing them.

MGCA's arrest phase is worth naming: it authors a rate of 26 and a pressure of 44/24,
which is a slow organised rhythm with almost no output rather than fibrillation or
asystole, and the picture follows the numbers. Whether the numbers are what the author
meant is a question for the author.

---

## 6. What this does not do

- It does not enter the condition language. Nothing can branch on the picture.
- It does not vary within a phase. A widening QRS is phases, as a falling pressure is.
- It does not store anything. The trace is display only; a result ordered while the trace
  shows one thing reports the phase's authored ECG.
- It does not draw the mini monitor in the expanded chart header. The numbers there are a
  convenience copy; the trace is in the header where it always was.
- It does not fix the ramp defect found on the way (the first five seconds of a case ramp
  from the previous case's numbers). That predates this change and is recorded in the
  CHANGELOG.
