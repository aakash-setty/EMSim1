# Arrival, handover, and the removal of the Patient tab

**Superseded.** These changes are now folded into `case-authoring-requirements.md`
v0.4 section 3.2 and `system-design-v2.md` v0.5 sections 0, 17 and 18, which are the
source of truth for how the system behaves. This document is retained as the rationale
record: it states why the Patient tab was removed and what was considered instead,
which the current documents give only as conclusions.

It originally amended `case-authoring-requirements.md` §3.2 and §3.1, and
`system-design-v2.md` §3.7, superseding the parts of those sections that described
`ems_handover_text` as learner-facing content and the splash screen as carrying an
arrival narrative.

## 1. Why

The Patient tab printed the whole authored background: past medical history,
every home medication, the full EMS narrative, and a generated appearance
paragraph. The splash screen printed the arrival line and the EMS narrative
again before the learner had pressed Begin.

Between them they handed over the history rather than asking the learner to take
it. A case whose teaching point is "elicit the precipitant of decompensation on
history" cannot also print the precipitant on the first screen.

The case file still carries all of that material. It is needed by the debrief,
the review packet, and the authoring process. It is simply no longer shown to
the learner.

## 2. What the learner now sees

**Splash screen.** Care setting, working title, one arrival line, the chief
complaint in the patient's voice, the mode choice. Nothing else. The arrival line
reads `Patient brought to the Resuscitation Bay` (or Trauma Bay, or Patient
Room).

**History tab, at the top.** Age, sex and weight, then two sentences of handover
under either "Handover from the paramedics" or "Handover from the triage nurse".
Everything else must be asked for.

There are now **seven tabs**. Patient is gone. History is the default tab.

Age, sex and weight stay on screen deliberately. They are on the wristband
rather than in the history, and weight-based dosing is unanswerable without the
last of them.

The general appearance line that the Patient tab used to generate is not lost:
it already exists at the top of the Exam tab as the non-skippable general status
line, which is where a resident looks for it.

## 3. Schema

### 3.1 `metadata.arrival`

```json
"arrival": {
  "mode": "ems",
  "location": "resuscitation_bay",
  "line": "Brought in by EMS. Handover given on arrival in the resuscitation bay."
}
```

| Field | Values | Effect |
|---|---|---|
| `mode` | `ems` \| `triage` | Chooses the heading above the handover |
| `location` | `resuscitation_bay` \| `trauma_bay` \| `patient_room` | The splash arrival line |
| `line` | free text | **No longer shown.** Authoring detail, kept for the review packet |

`mode` replaces the older free-text vocabulary (`Ambulance`, `Walk-in`,
`Transfer`, `Police`). Cases carrying the old values still run: the reader
normalises anything matching walk-in or triage to `triage` and everything else
to `ems`. Author the new values in new cases.

A walk-in or a transfer is `triage` unless paramedics hand over to you directly.

If `location` is missing the simulator recovers it from `line` when that names a
room, and otherwise omits the arrival line rather than guessing at a room.

### 3.2 `patient.arrival_handover`

```json
"arrival_handover": "Sixty-five year old man, breathing trouble that's been getting worse over the last few days. Family called us this morning when he couldn't manage the stairs."
```

**Two sentences. Not three.** This is the whole of what the learner is given for
free.

`patient.ems_handover_text` is retained and is now an author-facing field: the
full handover as it would really be given, for the review packet and for the
author's own reasoning. It is not displayed.

## 4. Writing the handover

The test to apply: **could a competent resident still get this case wrong after
reading it?** If not, it says too much.

### Include

- Age and sex
- The presenting problem, in the register of whoever is speaking
- A rough duration or tempo
- One concrete circumstance that explains why they came in today

### Exclude

- The precipitant. That is usually the case's teaching point.
- Past medical history, home medications, allergies.
- Pertinent negatives. Section 10.3 requires those to be authored as topics the
  learner must ask about; handing one over for free defeats the topic.
- Vital sign numbers. They are on the monitor, live, and a number in the
  handover will be stale within a minute.
- Anything naming or implying the diagnosis, per §10.4.
- Treatments already given, unless the case turns on them.

### Register

An EMS handover is spoken, slightly breathless, and organised around what the
crew saw at the scene. A triage note is written, terse, and organised around
what the patient said at the desk plus one thing the nurse observed.

**EMS, good:**
> Sixty-five year old man, breathing trouble that's been getting worse over the
> last few days. Family called us this morning when he couldn't manage the
> stairs.

**EMS, too much:**
> Sixty-five year old man, known heart failure, three or four days of worsening
> breathlessness, much worse since four this morning. He has not had any of his
> own medications for the last few days.

The second version hands over both the diagnosis and the precipitant. There is
nothing left to elicit.

