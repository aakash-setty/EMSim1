# Writing a procedure

A procedure is a hands-on skill practiced on a three-dimensional model: a cricothyrotomy,
later others. It is not a case. It has no phases, no vitals and no interview. The learner
picks instruments and does the steps, and the debrief lists what went wrong.

Nothing clinical here has been reviewed by a physician unless the pack's `review` field and
its SEED name the decision, the person and the date. Say so in anything you write.

## Where things live

| What | Where |
|---|---|
| The procedure | `procedures/<P>/<P>-procedure.json`, data only |
| Who decided what | `procedures/<P>/<P>-SEED.md` |
| The rules (step types) | `engine/procsim-core.js` |
| The model (layer kinds, depth queries) | `engine/procsim-geom.js` |
| The drawing and controls | `engine/procsim-view.js` |
| The Procedures box and window, loading | `engine/procedures.js` |
| Checks on a pack | `engine/validate_procedure.py` (the build runs it) |
| Behavior tests | `node engine/procsim-tests.js` (every pack) |
| three.js | `engine/vendor/three/` (see its README) |

The same rule as cases: nothing in `engine/` names a procedure, a structure or an
instrument. A pack names them and the engine reads only ids, depths, directions and ranges.
A new procedure that needs a step type the engine does not have is an engine change, made
and tested on its own first.

## How it reaches the learner

The pack is locked like a case. The build writes it to `private-packs/<P>.json`, the site
keeps a stub with its hash, and opening it goes through the same sign-in, edge function,
rate limit and hash check as a locked case (`ACCESS_UI.fetchProcedure`). The prefix must
not match a case's (the build checks).

The code (three.js and the three `procsim-*.js` files) is one script that loads only when a
procedure is opened. The site serves it as `site/px/procsim-<hash>.js`, from its own address,
which the content security policy allows. The local build carries it inline as text. The
code is never in the pack, because the policy does not let the page run code it downloads
from the bucket.

## Coordinates

Millimeters. x toward the patient's left, y anterior (toward the ceiling, supine), z toward
the head. The airway's axis is x = 0, y = 0. This frame is left-handed, so the view draws the
model mirrored in x to show it the right way round. Write the pack in the frame above and
do not mirror anything yourself.

## Layers

Each layer is one of:

