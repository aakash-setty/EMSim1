# Writing a case discussion

The case discussion is the left column of the debrief, shown after the learner reveals the
answers. `docs/case-authoring-requirements.md` section 10.5 has the engine rules. This guide
has the form, the figures, the voice, the checks and a prompt to start from. It records what
the owner asked for over several rounds on TIDE and TSS on 5 November 2026.

TSS is the model: `Claude outputs/tss-discussion/tss_discussion_v2.py`. Copy that script and
replace its content. Its helpers draw the figures. Its checks read the case's numbers from
the case files, and refuse style slips and markers the learner would see. TIDE follows the same
form (`Claude outputs/tide-discussion/tide_discussion_v6.py`).

Nothing clinical here has been reviewed by a physician unless a SEED names the decision, the
person and the date. Say so in anything you write.

## What it is for

A resident who has just played the case reads it once. They have already seen their own run
in the right-hand column. The discussion should leave them with the three or four ideas that
explain this case, each one they could use on the next patient. It teaches medicine. It does
not retell the case, and it is not a list of guideline lines.

## The form

1. "The case". Two or three sentences: who the patient is, what they have, what happens. Then
   "The right care, in order:" as three or four numbered steps taken from
   `intended_path_note` and the critical actions. Then one line naming the traps from
   `trap_actions` and the discouraged actions. This is the only place that describes the case.
2. The learning-goals box (`div.cd-goals`): the case's goals, up to six, in plain words.
3. Four or five numbered sections. Section 1 is the pathology: what the disease does to the
   organs and the circulation. The rest follow the learning goals. Two goals can share a
   section. A goal with no concept behind it, such as a drug choice, can be a bullet.
4. Each section has a heading that states the idea, a figure, one to three sentences that
   teach the idea, then two to four short bullets of one or two sentences. About 80 to 100
   words.
5. "Take home" in its box (`div.cd-home`): three to five lines a resident could repeat on
   shift.
6. Key references, folded away (`details.cd-refs`).

About 3,000 to 3,600 px tall at 620 px wide.

## Teach, do not narrate

Every bullet teaches something a resident can use on the next patient: a definition, a
mechanism, a threshold, a decision rule, a sign and what it means, or a pitfall. The case may
appear as a short example inside a bullet, never as its subject.

Do not describe what the simulator did: phases, timers, what happened after an order, or
scores. The learner saw that in their own run, and it does not transfer. Some cases' teaching
points talk about the simulator (its compressed clock, what it scores, a panel it lacks). Do
not carry those into the discussion.

| Narrates the case | Teaches |
|---|---|
| Her first liter brought her mean pressure to 76. A few minutes later it fell to 54. | A rise that fades within minutes means fluid has done what it can. |
| On fluid and norepinephrine with the tampon still in, she slides into deeper shock. | Fluid and norepinephrine hold the pressure up while the cause goes on. Only removing the source stops it. |
| His CO2 rose from 31 to 46. | With an acid load, a normal CO2 means breathing is not keeping up, often because the patient is tiring. |

Define the central term when learners commonly misread it. TSS states the definition of shock
because many learners treat a normal pressure as proof there is no shock.

## Precision

- If a word has a general meaning and a formal one, say which you mean. Shock is a failure of
  oxygen delivery and needs no low pressure. Septic shock, under Sepsis-3, does need it.
- Do not state signs as a diagnosis ("a fast heart, cool hands and a high lactate are
  shock"). Say what they suggest and what to do. Most signs have other causes.
- Give thresholds as numbers ("a lactate of 4 or more"), not "high".
- Say whether the evidence is randomized or observational when it matters.
- Every evidence statement ends in what to do. A trial result with no decision attached is a
  guideline line, and it goes.

## Figures

A figure earns its place when it shows why. Subjects that worked:

- The mechanism of the disease: an open air sac against one filled with pus, a superantigen
  switching on many T cells.
- A definition drawn: oxygen delivery against oxygen use, with shock below the critical point.
- What trades off to hold a number steady: heart rate rising as vessel tone falls.
- What a number hides: two patients with the same saturation at very different cost.
- Where each treatment acts on a causal chain, or what a treatment takes away.
- What a treatment does over time, when the shape is the lesson: fluid fades, a vasopressor
  holds.

Figures the owner rejected: a chart of the case's own numbers, a generic curve that only shows
things getting worse, and a figure that repeats the text.

Rules. No case numbers on a figure. Illustrative numbers are allowed if the caption says so.
Labels of 14 to 16 px. Colors from the script's palette, which reads in day and night. The
caption starts "Schematic." Each figure has an `aria-label` that says what it shows.

## Voice

Write the way an attending explains it at the bedside. Short sentences. US spelling.

Cut these on sight. Each one came up in an earlier draft:

- bold lead-ins, and labels such as Why, In this case or Takeaway
- slogans, and "X, not Y" lines
- lists of three for rhythm
- a long paragraph under a figure
- a guideline line with no reason, and any sentence that would fit any case
- pointers to other sections, such as "as the next section shows"

No em dashes, no semicolons, and never the words "quiet" or "quietly".

## Truth

- Every number from the case is read from the case files by the script and asserted, then
  filled in by placeholder.
- The discussion agrees with the case's debrief notes and teaching points. If they disagree,
  fix one and say which in the SEED.
- Read a definition or an effect size in its source.
- Mark anything unchecked in square brackets that start with `UNVERIFIED`, `PubMed`, `VERIFY`
  or `MODEL OUTPUT`. The engine strips only those (authoring 10.3). A note that starts with an
  author's name is shown to the learner. The script refuses one.
- List every `UNVERIFIED` note in the handoff for sign-off.

## Checks before handover

1. Run the script, then `python3 engine/build_simulator.py`, then
   `python3 engine/test_packs.py <PREFIX>`.
2. Open the built simulator, finish the case twice (the answers unlock after the second run)
   and reveal. Look at the discussion in day and night.
3. Read every figure. No label touching a line or running out of its box, nothing clipped.
4. Read every bullet and ask whether it would help with the next patient. If it only reports
   what happened in the case, rewrite it.
5. Confirm that no square-bracket note shows and that the height is in range.

## A prompt to start from

Give this to the agent with the prefix filled in. It assumes the case is built and passes its
tests. The plan step is there because most rounds on TIDE and TSS were spent fixing the choice
of ideas and figures after they were drawn.

```
Write the case discussion for <PREFIX>.

Read docs/case-discussion-guide.md in full, then authoring 10.5. From cases/<PREFIX>/ read
the SEED for the learning goals, case_1_shell.py for the patient and vitals, case_3_content.py
for the results, and case_5_handoff.py for intended_path_note, trap_actions and the teaching
points. Copy Claude outputs/tss-discussion/tss_discussion_v2.py to
Claude outputs/<prefix>-discussion/<prefix>_discussion_v1.py and replace its content.

Before you draw anything, send me a plan and stop:
- The case in two or three sentences, the right care in three or four steps, the traps.
- Four or five section headings. Section 1 is the pathology. Name the goal behind each later
  section. Say which central term needs defining, if any.
- For each section, one line on what the figure shows and why it explains something the text
  alone would not. If the honest answer is that it charts the case, pick another figure.
- For each section, the two to four points it teaches, each one usable on the next patient.

When I agree, build it, render it after two runs in day and night, fix every label
collision, and send me the screenshot. List every UNVERIFIED note. Do not claim physician
review.
```
