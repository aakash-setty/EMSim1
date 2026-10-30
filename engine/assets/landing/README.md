Screenshots for the welcome page (engine/landing.js), inlined by engine/build_simulator.py.

Real screens from the local build, 1440 x 900 at 1.5x, resized to 1600 x 1000 and saved as
JPEG quality 74.

- case.jpg: the CHFE case screen (28 September 2026), with every piece of case text blurred
  (4.5 px) and the headings, controls, monitor and patient left sharp.
- debrief.jpg (retaken 29 October 2026): the revealed debrief of a short TSS run, the one case
  with a written discussion, so the left column is not empty. Action names, notes, the
  discussion, references and captions are blurred 4.5 px. Headings, the done, not done and
  prompted marks, the buttons and the monitor are sharp.
- board.jpg (retaken 29 October 2026): the case list. Case titles are public, so nothing is
  blurred.

The blur is applied in the page before capture, so the unblurred text is not in these files.
Retake them after a visible change, so the page shows the current product. The script for
debrief.jpg and board.jpg is `Claude outputs/landing-caps/caps.py`:
`python3 caps.py <absolute path to build/simulator.html> <output folder>` (needs Playwright).
