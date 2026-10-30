/* Tests for Ambulance Run's rules (engine/arcade.js). node engine/arcade-tests.js
   The game is not clinical and is not part of any case. These check that every road the
   generator makes can be driven, that the speed and the score stay inside what the database
   accepts (the Supabase migration 003_arcade.sql), and that a crash ends the run. */
const fs=require('fs'), path=require('path'), vm=require('vm');
const HERE=__dirname, ROOT=path.join(HERE,'..');
const ARCADE=vm.runInNewContext(fs.readFileSync(path.join(HERE,'arcade.js'),'utf8')+'\n;ARCADE', {console, Math, performance:{now:()=>0}});
const {RULES, KINDS, newGame, step, speedAt, scoreOf, reachFor, rowGap}=ARCADE.rules;
let n=0, bad=0;
const chk=(name,ok,extra)=>{ n++; if(!ok){ bad++; console.log('FAIL '+name+(extra?' '+extra:'')); } };

/* A driver that knows where the open lane of each row is and has no reaction time. If the
   generator is right, it never crashes. */
function drive(seed, seconds){
  const g=newGame(seed), dt=1/60;
  let maxRate=0;
  while(g.t<seconds && !g.over){
    const next=g.marks.filter(m=>m.z+3 > RULES.playerZ).sort((a,b)=>a.z-b.z)[0];
    const press={left:0,right:0};
    if(next){ const d=next.path-g.target; if(d<0) press.left=-d; if(d>0) press.right=d; }
    const before=g.dist; step(g, dt, press);
    maxRate=Math.max(maxRate,(g.dist-before)/dt);
  }
  return {g, maxRate};
}
for(let s=1; s<=24; s++){
  const {g,maxRate}=drive(s*7919, 420);
  chk('seed '+s+': the driver who follows the open lane survives 7 minutes', !g.over, g.over?('crashed at t='+g.t.toFixed(1)+' into '+g.hit.kind):'');
  chk('seed '+s+': never faster than vmax', maxRate<=RULES.vmax+1e-6, String(maxRate));
}
/* Every row leaves a lane open, and later rows sometimes block more than one lane. */
{
  const g=newGame(42); let multi=0, total=0, worst=0, offRoad=0;
  const dt=1/60;
  while(g.t<300){
    const before=new Set(g.obs);
    step(g,dt,{left:0,right:0}); g.over=false; g.hit=null;   // drive through everything
    const fresh=g.obs.filter(o=>!before.has(o));
    if(fresh.length){
      const byZ={}; fresh.forEach(o=>{ const k=Math.round(o.z*1000); (byZ[k]=byZ[k]||[]).push(o.lane); });
      for(const k in byZ){ total++; const lanes=new Set(byZ[k]); worst=Math.max(worst,lanes.size); if(lanes.size>1) multi++;
        if(![...lanes].every(l=>l>=0&&l<RULES.lanes)) offRoad++; }
    }
  }
  chk('every obstacle is on the road', offRoad===0, offRoad+' rows');
  /* Lanes blocked per row, late in a run: 1.8 on average (owner, 29 and 30 October 2026). */
  { const g2=newGame(7); let obs=0; const seen=new Set(), rowsAt=new Set();
    while(g2.t<400){ step(g2,1/60,null); g2.over=false; g2.hit=null;
      /* Obstacles of one row are made together at one distance; key them by it when first seen. */
      if(g2.t>130) for(const o of g2.obs) if(!seen.has(o)){ seen.add(o); obs++; rowsAt.add(g2.t.toFixed(4)+':'+o.z.toFixed(3)); } }
    const per=obs/rowsAt.size;
    chk('late rows block about 1.8 lanes on average', per>1.7&&per<1.9, per.toFixed(2)); }
  chk('no row blocks every lane', worst<=RULES.lanes-1, 'worst '+worst);
  chk('some rows block more than one lane', multi>0, multi+' of '+total);
}
/* A crash ends the run. Standing still in one lane is hit sooner or later. */
{
  let crashed=0;
  for(let s=1;s<=10;s++){ const g=newGame(s); while(g.t<120&&!g.over) step(g,1/60,null); if(g.over) crashed++; }
  chk('never steering crashes', crashed===10, crashed+' of 10');
  const g=newGame(3); while(!g.over) step(g,1/60,null);
  const t=g.t, d=g.dist; step(g,1/60,{left:1});
  chk('nothing moves after a crash', g.t===t && g.dist===d);
  chk('the crash names what was hit', KINDS.some(k=>k.id===g.hit.kind));
}
/* Speed. */
chk('starts at v0', speedAt(0)===RULES.v0);
chk('speeds up', speedAt(30)>speedAt(10));
chk('caps at vmax', speedAt(10000)===RULES.vmax);
chk('rows always allow at least one lane of steering at top speed', reachFor(rowGap(1e6)*0.88, RULES.vmax)>=1);
/* Lane changes stay on the road. */
{ const g=newGame(1); step(g,0.016,{left:9}); chk('cannot steer off the left edge', g.target===0);
  step(g,0.016,{right:9}); chk('cannot steer off the right edge', g.target===RULES.lanes-1); }
/* The database's limit must allow the fastest honest run. */
{
  /* The migration folder is found by listing supabase/, so this file never spells its name. */
  const dir=fs.readdirSync(path.join(ROOT,'supabase')).map(d=>path.join(ROOT,'supabase',d)).find(d=>fs.existsSync(path.join(d,'003_arcade.sql')));
  const sql=fs.readFileSync(path.join(dir,'003_arcade.sql'),'utf8');
  const m=sql.match(/v_rate\s+constant\s+numeric\s*:=\s*([0-9.]+)/);
  chk('003_arcade.sql states its points-a-second limit', !!m);
  if(m) chk('the database allows the top speed', Number(m[1])>=RULES.vmax, m[1]+' < '+RULES.vmax);
}
console.log(n+' checks, '+(bad?bad+' FAILED':'all passed'));
process.exit(bad?1:0);
