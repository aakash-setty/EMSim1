# Source images kept out of the build

`media/` is inlined into `build/simulator.html` in full: every file in it becomes a data URI
whether or not a payload names it. An image the case does not show therefore costs build size
for nothing, so it lives here instead.

**`diph-ecg-post-bicarb.jpg`** is the second twelve-lead from Dr Medwid's document. It was
briefly assigned to the narrowing phase and was reverted on 5 September 2026: it is a
wide-complex tracing, so it sat under a nurse line saying the complexes had narrowed. That
phase reports in text again. See `DIPH-review-packet.md` section 2.9 and `DIPH-SEED.md`
section 9.10.

To put it back, move it into `media/` and give the narrowing phase an
`image("diph-ecg-post-bicarb", "Twelve-lead ECG")` payload in `case_3_content.py`.
