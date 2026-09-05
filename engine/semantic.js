/* ============================================================
   SEMANTIC MATCHING LAYER

   A sentence-embedding model that runs entirely in the learner's browser.
   Nothing is sent anywhere: there is no API key, no server, no per-question
   cost, and after the first load no network call. The model is
   all-MiniLM-L6-v2, int8 quantised, about 23 MB, fetched once from the
   Hugging Face CDN and then served from the browser's cache.

   PROGRESSIVE BY DESIGN. This file is inert until the model finishes loading.
   Until then, and permanently if loading fails, the lexical matcher in ui.js
   is the only matcher and behaviour is byte-identical to the build before this
   file existed. A resident on a bad connection gets the old simulator, not a
   broken one. Nothing here is on the critical path of starting or playing a
   case.

   WHY EMBEDDINGS RATHER THAN A CHAT MODEL. The task is to put a short question
   into one of about thirty-four buckets. That is what sentence embeddings are
   for. A chat model would need a server to hold the API key, would cost money
   per question, would add latency to a patient who is meant to answer at once,
   and would be non-deterministic, which matters in a tool whose debrief claims
   to report what the learner actually did.

   WHAT THIS FIXES. The lexical matcher scores by shared tokens, so a question
   sharing no token with any authored variant scores exactly zero. Measured on
   the CHFE bank, 31 of 40 common clinical terms and abbreviations appear in
   none of the 340 variants, so "PND?", "orthopnea?", "PMH?" and "NKDA?" all
   fell straight through to the out-of-scope fallback. An embedding model puts
   those next to the lay phrasings without anyone authoring them.

   ------------------------------------------------------------
   THE THRESHOLDS BELOW ARE NOT MEASURED. READ THIS.
   ------------------------------------------------------------
   They are starting values chosen to be conservative, not values fitted to
   this bank. They were set without running the model against the case,
   because the machine this was written on could not reach the model weights.

   Section 10.6 of the authoring requirements already asks for a matcher
   evaluation per case pack and already warns that tuning against a held-out
   set and then quoting the result measures memorisation. `engine/matcher_eval.mjs`
   is that harness. Run it before trusting any number in this file, and change
   these three constants to what it reports.

   Until that is done, the fusion rule below is deliberately arranged so the
   semantic layer can mostly only ADD correct matches: where it is not
   confident, the lexical result stands unchanged.
   ============================================================ */
