/* ============================================================
   Audio. Two channels:

   1. A continuous heartbeat. Tempo follows the heart rate on the monitor and
      pitch follows its oxygen saturation: A5 at the reference saturation, one
      semitone lower per percent below it. It is the monitor's sound, so it does
      not exist until the monitor is on the patient. Before that there is no
      heartbeat at all, which is the same silence the resident would be standing
      in, and it is the audible half of the empty screen.
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
  let ctx = null, master = null, on = true, beatTimer = null, lastRateKey = null;

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

  /* lub-dub: the second sound is quieter, lower and close behind the first. */
  function beat(hz) {
    const t = ctx.currentTime + 0.01;
    thump(hz, t, 0.30, 0.14);
    thump(hz * 0.75, t + 0.16, 0.17, 0.11);
  }

  function schedule() {
    clearInterval(beatTimer);
    beatTimer = null;
    if (!on || !ctx) return;
    const v = currentVitals();
    if (!v) return;
    const interval = 60000 / Math.max(20, Math.min(220, v.heart_rate));
    const hz = pitchFor(v.oxygen_saturation);
    beat(hz);
    beatTimer = setInterval(() => {
      const cur = currentVitals();
      if (!cur) { stop(); return; }     /* the case changed under us, or has no vitals */
      beat(pitchFor(cur.oxygen_saturation));
    }, interval);
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

  /* Called every render. Restarts the loop only when rate or pitch actually change,
     so the beat does not stutter on every frame. */
  function sync() {
    if (!on || !ctx) return;
    const v = currentVitals();
    if (!v) return;
    /* Quantised. During a ramp the raw values change every frame, and
       rescheduling the beat three hundred times over five seconds restarts the
       interval on each pass and sounds like stumbling. Two beats per minute and
       one percent are below what the ear picks out anyway. */
    const key = (Math.round(v.heart_rate / 2) * 2) + ':' + Math.round(v.oxygen_saturation);
    if (key !== lastRateKey) {
      lastRateKey = key;
      schedule();
    }
  }

  function stop() {
    clearInterval(beatTimer);
    beatTimer = null;
    lastRateKey = null;
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
    lastRateKey = null;
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
    start, unlock, toggle, sync, trill, stop,
    get running() { return on && !!ctx && ctx.state === 'running'; },
    get enabled() { return on; },
    /* exposed so the interface can state the mapping rather than hide it */
    describe() {
      const v = currentVitals();
      if (!v) return '';
      const steps = (CFG.spo2Reference - v.oxygen_saturation) * CFG.semitonesPerPercent;
      return `${Math.round(v.heart_rate)} bpm, ${Math.round(pitchFor(v.oxygen_saturation))} Hz `
           + `(${CFG.baseNote} minus ${steps} semitone${steps === 1 ? '' : 's'})`;
    }
  };
})();