**Triage, good:**
> Fifty-two year old woman, walked in with chest pain that started this
> afternoon. She looks uncomfortable and is sweating.

**Triage, too much:**
> Fifty-two year old woman, crushing central chest pain radiating to the left
> arm since 3pm, with nausea and diaphoresis. Denies previous cardiac history.

The second version is a complete cardiac history including a pertinent negative.

## 5. Vitals now ramp between phases

The monitor travels to the new phase's numbers over five seconds rather than
jumping. This is display only: transitions still fire the instant their
condition is met, a study still reports the authored vitals for the moment it
was ordered, and the debrief is unchanged.

It has one consequence for authoring. Two phases whose vitals differ by very
little will now read as a slow drift rather than a step, so if a phase change is
meant to be *noticed*, the vitals need to move enough to be seen. This is a
reason to make a deterioration phase's numbers frankly different rather than
subtly so.

The heartbeat audio ramps with the numbers.

## 6. Code changes required

### 6.1 `engine/build_simulator.py` (optional, tidying)

Remove `patient` from the tab lists so the shared payload matches what is
rendered. The UI already filters it, so skipping this changes nothing visible.

```python
TAB_ORDER = ["history", "exam", "stabilization",
             "investigations", "interventions", "consultations", "handoff"]
TAB_LABEL = {"history": "History", "exam": "Exam",
             "investigations": "Investigations", "stabilization": "Stabilization",
             "interventions": "Interventions", "consultations": "Consults",
             "handoff": "Handoff"}
```

### 6.2 `engine/new_case.py`

Replace the `"arrival"` block inside `metadata`:

```python
            "arrival": {
                "mode": todo("3.2", "ems | triage"),
                "location": todo("3.2", "resuscitation_bay | trauma_bay | patient_room"),
                "line": todo("3.2", "one line on how they reached you (author reference, not shown)"),
            },
```

Replace the `"patient"` block:

```python
        "patient": {
            "age": None, "sex": None, "weight_kg": None,
            "background": todo("3.2", "relevant history in one paragraph (NOT shown to the learner)"),
            "presenting_appearance": todo("3.2", "one or two sentences"),
            "arrival_handover": todo("3.2", "EXACTLY TWO SENTENCES, shown to the learner. "
                                            "Age and sex, the problem, a rough duration, and one "
                                            "circumstance. No past history, no medications, no "
                                            "pertinent negatives, no vital sign numbers, nothing "
                                            "naming the diagnosis or the precipitant."),
            "ems_handover_text": todo("3.2", "the full handover as it would really be given "
                                             "(author reference and review packet, not shown)"),
        },
```

In the SEED template, replace the arrival bullet under `## 3.2 Patient`:

```
- Arrival: EMS or triage, and which room (resuscitation bay, trauma bay, patient room):
- The two-sentence handover the learner will see:
- The full handover, for the review packet only:
```

### 6.3 `engine/validate_case.py`

Add this check and call it alongside the others:

```python
def check_arrival(case, errors, warnings, notes):
    """Section 3.2. The handover is the only history the learner gets for free,
    so its length is a clinical constraint, not a style preference."""
    ar = (case.get("metadata") or {}).get("arrival") or {}
    mode = str(ar.get("mode", "")).lower()
    if mode not in ("ems", "triage"):
        if any(k in mode for k in ("ambulance", "walk", "transfer", "police")):
            warnings.append(f"[arrival] mode {ar.get('mode')!r} uses the pre-0.4 vocabulary; "
                            f"use 'ems' or 'triage'")
        else:
            errors.append("[arrival] metadata.arrival.mode must be 'ems' or 'triage'")

    loc = ar.get("location")
    if loc not in ("resuscitation_bay", "trauma_bay", "patient_room"):
        errors.append("[arrival] metadata.arrival.location must be one of "
                      "resuscitation_bay, trauma_bay, patient_room; without it the "
                      "splash screen shows no arrival line")

    h = (case.get("patient") or {}).get("arrival_handover")
    if not h or str(h).startswith("TODO"):
        errors.append("[arrival] patient.arrival_handover is required; it is the only "
                      "history the learner is given without asking")
    else:
        h = str(h).strip()
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", h) if s.strip()]
        if len(sentences) > 2:
            errors.append(f"[arrival] arrival_handover is {len(sentences)} sentences; "
                          f"section 3.2 allows two")
        if len(h.split()) > 45:
            warnings.append(f"[arrival] arrival_handover is {len(h.split())} words; "
                            f"two sentences of handover is usually under 40")
        if re.search(r"\b\d{2,3}\s*(bpm|mmHg|%|/\d{2,3})", h) or re.search(r"\bsats?\b", h, re.I):
            warnings.append("[arrival] arrival_handover quotes vital signs; they are on the "
                            "monitor and will be stale within a minute")
```

`validate_case.py` already imports `re`.
