# Interview matching: diagnosis and options

**Superseded as a description of the system.** What was built is documented in
`system-design-v2.md` v0.5 section 20 (architecture) and
`case-authoring-requirements.md` v0.4 section 10.6 (measurements and authoring rules).
Read those for current behaviour. This document is retained because it holds the
diagnosis that motivated the work and the options that were rejected, neither of which
survives in the current documents.

Status: analysis of September 2026, with implementation notes added where an
option was subsequently built. Sections 1 to 3 are the measurement and are
unchanged; sections 4 to 7 are the options, annotated.

## 1. What was measured, and how much to trust it

The shipped matcher was extracted from the built `simulator.html` rather than
reimplemented, so these numbers describe the matcher that actually runs. It was
run against 54 questions in six categories, none of which appear in any variant
list.

| Category | | Shipped matcher |
|---|---|---|
| A | plain paraphrase, wording not in the bank | 21/25 (84%) |
| B | clinical shorthand, the way residents type | 5/12 (42%) |
| C | conversational, pronoun heavy | 3/5 (60%) |
| D | compound, two topics in one question | 3/3 (100%) |
| E | typos and dictation errors | 1/4 (25%) |
| F | out of scope, should match nothing | 3/5 (60%) |
| | **total** | **36/54 (67%)** |

**Caveats that matter.**

- The expected label for each question is my judgement of what the case author
  would want, not ground truth from the author. Category C in particular is
  arguable: I marked "has this ever happened before" as `past_medical_history`,
  and a reasonable author might not.
- The battery is harder than the one quoted in the spec. Section 10.6 reports
  23/25 on held-out phrasings, which is consistent with my category A alone
  (84%). The overall drop comes from categories the spec did not test.
- Category D scored 100% only because I counted a hit if *either* topic matched.
  The real behaviour is that one topic is answered and the other is dropped with
  no signal. See failure mode 4.
- Category F has n=5. Every claim about out-of-scope rejection below rests on a
  sample too small to put a confidence interval on. It is enough to show the
  failure exists; it is not enough to quantify the rate.

## 2. Five distinct failure modes

These are different problems with different fixes. Treating "matching accuracy"
as one number hides that.

### 2.1 The bank is written in one register and residents type in another

Of 40 common clinical terms and abbreviations, **31 appear nowhere in the entire
340-variant bank**: `orthopnea`, `PND`, `paroxysmal`, `nocturnal`, `dyspnea`,
`SOB`, `DOE`, `edema`, `PMH`, `PSH`, `NKDA`, `meds`, `compliance`, `adherence`,
`hemoptysis`, `syncope`, `presyncope`, `diaphoresis`, `exertional`, `JVD`,
`pleuritic`, `purulent`, `ETOH`, and others.

Those questions do not score badly. They score **exactly 0.00**, because after
stopword removal the query shares no token with any variant. "PND?",
"orthopnea?", "meds?", "PMH?", "NKDA?" and "compliance with meds" all fall
through to the out-of-scope fallback.

This is not a matcher defect. It is bank coverage. The likely cause is section
10.4: *"The patient uses lay language, not clinical terminology."* That
constraint governs the **answers**. It appears to have been applied to the
question side as well, where it does the opposite of what is wanted.

### 2.2 No character-level robustness

Token-set Dice gives no partial credit. "ortopnea" and "strat" score 0.00. Any
typo in a content word is a total loss, and this is a tool people type into
under time pressure.

### 2.3 One similarity number cannot separate "unrelated" from "unusually phrased"

Top-score distributions overlap in both the shipped matcher and every lexical
variant I tried:

```
shipped   in-scope      min 0.00  median 0.57  max 1.00
shipped   out-of-scope  min 0.00  median 0.00  max 0.65
```

"Do you want something to drink" scores 0.65 against `last_oral_intake`. "Are
you in pain right now from the mask" scores 0.49 against `chest_pain`. Both are
above the in-scope median. No single threshold separates them, because an
unrelated question can share a high-IDF token by accident, and an in-scope
question in an unfamiliar register shares none.

This is the failure the spec itself calls the highest technical risk, and it is
right to: a fallthrough is visible to the learner, a wrong topic is not.

### 2.4 Compound questions are silently lossy