const SEM = (function () {
  'use strict';

  /* ---------- tuning ----------
     Since v0.8 the thresholds below are NOT what decides a match. ui.js combines this
     module's per-topic cosines with the lexical matcher's per-topic scores (see the
     fusion block there, and FUSE). They are kept so describe() and the harness can
     still report the model's own confidence, and so an older build reads the same. */
  const ACCEPT = 0.62;  // cosine at or above this: the model is confident on its own
  const AGREE  = 0.45;  // between AGREE and ACCEPT: moderate confidence
  /* VETO would withhold an answer where nothing in the bank is close, even if
     the lexical matcher found a token overlap. It is DISABLED (0) by choice,
     not by oversight.

     The case for it is section 10.6: an out-of-scope question answered as
     though it were a different question is a wrong answer the learner cannot
     see. The case against it, which won here, is that this simulator is the
     learner's only source of history. There is no textbook page, no chart to
     re-read and no attending to ask, so an answer withheld is information lost
     for good, while a poorly matched answer at least sits in the transcript
     directly beneath the question the learner typed, where it can be judged.

     Set it back to about 0.28 to trade answers for safety, and measure the
     change with engine/matcher_eval.mjs before believing either number. */
  const VETO   = 0;

  const MODEL_ID = 'Xenova/all-MiniLM-L6-v2';
  /* Pinned exactly. An unpinned CDN URL means the matcher can change under a
     case that was validated against a different one. The web build is an ES
     module with a named `pipeline` export. */
  const LIB_URL = 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.2.0/dist/transformers.min.js';

  const DIM = 384;             // all-MiniLM-L6-v2 embedding width
  const BATCH = 24;            // bank rows embedded per turn, then yield to the UI
  const LIB_TIMEOUT_MS = 45000;
  const BANK_TIMEOUT_MS = 180000;

  const CACHE_DB = 'emsim-embeddings';
  const CACHE_STORE = 'vec';

  /* ---------- state ----------
     idle -> loading -> ready, or -> unavailable, which is terminal. There is
     no retry loop: a learner who is offline should not have the tab repeatedly
     trying to pull 23 MB while they work. */
  let state = 'idle';
  let extractor = null;
  let vecs = null;      // Float32Array of rows.length * DIM, unit length, row major
  let rows = [];        // [{topic, form}] parallel to vecs
  let bankKey = null;
  let gen = 0;          // guards against a case switch mid-load
  let lastError = null;
  const listeners = [];

  function setState(s) {
    if (s === state) return;
    state = s;
    for (const fn of listeners) { try { fn(s); } catch (e) { /* a listener must not stall the loader */ } }
  }

  /* ---------- small helpers ---------- */
  function hash(str) {                       // FNV-1a, only used to key the cache
    let h = 0x811c9dc5;
    for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 0x01000193); }
    return (h >>> 0).toString(36);
  }
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  function withTimeout(p, ms, what) {
    return Promise.race([p, sleep(ms).then(() => { throw new Error('timed out loading ' + what); })]);
  }

  /* ---------- embedding cache ----------
     Saves re-embedding 340 short strings on every load. Every path here
     swallows its own errors: IndexedDB is unavailable on file:// in some
     browsers, and in a private window in others, and a missing cache is a
     few seconds of background work rather than a failure. */
  function openDb() {
    return new Promise((res, rej) => {
      let r;
      try { r = indexedDB.open(CACHE_DB, 1); } catch (e) { return rej(e); }
      r.onupgradeneeded = () => { try { r.result.createObjectStore(CACHE_STORE); } catch (e) {} };
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error || new Error('indexeddb open failed'));
      r.onblocked = () => rej(new Error('indexeddb blocked'));
    });
  }
  async function cacheGet(k) {
    try {
      const db = await openDb();
      return await new Promise((res, rej) => {
        const q = db.transaction(CACHE_STORE, 'readonly').objectStore(CACHE_STORE).get(k);
        q.onsuccess = () => res(q.result || null);
        q.onerror = () => rej(q.error);
      });
    } catch (e) { return null; }
  }
  async function cachePut(k, buf) {
    try {
      const db = await openDb();
      await new Promise((res, rej) => {
        const q = db.transaction(CACHE_STORE, 'readwrite').objectStore(CACHE_STORE).put(buf, k);
        q.onsuccess = () => res();
        q.onerror = () => rej(q.error);
      });
    } catch (e) { /* cache is an optimisation, never a requirement */ }
  }

  /* ---------- model ---------- */
  async function makeExtractor(lib) {
    try {
      /* Remote only. Without this the library probes for a local /models path
         first, which on file:// produces a console error on every load and
         finds nothing. */
      if (lib.env) {
        lib.env.allowLocalModels = false;
        lib.env.allowRemoteModels = true;
      }
    } catch (e) { /* env shape is not part of the public contract */ }

    /* q8 is the 23 MB int8 build. The fallbacks cover older option spellings so
       a version bump does not silently drop to the 90 MB float32 weights. */
    const attempts = [{ dtype: 'q8' }, { quantized: true }, {}];
    let last = null;
    for (const opt of attempts) {
      try { return await lib.pipeline('feature-extraction', MODEL_ID, opt); }
      catch (e) { last = e; }
    }
    throw last || new Error('could not create the feature extraction pipeline');
  }

  async function embed(texts) {
    /* normalize:true makes every vector unit length, so a dot product is the
       cosine and no division is needed at match time. */
    const out = await extractor(texts, { pooling: 'mean', normalize: true });
    return out.data;                        // Float32Array, texts.length * DIM
  }

  async function embedBank(myGen) {
    const all = new Float32Array(rows.length * DIM);
    for (let i = 0; i < rows.length; i += BATCH) {
      if (myGen !== gen) return null;                 // a different case was selected
      const chunk = rows.slice(i, i + BATCH).map(r => r.form);
      const data = await embed(chunk);
      all.set(data.subarray(0, chunk.length * DIM), i * DIM);
      await sleep(0);                                 // let the UI paint between batches
    }
    return all;
  }

  /* ---------- public ---------- */

  /* Called once per case selection. Safe to call repeatedly. */
  async function init(caseId, topics) {
    if (state === 'unavailable') return;              // terminal, do not retry
    if (typeof indexedDB === 'undefined' && typeof fetch !== 'function') return;

    const nextRows = [];
    for (const t of (topics || [])) {
      for (const f of [t.canonical].concat(t.variants || [])) {
        if (typeof f === 'string' && f.trim()) nextRows.push({ topic: t.topic, form: f });
      }
    }
    if (!nextRows.length) return;

    const key = caseId + '|' + MODEL_ID + '|' + nextRows.length + '|'
              + hash(nextRows.map(r => r.form).join(''));
    if (key === bankKey && (state === 'ready' || state === 'loading')) return;

    const myGen = ++gen;
    bankKey = key;
    rows = nextRows;
    vecs = null;
    setState('loading');

    try {
      if (!extractor) {
        const lib = await withTimeout(import(LIB_URL), LIB_TIMEOUT_MS, 'the embedding library');
        if (myGen !== gen) return;
        extractor = await withTimeout(makeExtractor(lib), BANK_TIMEOUT_MS, 'the embedding model');
        if (myGen !== gen) return;
      }

      const cached = await cacheGet(key);
      if (cached && cached.byteLength === rows.length * DIM * 4) {
        vecs = new Float32Array(cached);
      } else {
        const built = await withTimeout(embedBank(myGen), BANK_TIMEOUT_MS, 'the question bank');
        if (myGen !== gen || !built) return;
        vecs = built;
        cachePut(key, vecs.buffer.slice(0));
      }

      if (myGen !== gen) return;
      setState('ready');
    } catch (e) {
      lastError = e;
      /* Deliberately not console.error: on a page a learner may have opened
         from a file, a red console entry reads as a broken simulator when the
         simulator is working exactly as designed. */
      if (typeof console !== 'undefined' && console.info) {
        console.info('[sim] semantic matching unavailable, staying on lexical matching:', e && e.message);
      }
      setState('unavailable');
    }
  }

  /* Best topic for a free-text question by cosine similarity, or null when the
     layer is not ready. Never throws: a failure here must not lose the
     learner's question. */
  async function best(q) {
    if (state !== 'ready' || !vecs) return null;
    let data;
    try { data = await embed([q]); } catch (e) { return null; }
    if (!data || data.length < DIM) return null;

    const scoreByTopic = Object.create(null);
    for (let i = 0; i < rows.length; i++) {
      let dot = 0;
      const off = i * DIM;
      for (let d = 0; d < DIM; d++) dot += data[d] * vecs[off + d];
      const t = rows[i].topic;
      if (!(t in scoreByTopic) || dot > scoreByTopic[t]) scoreByTopic[t] = dot;
    }
    let top = null, s1 = -1, s2 = -1;
    for (const t in scoreByTopic) {
      const s = scoreByTopic[t];
      if (s > s1) { s2 = s1; s1 = s; top = t; } else if (s > s2) { s2 = s; }
    }
    /* `scores` is what the fusion in ui.js combines with the lexical ranking. The
       out-of-scope bank, if the case has one, arrives from ui.js as a topic under
       its reserved id and is scored like any other; it is ui.js that turns a win
       for it into a fallback. */
    return { topic: top, score: s1, margin: s1 - (s2 < 0 ? 0 : s2), scores: scoreByTopic };
  }

  return {
    init, best,
    ACCEPT, AGREE, VETO, MODEL_ID, LIB_URL,
    get state() { return state; },
    get error() { return lastError; },
    ready: () => state === 'ready',
    onChange: fn => { listeners.push(fn); },
  };
})();
