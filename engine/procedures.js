/* ---------- procedures (28 October 2026) ----------
   The Procedures box under the milestones badge on the case list, the window that lists the
   procedures, and the loading of one.

   A procedure is two downloads, both made only when the learner opens it:
     1. The code: three.js and the procedure engine (procsim-geom.js, procsim-core.js,
        procsim-view.js), as one script. The site serves it as its own file from the site's
        own address (ACCESS.pxScript), which the content security policy allows. The local
        build carries it inline as text and runs it on first use.
     2. The pack: the procedure itself, as data. In the site it is a locked pack, fetched
        through the same signed-in route, edge function and hash check as a locked case
        (ACCESS_UI.fetchProcedure). The local build has every pack inline.
   The code never comes from the pack bucket, because the policy does not let the page run
   code it downloads that way. That is on purpose.

   Nothing here names a procedure. */
const PROCEDURES = (function(){
  const A=(typeof ANALYTICS==='object'&&ANALYTICS)||{track(){}};
  const $=id=>document.getElementById(id);
  const esc=t=>String(t==null?'':t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let codeReady=null, busy=-1, msg='', open=false, lastFocus=null, view=null;
  const list=()=> (typeof PROCS!=='undefined' && Array.isArray(PROCS)) ? PROCS : [];

  const ICON='<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+
    '<path d="M14.5 3.5l6 6-9.2 9.2a3 3 0 0 1-2.1.9H5.6l-.1-3.6a3 3 0 0 1 .9-2.1z"/><path d="M12 6l6 6"/><path d="M3 21h8"/></svg>';

  function paintFloat(){
    const b=$('px-float'); if(!b) return;
    if(!list().length){ b.hidden=true; return; }
    b.hidden=false;
    b.innerHTML=`<button class="px-box" type="button" id="px-open" aria-haspopup="dialog" aria-label="Procedures: practice a procedure">
      <span class="px-ic">${ICON}</span><span class="px-lab">Procedures</span></button>`;
    $('px-open').onclick=show;
  }
  function locked(p){ return !!p.locked; }
  function windowHTML(){
    const rows=list().map((p,i)=>{
      const c=p.card||{};
      return `<li><button class="px-row" type="button" data-px="${i}" ${busy>=0?'disabled':''}>
          <span class="px-rowic">${ICON}</span>
          <span class="px-rowt"><b>${esc(c.title||p.prefix)}</b><span>${esc(c.subtitle||'')}</span>
          <span class="px-rowb">${esc(c.blurb||'')}</span></span>
          <span class="px-rowm">${busy===i?'Downloading…':(c.minutes?'About '+esc(c.minutes)+' min':'')}${locked(p)&&!signedIn()?' · Sign in':''}</span>
        </button></li>`;
    }).join('');
    return `<div class="ms-back" data-pxclose="1"></div>
      <div class="ms-card px-card" role="dialog" aria-modal="true" aria-labelledby="px-h">
        <button class="db-x ms-x" type="button" data-pxclose="1" aria-label="Close"><svg viewBox="0 0 24 24" class="ic" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
        <div class="px-in">
          <h2 id="px-h">Procedures</h2>
          <p class="px-sub">Practice a procedure step by step on a three-dimensional model. Learn mode prompts every step. Practice mode does not.</p>
          <ul class="px-list">${rows}</ul>
          <p class="px-msg" role="status">${esc(msg)}</p>
          <p class="px-fine">Procedures are drafts and are not physician reviewed. Each one names its sources.</p>
        </div>
      </div>`;
  }
  function signedIn(){ return typeof ACCESS_UI==='object' && ACCESS_UI.signedIn ? ACCESS_UI.signedIn() : false; }
  function paintWindow(){
    const m=$('px-modal'); if(!m) return;
    m.hidden=!open; m.innerHTML=open?windowHTML():'';
    if(!open) return;
    m.querySelectorAll('[data-pxclose]').forEach(b=>b.onclick=hide);
    m.querySelectorAll('[data-px]').forEach(b=>b.onclick=()=>choose(+b.dataset.px));
  }
  function show(){
    lastFocus=document.activeElement; open=true; msg=''; paintWindow();
    A.track('procedures_opened');
    const f=document.querySelector('#px-modal [data-px]')||document.querySelector('#px-modal .ms-x'); if(f) f.focus();
  }
  function hide(){
    open=false; paintWindow();
    if(lastFocus&&lastFocus.focus) try{ lastFocus.focus(); }catch(e){}
  }

  /* The code, once per page. */
  function loadCode(){
    if(codeReady) return codeReady;
    codeReady=new Promise((resolve,reject)=>{
      if(typeof PXVIEW==='object'){ resolve(); return; }
      const inline=$('px-code');
      const s=document.createElement('script');
      if(inline && inline.textContent.trim()){
        s.textContent=inline.textContent;
        document.head.appendChild(s);
        if(typeof PXVIEW==='object'||window.PXVIEW) resolve(); else reject(new Error('inline'));
        return;
      }
      const src=(typeof ACCESS==='object'&&ACCESS.pxScript)||'';
      if(!src){ reject(new Error('none')); return; }
      s.src=src; s.async=true;
      s.onload=()=>resolve(); s.onerror=()=>reject(new Error('network'));
      document.head.appendChild(s);
    }).catch(e=>{ codeReady=null; throw e; });
    return codeReady;
  }
  function webgl(){
    try{ const c=document.createElement('canvas'); return !!(c.getContext('webgl2')||c.getContext('webgl')); }catch(e){ return false; }
  }
  async function choose(i){
    const p=list()[i]; if(!p||busy>=0) return;
    if(!webgl()){ msg='This browser cannot show 3D graphics (WebGL), which the procedures need.'; paintWindow(); return; }
    busy=i; msg=''; paintWindow();
    const t0=Date.now();
    try{
      let pack=p;
      const work=[loadCode()];
      if(locked(p)){
        if(!(typeof ACCESS_UI==='object'&&ACCESS_UI.fetchProcedure)) throw Object.assign(new Error('x'),{userMessage:'Procedures cannot be opened in this build.'});
        work.push(ACCESS_UI.fetchProcedure(p, ()=>choose(i)).then(k=>{ pack=k; }));
      }
      await Promise.all(work);
      A.track('procedure_loaded',{procedure:p.prefix, ms:Date.now()-t0});
      list()[i]=pack;
      busy=-1; open=false; paintWindow();
      start(pack);
    }catch(err){
      busy=-1;
      if(err&&err.code==='signin'){ msg=''; paintWindow(); return; }   /* the sign-in dialog is up; it retries */
      A.track('procedure_load_failed',{procedure:p.prefix, reason:(err&&err.reason)||(err&&err.message)||'other'});
      msg=(err&&err.userMessage)||'This procedure could not be opened. Try again.';
      paintWindow();
    }
  }
  function start(pack){
    const host=$('px-sim'); if(!host) return;
    document.body.classList.add('px-on');
    view=PXVIEW.open({pack, host, mode:'learn', hand:'right',
      onStart:o=>A.track('procedure_started',{procedure:pack.prefix, mode:o.mode, hand:o.hand}),
      onFinish:d=>A.track('procedure_finished',{procedure:pack.prefix, mode:d.mode, seconds:Math.round(d.seconds),
        errors:d.errors.length, critical:d.critical, clean:d.clean, total:d.total}),
      onClose:()=>{ document.body.classList.remove('px-on'); view=null; const b=$('px-open'); if(b) b.focus(); }});
  }
  function init(){
    const m=$('px-modal');
    if(m) document.addEventListener('keydown',e=>{ if(open && e.key==='Escape'){ e.preventDefault(); hide(); } });
    paintFloat();
  }
  return {init, show, hide, paintFloat, loadCode, _view:()=>view};
})();
