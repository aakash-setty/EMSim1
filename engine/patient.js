/* ============================================================
   The patient: a drawn figure standing in the room, between the panels.

   This module draws a person and moves them. It holds no clinical knowledge
   and names no case. A case says what the patient looks like (patient.avatar)
   and what is visible right now (content_keys.patient_visual, a guarded rule
   list like every other content key), and this module renders what it is told.
   It never decides that a respiratory rate means distress or that a phase means
   a seizure: a case says "eyes closed, seizure, work of breathing severe" and
   never says why, exactly as monitor.js is told "no P waves, QRS 180 ms".

   Four things live here.

   1. THE ARTWORK. PATIENT_ART is injected ahead of this file by the build from
      engine/patient-art.json, which engine/assets/avataaars/extract.js derives
      from the avataaars library (MIT, (c) 2017 Pablo Stanley and Fang-Pen Lin).
      Every option of the original generator is kept: 35 tops, 7 accessories,
      6 facial hair, 9 clothes, 11 shirt graphics, 12 eyes, 12 eyebrows,
      12 mouths, and the four colour palettes, plus a hospital gown and one
      eyebrow upstream never registered. The art is stored as loose parts
      with colour slots rather than whole avatars, so a part can be swapped
      alone, which is what a blink is.

   2. THE RIG. The original draws one flat picture. This one nests the same
      parts inside named groups so they can move independently:

        figure  everything. A seizure shakes this.
        torso   shoulders and clothes. Breathing lifts this.
        head    skull, face, hair, glasses. Bobs with laboured breathing.
        eyes, brows, mouth   inside the face.

      Each group has a channel {x, y, rot, sx, sy}. Every frame the channels are
      zeroed, every active feature adds its contribution, and the sums are
      written as transforms. Because contributions add, a seizing patient still
      breathes and a nystagmus add-on works whether or not the head is bobbing.

   3. POSES. Eyes, mouth and eyebrows each hold several drawings and show one.
      A blink is the eyes pose set to 'Close' for 130 ms. Features write to the
      pose in priority order, so eyes_closed beats blink and an add-on can beat
      both.

   4. FEATURES AND ADD-ONS. One registry. A feature is anything that can be
      active on a patient: the built-in behaviours (breathing, blink,
      eyes_closed, seizure) and every add-on a case can name (a nasal cannula,
      gaze deviation, later a BiPAP mask or an endotracheal tube). A feature may
      carry SVG for any of the named slots, a per-frame tick that writes to
      channels and poses, a list of layers to hide while it is on, or any mix.
      Adding one is a PATIENT.register() call and one line in the vocabulary in
      build_simulator.py; nothing else in the engine changes. See the README in
      engine/assets/avataaars for the coordinate landmarks an SVG is drawn to.

   The coordinate system is the original's: a 264 x 280 viewBox, head centred
   on x=132, eyes at (106,112) and (158,112), mouth centred near (132,156).
   ============================================================ */
