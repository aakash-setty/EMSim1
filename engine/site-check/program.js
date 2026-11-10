// Programs and analytics (10 November 2026), end to end against the mock: joining with a code,
// the run record that a finished case sends, no delete for a member, the analytics view for a
// program admin and for staff, and the link that carries a code.
//
// The case pack is served to the page by this script from private-packs/, so the check does
// not need the edge function. PACKS_DIR says where the packs are (default private-packs).
const {chromium}=require('playwright');
const fs=require('fs'), path=require('path');
const M='http://localhost:54321', SITE=process.env.SITE_URL||'http://localhost:8080/';
const PACKS=process.env.PACKS_DIR||'private-packs';
const pg=b=>fetch(M+'/__pg',b?{method:'POST',body:JSON.stringify(b)}:undefined).then(r=>r.json());
const ctl=b=>fetch(M+'/__ctl',{method:'POST',body:JSON.stringify(b)}).then(r=>r.json());
const setRuns=rows=>fetch(M+'/__runs',{method:'POST',body:JSON.stringify({rows})}).then(r=>r.json());
(async()=>{
 const b=await chromium.launch({executablePath:process.env.CHROME||undefined});
 const ctx=await b.newContext({viewport:{width:1440,height:900}});
 const p=await ctx.newPage(); const errs=[], csp=[];
 let fails=0;
 p.on('pageerror',e=>errs.push('pageerror: '+e.message));
 p.on('dialog',d=>d.accept().catch(()=>{}));
 p.on('console',m=>{ const t=m.text(); if(/Content Security Policy|Refused to/.test(t)) csp.push(t.slice(0,200)); else if(m.type()==='error' && !/ERR_TUNNEL|status of (400|401|403|404|406|409|429|500)/.test(t)) errs.push('console: '+t.slice(0,200)); });
 await ctx.route('**/functions/v1/case-pack',async route=>{
   let prefix=''; try{ prefix=JSON.parse(route.request().postData()||'{}').prefix||''; }catch(e){}
   const f=path.join(PACKS,prefix+'.json');
   if(!/^[A-Z][A-Z0-9]{1,15}$/.test(prefix)||!fs.existsSync(f)) return route.fulfill({status:404,contentType:'application/json',body:'{"error":"not_found"}'});
   route.fulfill({status:200,contentType:'application/json',body:fs.readFileSync(f)});
 });
 const ok=(n,c,x)=>{ if(!c) fails++; console.log((c?'ok   ':'FAIL ')+'program: '+n+(c||x===undefined?'':'  -> '+JSON.stringify(x).slice(0,500))); };
 const wait=ms=>p.waitForTimeout(ms);
 const txt=sel=>p.evaluate(s=>{ const e=document.querySelector(s); return e?e.innerText:null; },sel);
 const shock=async()=>{ for(let k=0;k<20;k++){ if(await p.evaluate(()=>{ const d=document.getElementById('chargedeliver'); return !!d&&!d.disabled&&!document.getElementById('chargeview').classList.contains('hidden'); })){ await p.click('#chargedeliver'); await wait(600); return; } await wait(250); } };
 const signIn=async()=>{ await p.click('#acct-in'); await wait(300);
   await p.fill('#signinemail','res@example.com'); await p.fill('#signinpass','right-password'); await p.keyboard.press('Enter'); await wait(1800); };

 await ctl({rpc:'ok',tamper:false,userOk:true,unconfirmed:false,storeOnly:false,runsFail:false}); await setRuns([]); await pg({reset:true});

 await p.goto(SITE); await wait(1200);
 await p.evaluate(()=>{ if(typeof LANDING==='object'&&LANDING&&LANDING.hide) LANDING.hide(); });
 ok('signed out: nothing about programs in the account line', await p.evaluate(()=>!document.getElementById('acct-prog')&&!document.getElementById('pg-open')));
 await signIn();
 ok('signed in, no program: Join a program is offered and Analytics is not',
    await p.evaluate(()=>!!document.getElementById('pg-join')&&!document.getElementById('pg-open')), await txt('#wl-acct'));

 // ---- joining
 await p.click('#pg-join'); await wait(200);
 ok('the join dialog says what the program will see', /see which cases you finish/.test(await txt('#pgjoin')||''));
 await p.fill('#pgj-code','WRONGCDE'); await p.fill('#pgj-name','Riley Test'); await p.click('#pgj-ok'); await wait(700);
 ok('a wrong code says so and stays open', /not one we know/.test(await txt('#pgj-err')||'')&&await p.evaluate(()=>!document.getElementById('pgjoin').classList.contains('hidden')), await txt('#pgj-err'));
 await p.fill('#pgj-code','mckc-de23'); await p.selectOption('#pgj-year','2'); await p.click('#pgj-ok'); await wait(1000);
 let st=await pg();
 ok('the right code joins, with the name and the year', st.member&&st.member.display_name==='Riley Test'&&st.member.pgy===2, st.member);
 ok('the account line shows the program, and a resident gets no Analytics button',
    /Mock EM/.test(await txt('#acct-prog')||'')&&await p.evaluate(()=>!document.getElementById('pg-open')&&!document.getElementById('pg-join')), await txt('#acct-prog'));
 ok('a resident cannot open the view from the console either', await p.evaluate(()=>{ const v=document.getElementById('pgview'); return v.classList.contains('hidden'); }));

 // ---- a finished case sends its record
 const idx=await p.evaluate(()=>CASES.findIndex(c=>c.prefix==='CHFE'));
 await p.evaluate(i=>ACCESS_UI.open(i),idx); await wait(2500); await shock();
 ok('the case opens', await p.evaluate(()=>typeof PACK==='object'&&PACK&&PACK.prefix==='CHFE'));
 await p.click('#beginbtn'); await wait(1200);
 await p.evaluate(()=>{ const first=Object.keys(ACT).find(id=>ACT[id].tab==='exam'); log({actionId:first});
   log({actionId:null,kind:'interview',topic:'x_topic',q:'a typed question that must not be kept',score:1,matcher:'m'});
   log({actionId:'early_exit',kind:'early_exit'}); finish(); });
 await wait(2500);
 st=await pg();
 const rec=st.records[0];
 ok('one record arrived for the finished run', st.records.length===1&&rec&&rec.case_prefix==='CHFE', st.records.length);
 ok('it is not met, with reasons', rec&&rec.result==='not_met'&&rec.why.length>0, rec&&[rec.result,rec.why]);
 ok('it holds graded items: critical actions, a diagnosis and a disposition',
    rec&&rec.items.some(i=>i.k==='critical')&&rec.items.filter(i=>i.k==='diagnosis').length===1&&rec.items.filter(i=>i.k==='disposition').length===1);
 ok('it carries the program and the year', rec&&rec.program_id===st.member.program_id&&rec.pgy===2);
 ok('the trail has ids and times and nothing typed', rec&&Array.isArray(rec.trail)&&rec.trail.length===3&&!JSON.stringify(rec.trail).includes('typed question')&&rec.trail.every(e=>typeof e.t==='number'), rec&&rec.trail);
 ok('no item carries a label', rec&&rec.items.every(i=>!('label' in i)&&!('name' in i)));

 // ---- a member cannot delete a finished attempt
 await p.evaluate(()=>{ if(typeof backToPicker==='function') backToPicker(); }); await wait(1500);
 const del=await p.evaluate(()=>{
   const tab=[...document.querySelectorAll('[data-dbtab]')].find(x=>/attempt|history/i.test(x.textContent)); if(tab) tab.click();
   const row=document.querySelector('[data-hmopen]'); if(row) row.click();
   return {row:!!row, del:!!document.querySelector('.hm-rx [data-hmdel]'), says:/cannot be deleted while you are in a program/.test(document.body.innerText)}; });
 ok('a finished attempt has no Delete for a program member', del.row&&!del.del&&del.says, del);

 // ---- a program admin
 await pg({member:Object.assign({},st.member,{role:'admin',join_code:'MCKCDE23'})});
 await p.reload(); await wait(1800);
 ok('an admin gets the Analytics button', await p.evaluate(()=>!!document.getElementById('pg-open')));
 await p.click('#pg-open'); await wait(1000);
 ok('the view opens on Overview with the program name', await p.evaluate(()=>!document.getElementById('pgview').classList.contains('hidden'))&&/Mock EM/.test(await txt('.pg-bar')||''), await txt('.pg-bar'));
 ok('an admin has no Programs tab and no program picker', await p.evaluate(()=>!document.querySelector('[data-pgtab="programs"]')&&!document.getElementById('pg-scope')));
 ok('the overview counts the run', /Finished runs/.test(await txt('.pg-tiles')||'')&&/First attempts/.test(await txt('.pg-pane')||''), await txt('.pg-tiles'));
 await p.click('[data-pgtab="people"]'); await wait(200);
 ok('Residents lists the member by name with what they finished, and the join code', /Riley Test/.test(await txt('.pg-pane')||'')&&/MCKCDE23/.test(await txt('.pg-pane')||''), (await txt('.pg-pane')||'').slice(0,300));
 await p.click('[data-pgtab="cases"]'); await wait(200);
 await p.click('[data-pgcase="CHFE"]'); await wait(200);
 ok('Cases opens a case to its actions, by display name', await p.evaluate(()=>document.querySelectorAll('.pg-detail table').length>=1&&!/_/.test(document.querySelector('.pg-detail tbody td').textContent)), (await txt('.pg-detail')||'').slice(0,200));
 await p.click('[data-pgtab="missed"]'); await wait(200);
 ok('Missed and unsafe lists a missed critical action', /Critical actions missed/.test(await txt('.pg-pane')||'')&&await p.evaluate(()=>document.querySelectorAll('.pg-pane table tbody tr').length>=1));
 await p.click('[data-pgtab="map"]'); await wait(200);
 ok('the gap map draws a topic row, and a small cell shows a count and no percentage',
    await p.evaluate(()=>document.querySelectorAll('.pg-map tbody tr').length>=1&&document.querySelectorAll('.pg-cell.few').length>=1&&!document.querySelector('.pg-cell.few b')));
 ok('the footer says what the numbers are', /simulated cases/.test(await txt('.pg-foot')||'')&&/not checked by the server/.test(await txt('.pg-foot')||''));
 await p.uncheck('#pg-first'); await wait(800);
 ok('First attempts only can be turned off', await p.evaluate(()=>PROGRAM._state().view.first===false&&PROGRAM._state().view.state==='ready'));
 await p.keyboard.press('Escape'); await wait(200);
 ok('Escape closes the view', await p.evaluate(()=>document.getElementById('pgview').classList.contains('hidden')));

 // ---- results by name switched off
 st=await pg();
 st.programs[0].show_named_results=false; await pg({programs:st.programs});
 await p.click('#pg-open'); await wait(900); await p.click('[data-pgtab="people"]'); await wait(200);
 ok('with the switch off the list still names who finished what and says results by name are off',
    /Riley Test/.test(await txt('.pg-pane')||'')&&/Results by name are off/.test(await txt('.pg-pane')||'')&&await p.evaluate(()=>!document.querySelector('.pg-pane .pg-mix:not(.k)')));
 await p.keyboard.press('Escape');
 st.programs[0].show_named_results=true; await pg({programs:st.programs});

 // ---- staff
 await pg({staff:true});
 await p.reload(); await wait(1800);
 await p.click('#pg-open'); await wait(1000);
 ok('staff get a picker of whose data, starting at every account, and a Programs tab',
    await p.evaluate(()=>{ const s=document.getElementById('pg-scope'); return !!s&&s.value==='all'&&s.options.length===2&&!!document.querySelector('[data-pgtab="programs"]'); }));
 await p.click('[data-pgtab="programs"]'); await wait(200);
 ok('Programs lists the program with its code and switches', /Mock EM/.test(await txt('.pg-pane')||'')&&/MCKCDE23/.test(await txt('.pg-pane')||'')&&await p.evaluate(()=>!!document.querySelector('[data-pgnamed]')&&!!document.getElementById('pg-enforce')));
 await p.fill('#pg-newname','Second Program'); await p.fill('#pg-newseats','12'); await p.click('#pg-new button[type=submit]'); await wait(1000);
 st=await pg();
 const made=st.calls.find(c=>c.fn==='staff_save_program'&&c.args.p_id===null);
 ok('creating a program sends its name and seats', made&&made.args.p_name==='Second Program'&&made.args.p_seats===12, made);
 ok('and the new program appears', /Second Program/.test(await txt('.pg-pane')||''));
 await p.click('[data-pgnamed="aaaaaaaa-0000-0000-0000-000000000001"]'); await wait(900);
 st=await pg();
 ok('the results-by-name switch is saved for that program', st.programs[0].show_named_results===false&&/group only/.test(await txt('.pg-msg')||''), await txt('.pg-msg'));
 await p.selectOption('#pg-scope','aaaaaaaa-0000-0000-0000-000000000001'); await wait(900);
 ok('staff can open one program', await p.evaluate(()=>PROGRAM._state().view.scope==='aaaaaaaa-0000-0000-0000-000000000001'&&PROGRAM._state().view.state==='ready'));
 await p.click('#pg-close'); await wait(200);

 // ---- a failure is said, not hidden
 await pg({fail:true});
 await p.click('#pg-open'); await wait(900);
 ok('when the numbers cannot be loaded the view says so', /could not be loaded/.test(await txt('.pg-pane')||''), await txt('.pg-pane'));
 await p.click('#pg-close'); await pg({fail:false});

 // ---- signing out clears it, and a link carries a code
 await p.click('#acct-out'); await wait(800);
 ok('signed out: the program buttons are gone', await p.evaluate(()=>!document.getElementById('pg-open')&&!document.getElementById('pg-join')));
 await pg({reset:true}); await setRuns([]);
 await p.goto(SITE+'?join=mckcde23'); await wait(1200);
 await p.evaluate(()=>{ if(typeof LANDING==='object'&&LANDING&&LANDING.hide) LANDING.hide(); });
 ok('the code is taken off the address', await p.evaluate(()=>!/join=/.test(location.search)));
 await signIn(); await wait(600);
 ok('after signing in from a join link the dialog opens with the code filled in',
    await p.evaluate(()=>!document.getElementById('pgjoin').classList.contains('hidden')&&document.getElementById('pgj-code').value==='MCKCDE23'));
 await p.click('#pgj-no'); await wait(200);
 ok('Not now closes it and forgets the code', await p.evaluate(()=>document.getElementById('pgjoin').classList.contains('hidden')&&!sessionStorage.getItem('emsim-join-code')));

 ok('no page errors', errs.length===0, errs);
 ok('no Content Security Policy refusals', csp.length===0, csp);
 await b.close();
 process.exit(fails?1:0);
})().catch(e=>{ console.log('FAIL program: the check itself threw  -> '+(e&&e.stack||e)); process.exit(1); });
