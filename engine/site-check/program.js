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
 ok('an admin has no Test data button', await p.evaluate(()=>!document.querySelector('[data-pgtest]')));
 ok('an admin has no Programs tab and no program picker', await p.evaluate(()=>!document.querySelector('[data-pgtab="programs"]')&&!document.getElementById('pg-scope')));
 ok('the overview counts the run', /Finished runs/.test(await txt('.pg-tiles')||'')&&/First attempts/.test(await txt('.pg-pane')||''), await txt('.pg-tiles'));
 await p.click('[data-pgtab="people"]'); await wait(200);
 ok('Residents lists the member by name with what they finished, and the join code', /Riley Test/.test(await txt('.pg-pane')||'')&&/MCKCDE23/.test(await txt('.pg-pane')||''), (await txt('.pg-pane')||'').slice(0,300));
 await p.click('[data-pgtab="cases"]'); await wait(200);
 await p.click('[data-pgcase="CHFE"]'); await wait(200);
 ok('Cases opens a case to its actions, by display name', await p.evaluate(()=>document.querySelectorAll('.pg-detail table').length>=1&&!/_/.test(document.querySelector('.pg-detail tbody td').textContent)), (await txt('.pg-detail')||'').slice(0,200));
 await p.click('[data-pgtab="missed"]'); await wait(200);
 ok('Missed and unsafe lists a missed critical action', /critical actions missed/i.test(await txt('.pg-pane')||'')&&await p.evaluate(()=>document.querySelectorAll('.pg-pane table tbody tr').length>=1));
 await p.click('[data-pgtab="prio"]'); await wait(200);
 ok('Teaching priorities, with one run: no skill area is rated, and each is listed as too few to rate',
    await p.evaluate(()=>document.querySelectorAll('.pg-pr').length===0)&&/too few chances to rate/i.test(await txt('.pg-pane')||''), (await txt('.pg-pane')||'').slice(0,300));
 ok('there is no gap map any more', await p.evaluate(()=>!document.querySelector('[data-pgtab="map"]')&&!document.querySelector('.pg-map')));
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
    await p.evaluate(()=>{ const s=document.getElementById('pg-scope'); return !!s&&s.value==='all'&&s.options.length===3&&!!document.querySelector('[data-pgtab="programs"]'); }));
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
 // ---- test data (10 November 2026): made up in the browser, staff only
 const before=(await pg()).calls.length;
 await p.click('.pg-testtab'); await wait(500);
 ok('Test data opens with a notice that nothing is real', await p.evaluate(()=>PROGRAM._state().view.test&&PROGRAM._state().view.tab==='overview')&&/made up in this browser/.test(await txt('.pg-testbar')||''), await txt('.pg-testbar'));
 ok('in test data there is no Programs tab', await p.evaluate(()=>!document.querySelector('[data-pgtab="programs"]')));
 const sizes=await p.evaluate(()=>PROGRAM._test());
 ok('the made-up program has 38 people and several hundred runs', sizes.people===38&&sizes.records>250, sizes);
 ok('the overview shows 36 residents', /36/.test(await p.evaluate(()=>document.querySelector('.pg-tile b').textContent)));
 await p.click('[data-pgtab="people"]'); await wait(200);
 ok('Residents lists all 38 with results by name and no Remove', await p.evaluate(()=>document.querySelectorAll('.pg-pane tbody tr').length===38&&document.querySelectorAll('.pg-pane tbody .pg-mix').length>=30&&!document.querySelector('[data-pgask]')&&!document.querySelector('[data-pgrole]')));
 await p.uncheck('#pg-testnamed'); await wait(400);
 ok('Results by name off: names and completion stay, results by name go', await p.evaluate(()=>document.querySelectorAll('.pg-pane tbody tr').length===38&&!document.querySelector('.pg-pane tbody .pg-mix'))&&/Results by name are off/.test(await txt('.pg-pane')||''));
 await p.check('#pg-testnamed'); await wait(300);
 await p.click('[data-pgtab="cases"]'); await wait(200);
 const nCases=await p.evaluate(()=>CASES.length);
 ok('Cases lists every case in the library', await p.evaluate(n=>document.querySelectorAll('.pg-pane tr.pg-row').length===n,nCases));
 await p.click('.pg-pane tr.pg-row [data-pgcase]'); await wait(200);
 ok('a case opens to nine critical actions with catalog names and a median time', await p.evaluate(()=>{ const rows=[...document.querySelectorAll('.pg-detail table')[0].querySelectorAll('tbody tr')];
   return rows.filter(r=>r.children[1].textContent==='critical').length===9&&rows.some(r=>/^\d+:\d\d$/.test(r.children[4].textContent)); }));
 await p.click('[data-pgtab="missed"]'); await wait(200);
 ok('Missed and unsafe has rows in all four lists', await p.evaluate(()=>[...document.querySelectorAll('.pg-pane table')].length===4&&[...document.querySelectorAll('.pg-pane table')].every(t=>t.querySelectorAll('tbody tr').length>0)));
 await p.click('[data-pgtab="prio"]'); await wait(200);
 const pr=await p.evaluate(()=>{ const rows=[...document.querySelectorAll('.pg-pr')];
   const share=r=>parseInt(r.querySelector('.pg-prv b').textContent,10), lost=r=>parseInt(r.querySelector('.pg-prv .pg-n').textContent,10);
   return {n:rows.length, shares:rows.map(share), lost:rows.map(lost), lead:document.querySelector('.pg-lead').innerText, first:rows[0].querySelector('.pg-prn').textContent,
     who:rows[0].querySelector('.pg-prw').textContent, bars:rows.every(r=>r.querySelectorAll('.pg-prbar i').length>=1)}; });
 ok('Teaching priorities ranks skill areas by the number of chances lost', pr.n>=6&&pr.lost.every((v,i)=>i===0||v<=pr.lost[i-1])&&pr.bars, pr.lost);
 ok('the lead sentence names the first skill area', pr.lead.includes(pr.first), pr.lead);
 ok('each row says how many learners and cases it rests on', /\d+ of \d+ learners, \d+ cases?/.test(pr.who), pr.who);
 await p.click('[data-pgsort="rate"]'); await wait(200);
 ok('it can be ordered by the share lost instead', await p.evaluate(()=>{ const v=[...document.querySelectorAll('.pg-pr')].map(r=>{ const m=r.querySelector('.pg-prv .pg-n').textContent.match(/(\d+) of (\d+)/); return +m[1]/+m[2]; });
   return v.every((x,i)=>i===0||x<=v[i-1]+1e-9)&&document.querySelector('[data-pgsort="rate"]').getAttribute('aria-pressed')==='true'; }));
 await p.click('[data-pgsort="count"]'); await wait(200);
 await p.click('.pg-pr [data-pgskill]'); await wait(200);
 ok('a skill area opens to its actions, by case', await p.evaluate(()=>{ const d=document.querySelector('.pg-prs .pg-detail'); return !!d&&d.querySelectorAll('tbody tr').length>=1&&d.querySelectorAll('thead th').length===5; }));
 await p.click('.pg-pr.on [data-pgskill]'); await wait(200);
 const dr=await p.evaluate(()=>{ const rows=[...document.querySelectorAll('.pg-dr')];
   return {n:rows.length, dots:rows.map(r=>[...r.querySelectorAll('.dot')].map(d=>d.textContent).join('')), verdicts:rows.map(r=>r.querySelector('.pg-verdict').textContent),
     kinds:[...new Set(rows.map(r=>r.querySelector('.pg-verdict').className.replace('pg-verdict ','')))], inside:rows.every(r=>[...r.querySelectorAll('.dot')].every(d=>{ const l=parseFloat(d.style.left); return l>=0&&l<=100; }))}; });
 ok('Does it close with training: one row per rated skill area, a numbered dot per year, inside the axis', dr.n===pr.n&&dr.dots.filter(x=>x==='123').length>=4&&dr.inside, dr.dots);
 ok('each row carries a verdict in words, and more than one kind of verdict appears', dr.verdicts.every(v=>v.length>10)&&dr.kinds.length>=2, dr.kinds);
 ok('the thresholds are said to be choices, not a standard', /not a standard/.test(await txt('.pg-pane')||''));
 await p.click('[data-pgtab="overview"]'); await wait(200);
 const ch=await p.evaluate(()=>{ const s=[...document.querySelectorAll('.pg-two > section')].map(e=>e.getBoundingClientRect());
   return {n:s.length, sameTop:s.length===2&&Math.abs(s[0].top-s[1].top)<2, leftOf:s.length===2&&s[0].right<=s[1].left,
     years:document.querySelectorAll('.pg-ych .pg-yrow').length, months:document.querySelectorAll('.pg-mch .pg-mcol').length,
     segs:[...document.querySelectorAll('.pg-ych .pg-stack i')].every(i=>/of \d+ \(\d+%\)/.test(i.title)),
     tables:document.querySelectorAll('.pg-two details table').length, open:document.querySelectorAll('.pg-two details[open]').length}; });
 ok('by year and by month are two charts side by side', ch.n===2&&ch.sameTop&&ch.leftOf, ch);
 ok('three year bars and a column per month, each segment saying its count and share', ch.years===3&&ch.months>=6&&ch.segs, ch);
 ok('each chart keeps its table, closed until asked for', ch.tables===2&&ch.open===0, ch);
 const runsFirst=await p.evaluate(()=>document.querySelectorAll('.pg-tile b')[4].textContent);
 ok('by year: PGY-1 does worse than PGY-3 on first attempts', await p.evaluate(()=>{ const rows=[...document.querySelectorAll('.pg-ych .pg-yrow')];
   const share=r=>{ const a=r.querySelector('.pg-stack i.a'); const m=a&&a.title.match(/\((\d+)%\)/); return m?+m[1]:0; };
   return rows.length===3&&/PGY-1/.test(rows[0].textContent)&&/PGY-3/.test(rows[2].textContent)&&share(rows[0])<share(rows[2]); }));
 await p.selectOption('#pg-days','30'); await wait(400);
 ok('the period narrows the made-up runs', Number(await p.evaluate(()=>document.querySelectorAll('.pg-tile b')[4].textContent))<Number(runsFirst), runsFirst);
 await p.selectOption('#pg-days',''); await wait(300);
 ok('test data sent nothing to the database', (await pg()).calls.length===before);
 await p.click('.pg-testbar [data-pgtest]'); await wait(900);
 ok('Back to real data returns to the real program', await p.evaluate(()=>!PROGRAM._state().view.test&&PROGRAM._state().view.scope==='aaaaaaaa-0000-0000-0000-000000000001'&&!document.querySelector('.pg-testbar')));
 await p.selectOption('#pg-scope','test'); await wait(500);
 ok('the picker also reaches test data', await p.evaluate(()=>PROGRAM._state().view.test));
 await p.selectOption('#pg-scope','all'); await wait(900);
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
