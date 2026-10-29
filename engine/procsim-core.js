/* ---------- procedure engine (28 October 2026) ----------
   The rules of a procedure, without any drawing. The view (procsim-view.js) turns the
   learner's clicks into calls here and draws what comes back. The tests call it directly.

   A pack is a list of steps. Each step has a type, and the type is the mechanism this file
   implements. Nothing here names a procedure, a structure or an instrument: the pack names
   them, and this file reads only ids, depths, directions and ranges.

     action    a button. Optional effect: {remove, hand, pose, blade, secured, side_from_choice}.
     choice    one of several options. The right one may depend on the learner's hand.
     palpate   find a zone on the skin with the finger.
     stab      place a blade on a zone with its cutting edge set, push until the tip reaches
               the named layer, without passing it.
     rotate    turn the blade a quarter turn at a time until the edge points the named way.
     insert    push a rod in along the blade until its tip reaches the named air layer.
     turn      swing the rod to run along the airway, tip toward the named end.
     advance   push the rod along the airway into a range of depths, then Done.
     railroad  push a tube over the rod, twisting, until its cuff is inside the air layer
               and its depth is in range, then Done.
     inflate   fill a cuff into a range of volumes, then Done.
     confirm   a check that shows its evidence (a capnograph) and completes.

   Two modes. Learn: every step is prompted and a wrong move is explained and refused.
   Practice: no prompts, the same refusals, and every error is kept for the debrief. Both
   keep the errors; only the debrief's wording differs.

   Directions. The operator stands on one side. "operator" is toward them, "far" away,
   "head" and "feet" along the neck. A quarter turn clockwise, seen from above with the head
   at the top, takes +x (the patient's left) to the feet. */
