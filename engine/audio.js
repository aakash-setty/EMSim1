/* ============================================================
   Audio. Three channels:

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
   2. A short two-note trill whenever the nurse issues a prompt, and a shorter,
      softer cue for every other nurse line. These are a person speaking rather
      than equipment, so neither is gated on the monitor and both fire from the
      first line whether or not anything is attached.
   3. Ward ambience, looping under everything at a very low level. It is the room
      rather than the patient or the nurse, so it is gated on neither the monitor
      nor anything clinical: it runs from the moment a case begins until the moment
      it ends, and it is silent everywhere else, which means the welcome screen,
      the splash, and the debrief. That last one is deliberate. The debrief is
      reading rather than resuscitating, and a room that is still humming while a
      learner reads about what they missed is the interface failing to notice that
      the case is over.

      It changes one thing that was previously load-bearing: the room is no longer
      silent before the monitor is attached. What is missing then is the MONITOR's
      sound, which is the point being made, and a ward that was silent until
      somebody attached a monitor was always the less truthful half of it.

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
  /* The room. `scene` is the only thing that decides whether it plays, and it is set by
     the interface at the two moments that matter rather than inferred from anything the
     patient is doing. */
  let ambBuffer = null, ambSource = null, ambGain = null, ambState = 'unloaded';
  let scene = 'idle';

  const HR_MIN = 20, HR_MAX = 220;   /* the validator's plausible range for a phase */

  /* Output levels, in one place because they are relative to each other rather than
     absolute, and every adjustment so far has been to the balance rather than to a single
     sound. All three were set by ear while playing a case; the beat was halved and the
     cue doubled on the author's instruction after doing so.

     **Peak gain is not perceived loudness and these numbers should not be read as a
     ranking.** The beat is a held tone at the saturation pitch, the cue is two very short
     components an octave up, and the trill is two sustained tones higher still, so a beat
     at 0.15 sits under a cue at 0.110 to the ear even though the number is larger. What
     the numbers are good for is the invariants the test suite checks: the octave partial
     stays well under the body of the beat, the cue is not so far under the beat that a
     beat landing at the same moment masks it, and nothing is loud enough to dominate.

     The heartbeat is the one that has to be right, because it is the only sound that
     never stops. A heartbeat pitched to be noticeable on the first beat is unbearable by
     the two hundredth. */
  const LEVEL = { beatBody: 0.15, beatOctave: 0.015, cueLow: 0.110, cueHigh: 0.056,
                  trillLow: 0.22, trillHigh: 0.22, ambience: 0.03 };

  /* ---------- the shape of one beat ----------
     Timing only. The two gains live in LEVEL with everything else, because the balance
     between the sounds is one decision and splitting it across two blocks is how it
     drifts.

     The beat was a thump until v0.8: a sine whose pitch fell a major sixth over 140 ms
     under a 12 ms attack and an exponential tail. Both halves of that read as percussion.
     A falling pitch is the acoustic signature of a struck object, and an envelope that
     starts decaying the instant it arrives is heard as something being hit rather than as
     a tone. It also made the pitch mapping approximate: the perceived pitch of a glide
     sits somewhere between its endpoints, so "one semitone per percent of saturation" was
     true of the number fed to the oscillator and not of what anybody heard.

     What replaces it is a gated tone at a fixed frequency. Rise, hold, fall, and the hold
     is the part that matters: a tone that sustains before it stops is heard as a tone,
     where a tone that decays from its first instant is heard as a strike. The duration is
     fixed rather than derived from the interval, so the beat is the same sound at 60 and
     at 180 and only the spacing between beats changes.

     The envelope is a raised cosine written as a single value curve rather than as a pair
     of ramps. That buys two things. It reaches true zero at both ends, where the old
     exponential ramps stopped at 0.0001 and left a small step on every beat, three times
     a second for a whole case. And the curve has no corner at the top, so the transition
     into the hold does not itself click.

     The octave partial is what stops a bare sine sounding like a test tone. It is faint,
     ten percent of the fundamental, and it uses a SHORTER window than the body, so it
     colours the arrival and is gone before the hold ends. A partial that ran the full
     length would just make the beat brighter; one that leaves early makes it soft. */
  const BEAT = {
    durMs: 78, riseMs: 8, fallMs: 25,          /* hold is the remainder, 45 ms */
    octaveDurMs: 44, octaveRiseMs: 8, octaveFallMs: 20,
    /* No beat may occupy more than this fraction of the interval it sits in. Nothing in
       the authored range comes close, since the shortest interval the rhythm model will
       produce is the 240 ms refractory floor and 78 ms is a third of it. It is here so a
       future case authoring a faster rate cannot make one beat overlap the next. */
    maxDutyCycle: 0.45,
  };
  /* The ambience figure is against a known reference rather than against whatever the
     recording happened to be: the loop is peak-normalised to 0.95 at build time, so it
     sits at about -18.6 dBFS on its own and at roughly -51 dBFS once this gain and the
     master are applied. That is the number to change if the room is too loud or too
     quiet, and it means something because the asset is normalised. */
  const AMB_FADE_IN = 1.6, AMB_FADE_OUT = 0.7;

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
    /* Its own gain node, so the room can be faded in and out without touching anything
       else and so a future control could mute it on its own. */
    ambGain = ctx.createGain();
    ambGain.gain.value = 0;
    ambGain.connect(master);
    loadAmbience();
    return true;
  }

  /* ---------- the room ----------
     Decoded once, from base64 in the page rather than from a file, because the whole
     product is one HTML file and a second request is a second thing that can fail on a
     hospital network. Every failure path ends at 'absent', which is a simulator with a
     silent room and nothing else different: a case must never fail to start because a
     decoder did not like an mp3. */
  function loadAmbience() {
    if (ambState !== 'unloaded' || !ctx) return;
    const uri = (typeof AMBIENCE === 'string') ? AMBIENCE : '';
    const comma = uri.indexOf(',');
    if (comma < 0) { ambState = 'absent'; return; }
    ambState = 'loading';
    let bytes;
    try {
      const bin = atob(uri.slice(comma + 1));
      bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    } catch (e) { ambState = 'absent'; return; }
    /* decodeAudioData both returns a promise and calls the callback in current
       browsers, and only calls the callback in older ones, so both are wired and the
       handler is idempotent. */
    const done = buf => {
      if (ambState !== 'loading') return;
      ambBuffer = buf; ambState = 'ready';
      sync();
    };
    const failed = () => { if (ambState === 'loading') ambState = 'absent'; };
    try {
      const p = ctx.decodeAudioData(bytes.buffer, done, failed);
      if (p && p.then) p.then(done, failed);
    } catch (e) { failed(); }
  }

  function startAmbience() {
    if (ambState !== 'ready' || ambSource || !on || !ctx || !ambGain) return;
    const src = ctx.createBufferSource();
    src.buffer = ambBuffer;
    src.loop = true;
    /* Loop points a little inside the buffer. An mp3 decodes with a short run of
       encoder padding at each end that is not part of the recording, and looping across
       it is a click. The loop was crossfaded at build time so the material either side
       of the seam already matches; the material is broadband room noise with no rhythm,
       so losing fifty milliseconds at each end of forty-five seconds costs nothing and
       removes the one thing that could make the seam audible. */
    const pad = Math.min(0.05, src.buffer.duration / 8);
    src.loopStart = pad;
    src.loopEnd = Math.max(pad + 0.5, src.buffer.duration - pad);
    src.connect(ambGain);
    src.start(0, pad);
    ambSource = src;
    ramp(LEVEL.ambience, AMB_FADE_IN);
  }

  function stopAmbience() {
    if (!ambSource || !ctx) return;
    const src = ambSource;
    ambSource = null;
    ramp(0.0001, AMB_FADE_OUT);
    try { src.stop(ctx.currentTime + AMB_FADE_OUT + 0.05); } catch (e) { /* already stopped */ }
  }

  function ramp(to, secs) {
    if (!ambGain) return;
    const t = ctx.currentTime;
    try {
      ambGain.gain.cancelScheduledValues(t);
      ambGain.gain.setValueAtTime(ambGain.gain.value, t);
      ambGain.gain.linearRampToValueAtTime(to, t + secs);
    } catch (e) { ambGain.gain.value = to; }
  }

  /* Started and stopped by the scene and by nothing else. Called from sync(), which the
     monitor render calls sixty times a second, so it also recovers the room if the
     context was unlocked or the sound switched on part way through a case. */
  function ambienceUpkeep() {
    if (scene === 'case' && on) { loadAmbience(); startAmbience(); }
    else stopAmbience();
  }

  /* The interface says which of two situations we are in. Nothing is inferred: a case is
     running between Begin and the debrief, and everything else, including the splash of
     a case that has been chosen but not started, is idle. */
  function setScene(s) {
    scene = (s === 'case') ? 'case' : 'idle';
    if (scene === 'idle') { stopBeat(); stopAmbience(); return; }
    if (on && ctx) { loadAmbience(); startAmbience(); sync(); }
  }

  /* A5 at the reference saturation, one semitone per percent below it. */
  function pitchFor(spo2) {
    const steps = (CFG.spo2Reference - spo2) * CFG.semitonesPerPercent;
    return CFG.baseHz * Math.pow(2, -steps / 12);
  }

  /* A rise, a hold and a fall as one array of gain values, both edges shaped as a raised
     cosine. Sampled at a fixed rate rather than a fixed point count, so a longer window
     gets more points instead of a coarser curve. The first and last values are exactly
     zero, which is what keeps the beat free of the step the old exponential ramps left. */
  function window_(durS, riseS, fallS, peak) {
    const n = Math.max(32, Math.round(durS * 8000));
    const a = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const t = (i / (n - 1)) * durS;
      let k;
      if (t < riseS)               k = 0.5 - 0.5 * Math.cos(Math.PI * (t / riseS));
      else if (t > durS - fallS)   k = 0.5 - 0.5 * Math.cos(Math.PI * ((durS - t) / fallS));
      else                         k = 1;
      a[i] = peak * k;
    }
    a[0] = 0; a[n - 1] = 0;
    return a;
  }

  /* One partial: a sine at a fixed frequency under one of those windows. No pitch
     movement of any kind, which is the whole difference between a beep and a knock. */
  function partial(hz, at, durS, riseS, fallS, peak) {
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = 'sine';
    o.frequency.setValueAtTime(hz, at);
    g.gain.setValueAtTime(0, at);
    g.gain.setValueCurveAtTime(window_(durS, riseS, fallS, peak), at, durS);
    o.connect(g).connect(master);
    o.start(at);
    o.stop(at + durS + 0.02);
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

  /* One beat: the body, plus a faint octave that leaves before the body does.
     `intervalMs` is the interval this beat sits in, and it is read only by the duty-cycle
     guard. Under every rate any case can author the guard is inactive and the beat is the
     same length every time, which is the point of it. */
  function beat(hz, intervalMs, gain) {
    const t = ctx.currentTime + 0.01;
    const room = (intervalMs / 1000) * BEAT.maxDutyCycle;
    const k = Math.min(1, room / (BEAT.durMs / 1000));
    partial(hz, t,
            (BEAT.durMs / 1000) * k, (BEAT.riseMs / 1000) * k, (BEAT.fallMs / 1000) * k,
            LEVEL.beatBody * gain);
    partial(hz * 2, t,
            (BEAT.octaveDurMs / 1000) * k, (BEAT.octaveRiseMs / 1000) * k,
            (BEAT.octaveFallMs / 1000) * k,
            LEVEL.beatOctave * gain);
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
    /* Nothing sounds outside a running case. The room stops because it is the room and
       the case is over; the heartbeat stops for the same reason, and it has to be checked
       here rather than only in setScene, because sync() runs sixty times a second and
       would otherwise start the chain again on the next frame. */
    if (scene !== 'case') { stopBeat(); stopAmbience(); return; }
    ambienceUpkeep();
    /* stopBeat, not stop. Losing the monitor silences the heartbeat and must not silence
       the room: the resident has taken equipment off a patient, not left the ward. */
    if (!currentVitals()) { if (beatTimer !== null) stopBeat(); return; }
    if (beatTimer === null) tick();
  }

  function stopBeat() {
    clearTimeout(beatTimer);
    beatTimer = null;
    prevMs = null;
  }

  /* Everything. This is what the interface calls when a case ends and when it is torn
     down, and it is the only thing that has to be right for the requirement that no
     sound survives into the debrief or back to the welcome screen. */
  function stop() {
    stopBeat();
    stopAmbience();
  }

  /* Nurse prompt: a rising two-note trill, deliberately unlike the heartbeat. */
  function trill() {
    if (!on || !ensure()) return;
    const t = ctx.currentTime + 0.01;
    [[1318.5, 0, LEVEL.trillLow], [1760.0, 0.09, LEVEL.trillHigh]].forEach(([hz, off, g]) => {
      const o = ctx.createOscillator(), gn = ctx.createGain();
      o.type = 'triangle';
      o.frequency.setValueAtTime(hz, t + off);
      gn.gain.setValueAtTime(0.0001, t + off);
      gn.gain.exponentialRampToValueAtTime(g, t + off + 0.015);
      gn.gain.exponentialRampToValueAtTime(0.0001, t + off + 0.14);
      o.connect(gn).connect(master);
      o.start(t + off);
      o.stop(t + off + 0.16);
    });
  }

  /* A short soft cue for a nurse line that is not a prompt: "giving five milligrams of
     metoprolol", a result landing, a blocked action. It exists so that a line nobody was
     looking at still registers, and the whole design problem is that it fires far more
     often than the trill does and therefore must not be noticeable enough to irritate.
     Three things keep it that way: it is brief, it is about half the trill's amplitude,
     and repeats inside a quarter of a second are dropped, because a submitted basket of
     orders narrates several lines at one instant and a burst of clicks would read as a
     fault. Two components a fifth of an octave apart, both decaying inside
     forty milliseconds, which reads as a soft wooden tick rather than as a tone. */
  let lastCue = 0;
  function cue() {
    if (!on || !ensure()) return;
    const wall = Date.now();
    if (wall - lastCue < 250) return;
    lastCue = wall;
    const t = ctx.currentTime + 0.01;
    [[520, LEVEL.cueLow, 0.030], [780, LEVEL.cueHigh, 0.022]].forEach(([hz, g, dur]) => {
      const o = ctx.createOscillator(), gn = ctx.createGain();
      o.type = 'triangle';
      o.frequency.setValueAtTime(hz, t);
      o.frequency.exponentialRampToValueAtTime(hz * 0.82, t + dur);
      gn.gain.setValueAtTime(0.0001, t);
      gn.gain.exponentialRampToValueAtTime(g, t + 0.006);
      gn.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.connect(gn).connect(master);
      o.start(t);
      o.stop(t + dur + 0.02);
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
    /* Clear the beat first. Calling start() while one is already pending would leave
       two chains running against each other, and the only symptom would be a beat that
       sounds subtly doubled. */
    stopBeat();
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
    start, unlock, toggle, sync, trill, cue, stop, setScene, intervalModel,
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
    get rhythm() { return rhythmNow(); },
    /* Exposed for the same reason describe() is: the balance between the sounds is a
       decision, and a decision nothing can check is a decision that drifts. */
    get levels() { return Object.assign({}, LEVEL); },
    /* The beat's envelope, for the interface and for the assertion that no beat can run
       into the next one. Timing in milliseconds, as authored. */
    get beatShape() {
      return Object.assign({ holdMs: BEAT.durMs - BEAT.riseMs - BEAT.fallMs }, BEAT);
    },
    /* For the interface and for tests. `state` is unloaded, loading, ready or absent;
       absent is a build with no ambience asset or a decoder that refused it, and is a
       working simulator rather than an error. */
    get ambience() {
      return { scene, state: ambState, playing: !!ambSource, level: LEVEL.ambience };
    }
  };
})();
