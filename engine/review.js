/* ---------- review tools: the local build only ----------
   build_simulator.py inlines this file into build/simulator.html and leaves it out of
   site/index.html, and the build refuses to write a site that contains it. The deployed
   product never has it. It is for authors and reviewers playing a case through quickly.

   A speed control. The case clock runs at 1, 2, 4, 8 or 16 times real time. It works by
   moving the clock's start time (T0) back while a case is running and not paused, so the
   engine sees nothing new: the fold, every deadline, every prompt and every transition
   happen exactly as they would at 1x, only sooner. Nothing here changes a case, a score
   or a debrief, and the chosen speed is shown on the debrief so a reviewer's run is not
   mistaken for a real one.

   Keys, while a case is running and focus is not in a text box: ] faster, [ slower. */
const REVIEW_SPEED=(()=>{
  const RATES=[1,2,4,8,16];
  let rate=1, last=Date.now(), box=null, maxRate=1, wasStarted=false;

  /* Runs whether or not the tab is visible, so a background tab does not lose time. The
     step is taken from the wall clock rather than assumed, so a throttled interval still
     advances the case by the right amount. */
  function step(){
    const t=Date.now(), dt=t-last; last=t;
    const started=(typeof STARTED!=='undefined') && STARTED;
    if(started && !wasStarted) maxRate=rate;          /* a new run begins at the current rate */
    wasStarted=started;
    const running=started && !ENDED && !PAUSED;
    if(running && rate>1){ T0-=(rate-1)*dt; if(rate>maxRate) maxRate=rate; }
    if(box) box.style.display=(typeof STARTED!=='undefined' && STARTED && !ENDED)?'flex':'none';
  }
  function set(r){
    if(!RATES.includes(r)) return;
    step();                       /* bank the time already run at the old rate */
    rate=r; paint();
  }
  function paint(){
    if(!box) return;
    box.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed', String(+b.dataset.rate===rate)));
  }
  function build(){
    const css=document.createElement('style');
    css.textContent=`
      #reviewspeed{position:fixed;right:14px;bottom:14px;z-index:90;display:none;align-items:center;gap:4px;
        padding:5px 7px;border-radius:10px;background:rgba(21,48,66,.88);color:#fff;
        font:500 11px/1 var(--mono,monospace);box-shadow:0 4px 14px rgba(0,0,0,.25)}
      #reviewspeed .lb{opacity:.8;margin-right:4px;letter-spacing:.04em;text-transform:uppercase}
      #reviewspeed button{font:inherit;color:#fff;background:transparent;border:1px solid rgba(255,255,255,.35);
        border-radius:6px;padding:4px 6px;cursor:pointer}
      #reviewspeed button[aria-pressed="true"]{background:#fff;color:#153042;border-color:#fff}`;
    document.head.appendChild(css);
    box=document.createElement('div');
    box.id='reviewspeed';
    box.setAttribute('role','group');
    box.setAttribute('aria-label','Review speed, local build only');
    box.title='Review speed. Local build only; the deployed site does not have this. Keys: [ and ]';
    box.innerHTML='<span class="lb">Review speed</span>'
      +RATES.map(r=>`<button type="button" data-rate="${r}">${r}x</button>`).join('');
    box.addEventListener('click',e=>{ const b=e.target.closest('button[data-rate]'); if(b) set(+b.dataset.rate); });
    document.body.appendChild(box);
    paint();
  }
  document.addEventListener('keydown',e=>{
    if(e.metaKey||e.ctrlKey||e.altKey) return;
    if(e.key!=='['&&e.key!==']') return;
    const tg=e.target, typing=tg&&(tg.tagName==='INPUT'||tg.tagName==='TEXTAREA'||tg.isContentEditable);
    if(typing||typeof STARTED==='undefined'||!STARTED||ENDED) return;
    const i=RATES.indexOf(rate)+(e.key===']'?1:-1);
    if(i>=0&&i<RATES.length){ set(RATES[i]); e.preventDefault(); }
  });
  /* The debrief says when a run was sped up, so a reviewer's run is never read as a real
     one. Added from here rather than in ui.js, so the product carries no trace of it. */
  function markDebrief(){
    const v=document.getElementById('endview');
    if(!v||v.classList.contains('hidden')||maxRate<=1) return;
    if(v.querySelector('.reviewspeed-note')) return;
    const at=v.querySelector('.gate')||v.querySelector('.dbf');
    if(!at) return;
    const n=document.createElement('p');
    n.className='sub reviewspeed-note';
    n.textContent='Review build: this run was played at up to '+maxRate+'x speed.';
    const h=at.querySelector('h2');
    if(h) h.after(n); else at.prepend(n);
  }
  build();
  setInterval(step,50);
  new MutationObserver(markDebrief).observe(document.getElementById('endview')||document.body,{childList:true,subtree:false});
  return {rate:()=>rate, set, fastestThisRun:()=>maxRate};
})();
