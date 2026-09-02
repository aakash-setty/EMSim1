/* Interview matcher evaluation for CHFE.
 *
 *   node cases/CHFE/CHFE-matcher-eval.js [build/simulator.html]
 *
 * Section 10.6 of the authoring requirements calls interview matching the highest
 * technical risk in the system, because a mismatch delivers a clinically wrong answer
 * with full confidence and, unlike a fallthrough, is invisible to the learner.
 *
 * This measures it. The matcher is extracted from the built prototype rather than
 * reimplemented, so the numbers below always describe what actually ships.
 *
 * The held-out phrasings are deliberately NOT copied from any variant list. They are
 * what a resident might type. Add to them; do not tune the matcher against them and
 * then quote the result, because that measures memorisation rather than coverage.
 */
const fs = require('fs');
const path = require('path');
const ROOT = path.dirname(path.dirname(__dirname));

const HTML = process.argv[2] || path.join(ROOT, 'build', 'simulator.html');
if (!fs.existsSync(HTML)) {
  console.error('no simulator at ' + HTML + '; run engine/build_simulator.py first');
  process.exit(2);
}
const html = fs.readFileSync(HTML, 'utf8');
const grab = id => JSON.parse(
  html.match(new RegExp('<script type="application/json" id="' + id + '">([\\s\\S]*?)</script>'))[1]);
const SHARED = grab('shared-data');
const CASES = grab('cases-data');
const pack = CASES.find(c => c.prefix === 'CHFE');
if (!pack) { console.error('CHFE is not in this build'); process.exit(2); }
global.CASE = pack.case;
global.PROTO = { matchThreshold: SHARED.matchThreshold };

/* Pull the shipped matcher out of the UI block. If this extraction fails the file
   should be fixed rather than the matcher reimplemented here, because a second copy
   would drift and then report on a matcher nobody runs. */
const start = html.indexOf('const STOP=new Set(');
const end = html.indexOf('/* ---------- events ---------- */');
if (start < 0 || end < 0 || end < start) {
  console.error('could not locate the matcher block in the prototype');
  process.exit(2);
}
eval(html.slice(start, end));
/* The weight tables are per case and are built on selection, so build them here too.
   Without this the matcher silently degrades to unweighted Dice and reports a worse
   score than the one that ships. */
if (typeof buildMatcher === 'function') buildMatcher();
else { console.error('buildMatcher missing from the extracted block'); process.exit(2); }

const held = [
  ['how many pillows do you sleep on', 'orthopnea'],
  ['can you lie flat', 'orthopnea'],
  ['do you wake up at night gasping', 'paroxysmal_nocturnal_dyspnea'],
  ['have you been taking your water tablet', 'medication_adherence'],
  ['did you run out of any of your pills', 'medication_adherence'],
  ['any pain in your chest', 'chest_pain'],
  ['are your ankles swollen', 'leg_swelling'],
  ['have you put on weight recently', 'weight_gain'],
  ['do you smoke', 'social_history_smoking_alcohol'],
  ['what medicines are you on', 'current_medications'],
  ['are you allergic to anything', 'allergies'],
  ['have you had a fever', 'fever_and_chills'],
  ['do you snore at night', 'sleep_apnea_and_snoring'],
  ['have you been coughing anything up', 'cough_and_sputum'],
  ['when did you last eat', 'last_oral_intake'],
  ['have you travelled recently', 'travel_immobility_surgery'],
  ['any calf pain', 'calf_pain_or_asymmetry'],
  ['do you use cocaine', 'substance_use_stimulants'],
  ['what happened to your heart before', 'past_medical_history'],
  ['how much salt do you eat', 'dietary_sodium'],
  ['how far can you normally walk', 'functional_baseline'],
  ['are you passing urine normally', 'urine_output'],
  ['have you coughed up any blood', 'hemoptysis'],
  ['does anything make it better', 'relieving_factors'],
  ['what does the breathlessness feel like', 'character_of_dyspnea'],
];

/* Questions the case does not cover. These should fall through, not be answered. */
const outOfScope = [
  'what is your favourite colour',
  'who is the prime minister',
  'do you like football',
  'what is my name',
  'have you got a dog',
];

/* Topics whose answer changes management. A wrong topic here is worse than a
   wrong topic elsewhere, because the resident acts on it. */
const CRITICAL_TOPICS = new Set([
  'medication_adherence', 'chest_pain', 'orthopnea',
  'paroxysmal_nocturnal_dyspnea', 'substance_use_stimulants',
  'calf_pain_or_asymmetry', 'fever_and_chills',
]);

let right = 0, wrong = 0, fell = 0, criticalWrong = 0;
const misses = [];
for (const [q, want] of held) {
  const got = matchTopic(q).topic;
  if (got === want) right++;
  else if (got === null) { fell++; misses.push(['fell through', q, want, '']); }
  else {
    wrong++;
    if (CRITICAL_TOPICS.has(want) || CRITICAL_TOPICS.has(got)) criticalWrong++;
    misses.push(['wrong topic', q, want, got]);
  }
}
let falsePos = 0;
for (const q of outOfScope) {
  const got = matchTopic(q).topic;
  if (got) { falsePos++; misses.push(['answered anyway', q, '(none)', got]); }
}

console.log('matcher threshold: ' + PROTO.matchThreshold);
console.log('topics: ' + CASE.interview.topics.length +
            ', variants: ' + CASE.interview.topics.reduce((n, t) => n + (t.variants || []).length, 0));
console.log('');
for (const [kind, q, want, got] of misses) {
  console.log('  ' + kind.padEnd(15) + '"' + q + '"' +
              (want !== '(none)' ? '  wanted ' + want : '') +
              (got ? '  got ' + got : ''));
}
console.log('');
console.log('held-out phrasings: ' + right + ' correct, ' + wrong + ' wrong topic, ' +
            fell + ' fell through, of ' + held.length);
console.log('wrong topic on a management-changing topic: ' + criticalWrong +
            '   <- the number that matters most');
console.log('out-of-scope: ' + (outOfScope.length - falsePos) + '/' + outOfScope.length +
            ' correctly unmatched');
console.log('');
console.log('A fallthrough is visible to the learner. A wrong topic is not.');
