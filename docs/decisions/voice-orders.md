# Orders that are spoken

Design v0.13. One feature, five decisions, and the alternatives that were set aside.
Kept for what was rejected. The current behaviour is described at the top of
`engine/voice.js` and `catalog/build_voice_aliases.py`; this file is not a source of
truth for how the system behaves.

---

## 1. The recogniser is the browser's

**Decision.** Speech is transcribed by the Web Speech API. Chrome and Edge send the
audio to Google's service, Safari to Apple's, Firefox has no implementation. The button
opens the same dropdown with a text box wherever recognition is missing or refused.

**Why.** It is zero bytes in the bundle and zero seconds to first use, and the
transcript it returns for medical vocabulary spoken in a quiet room is good. The
alternative was measured against the interview matcher's experience, below.

### Rejected: an in-browser model (Whisper through transformers.js)

The simulator already carries an optional embedding model for the interview, so the
loading path exists. Rejected for three reasons that compound. A speech model small
enough to load in a browser is about forty megabytes and is measurably worse on drug
names than the vendor services; the interview matcher's own history is that a model
which may never load must not be load-bearing, and a microphone that works only after a
download the hospital network may block is a microphone that does not work; and the
recording pipeline (a worker, chunking, voice activity detection) would be the largest
single piece of code in `engine/` for a feature whose parser is the actual work.
Reconsider when a deployment needs the spoken path to be offline. Until then the offline
path is the typed one, and it is the same parser.

### Rejected: a server

There is no server, and section 1 of the design says there will not be one.

---

## 2. The terminology is a generated table keyed by catalog id

**Decision.** `catalog/voice-aliases.json` is written by a Python script from phrases
authored in that script, keyed by catalog id, and resolved to the case's action ids by
the engine when the case is bound. The engine also derives phrases from every display
name, so an entry with no row is still orderable by its button.

**Why.** Section 2 of the layout rule: nothing in `engine/` names a drug. A parser with
"rocephin" in it would be that. Keying by catalog id rather than case id is what lets
one table serve every case, including the ones that rename an entry.

### Rejected: aliases as a field on each catalog entry

Cleaner in principle. Rejected because the alias table is a different kind of content
from the catalog: it changes when someone notices a phrase the microphone missed, which
is weekly, where the catalog changes when the clinical surface changes, which is rarely,
and a review of the catalog should not have to read past four thousand phrases.

### Rejected: hand-written JSON

The table has combinatorial rows (a fluid with a volume, a drip with a stop word), and
those are far easier to read as three short lists and a loop than as the hundred lines
they expand to. The script is the readable form; the JSON is the artifact.

---

## 3. The parser does not answer the case

**Decision.** A phrase that names a diagnosis rather than an order ("sepsis workup",
"hyperkalemia cocktail", "meningitis coverage") is refused with a hint to name the
studies or drugs. A phrase that could mean two entries is returned as a choice. A drug
the catalog lacks is refused rather than swapped for the nearest one it has. Two
author-stated conventions are recorded as exceptions: a bare "calcium" is the level, and
CMP is the Chem 7 plus the hepatic panel.

**Why.** The simulator scores whether the resident ordered the right things. A
microphone that turns "sepsis workup" into lactate, cultures, CBC and a chemistry has
ordered them, and the score would credit the parser. The same applies more quietly to
substitution: a resident who says calcium gluconate and is given calcium chloride has not
been taught that the catalog carries one and not the other, they have been corrected
without noticing.

### Rejected: resolve ambiguity by frequency

"Epi" is usually the code dose in an arrest and usually the intramuscular dose in
anaphylaxis, and the parser does not know which room it is in. A choice in the row costs
one click and never orders the wrong drug.

---

## 4. Doses, routes and reasons are stripped, not parsed

**Decision.** Units, numbers that discriminate nothing, and a reason after the order are
removed before lookup. A number survives only where it selects an entry (500 against a
litre, fifteen litres on a mask, three percent against twenty-three). Route words
(bolus, drip, IM, sublingual) survive because they select entries.

**Why.** The catalog has no dose field a spoken dose could fill, so parsing one would
produce a number nothing reads. The interface already narrates a dose from the entry's
template. Stripping is also what keeps the table small: without it every drug needs
every dose it is said with.

### Rejected: reject an order spoken without a dose

Considered as a teaching point. Rejected because the tabs do not require one either,
and a microphone stricter than the buttons would only push residents back to the buttons.

---

## 5. Two normalisers, one test, a fixed point

**Decision.** The Python script normalises every phrase before storing it; `voice.js`
carries the same pipeline for speech; `engine-tests.js` normalises the shipped table
with the JS pipeline and requires every phrase back unchanged. Both pipelines iterate to
a fixed point, bounded at four rounds.

**Why.** The two pipelines are the same pipeline only for as long as somebody checks,
and the check is cheap. The fixed point was not in the first version: dropping "by" from
"oxygen by mask" produced "oxygen mask", which a rule names, and "kidney function"
became "renal function", which another rule names, and eight phrases shipped half
normalised. The test found them; the loop fixed them.

### Rejected: one implementation, shared

The script could emit the normaliser as JavaScript, or the build could run the JS
through Node. Rejected because the build must not need Node (section 1: no
dependencies), and generating JavaScript from Python to avoid writing thirty lines twice
is the kind of cleverness this repository has been at pains to avoid.

---

## Known gaps

Recognition quality is the vendor's and varies with accent and room. A misheard drug
name that is more than one letter from any phrase is shown as not understood rather
than guessed, which is the safe failure but a frequent one for polysyllabic generics;
the fix is a row in the table, and the table is where such fixes belong. The parser
knows no doses, so "two units" of blood is one transfusion and "another liter" is one
litre. Consults and exams are not spoken; the author asked for investigations and
interventions, and stabilization was added by agreement.
