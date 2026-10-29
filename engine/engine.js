/* ============================================================
   Engine. Case-agnostic: no clinical knowledge, no case names.
   Mirrors system-design-v2.md section 12 components.

   v2 changes: the action surface is the action catalog, not the case. A case
   action binds onto a catalog entry and supplies the tag, prompt, prerequisites
   and debrief note. Everything else is inert. Study results resolve case first,
   catalog default second, nothing third.
   ============================================================ */

/* ---------- condition language (section 4) ---------- */
function tokenize(s){
  return s.replace(/\(/g,' ( ').replace(/\)/g,' ) ').trim().split(/\s+/).filter(Boolean);
}
function parseCond(s){
  if(s===null||s===undefined||s==='') return {t:'true'};
  const p={i:0,k:tokenize(s)};
  const n=pExpr(p);
  if(p.i<p.k.length) throw new Error('trailing tokens in condition: '+s);
  return n;
}
function pExpr(p){ let a=pTerm(p); while(p.k[p.i]==='OR'){p.i++; a={t:'or',a,b:pTerm(p)};} return a; }
function pTerm(p){ let a=pFac(p); while(p.k[p.i]==='AND'){p.i++; a={t:'and',a,b:pFac(p)};} return a; }
function pFac(p){
  if(p.k[p.i]==='NOT'){p.i++; return {t:'not',a:pFac(p)};}
  if(p.k[p.i]==='('){p.i++; const e=pExpr(p); if(p.k[p.i]!==')') throw new Error('unbalanced parens'); p.i++; return e;}
  return pAtom(p);
}
function pAtom(p){
  const k=p.k, i=p.i;
  if(k[i]==='phase'&&k[i+1]==='is'){p.i=i+3; return {t:'phase',v:k[i+2]};}
  if(k[i]==='flag'&&k[i+2]==='set'){p.i=i+3; return {t:'flag',v:k[i+1]};}
  if(k[i]==='study'&&k[i+2]==='ordered'){p.i=i+3; return {t:'ordered',v:k[i+1]};}
  if(k[i]==='study'&&k[i+2]==='resulted'){p.i=i+3; return {t:'resulted',v:k[i+1]};}
  if(k[i]==='action'&&k[i+2]==='taken'){p.i=i+3; return {t:'taken',v:k[i+1]};}
  /* The catalog ships prerequisites written as "flag F" without the trailing
     keyword, which section 3 does not permit. Accept it here so the prototype can
     run, and record it so the interface can say the grammar is being bent. */
  if(k[i]==='flag'&&(k[i+2]===undefined||k[i+2]==='AND'||k[i+2]==='OR'||k[i+2]===')')){
    LOOSE_CONDITIONS.add(p.k.join(' '));
    p.i=i+2; return {t:'flag',v:k[i+1]};
  }
  throw new Error('unparseable atom near: '+k.slice(i,i+3).join(' '));
}
const LOOSE_CONDITIONS=new Set();

function evalCond(n,st){
  switch(n.t){
    case 'true':     return true;
    case 'and':      return evalCond(n.a,st)&&evalCond(n.b,st);
    case 'or':       return evalCond(n.a,st)||evalCond(n.b,st);
    case 'not':      return !evalCond(n.a,st);
    case 'phase':    return st.phase===n.v;
    case 'flag':     return st.flags.has(n.v);
    case 'ordered':  return st.ordered.has(n.v);
    case 'resulted': return st.resulted.has(n.v);
    /* `satisfied` rather than `taken`: a case that has declared two catalog entries to
       be the same act through also_covers is asserting exactly that, so a condition
       naming either of them has to see the other. `taken` stays the set of buttons the
       resident actually pressed and is what the interface reads. */
    /* `satisfied` falling back to `taken`. A hand-built state -- the test harness, or
       anything outside the fold that wants to resolve one rule -- has no reason to know
       about a second set, and `satisfied` is always a superset of `taken`, so degrading
       to it is exactly right rather than merely safe. */
    case 'taken':    return (st.satisfied||st.taken).has(n.v);
  }
  return false;
}
const _ccache=new Map();
function cond(s){ if(!_ccache.has(s)) _ccache.set(s,parseCond(s)); return _ccache.get(s); }
function test(s,st){ return evalCond(cond(s===null?'':s),st); }

/* resolver: first match wins, unconditional default last */
function resolve(rules,st){
  for(const r of rules){ if(r.when===null||r.when===undefined||test(r.when,st)) return r.value; }
  return null;
}
/* An answer field may be a rule list (phase-conditional) or a plain string. */
function resolveText(v,st){
  if(v===null||v===undefined) return null;
  if(typeof v==='string') return v;
  return resolve(v,st);
}

/* ---------- case selection and the catalog merge ----------
   PROTO is assembled here rather than at build time so that every case shares one
   copy of the catalog. Section 6.2: catalog defaults apply unless the case waives
   them, and case prerequisites are additional rather than a replacement. */
let CASE=null, PROTO=null, PACK=null;
let PHASE={}, ACT={}, FU={}, CK=null, CONTENT={}, GENERAL_STATUS=null, PATIENT_VISUAL=null, PATIENT_ALSO=[], PUPILS=null, DEVICE_BY_ID={}, WORN_BY_ID={};

function orphanCategory(eff){
  if(eff.indexOf('exam_')===0) return 'exam';
  if(eff.indexOf('consult_')===0) return 'consultant';
  if(/^(labs_|echo_|cxr|ct_|pocus)/.test(eff)) return 'investigation';
  if(eff.indexOf('interview_topic_')===0) return 'interview';
  if(eff==='handoff_submit') return 'handoff';
  return 'stabilization';
}

function mergeAction(eff, base, caseAct, extra){
  base = base||{}; caseAct = caseAct||{};
  const waived=(caseAct.prerequisite_overrides||[]).map(w=>w.waived).filter(Boolean);
  const prereqs=[], seen=new Set();
  for(const p of (base.default_prerequisites||[])){
    if(seen.has(p.when)||waived.indexOf(p.when)>=0) continue;
    seen.add(p.when); prereqs.push(Object.assign({},p,{origin:'catalog_default'}));
  }
  for(const p of (caseAct.prerequisites||[])){
    if(seen.has(p.when)) continue;
    seen.add(p.when); prereqs.push(Object.assign({},p,{origin:'case'}));
  }
  const origins=new Set(prereqs.map(p=>p.origin));
  const flags=[...new Set((caseAct.flags_set||[]).concat(base.flags_set_default||[]))];
  const rec={
    id:eff,
    catalog_id:base.id||null,
    name:((extra&&extra.coveredBy)?null:caseAct.display_name)||base.name||eff.replace(/_/g,' '),
    tab:(extra&&extra.tab)||base.tab,
    group:(extra&&extra.group)||base.group,
    groups:(extra&&extra.group)?null:(base.groups||null),
    subgroup:(extra&&extra.group)?null:(base.subgroup||null),
    performs:base.performs||null,
    specimen:base.specimen||null,
    category:base.category||(extra&&extra.category)||orphanCategory(eff),
    state_changing:base.state_changing!==undefined?base.state_changing
                  :(caseAct.state_changing!==undefined?caseAct.state_changing:true),
    turnaround_class:base.turnaround_class||null,
    turnaround_override:caseAct.turnaround_override_seconds||null,
    narration_template:base.narration_template||(extra&&extra.narration_template)||null,
    dose_required:!!base.dose_required,
    persistent:!!base.persistent,
    repeatable:base.repeatable!==false,
    prerequisites:prereqs,
    prerequisite_source:origins.size>1?'mixed':(prereqs.length?prereqs[0].origin:'none'),
    prerequisite_waived:waived,
    flags_set:flags,
    default_result:base.default_result||null,
    /* Catalog capability: this act is what puts numbers on the monitor. */
    reveals_vitals:!!base.reveals_vitals,
    /* Never scored (owner, 23 October 2026): intubation care. Marked on the catalog entry at
       build time from catalog data, or by the case on a case-only action. Its effects stand. */
    ungraded:!!(base.ungraded||caseAct.ungraded),
    /* Expectation credit (owner, 29 October 2026), from catalog data: the catalog ids whose
       expectation this act also meets once taken. Resolved to action ids in buildActions. */
    credits:(base&&base.credits)||null,
    bound:!!caseAct.catalog_id,
    orphan:!!(extra&&extra.orphan),
    shadowed:(extra&&extra.shadowed)||[],
    covered_by:(extra&&extra.coveredBy)||null,
    /* Default vital effects (owner, 27 October 2026), from catalog data. Display only: they
       move the monitor and nothing a condition reads. The case's own list, even [], replaces
       them below. stopped_by names the catalog stop orders that end a default drip. */
    vital_effects:base.vital_effects_default||undefined,
    vital_source:base.vital_effects_default?'default':null,
    stopped_by:base.vital_effects_default?(base.stopped_by||null):null
  };
  if(caseAct.catalog_id){
    rec.tag=caseAct.tag;
    rec.prompt=caseAct.prompt;
    rec.debrief_note=caseAct.debrief_note;
    rec.references=caseAct.references;
    rec.halt_reason=caseAct.halt_reason;
    rec.follow_ups_triggered=caseAct.follow_ups_triggered;
    if(caseAct.vital_effects!==undefined){
      rec.vital_effects=caseAct.vital_effects;
      rec.vital_source=(caseAct.vital_effects||[]).length?'case':'none';
      rec.stopped_by=null;
    }
    /* Optional. Where a case action covers several catalog entries the debrief has to
       name the act rather than one of its routes, or a resident who gave amiodarone is
       told they completed 'Digoxin bolus'. The button keeps the catalog's own name;
       only the critical-action list uses this. */
    rec.expectation_label=caseAct.expectation_label;
    /* Optional. Other ways of saying this action aloud, in this case only. The voice
       parser indexes them ahead of the global table (voice.js build). It is the only way
       to give spoken phrases to a case-only action, which has no catalog id for the table
       to key on. Not borrowed by a covered sibling: the phrases name the action that
       authors them, and a sibling keeps its own catalog name and table rows. */
    rec.voice_phrases=(extra&&extra.coveredBy)?null:(caseAct.voice_phrases||null);
    /* Authoring 7.1 has always said a case may override the catalog's narration where
       the standard line would be wrong or confusing. Nothing read it, so the promise was
       not kept. Both this and nurse_alert below are borrowed by a covered sibling, so a
       line authored on a coverage group speaks for every route to the act. */
    rec.narration_override=caseAct.narration_override;
    /* A line the nurse volunteers after the action's own narration. It is rendered red
       and it goes into the running chart, because it is the kind of thing a resident has
       to be able to find again: "these agents take time to work" is useless if it has
       scrolled off the nurse's line by the time they wonder whether the drug failed. */
    rec.nurse_alert=caseAct.nurse_alert;
    /* Flags granted only on the Nth administration of an act. Flags are otherwise
       binary and permanent and section 12 tells authors not to build cases that depend
       on redosing, which is true of everything EXCEPT the one thing this expresses: an
       act that has to be repeated before it works. Counting is per counter rather than
       per action id, so a case can decide whether two doses of one drug and one dose
       each of two drugs are the same thing. */
    rec.flags_set_repeat=caseAct.flags_set_repeat;
    rec.flags_set_timed=caseAct.flags_set_timed;
    /* 27 October 2026. A flag granted only if `when` holds at the moment the act is taken,
       judged before the act's own flags are granted. It tells a dose given after some event
       apart from the doses before it, which a permanent flag cannot. */
    rec.flags_set_if=caseAct.flags_set_if;
    /* v0.20. Conditional credit. also_covers says two entries are always the same act.
       This says: taking this action also discharges another action's expectation, but
       only if `when` holds at the moment it is taken. It exists for an act that is right
       at one point in a case and wrong at another, where the order is the lesson: a
       beta blocker that counts as rate control once the breathing is supported and not
       before. The action keeps its own tag, flags and note, so the early administration
       can be discouraged while the late one is credited. */
    rec.also_satisfies=caseAct.also_satisfies;
    /* v0.21. An action the interface never lists: no button, no search hit. It exists so
       that something the resident does elsewhere in the interface (see handoffIntercept)
       can be an ordinary logged action with a tag, flags and a note. */
    rec.hidden=!!caseAct.hidden;
    /* 29 October 2026. Credit for a set of interview topics asked together: the action is
       satisfied once every topic it lists has been asked (or volunteered), in any order and
       in any phase. For questions that are one clinical act only as a set, such as the
       questions a decision rule turns on. See satisfy(). */
    rec.asked_all=caseAct.asked_all;
  }
  /* v0.26. A catalog entry kept off the menus and out of search: the three primary-survey
     exams, performed together through the composite that names them in `performs`. Kept
     apart from `hidden`, which is the case-authored flag, and still sayable by voice. */
  rec.menu_hidden=!!(base&&base.menu_hidden);
  return rec;
}

