# The patient figure: artwork, rig and add-ons

The figure in the room is drawn by `engine/patient.js` from `engine/patient-art.json`.
The artwork is the [avataaars](https://github.com/fangpenlin/avataaars) library, designed by
Pablo Stanley and packaged by Fang-Pen Lin, MIT licensed. `LICENSE` in this folder is their
licence. The build copies its text into `build/simulator.html` and `build/patient-lab.html`,
because the licence requires the notice to travel with the artwork.

Nothing at run time touches the avataaars site, React, or npm. `extract.js` is run once,
offline, to regenerate `patient-art.json`. The commands are at the top of that file.

## What was kept

Every option the generator offers: 35 tops, 7 accessories, 6 facial hair, 9 clothes,
11 shirt graphics, 12 eyes, 12 eyebrows, 12 mouths, and the skin, hair, facial hair and fabric
palettes. Option names are the generator's own, so a link built on getavataaars.com
translates key for key into `patient.avatar`.

Two additions, listed under `added` in the JSON:

- `clotheType: "HospitalGown"`, the default. The crew neck outline with a print.
- `eyebrowType: "FrownNatural"`. Upstream ships the drawing and never registers it.
- `eyeType: "Drowsy"` and `"Heavy"`. The default eye under a heavy lid, and under a lid so low
  only a sliver shows. Drawn for reduced alertness; the figure picks them itself from the
  phase's alertness level.

One omission: `ShortHairShaggy`, which upstream marks as broken and disables.

Any colour key accepts a palette name or a hex value such as `"#7a4b2a"`.

## Try it

`build/patient-lab.html` is written by every build. Pick an appearance, switch states, and
copy the JSON it prints into the case file.

## How a case uses it

```json
"patient": {
  "avatar": { "topType": "ShortHairSides", "hairColor": "SilverGray", "skinColor": "Pale" }
}
```

```json
"content_keys": {
  "patient_visual": {
    "rules": [
      { "when": "phase is seizing", "value": { "eyes": "open", "seizure": true } },
      { "when": "flag intubated set", "value": { "eyes": "closed" } },
      { "when": null, "value": {} }
    ]
  }
}
```

`patient_visual` is a guarded rule list like every other content key: first match wins, the
condition language is the engine's, and the value is the whole visible state. Keys left out
take their defaults.

| Key | Values | Default |
|---|---|---|
| `eyes` | `open`, `closed` | `open`. Open eyes blink on their own |
| `seizure` | `true`, `false` | `false` |
| `work_of_breathing` | `normal`, `increased`, `severe` | `normal` |
| `expression` | `{eyeType, eyebrowType, mouthType}` | the avatar's resting face |
| `addons` | list of registered add-on names | none |

The breathing rate is never authored here. It follows the respiratory rate on the monitor,
including the ramp between phases, and a rate of zero stops the chest.

A case with neither block still gets a figure: the default appearance, eyes open, breathing
at the monitor's rate.

## The rig

The 264 x 280 viewBox of the original. Groups nest so parts move independently:

```
figure                      a seizure shakes this
  slot: behind
  torso                     breathing lifts this
    body below the chin, neck shadow, clothes
    slot: torso
  head                      bobs with laboured breathing; pivot at the neck (132,192)
    skull and face skin
    slot: skin              clipped to the skin outline: colour change, rash, sweat
    face: mouth, nose, eyes, brows        each of mouth, eyes, brows is its own rig
    facial hair
    slot: face              cannula, mask, tube
    hair
    slot: overHair          straps
    accessories (glasses)
    slot: front
  slot: overlay             in front of everything, moves with the figure only
slot: backdrop              behind the figure, does not move
```

Each rig has a channel `{x, y, rot, sx, sy}`. Every frame the channels are zeroed, each active
feature adds to them, and the sums become transforms. Contributions add, so features compose
without knowing about each other.

Eyes, brows and mouth are also *poses*: each holds several drawings and shows one. A feature
sets `f.pose.eyes = 'Close'` and the rig swaps the drawing. Features run in priority order,
lowest first, so a higher priority has the last word.

Landmarks, in viewBox units. The lab's Landmarks button draws them over the figure.

| Point | x, y |
|---|---|
| eyes | 106,112 and 158,112 |
| nose tip | 132,134 |
| mouth centre | 132,156 |
| chin | 132,186 |
| ears | 77,118 and 187,118 |
| collar | 132,206 |

## Adding an add-on

Two edits.

1. Register it in `engine/patient.js`, beside the worked examples:

```js
register('bipap_mask',{
  label:'BiPAP mask strapped on',     // what a screen reader is told
  priority:55,                        // stacking and pose order; higher is later and on top
  hide:['accessories'],               // layers to hide while it is on (glasses come off)
  layers:{                            // SVG per slot, in viewBox units
    face:'<path d="..."/>',
    overHair:'<path d="..."/>'
  },
  tick:function(f){                   // optional, runs every frame
    f.pose.mouth='Serious';           // force a pose
    f.ch.head.y+=0.5;                 // or move a rig
  }
});
```

Any of `layers`, `hide` and `tick` may be omitted. `gaze_left` and `nystagmus` are `tick`
only, with no artwork. `nasal_cannula` is artwork only. Ids inside the SVG that must be unique
(masks, gradients, clip paths) are written `@@name` and are prefixed per patient at mount.
A layer may be a function `(inst) => svgString` when the drawing depends on the appearance.

Inside `tick`, `f` carries: `t` and `dt` in ms, `state`, `rr`, `breath` (0 at end-expiration
to 1 at end-inspiration), `ch` (the channels), `pose`, `mem` (scratch that persists for this
feature on this patient), `reduced` (the viewer prefers reduced motion) and `inst`.

2. Add the name to `SHARED["patient"]["addons"]` in `engine/build_simulator.py` and to
`PATIENT_ADDONS` in `engine/validate_case.py`. The engine tests fail if the three disagree.

A case then names it: `"addons": ["bipap_mask"]`, usually under a rule such as
`"when": "flag niv_on set"`.

## Motion and accessibility

Nothing flashes. A seizure is movement only, with no change in brightness. When the viewer's
system asks for reduced motion the amplitudes drop to about a third and the sign is still
readable. The figure carries a text description that updates with the state and uses
observational words only ("rhythmic shaking of the whole body", never "seizing").
The figure freezes while the case is paused.
