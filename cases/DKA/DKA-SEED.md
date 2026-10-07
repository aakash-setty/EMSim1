# DKA seed and provenance

Mild diabetic ketoacidosis with a potassium of 3.1 in a 24-year-old woman with type 1
diabetes and gastroenteritis. Drafted by a language model on 6 October 2026 at the request
of Aakash Setty. **No physician has reviewed this pack.** Authoring requirements section 17
applies. Read every number as a proposal.

## 0. What a person decided

Aakash Setty, 6 October 2026:

| Decision | What was decided |
|---|---|
| The case | Mild ketoacidosis with some hypokalemia, with a correct order of steps and feedback from several interventions that could have been chosen |
| Insulin threshold | Hold insulin until the potassium is above 3.5 |
| Clock and death | A case with no clock that harms her and no death is acceptable |
| Catalog | Add beta-hydroxybutyrate, subcutaneous insulin and oral potassium |
| Sources | Do a source pass before writing |
| Plan | The five-phase plan presented in conversation |

Everything else is model output.

## 1. Sources, and how far each was read

| Source | How it was read | What it supplied |
|---|---|---|
| Umpierrez et al., Hyperglycaemic crises in adults with diabetes: a consensus report (ADA, EASD, JBDS, AACE, DTS), 2024 | A mirror of the Diabetologia PDF, through a summarizing tool, by the author and again by an independent checking pass. Figure 4 was not readable. The publisher's sites refused the request | Severity table, potassium threshold and rate, fluid, insulin, dextrose, bicarbonate, phosphate, resolution, level of care |
| UBC RTVS simulation case, Basic Diabetic Ketoacidosis | Opened through the same tool | What another educator's case asks for: glucose, monitor, ECG, lines, fluid, insulin, repeat labs, and a potassium decision before potassium is added |
| FDA drug safety communication on ondansetron and the QT interval | Opened by the checking pass | 6 ms at 8 mg and 20 ms at 32 mg intravenously. Correct potassium and magnesium first |
| Cleveland Clinic Journal of Medicine review of the 2024 report | Opened by the checking pass | Agreement on potassium, bicarbonate, phosphate and level of care |
| EMCrit IBCC chapter on ketoacidosis | Summary, by the checking pass | US practice that differs: a 3.3 threshold, faster potassium |
| MedEdPORTAL case (PMC5491337), 2009 ADA statement, StatPearls | Could not be opened | Nothing. Statements about the 2009 threshold of 3.3 are from memory |

Nobody in this chain has read the publisher's text of the consensus report unfiltered. A
physician should read its Table 2 and Figure 4 before this case is used.

## 2. Learning goals and where each is acted on

| Goal | Source | Where the learner acts on it |
|---|---|---|
| Recognize ketoacidosis in a vomiting patient and grade it | Consensus report diagnostic criteria and Table 2. UBC case | The triage note does not mention diabetes. Glucose, gas, chemistry and ketones are orders the learner chooses |
| Know the potassium before insulin, and replace it first when under 3.5 | Consensus report, potassium section | Insulin is available from the first second and shows what it does. Potassium first leads to a different patient |
| Fluid first, and what it does not fix | Consensus report, fluid section | Fluid moves the heart rate and the glucose. A repeat chemistry shows the gap unchanged |
| Insulin without a bolus, by either route | Consensus report, insulin section | Three insulin entries, tagged by phase |
| Plan what follows insulin | Consensus report, dextrose and resolution | A follow-up asks for the dextrose plan. Stopping insulin in the treated phase is discouraged |

## 3. The stories

- Treated well: fluid, potassium found low and replaced, level repeated, insulin, dextrose plan.
- Insulin first: potassium 2.6, weakness, a longer QT. Holding insulin and giving potassium recover her, and insulin restarts.
- Bicarbonate: no change to see. A repeat chemistry shows the potassium at 2.9.
- Fluid only: she looks better and the gap is unchanged.
- Left alone: nothing changes in ten minutes. The nurse prompts.

## 4. Phases

| Phase | HR | BP | K | Reached |
|---|---|---|---|---|
| presentation | 112 | 104/64 | 3.1 | arrival |
| potassium_replaced | 112 | 104/64 | 3.6 | 20 seconds after intravenous potassium, if insulin has not acted first |
| treated | 104 | 106/66 | 3.7 | 10 seconds after an infusion or subcutaneous insulin, from potassium_replaced or recovering |
| potassium_falling | 118 | 102/62 | 2.6 | 10 seconds after any insulin given on arrival |
| recovering | 112 | 104/64 | 3.6 | 20 seconds after insulin is held and potassium given |

Authored rates are without fluid. A crystalloid bolus takes ten off the rate and adds six
to the pressure in every phase.

## 5. Changed after the independent check

- Ondansetron adds 5 ms to the QTc, not 20. Twenty is the figure for a 32 mg dose.
- The insulin bolus note was garbled and now follows the report's sentence.
- Phosphate is normal on arrival (3.4), and the note gives the report's cutoff as printed.
- Every blood gas is now consistent with the Henderson-Hasselbalch equation.
- Creatinine 1.2 is flagged abnormal for a 58 kg woman.
- Step-down is still the correct disposition, and the explanation now says the potassium
  is the reason. The report's own table suggests a regular or observation unit for mild
  ketoacidosis.
- Waiting for potassium now has a visible cost: ketones 4.2 to 4.6, bicarbonate 16 to 15.
- Bicarbonate lowers the potassium by 0.2, not 0.3.
- The arrival ECG is subtler, because many tracings are normal at 3.1.
- Wording softened on basal insulin, abdominal pain, lipase and the patient's weakness.

## 6. Known gaps

- A learner who gives both an infusion and a subcutaneous dose before holding insulin has
  already set the restart flag, and leaves the recovering phase without restarting.
- Doses are not modeled, so the rate of potassium cannot be taught by doing.
- Insulin ordered 11 to 19 seconds after potassium, with no repeat level, reaches treated.
  Potassium lands at 20 seconds before the early-insulin rule's 10 seconds are up. A scenario
  records it.
- Glargine is recommended once she is treated and unscored before that. It never lowers the
  potassium. Whether an early basal dose at 3.1 should be marked discouraged is a physician's call.
- The potassium threshold in many US protocols is 3.3. This case uses 3.5 by decision.
- The held-out interview questions were written by the same author as the variant bank.