function buildActions(pack){
  const caseActs={};
  pack.case.case_actions.forEach(a=>caseActs[a.catalog_id]=a);
  const hiddenBy={};   // case id bound to a catalog entry another case action already holds
  Object.keys(pack.shadowed||{}).forEach(h=>{
    const owner=pack.shadowed[h];
    (hiddenBy[owner]=hiddenBy[owner]||[]).push(h);
  });
  const out={};
  for(const cid in SHARED.actionsBase){
    const eff=(pack.bindings||{})[cid]||cid;
    /* covers: this catalog entry keeps its own id and name, but takes the case
       fields of another action, so a tag applies to every route to the same act. */
    const via=(pack.covers||{})[cid];
    const ca=caseActs[eff]||(via?caseActs[via]:null);
    out[eff]=mergeAction(eff, SHARED.actionsBase[cid], ca,
                         {shadowed:hiddenBy[eff]||[], coveredBy:via||null});
  }
  for(const eff in (pack.orphans||{})){
    const o=pack.orphans[eff];
    out[eff]=mergeAction(eff, null, caseActs[eff], Object.assign({orphan:true},o));
  }
  /* Expectation credit: catalog ids to this case's action ids. */
  const byCat={};
  for(const id in out){ const c=out[id].catalog_id; if(c) (byCat[c]=byCat[c]||[]).push(id); }
  for(const id in out){
    const cr=out[id].credits;
    out[id].credit_targets=cr?[].concat(...cr.map(c=>byCat[c]||[])).filter(x=>x!==id):[];
  }
  return out;
}

/* ---------- the patient's pronouns ----------
   Strings that are written once and shown for every case cannot name a sex: the nurse's
   idle line and the catalog's default prerequisite failure messages are the same words
   whoever is on the trolley. They said "he" until v0.11, which was wrong in the two packs
   whose patient is a woman, and the two packs that noticed worked around it by authoring
   a prerequisite override on every intravenous action in the case: MGCA carries about
   forty near-identical failure messages whose only purpose is a pronoun.

   Shared strings now carry tokens and this substitutes them from `patient.sex` when the
   case is bound. Authored case text contains no tokens and passes through untouched, so
   nothing an author wrote is rewritten by this.

   Verb agreement is why the contraction is inside the token: "{He's} all yours" can become
   "They're all yours" for a case that states no sex, where "{He} is" could not. Any shared
   string needing a present-tense verb after a bare subject pronoun has to be written around
   that, and the three in the catalog are. */
const PRONOUNS={
  male:   {He:'He',   he:'he',   His:'His',   his:'his',   Him:'Him',  him:'him',
           "He's":"He's",   "he's":"he's",   himself:'himself'},
  female: {He:'She',  he:'she',  His:'Her',   his:'her',   Him:'Her',  him:'her',
           "He's":"She's",  "he's":"she's",  himself:'herself'},
  _:      {He:'They', he:'they', His:'Their', his:'their', Him:'Them', him:'them',
           "He's":"They're","he's":"they're",himself:'themselves'},
};
function pron(text,sex){
  if(typeof text!=='string'||text.indexOf('{')<0) return text;
  const t=PRONOUNS[String(sex||'').toLowerCase()]||PRONOUNS._;
  return text.replace(/\{(He's|he's|He|he|His|his|Him|him|himself)\}/g,(m,k)=>t[k]);
}

/* let-bindings inside an eval are not visible to the caller, so the test harness
   reads them through this instead of touching the variables. */
function engineState(){ return {CASE,PROTO,PACK,PHASE,ACT,FU,CK,CONTENT,GENERAL_STATUS}; }

function selectCase(ref){
  PACK = typeof ref==='number' ? CASES[ref]
       : CASES.find(c=>c.prefix===ref||c.id===ref);
  if(!PACK) throw new Error('no such case: '+ref);
  CASE = PACK.case;
  PROTO = Object.assign({}, SHARED, {
    actions: buildActions(PACK),
    bindingCounts: PACK.bindingCounts,
    shadowed: PACK.shadowed,
    phaseShort: PACK.phaseShort,
    traps: PACK.traps,
    dispOrder: PACK.dispOrder,
    dispLabels: PACK.dispLabels,
    correctDxId: PACK.correctDxId,
    correctDxExplanation: PACK.correctDxExplanation,
    altDx: PACK.altDx,
    altDxDefensible: PACK.altDxDefensible||[],
    /* v0.9: the case's additional diagnoses, id to explanation. Appropriate beside the
       primary, and credited when listed with it. */
    addlDx: PACK.addlDx||{},
    /* 23 October 2026: the case's minor diagnoses, id to explanation. True of the patient
       and never scored: naming one costs nothing and leaving it out costs nothing. */
    minorDx: PACK.minorDx||{},
    promptCap: PACK.promptCap,
    /* v0.11. The pack's images, id to data URI, inlined at build time from
       cases/<PREFIX>/media/. Empty for a case that ships none. */
    media: PACK.media||{},
    /* 19 October 2026. The pack's CT series, id to {geometry, windows, notice, data}, from
       cases/<PREFIX>/media/<id>.series.*. Read only by the series viewer in ui.js. Empty for
       a case that ships none. */
    series: PACK.series||{},
    buildNotes: PACK.buildNotes
  });
  /* Substitute the patient's pronouns into every string this build shares between cases.
     Done here rather than in mergeAction so it happens exactly once per bind, and done on
     PROTO rather than SHARED so binding a second case does not read the first one's
     substitutions. mergeAction already copies each prerequisite with Object.assign, so
     writing to failure_message here cannot reach back into the catalog. */
  const SEX=(CASE.patient||{}).sex;
  PROTO.nurseIdle=pron(PROTO.nurseIdle,SEX);
  for(const _id in PROTO.actions)
    for(const _p of (PROTO.actions[_id].prerequisites||[]))
      _p.failure_message=pron(_p.failure_message,SEX);
  PHASE={}; CASE.phases.forEach(p=>PHASE[p.id]=p);
  ACT=PROTO.actions;
  FU={}; (CASE.follow_ups||[]).forEach(f=>FU[f.id]=f);
  CK=CASE.content_keys;
  CONTENT={};
  ['exam','labs','imaging','consultants'].forEach(g=>{
    Object.keys(CK[g]||{}).forEach(k=>{
      if(k==='authoring_note') return;
      const v=CK[g][k];
      CONTENT[k]=Array.isArray(v)?v:v.rules;
    });
  });
  GENERAL_STATUS = CK.general_status ? CK.general_status.rules : null;
  PATIENT_VISUAL = CK.patient_visual ? CK.patient_visual.rules : null;
  PATIENT_ALSO = (CK.patient_visual && CK.patient_visual.also) || [];
  PUPILS = (CK.pupils && Array.isArray(CK.pupils.rules)) ? CK.pupils : null;
  /* v0.17p. The airway device on the figure follows the button pressed, in every case, and
     not a flag each case happened to author: AFRVR's cannula set a flag nothing drew, DIPH
     sent three devices to one flag, CHFE had no cannula action of its own and MGCA's
     first-match list kept a mask on after the cannula went back on. SHARED.patient.
     deviceActions names the device per catalog entry; the case id it is pressed under is
     whatever the pack binds that entry to. */
  DEVICE_BY_ID={};
  const _dev=(SHARED.patient&&SHARED.patient.deviceActions)||{};
  for(const cid in _dev){ const eff=(PACK.bindings||{})[cid]||cid; if(ACT[eff]) DEVICE_BY_ID[eff]=_dev[cid]; }
  /* 11 October 2026. The same for what stays on once placed and replaces nothing (the
     pads): SHARED.patient.wornActions, drawn once the entry has gone through. */
  WORN_BY_ID={};
  const _worn=(SHARED.patient&&SHARED.patient.wornActions)||{};
  for(const cid in _worn){ const eff=(PACK.bindings||{})[cid]||cid; if(ACT[eff]) WORN_BY_ID[eff]=_worn[cid]; }
  return PACK;
}

