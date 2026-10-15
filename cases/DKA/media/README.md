# DKA media

Generated twelve-lead tracings, added 13 October 2026 on Aakash Setty's instruction.
Synthetic. Drawn by the ECG generator (`ECG_Generator`, its TypeScript source) from
this case's own ECG read by `ECG_Generator/EMSim case ECGs/generate.mjs`, which records
every choice the read left open. Measured before the noise was added, rendered at
twice size and saved as WebP, 1800 pixels wide, quality 80. Not from a patient.
Every number in a read is model output unless the case says otherwise. [UNVERIFIED:
a named person has to look at each picture beside its read, in its phase, before
release (authoring section 23).]

| Image | Drawn from | Caption | Rate drawn | Noise |
|---|---|---|---|---|
| `dka-ecg-potassium-replaced-ondansetron.webp` | `DKA-01-potassium-replaced-ondansetron` | Twelve-lead ECG. PR 140 ms, QRS 88 ms, QTc 455 ms | 102 (phase vitals with fluid, 102 (112 less 10)) | moderate |
| `dka-ecg-potassium-replaced.webp` | `DKA-02-potassium-replaced` | Twelve-lead ECG. PR 140 ms, QRS 88 ms, QTc 450 ms | 102 (phase vitals with fluid, 102 (112 less 10)) | moderate |
| `dka-ecg-treated-ondansetron.webp` | `DKA-03-treated-ondansetron` | Twelve-lead ECG. PR 140 ms, QRS 88 ms, QTc 450 ms | 94 (phase vitals with fluid, 94 (104 less 10). Without fluid it would be 104, sinus tachycardia rather than the "sinus rhythm" the read says) | moderate |
| `dka-ecg-treated.webp` | `DKA-04-treated` | Twelve-lead ECG. PR 140 ms, QRS 88 ms, QTc 445 ms | 94 (94, as above) | moderate |
| `dka-ecg-potassium-falling-ondansetron.webp` | `DKA-05-potassium-falling-ondansetron` | Twelve-lead ECG. PR 140 ms, QRS 88 ms, QTc 525 ms | 108 sinus, with ectopic beats (phase vitals with fluid, 108 (118 less 10)) | moderate |
| `dka-ecg-potassium-falling.webp` | `DKA-06-potassium-falling` | Twelve-lead ECG. PR 140 ms, QRS 88 ms, QTc 520 ms | 108 sinus, with ectopic beats (phase vitals with fluid, 108 (118 less 10)) | moderate |
| `dka-ecg-recovering-ondansetron.webp` | `DKA-07-recovering-ondansetron` | Twelve-lead ECG. PR 140 ms, QRS 88 ms, QTc 455 ms | 102 (phase vitals with fluid, 102 (112 less 10)) | moderate |
| `dka-ecg-recovering.webp` | `DKA-08-recovering` | Twelve-lead ECG. PR 140 ms, QRS 88 ms, QTc 450 ms | 102 (phase vitals with fluid, 102 (112 less 10)) | moderate |
| `dka-ecg-ondansetron-other-states.webp` | `DKA-09-ondansetron-other-states` | Twelve-lead ECG. PR 140 ms, QRS 88 ms, QTc 465 ms | 112 (arrival vitals, 112) | moderate |
| `dka-ecg-arrival-default.webp` | `DKA-10-arrival-default` | Twelve-lead ECG. PR 140 ms, QRS 88 ms, QTc 460 ms | 112 (arrival vitals, 112) | moderate |

## Chest film (added 14 October 2026)

`dka-cxr-normal.webp` is `Normal/Normal_Female.png` from the folder "Images Manual - Chest XRay" that Aakash Setty
supplied on 14 October 2026, converted to WebP (quality 82, 1024 pixels, greyscale). It is
shown captioned "Chest radiograph" with no read; the read is the comment the debrief prints.
Its original source is not recorded here. [UNVERIFIED: record where the film came from and
that it may be used, and have a named person look at it beside its read, in its state, before
release (authoring section 23).]
