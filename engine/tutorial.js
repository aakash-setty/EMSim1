/* ---------- How it works: a short tutorial (30 October 2026) ----------
   Owner request: "a small tutorial to know the general idea of how to use the sim ... a
   tutorial button on the home screen ... Be thoughtful on what a new user may be intimidated
   by or would need to know to not get frustrated."

   Nine screens, each one real screenshot of the case screen (CHFE, every piece of case text
   blurred before capture, engine/assets/tutorial/README.md) and a few plain sentences. What
   it covers is what trips a first run: the clock is real, the monitor is blank until it is
   attached, a click on most tabs only selects until Submit Order, the history is typed in
   your own words, results take time, the nurse will say why an order cannot happen yet, the
   pause at six minutes, and that only a handoff ends the case.

   Opened from the "How it works" button in the case list's banner and from the menu. The
   button is marked until the tutorial has been opened once in this browser. Nothing here
   names a case, a drug or a diagnosis. */
const TUTORIAL = (function(){
  const $=id=>document.getElementById(id);
  const A=(typeof ANALYTICS==='object'&&ANALYTICS)||{track(){}};
  const SEEN_KEY='emsim.tutorialSeen';
  const store={get(k){ try{ return localStorage.getItem(k); }catch(e){ return null; } },
               set(k,v){ try{ localStorage.setItem(k,v); }catch(e){} }};
  let open=false, at=0, lastFocus=null;

  /* Each screen: a title, its picture (an id in #tut-imgs), the picture's description, and
     the words. Words are plain HTML written here, not content from any case. */
  const SCREENS=[
    {t:'You are the doctor, and the clock is real', img:'overview',
     alt:'The case screen with seven numbered parts',
     body:`<p>A patient arrives and you run the first minutes of their care. Time runs as it would in a real resuscitation bay, and the patient gets better or worse with what you do and when. You cannot break anything, and every case can be replayed.</p>
      <ol class="tut-key"><li>The nurse, who reads back your orders and tells you what is happening.</li>
      <li>The monitor.</li><li>Voice order and search.</li>
      <li>The tabs: Stabilization, History, Exam, Labs/Imaging, Actions, Consults and Handoff.</li>
      <li>Where you choose orders.</li><li>The patient. Watch the face and the color.</li>
      <li>The record: what is pending and everything that has happened.</li></ol>`},
    {t:'Pick a mode, then Begin', img:'mode', alt:'The Begin button and the Normal and Easy switch',
     body:`<p>The medicine is the same in both. In <b>Easy</b>, the nurse speaks up sooner when something important is missing. In <b>Normal</b>, she waits much longer, so it shows what you would have done on your own.</p>
      <p class="tut-tip">First time? Choose Easy.</p>`},
    {t:'First moves: the monitor is blank until you attach it', img:'monitor',
     alt:'A blank monitor, the Stabilization group with the monitor selected, and the monitor showing numbers',
     body:`<p>Every case opens on <b>Stabilization</b>. Its top group acts the moment you click: the airway, breathing and circulation exam, the monitor, an IV and defibrillator pads.</p>
      <p>No numbers appear until the patient is on the monitor. That is on purpose: you decide when to look.</p>
      <p>Most medicines need an IV first. If one is missing, the nurse will say so.</p>`},
    {t:'Everywhere else: select, then Submit Order', img:'basket',
     alt:'Four labs selected, with Submit Order showing a count of four',
     body:`<p>On every other group, and on Labs/Imaging and Actions, a click only <b>selects</b>. Nothing happens to the patient until you press <b>Submit Order</b>.</p>
      <p>The blue bar lists what is selected and not yet sent. You can select on several tabs and send it all at once. Click a selected item again to remove it.</p>
      <p>You do not type doses. Each button is a standard order.</p>`},
    {t:'Ask in your own words, then examine', img:'history',
     alt:'The paramedics\' handover and two questions to the patient',
     body:`<p>On <b>History</b>, type a question the way you would say it: "What's going on?", "Any allergies?", "Do you take blood thinners?". Short is fine. One question at a time gets the clearest answer, and if the answer misses, rephrase. The paramedics' handover is at the top.</p>
      <p>On <b>Exam</b>, click a body system. The finding appears at once, and an abnormal one is marked in red. Repeat an exam later to see how the patient is now.</p>`},
    {t:'Results take time', img:'record', alt:'The Pending box counting down four labs, and the chart below',
     body:`<p>Labs and imaging run in the background. <b>Pending</b> counts them down and the nurse tells you when one is back. Results land in the <b>chart</b>, which you can filter or expand.</p>
      <p>A result shows the patient at the moment you ordered it, not when it arrives. Keep treating while you wait.</p>`},
    {t:'Listen to the nurse', img:'nurse', alt:'The nurse at the top left of the screen',
     body:`<p>She reads back each order, tells you when something cannot be done yet and why, and speaks up when the patient changes. A line in red is something she wants you to know.</p>
      <ul class="tut-list"><li>Press <kbd>/</kbd> or <b>Search</b> to find any order, result or note by name.</li>
      <li><b>Voice order</b> lets you say an order aloud, where your browser allows the microphone.</li>
      <li>At six minutes the case pauses once to ask for your differential. It is optional and not scored.</li>
      <li>Switch to another window and the case pauses itself.</li></ul>`},
    {t:'Only a handoff ends the case', img:'handoff', alt:'The Handoff tab: disposition, diagnoses and the confirm buttons',
     body:`<p>When you are ready, open <b>Handoff</b>. Choose where the patient goes, name your diagnoses (start typing to search the list, primary first), then <b>Hand over and end the case</b>.</p>
      <p>A case can also end early if the patient gets much worse. <b>Main menu</b> leaves at any point.</p>`},
    {t:'Then read the debrief', img:'debrief', alt:'The debrief: critical actions completed and missed, with the case discussion',
     body:`<p>It shows every critical action you did or missed, when, and why it mattered, followed by a discussion of the case.</p>
      <p>The scores point you to what to review. They do not rank you. Replay as often as you like.</p>`},
  ];

  function img(id){
    /* The debrief picture is the welcome page's own, so the page carries it once. */
    if(id==='debrief'){ const d=document.querySelector('.ld-shot img[alt^="The debrief"]'); return d?d.getAttribute('src'):''; }
    const t=$('tut-imgs'); const i=t&&t.content?t.content.getElementById('tut-'+id):null; return i?i.getAttribute('src'):''; }
  function html(){
    const s=SCREENS[at], n=SCREENS.length, last=at===n-1;
    const src=img(s.img);
    return `<div class="ms-back" data-tutclose="1"></div>
      <div class="ms-card tut-card" role="dialog" aria-modal="true" aria-labelledby="tut-h">
        <button class="db-x ms-x" type="button" data-tutclose="1" aria-label="Close the tutorial"><svg viewBox="0 0 24 24" class="ic" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
        <div class="tut-in">
          <figure class="tut-fig${s.img==='overview'?' wide':''}">${src?`<img src="${src}" alt="${s.alt.replace(/"/g,'&quot;')}">`:''}</figure>
          <div class="tut-txt">
            <p class="tut-step">How it works · ${at+1} of ${n}</p>
            <h2 id="tut-h">${s.t}</h2>
            <div class="tut-body">${s.body}</div>
          </div>
        </div>
        <div class="tut-foot">
          <div class="tut-dots" role="tablist" aria-label="Tutorial screens">${SCREENS.map((x,i)=>
            `<button type="button" role="tab" class="tut-dot${i===at?' on':''}" data-tutgo="${i}" aria-selected="${i===at}" aria-label="Screen ${i+1}: ${x.t.replace(/"/g,'&quot;')}"></button>`).join('')}</div>
          <div class="tut-btns">
            ${at>0?'<button type="button" class="btn ghost" data-tutstep="-1">Back</button>':'<button type="button" class="btn ghost" data-tutclose="1">Skip</button>'}
            ${last?'<button type="button" class="btn" data-tutdone="1">Choose a case</button>':'<button type="button" class="btn" data-tutstep="1">Next</button>'}
          </div>
        </div>
      </div>`;
  }
  function paint(focusNext){
    const m=$('tut-modal'); if(!m) return;
    m.hidden=!open; m.innerHTML=open?html():'';
    if(!open) return;
    m.querySelectorAll('[data-tutclose]').forEach(b=>b.onclick=hide);
    m.querySelectorAll('[data-tutstep]').forEach(b=>b.onclick=()=>go(at+Number(b.dataset.tutstep)));
    m.querySelectorAll('[data-tutgo]').forEach(b=>b.onclick=()=>go(Number(b.dataset.tutgo)));
    m.querySelectorAll('[data-tutdone]').forEach(b=>b.onclick=done);
    const f=m.querySelector(focusNext||'[data-tutstep="1"],[data-tutdone]'); if(f) f.focus();
  }
  function go(i){ if(i<0||i>=SCREENS.length) return; at=i; paint(); }
  function show(){
    lastFocus=document.activeElement; open=true; at=0;
    store.set(SEEN_KEY,'1'); markButtons();
    document.body.classList.add('tut-on');
    A.track('tutorial_opened');
    paint();
  }
  function hide(){
    if(!open) return;
    A.track('tutorial_closed',{screen:at+1, of:SCREENS.length});
    open=false; paint(); document.body.classList.remove('tut-on');
    if(lastFocus&&lastFocus.focus) try{ lastFocus.focus(); }catch(e){}
  }
  function done(){
    hide();
    const list=document.querySelector('.db-body'); if(list&&list.scrollIntoView) list.scrollIntoView({behavior:'smooth',block:'start'});
  }
  function markButtons(){
    const seen=!!store.get(SEEN_KEY);
    document.querySelectorAll('[data-tutorial]').forEach(b=>b.classList.toggle('tut-new',!seen));
  }
  function init(){
    if(!$('tut-modal')) return;
    document.addEventListener('click',e=>{ const b=e.target.closest&&e.target.closest('[data-tutorial]'); if(b){ e.preventDefault(); show(); } });
    document.addEventListener('keydown',e=>{
      if(!open) return;
      if(e.key==='Escape'){ e.preventDefault(); hide(); }
      else if(e.key==='ArrowRight'){ e.preventDefault(); go(at+1); }
      else if(e.key==='ArrowLeft'){ e.preventDefault(); go(at-1); }
    });
    markButtons();
  }
  return {init, show, hide, screens:()=>SCREENS.length, _at:()=>at};
})();
