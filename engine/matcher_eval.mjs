#!/usr/bin/env node
/* ============================================================
   Interview matcher evaluation, all packs, one harness.

     node engine/matcher_eval.mjs                          lexical only
     node engine/matcher_eval.mjs --semantic               add the embedding matcher and the shipped fusion
     node engine/matcher_eval.mjs --semantic --sweep       sweep the fusion thresholds on the TUNING set
     node engine/matcher_eval.mjs --semantic --model-path DIR
                                                           load the model from a local directory laid out
                                                           as transformers.js expects (Xenova/<id>/...)

   Section 10.6 of the authoring requirements asks for this and names the two
   traps it is easy to fall into:

   1. The matcher under test is EXTRACTED FROM THE BUILT PROTOTYPE, never
      reimplemented here. A second copy drifts and then reports on a matcher
      nobody runs. If the build changes shape and extraction fails, this script
      stops rather than falling back to a copy. The same goes for the fusion
      thresholds: they are read out of the build's semantic block.

   2. Tuning against a held-out set and quoting that set measures memorisation.
      So there are two kinds of question file:

        cases/<P>/<P>-matcher-eval-questions.json    HELD OUT. Author-written, never
                                                     tuned against, the numbers quoted.
        cases/<P>/<P>-matcher-tune-questions.json    TUNING. Phrasings withheld from the
                                                     variant bank at expansion time.
                                                     --sweep reads only this file.

      When no tuning file exists, --sweep refuses to run on the held-out set.

   The three reported numbers are not equally bad, and the report keeps them
   apart. A fallthrough is visible to the learner, who can rephrase. A wrong
   topic is not, and on a pertinent negative it is clinically opposite to the
   right answer. An out-of-scope question answered anyway is a wrong topic the
   learner had no way to expect.
   ============================================================ */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const flag = n => args.includes(n);
const opt = (n, d) => { const i = args.indexOf(n); return i >= 0 && args[i + 1] ? args[i + 1] : d; };

const ROOT = path.resolve(opt('--root', path.resolve(HERE, '..')));
const BUILT = path.resolve(opt('--build', path.join(ROOT, 'build', 'simulator.html')));
const CASES_DIR = path.resolve(opt('--cases', path.join(ROOT, 'cases')));
const WANT_SEMANTIC = flag('--semantic');
const WANT_SWEEP = flag('--sweep');
const MODEL_PATH = opt('--model-path', null);
const ONLY = opt('--only', null);
const VERBOSE = flag('--verbose');

/* ---------- the build ---------- */
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

/* ---------- the shipped lexical matcher, extracted ---------- */
const START = '/* ---------- interview matching (section 10.6) ---------- */';
const END = '/* ---------- fusion of the lexical and semantic matchers ----------';
const si = html.indexOf(START), ei = html.indexOf(END);
if (si < 0 || ei < 0 || ei < si) {
  console.error('could not extract the matcher from the build: the marker comments in engine/ui.js changed.\n'
    + 'Fix the markers here rather than pasting a copy of the matcher: section 10.6 requires\n'
    + 'that the evaluation runs the matcher that ships.');
  process.exit(1);
}
const matcherSrc = html.slice(si, ei);
/* The fusion region holds matchOne, splitClauses and matchQuestion: the code that
   decides how many answers a question gets and which matcher produced each. It refers
   to SEM, so it is run with a shim whose best() is this harness's embedding of the same
   model, and whose thresholds are the build's own. */
const FEND = 'function bindCase(){';
const fi = html.indexOf(FEND, ei);
if (fi < 0) { console.error('could not find the end of the fusion region (function bindCase)'); process.exit(1); }
const fusionSrc = html.slice(ei, fi);

function makeShipped(CASE, semBest, fuseOverride) {
  const PROTO = { matchThreshold: SHARED.matchThreshold, interviewDefaults: SHARED.interviewDefaults || {} };
  const SEM = { ready: () => !!semBest, best: async q => semBest ? semBest(q) : null };
  const fn = new Function('CASE', 'PROTO', 'SEM', 'FUSE_OVERRIDE',
    `${matcherSrc}\n${fusionSrc}\n buildMatcher(); return { matchTopic, matchOne, matchQuestion, matchTopics, semanticRows, rankTopics, OOS_TOPIC };`);
  return fn(CASE, PROTO, SEM, fuseOverride || null);
}