const PXCORE = (function(){
  const DIRS = { '+x':[1,0], '-x':[-1,0], '+z':[0,1], '-z':[0,-1] };
  const CW = { '+x':'-z', '-z':'-x', '-x':'+z', '+z':'+x' };      /* clockwise, seen from above */
  const CCW = { '-z':'+x', '-x':'-z', '+z':'-x', '+x':'+z' };

  function create(pack, geom, opts){
    opts=opts||{};
    const mode=opts.mode==='practice'?'practice':'learn';
    const hand=opts.hand==='left'?'left':'right';
    const now=opts.now||(()=>Date.now());
    const steps=pack.steps, tools={}, zones=pack.zones||[];
    (pack.tools||[]).forEach(t=>tools[t.id]=t);
    const air=(pack.layers.find(l=>l.air)||{}).id;
    const S={
      mode, hand, i:0, t0:now(), tEnd:null, finished:false,
      side:(pack.operator&&pack.operator.default_side)||'left',
      errors:[], stepLog:steps.map(s=>({id:s.id, label:s.label, errors:0, critical:0, t:null})),
      hand_state:'free', pose:'neutral', secured:false,
      tool:null,                                   /* the tool in the dominant hand */
      blade:null,                                  /* {x,z,depth,edge,col,in:true} */
      rod:null,                                    /* {depth, turned:null|'feet'} */
      tube:null,                                   /* {depth, caught:false} */
      cuff_ml:0, capno:false, removed:{}, clicksPassed:0
    };
    const opDir=()=> S.side==='left' ? '+x' : '-x';
    const named=d=>{ if(d===opDir()) return 'operator'; if(d===(S.side==='left'?'-x':'+x')) return 'far';
                     return d==='+z'?'head':'feet'; };
    const dirOf=n=> n==='operator'?opDir() : n==='far'?(S.side==='left'?'-x':'+x') : n==='head'?'+z':'-z';

    const cur=()=>steps[S.i]||null;
    function err(step, code, text, severityOverride){
      const sev=severityOverride || (step&&step.severity&&step.severity[code]) || (code==='order'?'minor':'major');
      const e={step:step?step.id:null, code, text, severity:sev, t:(now()-S.t0)/1000};
      S.errors.push(e);
      if(step){ const L=S.stepLog.find(r=>r.id===step.id); if(L){ L.errors++; if(sev==='critical') L.critical++; } }
      return {kind:'error', text, code};
    }
    function next(msg){
      const s=cur(); const L=S.stepLog[S.i]; if(L) L.t=(now()-S.t0)/1000;
      S.i++;
      if(S.i>=steps.length){ S.finished=true; S.tEnd=now(); }
      return {kind:'ok', text:msg||'', advanced:true, done:S.finished, step:s&&s.id};
    }
    /* A move that belongs to a later or earlier step. */
    function order(kindWanted){
      const s=cur();
      if(!s) return {kind:'info', text:'The procedure is finished.'};
      if(mode==='learn') return {kind:'info', text:'Not yet. '+(s.prompt||s.label), code:'order'};
      return err(s, 'order', 'That is not the next step.');
    }
    const is=(type)=>{ const s=cur(); return !!s && s.type===type; };
    function zoneAt(x, z){
      for(const zn of zones) if(x>=zn.x[0]&&x<=zn.x[1]&&z>=zn.z[0]&&z<=zn.z[1]) return zn;
      return null;
    }
    function feelOf(layer){ return (pack.feel&&pack.feel[layer])||{learn:layer||'', feel:''}; }

    /* ---- buttons ---- */
    function applyEffect(e){
      if(!e) return;
      if(e.remove){ S.removed[e.remove]=true; if(S.tool===e.remove) S.tool=null;
                    const t=tools[e.remove]; if(t&&t.kind==='rod') S.rod=null; if(t&&t.kind==='blade') S.blade=null; }
      if(e.hand) S.hand_state=e.hand;
      if(e.pose) S.pose=e.pose;
      if(e.blade&&S.blade) S.blade.traction=true;
      if(e.secured) S.secured=true;
    }
    function action(id){
      const s=cur();
      if(!s) return {kind:'info', text:'The procedure is finished.'};
      const d=(pack.distractors||[]).find(x=>x.id===id);
      if(d) return mode==='learn' ? {kind:'info', text:d.feedback} : err(s, 'distractor', d.feedback);
      if(s.type!=='action' || s.id!==id){
        const known=steps.find(x=>x.id===id);
        if(!known) return {kind:'info', text:'Unknown action.'};
        return order();
      }
      applyEffect(s.effect);
      return next(s.why ? '' : '');
    }
    function choose(optionId){
      const s=cur();
      if(!s || s.type!=='choice') return order();
      const right=(s.correct_by_hand&&s.correct_by_hand[hand]) || s.correct;
      if(s.effect&&s.effect.side_from_choice) S.side=optionId;
      if(optionId!==right){
        const r=err(s, 'wrong_choice', s.wrong||'Not the best choice.');
        if(mode==='learn') return r;
        return Object.assign(next(), {kind:'error', text:r.text});   /* practice keeps going from the side chosen */
      }
      return next();
    }

    /* ---- the finger ---- */
    function feel(x, z){
      const zn=zoneAt(x, z);
      return zn ? {zone:zn.id, name:zn.name, feel:zn.feel} : {zone:null, name:'', feel:''};
    }
    function palpate(x, z){
      const s=cur();
      if(!s || s.type!=='palpate') return order();
      const zn=zoneAt(x, z);
      if(zn && zn.id===s.target) return next();
      return err(s, 'zone', zn ? zn.wrong : 'That is not the membrane.');
    }

    /* ---- the blade ---- */
    function placeBlade(x, z, edgeName){
      const s=cur();
      if(!s || s.type!=='stab') return order();
      if(S.blade && S.blade.depth>0) return {kind:'info', text:'The blade is already in.'};
      const zn=zoneAt(x, z);
      if(!zn || zn.id!==s.target) return err(s, 'zone', zn ? zn.wrong : 'Not over the target.');
      const want=s.edge||'operator';
      if(edgeName!==want){
        const code=(edgeName==='head'||edgeName==='feet') ? 'edge_vertical' : 'edge_far';
        return err(s, code, (s.errors&&s.errors[code])||'The cutting edge is the wrong way.');
      }
      const col=geom.column(x, z);
      S.blade={x, z, depth:0, edge:dirOf(edgeName), col, resisted:false};
      return {kind:'ok', text:''};
    }
    function pushBlade(mm){
      const s=cur(), b=S.blade;
      if(!b) return is('stab') ? {kind:'info', text:'Place the blade first.'} : order();
      if(!s || s.type!=='stab') return order();
      const reach=s.reach||air;
      const lumen=geom.interval(b.col, reach);
      const lumenBottom=lumen ? b.col.top-lumen.bottom : Infinity;
      let d=b.depth+mm;
      /* Resistant layers stop the blade at their surface. */
      for(let k=0;k<b.col.intervals.length;k++){
        const v=b.col.intervals[k], L=geom.layers.find(l=>l.id===v.layer)||{};
        const dTop=b.col.top-v.top;
        if(L.resist && d>dTop && b.depth<=dTop+0.01){
          d=dTop;
          if(dTop>=lumenBottom-0.01){
            b.depth=Math.max(0, lumenBottom - (lumenBottom-(b.col.top-lumen.top))/2);
            const r=err(s, 'deep', (s.errors&&s.errors.deep)||'Too deep.');
            return Object.assign(r, {layer:reach, depth:b.depth, pulledBack:true});
          }
          b.depth=d;
          if(!b.resisted){ b.resisted=true; return Object.assign(err(s,'resist',(s.errors&&s.errors.resist)||'Resistance.'),{layer:v.layer,depth:d}); }
          return {kind:'info', text:feelOf(v.layer).feel, layer:v.layer, depth:d};
        }
      }
      if(d>lumenBottom){
        b.depth=(lumenBottom+(b.col.top-lumen.top))/2;
        return Object.assign(err(s, 'deep', (s.errors&&s.errors.deep)||'Too deep.'), {layer:reach, depth:b.depth, pulledBack:true});
      }
      b.depth=d;
      const layer=geom.layerAt(b.col, d);
      return {kind:'info', text:'', layer, depth:d};
    }
    function releaseBlade(){
      const s=cur(), b=S.blade;
      if(!s || s.type!=='stab' || !b) return {kind:'info', text:''};
      const layer=geom.layerAt(b.col, b.depth);
      if(layer===(s.reach||air)) return next();
      if(b.depth<=0) return {kind:'info', text:''};
      return {kind:'info', text:(s.errors&&s.errors.shallow)||'Not there yet.', code:'shallow'};
    }
    function rotateBlade(dir){              /* dir: 'cw' or 'ccw' */
      const s=cur(), b=S.blade;
      if(!b){ return {kind:'info', text:'There is no blade in.'}; }
      if(!s || s.type!=='rotate'){
        if(s && s.type==='stab' && b.depth===0) return {kind:'info', text:''};
        return order();
      }
      const to=(dir==='cw'?CW:CCW)[b.edge], name=named(to);
      if(name!==s.to){
        return err(s, name, (s.errors&&s.errors[name])||('The cutting edge would point '+name+'.'));
      }
      b.edge=to;
      return next();
    }

    /* ---- the rod: in along the blade, a turn, then along the airway ---- */
    function rodGeom(){
      const b=S.rodEntry;
      const lumen=geom.interval(b.col, air);
      const toTop=b.col.top-lumen.top, toBottom=b.col.top-lumen.bottom;
      const center=(toTop+toBottom)/2;
      if(!b.path){
        const T=Object.values(tools).find(t=>t.kind==='rod')||{};
        b.path=geom.rodPath(b.x, b.z, {air, tract_deg:T.tract_deg, bend_mm:T.bend_mm, straight_mm:T.straight_mm});
        b.tract=((T.tract_deg||65)*Math.PI/180);
      }
      return {toTop, toBottom, center, path:b.path, airEntry:b.path.airEntry};
    }
    function pushRod(mm){
      const s=cur();
      if(!s || !(s.type==='insert'||s.type==='advance')) return order();
      if(!S.rod){
        if(s.type!=='insert') return order();
        if(!S.blade) return {kind:'info', text:'There is no opening to guide it.'};
        S.rodEntry={x:S.blade.x, z:S.blade.z, col:S.blade.col};
        S.rod={depth:0, turned:null};
      }
      const R=rodGeom(), r=S.rod;
      if(!r.turned){
        let d=r.depth+mm;
        if(d>=R.toBottom){
          r.depth=R.toBottom-0.5;
          return Object.assign(err(s,'deep',(s.errors&&s.errors.deep)||'Hold-up at the back wall.','minor'),{depth:r.depth});
        }
        r.depth=Math.max(0,d);
        const inAir=r.depth>R.toTop;
        if(s.type==='insert' && inAir){ return next('The tip is in the trachea.'); }
        return {kind:'info', text:'', depth:r.depth};
      }
      /* Turned: along the airway. Clicks as the tip passes each ring. */
      const max=s.max_mm||Infinity;
      r.depth=Math.max(0, Math.min(r.depth+mm, max+20));
      let click='';
      if(s.clicks){
        const L=geom.layers.find(l=>l.id===s.clicks);
        if(L&&L.at){
          const tipZ=geom.along(R.path, r.depth).z;
          const passed=L.at.filter(z=>tipZ<z).length;
          if(passed>S.clicksPassed){ click=feelOf(s.clicks).feel||'Click.'; }
          S.clicksPassed=passed;
        }
      }
      if(r.depth>max){
        if(!r.long){ r.long=true; return Object.assign(err(s,'long',(s.errors&&s.errors.long)||'Too far.'),{depth:r.depth}); }
        return {kind:'info', text:(s.errors&&s.errors.long)||'', depth:r.depth};
      }
      r.long=false;
      return {kind:'info', text:click, depth:r.depth, click:!!click};
    }
    function turnRod(dir){
      const s=cur();
      if(!S.rod){ return is('turn')||is('insert') ? {kind:'info', text:'Put the tip in first.'} : order(); }
      if(s && s.type==='insert'){
        const R=rodGeom();
        if(S.rod.depth<=R.toTop) return err(s,'early_turn',(s.errors&&s.errors.early_turn)||'Tip in first.');
      }
      if(!s || s.type!=='turn') return order();
      /* The shaft starts across the neck toward the operator. A clockwise swing takes it
         toward the feet when the operator is on +x, which points the tip at the head. */
      const shaftTo=(dir==='cw'?CW:CCW)[opDir()];
      const tip=shaftTo==='+z'?'feet':'head';
      if(tip!==s.to) return err(s, tip, (s.errors&&s.errors[tip])||('The tip would point to the '+tip+'.'));
      S.rod.turned=tip;
      /* The tip is as far in as it was, now measured along the turned path. */
      S.rod.depth=Math.max(S.rod.depth/Math.sin(S.rodEntry.tract), rodGeom().airEntry+1);
      S.clicksPassed=0;
      return next();
    }
    function rodDone(){
      const s=cur();
      if(!s || s.type!=='advance') return order();
      const d=S.rod?S.rod.depth:0, [lo,hi]=s.range_mm;
      if(d<lo) return err(s,'short',(s.errors&&s.errors.short)||'Not far enough.');
      if(d>hi) return err(s,'long',(s.errors&&s.errors.long)||'Too far.');
      return next();
    }
    function pullRod(mm){ return pushRod(-mm); }

    /* ---- the tube over the rod ---- */
    function pushTube(mm, twist){
      const s=cur();
      if(!s || s.type!=='railroad') return order();
      if(!S.rod || !S.rod.turned) return {kind:'info', text:'There is no bougie to railroad over.'};
      if(!S.tube) S.tube={depth:0, caught:false};
      const R=rodGeom(), t=S.tube;
      const catchAt=R.airEntry-(s.catch_mm||0);
      let d=t.depth+mm;
      if(!twist && mm>0 && d>catchAt && t.depth<=catchAt+0.01){
        t.depth=catchAt;
        if(!t.caught){ t.caught=true; return Object.assign(err(s,'catch',(s.errors&&s.errors.catch)||'It catches.','minor'),{depth:t.depth}); }
        return {kind:'info', text:(s.errors&&s.errors.catch)||'', depth:t.depth};
      }
      t.depth=Math.max(0, Math.min(d, S.rod.depth-5));
      return {kind:'info', text:'', depth:t.depth, cuffIn:cuffIn()};
    }
    function cuffIn(){
      const s=steps.find(x=>x.type==='railroad'); if(!s||!S.tube) return false;
      const R=rodGeom();
      return (S.tube.depth-s.cuff_mm[1]) > R.airEntry+1;
    }
    function tubeDone(){
      const s=cur();
      if(!s || s.type!=='railroad') return order();
      const d=S.tube?S.tube.depth:0;
      if(!cuffIn()) return err(s,'cuff_out',(s.errors&&s.errors.cuff_out)||'The cuff is out.');
      if(d>s.depth_mm[1]) return err(s,'deep',(s.errors&&s.errors.deep)||'Too deep.');
      if(d<s.depth_mm[0]) return err(s,'cuff_out',(s.errors&&s.errors.cuff_out)||'Not far enough.');
      return next();
    }
    function pullTube(mm){
      const s=cur();
      if(!s || s.type!=='railroad' || !S.tube) return order();
      S.tube.depth=Math.max(0,S.tube.depth-mm);
      return {kind:'info', text:'', depth:S.tube.depth, cuffIn:cuffIn()};
    }

    /* ---- the cuff and the check ---- */
    function inflate(ml){
      const s=cur();
      if(!s || s.type!=='inflate') return order();
      S.cuff_ml=Math.max(0, Math.min((s.max_ml||30), S.cuff_ml+ml));
      return {kind:'info', text:'', ml:S.cuff_ml};
    }
    function inflateDone(){
      const s=cur();
      if(!s || s.type!=='inflate') return order();
      const [lo,hi]=s.range_ml;
      if(S.cuff_ml<lo) return err(s,'low',(s.errors&&s.errors.low)||'Too little.');
      if(S.cuff_ml>hi) return err(s,'high',(s.errors&&s.errors.high)||'Too much.');
      return next();
    }
    function confirm(){
      const s=cur();
      if(!s || s.type!=='confirm') return order();
      S.capno=true;
      return next();
    }

    function debrief(){
      const t=((S.tEnd||now())-S.t0)/1000;
      const clean=S.stepLog.filter(r=>r.t!=null && r.errors===0).length;
      return {mode, hand, side:S.side, seconds:t, finished:S.finished, steps:S.stepLog.map(r=>Object.assign({},r)),
              errors:S.errors.slice(), clean, total:steps.length,
              critical:S.errors.filter(e=>e.severity==='critical').length};
    }

    return {state:S, current:cur, action, choose, feel, palpate, placeBlade, pushBlade, releaseBlade, rotateBlade,
            pushRod, pullRod, turnRod, rodDone, pushTube, pullTube, tubeDone, inflate, inflateDone, confirm, debrief,
            named, dirOf, rodGeom:()=>S.rodEntry?rodGeom():null, cuffIn, zoneAt, feelOf};
  }
  return {create};
})();
if(typeof module!=='undefined') module.exports=PXCORE;
