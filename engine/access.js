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
  let known=false, mode='signin';
  let client=null, session=null, pending=-1, busy=false, loading=-1, lastFocus=null, msg='';
  const configured = () => SITE && !!CFG.supabaseUrl && !!CFG.supabaseKey &&
                           typeof supabase==='object' && typeof supabase.createClient==='function';

  function init(){
    /* The copyright line, and while any case is an unsigned draft, what that means. */
    const draft=CASES.some(c=>!c.card||c.card.unreviewed!==false);
    const legal=$('pk-legal');
    if(legal) legal.textContent=[CFG.legal||'', draft?'Cases are drafts under clinical review and are not for patient care.':'']
      .filter(Boolean).join(' ');
    const L=(typeof LANDING==='object'&&LANDING)||null;
    if(!SITE){
      /* The local build shows the welcome page only on request, for previews and screenshots. */
      if(L && /[?&]landing\b/.test(location.search)){ L.bind({signup:()=>L.hide(), login:()=>L.hide()}); L.show(); }
      return;
    }
    if(typeof ANALYTICS==='object') ANALYTICS.init();
    if(L){
      L.bind({signup:i=>showDialog(i,'signup'), login:i=>showDialog(i,'signin')});
      /* Until Supabase answers, guess from storage so a returning user does not see the welcome
         page flash up before their case board. */
      let stored=false;
      try{ for(let k=0;k<localStorage.length;k++){ const n=localStorage.key(k)||''; if(/^sb-.*-auth-token$/.test(n)) stored=true; } }catch(e){}
      if(!stored && !/[?&]code=/.test(location.search)) L.show();
    }
    $('wl-acct').hidden=false;
    bindDialog();
    if(!configured()){ msg='Sign-in is not configured for this build.'; paint(); return; }
    /* v0.18h. Google sign-in uses the PKCE redirect flow: Supabase sends the browser to
       Google and back to this page with ?code=..., which supabase-js exchanges for a
       session because detectSessionInUrl is on. Invite-only still holds: sign-ups are off
       in Supabase, so a Google account whose email was not invited is refused, and an
       invited email is linked to its Google identity automatically. */
    const oauthReturn = readOAuthReturn();
    client = supabase.createClient(CFG.supabaseUrl, CFG.supabaseKey,
      {auth:{persistSession:true, autoRefreshToken:true, detectSessionInUrl:!!CFG.googleSignIn, flowType:'pkce'}});
    client.auth.onAuthStateChange((_ev,s)=>{ session=s||null; A.user(session&&session.user&&session.user.id); paint(); });
    client.auth.getSession().then(({data})=>{
        session=(data&&data.session)||null; A.user(session&&session.user&&session.user.id);
        known=true; afterOAuthReturn(oauthReturn); paint(); })
      .catch(()=>{ session=null; known=true; afterOAuthReturn(oauthReturn); paint(); });
    if(CFG.googleSignIn){ $('signingoogle').hidden=false; $('signinor').hidden=false; }
    paint();
  }

  /* ---- Google (v0.18h) ---- */
  const PENDING_KEY='emsim.pendingCase';
  function readOAuthReturn(){
    const q=new URLSearchParams(location.search), h=new URLSearchParams(location.hash.replace(/^#/,''));
    const err=q.get('error_description')||h.get('error_description')||q.get('error')||h.get('error');
    const code=q.get('error_code')||h.get('error_code')||'';
    return {returned: q.has('code')||!!err, error: err?String(err).replace(/\+/g,' '):'', code};
  }
  function cleanUrl(){
    try{ history.replaceState(history.state, '', location.pathname); }catch(e){}
  }
  function afterOAuthReturn(r){
    if(!r.returned) return;
    cleanUrl();
    let prefix=''; try{ prefix=sessionStorage.getItem(PENDING_KEY)||''; sessionStorage.removeItem(PENDING_KEY); }catch(e){}
    if(r.error || !session){
      const closed=/signup|not allowed/i.test(r.code+' '+r.error);
      A.track('signin_failed',{method:'google', reason: closed?'signups_closed':'other'});
      const m= closed ? 'New accounts are closed right now. If you already have one, log in with the email it uses.'
                      : 'Google sign-in did not finish. Try again.';
      say(m); showDialog(-1,'signin'); $('signinerr').textContent=m;
      return;
    }
    const born=Date.parse((session.user&&session.user.created_at)||'')||0;
    A.track(Date.now()-born<10*60*1000?'signup_completed':'signin_succeeded',{method:'google'});
    const i=prefix?CASES.findIndex(c=>c.prefix===prefix):-1;
    if(i>=0) open(i);
  }
  async function google(){
    const b=$('signingoogle'); b.disabled=true; $('signinerr').textContent='';
    try{
      const want=pending>=0&&CASES[pending]?CASES[pending].prefix:'';
      try{ if(want) sessionStorage.setItem(PENDING_KEY,want); else sessionStorage.removeItem(PENDING_KEY); }catch(e){}
      const {error}=await client.auth.signInWithOAuth({provider:'google',
        options:{redirectTo: location.origin+location.pathname, queryParams:{prompt:'select_account'}}});
      if(error) throw error;
      /* The browser is now leaving for Google. */
    }catch(err){
      b.disabled=false;
      A.track('signin_failed',{method:'google', reason:'start_failed'});
      $('signinerr').textContent='Could not start Google sign-in. Check your connection and try again.';
    }
  }

  const signedIn = () => !!session;
  const isLocked = i => !!(CASES[i] && CASES[i].locked);

  /* The account line on the case board, and a repaint of the list so the lock marks follow
     the session. */
  function paint(){
    if(!SITE) return;
    const L=(typeof LANDING==='object'&&LANDING)||null;
    if(L && known){ if(session) L.hide(); else L.show(); }
    const box=$('wl-acct');
    const who=session&&session.user ? (session.user.email||'Signed in') : null;
    box.innerHTML = (who
        ? `<span class="who">Signed in as ${escA(who)}</span><button type="button" id="acct-out">Sign out</button>`
        : `<span class="who">Sign in to open a case.</span>`+
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
    $('signingoogle').addEventListener('click',google);
    $('signinswitch').addEventListener('click',e=>{ e.stopPropagation(); const b=e.target.closest('[data-signmode]'); if(b) setMode(b.dataset.signmode); });
    $('signinview').addEventListener('click',e=>{ if(e.target===$('signinview')) hideDialog(); });
    document.addEventListener('keydown',e=>{
      if(!modalOpen()) return;
      if(e.key==='Escape'){ e.preventDefault(); hideDialog(); }
    });
  }
  function modalOpen(){ const v=$('signinview'); return !!v && !v.classList.contains('hidden'); }
  /* v0.19. One dialog, two modes. Sign up is Google only unless emailSignUp is set: email
     sign-up needs a real email provider for the confirmation mail (see docs/deployment.md). */
  function setMode(m){
    mode=m;
    const up=m==='signup', pw=!up||!!CFG.emailSignUp, g=!!CFG.googleSignIn;
    $('signintitle').textContent= up?'Create your free account':'Log in';
    $('signinlede').textContent= up
      ? (g?'Sign up with your Google account. It takes a few seconds.':'Create an account with your email and a password.')
      : 'Welcome back.';
    ['signinemail','signinpass'].forEach(id=>{ $(id).hidden=!pw; const l=document.querySelector('label[for="'+id+'"]'); if(l) l.hidden=!pw; });
    $('signinok').hidden=!pw; $('signinok').textContent= up?'Create account':'Log in';
    $('signinpass').setAttribute('autocomplete', up?'new-password':'current-password');
    $('signingoogle').hidden=!g; $('signinor').hidden=!(g&&pw);
    const sw=$('signinswitch'); if(sw) sw.innerHTML= up
      ? 'Already have an account? <button type="button" class="linkbtn" data-signmode="signin">Log in</button>'
      : 'New here? <button type="button" class="linkbtn" data-signmode="signup">Create a free account</button>';
    $('signinfine').hidden=up;
    $('signinerr').textContent='';
  }
  function showDialog(i,m){
    if(!configured()){ say('Sign-in is not configured for this build.'); if(typeof LANDING==='object') LANDING.hide(); return; }
    pending=i; lastFocus=document.activeElement;
    setMode(m||'signin');
    $('signinerr').textContent=''; $('signinpass').value='';
    $('signinview').classList.remove('hidden');
    A.track(mode==='signup'?'signup_opened':'login_opened');
    setTimeout(()=>{ const e=$('signinemail'); if(e.hidden){ $('signingoogle').focus(); return; } (e.value?$('signinpass'):e).focus(); },0);
  }
  function hideDialog(){
    $('signinview').classList.add('hidden'); pending=-1;
    if(lastFocus&&lastFocus.focus) try{ lastFocus.focus(); }catch(e){}
  }
  async function submit(){
    if(mode==='signup') return signUpEmail();
    const email=$('signinemail').value.trim(), password=$('signinpass').value;
    if(!email||!password){ $('signinerr').textContent='Enter your email and password.'; return; }
    const ok=$('signinok'); ok.disabled=true; $('signinerr').textContent='';
    try{
      const {data,error}=await client.auth.signInWithPassword({email,password});
      if(error){
        A.track('signin_failed', {method:'password', reason: /invalid/i.test(error.message||'') ? 'wrong_credentials' : 'other'});
        $('signinerr').textContent = /invalid/i.test(error.message||'')
          ? 'That email and password do not match an account.'
          : 'Sign-in failed: '+(error.message||'unknown error')+'.';
        return;
      }
      session=data.session; msg='';
      A.user(session&&session.user&&session.user.id); A.track('signin_succeeded',{method:'password'});
      const want=pending; hideDialog(); paint();
      if(want>=0) open(want);
    }catch(err){
      A.track('signin_failed', {reason:'network'});
      $('signinerr').textContent='Could not reach the sign-in service. Check your connection and try again.';
    }finally{ ok.disabled=false; }
  }
  async function signUpEmail(){
    const email=$('signinemail').value.trim(), password=$('signinpass').value;
    if(!email||password.length<8){ $('signinerr').textContent='Enter your email and a password of at least 8 characters.'; return; }
    const ok=$('signinok'); ok.disabled=true;
    try{
      const {data,error}=await client.auth.signUp({email,password,options:{emailRedirectTo:location.origin+location.pathname}});
      if(error){ A.track('signup_failed',{method:'password'}); $('signinerr').textContent='Sign-up failed: '+(error.message||'unknown error')+'.'; return; }
      A.track('signup_completed',{method:'password'});
      if(data&&data.session){ session=data.session; hideDialog(); paint(); }
      else $('signinerr').textContent='Check your email for a link to confirm your address, then log in.';
    }catch(e){ $('signinerr').textContent='Could not reach the sign-in service. Check your connection and try again.'; }
    finally{ ok.disabled=false; }
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