/* ---------- the shipped fusion parameters, read from the build ---------- */
function shippedFuse() {
  const m = html.match(/const\s+FUSE\s*=\s*(\{[^}]*\})/);
  if (!m) throw new Error('could not read FUSE={...} from the build');
  return new Function(`return ${m[1]}`)();
}
function shippedModelId() {
  const m = html.match(/const\s+MODEL_ID\s*=\s*'([^']+)'/);
  return m ? m[1] : 'Xenova/all-MiniLM-L6-v2';
}

/* ---------- question sets ---------- */
function loadQuestions(prefix, kind) {
  const out = [];
  const perPack = path.join(CASES_DIR, prefix, `${prefix}-matcher-${kind}-questions.json`);
  let critical = [];
  if (fs.existsSync(perPack)) {
    const j = JSON.parse(fs.readFileSync(perPack, 'utf8'));
    critical = j.management_changing || [];
    for (const q of (j.questions || [])) {
      const e = q.expect !== undefined ? q.expect : (q.expected_topic === undefined ? null : q.expected_topic);
      out.push({ q: q.q, expect: e, register: q.register || 'unlabelled', source: path.basename(perPack) });
    }
  }
  /* Ambiguous rows are kept in the files for review and excluded from scoring. */
  return { rows: out.filter(x => x.expect !== '__ambiguous__'), critical };
}

/* ---------- semantic matcher, same model and settings as the browser ---------- */
async function loadExtractor() {
  let lib;
  try { lib = await import('@huggingface/transformers'); }
  catch (e) {
    console.error('\n--semantic needs the library:  npm install @huggingface/transformers@4.2.0\n');
    process.exit(1);
  }
  if (MODEL_PATH) { lib.env.allowRemoteModels = false; lib.env.localModelPath = MODEL_PATH; }
  else lib.env.allowLocalModels = false;
  const id = shippedModelId();
  const extractor = await lib.pipeline('feature-extraction', id, { dtype: 'q8' });
  return { extractor, id };
}
const DIM = 384;
/* Mirrors SEM.init() + SEM.best() in engine/semantic.js: the same rows (topics plus the
   out-of-scope pseudo-topic, taken from the shipped matchTopics()), max cosine per
   topic, and the per-topic score map the fusion consumes. This is the one piece of
   matching logic the harness reproduces rather than extracts, because the browser
   module wraps a model download; keep it in step with semantic.js. */
async function makeSemantic(CASE, extractor, topicsList) {
  const rows = [];
  for (const t of topicsList)
    for (const f of [t.canonical].concat(t.variants || [])) rows.push({ topic: t.topic, form: f });
  const bank = new Float32Array(rows.length * DIM);
  for (let k = 0; k < rows.length; k += 32) {
    const chunk = rows.slice(k, k + 32).map(r => r.form);
    const out = await extractor(chunk, { pooling: 'mean', normalize: true });
    bank.set(out.data.subarray(0, chunk.length * DIM), k * DIM);
  }
  /* Mirrors SEM.best(): max cosine per topic, and the margin to the runner-up. */
  const cache = new Map();
  return async function best(q) {
    if (cache.has(q)) return cache.get(q);
    const out = await extractor([q], { pooling: 'mean', normalize: true });
    const v = out.data;
    const by = Object.create(null);
    for (let r = 0; r < rows.length; r++) {
      let dot = 0; const off = r * DIM;
      for (let d = 0; d < DIM; d++) dot += v[d] * bank[off + d];
      const t = rows[r].topic;
      if (!(t in by) || dot > by[t]) by[t] = dot;
    }
    const ranked = Object.entries(by).sort((a, b) => b[1] - a[1]);
    const res = { topic: ranked[0][0], score: ranked[0][1],
                  margin: ranked[0][1] - (ranked[1] ? ranked[1][1] : 0), ranked, scores: by };
    cache.set(q, res);
    return res;
  };
}

