/* ============================================================
   The monitor's waveform: one lead, drawn live.

   Three things live here and they are one module because they share a clock.

   1. THE BEAT CLOCK. A self-rescheduling chain of setTimeout calls, one beat
      per link, each beat reading the current rate and rhythm when it books its
      successor. This used to live in audio.js. It moved here because the trace
      and the beep are the same beat seen by two senses: a QRS drawn a quarter
      of a second away from the sound it makes reads as a fault, and the only
      way two consumers can agree on when a beat happens is for one clock to
      tell both. The audio module subscribes to it. The chain runs whenever a
      case is running and the patient is on a monitor, whether or not sound is
      on, because a resident with the sound off still has to see the rhythm.

   2. THE WAVEFORM. A phase may carry an `ecg` block beside its `rhythm`, and
      from it this module builds one lead II complex per beat out of compact
      support primitives ported from the ECG generator project: every wave is
      exactly zero outside its landmark window, so the QRS duration an author
      writes is the QRS duration that renders, and the baseline between
      complexes is exactly flat rather than approximately so. The vocabulary
      an author has is deliberately small: whether P waves are present, how
      wide the QRS is, where the ST segment sits, how tall the T wave is, and
      the PR and QTc intervals. Plus two patterns with no complexes at all,
      ventricular fibrillation and asystole. That is what a single monitor
      lead can show, and nothing beyond it is claimed. The engine holds no
      association between any of these and a diagnosis, exactly as it holds
      none between a rhythm and a diagnosis: a case says "no P waves, QRS
      180 ms" and never says why.

   3. THE SWEEP. The trace is drawn the way a bedside monitor draws it: the pen
      moves left to right at a fixed paper speed, the newest sample is drawn at
      the pen, and a short blank gap runs ahead of the pen erasing the previous
      pass. When the pen reaches the right edge it starts again at the left.
      Nothing scrolls. The picture behind the gap is the last few seconds and
      stays until the pen comes round to overwrite it, which is what lets a
      reader look back at a beat that has just happened. The clock the sweep
      runs on freezes when the case pauses, so a paused monitor holds its
      picture rather than drawing a burst of baseline on resume.

   The interval model (the shape of an irregularly irregular rhythm) is here
   too, unchanged from audio.js, because the clock is what draws from it. Its
   parameters and their provenance note remain in SHARED.audio.rhythm.

   Evaluation order: this file declares `const MONITOR` and audio.js calls
   MONITOR.onBeat at its own top level, so it MUST come before audio.js in the
   bundle. Its own top level reads only SHARED. Everything else (ST, PHASE,
   CASE, rampedVitals, document) is looked up at call time behind typeof
   guards, so the module evaluates in the test harness with none of them.
   ============================================================ */