/* What the figure in the room is doing. A guarded rule list like any other content key:
   first match wins and the value is the whole visible state. The engine resolves it and
   understands none of it; engine/patient.js draws it. A case that authors nothing gets the
   shared default, a patient with open eyes who is breathing and nothing else. */
/* 19 October 2026. The pupils, for the magnified view of the figure's eyes (engine/pupils.js).
   Optional: content_keys.pupils is a guarded rule list, first match wins, and a case without
   it has no view. The value is {state, size_mm?, reaction?, side?}; iris is the block's. */
function pupilState(st){
  if(!PUPILS) return null;
  const v=resolve(PUPILS.rules,st);
  return v?{value:v,iris:PUPILS.iris||null}:null;
}
function patientVisual(st){
  /* `also` is the one place a content key is not first-match: every entry whose condition
     holds adds its add-ons to what the rules chose. Pads, a line and sweat are independent
     of each other and of the airway, and a first-match list can only say that by listing
     every combination. */
  const extra=[];
  for(const r of PATIENT_ALSO) if(test(r.when,st)) for(const a of (r.addons||[])) if(extra.indexOf(a)<0) extra.push(a);
  for(const id in WORN_BY_ID) if(st.taken&&st.taken.has(id)&&extra.indexOf(WORN_BY_ID[id])<0) extra.push(WORN_BY_ID[id]);
  const withExtra=v=>{ if(!extra.length) return v; const o=Object.assign({},v);
    o.addons=(v.addons||[]).concat(extra.filter(a=>(v.addons||[]).indexOf(a)<0)); return o; };
  let out;
  if(PATIENT_VISUAL){
    const v=resolve(PATIENT_VISUAL,st);
    if(v) out={value:withExtra(v),source:'case'};
  }
  if(!out&&extra.length) out={value:withExtra((SHARED.patient&&SHARED.patient.visualDefault)||{}),source:'case'};
  if(!out) out={value:(SHARED.patient&&SHARED.patient.visualDefault)||{},source:'default'};
  return withDevice(out,st);
}
/* The airway device the resident last put on replaces whatever airway the case's rules drew,
   and a tube, from the rules or the button, replaces every other device. With no device
   pressed the rules' choice stands, so CHFE's patient still arrives on the EMS cannula.
   Only a press that went through counts: a blocked one never reaches st.takenAt. */
const AIRWAY=['nasal_cannula','nonrebreather','bipap_mask','bag_valve_mask','intubated'];
function deviceNow(st){
  let best=null, bestAt=0, tube=false;
  for(const id in DEVICE_BY_ID){
    const at=(st.takenAt||{})[id]; if(!at) continue;
    if(DEVICE_BY_ID[id]==='intubated') tube=true;
    if(at>bestAt){ bestAt=at; best=DEVICE_BY_ID[id]; }
  }
  return tube?'intubated':best;
}
function withDevice(out,st){
  const d=deviceNow(st), cur=out.value.addons||[];
  if(!d&&cur.indexOf('intubated')<0) return out;
  const dev=cur.indexOf('intubated')>=0?'intubated':d;
  const addons=cur.filter(a=>AIRWAY.indexOf(a)<0).concat([dev]);
  return {value:Object.assign({},out.value,{addons}),source:out.source,device:d||null};
}

/* The line above the exam list. Case rules first, catalog default second. */
function generalStatus(st){
  if(GENERAL_STATUS){
    const v=resolve(GENERAL_STATUS,st);
    if(v) return {value:v,source:'case'};
  }
  return {value:SHARED.generalStatusDefault,source:'catalog_default'};
}

const catOf   = id => (ACT[id]||{}).category;
const IS_STUDY   = id=>catOf(id)==='investigation';
const IS_EXAM    = id=>catOf(id)==='exam';
const IS_CONSULT = id=>catOf(id)==='consultant';

function turnaround(id){
  const a=ACT[id]||{};
  if(a.turnaround_override) return a.turnaround_override;
  return PROTO.turnaround[a.turnaround_class]!==undefined
       ? PROTO.turnaround[a.turnaround_class] : PROTO.turnaround.lab;
}
function tagOf(id,st){
  const a=ACT[id];
  if(!a||!a.tag) return 'neutral';
  return resolve(a.tag,st)||'neutral';
}
function stateChanging(id){
  const a=ACT[id];
  if(!a) return false;
  if(IS_EXAM(id)) return false;
  if(catOf(id)==='interview') return false;
  return a.state_changing!==false;
}
function dispName(id){ return (ACT[id]&&ACT[id].name)||id.replace(/_/g,' '); }

/* ---------- result resolution: case, then catalog default, then nothing ------ */
function resolveResult(id,snap){
  if(CONTENT[id]) return {value:resolve(CONTENT[id],snap),source:'case'};
  /* v0.18a. A study covered by another (also_covers) is the same act, so it returns that
     action's authored result rather than a catalog "normal". CHFE's cardiac ultrasound
     read as a normal ventricle in a man with an ejection fraction of 25 percent. */
  const via=(ACT[id]||{}).covered_by;
  if(via&&CONTENT[via]) return {value:resolve(CONTENT[via],snap),source:'case'};
  const d=(ACT[id]||{}).default_result;
  if(d) return {value:d,source:'catalog_default'};
  return {value:null,source:'none'};
}

/* ---------- the fold (section 5.2) ---------- */
function snapshot(st){
  return {phase:st.phase,flags:new Set(st.flags),ordered:new Set(st.ordered),
          resulted:new Set(st.resulted),taken:new Set(st.taken),
          satisfied:new Set(st.satisfied)};
}
/* difficultyMultiplier scales every nurse prompt deadline, including escalations
   and follow-up prompts. It scales nothing else: result turnaround, transitions and
   tags are unaffected, so the medicine is identical in both modes and only the
   amount of help changes.

   v0.6: this now also means time-guarded transition deadlines are NOT scaled. Scaling
   them would make hard mode more forgiving (slower deterioration) at the same time as
   the later prompts make it less forgiving, and the mode would stop meaning anything.
   Design 17.1. */
