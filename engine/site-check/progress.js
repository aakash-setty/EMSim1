// Saved progress (28 October 2026), end to end against the mock's public.runs: autosave, leave
// and resume, the resumed run matching the one left, finishing into a score summary, the
// home panel, delete, Start over, the case-has-changed notice, a reload, and the local build.
const {chromium}=require('playwright');
const M='http://localhost:54321';
const ctl=b=>fetch(M+'/__ctl',{method:'POST',body:JSON.stringify(b)}).then(r=>r.json());
const table=()=>fetch(M+'/__runs').then(r=>r.json());
const setTable=rows=>fetch(M+'/__runs',{method:'POST',body:JSON.stringify({rows})}).then(r=>r.json());
(async()=>{
 const b=await chromium.launch({executablePath:process.env.CHROME||undefined});
 const ctx=await b.newContext({viewport:{width:1440,height:860}});
 const p=await ctx.newPage(); const errs=[], csp=[], dialogs=[];
 p.on('pageerror',e=>errs.push('pageerror: '+e.message));
 p.on('dialog',d=>{ dialogs.push(d.type()); d.accept().catch(()=>{}); });
 p.on('console',m=>{ const t=m.text(); if(/Content Security Policy|Refused to/.test(t)) csp.push(t.slice(0,200)); else if(m.type()==='error' && !/ERR_TUNNEL|status of (400|401|403|406|409|429|500)/.test(t)) errs.push('console: '+t.slice(0,200)); });
 const ok=(n,c,x)=>console.log((c?'ok   ':'FAIL ')+'progress: '+n+(c||x===undefined?'':'  -> '+JSON.stringify(x).slice(0,400)));
 const wait=ms=>p.waitForTimeout(ms);
 // A downloaded case waits behind the charging defibrillator until its button is pressed.
 const shock=async()=>{ for(let k=0;k<20;k++){ if(await p.evaluate(()=>{ const d=document.getElementById('chargedeliver'); return !!d&&!d.disabled&&!document.getElementById('chargeview').classList.contains('hidden'); })){ await p.click('#chargedeliver'); await wait(500); return; } await wait(150); } };
 await ctl({rpc:'ok',tamper:false,userOk:true,unconfirmed:false,storeOnly:false,runsFail:false}); await setTable([]);

 await p.goto('http://localhost:8080/'); await wait(1200);
 // Case numbers (28 October 2026): on the list, the welcome tiles, and found by "case N".
 const nums=await p.evaluate(()=>{
   const q=document.getElementById('wl-q'); q.value='case 4'; renderPicker();
   const hit=[...document.querySelectorAll('.wl-case')].map(b=>CASES[+b.dataset.case].prefix);
   q.value=''; renderPicker();
   return {n:CASES.length, cards:CASES.map(c=>c.card.number), rows:document.querySelectorAll('.wl-case .wl-no').length,
     tiles:document.querySelectorAll('.ld-case .n').length, hit}; });
 ok('every case has its own number, shown on every row and tile', new Set(nums.cards).size===nums.n&&nums.cards.every(n=>Number.isInteger(n)&&n>0)&&nums.rows===nums.n&&nums.tiles===nums.n, nums);
 ok('"case 4" finds exactly that case', nums.hit.length===1, nums.hit);
 ok('signed out: no home panel', await p.evaluate(()=>document.getElementById('wl-home').hidden&&!document.getElementById('picker').classList.contains('home-on')));
 const idx=await p.evaluate(()=>CASES.findIndex(c=>c.prefix==='CHFE'));
 const KEYS=await p.evaluate(()=>Object.fromEntries(CASES.map(c=>[c.prefix,c.versionKey])));
 ok('every case stub carries a version key', Object.values(KEYS).every(k=>/^[0-9a-f]{32}$/.test(k||'')), KEYS);
 await p.evaluate(i=>ACCESS_UI.open(i),idx); await wait(300);
 await p.fill('#signinemail','res@example.com'); await p.fill('#signinpass','right-password'); await p.keyboard.press('Enter'); await wait(2500);
 await shock();
 ok('signed in, the case splash is open', await p.evaluate(()=>PACK&&PACK.prefix==='CHFE'&&!document.getElementById('splash').classList.contains('hidden')));
 ok('the splash shows the case number', await p.evaluate(()=>document.getElementById('sp-no').textContent==='Case '+PACK.card.number&&!document.getElementById('sp-no').hidden));
 // The splash (29 October 2026): the patient's words come out of the mouth in a bubble, and the
 // mode is a small switch with an i that explains the other mode.
 const sp0=await p.evaluate(()=>{ const say=document.getElementById('sp-say'), t=say&&say.querySelector('.spsay-t'), path=say&&say.querySelector('path');
   const svg=document.querySelector('#sp-patient svg'), m=svg&&svg.querySelector('[data-rig="mouth"]');
   const mr=m&&m.getBoundingClientRect(), tr=t&&t.getBoundingClientRect();
   return {shown:!!say&&!say.hidden, text:t&&t.textContent, words:CASE.metadata.chief_complaint_patient_voice, d:(path&&path.getAttribute('d'))||'',
     sr:document.getElementById('sp-cc').classList.contains('srsay'), side:say&&say.dataset.side,
     clear:!!(mr&&tr)&&(tr.left>=mr.right||tr.right<=mr.left||tr.bottom<=mr.top),
     other:splashSayParts("Her mother: 'She wasn't making any sense.'"),
     seg:[...document.querySelectorAll('#sp-modes [data-mode]')].map(b=>b.dataset.mode+':'+b.getAttribute('aria-checked')), def:PROTO.difficulty.default}; });
 ok("the patient's words come out of the mouth in a bubble, kept in the card for a screen reader",
   sp0.shown&&sp0.text===sp0.words&&/Q/.test(sp0.d)&&sp0.sr&&sp0.clear&&['right','left','top'].includes(sp0.side), sp0);
 ok('a line given as "Speaker: words" names the speaker', sp0.other.who==='Her mother'&&sp0.other.text==="She wasn't making any sense.", sp0.other);
 ok('the mode is a small switch with the default chosen', sp0.seg.length===2&&sp0.seg[0]===sp0.def+':true', sp0.seg);
 const sp1=await p.evaluate(()=>{ const r=n=>n.getBoundingClientRect(), t=r(document.querySelector('#sp-say .spsay-t')), st=r(document.querySelector('#splash .spstage'));
   const above=[document.getElementById('sp-arrival'),document.getElementById('sp-title')].find(n=>n.offsetParent&&n.textContent.trim());
   const act=r(document.querySelector('#splash .splashactions')), sw=r(document.getElementById('sp-modes')), go=r(document.getElementById('beginbtn'));
   return {crosses:t.right>st.right+40&&t.left<st.right, clearAbove:t.top>=r(above).bottom, clearBelow:t.bottom<=act.top,
     switchRight:sw.left>go.right&&Math.abs((sw.top+sw.bottom)/2-(go.top+go.bottom)/2)<12}; });
 ok('side by side, the bubble crosses into the text half, clear of the title and the buttons', sp1.crosses&&sp1.clearAbove&&sp1.clearBelow, sp1);
 ok('the switch sits at the right of the row with Begin', sp1.switchRight, sp1);
 await p.hover('#sp-modes .spinfo-b'); await wait(300);
 ok('hovering the i explains the other mode', await p.evaluate(()=>{ const t=document.querySelector('#sp-modes .sptip');
   return getComputedStyle(t).visibility==='visible'&&t.textContent.length>10; }));
 const fig0=await p.evaluate(()=>{ window.__fig=document.querySelector('#sp-patient svg'); return true; });
 await p.click('#sp-modes [data-mode]:not([aria-checked="true"])'); await wait(200);
 const sw=await p.evaluate(()=>({mode:MODE, def:PROTO.difficulty.default, same:document.querySelector('#sp-patient svg')===window.__fig,
   checked:[...document.querySelectorAll('#sp-modes [data-mode]')].filter(b=>b.getAttribute('aria-checked')==='true').map(b=>b.dataset.mode)}));
 ok('the switch changes the mode without redrawing the patient', fig0&&sw.mode!==sw.def&&sw.checked.join()===sw.mode&&sw.same, sw);
 await p.click('#sp-modes [data-mode="'+sw.def+'"]'); await wait(150);
 ok('a case with nothing saved offers Begin only', await p.evaluate(()=>document.getElementById('sp-run').hidden&&document.getElementById('beginbtn').textContent==='Begin'));

 // A run in a non-default mode, with a few acts, a tab change and a handoff being drafted.
 const alt=await p.evaluate(()=>{ const D=SHARED.difficulty; return Object.keys(D.modes).find(k=>k!==D.default); });
 await p.evaluate(m=>{ MODE=m; begin(); },alt); await wait(4200);           // past the nurse card
 const acts=await p.evaluate(()=>{
   const ids=Object.keys(ACT).filter(id=>ACT[id].tab==='stabilization'&&!(ACT[id].performs&&ACT[id].performs.length)).slice(0,3);
   ids.forEach(id=>log({actionId:id})); render();
   TAB='investigations'; renderTabs(); renderTab();
   PENDING_HANDOFF={disposition:'x_test_disposition',diagnoses:['x_test_dx']};
   return ids; });
 ok('the run took three acts', acts.length===3, acts);
 await wait(6000);
 let T=await table();
 ok('autosave: one run in progress, with the log', T.length===1&&T[0].status==='in_progress'&&T[0].case_prefix==='CHFE'&&T[0].state&&T[0].state.log.length>=3&&T[0].mode===alt, T.map(r=>[r.status,r.case_prefix,r.mode,r.state&&r.state.log.length]));
 ok('the run is saved under this build\'s version key', T[0]&&T[0].version_key===KEYS.CHFE, [T[0]&&T[0].version_key,KEYS.CHFE]);

 // Leave through the rail's Main menu.
 await p.evaluate(()=>askLeave('menu')); await wait(400);
 const leave=await p.evaluate(()=>({txt:document.getElementById('leavemsg').textContent, t:now(), log:JSON.stringify(LOG)}));
 ok('the leave dialog says the progress is saved', /progress is saved/.test(leave.txt), leave.txt);
 await p.click('#leaveok'); await wait(1500);
 ok('left to the case list', await p.evaluate(()=>!document.getElementById('picker').classList.contains('hidden')));
 T=await table();
 ok('the saved moment is the moment of leaving', T.length===1&&Math.abs(T[0].state.t-leave.t)<0.05&&JSON.stringify(T[0].state.log)===leave.log, T[0]&&[T[0].state.t,leave.t]);
 ok('the home panel replaces most of the picture', await p.evaluate(()=>document.getElementById('picker').classList.contains('home-on')&&!document.getElementById('wl-home').hidden));
 const home=await p.evaluate(()=>document.getElementById('wl-home').innerText);
 ok('Continue lists the run with its case time', /Continue/i.test(home)&&/Resume/.test(home), home.slice(0,300));
 ok('the run carries its case number', /Case \d+/.test(home), home.slice(0,200));
 ok('the case row says in progress', await p.evaluate(()=>/In progress/.test((document.querySelector('.wl-case[data-case="'+CASES.findIndex(c=>c.prefix==='CHFE')+'"]')||{}).innerText||'')));
 await p.screenshot({path:'/tmp/e2e/progress-home.png'});

 // Resume from the home panel: the same run, paused at the same moment.
 const fnBefore=(await ctl({})).calls.fn;
 await p.click('[data-hmresume="CHFE"]'); await wait(1500);
 const r1=await p.evaluate(pre=>{
   const fp=st=>JSON.stringify({phase:st.phase,seq:st.phaseSeq,flags:[...st.flags].sort(),taken:[...st.taken].sort(),
     sat:[...st.satisfied].sort(),nurse:st.nurse.map(n=>n.t+n.kind+n.text),vitals:st.vitals,pending:st.pending.length});
   return {paused:PAUSED&&!document.getElementById('pauseview').classList.contains('hidden'),
     msg:document.getElementById('pausemsg').innerText, t:now(), mode:MODE, tab:TAB, ho:PENDING_HANDOFF,
     sameLog:JSON.stringify(LOG)===pre, sameState:fp(ST)===fp(fold(JSON.parse(pre),now(),DM())),
     nintro:typeof NINTRO==='object'&&NINTRO.active(), splash:!document.getElementById('splash').classList.contains('hidden')};
 },leave.log);
 ok('resumed paused, with a resume message, no nurse card, splash closed', r1.paused&&/Resumed at/.test(r1.msg)&&!r1.nintro&&!r1.splash, r1);
 ok('resumed at the saved case time', Math.abs(r1.t-leave.t)<0.05, [r1.t,leave.t]);
 ok('the same log and the same state as when it was left', r1.sameLog&&r1.sameState, r1);
 ok('mode, tab and the drafted handoff come back', r1.mode===alt&&r1.tab==='investigations'&&r1.ho.disposition==='x_test_disposition'&&r1.ho.diagnoses[0]==='x_test_dx', r1);
 ok('resuming a case already loaded does not download it again', (await ctl({})).calls.fn===fnBefore);
 await wait(1500);
 ok('the clock does not move until play is pressed', Math.abs(await p.evaluate(()=>now())-leave.t)<0.05);
 await p.click('#resumebtn'); await wait(1500);
 ok('after play the clock runs on from there', await p.evaluate(t=>now()>t+1&&now()<t+3,leave.t));

 // Finish: the row becomes a score summary and its log is emptied.
 await p.evaluate(()=>{ log({actionId:'early_exit',kind:'early_exit'}); finish(); }); await wait(1500);
 T=await table();
 const f=T.find(r=>r.status==='finished');
 ok('finishing turns the run into a score summary', T.length===1&&f&&f.state===null&&f.outcome&&f.ended_by==='early_exit'&&f.summary&&Array.isArray(f.summary.rows)&&f.summary.rows.length>=5, T);
 ok('the summary is labels, percentages and counts only', f&&f.summary.rows.every(r=>Object.keys(r).sort().join()==='detail,id,label,pct'), f&&f.summary.rows[0]);
 const pct=await p.evaluate(()=>{ const o=overallScore(ST); return o.scored?o.pct:null; });
 ok('the stored score is the debrief\'s', f&&f.score_pct===pct, [f&&f.score_pct,pct]);
 await p.evaluate(()=>toPickerFromDebrief()); await wait(1200);
 const h2=await p.evaluate(()=>({home:document.getElementById('wl-home').innerText, hist:document.getElementById('db-history').innerText,
   ms:document.getElementById('db-ms').textContent,
   stats:document.getElementById('db-stats').innerText, statsShown:!document.getElementById('db-stats').hidden, top:document.getElementById('db-scroll').scrollTop}));
 ok('back on the dashboard, at the top, nothing in progress', /No case in progress/.test(h2.home)&&h2.top===0, h2);
 ok('a note says what the case changed', /First score on Case \d+|Finished Case \d+/.test(h2.home)&&/Milestone earned: First case/.test(h2.home), h2.home.slice(0,300));
 ok('the hero shows the learner\'s numbers', h2.statsShown&&/cases passed/i.test(h2.stats)&&/cases finished/i.test(h2.stats)&&/day streak/i.test(h2.stats), h2.stats);
 ok('History lists the attempt', /Ended early|Critical|critical|failed/i.test(h2.hist), h2.hist.slice(0,300));
 ok('milestones count what was earned', /1 of 9/.test(h2.ms), h2.ms.slice(0,200));
 // The milestones float (28 October 2026): hovering drops six medals down, Show all opens all nine.
 await p.hover('#db-ms .ms-badge'); await wait(500);
 ok('hovering the milestone badge drops down six medals', await p.evaluate(()=>{ const d=document.querySelector('#db-ms .ms-drop');
   return !!d&&getComputedStyle(d).visibility==='visible'&&document.querySelectorAll('#db-ms .ms-list .tr').length===6; }));
 await p.click('#db-ms [data-msopen]'); await wait(400);
 ok('Show all opens every milestone in a dialog, focus on its close button', await p.evaluate(()=>!document.getElementById('db-msmodal').hidden&&
   document.querySelectorAll('#db-msmodal .tr').length===9&&document.activeElement&&document.activeElement.classList.contains('ms-x')));
 await p.keyboard.press('ArrowDown'); await p.keyboard.press('Enter'); await wait(300);
 ok('keys under the dialog do not reach the case list', await p.evaluate(()=>!document.getElementById('picker').classList.contains('hidden')&&document.getElementById('splash').classList.contains('hidden')));
 await p.keyboard.press('Escape'); await wait(250);
 ok('Escape closes the milestones dialog', await p.evaluate(()=>document.getElementById('db-msmodal').hidden&&!document.getElementById('picker').classList.contains('hidden')));
 await p.mouse.move(20,820); await wait(500);
 ok('focus is back on the badge and the drop-down is shut', await p.evaluate(()=>document.activeElement&&document.activeElement.classList.contains('ms-badge')&&
   getComputedStyle(document.querySelector('#db-ms .ms-drop')).visibility==='hidden'));
 await p.mouse.move(20,820); await wait(500);
 ok('two Next up cards, two different cases', await p.evaluate(()=>{ const n=[...document.querySelectorAll('#wl-home .cx-next [data-hmopencase]')].map(b=>b.dataset.hmopencase);
   return n.length===2&&new Set(n).size===2; }));
 ok('case cards: no review dot, the age and sex under the silhouette', await p.evaluate(()=>{ const c=[...document.querySelectorAll('#pk-list .wl-case')];
   return c.length>0&&!document.querySelector('#pk-list .wl-state')&&c.every(x=>x.querySelector('.dc-who .wl-face + .dc-ag')); }));
 await p.click('#wl-menubtn'); await wait(150); await p.click('#wl-menu [data-credits]'); await wait(300);
 ok('the menu opens the credits over the case list, above the milestone badge', await p.evaluate(()=>{ const v=document.getElementById('creditsview');
   const b=document.querySelector('#db-ms .ms-badge'), r=b&&b.getBoundingClientRect();
   const top=r?document.elementFromPoint(r.left+r.width/2,r.top+r.height/2):null;
   return !v.hidden&&v.querySelectorAll('.crd-item').length>=8&&(!top||!!top.closest('#creditsview')); }));
 await p.keyboard.press('Escape'); await wait(150);
 ok('each category is its own coloured panel, with a heading', await p.evaluate(()=>{ const s=[...document.querySelectorAll('#pk-list .wl-sec')];
   return s.length>1&&s.every(x=>/\bcat-\d\b/.test(x.className)&&x.querySelector('h3.wl-group')&&getComputedStyle(x).getPropertyValue('--cat').trim()); }));
 await p.click('[data-fbclose]'); await wait(200);
 ok('the note can be dismissed', await p.evaluate(()=>!document.querySelector('.db-fb')));
 ok('the case card carries its tier', await p.evaluate(()=>{ const c=document.querySelector('.wl-case[data-case="'+CASES.findIndex(c=>c.prefix==='CHFE')+'"]'); return /t-(tried|passed|mastered)/.test(c.className)&&/Attempted|Passed|Mastered/.test(c.innerText); }));
 await p.click('[data-dbtab="history"]'); await wait(200);
 ok('the History tab opens and Cases closes', await p.evaluate(()=>!document.getElementById('db-history').hidden&&document.getElementById('db-cases').hidden&&document.querySelector('[data-dbtab="history"]').getAttribute('aria-selected')==='true'));
 ok('the case row shows the attempt', await p.evaluate(()=>/attempt/.test(document.querySelector('.wl-case[data-case="'+CASES.findIndex(c=>c.prefix==='CHFE')+'"]').innerText)));
 await p.click('[data-hmopen]'); await wait(200);
 ok('an attempt opens to its summary rows', await p.evaluate(()=>document.querySelectorAll('.hm-part').length>=5));
 await p.screenshot({path:'/tmp/e2e/progress-attempt.png'});
 await p.click('.hm-rx [data-hmdel]'); await wait(150);
 await p.click('[data-hmdelok]'); await wait(800);
 ok('delete removes the attempt', (await table()).length===0&&await p.evaluate(()=>!document.querySelector('.hm-row')));
 await p.click('[data-dbtab="cases"]'); await wait(200);

 // Start over: a saved run is discarded and a new one takes its place.
 await p.evaluate(i=>chooseCase(i),idx); await wait(400);
 await p.evaluate(()=>begin()); await wait(4000); await p.evaluate(()=>{ log({actionId:Object.keys(ACT).find(id=>ACT[id].tab==='stabilization')}); }); await wait(6000);
 const firstId=(await table())[0]&&(await table())[0].id;
 await p.evaluate(()=>askLeave('menu')); await wait(300); await p.click('#leaveok'); await wait(1500);
 await p.evaluate(i=>chooseCase(i),idx); await wait(500);
 const sp=await p.evaluate(()=>({run:!document.getElementById('sp-run').hidden, resume:(document.getElementById('sp-resume')||{}).textContent||'', begin:document.getElementById('beginbtn').textContent}));
 ok('the splash offers Resume and Start over', sp.run&&/Resume at \d+:\d\d/.test(sp.resume)&&sp.begin==='Start over', sp);
 await p.click('#beginbtn'); await wait(4000); await wait(6000);
 T=await table();
 ok('Start over discards the old run and saves the new one', T.length===1&&T[0].status==='in_progress'&&T[0].id!==firstId, T.map(r=>[r.id===firstId,r.status]));

 // A reload keeps the run, with no browser prompt.
 await p.evaluate(()=>{ log({actionId:Object.keys(ACT).filter(id=>ACT[id].tab==='stabilization')[1]}); }); await wait(300);
 const beforeReload=await p.evaluate(()=>({t:now(),n:LOG.length}));
 await p.reload(); await wait(2500);
 T=await table();
 ok('a reload asks nothing', dialogs.length===0, dialogs);
 ok('the run survives the reload, saved up to the moment of leaving', T.length===1&&T[0].status==='in_progress'&&T[0].state.log.length===beforeReload.n&&T[0].state.t>=beforeReload.t-0.5, T[0]&&[T[0].state.log.length,beforeReload.n,T[0].state.t,beforeReload.t]);
 ok('after the reload the home panel shows it', /Resume/.test(await p.evaluate(()=>document.getElementById('wl-home').innerText)));

 // The case has changed since: the notice, and the run is deleted.
 const stale=Object.assign({},T[0],{version_key:'f'.repeat(32)});
 await setTable([stale]); await p.evaluate(()=>PROGRESS.refresh()); await wait(600);
 ok('Continue warns that the case has changed', /improved since/.test(await p.evaluate(()=>document.getElementById('wl-home').innerText)));
 await p.click('[data-hmresume="CHFE"]'); await wait(3000); await shock();
 const imp=await p.evaluate(()=>({shown:!document.getElementById('improvedview').classList.contains('hidden'), title:document.getElementById('improvedtitle').innerText,
   splash:!document.getElementById('splash').classList.contains('hidden'), started:STARTED}));
 ok('the case-has-been-improved notice opens over the splash, nothing resumed', imp.shown&&/improved/.test(imp.title)&&imp.splash&&!imp.started, imp);
 await wait(500);
 ok('and the old run is deleted', (await table()).length===0);
 await p.click('#improvedok'); await wait(200);
 ok('OK closes it and the splash offers Begin', await p.evaluate(()=>document.getElementById('improvedview').classList.contains('hidden')&&document.getElementById('beginbtn').textContent==='Begin'&&document.getElementById('sp-run').hidden));

 // A save that fails does not stop the case, and the leave dialog does not promise anything.
 await p.evaluate(()=>begin()); await wait(4000);
 await ctl({runsFail:true}); await p.evaluate(()=>log({actionId:Object.keys(ACT).find(id=>ACT[id].tab==='stabilization')})); await wait(6000);
 await p.evaluate(()=>askLeave('menu')); await wait(400);
 const lt=await p.evaluate(()=>document.getElementById('leavemsg').textContent);
 ok('with saving failing, the leave dialog says progress will be lost', /lose progress/.test(lt), lt);
 await p.click('#leavecancel'); await ctl({runsFail:false}); await wait(6000);
 ok('saving recovers when the server does', (await table()).length===1);
 await p.evaluate(()=>askLeave('menu')); await wait(300); await p.click('#leaveok'); await wait(1500);

 // Several runs in progress (28 October 2026): one Continue card, the newest, and the rest
 // behind "+N more in progress" in a dialog with Resume and Discard for each.
 const T0=await table(), older=d=>new Date(Date.now()-d*3600e3).toISOString();
 const extra=(pre,h)=>Object.assign({},T0[0],{id:require('crypto').randomUUID(), case_prefix:pre, version_key:KEYS[pre],
   state:{v:1,t:100,log:[]}, sim_seconds:100, started_at:older(h), updated_at:older(h)});
 await setTable(T0.concat([extra('MGCA',2),extra('TSS',5)])); await p.evaluate(()=>PROGRESS.refresh()); await wait(700);
 const mr=await p.evaluate(()=>({go:[...document.querySelectorAll('#wl-home .cx-go')].map(c=>(c.querySelector('[data-hmresume]')||{}).dataset.hmresume),
   more:(document.querySelector('#wl-home [data-cxmore]')||{}).textContent||'', cards:document.querySelectorAll('#wl-home .cx').length,
   filled:document.querySelectorAll('#wl-home [data-hmresume]:not(.ghost)').length}));
 ok('three runs in progress: one Continue card, the newest, and +2 more', mr.go.length===1&&mr.go[0]==='CHFE'&&/\+2 more in progress/.test(mr.more)&&mr.cards===3&&mr.filled===1, mr);
 await p.click('[data-cxmore]'); await wait(400);
 const rp=await p.evaluate(()=>({open:!document.getElementById('db-msmodal').hidden, rows:[...document.querySelectorAll('#db-msmodal .rp-row [data-hmresume]')].map(b=>b.dataset.hmresume),
   focus:document.activeElement&&document.activeElement.classList.contains('ms-x')}));
 ok('the dialog lists the other two, newest first, focus on its close button', rp.open&&rp.rows.join()==='MGCA,TSS'&&rp.focus, rp);
 for(let k=0;k<6;k++) await p.keyboard.press('Tab');
 ok('Tab stays inside the dialog', await p.evaluate(()=>!!document.activeElement.closest('#db-msmodal')));
 await p.click('#db-msmodal [data-hmdel]'); await wait(200); await p.click('#db-msmodal [data-hmdelok]'); await wait(700);
 const after=await p.evaluate(()=>({rows:document.querySelectorAll('#db-msmodal .rp-row').length, more:(document.querySelector('#wl-home [data-cxmore]')||{}).textContent||''}));
 ok('Discard in the dialog removes that run and the count follows', after.rows===1&&/\+1 more/.test(after.more)&&(await table()).filter(r=>r.status==='in_progress').length===2, after);
 await p.keyboard.press('Escape'); await wait(250);
 ok('Escape closes it, focus back on +1 more', await p.evaluate(()=>document.getElementById('db-msmodal').hidden&&document.activeElement&&document.activeElement.dataset.cxmore==='1'));
 await setTable(T0); await p.evaluate(()=>PROGRESS.refresh()); await wait(600);
 ok('one run in progress: no "more" control', await p.evaluate(()=>!document.querySelector('#wl-home [data-cxmore]')&&document.querySelectorAll('#wl-home .cx-go').length===1));

 // Phone width: the home panel and the list both fit, no sideways scroll.
 await p.setViewportSize({width:390,height:844}); await wait(400);
 const narrow=await p.evaluate(()=>({sw:document.documentElement.scrollWidth, home:document.getElementById('wl-home').getBoundingClientRect().height}));
 ok('phone width: no sideways scroll, the panel has room', narrow.sw<=390&&narrow.home>120, narrow);
 await p.screenshot({path:'/tmp/e2e/progress-phone.png'});
 await p.setViewportSize({width:1440,height:860});

 // Day and night (28 October 2026): the board's switch flips the theme and is remembered.
 const th0=await p.evaluate(()=>document.documentElement.dataset.theme);
 await p.click('.db-top [data-themetoggle]'); await wait(300);
 const th1=await p.evaluate(()=>({t:document.documentElement.dataset.theme, s:localStorage.getItem('emsim.theme')}));
 ok('the day and night switch flips the theme and remembers it', th1.t!==th0&&th1.s===th1.t&&['day','night'].includes(th1.t), [th0,th1]);
 await p.click('.db-top [data-themetoggle]'); await wait(300);
 ok('no page errors', errs.length===0, errs);
 ok('no CSP violations', csp.length===0, csp);

 // The site with no Supabase settings: nothing of this appears.
 const q=await ctx.newPage(); const errs0=[]; q.on('pageerror',e=>errs0.push(e.message));
 await q.goto('http://localhost:8090/'); await q.waitForTimeout(1000);
 ok('unconfigured site: no home panel, no progress calls', await q.evaluate(()=>document.getElementById('wl-home').hidden&&!PROGRESS.enabled())&&errs0.length===0, errs0);
 await b.close();
})();
