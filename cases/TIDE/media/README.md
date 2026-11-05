# TIDE media

## Chest films (4 November 2026)

`tide-cxr-multifocal.webp` is `Pneumonia/Multifocal_Male.png` from the folder "Images Manual -
Chest XRay" that Aakash Setty supplied, converted to WebP (quality 82, 1024 pixels, greyscale).
The model looked at it on 4 November 2026 beside its read: patchy airspace opacities in both
lower zones, more on the right. It is a PA erect film, while the patient is in a resuscitation
bay, where a portable AP film would be usual.

`tide-cxr-multifocal-ett.webp` is the same film with an endotracheal tube drawn in by
`Claude outputs/ett_v1/cxr_ett_draw.py` with
`{"carina":[553,455],"tw":50,"ctrl":[[552,-60],[552,60],[553,160],[553,260],[553,330]],"tipx":553}`.
The carina position was estimated by the model from a high-pass view of the film and is
uncertain, so the read says only that the tip is in the mid trachea above the carina. No
orogastric tube is drawn, and the read does not mention one.

[UNVERIFIED: record where the folder's films came from and that they may be used, and have a
named person look at both pictures beside their reads, in their states, before release
(authoring section 23).]

## Twelve-lead tracings (4 November 2026)

Reused, not drawn for this case. Generating new tracings needed the ECG generator built in the
workspace, and the build was refused there. Each file below is a byte-for-byte copy of a
generated tracing from another pack, chosen for the rate nearest the phase's monitor rate. The
reads are the reads each tracing was drawn from, so picture and read agree. The source packs'
own media READMEs record how each was drawn (generator, seed, noise, measurement). Synthetic,
normal morphology, not from a patient.

| Image | Copied from | Read | Phases | Monitor rate |
|---|---|---|---|---|
| `tide-ecg-sinus-116.webp` | `TSS/media/tss-ecg-stabilizing.webp` | Sinus tachycardia at 116. Normal axis. PR 140 ms, QRS 84 ms, QTc 430 ms. No ST elevation or depression. | presentation, low_after_fluid, case_complete | 118, 120 |
| `tide-ecg-sinus-114.webp` | `TSS/media/tss-ecg-fluid-responsive.webp` | The same, at 114 | fluid_response, on_pressor, failing_support, ventilated | 112, 110, 112, 112 |
| `tide-ecg-sinus-128.webp` | `TSS/media/tss-ecg-arrival-default.webp` | The same, at 128 | low_pressure, post_induction_collapse | 128, 128 |
| `tide-ecg-sinus-138.webp` | `TSS/media/tss-ecg-hypotensive.webp` | The same, at 138 | worsening_shock | 140 |
| `tide-ecg-brady-56.webp` | `SCOOT/media/scoot-ecg-herniation.webp` | Sinus bradycardia at 56. Normal axis. PR 150 ms, QRS 88 ms, QTc 430 ms. No ST change. | tiring | 56 |

To fit the tracings, the ventilated phase's heart rate moved from 106 to 112 and the tiring
phase's from 52 to 56, and each phase's monitor block now carries the intervals of its tracing.
The arrest phase is terminal and cannot order an ECG.

[UNVERIFIED: the same tracing appears in another case. A learner who has played TSS may
recognize it. A named person has to look at each picture beside its read, in its phase, before
release (authoring section 23). Replace with tracings drawn for this case when the generator
can be run.]
