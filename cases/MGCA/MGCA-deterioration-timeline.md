# Deterioration timeline

**Case:** `mgc-meningococcemia-adrenal-01`

Generated per section 14.2c. Time-guarded transitions are the only mechanism in this system that changes the patient without the resident doing anything, so they get their own review artifact. The per-key matrix cannot show them: it enumerates what a key resolves to in a phase, not how the phase was reached.

**How to review this.** For each row, ask two questions. Would this patient really deteriorate in that time if that treatment were withheld. And has the resident been given a fair chance to act, meaning a nurse prompt naming the missing treatment, early enough to be acted on.


## Time-guarded exits, by phase

| phase | at | guard (fires if still true) | to | terminal | preceding prompts |
|---|---|---|---|---|---|
| `presentation` | 240s (phase_entry) | `NOT flag steroid_given set` | `adrenal_crisis` | no | hydrocortisone_bolus at 70s |
| `presentation` | 240s (phase_entry) | `NOT flag abx_given set` | `progressive_meningococcaemia` | no | ceftriaxone at 45s |
| `adrenal_crisis` | 210s (phase_entry) | `NOT flag steroid_given set` | `frank_septic_shock` | no | hydrocortisone_bolus at 70s |
| `progressive_meningococcaemia` | 210s (phase_entry) | `NOT flag abx_given set` | `frank_septic_shock` | no | ceftriaxone at 45s |
| `frank_septic_shock` | 300s (phase_entry) | `NOT (flag abx_given set AND flag steroid_given set AND flag pressor_running set)` | `cardiac_arrest` | **yes** | ceftriaxone at 45s, hydrocortisone_bolus at 70s, norepinephrine_drip at 45s |

## The do-nothing trajectory

What happens from arrival if the resident performs no state-changing action at all. This is the trajectory a resident sees when they freeze, and it is the one an author is least likely to have imagined.

| elapsed | phase | HR | BP | RR | SpO2 | alertness | entered by |
|---|---|---|---|---|---|---|---|
| 0s | `presentation` | 124 | 99/63 | 24 | 98 | 0 | arrival |
| 240s | `adrenal_crisis` | 136 | 88/54 | 28 | 97 | 1 | clock, 240s |
| 450s | `frank_septic_shock` | 150 | 70/42 | 32 | 95 | 2 | clock, 210s |
| 750s | `cardiac_arrest` | 24 | 38/20 | 4 | 58 | 3 | clock, 300s |

## Narration the nurse gives on each time-driven change

This is the only place in the system where a nurse line may describe a trajectory, because here there is one. Every line below must still be true of the numbers the monitor shows immediately afterwards.


**`presentation` → `adrenal_crisis` at 240s**

> She's harder to rouse than she was ten minutes ago, doctor, and she's gone a worse colour. Her pressure's come down too. I don't think she's holding.


**`presentation` → `progressive_meningococcaemia` at 240s**

> The spots on her ankles have joined up into patches while we've been standing here, and there are new ones on her forearms. She's oozing round the cannula site now too.


**`adrenal_crisis` → `frank_septic_shock` at 210s**

> Her pressure's in the seventies now and she's not answering me properly. I can't feel a radial pulse on either side.


**`progressive_meningococcaemia` → `frank_septic_shock` at 210s**

> The purpura is spreading up both legs and onto her belly, and she's stopped answering me. Her pressure is seventy over forty.


**`frank_septic_shock` → `cardiac_arrest` at 300s**

> She's lost her output. No pulse. I'm starting compressions.
