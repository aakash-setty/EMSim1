# CHFE media

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
| `chfe-ecg-post-intubation-hypotension.webp` | `CHFE-01-post-intubation-hypotension` | Twelve-lead ECG. Ventricular rate 128, PR 160 ms, QRS 90 ms, QTc 456 ms | 128 (the read) | moderate |
| `chfe-ecg-improving-or-intubated-stable.webp` | `CHFE-02-improving-or-intubated-stable` | Twelve-lead ECG. Ventricular rate 94, PR 160 ms, QRS 90 ms, QTc 448 ms | 94 (the read) | moderate |
| `chfe-ecg-arrival-default.webp` | `CHFE-03-arrival-default` | Twelve-lead ECG. Ventricular rate 116, PR 160 ms, QRS 90 ms, QTc 452 ms | 116 (the read) | moderate |

## Chest film (added 14 October 2026)

`chfe-cxr-edema.webp` is `Edema/Edema+KirleyBliness _Male.png` from the folder "Images Manual - Chest XRay" that Aakash Setty
supplied on 14 October 2026, converted to WebP (quality 82, 1024 pixels, greyscale). It is
shown captioned "Chest radiograph" with no read; the read is the comment the debrief prints.
Its original source is not recorded here. [UNVERIFIED: record where the film came from and
that it may be used, and have a named person look at it beside its read, in its state, before
release (authoring section 23).]

## Intubated chest film (added 15 October 2026)

`chfe-cxr-edema-ett.webp` is `chfe-cxr-edema.webp (Edema+KirleyBliness _Male.png)` with an endotracheal tube drawn in, on Aakash Setty's instruction, by
`Claude outputs/ett_v1/cxr_ett_draw.py`: faint tube walls, a radiopaque line down one side and
a bevelled tip, about 10 mm wide, down the tracheal air column, with the tip about 1.5
tracheal widths above where the carina was estimated on the film. No cuff is drawn. Shown in
the intubated state, captioned "Chest radiograph", with the existing read unchanged as the
debrief comment. [UNVERIFIED: the carina position was estimated by eye and the film has no
recorded pixel spacing. The read says the tip is about 4 cm above the carina, and 1.5
tracheal widths is likely nearer 2 to 3 cm, so the read and the picture may disagree. A named
person should look at it beside its read before release (authoring section 23).]
