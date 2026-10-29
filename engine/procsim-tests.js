#!/usr/bin/env node
/* Tests for the procedure engine (engine/procsim-geom.js, engine/procsim-core.js) against
   every pack in procedures/. Run: node engine/procsim-tests.js

   The geometry is checked where the steps depend on it: the target zone sits over the air
   layer with no resistant layer in between, and the step's air layer has a back wall. The
   rules are checked by playing the intended path in both modes and both hands, then the
   errors one at a time. No browser: three.js is used for its math and raycaster only. */
'use strict';
const fs=require('fs'), path=require('path'), vm=require('vm');
const ROOT=path.join(__dirname,'..');
vm.runInThisContext(fs.readFileSync(path.join(ROOT,'engine/vendor/three/three.min.js'),'utf8'));
const load=f=>vm.runInThisContext(fs.readFileSync(path.join(ROOT,'engine',f),'utf8').replace(/^const (PX[A-Z]+)/m,'globalThis.$1'));
load('procsim-geom.js'); load('procsim-core.js');

let pass=0, fail=0;
const chk=(name, ok, extra)=>{ if(ok) pass++; else { fail++; console.log('FAIL', name, extra===undefined?'':extra); } };
const section=n=>console.log('--', n);

const dir=path.join(ROOT,'procedures');
const packs=fs.existsSync(dir)?fs.readdirSync(dir).filter(d=>fs.existsSync(path.join(dir,d,d+'-procedure.json'))):[];
if(!packs.length){ console.log('no procedure packs'); process.exit(1); }