const PATIENT=(function(){
  'use strict';
  const ART=(typeof PATIENT_ART!=='undefined'&&PATIENT_ART)?PATIENT_ART:null;

  /* ---------- vocabulary ---------- */
  /* The standard patient. One base for a man and one for a woman, identical except for
     the hair, and every case draws one of the two by patient.sex unless it authors a
     patient.avatar of its own. The build can replace these through SHARED.patient.base
     (setBases, below) so the choice lives with the rest of the shared vocabulary. Nothing
     in the appearance ever changes with the patient's state: states move the figure and
     swap the eyes, brows and mouth, and leave hair, clothes and colours alone. */
  const DEFAULT_APPEARANCE={
    topType:'ShortHairShortFlat', accessoriesType:'Blank', hairColor:'BrownDark', hatColor:'Gray01',
    facialHairType:'Blank', facialHairColor:'BrownDark',
    clotheType:'ShirtVNeck', clotheColor:'Gray01', graphicType:'Bat',
    eyeType:'Default', eyebrowType:'Default', mouthType:'Serious', skinColor:'Brown',
    build:'average',               /* thin | average | obese */
    ageGroup:'young'               /* young 18 to 39 | middle 40 to 59 | older 60 and over */
  };
  const BUILDS=['thin','average','obese'], AGE_GROUPS=['young','middle','older'];
  /* The author's bands are 18-40, 40-60 and 60-100; a patient of exactly 40 is drawn middle
     and of exactly 60 older. Under 18 draws as young: there is no child figure. */
  function ageGroupFor(age){ return typeof age!=='number'?'young':age>=60?'older':age>=40?'middle':'young'; }
  let BASES={male:{}, female:{topType:'LongHairStraight'}};
  function baseFor(sex,avatar){
    const out={}, b=BASES[sex]||BASES.male||{};
    for(const k in b) out[k]=b[k];
    for(const k in (avatar||{})) if(k!=='authoring_note'&&k!=='verify') out[k]=avatar[k];
    return out;
  }
  const DEFAULT_STATE={
    eyes:'open',                   /* open | closed */
    seizure:false,                 /* true | false */
    work_of_breathing:'normal',    /* normal | increased | severe */
    respiratory_rate:16,           /* breaths per minute; 0 stops the chest */
    expression:null,               /* {eyeType, eyebrowType, mouthType} overriding the avatar's resting face */
    addons:[],                     /* names of registered features */
    alertness:0,                   /* 0 alert, 1 drowsy, 2 obtunded, 3 unresponsive. Passed in like distress */
    distress:0                     /* 0 to 3. Not authored in patient_visual: the interface passes the
                                      phase's own appearance.distress_level, as it passes the rate */
  };
  const WOB={
    /* rise is how far the shoulders lift, in viewBox units, at the top of a breath */
    normal:   {rise:3.0, bob:0.35, flare:0,    open:0,    art:null},
    increased:{rise:5.0, bob:1.3,  flare:0.10, open:0.85, art:'Disbelief'},
    severe:   {rise:7.0, bob:2.4,  flare:0.20, open:1,    art:'Concerned'}
  };
  /* The resting face at each authored distress level. Nobody arriving in a resuscitation
     bay is smiling, so even level 0 is a neutral mouth. This is a drawing of a number the
     case already authored, not an inference: the module still does not know why. Closed
     eyes relax the face back to level 0, because a sedated patient does not look worried.
     An authored expression, or an avatar whose own face differs from the base, wins. */
  const DISTRESS_FACE=[
    {mouth:'Serious', brows:'Default'},
    {mouth:'Serious', brows:'SadConcerned'},
    {mouth:'Sad',     brows:'SadConcerned'},
    {mouth:'Sad',     brows:'SadConcernedNatural'}
  ];
  /* appearance key -> [art group, palette] */
  const PART_KEYS={topType:'top',accessoriesType:'accessories',facialHairType:'facialHair',
    clotheType:'clothes',graphicType:'graphic',eyeType:'eyes',eyebrowType:'eyebrow',mouthType:'mouth'};
  const COLOR_KEYS={skinColor:'skin',hairColor:'hair',facialHairColor:'facialHair',hatColor:'fabric',clotheColor:'fabric'};
  const SLOTS=['backdrop','behind','torso','underFace','skin','face','overHair','front','overlay'];
  const HIDEABLE=['clothes','facialHair','hair','accessories','eyes','brows','mouth','nose'];

  const EXTRA_PARTS={};            /* parts registered at run time, same shape as ART.parts */
  function partSrc(group,name){
    if(group==='nose') return ART?ART.parts.nose:'';      /* one drawing, not a map */
    if(EXTRA_PARTS[group]&&EXTRA_PARTS[group][name]!==undefined) return EXTRA_PARTS[group][name];
    if(ART&&ART.parts[group]&&ART.parts[group][name]!==undefined) return ART.parts[group][name];
    return undefined;
  }
  function optionsOf(group){
    const base=(ART&&ART.options[group])||[];
    return base.concat(Object.keys(EXTRA_PARTS[group]||{}).filter(k=>base.indexOf(k)<0));
  }
  function registerPart(group,name,svg){ (EXTRA_PARTS[group]=EXTRA_PARTS[group]||{})[name]=svg; }

  const HEX=/^#(?:[0-9a-f]{3}|[0-9a-f]{6})$/i;
  function colour(palette,v,fallback){
    const p=(ART&&ART.colors[palette])||{};
    if(p[v]) return p[v];
    if(typeof v==='string'&&HEX.test(v)) return v;
    return p[fallback]||'#999999';
  }

  /* Reports rather than throws: an unknown value falls back to the default and the
     problem is returned, so the validator and the lab can show it and the simulator
     still draws somebody. */
  function normalizeAppearance(a){
    const out={}, problems=[];
    a=a||{};
    for(const k in DEFAULT_APPEARANCE) out[k]=DEFAULT_APPEARANCE[k];
    for(const k in a){
      if(!(k in DEFAULT_APPEARANCE)){ problems.push('unknown avatar key '+k); continue; }
      if(k==='build'||k==='ageGroup'){
        if((k==='build'?BUILDS:AGE_GROUPS).indexOf(a[k])<0) problems.push(k+' '+JSON.stringify(a[k])+' is not one of '+(k==='build'?BUILDS:AGE_GROUPS).join(', '));
        else out[k]=a[k];
        continue;
      }
      if(PART_KEYS[k]){
        if(partSrc(PART_KEYS[k],a[k])===undefined) problems.push(k+' '+JSON.stringify(a[k])+' is not an option');
        else out[k]=a[k];
      } else {
        const pal=(ART&&ART.colors[COLOR_KEYS[k]])||{};
        if(!pal[a[k]]&&!HEX.test(String(a[k]))) problems.push(k+' '+JSON.stringify(a[k])+' is neither a palette name nor a hex colour');
        else out[k]=a[k];
      }
    }
    return {appearance:out,problems:problems};
  }
  function normalizeState(s){
    const out={}, problems=[];
    s=s||{};
    for(const k in DEFAULT_STATE) out[k]=DEFAULT_STATE[k];
    for(const k in s){
      if(!(k in DEFAULT_STATE)){ problems.push('unknown visual key '+k); continue; }
      out[k]=s[k];
    }
    if(out.eyes!=='open'&&out.eyes!=='closed'){ problems.push('eyes must be open or closed'); out.eyes='open'; }
    if(!WOB[out.work_of_breathing]){ problems.push('work_of_breathing must be normal, increased or severe'); out.work_of_breathing='normal'; }
    out.seizure=!!out.seizure;
    out.distress=Math.max(0,Math.min(3,Math.round(+out.distress||0)));
    out.alertness=Math.max(0,Math.min(3,Math.round(+out.alertness||0)));
    if(typeof out.respiratory_rate!=='number'||!(out.respiratory_rate>=0)) out.respiratory_rate=DEFAULT_STATE.respiratory_rate;
    out.addons=(Array.isArray(out.addons)?out.addons:[]).filter(n=>{
      if(FEATURES[n]&&!FEATURES[n].builtin) return true;
      problems.push('addon '+JSON.stringify(n)+' is not registered'); return false; });
    if(out.expression){
      const e={};
      for(const k of ['eyeType','eyebrowType','mouthType']){
        if(out.expression[k]===undefined) continue;
        if(partSrc(PART_KEYS[k],out.expression[k])===undefined) problems.push('expression.'+k+' '+JSON.stringify(out.expression[k])+' is not an option');
        else e[k]=out.expression[k];
      }
      out.expression=e;
    }
    return {state:out,problems:problems};
  }

  function mix(a,b,t){
    const p=h=>{ h=h.replace('#',''); if(h.length===3) h=h.split('').map(c=>c+c).join(''); return [0,2,4].map(i=>parseInt(h.substr(i,2),16)); };
    const x=p(a), y=p(b);
    return '#'+x.map((v,i)=>('0'+Math.round(v+(y[i]-v)*t).toString(16)).slice(-2)).join('');
  }
  /* ---------- the feature registry ---------- */
  const FEATURES={};
  function register(name,def){
    def=def||{};
    FEATURES[name]={name:name, priority:def.priority===undefined?50:def.priority, builtin:!!def.builtin,
      label:def.label||name.replace(/_/g,' '), describe:def.describe||null,
      layers:def.layers||null, skin:def.skin||null, hide:def.hide||null, enter:def.enter||null, exit:def.exit||null, tick:def.tick||null};
    INSTANCES.forEach(i=>{ i._dirty=true; });
    return FEATURES[name];
  }

  /* ---------- an instance ---------- */
  const INSTANCES=[];
  let UID=0;
  const RIGS={           /* pivot of each rig, in the coordinates the group lives in */
    figure:[132,280], torso:[132,280], shoulderL:[132,216], shoulderR:[132,216], head:[132,192],
    eyes:[56,30], brows:[56,14], mouth:[56,75], nose:[56,47]
  };
  function zero(){ return {x:0,y:0,rot:0,sx:1,sy:1}; }

  function Instance(container,appearance,state,opts){
    this.frameStyle=(opts&&opts.frame)==='circle'?'circle':'none';
    this.uid='pt'+(++UID)+'-';
    this.n=0;
    this.container=container;
    this.appearance=normalizeAppearance(appearance).appearance;
    this.state=normalizeState(state).state;
    this.mem={};                 /* per-feature scratch, keyed by feature name */
    this.active=[];
    this.t=0; this.breathPhase=0; this.last=null;
    this.seed=(UID*2654435761)>>>0;
    this._dirty=true; this._shown={}; this._tf={}; this._label='';
    this.build();
  }
  Instance.prototype.rand=function(){           /* small seeded generator: a test can replay a blink */
    let x=this.seed; x^=x<<13; x>>>=0; x^=x>>>17; x^=x<<5; x>>>=0; this.seed=x; return x/4294967296;
  };
  Instance.prototype.part=function(group,name,fills){
    let s=partSrc(group,name);
    if(!s) return '';
    const pre=this.uid+(this.n++)+'_';
    s=s.split('@@').join(pre);
    for(const k in fills) s=s.split('{'+k+'}').join(fills[k]);
    return s;
  };
  Instance.prototype.build=function(){
    if(!ART){ this.container.innerHTML=''; return; }
    const a=this.appearance, u=this.uid, B=ART.body;
    const skin=colour('skin',a.skinColor,'Light');
    this._skin=skin; this._skinShown=skin;
    /* Hair greys with the age group: part way at middle, fully at older. Brows stay dark. */
    const grey=function(hex){ return a.ageGroup==='older'?mix(hex,'#E4DEDC',0.92):a.ageGroup==='middle'?mix(hex,'#A9A5A3',0.45):hex; };
    const fills={skin:skin, hair:grey(colour('hair',a.hairColor,'BrownDark')), hat:colour('fabric',a.hatColor,'Gray01'),
                 fhair:grey(colour('facialHair',a.facialHairColor,'BrownDark')), cloth:colour('fabric',a.clotheColor,'PastelBlue')};
    /* The torso is drawn three times: once whole and still, then a left and a right half on
       top, each its own rig pivoting at the base of the neck. Rotating the halves outward
       lifts the shoulders while the collar stays where it is, which is what shoulders do;
       stretching the whole torso, which this replaced, lifted the collar with them and read
       as a shirt being pulled. The still copy underneath fills whatever the halves uncover,
       including the bottom corners, so no gap can open at the window's edge. */
    const self=this;
    const torsoCopy=function(){
      let c=self.part('clothes',a.clotheType,fills);
      c=c.replace('<!--G-->', a.clotheType==='GraphicShirt'?self.part('graphic',a.graphicType,fills):'');
      return '<g clip-path="url(#'+u+'tc)"><use xlink:href="#'+u+'body" transform="translate(32,36)" fill="'+skin+'" data-skin="1"/></g>'
        +'<g data-layer="clothes">'+c+'</g>';
    };
    const fh=(ART.noFacialHair.indexOf(a.topType)>=0)?'':this.part('facialHair',a.facialHairType,fills);
    const acc=(ART.noAccessories.indexOf(a.topType)>=0)?'':this.part('accessories',a.accessoriesType,fills);
    const slot=n=>'<g data-slot="'+n+'"></g>';
    this.container.innerHTML=
    '<svg class="pt-svg" viewBox="0 0 264 280" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" role="img" aria-label="Patient">'
    +'<defs>'
    +  '<clipPath id="'+u+'frame"><path d="'+B.clip+'"/></clipPath>'
    +  '<clipPath id="'+u+'hc"><rect x="0" y="-40" width="264" height="226"/></clipPath>'
    +  '<clipPath id="'+u+'tc"><rect x="0" y="190" width="264" height="106"/><rect x="106" y="168" width="52" height="24"/></clipPath>'   /* shoulders, plus only the neck's width above them, so a tilted head never shows a second jaw */
    /* masks, not clip paths: a clip is applied to each child separately, so the skin under
       the cloth bled through along the cut as a hairline; a mask cuts the finished group. It also stops a hair short of the hem, for the same
       reason: the art's own layered bottom edge bleeds when it is turned */
    +  '<mask id="'+u+'hl" maskUnits="userSpaceOnUse" x="-80" y="120" width="424" height="240"><rect x="-80" y="120" width="212" height="158.6" fill="#fff"/></mask>'
    +  '<mask id="'+u+'hr" maskUnits="userSpaceOnUse" x="-80" y="120" width="424" height="240"><rect x="132" y="120" width="212" height="158.6" fill="#fff"/></mask>'
    +  '<path id="'+u+'body" d="'+B.body+'"/>'
    +  '<mask id="'+u+'bm"><use xlink:href="#'+u+'body" transform="translate(32,36)" fill="#fff"/></mask>'
    +'</defs>'
    /* Transparent by default: the figure stands in the room and the page crops it at the
       bottom edge. frame:'circle' is the original's disc, for a page with no room. */
    +'<g data-slot="backdrop">'+(this.frameStyle==='circle'?'<circle class="pt-disc" cx="132" cy="160" r="120"/>':'')+'</g>'
    +'<g'+(this.frameStyle==='circle'?' clip-path="url(#'+u+'frame)"':'')+'><g data-rig="figure">'
    +  slot('behind')
    +  '<g data-rig="torso">'
    +    torsoCopy()
    +    '<g data-rig="shoulderL"><g mask="url(#'+u+'hl)">'+torsoCopy()+'</g></g>'
    +    '<g data-rig="shoulderR"><g mask="url(#'+u+'hr)">'+torsoCopy()+'</g></g>'
    +    '<g mask="url(#'+u+'bm)"><path d="'+B.neck+'" transform="translate(32,36)" fill="#000" fill-opacity=".1"/></g>'
    +    slot('torso')
    +  '</g>'
    +  '<g data-rig="head">'
    +    '<g clip-path="url(#'+u+'hc)"><use xlink:href="#'+u+'body" transform="translate(32,36)" fill="'+skin+'" data-skin="1"/></g>'
    +    slot('underFace')
    +    '<g mask="url(#'+u+'bm)">'+slot('skin')+'</g>'
    +    '<g transform="translate(76,82)" fill="#000">'
    +      '<g data-rig="mouth" data-layer="mouth"></g>'
    +      '<g data-rig="nose" data-layer="nose">'+this.part('nose','',fills)+'</g>'
    +      '<g data-rig="eyes" data-layer="eyes"></g>'
    +      '<g data-rig="brows" data-layer="brows"></g>'
    +    '</g>'
    +    '<g transform="translate(-1,0)" data-layer="facialHair">'+fh+'</g>'
    +    slot('face')
    +    '<g data-layer="hair">'+this.part('top',a.topType,fills)+'</g>'
    +    slot('overHair')
    +    '<g transform="translate(-1,0)" data-layer="accessories">'+acc+'</g>'
    +    slot('front')
    +  '</g>'
    +  slot('overlay')
    +'</g></g></svg>';
    const root=this.container.firstChild;
    this.svg=root;
    this.rig={}; root.querySelectorAll('[data-rig]').forEach(g=>{ this.rig[g.getAttribute('data-rig')]=g; });
    this.layer={}; root.querySelectorAll('[data-layer]').forEach(g=>{ const n=g.getAttribute('data-layer'); (this.layer[n]=this.layer[n]||[]).push(g); });
    this.slot={}; root.querySelectorAll('[data-slot]').forEach(g=>{ this.slot[g.getAttribute('data-slot')]=g; });
    this.variants={eyes:{},brows:{},mouth:{}};
    this._shown={}; this._tf={}; this._hidden={};
    this.active.forEach(f=>{ f._mounted=null; });
    this.active=[]; this._dirty=true;
  };
  const POSE_GROUP={eyes:'eyes',brows:'eyebrow',mouth:'mouth'};
  Instance.prototype.show=function(which,name){
    if(this._shown[which]===name) return;
    const bank=this.variants[which];
    if(!bank[name]){
      const g=document.createElementNS('http://www.w3.org/2000/svg','g');
      g.innerHTML=this.part(POSE_GROUP[which],name,{});
      this.rig[which].appendChild(g); bank[name]=g;
    }
    for(const k in bank) bank[k].style.display = k===name?'':'none';
    this._shown[which]=name;
  };

  Instance.prototype.setAppearance=function(a){
    const next=normalizeAppearance(a).appearance;
    if(JSON.stringify(next)===JSON.stringify(this.appearance)) return;
    this.appearance=next; this.build();
  };
  Instance.prototype.setState=function(s){
    const key=JSON.stringify(s||{});
    if(key===this._stateKey) return;
    this._stateKey=key;
    this.state=normalizeState(s).state; this._dirty=true;
  };

  /* Which features are on. Built-ins follow the state; add-ons are named by it. */
  Instance.prototype.reconcile=function(){
    const st=this.state, want=['breathing','blink'];
    if(st.alertness>0) want.push('alertness');
    if(st.eyes==='closed') want.push('eyes_closed');
    if(st.seizure) want.push('seizure');
    if(this.appearance.build!=='average') want.push('habitus');
    if(this.appearance.ageGroup!=='young') want.push('age_lines');
    st.addons.forEach(n=>{ if(want.indexOf(n)<0) want.push(n); });
    const next=want.map(n=>FEATURES[n]).filter(Boolean).sort((p,q)=>p.priority-q.priority);
    this.active.forEach(f=>{ if(next.indexOf(f)<0) this.unmountFeature(f); });
    next.forEach(f=>{ if(this.active.indexOf(f)<0) this.mountFeature(f); });
    this.active=next;
    const hide={};
    next.forEach(f=>(f.hide||[]).forEach(l=>{ hide[l]=true; }));
    HIDEABLE.forEach(l=>{ (this.layer[l]||[]).forEach(g=>{ g.style.display=hide[l]?'none':''; }); });
    /* A feature may recolour the skin itself (jaundice). Done on the fills, not as an
       overlay, so the neck and the chest inside a collar change with the face and cloth
       never does. Features apply in priority order, each to the last one's result. */
    let tone=this._skin;
    next.forEach(f=>{ if(f.skin) tone=f.skin(tone,this); });
    if(tone!==this._skinShown){ this.svg.querySelectorAll('[data-skin]').forEach(e=>e.setAttribute('fill',tone)); this._skinShown=tone; }
    this._dirty=false;
    this.describe();
  };
  Instance.prototype.mountFeature=function(f){
    this._skinShown=null;        /* a feature may bring skin-coloured nodes; repaint the tone */
    const m=this.mem[f.name]=this.mem[f.name]||{};
    m.nodes=[];
    if(f.layers) for(const s in f.layers){
      if(!this.slot[s]) continue;
      const g=document.createElementNS('http://www.w3.org/2000/svg','g');
      g.setAttribute('data-feature',f.name);
      const src=typeof f.layers[s]==='function'?f.layers[s](this):f.layers[s];
      g.innerHTML=String(src).split('@@').join(this.uid+(this.n++)+'_');
      /* keep slot contents in priority order so two add-ons stack predictably */
      g._p=f.priority;
      const sibs=[].slice.call(this.slot[s].children);
      const before=sibs.find(x=>x._p>f.priority);
      this.slot[s].insertBefore(g,before||null);
      m.nodes.push(g);
    }
    if(f.enter) f.enter(this,m);
  };
  Instance.prototype.unmountFeature=function(f){
    const m=this.mem[f.name]||{};
    (m.nodes||[]).forEach(g=>{ if(g.parentNode) g.parentNode.removeChild(g); });
    if(f.exit) f.exit(this,m);
    delete this.mem[f.name];
  };
  /* What a screen reader is told. The same words a sighted learner would use, and no
     interpretation: "shaking", not "seizing". */
  Instance.prototype.describe=function(){
    const st=this.state, bits=['Patient'];
    const al=st.seizure?0:st.alertness;
    bits.push(st.eyes==='closed'||al===3?'eyes closed':al===2?'eyes closed, opening briefly to a sliver':al===1?'eyelids heavy, nodding off at times':'eyes open');
    if(al>=2) bits.push('head fallen to one side, jaw slack');
    if(st.eyes!=='closed'&&al<2&&st.distress>=2) bits.push(st.distress===3?'looks very distressed':'looks distressed');
    if(st.seizure) bits.push('rhythmic shaking of the whole body');
    if(st.respiratory_rate===0) bits.push('no chest movement');
    else if(st.work_of_breathing==='increased') bits.push('breathing with effort, mouth opening with each breath');
    else if(st.work_of_breathing==='severe') bits.push('breathing with marked effort, head bobbing, mouth open with each breath');
    this.active.forEach(f=>{ if(!f.builtin) bits.push(f.describe||f.label); });
    const label=bits.join(', ')+'.';
    if(label!==this._label&&this.svg){ this.svg.setAttribute('aria-label',label); this._label=label; }
  };

  Instance.prototype.frame=function(nowMs){
    if(!this.svg) return;
    if(this._dirty) this.reconcile();
    const dt=this.last===null?0:Math.min(100,Math.max(0,nowMs-this.last));
    this.last=nowMs; this.t+=dt;
    const st=this.state, a=this.appearance, ex=st.expression||{};
    const rr=st.respiratory_rate;
    /* an obtunded or unresponsive face is slack, whatever the distress was before it */
    const face=DISTRESS_FACE[(st.eyes==='closed'||(st.alertness>=2&&!st.seizure))?0:st.distress]||DISTRESS_FACE[0];
    const restMouth=(a.mouthType===DEFAULT_APPEARANCE.mouthType)?face.mouth:a.mouthType;
    const restBrows=(a.eyebrowType===DEFAULT_APPEARANCE.eyebrowType)?face.brows:a.eyebrowType;
    this.breathPhase=(this.breathPhase+dt/1000*rr/60)%1;
    const f={t:this.t, dt:dt, state:st, inst:this, reduced:REDUCED, rr:rr, phase:this.breathPhase,
      breath:rr>0?breathCurve(this.breathPhase,rr):0,
      ch:{figure:zero(),torso:zero(),shoulderL:zero(),shoulderR:zero(),head:zero(),eyes:zero(),brows:zero(),mouth:zero(),nose:zero()},
      pose:{eyes:ex.eyeType||a.eyeType, brows:ex.eyebrowType||restBrows, mouth:ex.mouthType||restMouth,
            mouthOpen:0, mouthOpenArt:'Disbelief'},
      mem:null, authored:{eyes:!!ex.eyeType,brows:!!ex.eyebrowType,mouth:!!ex.mouthType}};
    for(let i=0;i<this.active.length;i++){
      const feat=this.active[i];
      if(feat.tick){ f.mem=this.mem[feat.name]; feat.tick(f); }
    }
    /* mouth: a part-open mouth is the open drawing squashed, so opening is a motion and
       not a flicker between two pictures */
    if(f.pose.mouthOpen>0.12&&partSrc('mouth',f.pose.mouthOpenArt)!==undefined){
      this.show('mouth',f.pose.mouthOpenArt);
      f.ch.mouth.sy*=0.3+0.7*Math.min(1,f.pose.mouthOpen);
      f.ch.mouth.sx*=0.85+0.15*Math.min(1,f.pose.mouthOpen);
    } else this.show('mouth',f.pose.mouth);
    this.show('eyes',f.pose.eyes);
    this.show('brows',f.pose.brows);
    for(const name in this.rig){
      const c=f.ch[name], p=RIGS[name];
      const s='translate('+c.x.toFixed(2)+' '+c.y.toFixed(2)+') rotate('+c.rot.toFixed(2)+' '+p[0]+' '+p[1]+')'
        +((c.sx!==1||c.sy!==1)?' translate('+p[0]+' '+p[1]+') scale('+c.sx.toFixed(3)+' '+c.sy.toFixed(3)+') translate('+(-p[0])+' '+(-p[1])+')':'');
      if(this._tf[name]!==s){ this.rig[name].setAttribute('transform',s); this._tf[name]=s; }
    }
    this.lastFrame=f;
  };
  Instance.prototype.destroy=function(){
    const i=INSTANCES.indexOf(this); if(i>=0) INSTANCES.splice(i,1);
    if(this.container) this.container.innerHTML='';
    this.svg=null;
  };

  /* 0 at end-expiration, 1 at end-inspiration. Three parts, because a breath that is a
     plain sine reads as a machine. Inspiration is active and eased at both ends.
     Expiration is passive: it lets go quickly and then tails off. At resting rates a pause
     follows before the next breath; the pause shrinks as the rate climbs and is gone by 28,
     and inspiration takes a growing share, which is what a fast breather looks like. */
  function breathCurve(phase,rr){
    const tp=0.2*Math.min(1,Math.max(0,(28-rr)/16));
    const ti=Math.min(0.46,0.34+Math.max(0,rr-16)*0.004);
    if(phase<ti){ const x=phase/ti; return x*x*(3-2*x); }
    const u=(phase-ti)/(1-ti-tp);
    if(u>=1) return 0;
    return 0.5*(1+Math.cos(Math.PI*Math.pow(u,0.7)));
  }

  /* ---------- built-in features ---------- */
  register('breathing',{builtin:true,priority:0,tick:function(f){
    const w=WOB[f.state.work_of_breathing]||WOB.normal, k=f.reduced?0.5:1, b=f.breath;
    /* The shoulders rise and drop once per breath, at the monitor's rate. Each half of the
       torso turns outward about the base of the neck; `rise` is the travel of the shoulder
       tip, about 75 units out from that pivot. The chest also widens a little and the head
       rides up a touch, because nothing in a breathing body moves alone. With effort the
       nostrils flare on the way in. */
    const ang=Math.asin(Math.min(0.2,w.rise*b*k/75))*180/Math.PI;
    f.ch.shoulderL.rot+=ang; f.ch.shoulderR.rot-=ang;
    f.ch.torso.sx*=1+0.0035*w.rise*b*k;
    f.ch.torso.sy*=1+0.0020*w.rise*b*k;
    f.ch.nose.sx*=1+w.flare*b*k; f.ch.nose.sy*=1+w.flare*0.5*b*k;
    f.ch.head.y-=w.bob*b*k;
    f.ch.head.rot-=w.bob*0.5*b*k;                 /* chin lifts a little on the way in */
    if(w.open>0){
      /* open through inspiration, closing through expiration. If the case authored a
         mouth for this state it wins and only the motion is kept. */
      if(!f.authored.mouth){ f.pose.mouthOpen=Math.max(f.pose.mouthOpen,w.open*Math.pow(b,0.6)); f.pose.mouthOpenArt=w.art; }
      if(!f.authored.brows&&f.state.work_of_breathing==='severe') f.pose.brows='SadConcernedNatural';
    }
  }});
  register('blink',{builtin:true,priority:10,tick:function(f){
    const m=f.mem;
    if(m.next===undefined){ m.next=f.t+800+f.inst.rand()*2500; m.until=0; }
    if(f.t>=m.next){
      m.until=f.t+(f.state.alertness>=1?320:130);        /* heavy lids close slowly */
      /* one blink in six is a double */
      m.next=f.t+(f.inst.rand()<0.17?330:2400+f.inst.rand()*3800);
    }
    if(f.t<m.until) f.pose.eyes='Close';
  }});
  /* Reduced alertness, drawn from the level the phase already authors (authoring 6: alert,
     drowsy, obtunded, unresponsive; "eye state, responsiveness"). Four faces:
       0 alert         eyes open, ordinary blinks. This feature is not even mounted.
       1 drowsy        heavy upper lids, slow blinks, and every so often the lids close for
                       a second and the head nods forward before coming back.
       2 obtunded      eyes closed, opening to a sliver for a moment every several seconds;
                       head fallen a little to one side, jaw slack.
       3 unresponsive  eyes closed and staying closed, head to the side, jaw slack.
     An authored eyes:"closed" still simply closes the eyes at any level. A seizure, which
     runs later, puts the eyes back and clenches the jaw, so a seizing patient at level 3 is
     drawn seizing. The slack jaw never fights laboured breathing: mouthOpen takes the
     larger of the two. */
  register('alertness',{builtin:true,priority:15,tick:function(f){
    const lvl=f.state.alertness, m=f.mem, k=f.reduced?0.5:1, t=f.t/1000;
    if(lvl===1){
      if(m.nod===undefined){ m.nod=f.t+4000+f.inst.rand()*5000; m.nodEnd=0; }
      if(f.t>=m.nod){ m.nodEnd=f.t+1500; m.nod=f.t+6000+f.inst.rand()*7000; }
      const left=m.nodEnd-f.t;
      if(left>0){                                   /* the long blink and the nod */
        const u=1-left/1500, dip=u<0.7?Math.sin(u/0.7*Math.PI/2):1-(u-0.7)/0.3;
        f.ch.head.y+=2.6*dip*k; f.ch.head.rot+=2.2*dip*k;
        if(u<0.8) f.pose.eyes='Close';
      }
      if(f.pose.eyes!=='Close') f.pose.eyes='Drowsy';
      f.ch.head.rot+=0.7*Math.sin(t*0.9)*k; f.ch.head.y+=0.8;
      return;
    }
    /* 2 and 3 */
    f.ch.head.rot+=(lvl===3?5:3.5)+0.4*Math.sin(t*0.5)*k;
    f.ch.head.y+=lvl===3?2.2:1.6; f.ch.head.x+=lvl===3?2:1.2;
    f.pose.eyes='Close';
    if(lvl===2){
      if(m.peek===undefined){ m.peek=f.t+2500+f.inst.rand()*3000; m.peekEnd=0; }
      if(f.t>=m.peek){ m.peekEnd=f.t+1100; m.peek=f.t+5000+f.inst.rand()*5000; }
      if(f.t<m.peekEnd) f.pose.eyes='Heavy';
    }
    if(!f.authored.mouth){ f.pose.mouthOpen=Math.max(f.pose.mouthOpen,0.42); }
  }});
  register('eyes_closed',{builtin:true,priority:20,tick:function(f){ f.pose.eyes='Close'; }});
  register('seizure',{builtin:true,priority:30,tick:function(f){
    /* Rhythmic jerks near 3.5 Hz with a fine tremor on top, the whole body moving
       together and the head a little more than the rest. The envelope wanders so it
       never looks like a loop. Reduced motion keeps the sign and drops most of the
       travel. No luminance changes anywhere: this is movement, never a flash. */
    const k=f.reduced?0.3:1, t=f.t/1000;
    const env=0.75+0.25*Math.sin(t*0.9)+0.1*Math.sin(t*2.3);
    const jerk=Math.pow(Math.abs(Math.sin(t*Math.PI*3.5)),0.6)*(Math.sin(t*Math.PI*3.5)>=0?1:-1);
    const trem=Math.sin(t*2*Math.PI*9.3)*0.5+Math.sin(t*2*Math.PI*13.1)*0.3;
    f.ch.figure.x+=(jerk*2.6+trem*0.9)*env*k;
    f.ch.figure.y+=(Math.abs(jerk)*-1.2+trem*0.5)*env*k;
    f.ch.figure.rot+=(jerk*1.1)*env*k;
    f.ch.head.rot+=(jerk*1.6+trem*0.8)*env*k;
    f.ch.head.x+=trem*0.8*k;
    /* No blinking through a seizure: a blink written earlier this frame is undone unless
       the eyes are meant to be closed. */
    if(f.state.eyes!=='closed') f.pose.eyes=(f.state.expression&&f.state.expression.eyeType)||f.inst.appearance.eyeType;
    if(!f.authored.mouth){ f.pose.mouth='Grimace'; f.pose.mouthOpen=0; }
  }});

  /* ---------- add-ons ----------
     Worked examples of each kind, so the next one has something to copy.
     gaze and nystagmus need no artwork at all: they move the eyes rig. The nasal
     cannula is artwork in a slot. Its drawing is a placeholder to be replaced. */
  register('gaze_left',{label:'gaze deviated to the patient’s left',priority:60,
    tick:function(f){ f.ch.eyes.x+=4.5; }});
  register('gaze_right',{label:'gaze deviated to the patient’s right',priority:60,
    tick:function(f){ f.ch.eyes.x-=4.5; }});
  register('nystagmus',{label:'horizontal jerk nystagmus',priority:61,
    tick:function(f){ const p=(f.t/1000*3)%1;           /* slow drift, fast return, 3 Hz */
      f.ch.eyes.x+=(p<0.8?p/0.8:1-(p-0.8)/0.2)*3-1.5; }});
  register('nasal_cannula',{label:'nasal cannula in place',priority:50,layers:{
    face:'<g fill="none" stroke-linecap="round" stroke-linejoin="round">'
      +'<path d="M72 128 C92 146 112 143 124 140 M192 128 C172 146 152 143 140 140" stroke="#fff" stroke-opacity=".55" stroke-width="5"/>'
      +'<path d="M72 128 C92 146 112 143 124 140 L140 140 C152 143 172 146 192 128" stroke="#9fd8cf" stroke-width="2.6"/>'
      +'<path d="M127 140 v-4 M137 140 v-4" stroke="#9fd8cf" stroke-width="3"/></g>',
    torso:'<path d="M112 206 C120 232 128 246 132 262 C136 246 144 232 152 206" fill="none" stroke="#9fd8cf" stroke-width="2.4" stroke-linecap="round"/>'
  }});

  /* Corrugated tubing: a pale tube with ribs. One helper so the mask's hose and the
     ventilator circuit are the same object. */
  function hose(d,w){
    return '<path d="'+d+'" fill="none" stroke="#7d97a6" stroke-width="'+(w+1.6)+'" stroke-linecap="round"/>'
      +'<path d="'+d+'" fill="none" stroke="#e6eff4" stroke-width="'+w+'" stroke-linecap="round"/>'
      +'<path d="'+d+'" fill="none" stroke="#9db3c0" stroke-width="'+w+'" stroke-dasharray="1.4 3.2" stroke-opacity=".75"/>';
  }

  /* An oronasal mask for non-invasive ventilation. Clear shell, so the mouth still shows
     through it and a labouring patient is still seen to labour. Four-point headgear drawn
     over the hair, the shell and hose in front of everything, and glasses come off. */
  register('bipap_mask',{label:'face mask strapped over the nose and mouth, connected to tubing',priority:55,
    hide:['accessories'],
    layers:{
      overHair:'<g fill="none" stroke="#33434d" stroke-width="5.5" stroke-opacity=".9">'
        +'<path d="M116 132 C98 124 82 116 62 110"/><path d="M148 132 C166 124 182 116 202 110"/>'
        +'<path d="M108 168 C94 164 80 158 64 150"/><path d="M156 168 C170 164 184 158 200 150"/></g>',
      front:'<path d="M132 115 C122 115 118 126 113 140 C108 154 101 164 105 172 C108 179 120 181 132 181 C144 181 156 179 159 172 C163 164 156 154 151 140 C146 126 142 115 132 115 Z" fill="#ffffff" fill-opacity=".30" stroke="#bfe3ee" stroke-width="4.5" stroke-linejoin="round"/>'
        +'<path d="M132 115 C122 115 118 126 113 140 C108 154 101 164 105 172 C108 179 120 181 132 181 C144 181 156 179 159 172 C163 164 156 154 151 140 C146 126 142 115 132 115 Z" fill="none" stroke="#6f93a6" stroke-width="1"/>'
        +'<path d="M132 128 C126 128 123 136 120 146 C117 156 114 163 117 168 C120 172 126 173 132 173 C138 173 144 172 147 168 C150 163 147 156 144 146 C141 136 138 128 132 128 Z" fill="#ffffff" fill-opacity=".22" stroke="#6f93a6" stroke-width="1"/>'
        +'<path d="M121 124 C115 138 110 150 108 160" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="2" stroke-linecap="round"/>'
        +hose('M132 170 C132 196 118 222 123 292',9)
        +'<circle cx="132" cy="166" r="8" fill="#e9f1f5" stroke="#6f93a6" stroke-width="1.4"/><circle cx="132" cy="166" r="3.4" fill="#b8ccd6"/>'
    }});

  /* A non-rebreather: a soft clear mask with side ports, a thin elastic strap, a reservoir
     bag hanging from it and narrow green oxygen tubing. The mouth shows through. The bag
     swells a little as the patient breathes out and sags as they breathe in. */
  register('nonrebreather',{label:'oxygen mask with a reservoir bag over the nose and mouth',priority:54,
    layers:{
      face:'<path d="M110 138 C96 132 84 126 68 122 M154 138 C168 132 180 126 196 122" fill="none" stroke="#e9efe9" stroke-width="2.2" stroke-linecap="round"/>',
      front:'<g data-nrb-bag="1"><path d="M123 182 C117 184 115 192 115 204 L115 238 C115 250 121 256 132 256 C143 256 149 250 149 238 L149 204 C149 192 147 184 141 182 Z" fill="#dff3ea" fill-opacity=".55" stroke="#7fb9a3" stroke-width="1.2"/>'
        +'<path d="M121 196 C120 214 120 232 123 246" fill="none" stroke="#fff" stroke-opacity=".8" stroke-width="2" stroke-linecap="round"/></g>'
        +'<path d="M139 184 C150 200 158 236 154 292" fill="none" stroke="#5fae8f" stroke-width="2.6" stroke-linecap="round"/>'
        +'<path d="M132 120 C123 120 119 130 115 142 C111 153 106 162 110 169 C113 175 122 178 132 178 C142 178 151 175 154 169 C158 162 153 153 149 142 C145 130 141 120 132 120 Z" fill="#e8f7f0" fill-opacity=".42" stroke="#8fc7b2" stroke-width="2.2" stroke-linejoin="round"/>'
        +'<path d="M122 128 C117 140 113 150 112 158" fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="2" stroke-linecap="round"/>'
        +'<circle cx="118" cy="158" r="4.2" fill="#fff" fill-opacity=".7" stroke="#8fc7b2" stroke-width="1"/><circle cx="146" cy="158" r="4.2" fill="#fff" fill-opacity=".7" stroke="#8fc7b2" stroke-width="1"/>'
        +'<path d="M126 176 H138 V185 H126 Z" fill="#cfe9de" stroke="#7fb9a3" stroke-width="1"/>'
    },
    enter:function(inst,m){ m.bag=inst.svg.querySelector('[data-nrb-bag]'); },
    tick:function(f){
      if(!f.mem.bag) return;
      const s=(1.04-0.14*f.breath).toFixed(3);
      if(f.mem.s!==s){ f.mem.bag.setAttribute('transform','translate(132 182) scale('+s+' 1) translate(-132 -182)'); f.mem.s=s; }
    }});

  /* An endotracheal tube, taped at the lips and connected to a ventilator circuit. The
     drawn mouth is hidden and replaced by an opening around the tube, so no behaviour can
     make an intubated patient grimace or mouth-breathe. Whether the eyes are closed is
     the case's to say, not this add-on's. */
  register('intubated',{label:'breathing tube in the mouth, taped in place and connected to ventilator tubing',priority:56,
    hide:['mouth'],
    layers:{
      front:'<ellipse cx="134" cy="157" rx="8.5" ry="5.2" fill="#000" fill-opacity=".65"/>'
        +'<path d="M100 143 H164 a3 3 0 0 1 3 3 v4 a3 3 0 0 1 -3 3 H100 a3 3 0 0 1 -3 -3 v-4 a3 3 0 0 1 3 -3 Z" fill="#fff" fill-opacity=".93" stroke="#c9d3da" stroke-width=".8"/>'
        +'<path d="M137 166 C128 172 121 182 123 193" fill="none" stroke="#8fc3d6" stroke-width="1.1"/>'
        +'<ellipse cx="123" cy="197" rx="3" ry="4.6" fill="#cfeaf3" stroke="#8fc3d6" stroke-width=".9"/>'
        +'<path d="M134 155 L143 176" fill="none" stroke="#7d97a6" stroke-width="7.6" stroke-linecap="round"/>'
        +'<path d="M134 155 L143 176" fill="none" stroke="#f1f7fa" stroke-width="6" stroke-linecap="round"/>'
        +'<path d="M134.6 156 L143 176" fill="none" stroke="#4f9cc4" stroke-width="1"/>'
        +'<path d="M131 150 L139 147 L141 153 L133 156 Z" fill="#fff" stroke="#c9d3da" stroke-width=".8"/>'
        +hose('M147 186 C154 206 170 232 166 292',9)
        +'<path d="M140 173 L148 170 L153 184 L145 187 Z" fill="#4f9cc4" stroke="#2f6f92" stroke-width="1" stroke-linejoin="round"/>'
    }});

  /* ---------- who the patient is: build and age ----------
     Both belong to the appearance, not the state, so they are fixed for the case and are
     mounted from it; a case cannot switch them on as add-ons. Both are drawn on top of the
     same avataaars head, which has one face shape, so they work by suggestion.

     Build. Obese: a fuller lower face and a second chin under the first, drawn in the skin
     tone beneath the features, a slightly wider head, and a torso a good deal wider, which
     takes the neck with it. Thin: a slightly narrower head, a narrower torso and neck,
     hollows under the cheekbones, shadowed temples and the two cords of the neck. */
  register('habitus',{builtin:true,priority:2,
    layers:{
      underFace:function(inst){ return inst.appearance.build!=='obese'?'':
        '<path d="M70 132 C68 160 76 182 96 192 C108 199 120 201 132 201 C144 201 156 199 168 192 C188 182 196 160 194 132 Z" fill="'+inst._skin+'" data-skin="1"/>'
        +'<path d="M104 185 Q132 198 160 185" fill="none" stroke="#000" stroke-opacity=".16" stroke-width="2.2" stroke-linecap="round"/>'; },
      skin:function(inst){ return inst.appearance.build!=='thin'?'':
        '<g fill="#000" fill-opacity=".09"><path d="M92 132 C90 146 96 162 108 170 C104 158 104 144 106 134 Z"/><path d="M172 132 C174 146 168 162 156 170 C160 158 160 144 158 134 Z"/>'
        +'<ellipse cx="84" cy="98" rx="6" ry="12"/><ellipse cx="180" cy="98" rx="6" ry="12"/></g>'
        +'<path d="M122 187 L126 206 M142 187 L138 206" fill="none" stroke="#000" stroke-opacity=".14" stroke-width="2" stroke-linecap="round"/>'; }
    },
    tick:function(f){
      const o=f.inst.appearance.build==='obese';
      f.ch.torso.sx*=o?1.14:0.87; f.ch.head.sx*=o?1.06:0.93;
    }});
  /* Age. The hair greys in build(). Here, the lines: at middle age a forehead line and the
     folds from nose to mouth, faintly; at older age those deeper, a second and third
     forehead line, crow's feet and the lower lids. */
  register('age_lines',{builtin:true,priority:3,
    layers:{skin:function(inst){
      const old=inst.appearance.ageGroup==='older', o=old?'.22':'.12';
      let s='<g fill="none" stroke="#000" stroke-opacity="'+o+'" stroke-width="1.5" stroke-linecap="round">'
        +'<path d="M110 90 Q132 86 154 90"/><path d="M121 138 Q112 148 113 160"/><path d="M143 138 Q152 148 151 160"/>';
      if(old) s+='<path d="M114 82 Q132 78.5 150 82"/><path d="M116 97 Q132 94.5 148 97"/>'
        +'<path d="M91 108 L85 105 M91 112 L84 112 M91 116 L85 119"/><path d="M173 108 L179 105 M173 112 L180 112 M173 116 L179 119"/>'
        +'<path d="M98 122 Q106 126.5 114 122"/><path d="M150 122 Q158 126.5 166 122"/>';
      return s+'</g>'; }}});

  /* ---------- signs ---------- */
  /* Jaundice. The skin itself is recoloured toward yellow, and the eyes gain a yellowed
     sclera, which the stock eyes do not have at all: they are dots on skin. The sclera is
     the point. On the darker skins of the palette the skin change is slight, as it is in
     life, and the eyes are where it shows. Hidden whenever the eyes are not plainly open. */
  register('jaundice',{label:'skin and the whites of the eyes are yellow',priority:70,
    skin:function(hex){ return mix(hex,'#E2B31C',0.40); },
    layers:{skin:'<clipPath id="@@lid"><rect x="80" y="109.4" width="110" height="24"/></clipPath><g data-icterus="1"><ellipse cx="106" cy="112" rx="10" ry="6.6" fill="#F3DD6B"/><ellipse cx="158" cy="112" rx="10" ry="6.6" fill="#F3DD6B"/>'
      +'<ellipse cx="106" cy="112" rx="10" ry="6.6" fill="none" stroke="#000" stroke-opacity=".18" stroke-width=".8"/><ellipse cx="158" cy="112" rx="10" ry="6.6" fill="none" stroke="#000" stroke-opacity=".18" stroke-width=".8"/></g>'},
    enter:function(inst,m){ m.g=inst.svg.querySelector('[data-icterus]'); const c=inst.svg.querySelector('clipPath[id$="lid"]'); m.clip=c?'url(#'+c.id+')':''; },
    tick:function(f){
      if(!f.mem.g) return;
      const heavy=f.pose.eyes==='Drowsy';        /* under a heavy lid only the lower sclera shows */
      const open=heavy||(f.pose.eyes===f.inst.appearance.eyeType||f.pose.eyes==='Default'||f.pose.eyes==='Surprised');
      const d=open?'':'none';
      if(f.mem.d!==d){ f.mem.g.style.display=d; f.mem.d=d; }
      const cp=heavy?f.mem.clip:'';
      if(f.mem.cp!==cp){ if(cp) f.mem.g.parentNode.setAttribute('clip-path',cp); else f.mem.g.parentNode.removeAttribute('clip-path'); f.mem.cp=cp; }
      /* the sclera rides with the eyes rig so gaze and nystagmus do not leave it behind */
      const e=f.ch.eyes, tf='translate('+(e.x*0.35).toFixed(2)+' '+(e.y*0.35).toFixed(2)+')';
      if(f.mem.tf!==tf){ f.mem.g.setAttribute('transform',tf); f.mem.tf=tf; }
    }});

  /* Sweating. A sheen on the forehead and beads that form, run a short way and fade, each on
     its own clock so they never move together. Drawn under the hair, so a fringe covers the
     ones at the hairline. */
  (function(){
    const beads=[[96,84,0],[118,78,.37],[150,80,.71],[171,88,.18],[84,118,.55],[181,122,.86],[112,96,.62],[160,100,.29],[92,150,.45],[170,148,.08]];
    let svg='<ellipse cx="132" cy="84" rx="34" ry="9" fill="#fff" fill-opacity=".13"/>';
    beads.forEach(function(b,i){ svg+='<g data-bead="'+i+'"><path d="M0 -3.4 C1.9 -0.6 2.5 0.8 2.5 2 A2.5 2.5 0 0 1 -2.5 2 C-2.5 0.8 -1.9 -0.6 0 -3.4 Z" fill="#dff1fb" fill-opacity=".9" stroke="#6fa9c9" stroke-opacity=".55" stroke-width=".5"/><circle cx="-.8" cy="1.6" r=".7" fill="#fff"/></g>'; });
    register('sweating',{label:'sweating, beads of sweat on the forehead and face',priority:48,
      layers:{face:svg},
      enter:function(inst,m){ m.b=[].slice.call(inst.svg.querySelectorAll('[data-bead]')); },
      tick:function(f){
        if(!f.mem.b) return;
        for(let i=0;i<f.mem.b.length;i++){
          const b=beads[i], u=((f.t/1000)/(3.2+i*0.23)+b[2])%1;      /* 0 forms, 1 gone */
          const y=b[1]+(u<0.25?0:(u-0.25)/0.75*9*(f.reduced?0.3:1));
          const o=u<0.12?u/0.12:(u>0.8?(1-u)/0.2:1), sc=0.55+0.45*Math.min(1,u/0.25);
          f.mem.b[i].setAttribute('transform','translate('+b[0]+' '+y.toFixed(2)+') scale('+sc.toFixed(2)+')');
          f.mem.b[i].setAttribute('opacity',o.toFixed(2));
        }
      }});
  })();

  /* Agitation. Motion only. The head turns and will not settle, the eyes dart and hold,
     the body shifts, and the mouth works as if talking. Built from a few slow sines at
     unrelated periods plus held random targets, so it never repeats visibly and never
     looks rhythmic, which is what separates it from the seizure. */
  register('agitation',{label:'restless and not settling, head turning, eyes darting, mouth working',priority:25,
    tick:function(f){
      const k=f.reduced?0.35:1, t=f.t/1000, m=f.mem;
      if(m.next===undefined){ m.next=0; m.ex=0; m.ey=0; m.hx=0; m.cx=0; m.cy=0; m.chx=0; m.talk=0; m.talkTo=0; }
      if(f.t>=m.next){                       /* pick a new place to look, hold it a moment */
        m.ex=(f.inst.rand()*2-1)*4.2; m.ey=(f.inst.rand()*2-1)*1.6; m.hx=(f.inst.rand()*2-1);
        m.talkTo=f.inst.rand()<0.6?0.25+f.inst.rand()*0.5:0;
        m.next=f.t+350+f.inst.rand()*1100;
      }
      const ease=Math.min(1,f.dt/90);          /* saccade fast, head follows slower */
      m.cx+=(m.ex-m.cx)*ease; m.cy+=(m.ey-m.cy)*ease; m.chx+=(m.hx-m.chx)*Math.min(1,f.dt/320);
      m.talk+=(m.talkTo*(0.55+0.45*Math.sin(t*11))-m.talk)*Math.min(1,f.dt/70);
      f.ch.eyes.x+=m.cx*k; f.ch.eyes.y+=m.cy*k;
      f.ch.head.x+=(m.chx*3.2+Math.sin(t*1.7)*1.2)*k;
      f.ch.head.rot+=(m.chx*3.4+Math.sin(t*2.3+1)*1.4)*k;
      f.ch.head.y+=Math.sin(t*3.1)*0.9*k;
      f.ch.figure.x+=(Math.sin(t*0.8)*2.2+Math.sin(t*1.9+2)*1.1)*k;
      f.ch.figure.rot+=Math.sin(t*1.1+0.5)*1.1*k;
      f.ch.shoulderL.rot+=Math.max(0,Math.sin(t*2.6))*1.6*k; f.ch.shoulderR.rot-=Math.max(0,Math.sin(t*2.1+2))*1.6*k;
      if(!f.authored.brows) f.pose.brows='UpDownNatural';
      if(!f.authored.mouth&&m.talk>0.12){ f.pose.mouthOpen=Math.max(f.pose.mouthOpen,m.talk); f.pose.mouthOpenArt='Disbelief'; }
    }});

  /* ---------- more devices ---------- */
  /* Defibrillator and pacing pads, anterolateral. The sternal pad sits below the patient's
     right clavicle, which is the viewer's left; the apical pad is mostly below the frame
     and only its top edge shows. The shirt comes off while they are on. Cables run off
     the bottom. */
  register('defib_pads',{label:'shirt off, defibrillator pads on the bare chest',priority:52,
    hide:['clothes'],            /* pads go on skin. Every torso copy already draws the body under
                                    its cloth, in the current skin tone, so hiding the cloth bares
                                    the chest for any outfit and follows jaundice with no more work */
    layers:{torso:'<g stroke-linejoin="round">'
      +'<path d="M88 274 C89 280 90 286 90 294" fill="none" stroke="#5a6b76" stroke-width="2.2" stroke-linecap="round"/>'
      +'<g transform="translate(2 12) rotate(-14 86 240)"><rect x="66" y="220" width="40" height="46" rx="9" fill="#f7fafc" stroke="#3c78b4" stroke-width="1.6"/>'
      +'<rect x="70.5" y="224.5" width="31" height="37" rx="6" fill="none" stroke="#3c78b4" stroke-opacity=".35" stroke-width="1" stroke-dasharray="2 2"/>'
      +'<path d="M89 231 L80 245 H86 L83 256 L93 241 H87 Z" fill="#e8a317" stroke="#b37a08" stroke-width=".6"/></g>'
      +'<g transform="rotate(10 196 280)"><rect x="176" y="262" width="42" height="40" rx="9" fill="#f7fafc" stroke="#3c78b4" stroke-width="1.6"/>'
      +'<rect x="180.5" y="266.5" width="33" height="31" rx="6" fill="none" stroke="#3c78b4" stroke-opacity=".35" stroke-width="1" stroke-dasharray="2 2"/></g></g>'}});

  /* A central line in the patient's right internal jugular, the viewer's left: a clear
     dressing low on the neck, the catheter under it, and three lumens hanging over the
     collar. In the overlay slot so long hair does not bury it and a tilted head does not
     carry it off the neck. */
  register('central_line',{label:'central line in the right side of the neck, under a clear dressing',priority:53,
    layers:{overlay:'<g stroke-linecap="round" stroke-linejoin="round">'
      +'<path d="M112 196 C108 204 106 210 104 216" fill="none" stroke="#f4f7f9" stroke-width="2.4"/>'
      +'<path d="M104 216 C96 216 88 214 80 210" fill="none" stroke="#f4f7f9" stroke-width="1.8"/>'
      +'<path d="M104 216 C97 220 90 222 83 222" fill="none" stroke="#f4f7f9" stroke-width="1.8"/>'
      +'<path d="M104 216 C100 222 96 227 91 231" fill="none" stroke="#f4f7f9" stroke-width="1.8"/>'
      +'<rect x="73" y="206" width="8" height="6" rx="1.5" fill="#8a5a2b"/><rect x="76" y="219" width="8" height="6" rx="1.5" fill="#2f6fb5"/><rect x="84" y="229" width="8" height="6" rx="1.5" fill="#f4f7f9" stroke="#9aa9b3" stroke-width=".7"/>'
      +'<path d="M101 213 l6 3 l-3 5 l-6 -3 Z" fill="#2f6fb5"/>'
      +'<g transform="rotate(-18 112 198)"><rect x="101" y="186" width="24" height="26" rx="4" fill="#fff" fill-opacity=".34" stroke="#fff" stroke-opacity=".9" stroke-width="1.6"/>'
      +'<path d="M104 190 l5 -1" stroke="#fff" stroke-opacity=".8" stroke-width="1.2"/></g></g>'}});

  /* A bag-valve mask held on the face by a gloved hand in a C-E grip: thumb and index
     finger over the mask, three fingers along the jaw. The bag sits to the viewer's right
     and is squeezed as the chest rises, because with a bag on the face the breath on the
     monitor is the one being given. Glasses come off. */
  register('bag_valve_mask',{label:'bag-valve mask held on the face, the bag being squeezed with each breath',priority:57,
    hide:['accessories'],
    layers:{front:
      '<g data-bvm-bag="1"><ellipse cx="205" cy="160" rx="40" ry="24" fill="#4aa6b8" fill-opacity=".9" stroke="#2d7d8f" stroke-width="1.6"/>'
      +'<path d="M180 141 C176 153 176 167 180 179 M196 137 C192 152 192 168 196 183 M213 137 C217 152 217 168 213 183 M229 141 C233 153 233 167 229 179" fill="none" stroke="#2d7d8f" stroke-opacity=".55" stroke-width="1.3"/>'
      +'<ellipse cx="198" cy="150" rx="20" ry="6" fill="#fff" fill-opacity=".18"/></g>'
      +'<path d="M244 160 H262" stroke="#2d7d8f" stroke-width="9" stroke-linecap="round"/><path d="M256 160 H290" stroke="#cfe7ee" stroke-width="14" stroke-opacity=".7" stroke-linecap="round"/>'
      +'<path d="M140 160 H168" stroke="#e9f1f5" stroke-width="10" stroke-linecap="round"/><path d="M140 160 H168" fill="none" stroke="#6f93a6" stroke-width="10" stroke-opacity=".35" stroke-dasharray="1.2 3"/>'
      +'<path d="M132 116 C122 116 118 127 113 141 C108 154 102 164 106 172 C109 178 120 180 132 180 C144 180 155 178 158 172 C162 164 156 154 151 141 C146 127 142 116 132 116 Z" fill="#ffffff" fill-opacity=".36" stroke="#cfe7ee" stroke-width="5" stroke-linejoin="round"/>'
      +'<path d="M132 116 C122 116 118 127 113 141 C108 154 102 164 106 172 C109 178 120 180 132 180 C144 180 155 178 158 172 C162 164 156 154 151 141 C146 127 142 116 132 116 Z" fill="none" stroke="#6f93a6" stroke-width="1"/>'
      +'<circle cx="137" cy="160" r="8.5" fill="#e9f1f5" stroke="#6f93a6" stroke-width="1.4"/>'
      /* the hand: forearm in from the viewer's left, palm at the jaw, C over the mask, E under the jaw */
      +'<g fill="none" stroke-linecap="round" stroke-linejoin="round">'
      +'<path d="M30 214 C52 204 66 196 80 186" stroke="#5a9fd4" stroke-width="22"/>'
      +'<path d="M80 186 C88 180 94 176 100 172" stroke="#6fb2e2" stroke-width="20"/>'
      +'<path d="M96 184 C108 190 122 192 136 190" stroke="#6fb2e2" stroke-width="7.5"/><path d="M94 176 C106 183 120 186 134 184" stroke="#6fb2e2" stroke-width="7.5"/><path d="M93 168 C104 176 116 180 128 179" stroke="#6fb2e2" stroke-width="7.5"/>'
      +'<path d="M98 160 C106 146 118 136 131 131" stroke="#6fb2e2" stroke-width="8.5"/>'
      +'<path d="M100 170 C112 170 124 172 138 176" stroke="#6fb2e2" stroke-width="8.5"/>'
      +'<path d="M96 184 C108 190 122 192 136 190 M94 176 C106 183 120 186 134 184 M98 160 C106 146 118 136 131 131 M100 170 C112 170 124 172 138 176" stroke="#3f86bd" stroke-opacity=".45" stroke-width="1"/></g>'},
    enter:function(inst,m){ m.bag=inst.svg.querySelector('[data-bvm-bag]'); },
    tick:function(f){
      if(!f.mem.bag) return;
      const s=(1-0.34*f.breath).toFixed(3);
      if(f.mem.s!==s){ f.mem.bag.setAttribute('transform','translate(205 160) scale(1 '+s+') translate(-205 -160)'); f.mem.s=s; }
    }});

  /* ---------- the bed (a trial) ----------
     A stretcher with the head up, behind the patient: backrest and mattress, headboard,
     pillow, side rails. In the backdrop slot, so it is outside the figure rig and stays
     still while the patient breathes, nods or seizes against it. It is drawn well past the
     264 x 280 viewBox on purpose; the simulator's svg does not clip, so the bed runs on
     behind the panels and off the bottom of the window. `flat` draws the shapes alone, kept
     so the two stages can be compared. */
  function bedArt(flat){
    const mattress='M-40 306 L-47 44 Q-48 20 -24 20 L288 20 Q312 20 311 44 L304 306 Z';
    const pillow='M22 84 C18 60 34 50 58 50 L206 50 C230 50 246 60 242 84 L246 158 C248 182 232 190 208 190 L56 190 C32 190 16 182 18 158 Z';
    /* The side rails, as slender tube: one bent loop with two uprights, drawn as strokes and
       not as filled plastic, so the room and the sheet show through almost all of it. Every
       earlier version (slabs, then a moulded frame with openings) read as clunky; a rail this
       size on a real stretcher is a thin line at the edge of vision and that is what this is. */
    const rail=function(x,flip){ const t='translate('+x+' 0)'+(flip?' scale(-1 1)':'');
      const loop='M4 312 L4 196 Q4 176 20 176 Q36 176 36 196 L36 312', bars='M14.7 178 L14.7 312 M25.3 178 L25.3 312';
      return '<g transform="'+t+'" fill="none" stroke-linecap="round" stroke-linejoin="round">'
        +(flat?'':'<path d="'+loop+'" transform="translate(3 3)" stroke="#22333f" stroke-opacity=".18" stroke-width="5" filter="url(#@@soft)"/>')
        +'<path d="'+bars+'" stroke="'+(flat?'#cfcabd':'#c9c4b7')+'" stroke-width="2.2"/>'
        +'<path d="'+loop+'" stroke="'+(flat?'#d8d3c7':'#cdc8bb')+'" stroke-width="4.6"/>'
        +(flat?'':'<path d="'+loop+'" stroke="#fff" stroke-opacity=".75" stroke-width="1.4" transform="translate(-0.9 -0.6)"/>')
        +'</g>'; };
    let s='';
    if(!flat) s+='<defs>'
      +'<linearGradient id="@@mat" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fbfcfd"/><stop offset=".55" stop-color="#eef2f5"/><stop offset="1" stop-color="#dfe6eb"/></linearGradient>'
      +'<linearGradient id="@@matside" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#9fb0bb" stop-opacity=".55"/><stop offset=".07" stop-color="#9fb0bb" stop-opacity="0"/><stop offset=".93" stop-color="#9fb0bb" stop-opacity="0"/><stop offset="1" stop-color="#9fb0bb" stop-opacity=".55"/></linearGradient>'
      +'<radialGradient id="@@pil" cx=".5" cy=".42" r=".75"><stop offset="0" stop-color="#e3e9ee"/><stop offset=".45" stop-color="#f6f8fa"/><stop offset="1" stop-color="#ffffff"/></radialGradient>'
      +'<linearGradient id="@@head" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e6e1d6"/><stop offset="1" stop-color="#c9c3b5"/></linearGradient>'
      +'<linearGradient id="@@railin" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e9e5db"/><stop offset=".5" stop-color="#dcd7cb"/><stop offset="1" stop-color="#cbc5b7"/></linearGradient>'
      +'<filter id="@@soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="7"/></filter>'
      +'<filter id="@@softer" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="12"/></filter>'
      +'<clipPath id="@@matclip"><path d="'+mattress+'"/></clipPath><clipPath id="@@pilclip"><path d="'+pillow+'"/></clipPath></defs>';
    /* headboard: a slim rounded bar, narrower than the mattress, of which a sliver shows */
    s+='<path d="M24 40 L24 16 Q24 6 36 6 L228 6 Q240 6 240 16 L240 40 Z" fill="'+(flat?'#ddd8cc':'url(#@@head)')+'" stroke="#c4bdae" stroke-width="1"/>';
    if(!flat) s+='<path d="M30 14 Q30 10.5 36 10.5 L228 10.5 Q234 10.5 234 14" fill="none" stroke="#fff" stroke-opacity=".6" stroke-width="1.4"/>';
    /* backrest and mattress */
    if(!flat) s+='<path d="'+mattress+'" transform="translate(0 5)" fill="#2a3b47" fill-opacity=".22" filter="url(#@@soft)"/>';
    s+='<path d="'+mattress+'" fill="'+(flat?'#f1f4f6':'url(#@@mat)')+'" stroke="#cfd8de" stroke-width="1.6"/>';
    if(!flat){
      s+='<g clip-path="url(#@@matclip)"><path d="'+mattress+'" fill="url(#@@matside)"/>'
        /* the fitted sheet: long soft folds pulled toward the corners, each a shadow with a light edge beside it */
        +'<g fill="none" stroke-linecap="round">'
        +'<path d="M-40 70 C10 96 -6 170 -34 214" stroke="#8fa1ad" stroke-opacity=".30" stroke-width="5" filter="url(#@@soft)"/>'
        +'<path d="M306 70 C256 96 272 170 300 214" stroke="#8fa1ad" stroke-opacity=".30" stroke-width="5" filter="url(#@@soft)"/>'
        +'<path d="M-36 196 C-2 214 14 252 6 306 M-10 40 C0 70 -6 110 -30 140" stroke="#7f93a0" stroke-opacity=".34" stroke-width="7" filter="url(#@@soft)"/>'
        +'<path d="M300 196 C266 214 250 252 258 306 M274 40 C264 70 270 110 294 140" stroke="#7f93a0" stroke-opacity=".34" stroke-width="7" filter="url(#@@soft)"/>'
        +'<path d="M-30 196 C0 216 14 254 8 300 M-8 44 C2 72 -4 108 -26 136" stroke="#a9b8c2" stroke-opacity=".38" stroke-width="1.2"/>'
        +'<path d="M294 196 C264 216 250 254 256 300 M272 44 C262 72 268 108 290 136" stroke="#a9b8c2" stroke-opacity=".38" stroke-width="1.2"/></g>'
        /* where the pillow and the shoulders press into it */
        +'<ellipse cx="132" cy="197" rx="124" ry="15" fill="#2a3b47" fill-opacity=".24" filter="url(#@@soft)"/>'
        +'<ellipse cx="136" cy="268" rx="124" ry="62" fill="#22333f" fill-opacity=".34" filter="url(#@@softer)"/></g>';
    }
    /* pillow */
    s+='<path d="'+pillow+'" fill="'+(flat?'#ffffff':'url(#@@pil)')+'" stroke="#d3dbe1" stroke-width="1.6"/>';
    if(!flat){
      s+='<g clip-path="url(#@@pilclip)">'
        +'<ellipse cx="135" cy="126" rx="80" ry="74" fill="#22333f" fill-opacity=".30" filter="url(#@@softer)"/>'
        /* creases running out from under the head to the corners, and the piped seam */
        +'<g fill="none" stroke-linecap="round"><path d="M58 96 C44 86 34 74 28 60 M52 128 C40 128 28 124 18 116 M60 160 C48 170 36 178 24 186 M206 96 C220 86 230 74 236 60 M212 128 C224 128 236 124 246 116 M204 160 C216 170 228 178 240 186 M96 58 C92 54 90 52 88 50 M168 58 C172 54 174 52 176 50" stroke="#9db0bc" stroke-opacity=".45" stroke-width="1.5"/>'
        +'<path d="M60 94 C46 84 36 72 30 58 M54 125.6 C42 125.6 30 121.6 20 113.6 M62 158 C50 168 38 176 26 184 M204 94 C218 84 228 72 234 58 M210 125.6 C222 125.6 234 121.6 244 113.6 M202 158 C214 168 226 176 238 184" stroke="#fff" stroke-opacity=".8" stroke-width="1.3"/></g>'
        +'<path d="'+pillow+'" fill="none" stroke="#fff" stroke-width="7" stroke-opacity=".85"/><path d="'+pillow+'" fill="none" stroke="#b9c6cf" stroke-width="1" stroke-opacity=".45" transform="translate(132 120) scale(.955 .94) translate(-132 -120)"/></g>';
    }
    s+=rail(-80,false)+rail(344,true);
    return s;
  }
  register('hospital_bed',{label:'lying back on a stretcher with the head up, on a pillow',priority:1,layers:{backdrop:bedArt(false)}});
  register('hospital_bed_flat',{label:'stretcher, shapes only',priority:1,layers:{backdrop:bedArt(true)}});

  /* ---------- the clock ---------- */
  let PAUSED=false, RAF=0, REDUCED=false, VNOW=0, WALL=null;
  try{
    const mq=window.matchMedia('(prefers-reduced-motion: reduce)');
    REDUCED=mq.matches;
    (mq.addEventListener?mq.addEventListener.bind(mq,'change'):mq.addListener.bind(mq))(e=>{ REDUCED=e.matches; });
  }catch(e){}
  function loop(now){
    RAF=0;
    if(WALL!==null&&!PAUSED) VNOW+=Math.min(100,now-WALL);
    WALL=now;
    for(let i=0;i<INSTANCES.length;i++) INSTANCES[i].frame(VNOW);
    if(INSTANCES.length) RAF=requestAnimationFrame(loop);
  }
  function kick(){ if(!RAF&&typeof requestAnimationFrame!=='undefined'){ WALL=null; RAF=requestAnimationFrame(loop); } }

  function mount(container,appearance,state,opts){
    const i=new Instance(container,appearance,state,opts);
    INSTANCES.push(i); kick();
    return i;
  }

  return {
    mount:mount, register:register, registerPart:registerPart, baseFor:baseFor, ageGroupFor:ageGroupFor,
    setBases:function(b){ if(b&&typeof b==='object') BASES=b; },
    normalizeAppearance:normalizeAppearance, normalizeState:normalizeState,
    setPaused:function(b){ PAUSED=!!b; },
    setReducedMotion:function(b){ REDUCED=!!b; },
    available:!!ART,
    vocabulary:function(){
      const o={parts:{},colors:(ART&&ART.colors)||{},slots:SLOTS.slice(),hideable:HIDEABLE.slice(),
        work_of_breathing:Object.keys(WOB),eyes:['open','closed'],
        addons:Object.keys(FEATURES).filter(n=>!FEATURES[n].builtin),
        defaults:{appearance:JSON.parse(JSON.stringify(DEFAULT_APPEARANCE)),state:JSON.parse(JSON.stringify(DEFAULT_STATE))},
        builds:BUILDS.slice(),ageGroups:AGE_GROUPS.slice(),
        partKeys:PART_KEYS,colorKeys:COLOR_KEYS,topUses:(ART&&ART.topUses)||{}};
      for(const k in PART_KEYS) o.parts[k]=optionsOf(PART_KEYS[k]);
      return o;
    },
    _breathCurve:breathCurve
  };
})();
