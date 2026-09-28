/* ---------- access (v0.18) ----------
   Who may open which case, in the deployed build.

   The local build (build/simulator.html) carries every case and has no backend; there this
   module does nothing and every case opens as before. The deployed build (site/index.html)
   carries a stub for each locked case: the card the case list shows, the patient's age and
   sex, and the SHA-256 of the pack. Opening a locked case asks an invited, signed-in user's
   session for the pack from the `case-pack` edge function, checks the bytes against that
   hash, and only then puts the pack in place of the stub and opens it the ordinary way.

   The hash check is what keeps a pack and the engine that plays it in step. A site
   redeployed without re-uploading the packs, or a pack uploaded from a different build, is
   refused with a message rather than played by an engine that may read it differently.

   Nothing here is a secret. The Supabase URL and key in ACCESS are the public ones; what
   a user may fetch is decided by the edge function and the database, not by this file. */
const ACCESS_UI = (function(){
  /* Analytics calls are no-ops unless ANALYTICS is present and configured (site build). */
  const A = (typeof ANALYTICS==='object' && ANALYTICS) || {track(){}, user(){}, count(){}};
  const CFG = (typeof ACCESS==='object' && ACCESS) || {mode:'local'};
  const SITE = CFG.mode==='site';
  const $ = id => document.getElementById(id);
  let client=null, session=null, pending=-1, busy=false, loading=-1, lastFocus=null, msg='';
  const configured = () => SITE && !!CFG.supabaseUrl && !!CFG.supabaseKey &&
                           typeof supabase==='object' && typeof supabase.createClient==='function';

  function init(){
    /* The copyright line, and while any case is an unsigned draft, what that means. */
    const draft=CASES.some(c=>!c.card||c.card.unreviewed!==false);
    const legal=$('pk-legal');
    if(legal) legal.textContent=[CFG.legal||'', draft?'Cases are drafts under clinical review and are not for patient care.':'']
      .filter(Boolean).join(' ');
    if(!SITE) return;
    if(typeof ANALYTICS==='object') ANALYTICS.init();
    $('wl-acct').hidden=false;
    bindDialog();
    if(!configured()){ msg='Sign-in is not configured for this build.'; paint(); return; }
    client = supabase.createClient(CFG.supabaseUrl, CFG.supabaseKey,
      {auth:{persistSession:true, autoRefreshToken:true, detectSessionInUrl:false}});
    client.auth.onAuthStateChange((_ev,s)=>{ session=s||null; A.user(session&&session.user&&session.user.id); paint(); });
    client.auth.getSession().then(({data})=>{ session=(data&&data.session)||null; A.user(session&&session.user&&session.user.id); paint(); })
      .catch(()=>{ session=null; paint(); });
    paint();
  }

  const signedIn = () => !!session;
  const isLocked = i => !!(CASES[i] && CASES[i].locked);

  /* The account line on the case board, and a repaint of the list so the lock marks follow
     the session. */
  function paint(){
    if(!SITE) return;
    const box=$('wl-acct');
    const who=session&&session.user ? (session.user.email||'Signed in') : null;
    box.innerHTML = (who
        ? `<span class="who">Signed in as ${escA(who)}</span><button type="button" id="acct-out">Sign out</button>`
        : `<span class="who">Invite only. Sign in to open a case.</span>`+
          (configured()?`<button type="button" id="acct-in">Sign in</button>`:''))+
      `<span class="msg" role="status">${escA(msg)}</span>`;
    const bi=$('acct-in'); if(bi) bi.onclick=()=>showDialog(-1);
    const bo=$('acct-out'); if(bo) bo.onclick=signOut;
    if(typeof wlVisible==='function' && wlVisible() && typeof renderPicker==='function') renderPicker();
  }
  function escA(t){ return String(t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function say(t){ msg=t||''; paint(); }

  /* ---- the dialog ---- */
  let bound=false;
  function bindDialog(){
    if(bound) return; bound=true;
    $('signinform').addEventListener('submit',e=>{ e.preventDefault(); submit(); });
    $('signincancel').addEventListener('click',hideDialog);
    $('signinview').addEventListener('click',e=>{ if(e.target===$('signinview')) hideDialog(); });
    document.addEventListener('keydown',e=>{
      if(!modalOpen()) return;
      if(e.key==='Escape'){ e.preventDefault(); hideDialog(); }
    });
  }
  function modalOpen(){ const v=$('signinview'); return !!v && !v.classList.contains('hidden'); }
  function showDialog(i){
    if(!configured()){ say('Sign-in is not configured for this build.'); return; }
    pending=i; lastFocus=document.activeElement;
    $('signinerr').textContent=''; $('signinpass').value='';
    $('signinview').classList.remove('hidden');
    setTimeout(()=>{ const e=$('signinemail'); (e.value?$('signinpass'):e).focus(); },0);
  }
  function hideDialog(){
    $('signinview').classList.add('hidden'); pending=-1;
    if(lastFocus&&lastFocus.focus) try{ lastFocus.focus(); }catch(e){}
  }
  async function submit(){
    const email=$('signinemail').value.trim(), password=$('signinpass').value;
    if(!email||!password){ $('signinerr').textContent='Enter your email and password.'; return; }
    const ok=$('signinok'); ok.disabled=true; $('signinerr').textContent='';
    try{
      const {data,error}=await client.auth.signInWithPassword({email,password});
      if(error){
        A.track('signin_failed', {reason: /invalid/i.test(error.message||'') ? 'wrong_credentials' : 'other'});
        $('signinerr').textContent = /invalid/i.test(error.message||'')
          ? 'That email and password do not match an invited account.'
          : 'Sign-in failed: '+(error.message||'unknown error')+'.';
        return;
      }
      session=data.session; msg='';
      A.user(session&&session.user&&session.user.id); A.track('signin_succeeded');
      const want=pending; hideDialog(); paint();
      if(want>=0) open(want);
    }catch(err){
      A.track('signin_failed', {reason:'network'});
      $('signinerr').textContent='Could not reach the sign-in service. Check your connection and try again.';
    }finally{ ok.disabled=false; }
  }
  async function signOut(){
    /* Local scope: this browser only. The default signs the account out on every device. */
    A.track('signed_out'); A.user(null);
    try{ await client.auth.signOut({scope:'local'}); }catch(e){}
    /* Reloading drops every pack already fetched in this tab along with the session. */
    location.reload();
  }

  /* ---- opening a locked case ---- */
  async function open(i){
    if(!isLocked(i)){ chooseCase(i); return; }
    if(busy){ say('Another case is still loading.'); return; }
    if(!configured()){ say('Sign-in is not configured for this build.'); return; }
    busy=true;
    /* A returning user can click before init's getSession has answered. Ask again rather
       than showing the sign-in box to someone who is signed in. */
    if(!session){
      try{ const {data}=await client.auth.getSession(); session=(data&&data.session)||null; }catch(e){}
    }
    if(!session){ busy=false; showDialog(i); return; }
    say(''); loading=i; paintRow();
    const t0=Date.now(), prefix=CASES[i].prefix;
    try{
      const pack=await fetchPack(CASES[i]);
      A.track('case_loaded', {case:prefix, ms:Date.now()-t0, bytes:CASES[i].packBytes||null});
      CASES[i]=pack;
      busy=false; loading=-1; paintRow();
      chooseCase(i);
    }catch(err){
      loading=-1;
      A.track('case_load_failed', {case:prefix, reason:(err&&err.reason)||(err&&err.code)||'other', status:(err&&err.status)||null});
      if(err&&err.code==='signin'){ session=null; paint(); showDialog(i); }
      else say((err&&err.userMessage)||'This case could not be opened. Try again.');
    }finally{
      busy=false; loading=-1; paintRow();
    }
  }
  /* The loading mark lives in state, not only on the element, because a token refresh
     repaints the list mid-download. renderPicker asks loadingIndex(). */
  function paintRow(){
    document.querySelectorAll('.wl-case.loading').forEach(r=>r.classList.remove('loading'));
    if(loading>=0){ const r=document.querySelector('.wl-case[data-case="'+loading+'"]'); if(r) r.classList.add('loading'); }
  }
  function fail(userMessage,code,reason,status){ const e=new Error(userMessage); e.userMessage=userMessage; e.code=code; e.reason=reason; e.status=status; return e; }
  async function fetchPack(stub){
    let s=null, gsErr=null;
    try{ const r=await client.auth.getSession(); s=r.data&&r.data.session; gsErr=r.error; }  // refreshes an expired token
    catch(e){ gsErr=e; }
    /* A refresh that failed for want of a network is not a signed-out user. */
    if(!s&&gsErr) throw fail('Could not reach the sign-in service. Check your connection and try again.');
    if(!s) throw fail('Sign in to open this case.','signin');
    if(!(window.crypto&&crypto.subtle)) throw fail('This browser cannot verify the case download. Use a current browser over https.');
    const ctl=new AbortController(), timer=setTimeout(()=>ctl.abort(),30000);
    let res;
    try{
      res=await fetch(CFG.supabaseUrl.replace(/\/+$/,'')+'/functions/v1/'+encodeURIComponent(CFG.edgeFunction||'case-pack'),{
        method:'POST', signal:ctl.signal,
        headers:{'Authorization':'Bearer '+s.access_token,'apikey':CFG.supabaseKey,'Content-Type':'application/json'},
        body:JSON.stringify({prefix:stub.prefix, sha256:stub.packSha256})});
    }catch(e){
      throw fail(e&&e.name==='AbortError'?'The case took too long to download. Try again.':'Could not reach the server. Check your connection and try again.',undefined,e&&e.name==='AbortError'?'timeout':'network');
    }finally{ clearTimeout(timer); }
    if(res.status===401) throw fail('Your session has ended. Sign in again.','signin','session_ended',401);
    if(res.status===403) throw fail('Your account does not have access to cases right now.',undefined,'no_access',403);
    if(res.status===404) throw fail('This case is not available right now. If it was just updated, try again in a minute.',undefined,'not_found',404);
    if(res.status===429) throw fail('You have opened a lot of cases in a short time. Try again later.',undefined,'rate_limited',429);
    if(!res.ok) throw fail('The server could not send this case ('+res.status+'). Try again.',undefined,'server_error',res.status);
    const text=await res.text();
    const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
    const hex=[...new Uint8Array(digest)].map(b=>b.toString(16).padStart(2,'0')).join('');
    if(hex!==stub.packSha256) throw fail('This case is being updated. Try again in a few minutes.',undefined,'hash_mismatch');
    let pack;
    try{ pack=JSON.parse(text); }catch(e){ throw fail('The case download was damaged. Try again.'); }
    if(!pack||pack.prefix!==stub.prefix||pack.locked) throw fail('The server sent the wrong case. Try again.');
    return pack;
  }

  return {init, open, isLocked, signedIn, modalOpen, loadingIndex:()=>loading, site:SITE};
})();