const MONITOR = (() => {
  const CFG = SHARED.audio;
  const MON = SHARED.monitor || {};
  const HR_MIN = 20, HR_MAX = 220;   /* the validator's plausible range for a phase */

  /* ---------- the interval model ----------
     Moved verbatim from audio.js in v0.16, comment included, because the clock that
     draws from it is here now. Exposed rather than private, because it is a claim
     about physiology that a reviewer has to be able to check, and because the audio's
     `describe()` and the test harness both read it. Given a mean interval and a rhythm
     name it returns the length of one R-R interval in milliseconds.

     For `irregularly_irregular` the interval is a shifted exponential:

         interval = mean * (s + (1 - s) * Exp(1))

     A fixed fraction s of the mean is refractory and the remainder is exponentially
     distributed. Two properties matter and both are asserted in the test suite.

     THE MEAN IS PRESERVED EXACTLY. E[Exp(1)] = 1, so E[interval] = mean * (s + (1-s))
     = mean. The authored heart rate is therefore the real average rate, not an
     approximation of it, which is what lets the rate on the monitor and the rate in
     the ear stay the same number while every individual interval differs.

     THE SPREAD NARROWS AS THE RATE RISES. s is raised where a fixed refractory floor
     would otherwise be breached, so the coefficient of variation, which is (1 - s),
     falls at fast rates. That is not a fudge to keep the arithmetic tidy: at high
     ventricular rates the interval distribution really is compressed, because
     concealed conduction into the atrioventricular node leaves less room between
     beats. It also means no interval is ever shorter than the floor, so two beats
     can never collide.

     The exponential shape is right-skewed, which is what produces the occasional
     long pause that makes an irregularly irregular rhythm recognisable. The
     parameters are teaching choices and live in SHARED.audio.rhythm, where the
     provenance note says so. */
  function intervalModel(meanMs, rhythm) {
    const r = CFG.rhythm && CFG.rhythm[rhythm];
    if (!r || !(r.refractoryFraction > 0) || !(r.refractoryFraction < 1)) return meanMs;
    /* Raise the refractory fraction rather than clamping the result. Clamping a draw
       up to a floor would push a third of the beats at 220 bpm onto the floor and the
       mean would no longer be the authored rate. */
    const s = Math.min(0.98, Math.max(r.refractoryFraction, (r.absoluteFloorMs || 0) / meanMs));
    /* Math.random() can return exactly 0 and ln(0) is -Infinity, so the draw is taken
       from (0, 1] rather than [0, 1). */
    const draw = -Math.log(1 - Math.random());
    const ms = meanMs * (s + (1 - s) * draw);
    /* The ceiling truncates a tail with a probability of roughly one in a thousand and
       exists only so that a pathological draw cannot leave a long silence. */
    return Math.min(meanMs * (r.ceilingMultiple || 3), ms);
  }

  /* The rhythm the current phase declares. An unrecognised value falls back to regular
     rather than throwing: the validator rejects one at authoring time, and a built file
     that somehow carries one should still draw and sound something. */
  function rhythmNow() {
    if (typeof PHASE === 'undefined' || typeof ST === 'undefined' || !ST) return 'regular';
    const p = PHASE[ST.phase];
    const r = p && p.rhythm;
    return (r && CFG.rhythm && CFG.rhythm[r]) ? r : 'regular';
  }

  /* The vitals the monitor is showing right now, or null if it is showing nothing.
     Moved from audio.js, where it was private; the trace needs the same answer.
     No monitor, no vitals: ST.monitoring is set by the fold the moment an action
     carrying the catalog's reveals_vitals capability is taken. The phase baseline with
     any active vital effect applied, then the five-second ramp on top, so the beat
     follows the number on the screen and not the number in the file. */
  function vitalsNow() {
    if (typeof CASE === 'undefined' || !CASE) return null;
    if (typeof ST === 'undefined' || !ST || !ST.monitoring) return null;
    let v = ST.vitals;
    if (!v) { const p = PHASE[ST.phase]; v = p ? p.vitals : null; }
    if (typeof rampedVitals === 'function') { const r = rampedVitals(); if (r) v = r; }
    if (!v || typeof v.heart_rate !== 'number' || typeof v.oxygen_saturation !== 'number') return null;
    return v;
  }

  /* ---------- the ecg block ----------
     What an author may write on a phase, resolved to what the synthesiser reads. The
     defaults and the closed pattern vocabulary come from SHARED.monitor.ecg so that
     the validator, the build and this module agree on one set; a build without that
     block (an older one) gets the same figures from the fallbacks here. Values are
     clamped to the validator's ranges as a backstop only: a case that reaches the
     browser has already been validated, and a clamp that fires is a build that skipped
     a step, not a feature. */
  const E = MON.ecg || {};
  const DEF = Object.assign({ pr_ms: 160, qrs_ms: 90, qtc_ms: 420, st_mv: 0 }, E.defaults || {});
  const RANGE = Object.assign({ pr_ms: [80, 400], qrs_ms: [50, 260], qtc_ms: [280, 720],
                                st_mv: [-0.6, 0.6], t_mv: [-1.2, 1.5] }, E.ranges || {});
  const PATTERNS = new Set(Object.keys(E.patterns || {}).filter(k => k[0] !== '_'));
  if (!PATTERNS.size) ['organised', 'ventricular_fibrillation', 'asystole'].forEach(p => PATTERNS.add(p));
  const clampTo = (k, v) => Math.min(RANGE[k][1], Math.max(RANGE[k][0], v));
  const num = (v, d) => (typeof v === 'number' && isFinite(v)) ? v : d;

  function resolveSpec(ecg, rhythm) {
    const e = ecg || {};
    const pattern = PATTERNS.has(e.pattern) ? e.pattern : 'organised';
    return {
      pattern,
      /* P waves default to present, except under an irregularly irregular rhythm,
         where they default to absent. That default is the one the old decorative trace
         already drew, and it is a default rather than a rule: an author whose
         irregularly irregular rhythm does have P waves writes p_waves: true. */
      pWaves: typeof e.p_waves === 'boolean' ? e.p_waves : rhythm !== 'irregularly_irregular',
      prS:  clampTo('pr_ms',  num(e.pr_ms,  DEF.pr_ms))  / 1000,
      qrsS: clampTo('qrs_ms', num(e.qrs_ms, DEF.qrs_ms)) / 1000,
      qtcS: clampTo('qtc_ms', num(e.qtc_ms, DEF.qtc_ms)) / 1000,
      stMv: clampTo('st_mv',  num(e.st_mv,  DEF.st_mv)),
      /* null means "derive it": upright and modest for a narrow complex, and for a
         wide one the discordant T that secondary repolarisation produces. An authored
         figure is used as written. */
      tMv:  typeof e.t_mv === 'number' && isFinite(e.t_mv) ? clampTo('t_mv', e.t_mv) : null,
    };
  }

  function ecgNow() {
    if (typeof PHASE === 'undefined' || typeof ST === 'undefined' || !ST) return resolveSpec(null, 'regular');
    const p = PHASE[ST.phase];
    return resolveSpec(p && p.ecg, rhythmNow());
  }

  /* ---------- primitives ----------
     Ported from the ECG generator's deflections.ts. Both have COMPACT SUPPORT: exactly
     zero at and outside their window, C1 continuous everywhere. That is what makes the
     landmarks literal. Times are seconds relative to the QRS onset of the beat. */

  /* b(t) = A * sin(pi u)^(2p), u warping [on, peak] onto [0, 0.5] and [peak, off] onto
     [0.5, 1]. p = 1 is a raised cosine; below 1 is more pointed; above 1 is a broad
     dome with a slurred edge, which is what a conduction delay looks like. */
  function bump(on, peak, off, amp, p) {
    p = p || 1;
    const rise = peak - on, fall = off - peak, ex = 2 * p;
    return { on, off, at(t) {
      if (t <= on || t >= off) return 0;
      const u = t < peak ? 0.5 * (t - on) / rise : 0.5 + 0.5 * (t - peak) / fall;
      return amp * Math.pow(Math.sin(Math.PI * u), ex);
    } };
  }

  /* A smooth rise to levelA at riseEnd, a body to levelB at fallStart, and a monotone
     cubic fall to zero at off. This is the ST segment: the rise sits inside the terminal
     QRS so it merges with the S upstroke, the body is the segment itself, and the fall
     is under the T wave. The incoming slope of the fall is clamped so it cannot
     overshoot past zero. */
  function plateau(on, riseEnd, fallStart, off, levelA, levelB, shape) {
    const k = shape || 1;
    const riseDur = riseEnd - on, bodyDur = fallStart - riseEnd, fallDur = off - fallStart;
    let m0 = bodyDur > 0 ? (levelB - levelA) * k / bodyDur : 0;
    if (fallDur > 0) {
      const secant = -levelB / fallDur;
      if (secant === 0 || Math.sign(m0) !== Math.sign(secant)) m0 = 0;
      else if (Math.abs(m0) > 3 * Math.abs(secant)) m0 = 3 * secant;
    }
    return { on, off, at(t) {
      if (t <= on || t >= off) return 0;
      if (t < riseEnd) { const x = (t - on) / riseDur; return levelA * x * x * (3 - 2 * x); }
      if (t < fallStart) { const x = bodyDur > 0 ? (t - riseEnd) / bodyDur : 0; return levelA + (levelB - levelA) * Math.pow(x, k); }
      const x = (t - fallStart) / fallDur;
      return levelB * (1 + 2 * x) * (1 - x) * (1 - x) + m0 * fallDur * x * (1 - x) * (1 - x);
    } };
  }

  /* ---------- one complex in lead II ----------
     `rrS` is the interval this beat sits in, which sets the QT through Bazett and the
     ST share of it through the generator's partition model. Returns the deflections
     and the landmark timeline relative to QRS onset, and an `at(t)` summing them.

     The lead II amplitudes for a narrow complex are the generator's textbook-typical
     placeholders (P 0.15, Q -0.05, R 1.1, S -0.15, T 0.35 mV). They are not fitted to
     any corpus and the generator says so. What this module adds is one continuous
     blend from that narrow complex to a wide one as the authored QRS duration rises
     past 100 ms, following the generator's sodium-channel pattern in lead II: the
     initial r is held short, the extra duration goes into a deep broad terminal S
     drawn as a dome, the J point sits on the return limb of that S, and the T wave
     is discordant to it. The figures in the blend are stylisations tuned to look like
     the exemplar tracings the generator was tuned against, not measurements. */
  const AMP = { p: 0.15, q: -0.05, r: 1.1, s: -0.15, t: 0.35 };
  function synth(spec, rrS) {
    const rr = Math.max(0.25, rrS || 0.8);
    const qrs = spec.qrsS;
    /* QT by Bazett from the authored QTc, then partitioned: the ST segment's share of
       the JT interval shrinks with the rate (Malik's group; see the generator README),
       and the T keeps at least 80 ms however fast the rate. */
    let qt = Math.max(qrs + 0.10, spec.qtcS * Math.sqrt(rr));
    /* At fast rates the QT has to fit inside the interval, or the next P and QRS land
       on this T. Real hearts shorten it too; this is the same clamp a generator needs. */
    qt = Math.min(qt, Math.max(qrs + 0.10, rr - 0.04));
    const jt = qt - qrs;
    let st = 0.32 * Math.sqrt(Math.max(0.2, rr)) * jt;
    st = Math.max(0, Math.min(st, jt - 0.08));
    const tOn = qrs + st, tOff = qt;
    const tPeakFrac = 0.5 + 0.05 * Math.max(0, Math.min(1, (rr - 0.5) / 0.5));

    /* The width blend. 0 at 90 ms and below, 1 at 170 ms and above. It starts at the
       upper edge of normal and saturates well before the widest QRS a case authors,
       because the thing a monitor has to make legible is the difference between 90 and
       130 ms, and a blend that only began at 100 left a 132 ms complex looking like a
       slightly heavy normal one. Timing is still literal: only the shape steepens. */
    const w = Math.max(0, Math.min(1, (qrs - 0.09) / 0.08));
    const lerp = (a, b) => a + (b - a) * w;
    const qAmp = AMP.q * (1 - w);
    const rAmp = lerp(AMP.r, 0.85);
    const sAmp = lerp(AMP.s, -0.95);
    const qrsSharp = 0.8, termSharp = lerp(0.8, 1.5);
    const qPeak = 0.12 * qrs;
    const rPeak = lerp(0.40, Math.min(0.30, 0.03 / qrs)) * qrs;
    const sPeak = lerp(0.72, 0.64) * qrs;
    /* Secondary repolarisation, blended in with the width: J point at 0.3 of the
       terminal deflection with its sign, T at 0.8 of it with the opposite sign. */
    const stJ = spec.stMv + w * 0.3 * sAmp;
    const stT = spec.stMv + w * 0.15 * sAmp;
    const tAmp = spec.tMv !== null ? spec.tMv : lerp(AMP.t, -0.8 * sAmp);

    const parts = [];
    const lm = { pOn: null, pOff: null, qrsOn: 0, j: qrs, tOn, tOff };
    if (spec.pWaves) {
      /* P duration shortens a little at fast rates, as it does in life, and the PR is
         authored. At a fast rate the P lands on the previous beat's T wave, which is
         what happens in life too, and the two simply add. A PR longer than the interval
         itself is meaningless and is cut to fit inside it. */
      const pDur = rr < 0.5 ? 0.08 : 0.09;
      const pr = Math.min(spec.prS, Math.max(pDur + 0.02, rr - 0.03));
      lm.pOn = -pr; lm.pOff = -pr + pDur;
      parts.push(bump(lm.pOn, lm.pOn + 0.5 * pDur, lm.pOff, AMP.p, 1.0));
    }
    if (qAmp !== 0) parts.push(bump(0, qPeak, rPeak, qAmp, qrsSharp));
    parts.push(bump(qAmp !== 0 ? qPeak : 0, rPeak, sPeak, rAmp, qrsSharp));
    parts.push(bump(rPeak, sPeak, qrs, sAmp, termSharp));
    let stPart = null;
    if (stJ !== 0 || stT !== 0) { stPart = plateau(sPeak, qrs, tOn, tOff, stJ, stT, 1); parts.push(stPart); }
    if (tAmp !== 0) {
      const tPeak = tOn + tPeakFrac * (tOff - tOn);
      const under = stPart ? stPart.at(tPeak) : 0;
      /* The bump is reduced by what the plateau contributes at the T peak, so the T
         measured from the baseline is the requested figure. */
      parts.push(bump(tOn, tPeak, tOff, tAmp - under, 1.0));
    }
    const on = Math.min(...parts.map(d => d.on)), off = Math.max(...parts.map(d => d.off));
    return { on, off, landmarks: lm, parts, at(t) {
      let v = 0;
      for (const d of parts) if (t > d.on && t < d.off) v += d.at(t);
      return v;
    } };
  }

  /* ---------- patterns with no complexes ----------
     Both are functions of time alone. Ventricular fibrillation is three incommensurate
     sinusoids in the 3 to 7 Hz band under a slow amplitude wander, which is the
     generator's f-wave construction scaled up to a coarse fibrillatory waveform;
     asystole is a near-flat line with the wander the electrodes always carry. Neither
     is a model of anything, and a case authoring either is authoring a picture. */
  function fibrillation(t) {
    /* Each component is frequency-modulated by a slow sine of its own, so the sum never
       settles into a repeating figure the eye can lock onto: three fixed sinusoids read
       as a pattern within a few seconds, which is exactly what fibrillation is not. */
    const tp = 2 * Math.PI * t;
    const mod = 0.7 + 0.3 * Math.sin(tp * 0.23) * Math.sin(tp * 0.089 + 0.8);
    return 0.45 * mod * (Math.sin(tp * 4.6 + 2.6 * Math.sin(tp * 0.31))
                       + 0.7 * Math.sin(tp * 6.9 + 1.7 + 2.1 * Math.sin(tp * 0.47))
                       + 0.5 * Math.sin(tp * 3.1 + 0.6 + 3.0 * Math.sin(tp * 0.19))
                       + 0.3 * Math.sin(tp * 8.3 + 1.2 * Math.sin(tp * 0.71)));
  }
  function wander(t) { return 0.015 * Math.sin(2 * Math.PI * 0.21 * t) + 0.01 * Math.sin(2 * Math.PI * 0.07 * t + 1.1); }

  /* ---------- the beat clock ----------
     `mt()` is monitor time in milliseconds: it runs while the scene is a case and
     freezes otherwise, so a pause holds the picture and the pen resumes where it
     stopped. Complexes are stamped in monitor time. Real timers still book the beats,
     because the chain stops on pause and there is nothing pending across the gap. */
  const perf = () => (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
  let scene = 'idle', frozenAt = perf(), clockOffset = 0;
  function mt() { return (frozenAt === null ? perf() : frozenAt) - clockOffset; }

  /* beatTimer !== null means a beat is pending. It is the single source of truth for
     whether the chain is running. prevMs is the interval that has just elapsed, which
     the audio derives the next beat's loudness from. */
  let beatTimer = null, prevMs = null;
  const listeners = [];
  /* Complexes booked for the trace, each { at: monitor ms of QRS onset, c: synth() }.
     Bounded, because in a harness with a virtual timer the picture never advances. */
  let complexes = [];
  const KEEP = 48;
  function book(atMs, spec, rrS, withP, notBefore) {
    const c = synth(withP ? spec : Object.assign({}, spec, { pWaves: false }), rrS);
    /* A P wave cannot start before the moment it was booked, because the pen may
       already have drawn that stretch as baseline. Shift the whole complex rather than
       clip the P: a few milliseconds late is invisible, a clipped P is not. */
    if (notBefore !== undefined && atMs + c.on * 1000 < notBefore) atMs = notBefore - c.on * 1000;
    complexes.push({ at: atMs, c });
    if (complexes.length > KEEP) complexes.splice(0, complexes.length - KEEP);
  }

  function tick() {
    beatTimer = null;
    if (scene !== 'case') return;
    const v = vitalsNow();
    if (!v) return;
    const meanMs = 60000 / Math.max(HR_MIN, Math.min(HR_MAX, v.heart_rate));
    const rhythm = rhythmNow();
    const spec = ecgNow();
    /* The next interval is drawn before the beat is announced, because the audio's
       lub-dub has to fit inside it and the trace has to know when the next QRS is. */
    const nextMs = intervalModel(meanMs, rhythm);
    const now = mt();
    if (spec.pattern === 'organised') {
      /* The first beat of a chain is drawn at the moment it sounds, with no P wave: its
         P would have been in the past. Every later beat is booked one interval ahead,
         which is what lets its P wave be drawn before its QRS arrives, and is why the
         picture and the sound can agree. */
      if (prevMs === null) book(now, spec, meanMs / 1000, false);
      book(now + nextMs, spec, nextMs / 1000, true, now);
      const ev = { at: now, meanMs, nextMs, prevMs, rhythm, vitals: v };
      for (const fn of listeners) { try { fn(ev); } catch (e) { /* one consumer must not stop the other */ } }
    }
    prevMs = nextMs;
    /* Scheduled forward from now with no attempt to make up lost time. */
    beatTimer = setTimeout(tick, nextMs);
  }

  function stopChain() {
    clearTimeout(beatTimer);
    beatTimer = null;
    prevMs = null;
    /* A complex booked for a moment that has not come yet would be drawn on resume
       beside the fresh first beat of the restarted chain, one right after the other. */
    const now = mt();
    complexes = complexes.filter(x => x.at <= now);
  }

  /* Called every render. Starts a stopped chain, stops a running one, nothing else. */
  function sync() {
    if (scene !== 'case' || !vitalsNow()) { if (beatTimer !== null) stopChain(); return; }
    if (beatTimer === null) tick();
  }

  /* The interface says which of two situations we are in. Mirrors AUDIO.setScene and is
     called beside it. Idle freezes the clock and stops the chain; a case thaws it. */
  function setScene(s) {
    const next = (s === 'case') ? 'case' : 'idle';
    if (next === scene) return;
    if (next === 'idle') { frozenAt = perf(); stopChain(); }
    else { clockOffset += perf() - frozenAt; frozenAt = null; }
    scene = next;
  }

  /* Everything the trace holds, cleared. For a new run or a return to the picker. */
  function reset() {
    stopChain();
    complexes = [];
    pen = null;
    if (cv2d) { cv2d.ctx.clearRect(0, 0, cv2d.w, cv2d.h); }
  }

  /* The sample the trace shows at monitor time t (ms): the sum of every booked complex
     that is live at t, or the pattern layer for a phase with no complexes, plus the
     electrode wander every real trace carries. */
  function sample(tMs, spec) {
    const t = tMs / 1000;
    let v = 0;
    if (spec.pattern === 'ventricular_fibrillation') v = fibrillation(t);
    else if (spec.pattern !== 'asystole') {
      for (const x of complexes) {
        const rel = (tMs - x.at) / 1000;
        if (rel > x.c.on && rel < x.c.off) v += x.c.at(rel);
      }
    }
    return v + wander(t) + (Math.random() - 0.5) * 0.008;
  }

  /* ---------- the sweep ----------
     Paper speed and gain are in millimetres, as they are on the device being imitated,
     and a CSS pixel is 1/96 of an inch, so 50 mm/s is about 189 px/s: a 600 px trace
     holds a little over three seconds. Fifty rather than the diagnostic 25 because the
     trace is small and the property it most needs to show is QRS width: at 25 mm/s a
     130 ms complex is twelve pixels against eight for a normal one, which the eye does
     not read as wide. Doubling the speed is what a clinician does on a real monitor to
     look at a QRS, and it costs half the seconds on screen, which at three seconds is
     still five to eight beats. The gain is lower than a diagnostic strip's
     10 mm/mV because the trace is 48 px tall and a 1.1 mV R wave at 10 mm/mV would be
     42 px on its own. Five mm/mV keeps a deep wide S and a discordant T inside the box. */
  const PX_PER_MM = 96 / 25.4;
  const SWEEP = (MON.sweepMmPerSecond || 50) * PX_PER_MM;      /* px per second */
  const GAIN  = (MON.gainMmPerMillivolt || 5) * PX_PER_MM;     /* px per mV    */
  const GAP   = (MON.eraseGapMm || 6) * PX_PER_MM;             /* px ahead of the pen */
  const FS    = 300;                                           /* samples per second */
  let cv2d = null, pen = null, blank = true;

  /* The canvas at device resolution, re-fitted whenever its CSS size changes. A refit
     clears the picture, which is right: the old picture was drawn at another width. */
  function fit() {
    if (typeof document === 'undefined') return null;
    const el = document.getElementById('trace');
    if (!el || !el.getContext) return null;
    const w = el.clientWidth, h = el.clientHeight;
    if (!w || !h) return null;
    const dpr = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;
    if (!cv2d || cv2d.el !== el || cv2d.w !== w || cv2d.h !== h || cv2d.dpr !== dpr) {
      el.width = Math.round(w * dpr); el.height = Math.round(h * dpr);
      const ctx = el.getContext('2d');
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.lineWidth = 1.6; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      const colour = (typeof getComputedStyle === 'function')
        ? (getComputedStyle(el).getPropertyValue('--hr') || '').trim() : '';
      ctx.strokeStyle = colour || '#3FE39A';
      cv2d = { el, ctx, w, h, dpr, base: Math.round(h * 0.56) + 0.5 };
      pen = null; blank = true;
    }
    return cv2d;
  }

  function yOf(mv) {
    const y = cv2d.base - mv * GAIN;
    return Math.min(cv2d.h - 1, Math.max(1, y));
  }

  /* One frame. `on` is whether the patient is on a monitor; off means a dark screen,
     which is the same nothing the vital cells show. While idle the picture is held. */
  function frame(on) {
    const c = fit();
    if (!c) return;
    if (!on) { if (!blank) { c.ctx.clearRect(0, 0, c.w, c.h); blank = true; pen = null; } return; }
    if (scene !== 'case') return;
    const now = mt();
    const spec = ecgNow();
    if (pen === null) {
      pen = { t: now, x: (now / 1000 * SWEEP) % c.w, y: yOf(sample(now, spec)) };
      if (blank) { c.ctx.clearRect(0, 0, c.w, c.h); blank = false; }
      return;
    }
    let n = Math.floor((now - pen.t) / 1000 * FS);
    if (n <= 0) return;
    /* A long gap (a throttled tab that somehow was not paused) is not replayed: the pen
       is lifted and set down again at now, and the intervening picture is simply not
       drawn, rather than a line being ruled across the gap. */
    if (n > FS * 2) { pen = null; return; }
    const ctx = c.ctx;
    /* Clear ahead first, then stroke. The cleared band starts one pixel AFTER the pen,
       not at it: the stroke that follows begins at the pen and overdraws that pixel, so
       the join is continuous, where a band starting at or behind the pen wipes the
       antialiased edge of the previous stroke's end cap and leaves a hairline gap at
       every frame boundary, which reads as a dashed line at slow sweep speeds. */
    let segX0 = pen.x;
    const pts = [[pen.x, pen.y]];
    const flush = (xEnd) => {
      const x0 = Math.max(0, segX0 + 1);
      ctx.clearRect(x0, 0, Math.max(0, Math.min(c.w, xEnd + GAP) - x0), c.h);
      ctx.beginPath();
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
      ctx.stroke();
    };
    for (let i = 1; i <= n; i++) {
      const t = pen.t + i * 1000 / FS;
      const x = (t / 1000 * SWEEP) % c.w;
      const y = yOf(sample(t, spec));
      if (x < pts[pts.length - 1][0]) {
        /* The pen has reached the right edge: finish this pass, wipe the start of the
           next, and begin again at the left without a line across the join. */
        flush(c.w);
        ctx.clearRect(0, 0, GAP, c.h);
        pts.length = 0; segX0 = 0;
      }
      pts.push([x, y]);
    }
    flush(pts[pts.length - 1][0]);
    pen = { t: pen.t + n * 1000 / FS, x: pts[pts.length - 1][0], y: pts[pts.length - 1][1] };
  }

  return {
    intervalModel, rhythmNow, vitalsNow, resolveSpec, synth, ecgNow,
    sync, setScene, reset, frame,
    /* Subscribe to beats. Called once by audio.js at its top level. */
    onBeat(fn) { listeners.push(fn); return () => { const i = listeners.indexOf(fn); if (i >= 0) listeners.splice(i, 1); }; },
    /* For the interface and for tests. */
    get scene() { return scene; },
    get pending() { return beatTimer !== null; },
    get clock() { return mt(); },
    get booked() { return complexes.map(x => ({ at: x.at, on: x.c.on, off: x.c.off })); },
    get config() { return { sweepPxPerSecond: SWEEP, gainPxPerMillivolt: GAIN, eraseGapPx: GAP, sampleHz: FS,
                            patterns: Array.from(PATTERNS), defaults: Object.assign({}, DEF), ranges: RANGE }; },
    /* A one-line account of what is on the screen, for the sound control's tooltip. */
    describe() {
      const v = vitalsNow();
      if (!v) return '';
      const s = ecgNow();
      const pat = s.pattern === 'organised'
        ? `${s.pWaves ? 'P waves' : 'no P waves'}, QRS ${Math.round(s.qrsS * 1000)} ms`
        : s.pattern.replace('_', ' ');
      return `${Math.round(v.heart_rate)} bpm, ${rhythmNow().replace('_', ' ')}, ${pat}`;
    },
  };
})();