function fold(log, now, difficultyMultiplier){
  const DM = difficultyMultiplier || 1;
  const st={
    phase:CASE.phases[0].id, flags:new Set(), ordered:new Set(), resulted:new Set(), taken:new Set(),
    takenAt:{}, takenSeq:0,
    /* The last time each action went through, on the case clock. A default drip effect
       reads it to know whether its stop order has been given since it started. */
    lastAt:{},
    /* Two sets, because they answer two different questions and conflating them put a
       pressed highlight on a button nobody had pressed.

       `taken` is what the resident did: one entry per button, and it is what the action
       grid reads to draw a control as already used.

       `satisfied` is what has been accomplished: `taken`, plus the covering action of
       anything performed through an also_covers group. A case that binds digoxin,
       amiodarone and metoprolol into one act is asserting that any of them discharges
       it, so giving one has to satisfy the critical action, discharge a follow-up that
       names it, suppress its prompt and make `action X taken` true. None of that means
       the other two buttons were pressed. */
    satisfied:new Set(),
    /* How many times each counter has been administered. Not in the condition language
       and not in the snapshot: a case reads it only through the flag it grants, which is
       what keeps the per-key review matrix finite. */
    adminCount:{},
    orders:{}, phaseEntry:{}, phaseSeq:[], halted:null, complete:null, earlyExit:null,
    /* The third ending. `halted` is a harmful action, `complete` is a handoff, and
       `failed` is the clock walking the case into a terminal phase that is neither.
       Before this existed a case authoring allow_time_to_terminal reached its arrest
       phase and then simply kept running: the monitor showed the last numbers before
       output was lost, the clock carried on, and the interface never noticed the
       patient had died. Set in the fold from the phase table, so no engine code names
       a phase and no case implements an ending. */
    failed:null,
    nurse:[], readouts:[], blocked:[], timeline:[], prompted:new Set(),
    promptFires:[], fuFires:[], fuOutstanding:new Set(), handoff:null, now:now, dm:DM,
    expected:new Set(), expectedByPhase:{}, recommendedTaken:new Set(), defaultsServed:new Set(),
    /* v0.9. The recommended counterpart of `expected`: every action that carried the
       recommended tag on entry to a phase the run visited. `recommendedTaken` only ever
       held the ones that were done, so the debrief could praise a recommended act but
       could not say how many were on offer. The summary scores read both. */
    recommendedExpected:new Set(),
    /* 29 October 2026 (owner: do not tell a learner they missed something that did not
       matter). A phase's recommended actions are held here on entry and become expected
       only if the run stays in that phase for REC_GRACE seconds. A state the learner's own
       treatment ended in a few seconds asks nothing more of them. One done anyway still
       counts. */
    recPending:null,
    /* v0.9. Every interview topic the resident's questions reached, whether or not the
       case also binds it as an action. The summary's History score reads it. */
    askedTopics:new Set(), volunteered:new Set(),
    /* Section 7.3's fifth tier. It was defined in the spec, authored by MGCA on 31
       tag rules, recorded on the timeline, and then read by nothing: the debrief
       surfaced critical, recommended, harmful and the neutral traps, so a
       discouraged action produced no output at all. A tier that carries no weight
       is the defect the tier was added to fix. */
    discouragedTaken:new Set(),
    /* v0.6. guardTrue records when a measured_from:"guard_true" rule first held, so a
       delayed consequence is timed from the action rather than from phase entry.
       timeFires is what the debrief reads to name the deadline that expired. */
    guardTrue:{}, timeFires:[],
    /* v0.7. monitoring is the moment an action carrying the catalog's reveals_vitals
       capability was taken. Until then the interface has no numbers to show and no
       heartbeat to play, because the resident has not put a monitor on the patient.
       It is derived, not authored: no case names it and no case can turn it off. */
    monitoring:null,
    /* v0.7. One record per administration of an action carrying vital_effects, in log
       order. What is ACTIVE at a given moment is derived from these by activeEffects
       below, so a thirty-second effect expires without anything having to be scheduled. */
    vitalFx:[], vitalEffects:[], vitals:null,
    /* v0.8. A flag that lapses. flagGrants records, per flag, whether some action has
       granted it permanently and the latest moment a timed grant runs to; the flag is
       removed only when no live grant remains. flagExpiries is what the debrief and the
       tests read to name the moment something wore off. See expiringFlags below. */
    flagGrants:{}, flagExpiries:[]
  };
  st.phaseEntry[st.phase]=0;
  st.phaseSeq.push({id:st.phase,t:0});

  const ev=[]; let evseq=0;
  const push=(e)=>{ e._s=evseq++; e.done=false; ev.push(e); };
  const promptCount={};

  const REC_GRACE=30;
  function confirmRecommended(t){
    const p=st.recPending; if(!p) return;
    const long=t-p.t>=REC_GRACE-1e-6;
    p.ids.forEach(id=>{ if(long||st.satisfied.has(id)) st.recommendedExpected.add(id); });
    st.recPending=null;
  }
  function onPhaseEntry(phase,t){
    scheduleDeadlines(phase,t);
    const entrySt=snapshot(st); entrySt.phase=phase;
    const recIds=[];
    for(const id in ACT){
      const a=ACT[id];
      /* An entry covered through also_covers borrows another action's case fields so
         that a tag cannot be escaped by choosing a sibling. It must not borrow the
         prompt or the expectation: the resident performs the act once, and four
         entries prompting for one act both nags and consumes the per-phase prompt cap.
         That defect suppressed the glucocorticoid prompt in MGCA and left a
         deterioration unwarned, which is the thing the cap must never do. */
      if(a.covered_by) continue;
      if(a.ungraded) continue;
      if(a.tag&&tagOf(id,entrySt)==='critical'){
        st.expected.add(id);
        (st.expectedByPhase[phase]=st.expectedByPhase[phase]||new Set()).add(id);
      }
      if(a.tag&&tagOf(id,entrySt)==='recommended') recIds.push(id);
      if(!a.prompt) continue;
      if(tagOf(id,entrySt)!=='critical') continue;
      push({t:t+a.prompt.deadline_seconds*DM,kind:'prompt',id,phase,level:1});
      if(a.prompt.escalation)
        push({t:t+a.prompt.escalation.deadline_seconds*DM,kind:'prompt',id,phase,level:2});
    }
    st.recPending={t,ids:recIds};
  }
  function cancelPromptsFor(phase){
    for(const e of ev) if((e.kind==='prompt'||e.kind==='deadline')&&e.phase===phase&&!e.done)
      e.done=true;
  }
  /* A time-guarded deadline joins the same schedule as prompts and results. No new
     loop: the fold already merges log entries and derived events in timestamp order,
     and the 5.3 tiebreak (log entries first at equal timestamps) means a resident who
     gets the drug in on the deadline is credited. */
  function scheduleDeadlines(phase,t){
    const p=PHASE[phase];
    if(!p||!p.transitions) return;
    for(let i=0;i<p.transitions.length;i++){
      const tr=p.transitions[i];
      if(tr.after_seconds===undefined) continue;
      if((tr.measured_from||'phase_entry')!=='guard_true'){
        push({t:t+tr.after_seconds,kind:'deadline',phase});
        continue;
      }
      /* A guard_true rule is timed from the moment its guard first holds, which is
         usually later than phase entry, so a deadline scheduled here would fire at the
         wrong time. Two cases. If the guard ALREADY holds on entry -- the resident gave
         the drug in the phase before this one -- the clock starts now and the deadline
         is real. Otherwise transitionDue schedules it at the moment the guard first
         holds. Without both, a guard_true transition could only ever fire on the
         resident's next action, so a case authoring "this takes a minute to work" left
         a resident who gave the drug and then waited watching nothing happen. */
      let holds; try{ holds=test(tr.when,st); }catch(e){ holds=false; }
      if(!holds) continue;
      const k=phase+'|'+i;
      if(st.guardTrue[k]===undefined) st.guardTrue[k]=t;
      push({t:st.guardTrue[k]+tr.after_seconds,kind:'deadline',phase});
    }
  }
  function enterPhase(to,t){
    /* v0.20. A terminal phase may ask to show the monitor as it stood when the run got
       there (inherit_vitals), instead of one authored set of numbers that is right for
       one route and flattering or unfair for the others. Taken here, before the phase
       changes, from the phase being left and the effects acting at this moment. */
    if(PHASE[to]&&PHASE[to].inherit_vitals&&PHASE[st.phase]&&!PHASE[st.phase].terminal){
      const keep=st.vitalEffects;
      st.vitalEffects=activeEffects(st,t);
      st.inheritedVitals=effectiveVitals(st);
      st.vitalEffects=keep;
    }
    cancelPromptsFor(st.phase);
    confirmRecommended(t);
    st.phase=to;
    st.phaseEntry[to]=t;
    st.phaseSeq.push({id:to,t});
    if(!PHASE[to].terminal) onPhaseEntry(to,t);
    /* Completion is recorded here rather than after each call site. It used to be
       tested only in applyLog, so a case that authored a time-guarded transition into
       case_complete reached the phase without the run ever being marked complete, and
       the same hole opened again for every new kind of timed event. One place. */
    if(to==='case_complete') st.complete={t};
  }
  /* v0.6: a transition rule may carry after_seconds. It matches only when its guard
     holds AND the deadline has passed, measured from phase entry by default or from
     the moment the guard first became true. A rule without after_seconds is
     instantaneous and behaves exactly as it did in v0.5, so a case that authors none
     is bit-identical. Design 2.1a. */
  /* v0.21. The deadline event is scheduled at start+after_seconds and then tested with
     t-start >= after_seconds. In play the clock is a float, and 12.386-7.386 is
     4.999999999999999, so the event arrived, the test failed by one part in 10^15, and
     nothing was ever scheduled again: the transition then waited for the resident's next
     action. Every delayed consequence in every pack did this on roughly half of all runs.
     The tests never saw it because they log whole seconds. */
  const DUE_EPS=1e-6;
  function transitionDue(tr,idx,t){
    if(tr.after_seconds===undefined) return true;
    if((tr.measured_from||'phase_entry')==='guard_true'){
      const k=st.phase+'|'+idx;
      if(st.guardTrue[k]===undefined){
        st.guardTrue[k]=t;
        /* The deadline this rule needs did not exist until now, because at phase entry
           the guard was false. Scheduled once, on the first check that finds it true. */
        push({t:t+tr.after_seconds,kind:'deadline',phase:st.phase});
      }
      return t-st.guardTrue[k] >= tr.after_seconds-DUE_EPS;
    }
    return t-(st.phaseEntry[st.phase]||0) >= tr.after_seconds-DUE_EPS;
  }
  function checkTransitions(t,hop){
    hop=hop||0;
    const p=PHASE[st.phase];
    if(!p||!p.transitions) return;
    for(let i=0;i<p.transitions.length;i++){
      const tr=p.transitions[i];
      if(!test(tr.when,st)) continue;
      if(!transitionDue(tr,i,t)) continue;
      if(tr.to!==st.phase){
        if(tr.after_seconds!==undefined){
          /* The only place a nurse line may describe a trajectory, because one has
             just happened and the monitor is about to show it. Design 2.2. Emitted
             on its own kind so the no-trajectory assertion on prompts stays valid. */
          if(tr.narration) narrate(t,tr.narration,'deterioration');
          st.timeFires.push({t,from:st.phase,to:tr.to,after:tr.after_seconds,
                             when:tr.when,note:tr.debrief_note||''});
        }
        /* 27 October 2026. A transition may grant flags as it fires, permanently, before
           the new phase is entered. It records that something has happened once (a relapse,
           say) so that a guard can make it happen only once. */
        (tr.flags_set||[]).forEach(f=>grantFlag(f,t,null));
        enterPhase(tr.to,t);
        /* 29 October 2026. After an instant move, the phase just entered may already have
           a rule that holds: a diuretic given before the patient stabilized, so stabilizing
           should lead straight on to improving. Until now that rule waited for the
           resident's next order. It is checked here, at the same moment. Only after an
           instant move: a timed rule is a deterioration or a delayed consequence the
           resident is meant to meet, and an earlier order must not cancel it unseen (DIPH's
           seizure fires whatever was given). Bounded, so two rules cannot loop. */
        if(tr.after_seconds===undefined&&hop<8&&PHASE[st.phase]&&!PHASE[st.phase].terminal)
          checkTransitions(t,hop+1);
      }
      return;
    }
  }

  /* ---------- the patient's side of the conversation (design 10.7) ----------
     Everything here is derived, so it replays exactly. Before v0.8 an interview entry
     produced the topic's paragraph and nothing else: asking twice returned the same
     paragraph twice, a follow-up had nothing to attach to, and a question the matcher
     had guessed at was answered with the same confidence as one it was sure of.

     The entry may carry, from the matcher:
       topic     the topic asked about, or null
       fact      a sub-question of that topic answered by one authored fact
       more      "anything else?" against the topic last spoken about
       clarify   two topics the matcher could not choose between
       uncertain the match cleared the threshold without much to spare

     What it does with them, in order:
       clarify   the patient asks which was meant; nothing is marked as asked
       fact      that fact's text, marked told
       more      the next untold facts of the topic, or that there are none
       repeat    a topic already answered gets a short restatement, not the paragraph
       first ask the topic's answer, with every fact it carries marked told, and an
                 echo of the topic in front when the match was uncertain. Since v0.18a
                 the patient also volunteers the adjacent topics the case lists for it
                 (see volunteersFor), so a learner needs fewer questions to see the
                 picture. */
  const said={topics:{},facts:new Set(),volunteered:new Set()};
  const IV=CASE.interview, DEF=(PROTO.interviewDefaults||{});
  const G=IV.global_answer_rules||[];
  const gated=(rules)=>resolve(G.concat(rules),st);
  const echoOf=T=>T&&T.echo?T.echo:null;
  function composeInterview(entry,t){
    const T=entry.topic?IV.topics.find(x=>x.topic===entry.topic):null;
    const push=(key,body,matched,label)=>{
      st.timeline.push({t,id:'interview:'+key,type:'observational',label});
      st.readouts.push({t,kind:'speech',key,title:entry.q,body,matched});
    };
    if(entry.clarify&&entry.clarify.length===2){
      const [a,b]=entry.clarify.map(id=>IV.topics.find(x=>x.topic===id));
      const la=(a&&a.echo)||(a?a.topic.replace(/_/g,' '):'that'), lb=(b&&b.echo)||(b?b.topic.replace(/_/g,' '):'that');
      const tpl=IV.clarify_template||DEF.clarifyTemplate||"'Sorry, do you mean {a}, or {b}?'";
      const body=gated([{when:null,value:tpl.replace('{a}',la.replace(/\?$/,'')).replace('{b}',lb.replace(/\?$/,''))}]);
      push('clarify',body,null,'Asked to clarify a question'); return;
    }
    if(!T){
      push('unmatched',gated(IV.out_of_scope_fallback),null,'Question not understood'); return;
    }
    const facts=T.facts||[];
    const key='told:'+T.topic;
    st.askedTopics.add(T.topic);
    const count=said.topics[T.topic]||0;
    const label='Asked about '+T.topic.replace(/_/g,' ');
    const mark=id=>said.facts.add(T.topic+'#'+id);
    if(entry.fact){
      const f=facts.find(x=>x.id===entry.fact);
      if(f){
        const body=gated(Array.isArray(f.value)?f.value:[{when:null,value:f.value}]);
        mark(f.id); said.topics[T.topic]=count+1;
        push(T.topic,body,T.topic,label+' ('+f.id.replace(/_/g,' ')+')');
        satisfy(T.topic); return;
      }
    }
    if(entry.more){
      const untold=facts.filter(f=>!said.facts.has(T.topic+'#'+f.id)).slice(0,2);
      if(!untold.length){
        push(T.topic,gated([{when:null,value:IV.nothing_more||DEF.nothingMore||"'No, that's everything, really.'"}]),T.topic,label+' (nothing more)');
        return;
      }
      const parts=untold.map(f=>{ mark(f.id); return gated(Array.isArray(f.value)?f.value:[{when:null,value:f.value}]); }).filter(Boolean);
      push(T.topic,parts.join(' '),T.topic,label+' (more)'); return;
    }
    if(count>0){
      /* A repeat. The restatement is the fact marked `restate`, else the first fact,
         else the first sentence of the answer, under a prefix that says it was already
         said. The prefix rotates so a third ask does not read like the second. */
      const first=facts.find(f=>f.restate)||facts[0];
      let core=first?gated(Array.isArray(first.value)?first.value:[{when:null,value:first.value}]):null;
      if(!core){ const full=gated(T.answer)||''; core=firstSentence(full); }
      const prefixes=IV.repeat_prefixes||DEF.repeatPrefixes||["'Like I said, {answer}'"];
      const tpl=prefixes[Math.min(count-1,prefixes.length-1)];
      said.topics[T.topic]=count+1;
      push(T.topic,tpl.replace('{answer}',stripQuotes(core)),T.topic,label+' (again)'); return;
    }
    /* first ask */
    let body=gated(T.answer);
    facts.forEach(f=>{ if(f.in_answer!==false) mark(f.id); });
    said.topics[T.topic]=1;
    if(entry.uncertain&&echoOf(T)&&body){
      const e=echoOf(T);
      body=quoteJoin(e.charAt(0).toUpperCase()+e.slice(1)+'?',body);
    }
    const vols=body?volunteersFor(T):[];
    vols.forEach(v=>{ body=joinSpeech(body,v.line); said.volunteered.add(v.topic); });
    push(T.topic,body,T.topic,label+(vols.length?' (also mentioned '+vols.map(v=>v.topic.replace(/_/g,' ')).join(' and ')+')':''));
    satisfy(T.topic);
    vols.forEach(v=>{ st.volunteered.add(v.topic); satisfy(v.topic); });
  }
  /* v0.18a. Volunteering. A topic may list `adjacent` topics; each adjacent topic that has
     a short `volunteer` line, has not been spoken about, and is not one of the case's
     `must_ask` safety screens is added to the first answer, in the patient's own voice,
     and counts as asked. Nothing is volunteered while a global rule is speaking for the
     patient (intubated, unresponsive, the relative out of the room) or while the case's
     `volunteer_blocked_when` holds (a confused patient answers only what is asked). A
     topic volunteered this way still gives its full answer when it is asked later. */
  function volunteersFor(T){
    if(!T||!T.adjacent||!T.adjacent.length) return [];
    if(G.some(r=>test(r.when,st))) return [];
    if(IV.volunteer_blocked_when&&test(IV.volunteer_blocked_when,st)) return [];
    const must=new Set(IV.must_ask||[]);
    const out=[];
    for(const id of T.adjacent){
      const Y=IV.topics.find(x=>x.topic===id);
      if(!Y||!Y.volunteer||must.has(id)||said.topics[id]||said.volunteered.has(id)) continue;
      const line=resolve(Array.isArray(Y.volunteer)?Y.volunteer:[{when:null,value:Y.volunteer}],st);
      if(line) out.push({topic:id,line});
    }
    return out;
  }
  /* Two stretches of quoted speech become one: 'A.' + 'B.' reads 'A. B.' rather than two
     quotations side by side. Anything else is joined with a space. */
  function joinSpeech(a,b){
    const x=String(a||'').trim(), y=String(b||'').trim();
    if(!x) return y; if(!y) return x;
    for(const q of ["'",'"']) if(x.endsWith(q)&&y.startsWith(q)) return x.slice(0,-1).trimEnd()+' '+y.slice(1);
    return x+' '+y;
  }
  function satisfy(topic){
    st.askedTopics.add(topic);
    if(ACT['interview_topic_'+topic]){
      st.taken.add('interview_topic_'+topic);
      st.satisfied.add('interview_topic_'+topic);
    }
    for(const id in ACT){
      const a=ACT[id];
      if(!a||!Array.isArray(a.asked_all)||!a.asked_all.length||st.satisfied.has(id)) continue;
      if(a.asked_all.every(x=>st.askedTopics.has(x))){ st.taken.add(id); st.satisfied.add(id); }
    }
  }
  /* Answers are authored inside single quotes as the patient's speech. Splicing an echo
     or a prefix onto one has to respect that, or the transcript shows stray quotes. */
  function stripQuotes(s){
    s=String(s||'').trim();
    for(const q of ["'",'"']) if(s.startsWith(q)&&s.endsWith(q)&&s.length>1) return s.slice(1,-1).trim();
    return s;
  }
  function quoteJoin(echo,body){
    const b=String(body).trim();
    for(const q of ["'",'"']) if(b.startsWith(q)) return q+echo+" "+b.slice(1);
    return echo+' '+b;
  }
  function firstSentence(s){
    const inner=stripQuotes(s);
    const m=inner.match(/^(.+?[.!?])(\s|$)/);
    return m?m[1]:inner;
  }

  onPhaseEntry(st.phase,0);

  let li=0;
  for(;;){
    if(st.halted||st.complete||st.earlyExit) break;
    const L=(li<log.length&&log[li].t<=now)?log[li]:null;
    let E=null;
    for(const e of ev){ if(!e.done&&e.t<=now&&(!E||e.t<E.t||(e.t===E.t&&e._s<E._s))) E=e; }
    if(!L&&!E) break;
    let takeLog;
    if(!E) takeLog=true; else if(!L) takeLog=false; else takeLog=(L.t<=E.t);
    if(takeLog){ applyLog(log[li],log[li].t); li++; }
    else { E.done=true; applyEvent(E,E.t); }
  }

  function narrate(t,text,kind){ if(text) st.nurse.push({t,text,kind:kind||'narration'}); }

  /* An obligation is discharged when a listed action has been performed, or when an
     authored condition holds. The second exists because `satisfied_by` is set
     membership and cannot express "again": an obligation to repeat a dose is already
     satisfied by the dose that created it. Either alone is enough; a follow-up with
     neither is never satisfiable and the validator refuses it. */
  function fuSatisfied(f,state){
    if(f.satisfied_by&&f.satisfied_by.some(x=>state.satisfied.has(x))) return true;
    if(f.satisfied_when){
      try{ return test(f.satisfied_when,state); }catch(e){ return false; }
    }
    return false;
  }

  /* ---------- flag grants (design 2.7) ----------
     A permanent grant is absorbing: once any action has set a flag without a duration,
     no later timed grant can take it away, because the permanent one is still true. A
     timed grant extends the flag to the later of its own expiry and any expiry already
     standing, so a second dose refreshes rather than shortening. */
  function grantFlag(f,t,duration,lapseNote){
    st.flags.add(f);
    const g=st.flagGrants[f]||(st.flagGrants[f]={permanent:false,until:-Infinity});
    if(duration===null||duration===undefined){ g.permanent=true; return; }
    if(g.permanent) return;
    /* 28 October 2026: a timed grant may carry the line the nurse says when it lapses. The
       latest grant's line is the one said. */
    if(lapseNote) g.note=lapseNote;
    const until=t+duration;
    if(until>g.until) g.until=until;
    push({t:until,kind:'flag_expire',flag:f});
  }

  function applyLog(entry,t){
    const id=entry.actionId;
    const a=ACT[id];

    if(entry.kind==='early_exit'){
      st.earlyExit={t}; st.timeline.push({t,id:'early_exit',type:'end',label:'Ended the case early'});
      return;
    }
    if(entry.kind==='interview'){
      composeInterview(entry,t);
      return;
    }
    if(!a) return;

    /* prerequisite checker: the condition is a requirement that must hold */
    for(const pr of (a.prerequisites||[])){
      let ok;
      try{ ok=test(pr.when,st); }catch(e){ ok=true; }   // unparseable catalog condition
      if(!ok){
        st.blocked.push({t,id,message:pr.failure_message,source:pr.origin||a.prerequisite_source});
        st.timeline.push({t,id,type:'blocked',label:'Blocked: '+dispName(id)});
        narrate(t,pr.failure_message,'blocked');
        return;
      }
    }

    st.taken.add(id);
    st.lastAt[id]=t;
    st.takenAt[id]=++st.takenSeq;   // order of the last press, for the airway device (v0.17p)
    st.satisfied.add(id);
    /* An entry covered through also_covers borrows the covering action's tag, flags and
       note, so it already advances the case and is scored the same way. It was not
       recorded as having satisfied the covering action itself, which meant the debrief
       listed the critical action as missed by a resident who had performed it by another
       route, and `action X taken` was false after a sibling. Coverage is the case
       asserting the two acts are the same act; recording both is what that assertion
       means. It goes only into `satisfied`: putting it into `taken` as well drew the
       covering action's button as though the resident had pressed that one too. */
    if(a.covered_by) st.satisfied.add(a.covered_by);
    /* 29 October 2026. One act by any reasonable route (catalog expectation credit): a
       mask meets the expectation of a cannula, either blood gas the other's. Only the
       expectation. Flags, phases and the button's own state are untouched. */
    for(const x of (a.credit_targets||[])) st.satisfied.add(x);
    /* Judged against the state as it stood when the button was pressed, before this
       action's own flags are granted, so an action cannot satisfy its own condition. */
    for(const s of (a.also_satisfies||[])){
      let ok; try{ ok=(s.when===null||s.when===undefined)?true:test(s.when,st); }catch(e){ ok=false; }
      if(ok) st.satisfied.add(s.id);
    }

    /* Catalog capability, checked before the state-changing split so an act that
       reveals the vitals does so whether or not it changes the patient. */
    if(a.reveals_vitals && !st.monitoring) st.monitoring={t,id};

    if(!stateChanging(id)){
      if(IS_EXAM(id)){
        const r=CONTENT[id]?{value:resolve(CONTENT[id],st),source:'case'}
                           :{value:(ACT[id]||{}).default_result||null,source:'catalog_default'};
        st.readouts.push({t,kind:'exam',key:id,title:dispName(id),
          body:r.value,source:r.source});
        if(r.source!=='case') st.defaultsServed.add(id);
      } else if(IS_CONSULT(id)){
        st.readouts.push({t,kind:'consult',key:id,title:dispName(id),
          body: CONTENT[id]?resolve(CONTENT[id],st):PROTO.globalConsultant,
          source: CONTENT[id]?'case':'catalog_default'});
        if(!CONTENT[id]) st.defaultsServed.add(id);
      }
      st.timeline.push({t,id,type:'observational',label:dispName(id)});
      return;
    }

    const tag=tagOf(id,st);
    st.timeline.push({t,id,type:'state-changing',label:dispName(id),tag});

    if(tag==='harmful'){
      st.halted={t,id,reason:a.halt_reason||'This action halted the case.'};
      enterPhase('halted',t);
      narrate(t,a.halt_reason||'',"halt");
      return;
    }
    /* A covered sibling acts as its covering action, so it is graded as that action is:
       midazolam standing in for a benzodiazepine for a seizure is graded with it. */
    const ungraded=a.covered_by?!!(ACT[a.covered_by]&&ACT[a.covered_by].ungraded):a.ungraded;
    if(tag==='recommended'&&!ungraded) st.recommendedTaken.add(id);
    if(tag==='discouraged'&&!ungraded) st.discouragedTaken.add(id);
    narrate(t,narrationFor(id),'narration');
    /* On its own kind, so the assertion that no PROMPT describes a trajectory is
       unaffected by it and so the interface can colour it and file it in the chart. Said
       once per administration, which is right: a resident who redoses should hear it
       again. */
    /* 13 October 2026. A string, or a rule list resolved against the state at the moment
       of the order, so a second order of the same drug can carry a different line. */
    { const al=resolveText(a.nurse_alert,st); if(al) narrate(t,al,'alert'); }

    const condFlags=(a.flags_set_if||[]).filter(fc=>test(fc.when,st)).map(fc=>fc.flag);
    (a.flags_set||[]).forEach(f=>grantFlag(f,t,null));
    condFlags.forEach(f=>grantFlag(f,t,null));
    for(const fr of (a.flags_set_repeat||[])){
      /* The counter defaults to the act rather than to the button, so a sibling covered
         through also_covers counts toward the same total. */
      const key=fr.counter||a.covered_by||id;
      st.adminCount[key]=(st.adminCount[key]||0)+1;
      if(st.adminCount[key]>=fr.after_administrations) grantFlag(fr.flag,t,null);
    }
    for(const tf of (a.flags_set_timed||[])) grantFlag(tf.flag,t,tf.duration_seconds,tf.lapse_note);

    /* An administration, not an effect. Whether it is still acting is decided later,
       against the clock and against its guard, so a repeat dose refreshes rather than
       stacks and a stopped drip stops mattering without a second log entry. */
    for(const fx of (a.vital_effects||[]))
      st.vitalFx.push({t,id,vital:fx.vital,delta:fx.delta,
                       key:fx.key||id,
                       onset:fx.onset_seconds===undefined?null:fx.onset_seconds,
                       duration:fx.duration_seconds===undefined?null:fx.duration_seconds,
                       guard:fx.while===undefined?null:fx.while,
                       /* Only a default effect is ended by a stop order. A case's own effect
                          says when it stops through its while guard. */
                       stop:(a.vital_source==='default'&&a.stopped_by)?
                         a.stopped_by.map(c=>((PACK&&PACK.bindings)||{})[c]||c):null});

    if(IS_CONSULT(id)){
      st.readouts.push({t,kind:'consult',key:id,title:dispName(id),
        body: CONTENT[id]?resolve(CONTENT[id],st):PROTO.globalConsultant,
        source: CONTENT[id]?'case':'catalog_default'});
      if(!CONTENT[id]) st.defaultsServed.add(id);
    }

    if(IS_STUDY(id)){
      st.ordered.add(id);
      const due=t+turnaround(id);
      const rec={orderT:t,dueT:due,snap:snapshot(st),value:null,source:null};
      (st.orders[id]=st.orders[id]||[]).push(rec);
      push({t:due,kind:'result',id,rec});
    }

    (a.follow_ups_triggered||[]).forEach(fid=>{
      const f=FU[fid]; if(!f) return;
      push({t:t+f.deadline_seconds*DM,kind:'followup',fid});
    });

    if(id==='handoff_submit') st.handoff=normaliseHandoff(entry.payload);

    checkTransitions(t);
  }

  function applyEvent(e,t){
    if(e.kind==='result'){
      const r=resolveResult(e.id,e.rec.snap);
      e.rec.value=r.value; e.rec.source=r.source;
      if(r.source==='catalog_default') st.defaultsServed.add(e.id);
      st.resulted.add(e.id);
      const a=ACT[e.id]||{};
      const tmpl={lab:'{name} is back.',imaging:'{name} is up on the screen.',
                  radiograph:'{name} is up on the screen.',
                  ecg:'{name} is up.',bedside:'{name} is done.',ultrasound:'{name} is done.'}[a.turnaround_class]||'{name} is back.';
      /* Leads with the name, so it goes through the same sentence rule as the rest. */
      narrate(t,sentence(tmpl.replace('{name}',dispName(e.id))),'result');
      return;
    }
    if(e.kind==='prompt'){
      if(st.satisfied.has(e.id)) return;
      const a=ACT[e.id];
      if(a.prompt.guard&&!test(a.prompt.guard,st)) return;
      promptCount[e.phase]=(promptCount[e.phase]||0);
      /* v0.9. The cap counts the different things the nurse raises in a phase, so
         that she does not nag about nine of them. An escalation raises nothing new:
         it is the same warning said harder, and it exists because the fairness rule
         rests on it (the deterioration's guard depends on the action it names). It
         therefore neither consumes a slot nor is silenced by one. Before this, moving
         a first warning later in a busy phase could push its own escalation past the
         cap and leave the deterioration effectively unwarned. */
      if(e.level!==2){
        if(promptCount[e.phase]>=PROTO.promptCap) return;
        promptCount[e.phase]++;
      }
      narrate(t,e.level===2?a.prompt.escalation.text:a.prompt.text,'prompt');
      st.prompted.add(e.id);
      st.promptFires.push({t,id:e.id,level:e.level});
      return;
    }
    if(e.kind==='deadline'){ checkTransitions(t); return; }
    /* A flag lapsing is a state change with no log entry behind it, which is the whole
       point: the resident did nothing and something stopped working. It has to re-check
       transitions for the same reason a deadline does, or a case could author "when the
       drug is no longer acting, deteriorate" and have it fire only if the resident
       happened to press something afterwards. */
    if(e.kind==='flag_expire'){
      const g=st.flagGrants[e.flag];
      if(!g||g.permanent) return;
      /* A later grant supersedes this expiry. The superseding grant pushed its own
         event, so nothing is lost by returning here. */
      if(g.until>t) return;
      if(!st.flags.has(e.flag)) return;
      st.flags.delete(e.flag);
      st.flagExpiries.push({t,flag:e.flag});
      /* Said as an alert, so it is filed in the running chart and is not a prompt. */
      if(g.note) narrate(t,g.note,'alert');
      checkTransitions(t);
      return;
    }
    if(e.kind==='followup'){
      const f=FU[e.fid];
      if(f.applies_when&&!test(f.applies_when,st)) return;
      if(fuSatisfied(f,st)) return;
      promptCount[st.phase]=(promptCount[st.phase]||0)+1;
      narrate(t,f.nurse_prompt,'prompt');
      st.fuFires.push({t,fid:e.fid});
      /* A follow-up with graded false (post-intubation care) is still asked, and never listed
         in the debrief as an obligation left open. */
      if(f.graded!==false) st.fuOutstanding.add(e.fid);
      return;
    }
  }

  st.pending=[];
  Object.keys(st.orders).forEach(id=>st.orders[id].forEach(o=>{
    if(o.value===null) st.pending.push({id,dueT:o.dueT,orderT:o.orderT});
  }));
  st.fuOutstanding.forEach(fid=>{
    const f=FU[fid];
    if(fuSatisfied(f,st)) st.fuOutstanding.delete(fid);
  });
  confirmRecommended(st.earlyExit?st.earlyExit.t:now);
  st.vitalEffects = activeEffects(st, now);
  st.vitals = effectiveVitals(st);
  /* Terminal by the clock. Tested after everything else so `halted`, `complete` and
     `earlyExit` win: those three carry their own reason and their own debrief, and a
     run that ended by one of them is not additionally a failure. The interface decides
     how long to hold the monitor on the terminal numbers before it ends the run; the
     engine only reports that the run is over and when the phase was entered. */
  if(!st.halted && !st.complete && !st.earlyExit
     && PHASE[st.phase] && PHASE[st.phase].terminal)
    /* byClock says how this terminal phase was reached, because since v0.11 it is no longer
       always the clock: a case may author an instantaneous transition into a terminal phase,
       and DIPH does, for an antiarrhythmic given into a rhythm caused by channel blockade.
       Until this existed the debrief said "Ended by the clock" for that run, which was a
       false statement about the resident's own case. Derived rather than authored: a timed
       arrival is one that appears in timeFires. */
    st.failed={phase:st.phase, t:st.phaseEntry[st.phase],
               reason:PHASE[st.phase].timeout_reason||'',
               byClock:st.timeFires.some(f=>f.to===st.phase)};
  return st;
}

