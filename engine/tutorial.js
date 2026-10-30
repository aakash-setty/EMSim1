/* ---------- How it works: a short tutorial (30 October 2026) ----------
   Owner request: "a small tutorial to know the general idea of how to use the sim ... a
   tutorial button on the home screen ... Be thoughtful on what a new user may be intimidated
   by or would need to know to not get frustrated."

   Eight screens (the mode screen and most words removed on 30 October, owner: "too many words"),
   each one real screenshot of the case screen (CHFE, every piece of case text
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
     body:`<p>The patient changes with what you do and when. You cannot break anything, and every case can be replayed.</p>
      <ol class="tut-key"><li>Nurse</li><li>Monitor</li><li>Voice order and search</li><li>Tabs</li>
      <li>Orders</li><li>Patient</li><li>Pending and chart</li></ol>`},
    {t:'The monitor is blank until you attach it', img:'monitor',
     alt:'A blank monitor, the Stabilization group with the monitor selected, and the monitor showing numbers',
     body:`<p>The top <b>Stabilization</b> group acts on the click: monitor, IV, pads, ABC exam.</p>
      <p>Most medicines need an IV first.</p>`},
    {t:'Everywhere else: select, then Submit Order', img:'basket',
     alt:'Four labs selected, with Submit Order showing a count of four',
     body:`<p>A click only selects. Nothing happens until <b>Submit Order</b>.</p><p>No doses to type.</p>`},
    {t:'Ask in your own words', img:'history',
     alt:'The paramedics\' handover and two questions to the patient',
     body:`<p>Type it the way you would say it: "What's going on?" One question at a time.</p>
      <p>On <b>Exam</b>, click a body system. Abnormal findings show in red.</p>`},
    {t:'Results take time', img:'record', alt:'The Pending box counting down four labs, and the chart below',
     body:`<p>Watch <b>Pending</b>. Keep treating while you wait.</p>`},
    {t:'Listen to the nurse', img:'nurse', alt:'The nurse at the top left of the screen',
     body:`<p>She tells you what she is doing, what cannot happen yet, and when the patient changes.</p>
      <p>Press <kbd>/</kbd> to search any order. Switching windows pauses the case.</p>`},
    {t:'Only a handoff ends the case', img:'handoff', alt:'The Handoff tab: disposition, diagnoses and the confirm buttons',
     body:`<p>Choose where the patient goes, name your diagnoses, then hand over.</p>`},
    {t:'Then read the debrief', img:'debrief', alt:'The debrief: critical actions completed and missed, with the case discussion',
     body:`<p>What you did or missed, when, and why it mattered. Replay as often as you like.</p>`},
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
        ${at>0?`<button type="button" class="tut-arrow prev" data-tutstep="-1" aria-label="Previous"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg></button>`:''}
        ${!last?`<button type="button" class="tut-arrow next" data-tutstep="1" aria-label="Next"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg></button>`:''}
        <div class="tut-foot">
          <div class="tut-dots" role="tablist" aria-label="Tutorial screens">${SCREENS.map((x,i)=>
            `<button type="button" role="tab" class="tut-dot${i===at?' on':''}" data-tutgo="${i}" aria-selected="${i===at}" aria-label="Screen ${i+1}: ${x.t.replace(/"/g,'&quot;')}"></button>`).join('')}</div>
          ${last?'<button type="button" class="btn" data-tutdone="1">Choose a case</button>':''}
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
    const f=m.querySelector(focusNext||'.tut-arrow.next,[data-tutdone],.tut-arrow.prev'); if(f) f.focus({preventScroll:true});
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
