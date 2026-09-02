# CHFE author's seed

**There is no seed for this case, and that is the defect the whole pack is built around.**

Section 3 of `docs/case-authoring-requirements.md` says the physician supplies ground
truth first and the drafting AI expands it. This case was produced the other way round:
a language model generated every AUTHOR-ONLY field, then the tooling was built to make
the result reviewable. Section 17 of the authoring document covers what to do when that
happens.

The consequence is that the reviewing physician is not checking an expansion of their
own ground truth. They are authoring the ground truth in review, one field at a time,
which is slower and needs a different frame of mind: read every number as a proposal,
not as a transcription.

Read `CHFE-review-packet.md` before anything else. It lists the fields awaiting primary
sign-off, the clinical calls most likely to be wrong, and the reference verification
status.

**When a physician does write the seed retrospectively**, replace this file with the
section 3 template that `engine/new_case.py` generates, fill it in independently of the
case file, and then diff the two. Anything in the case file that the seed does not
support is an invented fact and should be removed rather than reconciled.
