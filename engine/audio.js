/* ============================================================
   Audio. Two channels:

   1. A continuous heartbeat. Tempo follows the heart rate on the monitor and
      pitch follows its oxygen saturation: A5 at the reference saturation, one
      semitone lower per percent below it. It is the monitor's sound, so it does
      not exist until the monitor is on the patient. Before that there is no
      heartbeat at all, which is the same silence the resident would be standing
      in, and it is the audible half of the empty screen.

      The beat is a self-rescheduling chain rather than a fixed interval, and
      each beat reads the current vitals when it schedules the next one. That is
      what lets the tempo follow the five-second ramp between phases continuously
      instead of being restarted whenever the rate crosses a quantisation step,
      and it is what makes an uneven rhythm expressible at all.

      A phase may declare a `rhythm`. The vocabulary is closed and lives in
      SHARED.audio.rhythm; the engine knows nothing about which diagnoses produce
      which rhythm, exactly as it knows nothing about which drugs are harmful.
      `regular` is the default and is bit-identical to the behaviour before this
      existed. `irregularly_irregular` draws every R-R interval independently, so
      there is no underlying periodicity for a listener to lock onto, which is
      the thing that distinguishes it from a regular beat with jitter added.
   2. A short two-note trill whenever the nurse issues a prompt. This is a person
      speaking rather than equipment, so it is not gated on the monitor and fires
      from the first prompt whether or not anything is attached.

   The pitch mapping makes desaturation audible before the resident looks at
   the monitor, which is the intended effect but is also a teaching decision
   worth flagging: a real bedside monitor's pitch drop is not linear in
   semitones and does not start at 100%.

   Browsers will not start audio without a gesture, so the context is created
   on the first click and the toggle reflects real state rather than intent.
   ============================================================ */
