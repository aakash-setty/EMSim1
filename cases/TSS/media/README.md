# TSS media

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
| `tss-ecg-fluid-responsive.webp` | `TSS-01-fluid-responsive` | Twelve-lead ECG. Ventricular rate 114, PR 140 ms, QRS 84 ms, QTc 430 ms | 114 (the read) | moderate |
| `tss-ecg-hypotensive.webp` | `TSS-02-hypotensive` | Twelve-lead ECG. Ventricular rate 138, PR 140 ms, QRS 84 ms, QTc 430 ms | 138 (the read) | moderate |
| `tss-ecg-supported.webp` | `TSS-03-supported` | Twelve-lead ECG. Ventricular rate 124, PR 140 ms, QRS 84 ms, QTc 430 ms | 124 (the read) | moderate |
| `tss-ecg-profound-shock.webp` | `TSS-04-profound-shock` | Twelve-lead ECG. Ventricular rate 148, PR 140 ms, QRS 84 ms, QTc 430 ms | 148 (the read) | moderate |
| `tss-ecg-stabilizing.webp` | `TSS-05-stabilizing` | Twelve-lead ECG. Ventricular rate 116, PR 140 ms, QRS 84 ms, QTc 430 ms | 116 (the read) | moderate |
| `tss-ecg-arrival-default.webp` | `TSS-06-arrival-default` | Twelve-lead ECG. Ventricular rate 128, PR 140 ms, QRS 84 ms, QTc 430 ms | 128 (the read) | moderate |

## Chest film (added 14 October 2026)

`tss-cxr-normal.webp` is `Normal/Normal_Female.png` from the folder "Images Manual - Chest XRay" that Aakash Setty
supplied on 14 October 2026, converted to WebP (quality 82, 1024 pixels, greyscale). It is
shown captioned "Chest radiograph" with no read; the read is the comment the debrief prints.
Its original source is not recorded here. [UNVERIFIED: record where the film came from and
that it may be used, and have a named person look at it beside its read, in its state, before
release (authoring section 23).]
