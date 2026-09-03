#!/usr/bin/env node
/* ============================================================
   Matcher evaluation and threshold calibration.

     node engine/matcher_eval.mjs                       lexical only
     node engine/matcher_eval.mjs --semantic            add the embedding matcher
     node engine/matcher_eval.mjs --semantic --sweep    and sweep the thresholds

   Section 10.6 of the authoring requirements asks for exactly this, and asks
   for one thing that is easy to get wrong: the matcher under test is EXTRACTED
   FROM THE BUILT PROTOTYPE rather than reimplemented here. A second copy of the
   matching logic drifts, and then the evaluation reports on a matcher nobody
   runs. If the build changes shape and extraction fails, this script stops with
   an error rather than falling back to a copy.

   It also warns about the other trap named in 10.6: do not tune the thresholds
   against a held-out set and then quote that set's accuracy. Tune on one set,
   quote another.

   The semantic pass downloads all-MiniLM-L6-v2 (about 23 MB) on first run and
   needs the package installed:

     npm install @huggingface/transformers@4.2.0
   ============================================================ */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const BUILT = path.join(ROOT, 'build', 'simulator.html');

const argv = new Set(process.argv.slice(2));
const WANT_SEMANTIC = argv.has('--semantic');
const WANT_SWEEP = argv.has('--sweep');

/* ---------- load the built prototype ---------- */
if (!fs.existsSync(BUILT)) {
  console.error(`no build at ${BUILT}\nrun: python3 engine/build_simulator.py`);
  process.exit(1);
}
const html = fs.readFileSync(BUILT, 'utf8');

function jsonBlock(id) {
  const m = html.match(new RegExp(`<script type="application/json" id="${id}">([\\s\\S]*?)</script>`));
  if (!m) throw new Error(`could not find the ${id} block in the build`);
  return JSON.parse(m[1]);
}
const SHARED = jsonBlock('shared-data');
const PACKS = jsonBlock('cases-data');

/* ---------- extract the shipped lexical matcher ---------- */
const START = '/* ---------- interview matching (section 10.6) ---------- */';
const END = '/* ---------- fusion of the lexical and semantic matchers ----------';
const i = html.indexOf(START), j = html.indexOf(END);
if (i < 0 || j < 0 || j < i) {
  console.error('could not extract the matcher from the build.\n'
    + 'The marker comments in engine/ui.js changed. Fix the markers in this script\n'
    + 'rather than pasting a copy of the matcher here: section 10.6 requires that\n'
    + 'the evaluation runs the matcher that actually ships.');
  process.exit(1);
}
const matcherSrc = html.slice(i, j);

function makeLexical(CASE) {
  const PROTO = { matchThreshold: SHARED.matchThreshold };
  const fn = new Function('CASE', 'PROTO',
    `${matcherSrc}\n buildMatcher(); return { matchTopic, norm, DF: () => DF };`);
  return fn(CASE, PROTO);
}

