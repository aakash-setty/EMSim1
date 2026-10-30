Screenshots for the How it works tutorial (engine/tutorial.js), inlined by
engine/build_simulator.py as data URIs in a template, #tut-imgs.

Real screens from the CHFE case in the local build, 1440 x 900 at 1.5x, taken 30 October
2026. The paramedics' handover, the patient's answers, exam findings, results, the chart where
it holds results, nurse lines that belong to the case and the case's disposition choices are
blurred (4.5 px) in the page before capture, so the clear text is not in these files. Orders,
tab names, buttons and the monitor are sharp. Cropped, resized to at most 1100 px wide and
saved as WebP quality 72. The overview carries seven numbered markers drawn after capture.

The debrief screen reuses engine/assets/landing/debrief.jpg.

Retake them after a visible change to the case screen. Script:
`Claude outputs/tutorial/caps_tutorial.py` (needs Playwright), then the crop step described
in the tutorial handoff note.