/* ---------- scoring ---------- */
/* `resolve` returns the list of topics the question was answered with (null entries
   are fallthroughs). A question is correct only when that list, as a set, equals the
   expected set: a compound question answered by one of its two topics is a partial,
   and a single question answered with a spurious second topic is an extra. Both are
   reported as their own kind rather than folded into "wrong". */
function score(set, resolve, critical) {
  const reg = {};
  const t = { hit: 0, wrong: 0, partial: 0, extra: 0, fell: 0, falsePos: 0, trueNeg: 0, criticalWrong: [], misses: [] };
  for (const c of set) {
    const raw = resolve(c) || [];
    const gotList = raw.filter(x => x !== undefined);
    const got = [...new Set(gotList.filter(x => x !== null))];
    const exp0 = c.expect === null ? [] : (Array.isArray(c.expect) ? c.expect : [c.expect]);
    if (raw.clarify) {
      reg[c.register] = reg[c.register] || { n: 0, ok: 0 }; reg[c.register].n++;
      t.clarify = (t.clarify || 0) + 1;
      const covered = exp0.length && exp0.some(x => raw.clarify.includes(x));
      t.misses.push([covered ? 'asked to clarify (right pair)' : 'asked to clarify', c.register, c.q, exp0.join('+') || '(none)', raw.clarify.join(' or ')]);
      continue;
    }
    const exp = c.expect;
    const expList = exp === null ? [] : (Array.isArray(exp) ? exp : [exp]);
    reg[c.register] = reg[c.register] || { n: 0, ok: 0 };
    reg[c.register].n++;
    const same = got.length === expList.length && expList.every(x => got.includes(x));
    if (exp === null) {
      if (!got.length) { t.trueNeg++; reg[c.register].ok++; }
      else { t.falsePos++; t.misses.push(['answered anyway', c.register, c.q, '(none)', got.join('+')]); }
      continue;
    }
    if (same) { t.hit++; reg[c.register].ok++; continue; }
    if (!got.length) { t.fell++; t.misses.push(['fell through', c.register, c.q, expList.join('+'), '']); continue; }
    const overlap = expList.filter(x => got.includes(x)).length;
    if (overlap === expList.length) { t.extra++; t.misses.push(['extra answer', c.register, c.q, expList.join('+'), got.join('+')]); continue; }
    if (overlap > 0) { t.partial++; t.misses.push(['partial', c.register, c.q, expList.join('+'), got.join('+')]); continue; }
    t.wrong++;
    t.misses.push(['wrong topic', c.register, c.q, expList.join('+'), got.join('+')]);
    if (got.some(g => critical.has(g)) || expList.some(x => critical.has(x)))
      t.criticalWrong.push(`${c.q}  ->  ${got.join('+')}  (wanted ${expList.join('+')})`);
  }
  const inN = set.filter(c => c.expect !== null).length, outN = set.length - inN;
  return { reg, t, inN, outN };
}
function line(r) {
  const { t, inN, outN } = r;
  const pct = (a, b) => b ? `${Math.round(100 * a / b)}%` : '–';
  return `in-scope ${t.hit}/${inN} (${pct(t.hit, inN)})  wrong ${t.wrong}  partial ${t.partial}  extra ${t.extra}  fell ${t.fell}  clarify ${t.clarify || 0}  `
       + `critical-wrong ${t.criticalWrong.length}   out-of-scope refused ${t.trueNeg}/${outN} (${pct(t.trueNeg, outN)})`;
}
function report(title, r) {
  console.log(`\n  ${title}`);
  console.log(`    ${line(r)}`);
  const regs = Object.keys(r.reg).sort();
  console.log('    ' + regs.map(k => `${k} ${r.reg[k].ok}/${r.reg[k].n}`).join('   '));
  if (r.t.criticalWrong.length) {
    console.log('    wrong on a management-changing topic:');
    for (const s of r.t.criticalWrong) console.log('      ' + s);
  }
  if (VERBOSE) for (const [k, reg, q, want, got] of r.t.misses)
    console.log(`      ${k.padEnd(15)} [${reg}] "${q}"` + (want !== '(none)' ? `  wanted ${want}` : '') + (got ? `  got ${got}` : ''));
}