/* ---------- vital effects (design 2.3) ----------
   A phase authors the patient's baseline. An action may move one number off that
   baseline for as long as it is acting. The two are separate on purpose: a phase is a
   clinical state and is entered once, so it cannot express "for the next thirty
   seconds", and it cannot express an effect that is undone when the drip is stopped or
   when the patient is intubated.

   Three rules, and they are the whole mechanism:

   DURATION. duration_seconds absent means the effect lasts as long as its guard holds.
   Present, it lapses that many seconds after the administration.

   GUARD. `while` is an ordinary section 3 condition, evaluated against the state as it
   now stands. An effect whose guard has gone false is simply not in the list.

   KEY. Effects sharing a key do not stack: the most recent administration wins. The key
   defaults to the action id, so giving the same drug twice refreshes its effect rather
   than doubling it. Two routes to the same drug should be given the same explicit key,
   for the same reason a harmful tag has to cover every route to the same act.

   Terminal phases are exempt. halted and case_complete author the numbers a reader is
   meant to be left looking at, and an effect still running when the case ends would
   edit the ending. */
const VITAL_BOUNDS={heart_rate:[0,300],systolic_bp:[0,300],diastolic_bp:[0,300],
                    oxygen_saturation:[0,100],respiratory_rate:[0,80],temperature_c:[25,45]};
