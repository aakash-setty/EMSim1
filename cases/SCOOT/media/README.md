# SCOOT media

Generated twelve-lead tracings, added 19 October 2026 by a language model, following the
13 October 2026 default (authoring section 23). Synthetic. Drawn with the ECG generator
(`~/Downloads/ECG_Generator`, its built `dist/`, read only) by
`Claude outputs/scoot-ecg/generate-scoot.mjs`, which uses the same sinus-strip path as
`ECG_Generator/EMSim case ECGs/generate.mjs` with this case's own reads, normal morphology,
and the moderate noise preset on seeds 300 to 303 (clear of the seeds generate.mjs uses).
`generate.mjs` and its manifest were not changed. Measured before the noise was added.
Rendered at twice size in Chromium and saved as WebP, 1800 pixels wide, quality 80. Not
from a patient. Every number in a read is model output. [UNVERIFIED: a named person has
to look at each picture beside its read, in its phase, before release (authoring section
23).]

| Image | Drawn from | Caption | Rate drawn | Measured (rate, PR, QRS, QTc) |
|---|---|---|---|---|
| `scoot-ecg-arrival.webp` | `SCOOT-01-arrival` | Twelve-lead ECG. Ventricular rate 88, PR 150 ms, QRS 88 ms, QTc 410 ms | 88 (arrival vitals) | 88, 150, 88, 410 |
| `scoot-ecg-decline.webp` | `SCOOT-02-decline` | Twelve-lead ECG. Ventricular rate 96, PR 150 ms, QRS 88 ms, QTc 410 ms | 96 (decline vitals) | 96, 150, 88, 410 |
| `scoot-ecg-herniation.webp` | `SCOOT-03-herniation` | Twelve-lead ECG. Ventricular rate 56, PR 150 ms, QRS 88 ms, QTc 430 ms | 56 (herniation vitals) | 56, 150, 88, 430 |
| `scoot-ecg-temporized.webp` | `SCOOT-04-temporized` | Twelve-lead ECG. Ventricular rate 70, PR 150 ms, QRS 88 ms, QTc 420 ms | 70 (temporized vitals) | 70, 150, 88, 420 |

The arrival tracing also answers in case_complete. The brainstem compression phase has no
tracing because a terminal phase cannot order one. PR 150 ms matches each phase's monitor
block.

## Head CT (added 19 October 2026, owner instruction)

`scoot-ct-head.series.json` and `scoot-ct-head.series.gz` are a 31-image axial head CT, and
`scoot-ct-head.webp` is its still (image 16 of 31, brain window W 80 L 40), the thumbnail in
the record. They are the EDH case (Case 3, `cases/edh.js`) of Aakash Setty's artifact "Head CT
Teaching Cases" (https://claude.ai/artifact/225E69mr6M4psdgX9EjMbj), version 1792432464-742b,
read on 19 October 2026. That artifact says the images are computer generated from the Colin27
head MRI, converted to CT densities, with the lesion built in and a scanner simulated, and that
a neuroradiologist has not reviewed them.

What was changed in copying: the Hounsfield units were rewritten as two byte planes of
HU + 1024 and gzipped, and every voxel below -300 HU (air, the head holder's noise) was set
to -1000 HU. Nothing at or above -300 HU changed. The artifact's lesion maps were not copied.
The conversion and a round-trip check were run by a model in its workspace. The geometry is
the artifact's: 389 by 486 pixels of 0.488 mm, 5 mm slices from z -64 to +86 mm.

Colin27: Copyright (C) 1993-2009 Louis Collins, McConnell Brain Imaging Centre, Montreal
Neurological Institute, McGill University. Permission to use, copy, modify, and distribute
this software and its documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appear in all copies. The authors and McGill
University make no representations about the suitability of this software for any purpose.
It is provided "as is" without express or implied warranty.

[UNVERIFIED: a named person has to look at the series beside its read before release
(authoring section 23).]
