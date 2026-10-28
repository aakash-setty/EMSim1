# Fonts

The two typefaces of the interface (author's choice, 28 October 2026):

| Role | Family | File | Weights |
|---|---|---|---|
| All text: interface, titles (at a heavier weight), the patient's own words (italic) | Atkinson Hyperlegible Next | `atkinson-hyperlegible-next-latin-wght-normal.woff2`, `atkinson-hyperlegible-next-latin-wght-italic.woff2` | 200 to 800, variable |
| Numbers: monitor, clock, timers, labs, labels | Atkinson Hyperlegible Mono | `atkinson-hyperlegible-mono-latin-wght-normal.woff2` | 200 to 800, variable |

- The Braille Institute commissioned Atkinson Hyperlegible for readers with low vision. Its letters that are easily confused are drawn to differ: the lower-case l has a tail, the 1 has a flag, the zero is slashed in both the text and the mono. Next (2025) is the expanded family. Mono is its monospaced companion.
- Checked on screen at 40 and 56 px against the previous faces: I, l and 1 are distinct, and 0 and O are distinct, in both families.

Both are under the SIL Open Font License 1.1 (the `OFL-*.txt` files here). The license allows use, embedding and redistribution with the software, and forbids selling the fonts by themselves. Each license file has to stay with the fonts.

The files are the Latin subsets from Fontsource 5.3.0 (`@fontsource-variable/atkinson-hyperlegible-next`, `@fontsource-variable/atkinson-hyperlegible-mono` on npm). `engine/build_simulator.py` inlines them into both builds as data URIs, so the page makes no font request to anyone, the local file works offline, and the Content-Security-Policy needs only `font-src data:`. Characters outside the Latin subset fall back to the system font.

The faces used before (Overpass, Overpass Mono, Brygada 1918, chosen and replaced the same day) are kept with their licenses in `Claude outputs/fonts-atkinson/retired-fonts/`, outside the repository.