function activeEffects(st, now){
  const byKey=new Map();
  for(const fx of st.vitalFx){
    /* Both windows are measured from the administration, which is one rule rather than
       two and is why the validator refuses a duration that does not outlast its onset.
       The active window is [t + onset, t + duration). */
    if(fx.onset!==null && now-fx.t < fx.onset) continue;
    if(fx.duration!==null && now-fx.t >= fx.duration) continue;
    if(fx.stop && fx.stop.some(s=>st.lastAt&&st.lastAt[s]!==undefined&&st.lastAt[s]>=fx.t)) continue;
    if(fx.guard){
      let ok; try{ ok=test(fx.guard,st); }catch(e){ ok=true; }
      if(!ok) continue;
    }
    const prev=byKey.get(fx.key);
    if(!prev||fx.t>=prev.t) byKey.set(fx.key,fx);
  }
  return [...byKey.values()];
}
/* What the monitor should read. Display and audio both take their numbers from here;
   nothing else in the engine does, because vitals do not enter the condition language
   and a study still reports the phase baseline for the moment it was ordered. */
function effectiveVitals(st){
  const p=PHASE[st.phase];
  const base=p?p.vitals:null;
  if(!base) return null;
  if(p.terminal&&p.inherit_vitals&&st.inheritedVitals) return st.inheritedVitals;
  if(p.terminal||!st.vitalEffects||!st.vitalEffects.length) return base;
  const out={};
  for(const k in base) out[k]=base[k];
  for(const fx of st.vitalEffects){
    if(typeof out[fx.vital]!=='number') continue;
    const b=VITAL_BOUNDS[fx.vital]||[-Infinity,Infinity];
    out[fx.vital]=Math.min(b[1],Math.max(b[0],out[fx.vital]+fx.delta));
  }
  if(typeof out.temperature_c==='number') out.temperature_c=Math.round(out.temperature_c*10)/10;
  return out;
}

