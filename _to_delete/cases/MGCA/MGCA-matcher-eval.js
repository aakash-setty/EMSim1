/* Interview matcher evaluation for MGCA.
 *
 *   node cases/MGCA/MGCA-matcher-eval.js [build/simulator.html]
 *
 * Section 10.6 calls interview matching the highest technical risk in the system,
 * because a mismatch delivers a clinically wrong answer with full confidence and,
 * unlike a fallthrough, is invisible to the learner.
 *
 * The matcher is extracted from the built prototype rather than reimplemented, so the
 * numbers describe what actually ships. A second copy would drift and then report on a
 * matcher nobody runs.
 *
 * The held-out phrasings live in MGCA-matcher-eval-questions.json and are stratified by
 * register: paraphrase, shorthand, typo, compound, conversational. Section 10.6 is
 * explicit that an author-written set of well-formed lay sentences will report that the
 * matcher is fine no matter what has been done to it, which is why the registers are
 * separated and reported separately here.
 *
 * Do not tune the matcher against this set and then quote the result. That measures
 * memorisation rather than coverage.
 */
const fs = require('fs');
const path = require('path');
const HERE = __dirname;
const ROOT = path.dirname(path.dirname(HERE));

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
const pack = CASES.find(c => c.prefix === 'MGCA');
if (!pack) { console.error('MGCA is not in this build'); process.exit(2); }
global.CASE = pack.case;
global.PROTO = { matchThreshold: SHARED.matchThreshold };

/* The end marker is the fusion block, not the events block: between the lexical
   matcher and the events handler sit the semantic fusion rule and a top-level
   SEM.onChange registration, and evaluating those here throws because semantic.js is
   not loaded. Ending at the fusion comment takes the lexical matcher and nothing else,
   which is also what this measures: the matcher that runs before, and instead of, the
   embedding model. */
const start = html.indexOf('const STOP=new Set(');
const end = html.indexOf('/* ---------- fusion of the lexical and semantic matchers ----------');
if (start < 0 || end < 0 || end < start) {
  console.error('could not locate the matcher block in the prototype');
  process.exit(2);
}
eval(html.slice(start, end));
if (typeof buildMatcher === 'function') buildMatcher();
else { console.error('buildMatcher missing from the extracted block'); process.exit(2); }

const SET = JSON.parse(fs.readFileSync(path.join(HERE, 'MGCA-matcher-eval-questions.json'), 'utf8'));

/* Topics whose answer changes management. A wrong topic here is worse than a wrong
   topic elsewhere, because the resident acts on it. Neck stiffness and photophobia
   decide whether this reads as meningitis; the tampon question is what excludes toxic
   shock; the medication history is where the ibuprofen that worsened the kidney lives;
   tick exposure is the Rocky Mountain spotted fever discriminator. */
const CRITICAL_TOPICS = new Set([
  'neck_stiffness', 'photophobia', 'menstrual_and_tampon', 'tick_and_outdoor_exposure',
  'current_medications', 'vaccinations', 'rash', 'urine_output', 'sick_contacts',
]);

const inScope = SET.questions.filter(q => q.expected_topic && q.expected_topic !== '__ambiguous__');
const ambiguous = SET.questions.filter(q => q.expected_topic === '__ambiguous__');
const outOfScope = SET.questions.filter(q => q.expected_topic === null);

const byRegister = {};
let right = 0, wrong = 0, fell = 0, criticalWrong = 0;
const misses = [];

for (const q of inScope) {
  const got = matchTopic(q.q).topic;
  const r = byRegister[q.register] = byRegister[q.register] || { ok: 0, n: 0 };
  r.n++;
  if (got === q.expected_topic) { right++; r.ok++; }
  else if (got === null) { fell++; misses.push(['fell through', q.register, q.q, q.expected_topic, '']); }
  else {
    wrong++;
    if (CRITICAL_TOPICS.has(q.expected_topic) || CRITICAL_TOPICS.has(got)) criticalWrong++;
    misses.push(['wrong topic', q.register, q.q, q.expected_topic, got]);
  }
}

let falsePos = 0;
for (const q of outOfScope) {
  const got = matchTopic(q.q).topic;
  if (got) { falsePos++; misses.push(['answered anyway', q.register, q.q, '(none)', got]); }
}

console.log('matcher threshold: ' + PROTO.matchThreshold);
console.log('topics: ' + CASE.interview.topics.length +
            ', variants: ' + CASE.interview.topics.reduce((n, t) => n + (t.variants || []).length, 0));
console.log('');
for (const [kind, reg, q, want, got] of misses) {
  console.log('  ' + kind.padEnd(15) + '[' + reg + '] "' + q + '"' +
              (want !== '(none)' ? '  wanted ' + want : '') +
              (got ? '  got ' + got : ''));
}
console.log('');
for (const reg of Object.keys(byRegister).sort()) {
  const r = byRegister[reg];
  console.log('  ' + reg.padEnd(16) + r.ok + '/' + r.n);
}
console.log('');
console.log('held-out phrasings: ' + right + ' correct, ' + wrong + ' wrong topic, ' +
            fell + ' fell through, of ' + inScope.length);
console.log('wrong topic on a management-changing topic: ' + criticalWrong +
            '   <- the number that matters most');
console.log('out-of-scope: ' + (outOfScope.length - falsePos) + '/' + outOfScope.length +
            ' correctly unmatched   <- ' + outOfScope.length +
            ' is far too few to conclude anything; 30 is the floor');
if (ambiguous.length)
  console.log('excluded as ambiguous: ' + ambiguous.length +
              ' (no single right answer, kept in the file for review)');
console.log('');
console.log('A fallthrough is visible to the learner. A wrong topic is not.');