const AUDIO = (() => {
  /* Audio configuration is global, not per case, so it reads SHARED. Reading PROTO
     here would capture null: this module is evaluated before any case is selected. */
  const CFG = SHARED.audio;
  /* beatTimer !== null means a beat is pending. It is the single source of truth for
     whether the chain is running: there is no second flag to fall out of step with it.
     prevMs is the interval that has just elapsed, which is what the loudness of the
     next beat is derived from. */
  let ctx = null, master = null, on = true, beatTimer = null, prevMs = null;

  const HR_MIN = 20, HR_MAX = 220;   /* the validator's plausible range for a phase */

  /* ---------- the interval model ----------
     Exposed rather than private, because it is a claim about physiology that a
     reviewer has to be able to check, and because `describe()` and the test harness
     both read it. Given a mean interval and a rhythm name it returns the length of
     one R-R interval in milliseconds.

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
     that somehow carries one should still make a sound. */
  function rhythmNow() {
    if (typeof PHASE === 'undefined' || typeof ST === 'undefined' || !ST) return 'regular';
    const p = PHASE[ST.phase];
    const r = p && p.rhythm;
    return (r && CFG.rhythm && CFG.rhythm[r]) ? r : 'regular';
  }

  function ensure() {
    if (ctx) {
      if (ctx.state === 'suspended') ctx.resume();
      return true;
    }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return false;
    ctx = new AC();
    master = ctx.createGain();
    master.gain.value = 0.85;
    master.connect(ctx.destination);
    return true;
  }

  /* A5 at the reference saturation, one semitone per percent below it. */
  function pitchFor(spo2) {
    const steps = (CFG.spo2Reference - spo2) * CFG.semitonesPerPercent;
    return CFG.baseHz * Math.pow(2, -steps / 12);
  }

  /* One thump: a short pitched blip with a percussive envelope. */
  function thump(hz, at, gain, dur) {
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = 'sine';
    o.frequency.setValueAtTime(hz, at);
    o.frequency.exponentialRampToValueAtTime(Math.max(40, hz * 0.55), at + dur);
    g.gain.setValueAtTime(0.0001, at);
    g.gain.exponentialRampToValueAtTime(gain, at + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    o.connect(g).connect(master);
    o.start(at);
    o.stop(at + dur + 0.02);
  }

  /* In an uneven rhythm the first heart sound varies in intensity from beat to beat,
     because a long diastole fills the ventricle more than a short one does and the
     stroke volume follows. That is a real auscultatory finding, and it is also the
     thing that makes an irregular rhythm sound irregular rather than sound like a
     metronome with jitter sprinkled on it: without it the ear hears mistimed identical
     beats, with it the ear hears a heart. Derived from the interval that has just
     elapsed, bounded, and off entirely for a regular rhythm. */
  function fillingGain(rhythm, meanMs) {
    const r = CFG.rhythm && CFG.rhythm[rhythm];
    if (!r || !r.gainPerRatio || !prevMs || !meanMs) return 1;
    const g = 1 + (prevMs / meanMs - 1) * r.gainPerRatio;
    return Math.min(r.gainCeiling || 1.3, Math.max(r.gainFloor || 0.7, g));
  }

  /* lub-dub: the second sound is quieter, lower and close behind the first.
     The gap is 160 ms except where the interval about to elapse is short enough that
     160 ms would put the dub on top of the next lub. At the rates the two earlier
     cases author it is always 160 ms, so their sound is unchanged; it only starts to
     compress above about 155 beats per minute, which is where this case begins. */
  function beat(hz, intervalMs, gain) {
    const t = ctx.currentTime + 0.01;
    const gap = Math.min(0.16, (intervalMs / 1000) * 0.42);
    thump(hz, t, 0.30 * gain, Math.min(0.14, gap * 0.9));
    thump(hz * 0.75, t + gap, 0.17 * gain, Math.min(0.11, gap * 0.7));
  }

  /* One beat, then the next appointment. Everything is read fresh here rather than
     captured when the chain started, so the rate, the pitch and the rhythm all track
     whatever the monitor is currently showing, including mid-ramp. The chain simply
     stops if there is nothing to sound; sync() restarts it when there is. */
  function tick() {
    beatTimer = null;
    if (!on || !ctx) return;
    const v = currentVitals();
    if (!v) return;
    const meanMs = 60000 / Math.max(HR_MIN, Math.min(HR_MAX, v.heart_rate));
    const rhythm = rhythmNow();
    /* The next interval is drawn before the beat is played, because the lub-dub gap
       has to fit inside it. */
    const nextMs = intervalModel(meanMs, rhythm);
    beat(pitchFor(v.oxygen_saturation), nextMs, fillingGain(rhythm, meanMs));
    prevMs = nextMs;
    /* Scheduled forward from now with no attempt to make up lost time. A background
       tab throttles timers to about a second, and a chain that tried to catch up
       would fire a burst of beats the moment the tab came back. */
    beatTimer = setTimeout(tick, nextMs);
  }

  function currentVitals() {
    if (!CASE) return null;
    /* No monitor, no monitor sound. ST.monitoring is set by the fold the moment an
       action carrying the catalog's reveals_vitals capability is taken. */
    if (!ST || !ST.monitoring) return null;
    /* The phase baseline with any active vital effect already applied, so a thirty
       second rise in saturation is heard as well as seen. */
    let v = ST.vitals;
    if (!v) { const p = PHASE[ST.phase]; v = p ? p.vitals : null; }
    /* The monitor travels to the new phase's numbers over five seconds. The
       heartbeat travels with it, because a beat that jumps to the new rate
       while the displayed rate is still moving sounds like a fault. Guarded by
       typeof so this file keeps working without the UI layer. */
    if (typeof rampedVitals === 'function') { const r = rampedVitals(); if (r) v = r; }
    /* An unauthored case has null vitals. There is no tempo and no pitch to derive,
       so play nothing rather than guessing at a rate. */
    if (!v || typeof v.heart_rate !== 'number' || typeof v.oxygen_saturation !== 'number') return null;
    return v;
  }

  /* Called every render, sixty times a second. It starts the chain and stops it and
     does nothing else, because the chain reads the rate itself.

     This used to quantise the rate and the saturation and restart the beat whenever
     the quantised value changed, which existed to stop a five-second ramp restarting
     the interval three hundred times and sounding like stumbling. There is nothing
     left to restart, so the quantisation is gone and with it the last place where the
     beat could stutter. It also means the tempo now follows the ramp exactly rather
     than in two-beat-per-minute steps. */
  function sync() {
    if (!on || !ctx) return;
    if (!currentVitals()) { if (beatTimer !== null) stop(); return; }
    if (beatTimer === null) tick();
  }

  function stop() {
    clearTimeout(beatTimer);
    beatTimer = null;
    prevMs = null;
  }

  /* Nurse prompt: a rising two-note trill, deliberately unlike the heartbeat. */
  function trill() {
    if (!on || !ensure()) return;
    const t = ctx.currentTime + 0.01;
    [[1318.5, 0], [1760.0, 0.09]].forEach(([hz, off]) => {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.type = 'triangle';
      o.frequency.setValueAtTime(hz, t + off);
      g.gain.setValueAtTime(0.0001, t + off);
      g.gain.exponentialRampToValueAtTime(0.22, t + off + 0.015);
      g.gain.exponentialRampToValueAtTime(0.0001, t + off + 0.14);
      o.connect(g).connect(master);
      o.start(t + off);
      o.stop(t + off + 0.16);
    });
  }

  /* Called on any user gesture. Creates or resumes the context, but never
     turns the sound back on after the user has switched it off. */
  function unlock() {
    if (!on) return false;
    if (!ensure()) return false;
    sync();
    return true;
  }

  function start() {
    if (!ensure()) return false;
    on = true;
    /* Clear first. Calling start() while a beat is already pending would otherwise
       leave two chains running against each other, and the only symptom would be a
       beat that sounds subtly doubled. */
    stop();
    sync();
    return true;
  }

  function toggle() {
    if (on && ctx) {
      on = false;
      stop();
    } else {
      on = true;
      start();
    }
    return on;
  }

  return {
    start, unlock, toggle, sync, trill, stop, intervalModel,
    get running() { return on && !!ctx && ctx.state === 'running'; },
    get enabled() { return on; },
    /* exposed so the interface can state the mapping rather than hide it */
    describe() {
      const v = currentVitals();
      if (!v) return '';
      const steps = (CFG.spo2Reference - v.oxygen_saturation) * CFG.semitonesPerPercent;
      const rhythm = rhythmNow();
      const r = CFG.rhythm && CFG.rhythm[rhythm];
      return `${Math.round(v.heart_rate)} bpm, ${Math.round(pitchFor(v.oxygen_saturation))} Hz `
           + `(${CFG.baseNote} minus ${steps} semitone${steps === 1 ? '' : 's'})`
           + (r && r.label ? `, ${r.label}` : '');
    },
    /* The rhythm the beat is currently using, for the interface and for tests. */
    get rhythm() { return rhythmNow(); }
  };
})();