/* A catalog display name is Title Case because it is a button, and a button's label
   shouts when it is dropped into the middle of a sentence. Lowercasing the whole of it
   was the first fix and it broke the other half: "Normal Saline 1L bolus" became "1l",
   "Furosemide 40 mg IV" became "iv", and "Ringer's" lost a proper noun.

   Only tokens that are ordinary Title Case are lowered. A token carrying a digit, an
   internal capital, an apostrophe or a slash is left exactly as the catalog wrote it,
   because every one of those is a unit, an acronym or a name, and none of them was
   capitalised to look like a button. A hyphenated pair of ordinary words is Title Case
   too, so "Non-Invasive" lowers and "BiPAP/CPAP" does not. */
function softLower(name){
  return String(name||'').split(' ')
    .map(w => /^[A-Z][a-z]+(-[A-Z][a-z]+)*$/.test(w) ? w.toLowerCase() : w)
    .join(' ');
}

/* Some templates lead with the name, so the first word of the sentence is whatever
   softLower left behind. A sentence starts with a capital. */
function sentence(t){
  return t ? t.charAt(0).toUpperCase() + t.slice(1) : t;
}

function narrationFor(id){
  const a=ACT[id]||{};
  if(a.narration_override) return a.narration_override;
  if(a.narration_template){
    /* Dose entry is not implemented, so {dose} is dropped rather than faked. Dropping the
       word and leaving the grammar around it produced "Giving of ceftriaxone", because the
       preposition belongs to the dose and not to the drug. The slot is removed together
       with whatever joins it to the name, in both directions, so "Giving {dose} of {name}"
       becomes "Giving ceftriaxone" and "Starting {name} at {dose}" becomes "Starting
       noradrenaline". If doses are ever implemented, this collapse is the thing to remove
       rather than to work around. */
    return sentence(a.narration_template
             .replace(/\{dose\}\s+of\s+/g,'')
             .replace(/\s+at\s+\{dose\}/g,'')
             .replace(/\{dose\}/g,'')
             .replace('{name}',softLower(a.name))
             .replace('{name_lower}',softLower(a.name))   // an older template spelling
             .replace(/\s{2,}/g,' ').trim());
  }
  if(IS_STUDY(id)) return sentence(dispName(id))+' is away.';
  return 'Okay: '+softLower(dispName(id))+'.';
}


/* ---------- the handoff's diagnoses (v0.9) ----------
   A handover names a working diagnosis and, usually, the things that are also true of
   the patient. The payload therefore carries an ordered list, `diagnoses`, whose first
   entry is the primary. The singular `diagnosis` is kept in step with it for every
   reader written before the list existed, and a payload that only has the singular
   (an older log, an older test) is widened to a list of one. */
function normaliseHandoff(p){
  if(!p) return null;
  const out=Object.assign({},p);
  let list=Array.isArray(p.diagnoses)?p.diagnoses.filter(Boolean):[];
  if(!list.length&&p.diagnosis) list=[p.diagnosis];
  list=list.filter((d,i)=>list.indexOf(d)===i);
  out.diagnoses=list;
  out.diagnosis=list[0]||null;
  return out;
}

/* ---------- a handoff that does not end the case (v0.21) ----------
   Choosing a level of care and confirming normally ends the run. A case may say that one
   disposition, chosen in a state it names, is not accepted as a handoff and has a
   consequence instead: `handoff.disposition_intercepts`, a list of
   {disposition, when, action}. When the resident confirms that disposition and `when`
   holds, the interface logs `action` (an ordinary case action, usually hidden) in place
   of handoff_submit, and the case carries on. The first rule that matches wins.

   It exists for the discharge that a patient does not survive leaving on: ending the run
   there teaches the verdict, and letting it play out teaches the reason and leaves the
   resident with a patient to recover. Nothing is hard-coded: a case that authors no
   intercepts hands over exactly as before. The payload is never read by the condition
   language, so the review matrix is unchanged. */
function handoffIntercept(st,disposition){
  const rules=(CASE&&CASE.handoff&&CASE.handoff.disposition_intercepts)||[];
  for(const r of rules){
    if(r.disposition!==disposition||!r.action||!ACT[r.action]) continue;
    let ok; try{ ok=(r.when===null||r.when===undefined)?true:test(r.when,st); }catch(e){ ok=false; }
    if(ok) return r.action;
  }
  return null;
}

/* One verdict per diagnosis the resident listed, plus the authored ones they did not.
   Verdicts, in the order the debrief prints them:
     primary_correct     the case's main diagnosis, listed first
     primary_defensible  an alternative the case marks acceptable_with_qualification, first
     primary_incorrect   anything else, first
     main_not_primary    the case's main diagnosis, listed but not first
     appropriate         one of the case's additional_diagnoses
     also_true           one of the case's minor_diagnoses (23 October 2026). Not scored
     defensible          an acceptable_with_qualification alternative, not first
     unsupported         anything else
   and `missed` for additional diagnoses that were authored and not listed, and `optional`
   for minor diagnoses not listed, which the debrief shows without counting against anyone.
   The main diagnosis is never in `missed`: not naming it is the primary verdict's job to say. */
