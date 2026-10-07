# TSS seed and provenance

Menstrual staphylococcal toxic shock syndrome in a 22-year-old woman. Drafted by a language
model on 6 October 2026 at the request of Aakash Setty. **No physician has reviewed this
pack.** Authoring requirements section 17 applies: the AUTHOR-ONLY fields were generated,
so a physician is authoring the ground truth in review. Read every number as a proposal.

## 0. What a person decided

Aakash Setty, 6 October 2026, in answer to four questions asked before drafting:

| Question | Decision |
|---|---|
| Which antibiotic orders count | Vancomycin plus clindamycin is the target. A broad agent added is accepted without penalty. Missing clindamycin is noted in the debrief only and is not scored |
| Discharge as gastroenteritis | She faints on standing and the case continues |
| Response to removing the tampon | It stops the decline. No dramatic rebound |
| When norepinephrine is expected | Once the mean pressure stays under 65 after about 30 mL/kg. More fluid without a vasopressor is allowed and she keeps sliding |

He also approved, in outline, the patient, the story and the three learning goals in the
case plan written in the same conversation. Everything else below is model output.

## 1. Learning goals, and what in the case makes the learner act on each

| Goal | What the case contains so the learner meets it by deciding |
|---|---|
| Recognize shock in a young patient who compensates | She talks, apologizes and blames a takeout meal. Only the monitor, the capillary refill and the lactate say otherwise. Discharge is available and has a consequence |
| Find the source and remove it | Nobody mentions her period. The history and the pelvic examination are available and never prompted on arrival. Her course changes only when the tampon is out |
| Resuscitate toxin-mediated shock | The first liter helps and the help fades. Further fluid buys six points for a minute. A vasopressor is what holds her |

## 2. Phases

Six clinical phases and one terminal. No halted phase, no arrest, nothing tagged harmful.

| Phase | HR | BP | RR | SpO2 | T | Reached |
|---|---|---|---|---|---|---|
| presentation | 128 | 94/58 | 22 | 97 | 39.4 | arrival |
| fluid_responsive | 114 | 104/62 | 20 | 98 | 39.2 | ten seconds after any crystalloid bolus |
| hypotensive | 138 | 78/42 | 26 | 95 | 39.6 | fluid response fades at 150 s. Or no fluid by 300 s. Or five seconds after an attempted discharge |
| supported | 124 | 92/50 | 24 | 96 | 39.5 | fluid and a vasopressor, tampon still in |
| profound_shock | 148 | 66/32 | 30 | 92 | 39.8 | hypotensive 240 s without both fluid and a vasopressor. Or supported 270 s with the source in |
| stabilizing | 116 | 98/56 | 22 | 97 | 39.1 | fluid, a vasopressor and the source out |

The intended path passes through `hypotensive`. That follows the fourth decision above.

## 3. What needs a physician's signature first

1. Every vital sign in the table above.
2. The five clocks: 300, 150, 240, 270 and 5 seconds.
3. Every laboratory value and reference interval in `case_3_content.py`.
4. That removing the tampon stops the decline within ten seconds of case clock.
5. That she always faints on an attempted discharge.
6. The tags in `case_2_actions.py`, above all: nothing harmful, rate control and a
   diuretic only discouraged, intubation discouraged until she is obtunded.
7. Every sentence in every debrief note. Notes that lean on a guideline or trial carry
   `[UNVERIFIED]`.

## 4. Checked, and by what

An independent model pass on 6 October 2026 opened the CDC 2011 toxic shock case
definition, the Surviving Sepsis Campaign 2021 text, the SCCM guideline page, StatPearls
and the Internet Book of Critical Care, and compared the pack against them. It was not a
physician review. It found 18 problems and the ones that could teach something false were
fixed the same day:

- The lumbar puncture note said she had no headache and cited platelets of 98 as a reason.
  She has a mild headache and 98 is not a contraindication. Rewritten.
- "A supple neck makes meningitis unlikely" and "the rash decides it" were too certain.
  Softened.
- The arterial gases were not consistent with their own pH and pCO2. Bicarbonate lowered.
- Creatinine was 2.2 against an upper limit of 1.2, which does not meet the CDC renal
  criterion of twice the upper limit. Now 2.6.
- "The indication for norepinephrine" is now "an indication", and the note no longer
  claims 30 mL/kg was given when only one bolus was.
- Six smaller contradictions between notes and authored values.

Confirmed against an opened source: the CDC criteria and thresholds, that her findings
meet a probable case once she is hypotensive, 30 mL/kg as a weak recommendation, a mean
pressure target of 65, norepinephrine first, peripheral vasopressors as acceptable short
term, blood culture yield under 5 percent, clindamycin for toxin suppression on non-trial
evidence, weak evidence for immunoglobulin, and desquamation at one to two weeks.

Not verified by anyone: the SOAP II figures behind the dopamine note, that most menstrual
toxic shock is methicillin-susceptible, lactate over 4 as a risk marker, and the CT
appearance of a tampon. The Surviving Sepsis guideline has a newer edition than the one
opened.

## 4a. Approved by Aakash Setty, 6 October 2026

After reading the summary of the finished case he approved these five as drafted:

1. The overlap with MGCA stands. The two cases are a deliberate pair.
2. The five clocks: 300, 150, 240, 270 and 5 seconds.
3. Cool hands with a four-second capillary refill in a flushed patient.
4. Rate control is discouraged and does not halt the case.
5. The dopamine note and the note that most menstrual toxic shock is
   methicillin-susceptible stay as written, with their `[UNVERIFIED]` markers.

This is approval of the design choices. It is not the section 14.3 sign-off, and the
laboratory values, tags, notes and interview are still unreviewed.

## 5. Open questions for the physician

1. Her hands are cool with a four-second capillary refill while she is flushed. Early toxic
   shock is classically warm. The case treats her as both dry and vasodilated. Is that the
   patient you want?
2. Pulse pressure is 36 to 42 in every phase. A wider one would read as more distributive.
3. Hemoglobin 14.9 on day five of a period. Plausible as hemoconcentration. Anemia is
   also described in toxic shock.
4. No calcium is authored. Hypocalcemia is described in toxic shock.
5. Would she really go to the beach with a fever of 102 and six stools a day? The beach
   exists to give her an explanation for the rash.
6. This case and MGCA are both a young woman with fever, a rash and shock. MGCA asks about
   tampons as a negative. Played in sequence they are a deliberate pair. Played back to
   back a learner may guess. Decide whether the welcome list should separate them.
7. Linezolid is not in the catalog. Some centers prefer it to vancomycin here.

## 6. Engine and catalog changes made for this case (v0.21)

- Catalog: `remove_vaginal_foreign_body` under Procedures.
- Engine: `handoff.disposition_intercepts` and `hidden` case actions, so one disposition
  can have a consequence instead of ending the run.
- Engine fix, found by playing this case in a browser: a delayed consequence could fail to
  fire until the next click, in every pack. See CHANGELOG v0.21.