"Any chest pain or palpitations" answers palpitations and drops chest pain. The
learner has no way to know half the question was discarded, and in a case where
one of the two is a pertinent negative, they will record a negative they were
never actually given.

### 2.5 The rare-token override is dead code

The override is documented as a tiebreak for distinctive words. In practice
**393 of the 443 vocabulary words have DF ≤ 2**, so nearly every content word is
"rare" and the mechanism has no discriminating power. Run across all 340
authored variants, it changed the winning topic **zero times**.

It also `break`s after the first rare token in query order, so where it does fire
the result depends on word order in a way nothing else in the matcher does.

It is not causing harm today. It is carrying a comment claiming a role it does
not play, which is worse than absent, because the next person to read the file
will believe the problem is handled.

## 3. What a cheap lexical fix buys, and what it costs

I prototyped three changes on a scratch copy: a shared clinical lexicon mapping
abbreviations and clinical terms to the lay tokens the bank uses, a character
trigram floor for typos, and confidence bands instead of a single threshold.

| Category | Shipped | Prototype |
|---|---|---|
| A paraphrase | 84% | 92% |
| B shorthand | 42% | **83%** |
| C conversational | 60% | 40% |
| D compound | 100% | 100% |
| E typos | 25% | **75%** |
| F out of scope | 60% | **0%** |
| total | 67% | 76% |

The headline is not the 67 to 76. It is that **lexical widening trades
out-of-scope rejection for coverage, roughly one for one**. The trigram floor
that rescues "ortopnea" also gives every unrelated question a plausible-looking
score. Category F went to zero.

The conclusion I draw is that coverage and rejection are not the same axis and
cannot both be fixed by tuning similarity. Any widening has to be paired with an
explicit rejection mechanism, not with a higher threshold.

## 4. Options, cheapest first

### Tier 0. Authoring, no code

**0a. Add clinical-register variants to every topic.** The single highest-value
change, because it converts a class of total failures (score 0.00) into ordinary
matches. Does not violate section 10.4, which constrains answers.

**0b. Go from 10 variants to 20.** Section 10.1 already asks for this and calls
ten "the floor", and notes the measured error rate at the floor is not
comfortable. Every one of the 34 topics in the CHFE case is at exactly ten. The
spec's own prioritisation applies: expand first on topics where a wrong answer
changes management.

Cost: author time, and it is not small. Benefit: measurable, and it improves
every downstream option because they all match against this bank.

### Tier 1. Cheap runtime code, preserves the architecture

**1a. Confidence bands and disambiguation.** Three outcomes instead of two:
confident, ambiguous, none. On ambiguous, the *nurse* asks which one is meant
rather than the patient answering the wrong question. This converts the
dangerous invisible failure into a visible one. See the open question in §6, it
has a real pedagogical cost.

**1b. A shared clinical lexicon.** Case-independent, lives beside the action
catalog, maintained once for all cases. Measured: category B 42% to 83%.

**1c. Character trigram floor.** Measured: category E 25% to 75%. Only safe
behind 1a.

**1d. Multi-intent split.** Split on "and", "or" and commas; answer every clause
that clears the confident band, in order. Removes 2.4.

**1e. Delete or repair the rare-token override.** Either give it a real DF
threshold that makes "rare" mean something across a larger bank, or remove it
and its comment.

### Tier 2. Build-time expansion with a model

*(Partly overtaken by events. An in-browser sentence-embedding model was built
in September 2026 as `engine/semantic.js`: all-MiniLM-L6-v2, int8, about 23 MB,
loaded once from a CDN and run entirely on the learner's machine. It needs no
server, no key and no per-question cost, so it does not cost the architecture
what Tier 3 would. Bank expansion below remains worth doing independently: every
matcher, semantic included, matches against this bank.)*

Use an LLM at **authoring** time to expand each topic to 50 to 100 paraphrases
spanning lay, clinical and shorthand registers, then ship the expanded bank. No
model at runtime, so the single-file no-backend architecture survives intact and
behaviour stays deterministic.

Costs: bundle size (340 variants to roughly 2,500 needs measuring against the
current 155 KB case payload), and review burden, since section 10.1 marks
variants AI-draftable but author-spot-checked, and spot-checking 2,500 is a
different job from spot-checking 340.

### Tier 3. A model at runtime

