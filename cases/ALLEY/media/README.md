# ALLEY media

## Chest film (11 November 2026)

`alley-cxr-normal.webp` is `Normal/Normal_Male.png` from the folder "Images Manual - Chest
XRay" that Aakash Setty supplied, converted to WebP (quality 82, 1024 pixels, greyscale). Its
read is the catalog's normal read. [UNVERIFIED: record where the folder's films came from and
that they may be used, and have a named person look at the picture beside its read before
release (authoring section 23).]

## Twelve-lead tracings (11 November 2026)

Reused, not drawn for this case, as TIDE did. Each file is a byte-for-byte copy of a generated
tracing from another pack, chosen for the rate nearest the phase's monitor rate. The phase heart
rates were set to match (112, 114, 116, 96). Synthetic, normal morphology, not from a patient.

| Image | Copied from | Read | Phases | Monitor rate |
|---|---|---|---|---|
| `alley-ecg-sinus-114.webp` | `TSS/media/tss-ecg-fluid-responsive.webp` | Sinus tachycardia. PR 140 ms, QRS 84 ms, QTc 430 ms. No ST change | presentation, drifting, held_early, held_mid | 112, 114 |
| `alley-ecg-sinus-116.webp` | `TSS/media/tss-ecg-stabilizing.webp` | The same, at 116 | untreated_floor, held_late | 116 |
| `alley-ecg-sinus-96.webp` | `SCOOT/media/scoot-ecg-decline.webp` | Sinus rhythm. PR 150 ms, QRS 88 ms, QTc 410 ms | improving | 96 |

Fluid, bicarbonate and sedation move the monitor's rate, and a result never sees an effect, so
the captions leave the rate out.