- `slab`: a solid sheet through stations along z. Each station has `outer` and `inner`
  cross-sections, or `outer` with an `offset` (the inner face that many millimeters to the
  right of the line's direction).
- `surface`: a closed loop with no thickness. Use it for the air layer.
- `tube`: a path of `[x, y, z]` points and a `radius`.
- `repeat`: a slab `template` placed at each z in `at`.
- `mirror_of`: a copy of an earlier layer across the midline.

A cross-section is `{"ellipse": [cx, cy, rx, ry], "from": deg, "to": deg}`, where 0 degrees
is anterior and 90 the patient's left, or `{"poly": [[x, y], ...]}`. A full 360 degrees is a
closed ring.

`segments` sets how finely a layer's cross-sections are sampled (40 by default). Give the
skin and fat more (120 in CRIC), because their outline carries the landmarks.

Flags: `hit` (the depth queries see it), `resist` (a blade stops at its surface), `air` (the
one layer the instruments must reach, exactly one per pack), `section_only` (drawn only in
the midline cut, to fill space the model leaves hollow). The first layer is the skin: the
pointer and every depth are measured from it.

**Check.** Run `node engine/procsim-tests.js`. It checks that the target zone sits over the
air layer at all four corners with nothing resistant in between, and that something lies
behind the air. Then open the procedure and look at the midline cut. A layer that crosses
another shows as a patch of the wrong color in the cut.

## The field and the drapes

`field` is the window the drapes leave: `{"z": [low, high], "x": half-width}`. The view lays
one cloth over everything outside it, resting on the skin, so the chest and the chin show
their shape under it. The model can stop just past the field: the cloth hides its ends. A layer marked
`under_drape` is something the cloth rests on (CRIC has a head and a nose only for that), so
the drape shows a body, not a box. `table_y` is the height of the table. A `tube` with `caps: true` gets
rounded ends, for a limb rather than a vessel. Zoom out in the view to see the whole patient.

Get the proportions right before anything else, from measures a clinician knows. CRIC uses
the sternomental and thyromental distances and records them in `proportions`. A model that
is the wrong length reads as wrong however good each part is.

## Instruments that bend

A rod (a bougie) is semi-rigid. Before it is turned, its shaft lies across the neck and only
the angled tip goes in (`coude_deg`, `tip_mm`). After it is turned, it follows one path
(`engine/procsim-geom.js`, `rodPath`): straight through the tract at `tract_deg` from the skin
plane, `straight_mm` further into the air, one arc of radius `bend_mm`, then down the airway.
Outside, the shaft continues the tract's line. The tube over it follows the same path. The
tests check that the path crosses nothing but the layers above the air and the air itself,
stays off the back wall, and never bends tighter than `bend_mm`. Choose the tract angle so
the tract stays inside the opening, and the bend so the arc has room in the airway.

## Zones

What the finger feels and where the blade may go. Each zone is an x range and a z range on
the skin, with `feel` (shown while the finger is over it) and `wrong` (said when the learner
picks it and it is not the target). The first zone that contains a point wins, so list the
target first and the catch-all last.

## Steps

Each step has `id`, `type`, `label`, `prompt` (Learn mode), `why` (Learn mode, quote the
source), and `source`. Types:

| Type | The learner | Fields |
|---|---|---|
| `action` | presses a button | `effect`: `remove` (a tool), `hand` (a key of `hands`), `pose`, `blade`, `secured` |
| `choice` | picks an option | `options`, `correct` or `correct_by_hand`, `wrong` |
| `palpate` | clicks a zone with the finger | `target` |
| `stab` | places a blade with its edge set, pushes into the air layer | `tool`, `target`, `edge`, `reach` |
| `rotate` | turns the blade a quarter turn at a time | `tool`, `to` (`head` or `feet`) |
| `insert` | pushes a rod in along the blade until its tip is in the air | `tool`, `guide` |
| `turn` | swings the rod to run along the airway | `tool`, `to` |
| `advance` | pushes the rod into a range, then Done | `tool`, `range_mm`, `max_mm`, `clicks` |
| `railroad` | pushes a tube over the rod, rotating, then Done | `tool`, `cuff_mm`, `depth_mm`, `catch_mm` |
| `inflate` | fills a cuff into a range, then Done | `tool`, `range_ml`, `max_ml` |
| `confirm` | checks the evidence (a capnograph) | `tool`, `show` |

`errors` maps an error code to what the learner is told. `severity` maps a code to
`critical` or `major` (default `major`, order errors `minor`). Directions are `operator`,
`far`, `head` and `feet`. The operator's side comes from the `choice` step whose effect is
`side_from_choice`.

Learn mode prompts every step and refuses a wrong move with the reason. Practice mode shows
no prompts, refuses the same moves, and lists every error in the debrief. Practice shows
every remaining `action` and the `distractors` in alphabetical order, so the list does not
give the sequence away.

## Style

The learner's text follows the house style: plain, direct, short sentences, US spelling, no
em dashes, no semicolons, never "quiet". Quote the source in `why` where you can. A depth, a
volume or a range that no source gives is a teaching choice: say so in the pack's `review`
and in the SEED. The validator refuses reviewer markers in anything the learner reads.

## Sign-off

The pack validates and `node engine/procsim-tests.js` passes. You have played it in both
modes with each hand, and opened the midline cut at the stab, the bougie and the tube. Every
step's `why` quotes or names its source. The SEED says what was decided, by whom and when,
and that it is not physician reviewed.