/* ---------- eval set ---------- */
function loadEval(prefix) {
  const p = path.join(HERE, 'eval', `interview-eval-${prefix}.json`);
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

/* ---------- semantic matcher, same model and settings as the browser ---------- */
async function makeSemantic(CASE) {
  let lib;
  try { lib = await import('@huggingface/transformers'); }
  catch (e) {
    console.error('\n--semantic needs the library:  npm install @huggingface/transformers@4.2.0\n');
    process.exit(1);
  }
  lib.env.allowLocalModels = false;
  const extractor = await lib.pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2', { dtype: 'q8' });
  const rows = [];
  for (const t of CASE.interview.topics)
    for (const f of [t.canonical].concat(t.variants || [])) rows.push({ topic: t.topic, form: f });

  const DIM = 384;
  const bank = new Float32Array(rows.length * DIM);
  for (let k = 0; k < rows.length; k += 32) {
    const chunk = rows.slice(k, k + 32).map(r => r.form);
    const out = await extractor(chunk, { pooling: 'mean', normalize: true });
    bank.set(out.data.subarray(0, chunk.length * DIM), k * DIM);
    process.stdout.write(`\rembedding bank ${Math.min(k + 32, rows.length)}/${rows.length}   `);
  }
  process.stdout.write('\r' + ' '.repeat(40) + '\r');

  return async function best(q) {
    const out = await extractor([q], { pooling: 'mean', normalize: true });
    const v = out.data;
    const by = Object.create(null);
    for (let r = 0; r < rows.length; r++) {
      let dot = 0; const off = r * DIM;
      for (let d = 0; d < DIM; d++) dot += v[d] * bank[off + d];
      const t = rows[r].topic;
      if (!(t in by) || dot > by[t]) by[t] = dot;
    }
    let top = null, s = -1;
    for (const t in by) if (by[t] > s) { s = by[t]; top = t; }
    return { topic: top, score: s };
  };
}

/* ---------- the fusion rule, mirroring engine/semantic.js ---------- */
function fuse(lex, sem, A, G, V) {
  if (!sem) return { topic: lex.topic, by: 'lexical' };
  if (sem.score >= A) return { topic: sem.topic, by: 'semantic' };
  if (sem.score >= G && sem.topic === lex.topic) return { topic: sem.topic, by: 'both' };
  if (sem.score < V) return { topic: null, by: 'veto' };
  return { topic: lex.topic, by: 'lexical' };
}

/* ---------- scoring ----------
   Reported separately, because they are not equally bad. A fallthrough is
   visible to the learner. A wrong topic is not, and a wrong topic on a
   pertinent negative is clinically opposite to the right answer. */
function score(cases, resolve, critical) {
  const cat = {}, tally = { hit: 0, wrong: 0, fell: 0, falsePos: 0, trueNeg: 0, criticalWrong: [] };
  for (const c of cases) {
    const got = resolve(c);
    const exp = c.expect;                       // null means out of scope
    const ok = exp === null ? got === null : (Array.isArray(exp) ? exp : [exp]).includes(got);
    cat[c.category] = cat[c.category] || { n: 0, ok: 0 };
    cat[c.category].n++; if (ok) cat[c.category].ok++;
    if (exp === null) { if (got === null) tally.trueNeg++; else tally.falsePos++; }
    else if (ok) tally.hit++;
    else if (got === null) tally.fell++;
    else {
      tally.wrong++;
      if (critical.has(got) || critical.has(Array.isArray(exp) ? exp[0] : exp))
        tally.criticalWrong.push(`${c.q}  ->  ${got}  (wanted ${exp})`);
    }
  }
  return { cat, tally };
}

function report(title, r, n) {
  const t = r.tally;
  console.log(`\n== ${title} ==`);
  for (const k of Object.keys(r.cat).sort())
    console.log(`   ${k}  ${r.cat[k].ok}/${r.cat[k].n}  ${Math.round(100 * r.cat[k].ok / r.cat[k].n)}%`);
  const acc = Object.values(r.cat).reduce((a, c) => a + c.ok, 0);
  console.log(`   total ${acc}/${n}  ${Math.round(100 * acc / n)}%`);
  console.log(`   in scope:  ${t.hit} correct, ${t.wrong} WRONG TOPIC, ${t.fell} fell through`);
  console.log(`   out of scope: ${t.trueNeg} correctly refused, ${t.falsePos} answered anyway`);
  if (t.criticalWrong.length) {
    console.log(`   wrong topic where it changes management or flips a pertinent negative:`);
    for (const s of t.criticalWrong) console.log(`     ${s}`);
  }
}

/* ---------- run ---------- */
for (const pack of PACKS) {
  const CASE = pack.case;
  const set = loadEval(pack.prefix);
  console.log('\n' + '='.repeat(66));
  console.log(`${pack.prefix}  ${CASE.case_id}   ${CASE.interview.topics.length} topics, `
    + `${CASE.interview.topics.reduce((a, t) => a + (t.variants || []).length, 0)} variants`);
  if (!set) { console.log(`  no eval set at engine/eval/interview-eval-${pack.prefix}.json, skipped`); continue; }
  if (set.provenance) console.log(`  eval set: ${set.provenance}`);
  console.log('='.repeat(66));

  const critical = new Set(
    (set.management_changing || []).concat(
      CASE.interview.topics.filter(t => t.pertinent_negative).map(t => t.topic)));

  const lex = makeLexical(CASE);
  const lexOut = new Map(set.cases.map(c => [c.q, lex.matchTopic(c.q)]));
  report('lexical only, the matcher that ships today',
    score(set.cases, c => lexOut.get(c.q).topic, critical), set.cases.length);

  if (!WANT_SEMANTIC) continue;

  const best = await makeSemantic(CASE);
  const semOut = new Map();
  for (const c of set.cases) semOut.set(c.q, await best(c.q));

  const A = 0.62, G = 0.45, V = 0.28;   // keep in step with engine/semantic.js
  report(`lexical + semantic  (ACCEPT ${A}, AGREE ${G}, VETO ${V})`,
    score(set.cases, c => fuse(lexOut.get(c.q), semOut.get(c.q), A, G, V).topic, critical),
    set.cases.length);

  /* Separability. If the in-scope and out-of-scope score ranges overlap, no
     choice of VETO separates them and the fix is not a threshold. */
  const inS = set.cases.filter(c => c.expect !== null).map(c => semOut.get(c.q).score);
  const outS = set.cases.filter(c => c.expect === null).map(c => semOut.get(c.q).score);
  const stat = a => a.length ? `min ${Math.min(...a).toFixed(2)}  median ${a.slice().sort((x, y) => x - y)[a.length >> 1].toFixed(2)}  max ${Math.max(...a).toFixed(2)}` : 'none';
  console.log(`\n   cosine, in scope:     ${stat(inS)}`);
  console.log(`   cosine, out of scope: ${stat(outS)}`);
  if (outS.length < 20)
    console.log(`   WARNING: only ${outS.length} out-of-scope questions. Too few to tune VETO against.`);

  if (WANT_SWEEP) {
    console.log('\n   threshold sweep (correct / wrong topic / fell through / false positive)');
    for (const a of [0.50, 0.55, 0.60, 0.62, 0.65, 0.70, 0.75]) {
      const line = [];
      for (const v of [0.00, 0.25, 0.30, 0.35, 0.40]) {
        const r = score(set.cases, c => fuse(lexOut.get(c.q), semOut.get(c.q), a, G, v).topic, critical).tally;
        line.push(`V${v.toFixed(2)} ${r.hit}/${r.wrong}/${r.fell}/${r.falsePos}`);
      }
      console.log(`   ACCEPT ${a.toFixed(2)}  ` + line.join('   '));
    }
    console.log('\n   Pick from this table by asking which column has the fewest WRONG TOPIC');
    console.log('   results, not the highest total. Then quote a different eval set.');
  }
}
