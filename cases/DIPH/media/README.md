# DIPH media

Generated twelve-lead tracings, added 13 October 2026 on Aakash Setty's instruction.
Synthetic. Drawn by the ECG generator (`ECG_Generator`, its TypeScript source) from
this case's own ECG read by `ECG_Generator/EMSim case ECGs/generate.mjs`, which records
every choice the read left open. Measured before the noise was added, rendered at
twice size and saved as WebP, 1800 pixels wide, quality 80. Not from a patient.
Every number in a read is model output unless the case says otherwise. [UNVERIFIED:
a named person has to look at each picture beside its read, in its phase, before
release (authoring section 23).]

`diph-ecg-arrival.jpg` and `diph-cxr.jpg` are the images from the source document
and are not generated. Their provenance is in `case_3_content.py` and the review
packet.

| Image | Drawn from | Caption | Rate drawn | Noise |
|---|---|---|---|---|
| `diph-ecg-pulseless-vt.webp` | `DIPH-01-pulseless-vt` | Twelve-lead ECG | 190 (the read) | moderate |
| `diph-ecg-wide-complex-tachycardia.webp` | `DIPH-02-wide-complex-tachycardia` | Twelve-lead ECG | 180 (the read) | moderate |
| `diph-ecg-seizing.webp` | `DIPH-03-seizing` | Twelve-lead ECG | 108 sinus, with ectopic beats (the read) | heavy |
| `diph-ecg-stabilized.webp` | `DIPH-04-stabilized` | Twelve-lead ECG | 100 (the read) | moderate |
| `diph-ecg-stabilizing.webp` | `DIPH-05-stabilizing` | Twelve-lead ECG | 115 (the read) | moderate |
| `diph-ecg-arrival-after-bicarbonate.webp` | `DIPH-06-arrival-after-bicarbonate` | Twelve-lead ECG | 135 (the read) | moderate |
