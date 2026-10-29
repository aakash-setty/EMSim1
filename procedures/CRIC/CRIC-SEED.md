# CRIC: cricothyrotomy, scalpel, bougie, tube

A normal adult neck with a palpable cricothyroid membrane. The learner does the transverse
stab technique from the Difficult Airway Society 2025 eFONA card, in Learn mode (prompted)
or Practice mode (not prompted, errors in the debrief). No complications. Cases with
complications are planned and not built.

Not physician reviewed.

## What a person decided

- 28 October 2026, Aakash Setty: a Procedures box beside the milestones badge (moved there
  from under it on 29 October) opens a window
  of procedures. The first is a cricothyrotomy built in three.js, downloaded on click the
  way locked cases are. A normal neck, no complications.
- 28 October 2026, Aakash Setty: the technique is scalpel, bougie, tube (DAS 2025, transverse
  stab incision, palpable membrane). Learn and Practice modes. The anatomy is shown in
  layers.
- 28 October 2026, Aakash Setty: sign-in is required, like locked cases.
- 28 October 2026, Aakash Setty: the bougie bent too sharply and the neck looked unnatural.
  The bougie now follows the tissue: a straight tract through the membrane opening, one gentle
  arc inside the airway, down the trachea, and a straight shaft outside. The neck gained the
  sternocleidomastoids, the clavicles and manubrium, the suprasternal notch, a submental slope
  to the chin, and drapes with a window over the neck.
- 28 October 2026, Aakash Setty: the neck was far too long. A head now lies under the drape
  so the shape reads, and the proportions follow two bedside measures: suprasternal notch to
  chin tip 14 cm (sternomental distance, under 12.5 cm is associated with difficulty) and
  thyroid notch to chin tip 7 cm (thyromental distance, normal over 6.5 cm). The neck is
  about 11 cm deep front to back over the larynx.
- 28 October 2026, Aakash Setty: the chin and face were lost in the head shape. The head is
  now built from simple solids at landmark positions (chin, jaw, lips, nose, brow, cheeks,
  ears, cranium), so the profile shows them under the drape.
- 28 October 2026, Aakash Setty: build the torso. A trunk, shoulders, the trapezius slope and
  arms at the sides now lie under the drape (`make_cric_torso.py`). Shapes only, sized by eye
  to an adult: chest about 19 cm deep at the lower sternum, shoulders about 45 cm across.
  No legs: the drape falls away past the hips.
- 29 October 2026, Aakash Setty: the trapezius and the area above the clavicles were missing.
  The clavicles now run out to the acromion, the upper trapezius slopes from the back of the
  neck to the shoulder behind them, the deltoid caps the shoulder, and the hollow above each
  clavicle opens between them. The drapes now cover only the chest below the clavicles and
  the face above the chin, so the whole neck is bare from side to side. Placed by eye.
- 29 October 2026, Aakash Setty: the bougie grew outside as it went in, and the tube had no
  end. Both now have a fixed length, so what goes in comes off the outer end. The turn buttons
  are much larger. When a step needs an instrument, Learn mode says to pick it up and the
  instrument glows in the tray. The cuff can be deflated with a button.

## What a model chose, not yet reviewed

- The step list and its order, and every quotation in `why`, from the DAS 2025 action card
  and its teaching framework, read on 28 October 2026
  (https://das.uk.com/wp-content/uploads/2025/12/2025-CICO-Transverse-stab-incision-pdf.pdf).
- The geometry. Teaching geometry, not measured anatomy. The membrane is about 9 mm high and
  20 mm wide. A CT study of trauma patients reports a mean height of about 7.9 mm in men and
  6.0 mm in women (https://pearl.plymouth.ac.uk/handle/10026.1/9570, citation details
  unverified). Skin 2 mm, fat about 5 mm over the membrane, both teaching choices.
- The bougie range of 10 to 15 cm is from the card. The tube's depth range (55 to 85 mm from
  the skin) and the cuff's position on the tube are teaching choices.
- The cuff volume range of 5 to 10 mL is a teaching choice.
- The lengths: bougie 60 cm, tube 28 cm with a 16 mm connector. Round figures for an adult
  bougie and a 6.0 tube, not checked against a product sheet.
- The bougie's path: tract 70 degrees from the skin plane, 4 mm further straight into the
  air, then an arc of 12 mm radius. Teaching choices, chosen so the tract stays inside the
  membrane opening and the arc clears the cricoid ring and the back wall. The coude tip is
  drawn at 40 degrees.
- The outer shape: the sternocleidomastoids, clavicles and manubrium are placed by eye.
  The skin and fat are shaped round them (`Claude outputs/procedures-gen/make_cric_anatomy.py`).
- The proportions: 14 cm and 7 cm are chosen just above the two thresholds, a model's
  choice. The thyroid cartilage about 2 cm tall in the midline, the hyoid 1 cm above it, the
  tracheal rings 6.6 mm apart: by eye. The head is a draped shape only, a union of simple solids at
  landmarks placed by eye (`make_cric_head.py`), not anatomy. Made by `Claude outputs/procedures-gen/make_cric_proportions.py`.
- The distractors and their feedback.
- The anterior jugular veins, strap muscles and thyroid isthmus are placed to teach why the
  stab stays in the midline and above the cricoid. Their positions are not measured.
- Practice mode refuses a move out of order, as Learn mode does, and counts it.

## Open questions

- Should Practice mode let a wrong move happen and show its consequence (bleeding, a false
  passage) rather than refuse it? That is the natural first complication case.
- The vertical incision technique for an impalpable membrane is mentioned only as a
  distractor.