function scoreDiagnoses(st){
  const out={rows:[],missed:[],optional:[]};
  if(!st.handoff) return out;
  const list=st.handoff.diagnoses||[];
  const addl=PROTO.addlDx||{};
  const minor=PROTO.minorDx||{};
  const alt=PROTO.altDx||{};
  const defensible=PROTO.altDxDefensible||[];
  list.forEach((id,i)=>{
    let verdict, why;
    if(i===0){
      if(id===PROTO.correctDxId){ verdict='primary_correct'; why=PROTO.correctDxExplanation; }
      else if(defensible.includes(id)){ verdict='primary_defensible'; why=alt[id]; }
      else { verdict='primary_incorrect'; why=alt[id]||addl[id]||minor[id]||PROTO.unlistedDxNote; }
    } else if(id===PROTO.correctDxId){ verdict='main_not_primary'; why=PROTO.correctDxExplanation; }
    else if(addl[id]!==undefined){ verdict='appropriate'; why=addl[id]; }
    else if(minor[id]!==undefined){ verdict='also_true'; why=minor[id]; }
    else if(defensible.includes(id)){ verdict='defensible'; why=alt[id]; }
    else { verdict='unsupported'; why=alt[id]||PROTO.unlistedDxNote; }
    out.rows.push({id,verdict,why:why||''});
  });
  for(const id in addl) if(!list.includes(id)) out.missed.push({id,why:addl[id]});
  for(const id in minor) if(!list.includes(id)) out.optional.push({id,why:minor[id]});
  return out;
}

/* ---------- the seven-category summary (v0.9) ----------
   Points direct review; they do not rank the resident, and the debrief says so. Each
   category is scored from what the case authored, never from a judgement the engine
   makes about medicine:

     History         key topics asked. `interview.key_topics` if the case lists them,
                     otherwise every topic in the bank.
     Physical        regions examined, out of the exams the case tags critical or
                     recommended; failing that `debrief_configuration.key_exams`; failing
                     that every exam the case authors findings for.
     Stabilization,  critical actions at two points each and recommended at one, out
     Interventions,  of the critical and recommended actions that were expected on that
     Investigations, tab in the phases the run visited. Each discouraged action taken
     Consults        on the tab costs a point. A harmful action that halted the case
                     zeroes its tab.
     Handoff         level of care, primary diagnosis, additional diagnoses. See below.

   A tab on which the case expected nothing scores null and prints as not applicable. */
function summaryScores(st){
  const rows=[];
  const pct=(p,m)=>m>0?Math.max(0,Math.min(100,Math.round(100*p/m))):null;

  // History
  const topics=(CASE.interview&&CASE.interview.topics)||[];
  const key=(CASE.interview&&Array.isArray(CASE.interview.key_topics)&&CASE.interview.key_topics.length)
    ? CASE.interview.key_topics.filter(t=>topics.some(x=>x.topic===t))
    : topics.map(x=>x.topic);
  const asked=key.filter(t=>st.askedTopics.has(t));
  rows.push({id:'history',label:'History',points:asked.length,max:key.length,
             pct:pct(asked.length,key.length),
             detail:asked.length+' of '+key.length+(CASE.interview&&CASE.interview.key_topics&&CASE.interview.key_topics.length?' key topics asked':' topics asked'),
             missed:key.filter(t=>!st.askedTopics.has(t))});

  // Physical
  const examIds=Object.keys(ACT).filter(id=>ACT[id].tab==='exam'&&!ACT[id].covered_by);
  let keyEx=examIds.filter(id=>st.expected.has(id)||st.recommendedExpected.has(id));
  let exHow='examined, of the exams this case expects';
  if(!keyEx.length){
    const dbg=CASE.debrief_configuration||{};
    if(Array.isArray(dbg.key_exams)&&dbg.key_exams.length){
      keyEx=dbg.key_exams.filter(id=>examIds.includes(id)); exHow='of the key examinations';
    } else {
      keyEx=examIds.filter(id=>!!CONTENT[id]); exHow='regions examined';
    }
  }
  const exDone=keyEx.filter(id=>st.satisfied.has(id)||st.taken.has(id));
  rows.push({id:'physical',label:'Physical',points:exDone.length,max:keyEx.length,
             pct:pct(exDone.length,keyEx.length),
             detail:exDone.length+' of '+keyEx.length+' '+exHow,
             missed:keyEx.filter(id=>!(st.satisfied.has(id)||st.taken.has(id)))});

  // The four ordering tabs
  const TABS=[['stabilization','Stabilization'],['interventions','Actions'],
              ['investigations','Labs/Imaging'],['consultations','Consults']];
  for(const [tab,label] of TABS){
    const crit=[...st.expected].filter(id=>ACT[id]&&ACT[id].tab===tab);
    const rec=[...st.recommendedExpected].filter(id=>ACT[id]&&ACT[id].tab===tab&&!st.expected.has(id));
    const critDone=crit.filter(id=>st.satisfied.has(id));
    const recDone=rec.filter(id=>st.satisfied.has(id));
    const dis=[...st.discouragedTaken].filter(id=>ACT[id]&&ACT[id].tab===tab);
    const halted=!!(st.halted&&ACT[st.halted.id]&&ACT[st.halted.id].tab===tab);
    const max=2*crit.length+rec.length;
    let points=2*critDone.length+recDone.length-dis.length;
    if(halted) points=0;
    const bits=[];
    if(crit.length) bits.push(critDone.length+' of '+crit.length+' critical');
    if(rec.length) bits.push(recDone.length+' of '+rec.length+' recommended');
    if(dis.length) bits.push(dis.length+' discouraged');
    if(halted) bits.push('halted the case');
    rows.push({id:tab,label,points:Math.max(0,points),max,pct:max?pct(points,max):null,
               detail:bits.join(', ')||'nothing expected on this tab',halted,
               missed:crit.filter(id=>!st.satisfied.has(id)).concat(rec.filter(id=>!st.satisfied.has(id)))});
  }

  // Handoff
  const h=st.handoff, H=CASE.handoff;
  const addl=PROTO.addlDx||{}; const nAddl=Object.keys(addl).length;
  const W={disp:40, primary:nAddl?40:60, addl:nAddl?20:0};
  let hp=0; const bits=[];
  if(h){
    const dOK=h.disposition===H.correct_disposition.id;
    const dAlt=(H.alternative_dispositions||[]).find(a=>a.id===h.disposition);
    const dDef=!dOK&&dAlt&&dAlt.verdict==='acceptable_with_qualification';
    hp+=dOK?W.disp:(dDef?W.disp/2:0);
    bits.push('disposition '+(dOK?'correct':(dDef?'defensible':'incorrect')));
    const dx=scoreDiagnoses(st);
    const first=dx.rows[0];
    const mainListed=dx.rows.some(r=>r.verdict==='main_not_primary');
    if(first&&first.verdict==='primary_correct'){ hp+=W.primary; bits.push('primary diagnosis correct'); }
    else if(first&&first.verdict==='primary_defensible'){ hp+=W.primary/2; bits.push('primary diagnosis defensible'); }
    else if(mainListed){ hp+=W.primary/2; bits.push('main diagnosis listed, not as primary'); }
    else bits.push('primary diagnosis incorrect');
    if(nAddl){
      const got=dx.rows.filter(r=>r.verdict==='appropriate').length;
      hp+=Math.round(W.addl*got/nAddl);
      bits.push(got+' of '+nAddl+' additional diagnoses');
    }
    const bad=dx.rows.filter(r=>r.verdict==='unsupported'||r.verdict==='primary_incorrect').length;
    if(bad){ hp-=5*bad; bits.push(bad+' unsupported'); }
  } else {
    bits.push(st.halted?'no handoff, the case halted':(st.earlyExit?'ended without handing over':'no handoff'));
  }
  rows.push({id:'handoff',label:'Handoff',points:Math.max(0,hp),max:100,pct:pct(hp,100),
             detail:bits.join(', ')});
  return rows;
}

/* ---------- overall score (author instruction, 11 October 2026) ----------
   One number for the debrief's second dial. Critical actions carry 85 of the 100: all of
   them done is 85, and each counts its share. The other 15 is split evenly between two
   parts, each a fraction from 0 to 1: the recommended actions across every tab (less one
   for each discouraged action taken, never below zero), and the handoff (its own 0 to 100).
   The history and the examination still have their own rows in the Summary and no longer
   count here (author instruction, 28 October 2026). A part
   the case gives nothing to score drops out and the others share its weight. A case with
   no critical actions gives the 85 in full. A run that a harmful action halted or that ended
   in a terminal phase is not scored, as everywhere else in the debrief: `scored` is false. */
const OVERALL={critical:85, rest:15};
function overallScore(st){
  /* A critical action done only after the nurse prompted for it earns half (author
     instruction, 11 October 2026). A prompt fires only while the act is still undone, so
     prompted and satisfied means it was done after the prompt. */
  const crit=[...st.expected], critDone=crit.filter(id=>st.satisfied.has(id)).length;
  const critCredit=crit.reduce((s,id)=>s+(st.satisfied.has(id)?(st.prompted.has(id)?0.5:1):0),0);
  const critFrac=crit.length?critCredit/crit.length:1;
  const rows=summaryScores(st), byId={}; rows.forEach(r=>byId[r.id]=r);
  const frac=r=>(r&&r.max>0)?Math.max(0,Math.min(1,r.points/r.max)):null;
  const rec=[...st.recommendedExpected].filter(id=>!st.expected.has(id));
  const recDone=rec.filter(id=>st.satisfied.has(id)).length;
  const recFrac=rec.length?Math.max(0,recDone-st.discouragedTaken.size)/rec.length:null;
  const parts=[
    {id:'recommended',label:'Recommended actions',frac:recFrac},
    {id:'handoff',label:'Handoff',frac:frac(byId.handoff)},
  ].filter(p=>p.frac!==null);
  const each=parts.length?OVERALL.rest/parts.length:0;
  parts.forEach(p=>{ p.weight=each; p.points=p.frac*each; });
  const restPts=parts.length?parts.reduce((s,p)=>s+p.points,0):OVERALL.rest;
  const total=OVERALL.critical*critFrac+restPts;
  return {scored:!(st.halted||st.failed), pct:Math.round(total),
          critical:{done:critDone,total:crit.length,points:OVERALL.critical*critFrac},
          parts};
}