Section 10.6 already sanctions this: *"A model may be used only to match free
text to an authored topic."* Send the question and the topic list, get back a
topic id or null. This is the only option that genuinely solves out-of-scope
rejection and compound questions rather than mitigating them.

Costs, all real:

- **Network dependency.** The simulator currently runs from a single file with
  no backend. A runtime model ends that. For a tool aimed at residents
  worldwide, some of whom will use it on poor connections, this is a product
  decision, not an implementation detail.
- **Non-determinism.** The same question can route differently on two runs. In a
  teaching tool whose debrief claims to report what the learner did, that is a
  correctness problem, not just an annoyance.
- **Cost and latency** per question, in a UI where the patient is meant to answer
  immediately.

**Hybrid, which I would argue for over pure Tier 3.** Lexical layer first; call
the model **only** when the lexical result lands in the ambiguous band. The
common path stays offline, deterministic and instant; the model is spent on the
hard cases only. It also degrades correctly: if the network is unavailable, the
ambiguous band falls back to the disambiguation prompt from 1a.

## 5. The prerequisite: a measurement harness

Section 10.6 already specifies one. A `<PREFIX>-matcher-eval.js` per case pack,
holding held-out phrasings that appear in no variant list, extracting the matcher
from the built prototype rather than reimplementing it.

**Built, September 2026: `engine/matcher_eval.mjs`,** with a seed set at
`engine/eval/interview-eval-CHFE.json`. It extracts the lexical matcher out of
`build/simulator.html` by marker comment rather than holding a copy, reports by
category, separates wrong-topic from fallthrough, flags wrong topics on
management-changing topics and pertinent negatives, and sweeps the semantic
thresholds. The seed set is the 54-question battery from section 1 of this
document and is **not author-written**: see the caveats there and the
`provenance` field in the file itself.

Nothing in section 4 should be tuned before a real held-out set exists, or the
result measures memorisation. The spec says this explicitly and it is worth
repeating.

What it needs beyond what the spec describes:

- **Held-out phrasings written by someone other than the variant author.** An
  author writing both will unconsciously write test questions in the register
  they already used, which is exactly the blind spot in 2.1.
- **Categories, not one accuracy number.** The five failure modes above have
  different fixes and different severities. A single percentage hides which one
  moved.
- **Wrong-topic rate reported separately for management-changing topics**, per
  the spec's own instruction, and separately again for pertinent negatives, where
  a wrong answer is clinically opposite to the right one.
- **An out-of-scope set large enough to matter.** The current n=5 in my battery
  and the n=5 quoted in the spec are both too small to tune against.

## 6. Open questions I cannot answer for you

1. **Is offline, no-backend a hard requirement?** It determines whether Tier 3
   exists at all. Everything else is downstream of this answer.

2. **Is a disambiguation prompt pedagogically acceptable?** This is the part of
   1a I am least sure of. "Do you mean whether he sleeps flat, or whether he
   wakes at night?" tells the resident that both are things worth asking. That is
   a hint they did not earn, delivered at the moment they were closest to
   missing something. It may be that the honest behaviour is the fallthrough,
   and that the fix belongs entirely in the bank rather than in the interaction.
   A physician educator should decide this, not me.

3. **Who writes the held-out eval set, and when?** If it is written after the
   variants by the same person, the measurement is close to worthless.

4. **How much authoring budget exists per case?** Section 10.5 already notes that
   distressed-phase answers roughly double interview authoring effort. Tier 0
   roughly doubles it again. If that budget does not exist, Tier 2 or Tier 3
   stops being an optimisation and becomes the only route.

## 7. What I would do, in order

1. ~~Build the eval harness (§5).~~ Done. Still needs a real held-out set
   written by someone other than the variant author before its numbers mean
   anything.
2. Ship confidence bands (1a), decision on the disambiguation prompt pending
   question 6.2. This addresses the failure the spec calls the highest risk.
3. Add the clinical lexicon (1b) and trigram floor (1c) behind the bands, and
   re-measure. Expect coverage up and rejection down; the bands are what keeps
   the second from becoming a wrong answer.
4. Multi-intent split (1d); delete the dead override (1e).
5. Expand variants (Tier 0) on management-changing topics first, measuring after
   each batch so the marginal value of variant number 11 through 20 is known
   rather than assumed.
6. Only then decide between Tier 2 and the hybrid, with numbers rather than
   argument.