for(const P of packs){
  const pack=JSON.parse(fs.readFileSync(path.join(dir,P,P+'-procedure.json'),'utf8'));
  const G=PXGEOM.build(pack);
  const air=pack.layers.find(l=>l.air).id;
  const stab=pack.steps.find(s=>s.type==='stab');
  const zone=pack.zones.find(z=>z.id===stab.target);
  const cx=(zone.x[0]+zone.x[1])/2, cz=(zone.z[0]+zone.z[1])/2;

  section(P+': geometry');
  const col=G.column(cx,cz);
  chk('the skin is the top of the target column', col.intervals[0]&&col.intervals[0].layer===G.skinId, JSON.stringify(col.intervals[0]));
  const ai=G.interval(col, air);
  chk('the air layer is under the target', !!ai);
  const above=col.intervals.filter(v=>ai&&v.top>ai.top);
  const resistAbove=above.filter(v=>(G.layers.find(l=>l.id===v.layer)||{}).resist);
  chk('nothing resistant lies over the air at the target', resistAbove.length===0, resistAbove.map(v=>v.layer).join());
  chk('something lies behind the air at the target', col.intervals.some(v=>ai&&v.top<=ai.bottom+0.01));
  for(const [dx,dz] of [[zone.x[0]+0.2,zone.z[0]+0.2],[zone.x[1]-0.2,zone.z[1]-0.2],[zone.x[0]+0.2,zone.z[1]-0.2],[zone.x[1]-0.2,zone.z[0]+0.2]]){
    const c=G.column(dx,dz), a=G.interval(c,air);
    chk('the zone corner '+dx.toFixed(1)+','+dz.toFixed(1)+' is over air with nothing resistant above',
        !!a && !c.intervals.some(v=>v.top>a.top && (G.layers.find(l=>l.id===v.layer)||{}).resist));
  }
  for(const z of pack.zones) chk('zone '+z.id+' has feel and wrong text', !!z.feel&&!!z.wrong);
  const ids=new Set(G.layers.map(l=>l.id));
  for(const k in (pack.feel||{})) chk('feel names a layer: '+k, ids.has(k));

  /* The intended path, as the view would drive it. */
  function play(mode, hand, opts){
    opts=opts||{};
    let t=0; const now=()=>t;
    const sim=PXCORE.create(pack, G, {mode, hand, now});
    const out=[];
    const side=pack.steps.find(s=>s.type==='choice').correct_by_hand[hand];
    const cwFeet = side==='left';           /* clockwise takes +x to the feet */
    for(let guard=0; guard<200 && !sim.state.finished; guard++){
      const s=sim.current(); t+=2000;
      let r;
      if(s.type==='action') r=sim.action(s.id);
      else if(s.type==='choice') r=sim.choose(side);
      else if(s.type==='palpate') r=sim.palpate(cx,cz);
      else if(s.type==='stab'){
        r=sim.placeBlade(cx,cz,s.edge);
        for(let k=0;k<200&&!(r&&r.advanced);k++){ sim.pushBlade(0.5); r=sim.releaseBlade(); }
      }
      else if(s.type==='rotate') r=sim.rotateBlade(cwFeet?'cw':'ccw');
      else if(s.type==='insert'){ for(let k=0;k<400&&!(r&&r.advanced);k++) r=sim.pushRod(0.5); }
      else if(s.type==='turn') r=sim.turnRod(cwFeet?'ccw':'cw');
      else if(s.type==='advance'){ while(sim.state.rod.depth<(s.range_mm[0]+s.range_mm[1])/2) sim.pushRod(1); r=sim.rodDone(); }
      else if(s.type==='railroad'){ while(!sim.cuffIn()||sim.state.tube.depth<s.depth_mm[0]+2) sim.pushTube(1,true); r=sim.tubeDone(); }
      else if(s.type==='inflate'){ while(sim.state.cuff_ml<(s.range_ml[0]+s.range_ml[1])/2) sim.inflate(0.5); r=sim.inflateDone(); }
      else if(s.type==='confirm') r=sim.confirm();
      out.push([s.id, r&&r.kind, r&&r.text]);
      if(!r||!r.advanced){ return {sim, out, stuck:s.id, r}; }
    }
    return {sim, out};
  }
  section(P+': the turned rod stays in the tract and the airway');
  {
    const rod=pack.tools.find(t=>t.kind==='rod')||{};
    const path=G.rodPath(cx, cz, {air, tract_deg:rod.tract_deg, bend_mm:rod.bend_mm, straight_mm:rod.straight_mm});
    chk('there is a path', !!path && path.pts.length>100);
    const allowed=new Set(col.intervals.filter(v=>ai && v.top>=ai.top-0.01).map(v=>v.layer));
    const bad=[];
    for(const p of path.pts){
      if(p.s>path.airEntry+120) break;
      const c=G.column(p.x, p.z);
      let best=null; for(const v of c.intervals) if(p.y<=v.top+0.3 && p.y>=v.bottom-0.3 && (!best || v.top-v.bottom<best.top-best.bottom)) best=v;
      if(best && !allowed.has(best.layer)) bad.push(best.layer+'@'+p.s.toFixed(0));
    }
    chk('nothing but the tract and the air for 12 cm past the opening', bad.length===0, bad.slice(0,6).join(' '));
    const inner=path.pts.filter(p=>p.s>path.airEntry);
    chk('the arc stays off the back wall', inner.every(p=>p.y>ai.bottom+2), Math.min(...inner.map(p=>p.y)).toFixed(1));
    let maxTurn=0; for(let i=4;i<path.pts.length;i++){ const a=path.pts[i-4], b=path.pts[i-2], c=path.pts[i];
      const u=[b.y-a.y,b.z-a.z], v=[c.y-b.y,c.z-b.z], cr=Math.abs(u[0]*v[1]-u[1]*v[0])/(Math.hypot(...u)*Math.hypot(...v)||1);
      maxTurn=Math.max(maxTurn, Math.asin(Math.min(1,cr))/Math.hypot(...u)); }
    chk('no bend tighter than the authored radius', 1/maxTurn >= (rod.bend_mm||16)*0.9, (1/maxTurn).toFixed(1)+' mm');
  }

  section(P+': the intended path');
  for(const mode of ['learn','practice']) for(const hand of ['right','left']){
    const {sim, stuck, r}=play(mode, hand);
    chk(mode+', '+hand+'-handed: finishes', sim.state.finished, stuck+' '+JSON.stringify(r));
    chk(mode+', '+hand+'-handed: no errors', sim.state.errors.length===0, JSON.stringify(sim.state.errors));
    const d=sim.debrief();
    chk(mode+', '+hand+'-handed: every step clean', d.clean===d.total, d.clean+'/'+d.total);
  }

  section(P+': errors');
  const fresh=(mode,hand)=>PXCORE.create(pack, G, {mode:mode||'practice', hand:hand||'right', now:()=>0});
  const walkTo=(sim, id)=>{
    /* Play the intended path up to the step with this id. */
    const hand=sim.state.hand, side=pack.steps.find(s=>s.type==='choice').correct_by_hand[hand], cwFeet=side==='left';
    for(let g=0; g<200 && sim.current() && sim.current().id!==id; g++){
      const s=sim.current();
      if(s.type==='action') sim.action(s.id);
      else if(s.type==='choice') sim.choose(side);
      else if(s.type==='palpate') sim.palpate(cx,cz);
      else if(s.type==='stab'){ sim.placeBlade(cx,cz,s.edge); for(let k=0;k<200&&sim.current()===s;k++){ sim.pushBlade(0.5); sim.releaseBlade(); } }
      else if(s.type==='rotate') sim.rotateBlade(cwFeet?'cw':'ccw');
      else if(s.type==='insert'){ for(let k=0;k<400&&sim.current()===s;k++) sim.pushRod(0.5); }
      else if(s.type==='turn') sim.turnRod(cwFeet?'ccw':'cw');
      else if(s.type==='advance'){ while(sim.state.rod.depth<(s.range_mm[0]+s.range_mm[1])/2) sim.pushRod(1); sim.rodDone(); }
      else if(s.type==='railroad'){ while(!sim.cuffIn()||sim.state.tube.depth<s.depth_mm[0]+2) sim.pushTube(1,true); sim.tubeDone(); }
      else if(s.type==='inflate'){ while(sim.state.cuff_ml<(s.range_ml[0]+s.range_ml[1])/2) sim.inflate(0.5); sim.inflateDone(); }
      else if(s.type==='confirm') sim.confirm();
    }
    return sim;
  };
  { const sim=fresh(); const r=sim.action(pack.steps[3].id);
    chk('practice: a later button is an order error', r.kind==='error' && sim.state.errors[0].code==='order'); }
  { const sim=fresh('learn'); const r=sim.action(pack.steps[3].id);
    chk('learn: a later button is refused with the prompt', r.kind==='info' && /Not yet/.test(r.text) && sim.state.errors.length===0); }
  { const sim=fresh(); const d=pack.distractors[0]; const r=sim.action(d.id);
    chk('practice: a distractor is an error with its feedback', r.kind==='error' && r.text===d.feedback); }
  { const sim=walkTo(fresh(),'side'); const r=sim.choose('right');
    chk('practice: the wrong side is an error and play goes on from it', r.kind==='error' && sim.state.side==='right' && sim.current().id!=='side'); }
  { const sim=walkTo(fresh('learn'),'side'); const r=sim.choose('right');
    chk('learn: the wrong side is refused', r.kind==='error' && sim.current().id==='side'); }
  { const sim=walkTo(fresh('practice','left'),'side'); const r=sim.choose('right');
    chk('left-handed: the right side is correct', r.kind==='ok'); }
  const pal=pack.steps.find(s=>s.type==='palpate').id;
  for(const zid of ['cricoid','thyroid_lower','prominence','isthmus','ctm_lateral']){
    const z=pack.zones.find(q=>q.id===zid); if(!z) continue;
    const sim=walkTo(fresh(),pal); const r=sim.palpate((z.x[0]+z.x[1])/2 + (zid==='ctm_lateral'?8:0), (z.z[0]+z.z[1])/2);
    chk('palpating the '+zid+' is wrong with its own words', r.kind==='error' && r.text===z.wrong, r.text);
  }
  { const sim=walkTo(fresh(),stab.id); const r=sim.placeBlade(cx,cz,'far');
    chk('a stab with the edge away is refused', r.kind==='error' && r.code==='edge_far'); }
  { const sim=walkTo(fresh(),stab.id); const r=sim.placeBlade(cx,cz,'head');
    chk('a stab along the neck is refused', r.kind==='error' && r.code==='edge_vertical'); }
  { const sim=walkTo(fresh(),stab.id); const z=pack.zones.find(q=>q.id==='thyroid');
    const r=sim.placeBlade(0,(z.z[0]+z.z[1])/2,'operator');
    chk('a stab over the cartilage is refused at placement', r.kind==='error' && r.code==='zone'); }
  { const sim=walkTo(fresh(),stab.id); sim.placeBlade(cx,cz,'operator');
    let r, deep=null; for(let k=0;k<120;k++){ r=sim.pushBlade(1); if(r.code==='deep'){ deep=r; break; } }
    chk('pushing on through the airway is a critical error', !!deep && sim.state.errors.some(e=>e.code==='deep'&&e.severity==='critical'));
    chk('and the blade is pulled back into the air', sim.releaseBlade().advanced===true); }
  { const sim=walkTo(fresh(),stab.id); sim.placeBlade(cx,cz,'operator'); sim.pushBlade(3);
    const r=sim.releaseBlade(); chk('a shallow stab says push again', r.code==='shallow' && sim.current().id===stab.id); }
  const rot=pack.steps.find(s=>s.type==='rotate').id;
  { const sim=walkTo(fresh(),rot); const r=sim.rotateBlade('ccw');
    chk('right-handed, on the left: counterclockwise points the edge at the head', r.kind==='error' && r.code==='head'); }
  { const sim=walkTo(fresh('practice','left'),rot); const r=sim.rotateBlade('ccw');
    chk('left-handed, on the right: counterclockwise points the edge at the feet', r.kind==='ok'); }
  const ins=pack.steps.find(s=>s.type==='insert').id;
  { const sim=walkTo(fresh(),ins); sim.pushRod(2); const r=sim.turnRod('ccw');
    chk('turning the rod before the tip is in is refused', r.code==='early_turn'); }
  const turn=pack.steps.find(s=>s.type==='turn').id;
  { const sim=walkTo(fresh(),turn); const r=sim.turnRod('cw');
    chk('turning the rod tip toward the head is refused', r.kind==='error' && r.code==='head'); }
  const adv=pack.steps.find(s=>s.type==='advance');
  { const sim=walkTo(fresh(),adv.id); const r=sim.rodDone();
    chk('stopping the rod short is an error', r.code==='short'); }
  { const sim=walkTo(fresh(),adv.id); let n=0; for(let k=0;k<adv.max_mm+40;k++){ const r=sim.pushRod(1); if(r.code==='long') n++; }
    chk('going too far is one error, not one per push', n===1, n);
    sim.pullRod(sim.state.rod.depth-(adv.range_mm[0]+5)); chk('pulling back into range is accepted', sim.rodDone().kind==='ok'); }
  { const sim=walkTo(fresh(),adv.id); let clicks=0; while(sim.state.rod.depth<adv.range_mm[0]){ if(sim.pushRod(1).click) clicks++; }
    chk('the rings click on the way down', clicks>=3, clicks); }
  const rr=pack.steps.find(s=>s.type==='railroad');
  { const sim=walkTo(fresh(),rr.id); let r; for(let k=0;k<80;k++){ r=sim.pushTube(1,false); if(r.code==='catch') break; }
    chk('a tube pushed without twisting catches', r.code==='catch');
    for(let k=0;k<80;k++) sim.pushTube(1,true);
    chk('twisting gets it past', sim.state.tube.depth>sim.rodGeom().toTop); }
  { const sim=walkTo(fresh(),rr.id); for(let k=0;k<4;k++) sim.pushTube(1,true);
    chk('the cuff outside the airway is refused', sim.tubeDone().code==='cuff_out'); }
  { const sim=walkTo(fresh(),rr.id); const td=()=>sim.state.tube?sim.state.tube.depth:0; for(let k=0;k<400 && td()<rr.depth_mm[1]+5 && td()<sim.state.rod.depth-6;k++) sim.pushTube(1,true);
    chk('the tube too deep is refused', sim.tubeDone().code==='deep'); }
  const inf=pack.steps.find(s=>s.type==='inflate');
  { const sim=walkTo(fresh(),inf.id); sim.inflate(inf.range_ml[0]-1); chk('a soft cuff is refused', sim.inflateDone().code==='low'); }
  { const sim=walkTo(fresh(),inf.id); sim.inflate(inf.range_ml[1]+2); chk('an overfilled cuff is refused', sim.inflateDone().code==='high'); }
  { const sim=walkTo(fresh(),inf.id); sim.inflate(inf.range_ml[1]+2); sim.inflate(-100);
    chk('the cuff never goes below empty', sim.state.cuff_ml===0); }
  { const sim=walkTo(fresh(),inf.id); sim.inflate(inf.range_ml[1]+2); sim.inflate(-3);
    chk('deflating takes air out of an overfilled cuff', Math.abs(sim.state.cuff_ml-(inf.range_ml[1]-1))<1e-9 && sim.inflateDone().kind!=='error'); }
  { const sim=walkTo(fresh(),inf.id); chk('the bougie is out before the cuff', sim.state.rod===null); }
  { const sim=walkTo(fresh(),'secure'); chk('the scalpel is out by the end', sim.state.blade===null); }

  section(P+': the pack');
  const srcIds=new Set(pack.sources.map(s=>s.id));
  for(const s of pack.steps){
    chk(s.id+' has a label and a prompt', !!s.label && !!s.prompt);
    chk(s.id+' has a why', !!s.why);
    chk(s.id+' names a source that exists', !s.source || srcIds.has(s.source));
    if(s.tool) chk(s.id+' names a tool that exists', pack.tools.some(t=>t.id===s.tool));
  }
  const text=JSON.stringify(pack);
  chk('no em dash in the pack', !/—/.test(text));
  chk('no semicolon in learner text', !pack.steps.some(s=>/;/.test((s.prompt||'')+(s.label||'')+Object.values(s.errors||{}).join(''))));
  chk('no "quiet"', !/\bquiet(ly)?\b/i.test(text));
  chk('the pack says it is not physician reviewed', /not physician reviewed/i.test(pack.review||''));
}
console.log(pass+' checks, '+(fail?fail+' FAILED':'all passed'));
process.exit(fail?1:0);
