# MGCA author's seed

Unlike CHFE, this case had a real seed. The author supplied the diagnosis, six clinical
states with their vital signs, the laboratory values in each state, the transition
triggers, the five critical actions, the constraint that the lumbar puncture happens only
if the patient is not hypotensive, and the patient's age and sex.

Everything else was expanded by a language model and is unsigned. The division is recorded
in `MGCA-review-packet.md` section 1. The seed-to-phase mapping below is section 4 of the
same document, kept here so the seed can be read on its own.

---

## 4. Your six states, and where the engine could not follow them

| Your state | Phase id | How it is entered |
|---|---|---|
| 0, initial presentation | `presentation` | arrival |
| 1, early improvement | `improving` | antibiotic, glucocorticoid and volume all given |
| 2, adrenal crisis progression | `adrenal_crisis` | fluid or dextrose given, glucocorticoid not |
| 3, progressive meningococcaemia | `progressive_meningococcaemia` | glucocorticoid and volume given, antibiotic not |
| 4, frank septic shock | `frank_septic_shock` | intubation, **or the clock at 210s from either deterioration branch** |
| 5, stabilised septic shock | `stabilized_shock` | antibiotic, glucocorticoid and vasopressor all present |

**State 4 is now implemented as you specified it.** The previous draft of this packet recorded that
"continued progression despite inadequate or delayed treatment" could not be authored, because the
engine had no time-driven transitions, and that the phase was reachable only by intubating. That
substitution misattributed the deterioration to something the resident did rather than to something
they omitted. Time-guarded transitions were added to the engine for this, and the case now carries
five of them:

| From | At | Fires if | To |
|---|---|---|---|
| `presentation` | 240s | glucocorticoid still not given | `adrenal_crisis` |
| `presentation` | 240s | antibiotic still not given | `progressive_meningococcaemia` |
| `adrenal_crisis` | 210s | glucocorticoid still not given | `frank_septic_shock` |
| `progressive_meningococcaemia` | 210s | antibiotic still not given | `frank_septic_shock` |
| `frank_septic_shock` | 300s | any of the three still missing | `cardiac_arrest`, terminal |

Intubation still reaches `frank_septic_shock` instantly, because that physiology is real and worth
teaching, but it is no longer the only route.

**Two things about this need your decision, and they are the most consequential items in this
packet.**

*The deadlines are clinical claims.* Four minutes without hydrocortisone, four minutes without a
cephalosporin, then three and a half more, then five in refractory shock before arrest. Those numbers
are compressed against real disease tempo, in the same way the five-second laboratory turnaround is,
and they are model output. If you think a patient like this has longer or shorter, change them; they
are single integers in the phase transitions.

*This case can now kill the patient without the resident touching her.* A completely passive run
arrests at 750 seconds against an estimated runtime of 600. That required an explicit per-transition
opt-in, which exists precisely so it cannot happen by accident, and the arrest is a separate terminal
phase with its own `timeout_reason` rather than the shared `halted` phase, so the debrief attributes
it to the omission rather than to anything the resident did. It is defensible: untreated fulminant
meningococcaemia with adrenal haemorrhage kills within hours and your seed asked for progression
toward peri-arrest on failure to intervene. It is still the single thing in this case most in need of
a physician's signature.

*The fairness guarantee, and what it does not cover.* The validator enforces that every deterioration
is preceded, in the same phase, by a nurse prompt naming the missing treatment at least twenty
seconds earlier. Here the margins are much wider than that: the antibiotic prompts at 45 and
escalates at 90 against a 240-second deadline, the hydrocortisone at 70 and 140 against the same. A
resident who acts on the second prompt has a hundred seconds to spare. What this does not cover is
hard mode, which multiplies prompt deadlines by three and deliberately does not slow deterioration
down, so in hard mode the hydrocortisone escalation at 420 seconds lands after the phase has already
ended. That is the intended behaviour of hard mode and the reasoning is in system design 17.1, but
you should confirm you accept it for this case.

**Second consequence you should decide on: the adrenal crisis branch will be entered by most good runs.** Your state 2 trigger is fluid or dextrose without hydrocortisone. Fluid resuscitation is a critical action and it will almost always precede the chemistry panel that reveals the adrenal component, so a resident doing sepsis care correctly enters the deterioration branch. The phase ordering mitigates this: if the antibiotic and the hydrocortisone are already in when the fluid finishes, the case goes straight to `improving` instead. So the branch discriminates on order rather than on competence, and a resident who sends the chemistry, reads it, gives hydrocortisone and then gives fluid avoids it entirely. Whether that is the lesson you want, or whether it unfairly penalises the conventional sequence, is your call.

---