/* ---------- run ---------- */
let ext = null;
if (WANT_SEMANTIC) {
  const r = await loadExtractor();
  ext = r.extractor;
  console.log(`semantic model: ${r.id}${MODEL_PATH ? '  (local: ' + MODEL_PATH + ')' : '  (remote)'}`);
}
const FUSE = WANT_SEMANTIC ? shippedFuse() : null;
if (FUSE) console.log(`shipped fusion: ${JSON.stringify(FUSE)}`);

const summary = [];
for (const pack of PACKS) {
  if (ONLY && pack.prefix !== ONLY) continue;
  const CASE = pack.case;
  const heldSet = loadQuestions(pack.prefix, 'eval'), tuneSet = loadQuestions(pack.prefix, 'tune');
  const held = heldSet.rows, tune = tuneSet.rows;
  const nVar = CASE.interview.topics.reduce((a, t) => a + (t.variants || []).length, 0);
  console.log('\n' + '='.repeat(72));
  console.log(`${pack.prefix}  ${CASE.case_id}   ${CASE.interview.topics.length} topics, ${nVar} variants`);
  console.log(`  held-out: ${held.length} questions (${held.filter(c => c.expect === null).length} out of scope)`
    + (tune.length ? `   tuning: ${tune.length} questions (${tune.filter(c => c.expect === null).length} out of scope)` : '   tuning: none'));
  console.log('='.repeat(72));
  if (!held.length) { console.log('  no held-out questions, skipped'); continue; }

  const critical = new Set(
    heldSet.critical.concat(CASE.interview.topics.filter(t => t.pertinent_negative).map(t => t.topic)));

  /* Held-out means held out. A phrasing that also sits in the bank measures memorisation. */
  {
    const bank = new Set();
    for (const t of CASE.interview.topics)
      for (const f of [t.canonical].concat(t.variants || [])) bank.add(String(f).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim());
    for (const f of (CASE.interview.out_of_scope_bank || [])) bank.add(String(f).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim());
    const leaked = held.filter(c => bank.has(c.q.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()));
    if (leaked.length) {
      console.error(`  REFUSING: ${leaked.length} held-out question(s) appear verbatim in the bank:`);
      for (const c of leaked) console.error('    ' + c.q);
      process.exit(1);
    }
  }

  /* Everything the learner types goes through matchQuestion, so that is what is scored:
     it is the shipped path including clause splitting, run once with the embedding
     model absent (the matcher a resident gets before the model loads, or on a machine
     where it never does) and once with it present. */
  const runAll = async (m, set) => {
    const out = new Map();
    for (const c of set) {
      const ms = await m.matchQuestion(c.q);
      const arr = ms.map(x => x.topic);
      if (ms.length === 1 && ms[0].clarify) arr.clarify = ms[0].clarify;
      out.set(c.q, arr);
    }
    return out;
  };
  const lexM = makeShipped(CASE, null, null);
  const lexOut = await runAll(lexM, held);
  const lexOf = q => lexM.matchTopic(q);
  const rLex = score(held, c => lexOut.get(c.q), critical);
  report('shipped, lexical only (before the model loads)', rLex);
  const row = { pack: pack.prefix, lexical: line(rLex) };

  if (WANT_SEMANTIC) {
    const best = await makeSemantic(CASE, ext, lexM.semanticRows());
    const semOf = new Map();
    for (const c of held.concat(tune)) semOf.set(c.q, await best(c.q));

    const OOS = lexM.OOS_TOPIC;
    const rSem = score(held, c => [semOf.get(c.q).topic === OOS ? null : semOf.get(c.q).topic], critical);
    report('embedding model alone, no threshold (what it believes)', rSem);

    const fusM = makeShipped(CASE, best, null);
    const fusOut = await runAll(fusM, held);
    const rFus = score(held, c => fusOut.get(c.q), critical);
    report('shipped, lexical + semantic (this is the number to quote)', rFus);
    row.fused = line(rFus);
    if (flag('--diagnose')) {
      const useTune = flag('--tune-set') && tune.length;
      const dSet = useTune ? tune : held;
      const dOut = useTune ? await runAll(fusM, tune) : fusOut;
      console.log(`\n    diagnosis of every miss on the ${useTune ? 'TUNING' : 'held-out'} set: what each matcher said`);
      for (const c of dSet) {
        const got = dOut.get(c.q).filter(x => x !== null);
        const exp = c.expect === null ? [] : (Array.isArray(c.expect) ? c.expect : [c.expect]);
        const ok = got.length === exp.length && exp.every(x => got.includes(x));
        if (ok) continue;
        const l = lexOf(c.q), sm = semOf.get(c.q);
        const r2 = sm.ranked.slice(0, 3).map(([t, s]) => `${t} ${s.toFixed(2)}`).join(', ');
        const one = await fusM.matchOne(c.q);
        console.log(`      "${c.q}"  want ${exp.join('+') || 'none'}`);
        console.log(`         lex ${l.topic} ${l.score.toFixed(2)}${l.oos ? ' (oos)' : ''}   sem [${r2}]   fused ${one.topic} ${one.score.toFixed(2)} ${one.matcher}   shipped ${got.join('+') || 'none'}`);
      }
    }

    /* Separability on the held-out set, reported not tuned on. */
    const inS = held.filter(c => c.expect !== null).map(c => semOf.get(c.q).score);
    const outS = held.filter(c => c.expect === null).map(c => semOf.get(c.q).score);
    const stat = a => a.length
      ? `min ${Math.min(...a).toFixed(2)}  p25 ${a.slice().sort((x, y) => x - y)[a.length >> 2].toFixed(2)}  median ${a.slice().sort((x, y) => x - y)[a.length >> 1].toFixed(2)}  max ${Math.max(...a).toFixed(2)}`
      : 'none';
    console.log(`\n    cosine, in scope:      ${stat(inS)}`);
    console.log(`    cosine, out of scope:  ${stat(outS)}`);
    if (outS.length < 30) console.log(`    NOTE: ${outS.length} out-of-scope questions; section 10.6 asks for 30.`);

    if (WANT_SWEEP) {
      if (!tune.length) {
        console.log('\n    --sweep skipped: no tuning set. Sweeping on the held-out set and then quoting it');
        console.log('    measures memorisation (section 10.6). Create cases/' + pack.prefix + '/' + pack.prefix + '-matcher-tune-questions.json.');
      } else {
        console.log('\n    sweep ON THE TUNING SET, shipped matchQuestion with FUSE overridden');
        console.log('    cells: correct / wrong / fell / out-of-scope answered anyway');
        const WS = [0.3, 0.4, 0.5, 0.6, 0.7], TH = [0.35, 0.40, 0.45, 0.50, 0.55];
        console.log('    weight  ' + TH.map(t => `thr ${t.toFixed(2)}`.padEnd(18)).join(''));
        for (const w of WS) {
          const cells = [];
          for (const th of TH) {
            const m = makeShipped(CASE, best, { ...FUSE, weight: w, threshold: th });
            const out = await runAll(m, tune);
            const r = score(tune, c => out.get(c.q), critical).t;
            cells.push(`${r.hit}/${r.wrong}/${r.fell}/${r.falsePos}`.padEnd(18));
          }
          console.log(`    ${w.toFixed(2)}    ` + cells.join(''));
        }
        console.log('    Choose the cell with the fewest WRONG and answered-anyway results, set FUSE in');
        console.log('    engine/ui.js, rebuild, and re-run without --sweep to quote the held-out line.');
      }
    }
  }
  summary.push(row);
}

console.log('\n' + '='.repeat(72));
console.log('SUMMARY');
for (const r of summary) {
  console.log(`  ${r.pack}`);
  console.log(`    lexical:  ${r.lexical}`);
  if (r.fused) console.log(`    fused:    ${r.fused}`);
}
