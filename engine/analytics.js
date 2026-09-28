/* ---------- analytics (v0.18f) ----------
   Product analytics through PostHog, in the deployed site only. The local build and the
   tests never load PostHog; every call here is then a no-op.

   What is sent, and what is not. Events carry the case prefix, the difficulty, counts and
   durations, and the kind of ending. They never carry case text, typed questions, orders,
   diagnoses, the reflection note or anything a learner writes. Autocapture is off because it
   reads the text of what is clicked, and much of what is clicked here is case content.
   Session recording is off, and the vendored build cannot load it later.

   Who. A learner is identified by their Supabase user id and nothing else: no email, no
   name. Before sign-in they are an anonymous visitor, and person profiles are only made
   for identified users. */
const ANALYTICS = (function(){
  const CFG = (typeof ACCESS==='object' && ACCESS) || {mode:'local'};
  const on = CFG.mode==='site' && !!CFG.posthogKey && typeof posthog==='object' && posthog && typeof posthog.init==='function';
  let ready=false, errors=0, uid=null;
  const counts={};

  function init(){
    if(!on||ready) return;
    try{
      posthog.init(CFG.posthogKey, {
        api_host: CFG.posthogHost || 'https://us.i.posthog.com',
        ui_host: 'https://us.posthog.com',
        person_profiles: 'identified_only',
        autocapture: false,
        capture_pageview: true,
        capture_pageleave: true,
        disable_session_recording: true,
        disable_surveys: true,
        disable_external_dependency_loading: true,
        advanced_disable_toolbar_metrics: true,
        mask_all_text: true,
        mask_all_element_attributes: true,
      });
      ready=true;
    }catch(e){ ready=false; }
    window.addEventListener('error', e=>jsError(e && e.message));
    window.addEventListener('unhandledrejection', e=>jsError(e && e.reason && (e.reason.message||String(e.reason))));
  }
  function track(name, props){
    if(!ready) return;
    try{ posthog.capture(name, props||{}); }catch(e){}
  }
  /* Called by access.js whenever the session changes. */
  function user(id){
    if(!ready) return;
    try{
      if(id && id!==uid){ posthog.identify(id); uid=id; }
      else if(!id && uid){ posthog.reset(); uid=null; }
    }catch(e){}
  }
  /* A tally for the current run, sent with case_finished and then cleared. */
  function count(key, n){ counts[key]=(counts[key]||0)+(n||1); }
  function takeCounts(){ const c=Object.assign({},counts); Object.keys(counts).forEach(k=>delete counts[k]); return c; }
  /* Errors, at most five per page load, with the message cut to 200 characters. A stopgap
     until Sentry. */
  function jsError(msg){
    if(!ready || errors>=5) return;
    errors++;
    track('js_error', {message: String(msg||'unknown').slice(0,200),
                       case: (typeof PACK==='object' && PACK && PACK.prefix) || null});
  }
  return {init, track, user, count, takeCounts, enabled:()=>ready};
})();
