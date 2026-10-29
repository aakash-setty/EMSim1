/* ---------- procedure view (28 October 2026) ----------
   Draws a procedure pack in three.js and turns the learner's pointer and buttons into calls
   on the procedure engine (procsim-core.js). Loaded only when a procedure is opened, with
   three.js, as one file (see engine/procedures.js).

   What the learner sees:
     - the neck, built layer by layer from the pack, with a layers panel: each group can be
       hidden, the skin and fat can be made see-through, and a midline cut shows the depth;
     - a tool tray from the pack's tools;
     - a step card: in Learn the step, its prompt and why; in Practice only "What next?";
     - a readout of what the instrument tip is in: the layer's name in Learn, only what it
       feels like in Practice;
     - a debrief at the end.

   Nothing here names a procedure or a structure. Tool behavior follows the tool's kind
   (finger, blade, rod, tube, syringe, bag). */
const PXVIEW = (function(){
  const esc=t=>String(t==null?'':t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const SPEED={blade:6, rod_in:10, rod:35, tube:25, syringe:3};   /* mm or mL per second */

  const CSS=`
.pxs{position:fixed;inset:0;z-index:130;display:grid;grid-template-rows:auto 1fr auto;background:#0f1a22;color:var(--ink);font-family:var(--sans)}
.pxs *{box-sizing:border-box}
.pxs-top{display:flex;align-items:center;gap:12px;padding:10px 16px;background:var(--solid);border-bottom:1px solid var(--rule)}
.pxs-title{font-weight:750;font-size:16px}
.pxs-pill{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:3px 9px;border-radius:999px;background:var(--actl);color:var(--act);border:1px solid var(--actb)}
.pxs-pill.pr{background:var(--warnl);color:var(--warn);border-color:var(--warn)}
.pxs-time{font-family:var(--mono);font-size:14px;color:var(--ink2);margin-left:auto}
.pxs-btn{font:inherit;font-size:13px;font-weight:650;padding:7px 12px;border-radius:9px;border:1px solid var(--rule);background:var(--solid);color:var(--ink);cursor:pointer}
.pxs-btn:hover{border-color:var(--actb)}
.pxs-btn:focus-visible{outline:2px solid var(--act);outline-offset:2px}
.pxs-btn.pri{background:var(--act);color:#fff;border-color:var(--act)}
.pxs-btn.hold{min-width:92px;user-select:none;-webkit-user-select:none;touch-action:none}
.pxs-btn.hold.on{background:var(--act);color:#fff}
.pxs-btn[aria-pressed="true"]{background:var(--actl);border-color:var(--act);color:var(--act)}
.pxs-btn.glow{box-shadow:0 0 0 3px var(--actb)}
.pxs-mid{position:relative;min-height:0}
.pxs-canvas{position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:none}
.pxs-card{position:absolute;left:14px;top:14px;width:min(360px,calc(100% - 28px));max-height:calc(100% - 28px);overflow:auto;
  background:var(--solid);border:1px solid var(--rule);border-radius:14px;padding:14px 14px 12px;box-shadow:0 18px 40px -20px rgba(0,0,0,.55)}
.pxs-n{font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink3)}
.pxs-h{font-size:17px;font-weight:750;margin:3px 0 6px;line-height:1.25}
.pxs-p{font-size:14px;line-height:1.45;margin:0 0 8px;color:var(--ink)}
.pxs-why{font-size:12.5px;line-height:1.45;color:var(--ink2);margin:0 0 8px}
.pxs-why summary{cursor:pointer;color:var(--act);font-weight:650}
.pxs-fb{font-size:13.5px;line-height:1.4;padding:8px 10px;border-radius:9px;margin:6px 0 8px;display:none}
.pxs-fb.on{display:block}
.pxs-fb.error{background:var(--harml);color:var(--harm);border:1px solid var(--harmb)}
.pxs-fb.ok{background:var(--okl);color:var(--ok)}
.pxs-fb.info{background:var(--actl);color:var(--ink)}
.pxs-acts{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.pxs-acts .pxs-btn{text-align:left}
.pxs-acts.many .pxs-btn{font-size:12.5px;padding:5px 9px;font-weight:600}
.pxs-card[hidden]{display:none}
.pxs-grp{font-size:12px;color:var(--ink3);margin:8px 0 2px;width:100%}
.pxs-ctl{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;align-items:center}
.pxs-hands{font-size:12px;color:var(--ink2);margin-top:8px}
.pxs-steps{margin:10px 0 0;padding:0 0 0 18px;font-size:12.5px;color:var(--ink2)}
.pxs-steps li.done{color:var(--ok)}
.pxs-steps li.cur{color:var(--ink);font-weight:700}
.pxs-read{position:absolute;left:50%;top:14px;transform:translateX(-50%);background:rgba(15,26,34,.82);color:#eaf2f7;
  padding:7px 14px;border-radius:999px;font-size:13.5px;pointer-events:none;max-width:min(560px,60vw);text-align:center;display:none}
.pxs-read.on{display:block}
.pxs-read b{font-family:var(--mono);color:#9fd3ff;margin-right:8px}
.pxs-layers{position:absolute;right:14px;top:14px;width:230px;background:var(--solid);border:1px solid var(--rule);border-radius:14px;padding:12px;
  font-size:13px;box-shadow:0 18px 40px -20px rgba(0,0,0,.55)}
.pxs-layers[hidden]{display:none}
.pxs-layers h3{margin:0 0 6px;font-size:13px;font-weight:750}
.pxs-layers label{display:flex;align-items:center;gap:8px;padding:3px 0;cursor:pointer}
.pxs-sw{width:12px;height:12px;border-radius:3px;border:1px solid var(--rule)}
.pxs-layers input[type=range]{width:100%}
.pxs-tray{display:flex;gap:8px;padding:10px 14px;background:var(--solid);border-top:1px solid var(--rule);overflow-x:auto}
.pxs-tool{display:flex;flex-direction:column;align-items:flex-start;gap:2px;min-width:132px;padding:8px 10px;border-radius:10px;border:1px solid var(--rule);
  background:var(--solid);color:var(--ink);font:inherit;cursor:pointer;text-align:left}
.pxs-tool b{font-size:13px}
.pxs-tool span{font-size:11.5px;color:var(--ink3);line-height:1.3}
.pxs-tool[aria-pressed="true"]{border-color:var(--act);background:var(--actl)}
.pxs-tool.glow{border-color:var(--act);background:var(--actl);animation:pxsglow 1.3s ease-in-out infinite}
.pxs-tool.glow b::before{content:"Pick up";display:inline-block;margin-right:6px;padding:1px 6px;border-radius:999px;background:var(--act);color:#fff;
  font-size:10px;letter-spacing:.06em;text-transform:uppercase;vertical-align:1px}
@keyframes pxsglow{0%,100%{box-shadow:0 0 0 2px var(--actb),0 0 14px 2px rgba(31,111,178,.25)}50%{box-shadow:0 0 0 5px var(--actb),0 0 26px 8px rgba(31,111,178,.45)}}
@media (prefers-reduced-motion:reduce){.pxs-tool.glow{animation:none;box-shadow:0 0 0 4px var(--actb)}}
.pxs-rot{display:inline-flex;flex-direction:column;align-items:center;gap:3px;width:78px;padding:8px 4px 6px;border-radius:14px;border:1px solid var(--rule);
  background:var(--solid);color:var(--act);font:inherit;font-size:11.5px;font-weight:650;cursor:pointer}
.pxs-rot svg{width:40px;height:40px}
.pxs-rot span{color:var(--ink2)}
.pxs-rot:hover{border-color:var(--act);background:var(--actl)}
.pxs-rot:focus-visible{outline:2px solid var(--act);outline-offset:2px}
.pxs-pick{margin:8px 0;padding:9px 11px;border-radius:10px;background:var(--actl);border:1px solid var(--actb);font-size:13.5px;line-height:1.4}
.pxs-pick b{color:var(--act)}
.pxs-hold{font-size:12.5px;color:var(--ink2);margin-top:6px}
.pxs-capno{position:absolute;right:14px;bottom:14px;background:#0b141a;border:1px solid #23404f;border-radius:10px;padding:6px 8px;color:#ffe46b;font-family:var(--mono);font-size:11px}
.pxs-capno[hidden]{display:none}
.pxs-deb{position:absolute;inset:0;display:grid;place-items:center;background:rgba(8,20,30,.55);padding:16px;z-index:5}
.pxs-debc{width:min(720px,100%);max-height:calc(100% - 16px);overflow:auto;background:var(--solid);border-radius:18px;padding:22px 24px;box-shadow:0 40px 90px -30px rgba(0,0,0,.6)}
.pxs-debc h2{margin:0 0 4px;font-size:22px}
.pxs-stats{display:flex;gap:18px;flex-wrap:wrap;margin:12px 0}
.pxs-stat b{display:block;font-family:var(--mono);font-size:22px}
.pxs-stat span{font-size:12px;color:var(--ink2)}
.pxs-debc ol{padding-left:20px;font-size:13.5px;line-height:1.5}
.pxs-debc li.bad{color:var(--harm)}
.pxs-debc .src{font-size:12px;color:var(--ink2)}
.pxs-start{position:absolute;inset:0;display:grid;place-items:center;background:rgba(8,20,30,.55);padding:16px;z-index:6}
.pxs-startc{width:min(520px,100%);background:var(--solid);border-radius:18px;padding:22px 24px}
.pxs-startc h2{margin:0 0 6px;font-size:21px}
.pxs-startc p{font-size:14px;line-height:1.45;color:var(--ink2);margin:0 0 12px}
.pxs-seg{display:flex;gap:8px;margin:0 0 14px;flex-wrap:wrap}
.pxs-seg .pxs-btn{flex:1;min-width:150px;text-align:left}
.pxs-seg .pxs-btn small{display:block;font-weight:500;color:var(--ink2);margin-top:2px}
.pxs-note{font-size:12px;color:var(--ink3);line-height:1.4}
@media (max-width:760px){ .pxs-layers{top:auto;bottom:14px;width:200px} .pxs-card{width:calc(100% - 28px);max-height:42%} }
`;
  let styled=false;
  function style(){ if(styled) return; styled=true; const s=document.createElement('style'); s.textContent=CSS; document.head.appendChild(s); }

  function open(cfg){
    style();
    const pack=cfg.pack, root=cfg.host;
    const tools={}; (pack.tools||[]).forEach(t=>tools[t.id]=t);
    const groups=pack.groups||[];
    root.innerHTML='';
    root.className='pxs'; root.setAttribute('role','dialog'); root.setAttribute('aria-modal','true'); root.setAttribute('aria-label',pack.card.title);
    root.innerHTML=`
      <div class="pxs-top">
        <span class="pxs-title">${esc(pack.card.title)}</span>
        <span class="pxs-pill" id="pxs-mode"></span>
        <span class="pxs-time" id="pxs-time">00:00</span>
        <button class="pxs-btn" type="button" id="pxs-lay" aria-pressed="true">Layers</button>
        <button class="pxs-btn" type="button" id="pxs-reset">Reset view</button>
        <button class="pxs-btn" type="button" id="pxs-exit">Exit</button>
      </div>
      <div class="pxs-mid" id="pxs-mid">
        <canvas class="pxs-canvas" id="pxs-cv" aria-label="Three-dimensional model of the neck. Drag to turn it, scroll to zoom."></canvas>
        <div class="pxs-read" id="pxs-read" aria-live="polite"></div>
        <div class="pxs-card" id="pxs-card"></div>
        <div class="pxs-layers" id="pxs-layers"></div>
        <div class="pxs-capno" id="pxs-capno" hidden><div>EtCO2</div><canvas width="220" height="64" id="pxs-capcv"></canvas></div>
      </div>
      <div class="pxs-tray" id="pxs-tray" role="toolbar" aria-label="Instruments"></div>`;
    const $=id=>root.querySelector('#'+id);

    /* ---- three ---- */
    const canvas=$('pxs-cv');
    let renderer;
    try{ renderer=new THREE.WebGLRenderer({canvas, antialias:true, stencil:true}); }
    catch(e){ root.innerHTML='<div class="pxs-top"><span class="pxs-title">'+esc(pack.card.title)+'</span></div><div class="pxs-mid" style="display:grid;place-items:center;color:#fff;padding:20px">This browser could not start 3D graphics (WebGL), which the procedure needs. Try a current browser with hardware acceleration on.</div>';
              setTimeout(()=>{ root.hidden=true; root.innerHTML=''; cfg.onClose&&cfg.onClose(); }, 6000); return null; }
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio||1));
    renderer.localClippingEnabled=true;
    const scene=new THREE.Scene();
    scene.background=new THREE.Color('#1b2a35');
    const camera=new THREE.PerspectiveCamera(36, 1, 5, 4000);
    scene.add(new THREE.HemisphereLight(0xf2f6ff, 0x3a2a24, 1.15));
    const key=new THREE.DirectionalLight(0xffffff, 1.6); key.position.set(120, 260, 80); scene.add(key);
    const fill=new THREE.DirectionalLight(0xdfe8ff, 0.55); fill.position.set(-160, 120, -120); scene.add(fill);
    const G=PXGEOM.build(pack);
    /* The pack's x runs to the patient's left, which with y anterior and z to the head is a
       left-handed frame. three.js draws right-handed, so everything of the patient's goes in
       one group mirrored in x. Without it the model would be drawn as its mirror image, and
       "clockwise seen from above" would turn the wrong way. Pointer hits are mirrored back. */
    const world=new THREE.Group(); world.scale.x=-1; scene.add(world);
    world.add(G.root);
    /* A bed under the patient, and drapes over everything outside the pack's field. */
    const scenery=[];
    const bed=new THREE.Mesh(new THREE.BoxGeometry(640, 6, 1300), new THREE.MeshStandardMaterial({color:'#d9e2e8', roughness:0.95}));
    const TABLE=(pack.table_y!=null?pack.table_y:-44);
    bed.position.set(0, TABLE-3, -220); world.add(bed); scenery.push(bed);
    /* Drapes: one cloth over everything outside the pack's field, lying on the skin and on
       the body beyond it, with the field as a window. A height field from the skin, so the
       chest and the jaw show their shape under the cloth. */
    if(pack.field && pack.field.z){
      const [z0,z1]=pack.field.z;
      /* The window: a polygon of [x, z] points if the pack gives one, otherwise a rectangle. */
      const win=pack.field.window || [[-(pack.field.x||70),z0],[pack.field.x||70,z0],[pack.field.x||70,z1],[-(pack.field.x||70),z1]];
      const fx=Math.max(...win.map(p=>Math.abs(p[0])));
      const inWin=(x,z)=>{ let c=false; for(let i=0,j=win.length-1;i<win.length;j=i++){ const [xi,zi]=win[i], [xj,zj]=win[j];
        if(((zi>z)!==(zj>z)) && (x<(xj-xi)*(z-zi)/(zj-zi)+xi)) c=!c; } return c; };
      const skinRay=new THREE.Raycaster(), down=new THREE.Vector3(0,-1,0);
      /* The extent along z of everything the drape rests on. */
      const box=new THREE.Box3(); G.drapeMeshes.forEach(m=>box.expandByObject(m));
      const zmin=box.min.z, zmax=box.max.z;
      const topAt=(x,z)=>{ skinRay.set(new THREE.Vector3(x,400,Math.max(zmin+0.5,Math.min(zmax-0.5,z))), down);
        const h=skinRay.intersectObjects(G.drapeMeshes,false)[0]; return h?h.point.y:null; };
      /* A grid whose lines fall exactly on the window's edges, so the edge is straight. */
      /* Grid lines fall exactly on the window's edges, 4 mm apart near the field and 10 mm
         apart far from it, where the cloth only has to show the body's shape. */
      const axis=(lo,hi,a,b)=>{ const out=[]; const n=Math.max(1,Math.round((b-a)/4)), d=(b-a)/n;
        for(let k=0;k<=n;k++) out.push(+(a+k*d).toFixed(3));
        for(let v=a, st=4; v>lo; ){ st=(a-v)>70?10:4; v-=st; out.unshift(+Math.max(lo,v).toFixed(3)); }
        for(let v=b, st=4; v<hi; ){ st=(v-b)>70?10:4; v+=st; out.push(+Math.min(hi,v).toFixed(3)); }
        return out; };
      const xs=axis(-300,300,-fx,fx), zs=axis(zmin-60,zmax+60,z0,z1), nx=xs.length, nz=zs.length;
      const H=new Float32Array(nx*nz), S=new Float32Array(nx*nz).fill(-1e9);
      for(let j=0;j<nz;j++) for(let i=0;i<nx;i++){
        const x=xs[i], z=zs[j], t=topAt(x,z), k=j*nx+i;
        /* Off the body the cloth slopes to the bed. Under it the cloth rests on the skin. */
        H[k]= t==null ? TABLE+4 : t+3.5;
        /* Past the ends of the model the body falls away under the cloth. */
        const dz=z<zmin?zmin-z:z>zmax?z-zmax:0;
        if(dz>0 && t!=null) H[k]=Math.max(TABLE+5, H[k]-(H[k]-TABLE)*(1-Math.cos(Math.min(1,dz/110)*Math.PI/2)));
        if(t!=null) S[k]=t+2.2;
      }
      /* The cloth tents over steep sides: each point rests on the highest skin near it. */
      { const S0=S.slice();
        for(let j=0;j<nz;j++) for(let i=0;i<nx;i++){ let m=S0[j*nx+i];
          for(let dj=-1;dj<=1;dj++) for(let di=-1;di<=1;di++){ const jj=j+dj, ii=i+di; if(jj<0||ii<0||jj>=nz||ii>=nx) continue;
            m=Math.max(m, S0[jj*nx+ii]-0.6*Math.hypot(di,dj)*4*0.35); }
          S[j*nx+i]=m; H[j*nx+i]=Math.max(H[j*nx+i], m+1.2); } }
      /* Let the cloth fall softly: smooth it, never through the skin. */
      for(let it=0; it<3; it++){
        const N=H.slice();
        for(let j=1;j<nz-1;j++) for(let i=1;i<nx-1;i++){ const k=j*nx+i;
          N[k]=Math.max(S[k], (H[k]*4+H[k-1]+H[k+1]+H[k-nx]+H[k+nx])/8); }
        H.set(N);
      }
      const pos=new Float32Array(nx*nz*3);
      for(let j=0;j<nz;j++) for(let i=0;i<nx;i++){ const k=j*nx+i, x=xs[i], z=zs[j];
        const onEdge=!inWin(x,z) && [[4,0],[-4,0],[0,4],[0,-4],[8,0],[-8,0]].some(([dx,dz])=>inWin(x+dx,z+dz));
        /* A vertex just outside a slanted edge moves onto it, so the edge is a line and not a
           staircase. */
        let xx=x;
        if(onEdge){ const xs2=[]; for(let a=0,b=win.length-1;a<win.length;b=a++){ const [xa,za]=win[a],[xb,zb]=win[b];
            if((za>z)!==(zb>z)) xs2.push(xa+(xb-xa)*(z-za)/(zb-za)); }
          for(const xe of xs2) if(Math.abs(x-xe)<8.01){ xx=xe; break; } }
        pos[k*3]=xx; pos[k*3+1]=H[k]-(onEdge?1.2:0); pos[k*3+2]=z; }
      const idx=[];
      for(let j=0;j<nz-1;j++) for(let i=0;i<nx-1;i++){
        const cx=(xs[i]+xs[i+1])/2, cz=(zs[j]+zs[j+1])/2;
        if(inWin(cx,cz)) continue;      /* the window */
        const a=j*nx+i, b=a+1, c=a+nx, d=c+1; idx.push(a,c,b, b,c,d);
      }
      const g=new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(pos,3)); g.setIndex(idx); g.computeVertexNormals();
      const drape=new THREE.Mesh(g, new THREE.MeshStandardMaterial({color:'#3a8a8f', roughness:0.95, side:THREE.DoubleSide}));
      world.add(drape); scenery.push(drape);
    }
    const clip=new THREE.Plane(new THREE.Vector3(-1,0,0), 0);
    const mats=[];
    G.root.traverse(o=>{ if(o.isMesh && mats.indexOf(o.material)<0) mats.push(o.material); });
    mats.forEach(m=>{ m.userData.baseOpacity=m.opacity; });
    /* Section caps for the midline cut. The layers are hollow shells, so a cut shows their
       insides. For each solid layer, its faces behind the cut toggle a stencil bit wherever
       they are drawn; an odd count means that pixel of the cut lies inside the layer, and a
       plane in the layer's color is drawn there. The parity test does not care which way
       the faces wind. The air layer gets no cap: it is the space the cut should show. */
    const caps=[];
    { let order=1;
      for(const L of G.layers){
        const cg=new THREE.Group(); cg.visible=false;
        for(const mesh of G.groups[L.id].children){
          const sm=new THREE.Mesh(mesh.geometry, new THREE.MeshBasicMaterial({side:THREE.DoubleSide, depthWrite:false, depthTest:false,
            colorWrite:false, stencilWrite:true, stencilFunc:THREE.AlwaysStencilFunc, stencilFail:THREE.InvertStencilOp,
            stencilZFail:THREE.InvertStencilOp, stencilZPass:THREE.InvertStencilOp, clippingPlanes:[clip]}));
          sm.renderOrder=order; cg.add(sm);
        }
        /* The air layer's cap is dark: it is the space inside the airway, drawn over the deep
           tissue cap behind it. Caps are drawn in pack order, so later layers win. */
        const plane=new THREE.Mesh(new THREE.PlaneGeometry(700, 700), new THREE.MeshStandardMaterial({color:L.air?'#26343e':(L.color||'#ccc'), roughness:0.85,
          side:THREE.DoubleSide, stencilWrite:true, stencilRef:0, stencilFunc:THREE.NotEqualStencilFunc,
          stencilFail:THREE.ReplaceStencilOp, stencilZFail:THREE.ReplaceStencilOp, stencilZPass:THREE.ReplaceStencilOp}));
        plane.rotation.y=Math.PI/2; plane.renderOrder=order+0.5;
        plane.onAfterRender=r=>r.clearStencil();
        cg.add(plane); world.add(cg);
        caps.push({L, cg}); order+=1;
      }
    }

    const controls=new THREE.OrbitControls(camera, canvas);
    controls.enableDamping=true; controls.dampingFactor=0.12; controls.enablePan=false;
    controls.minDistance=70; controls.maxDistance=1700;
    controls.minPolarAngle=0.12; controls.maxPolarAngle=Math.PI*0.62;
    function resetView(){
      const s=sim.state.side==='right'?-1:1;
      camera.position.set(-s*250, 330, -190);    /* world x is the pack's x mirrored */
      controls.target.set(0, 0, 45); controls.update();
    }

    /* ---- the engine ---- */
    let sim=null, mode=cfg.mode, hand=cfg.hand;
    const view={tool:null, preEdge:'-z', twist:true, msg:null, hold:null, cut:false, see:1, hidden:{}, readout:'', startedAt:0, ended:false};

    /* ---- instruments ---- */
    const toolObj={};
    function mat(c,o){ return new THREE.MeshStandardMaterial({color:c, roughness:0.4, metalness:0.15, transparent:o<1, opacity:o==null?1:o}); }
    /* finger */
    const finger=new THREE.Group();
    { const tip=new THREE.Mesh(new THREE.SphereGeometry(6.5, 20, 14), mat('#e2b08f', 0.92));
      const shaft=new THREE.Mesh(new THREE.CylinderGeometry(7.5, 8.5, 70, 18), mat('#e2b08f', 0.92));
      shaft.position.y=36; finger.add(tip); finger.add(shaft); finger.visible=false; world.add(finger); }
    /* blade: built pointing down, cutting edge on +x */
    const blade=new THREE.Group();
    { const T=Object.values(tools).find(t=>t.kind==='blade')||{}; const L=T.blade_len||38, W=T.blade_w||8;
      const steel=new THREE.Mesh(new THREE.BoxGeometry(W, L, 0.7), mat('#c9d3da'));
      steel.position.set(0, L/2, 0);
      const edge=new THREE.Mesh(new THREE.BoxGeometry(0.9, L-4, 1.2), new THREE.MeshBasicMaterial({color:'#e5332a'}));
      edge.position.set(W/2+0.2, L/2+2, 0);
      const handle=new THREE.Mesh(new THREE.BoxGeometry(9, 90, 5), mat('#33424c'));
      handle.position.set(-1, L+45, 0);
      blade.add(steel); blade.add(edge); blade.add(handle); blade.visible=false; world.add(blade); }
    const slit=new THREE.Mesh(new THREE.BoxGeometry(9, 0.6, 1.2), new THREE.MeshBasicMaterial({color:'#5b1712'}));
    slit.visible=false; world.add(slit);
    const rodMat=mat('#e8dcc0'), tubeMat=mat('#f4f7f9', 0.82), cuffMat=mat('#d6ecff', 0.7);
    let rodMesh=null, tubeMesh=null, cuffMesh=null, connMesh=null;
    const connMat=mat('#2f6fa8');
    /* the target ring, Learn only */
    const ring=new THREE.Mesh(new THREE.RingGeometry(1, 1.25, 48), new THREE.MeshBasicMaterial({color:'#3fb6ff', transparent:true, opacity:0.85, side:THREE.DoubleSide, depthTest:false}));
    ring.rotation.x=-Math.PI/2; ring.renderOrder=10; ring.visible=false; world.add(ring);

    const DIRV={'+x':[1,0],'-x':[-1,0],'+z':[0,1],'-z':[0,-1]};
    function placeBladeMesh(x, top, z, depth, edgeDir){
      const [ex,ez]=DIRV[edgeDir];
      blade.position.set(x, top-depth, z);
      blade.rotation.set(0, Math.atan2(-ez, ex), 0);   /* local +x onto the edge direction */
      blade.visible=true;
    }
    /* A path from the tip outward, for the rod and the tube.
       Before the turn: the shaft lies across the neck, parallel to the floor, toward the
       operator, and only the angled (coude) tip goes in, down and away along the blade.
       After the turn: the path the geometry gives (straight through the tract, one gentle arc
       inside the airway, then down the airway) and, outside, the same line continued: the
       shaft rises toward the head at the tract's angle. No hairpin: a bougie is semi-rigid. */
    /* A path from the tip outward, for the rod and the tube, of the instrument's own length
       (length_mm): what goes in comes off the end outside.
       Before the turn: the shaft lies across the neck, parallel to the floor, toward the
       operator, and only the angled (coude) tip goes in, down and away along the blade.
       After the turn: the path the geometry gives (straight through the tract, one gentle arc
       inside the airway, then down the airway) and, outside, the same line continued: the
       shaft rises toward the head at the tract's angle. No hairpin: a bougie is semi-rigid. */
    function rodPath(depth, turned, kind){
      const e=sim.state.rodEntry; if(!e) return null;
      const R=sim.rodGeom(), top=e.col.top, s=sim.state.side==='right'?-1:1;
      const T=Object.values(tools).find(t=>t.kind==='rod')||{};
      const I=Object.values(tools).find(t=>t.kind===(kind||'rod'))||T;
      const total=I.length_mm||600;
      const pts=[];
      if(!turned){
        const cd=(T.coude_deg||40)*Math.PI/180, tipLen=T.tip_mm||28;
        const c=[-s*Math.cos(cd), -Math.sin(cd), 0];
        const along=Math.max(0, depth/Math.sin(cd));
        const tip=[e.x+c[0]*along, top+c[1]*along, e.z];
        const knee=[tip[0]-c[0]*tipLen, tip[1]-c[1]*tipLen, e.z];
        for(let k=0;k<=8;k++){ const f=k/8; pts.push([tip[0]+(knee[0]-tip[0])*f, tip[1]+(knee[1]-tip[1])*f, e.z]); }
        const rest=Math.max(10, total-tipLen);
        pts.push([knee[0]+s*6, knee[1]+0.8, e.z]);
        for(const f of [0.08, 0.4, 1]) pts.push([knee[0]+s*rest*f, knee[1]+1, e.z]);
      } else {
        const P=R.path.pts, n=Math.min(P.length-1, Math.round(depth/0.5));
        for(let i=n;i>=0;i-=2) pts.push([P[i].x, P[i].y, P[i].z]);
        if(pts.length<2) pts.push([P[0].x, P[0].y, P[0].z]);
        const d=R.path.dir, rest=Math.max(4, total-depth);
        for(const f of [0.01, 0.2, 0.55, 1]) pts.push([e.x, top+d[1]*rest*f, e.z+d[2]*rest*f]);
      }
      return pts.map(p=>new THREE.Vector3(p[0],p[1],p[2]));
    }
    function tubeAlong(pts, r, from, to){
      const curve=new THREE.CatmullRomCurve3(pts, false, 'centripetal', 0.2);
      if(from==null) return new THREE.TubeGeometry(curve, 120, r, 14, false);
      const L=curve.getLength(), a=Math.max(0,from/L), b=Math.min(1,to/L);
      const sub=[]; for(let i=0;i<=24;i++) sub.push(curve.getPointAt(a+(b-a)*i/24));
      return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(sub), 24, r, 14, false);
    }
    function drawInstruments(){
      const S=sim.state;
      /* blade */
      if(S.blade){ placeBladeMesh(S.blade.x, S.blade.col.top, S.blade.z, S.blade.depth, S.blade.edge); }
      else if(view.tool && tools[view.tool].kind==='blade' && view.hover && cur() && cur().type==='stab'){
        placeBladeMesh(view.hover.x, view.hover.top+1, view.hover.z, 0, view.preEdge);
      } else blade.visible=false;
      slit.visible=!!S.rodEntry || !!(S.blade&&S.blade.depth>0);
      if(slit.visible){ const e=S.rodEntry||S.blade; slit.position.set(e.x, e.col.top+0.2, e.z); }
      /* rod */
      if(rodMesh){ world.remove(rodMesh); rodMesh.geometry.dispose(); rodMesh=null; }
      if(S.rod){ const T=Object.values(tools).find(t=>t.kind==='rod')||{};
        const p=rodPath(S.rod.depth, S.rod.turned); if(p){ rodMesh=new THREE.Mesh(tubeAlong(p, T.radius||2.5), rodMat); world.add(rodMesh); } }
      /* tube and cuff */
      if(tubeMesh){ world.remove(tubeMesh); tubeMesh.geometry.dispose(); tubeMesh=null; }
      if(cuffMesh){ world.remove(cuffMesh); cuffMesh.geometry.dispose(); cuffMesh=null; }
      if(connMesh){ world.remove(connMesh); connMesh.geometry.dispose(); connMesh=null; }
      if(S.tube && S.tube.depth>0){ const T=Object.values(tools).find(t=>t.kind==='tube')||{};
        const p=rodPath(S.tube.depth, 'feet', 'tube');
        if(p){ tubeMesh=new THREE.Mesh(tubeAlong(p, T.radius||4.1), tubeMat); world.add(tubeMesh);
          /* The connector at the outer end. */
          const L=T.length_mm||280, C=T.connector_mm||16;
          if(connMesh){ world.remove(connMesh); connMesh.geometry.dispose(); connMesh=null; }
          connMesh=new THREE.Mesh(tubeAlong(p, (T.radius||4.1)+1.6, L-C, L), connMat); world.add(connMesh);
          const rr=pack.steps.find(s=>s.type==='railroad');
          if(rr&&rr.cuff_mm){ const infl=pack.steps.find(s=>s.type==='inflate'); const full=infl?infl.range_ml[1]:10;
            const r=(T.radius||4.1)+0.6+Math.min(1.4,S.cuff_ml/full)*4.5;
            cuffMesh=new THREE.Mesh(tubeAlong(p, r, rr.cuff_mm[0], rr.cuff_mm[1]), cuffMat); world.add(cuffMesh); } } }
      /* finger */
      finger.visible=!!(view.tool && tools[view.tool].kind==='finger' && view.hover);
      if(finger.visible) finger.position.set(view.hover.x, view.hover.top+6, view.hover.z);
      /* target ring */
      const s=cur();
      const showRing=mode==='learn' && s && (s.type==='palpate' || (s.type==='stab' && !(S.blade&&S.blade.depth>0)));
      ring.visible=!!showRing;
      if(showRing){ const z=pack.zones.find(q=>q.id===s.target);
        const cx=(z.x[0]+z.x[1])/2, cz=(z.z[0]+z.z[1])/2, c=G.column(cx,cz);
        ring.position.set(cx, (c.top||20)+0.6, cz); const rr=Math.max(z.x[1]-z.x[0], z.z[1]-z.z[0])/2+1.5; ring.scale.set(rr, rr, 1); }
    }

    /* ---- layers panel ---- */
    function layersHTML(){
      const rows=groups.map(g=>{ const L=G.layers.find(l=>l.group===g.id)||{};
        return `<label><input type="checkbox" data-grp="${esc(g.id)}" ${view.hidden[g.id]?'':'checked'}><span class="pxs-sw" style="background:${esc(L.color||'#ccc')}"></span>${esc(g.name)}</label>`; }).join('');
      return `<h3>Layers</h3>${rows}
        <div style="margin-top:8px"><label for="pxs-see" style="display:block">See through the skin and fat</label>
        <input type="range" id="pxs-see" min="0.1" max="1" step="0.05" value="${view.see}"></div>
        <label style="margin-top:6px"><input type="checkbox" id="pxs-cut" ${view.cut?'checked':''}>Midline cut</label>`;
    }
    function applyLayers(){
      /* A section_only layer is never drawn as a surface, only as its cap in the cut. */
      for(const L of G.layers){ const g=G.groups[L.id]; g.visible=!view.hidden[L.group] && !L.section_only; }
      const seeIds=new Set(groups.filter(g=>g.see_through).map(g=>g.id));
      /* The cut keeps the half away from the operator, so the cut face looks at them. */
      clip.normal.set(sim.state.side==='right'?-1:1, 0, 0);   /* world x is mirrored */
      mats.forEach(m=>{ m.clippingPlanes=view.cut?[clip]:[]; m.needsUpdate=true; });
      for(const L of G.layers){
        const m=G.groups[L.id].children[0]&&G.groups[L.id].children[0].material; if(!m) continue;
        const base=m.userData.baseOpacity==null?1:m.userData.baseOpacity;
        const o=seeIds.has(L.group)?Math.min(base, view.see):base;
        m.opacity=o; m.transparent=o<1; m.depthWrite=o>=1;
      }
      [rodMat, tubeMat, cuffMat].forEach(m=>{ m.clippingPlanes=[]; });
      for(const c of caps) c.cg.visible=view.cut && !view.hidden[c.L.group];
      scenery.forEach(m=>{ m.visible=!view.cut; });
    }
    function bindLayers(){
      const box=$('pxs-layers'); box.innerHTML=layersHTML();
      box.querySelectorAll('[data-grp]').forEach(c=>c.onchange=()=>{ view.hidden[c.dataset.grp]=!c.checked; applyLayers(); });
      $('pxs-see').oninput=e=>{ view.see=+e.target.value; applyLayers(); };
      $('pxs-cut').onchange=e=>{ view.cut=e.target.checked; applyLayers();
        if(view.cut){ const s=sim.state.side==='right'?-1:1; camera.position.set(-s*260, 30, 8); controls.target.set(0,4,8); controls.update(); }
        else resetView(); };
    }

    /* ---- the step card ---- */
    const cur=()=>sim&&sim.current();
    /* A message belongs to the step it was said in: it goes when the step changes. Call
       after the engine has answered, so a step that just completed keeps its own words. */
    function say(r){
      if(!r) return;
      if(r.kind==='ok' && !r.text) { view.msg=null; return; }
      if(!r.text && r.kind==='info') return;
      view.msg={kind:r.kind, text:r.text, at:sim.state.i};
    }
    function handsLine(){
      const h=(pack.hands||{})[sim.state.hand_state];
      return h?`<div class="pxs-hands"><b>Non-dominant hand:</b> ${esc(h)}</div>`:'';
    }
    function actionButtons(){
      const s=cur(); if(!s) return '';
      if(mode==='learn'){
        if(s.type==='action') return `<div class="pxs-acts"><button class="pxs-btn pri" data-act="${esc(s.id)}">${esc(s.label)}</button></div>`;
        if(s.type==='choice') return `<div class="pxs-acts">${s.options.map(o=>`<button class="pxs-btn" data-choose="${esc(o.id)}">${esc(o.label)}</button>`).join('')}</div>`;
        return '';
      }
      /* Practice: every remaining button, in a fixed order that does not give the sequence away. */
      const doneIds=new Set(sim.state.stepLog.filter(r=>r.t!=null).map(r=>r.id));
      const items=pack.steps.filter(x=>x.type==='action' && !doneIds.has(x.id)).map(x=>({id:x.id,label:x.label}))
        .concat((pack.distractors||[]).map(d=>({id:d.id,label:d.label})))
        .sort((a,b)=>a.label.localeCompare(b.label));
      const ch=pack.steps.filter(x=>x.type==='choice' && !doneIds.has(x.id));
      return `<div class="pxs-grp">Actions</div><div class="pxs-acts many">${items.map(i=>`<button class="pxs-btn" data-act="${esc(i.id)}">${esc(i.label)}</button>`).join('')}</div>`+
        ch.map(c=>`<div class="pxs-grp">${esc(c.label)}</div><div class="pxs-acts many">${c.options.map(o=>`<button class="pxs-btn" data-choose="${esc(o.id)}">${esc(o.label)}</button>`).join('')}</div>`).join('');
    }
    function controlsHTML(){
      const t=view.tool&&tools[view.tool]; if(!t) return (mode==='learn'&&needTool()) ? '' : '<div class="pxs-note" style="margin-top:8px">Pick an instrument from the tray, or an action.</div>';
      const S=sim.state, k=t.kind;
      if(k==='finger') return `<div class="pxs-note" style="margin-top:8px">Move over the neck to feel. Click to mark.</div>`;
      if(k==='blade'){
        const edge=S.blade?S.blade.edge:view.preEdge;
        const nm={operator:'toward you', far:'away from you', head:'toward the head', feet:'toward the feet'}[sim.named(edge)];
        return `<div class="pxs-ctl"><span class="pxs-note">Cutting edge: <b>${esc(nm)}</b></span></div>
          <div class="pxs-ctl"><button class="pxs-rot" data-rot="ccw" aria-label="Turn the blade counterclockwise, seen from above"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7.5 6.5A8 8 0 1 1 4.2 13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M3 4.5v5h5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg><span>Turn left</span></button>
          <button class="pxs-rot" data-rot="cw" aria-label="Turn the blade clockwise, seen from above"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16.5 6.5A8 8 0 1 0 19.8 13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M21 4.5v5h-5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg><span>Turn right</span></button></div>
          <div class="pxs-ctl">${S.blade?`<button class="pxs-btn hold" data-hold="blade">Push</button>`:'<span class="pxs-note">Click the neck to place the blade.</span>'}</div>`;
      }
      if(k==='rod') return `<div class="pxs-ctl"><button class="pxs-btn hold" data-hold="rod">Push</button><button class="pxs-btn hold" data-hold="rodback">Pull back</button>
          <button class="pxs-btn" data-done="rod">Done</button></div>
          <div class="pxs-ctl"><button class="pxs-rot" data-turn="ccw" aria-label="Swing the bougie counterclockwise, seen from above"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7.5 6.5A8 8 0 1 1 4.2 13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M3 4.5v5h5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg><span>Swing left</span></button><button class="pxs-rot" data-turn="cw" aria-label="Swing the bougie clockwise, seen from above"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16.5 6.5A8 8 0 1 0 19.8 13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M21 4.5v5h-5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg><span>Swing right</span></button></div>
          <div class="pxs-note">In: <b>${S.rod?(S.rod.depth/10).toFixed(1):'0.0'} cm</b></div>`;
      if(k==='tube') return `<div class="pxs-ctl"><button class="pxs-btn hold" data-hold="tube">Push</button><button class="pxs-btn hold" data-hold="tubeback">Pull back</button>
          <button class="pxs-btn" data-twist="1" aria-pressed="${view.twist}">Rotate as you push</button>
          <button class="pxs-btn" data-done="tube">Done</button></div>`;
      if(k==='syringe') return `<div class="pxs-ctl"><button class="pxs-btn hold" data-hold="syringe">Inflate</button>
          <button class="pxs-btn hold" data-hold="syringe_out">Deflate</button>
          <button class="pxs-btn" data-done="syringe">Done</button></div>
          <div class="pxs-note">Pilot balloon: <b>${S.cuff_ml<3?'empty':S.cuff_ml<5?'soft':S.cuff_ml<=10?'firm':'very tense'}</b></div>`;
      if(k==='bag') return `<div class="pxs-ctl"><button class="pxs-btn pri" data-vent="1">Ventilate</button></div>`;
      return '';
    }
    /* Which instrument the step needs, said plainly. Learn mode only: in Practice choosing the
       instrument is part of the test. */
    function needTool(){
      const s=cur(); if(!s) return null;
      const id=s.tool || (s.type==='palpate' ? (Object.values(tools).find(t=>t.kind==='finger')||{}).id : null);
      return id && tools[id] ? tools[id] : null;
    }
    function pickHTML(){
      const t=view.tool && tools[view.tool];
      const hold=t?`<div class="pxs-hold">In your hand: <b>${esc(t.name)}</b></div>`:'';
      if(mode!=='learn') return hold;
      const need=needTool();
      if(need && view.tool!==need.id) return `<div class="pxs-pick">Pick up the <b>${esc(need.name)}</b>. It is glowing in the tray below.</div>`;
      return hold;
    }
    function card(){
      const s=cur(), S=sim.state, n=pack.steps.length;
      let h='';
      if(!s){ h='<div class="pxs-h">Done</div>'; }
      else if(mode==='learn'){
        h=`<div class="pxs-n">Step ${S.i+1} of ${n}</div><div class="pxs-h">${esc(s.label)}</div><p class="pxs-p">${esc(s.prompt)}</p>
           <details class="pxs-why"><summary>Why</summary>${esc(s.why)}</details>`;
      } else {
        h=`<div class="pxs-n">Practice · ${S.stepLog.filter(r=>r.t!=null).length} of ${n} done</div><div class="pxs-h">What next?</div>`;
      }
      if(view.msg && view.msg.at===S.i) h+=`<div class="pxs-fb on ${view.msg.kind}" role="status">${esc(view.msg.text)}</div>`;
      h+=pickHTML()+actionButtons()+controlsHTML()+handsLine();
      if(mode==='learn') h+=`<details class="pxs-why" style="margin-top:10px"${view.listOpen?' open':''}><summary>All steps</summary><ol class="pxs-steps">${pack.steps.map((x,i)=>`<li class="${i<S.i?'done':i===S.i?'cur':''}">${esc(x.label)}</li>`).join('')}</ol></details>`;
      const c=$('pxs-card'); c.hidden=false; c.innerHTML=h;
      if(view.msg && view.msg.at===S.i) c.scrollTop=0;
      const lst=c.querySelector('details:last-of-type'); if(lst&&mode==='learn') lst.addEventListener('toggle',()=>{ view.listOpen=lst.open; });
      c.querySelectorAll('[data-act]').forEach(b=>b.onclick=()=>{ say(sim.action(b.dataset.act)); after(); });
      c.querySelectorAll('[data-choose]').forEach(b=>b.onclick=()=>{ say(sim.choose(b.dataset.choose)); after(); resetView(); });
      c.querySelectorAll('[data-rot]').forEach(b=>b.onclick=()=>{
        if(sim.state.blade){ say(sim.rotateBlade(b.dataset.rot)); }
        else { const CW={'+x':'-z','-z':'-x','-x':'+z','+z':'+x'}, CCW={'-z':'+x','-x':'-z','+z':'-x','+x':'+z'};
               view.preEdge=(b.dataset.rot==='cw'?CW:CCW)[view.preEdge]; }
        after(); });
      c.querySelectorAll('[data-turn]').forEach(b=>b.onclick=()=>{ say(sim.turnRod(b.dataset.turn)); after(); });
      c.querySelectorAll('[data-done]').forEach(b=>b.onclick=()=>{ const k=b.dataset.done;
        say(k==='rod'?sim.rodDone():k==='tube'?sim.tubeDone():sim.inflateDone()); after(); });
      c.querySelectorAll('[data-twist]').forEach(b=>b.onclick=()=>{ view.twist=!view.twist; card(); });
      c.querySelectorAll('[data-vent]').forEach(b=>b.onclick=()=>{ say(sim.confirm()); if(sim.state.capno) $('pxs-capno').hidden=false; after(); });
      c.querySelectorAll('[data-hold]').forEach(b=>bindHold(b, b.dataset.hold));
    }
    function tray(){
      const s=cur();
      $('pxs-tray').innerHTML=(pack.tools||[]).filter(t=>!sim.state.removed[t.id]||t.id===view.tool).map(t=>
        `<button class="pxs-tool${mode==='learn'&&needTool()&&needTool().id===t.id&&view.tool!==t.id?' glow':''}" type="button" data-tool="${esc(t.id)}" aria-pressed="${view.tool===t.id}">
          <b>${esc(t.name)}</b><span>${esc(t.desc||'')}</span></button>`).join('');
      $('pxs-tray').querySelectorAll('[data-tool]').forEach(b=>b.onclick=()=>{ view.tool=view.tool===b.dataset.tool?null:b.dataset.tool; view.hover=null; tray(); card(); });
    }
    function after(){
      if(sim.state.finished && !view.ended){ view.ended=true; setTimeout(debrief, 900); }
      /* An instrument that has been taken out cannot stay in the hand. */
      if(view.tool && sim.state.removed[view.tool]) view.tool=null;
      tray(); card(); drawInstruments();
    }

    /* ---- hold to push ---- */
    function bindHold(btn, what){
      let raf=0, last=0, on=false;
      const step=(ts)=>{
        if(!on) return;
        const tnow=performance.now(), dt=Math.max(0,Math.min(0.25,(tnow-last)/1000)); last=tnow;
        let r=null;
        if(what==='blade') r=sim.pushBlade(SPEED.blade*dt);
        else if(what==='rod') r=sim.pushRod((sim.state.rod&&sim.state.rod.turned?SPEED.rod:SPEED.rod_in)*dt);
        else if(what==='rodback') r=sim.pullRod(SPEED.rod*dt);
        else if(what==='tube') r=sim.pushTube(SPEED.tube*dt, view.twist);
        else if(what==='tubeback') r=sim.pullTube(SPEED.tube*dt);
        else if(what==='syringe') r=sim.inflate(SPEED.syringe*dt);
        else if(what==='syringe_out') r=sim.inflate(-SPEED.syringe*dt);
        readout(r, what);
        if(r && (r.kind==='error' || r.advanced || r.code==='order')){ say(r); stop(true); return; }
        drawInstruments();
        const n=root.querySelector('.pxs-note b'); if(n && what.indexOf('rod')===0 && sim.state.rod) n.textContent=(sim.state.rod.depth/10).toFixed(1)+' cm';
        if(n && what.indexOf('syringe')===0){ const ml=sim.state.cuff_ml; n.textContent=ml<3?'empty':ml<5?'soft':ml<=10?'firm':'very tense'; }
        raf=requestAnimationFrame(step);
      };
      const start=(e)=>{ e.preventDefault(); if(on) return; on=true; btn.classList.add('on'); last=performance.now(); raf=requestAnimationFrame(step); };
      const stop=(fromStep)=>{ if(!on) return; on=false; cancelAnimationFrame(raf); btn.classList.remove('on');
        if(what==='blade'){ say(sim.releaseBlade()); }
        after(); };
      btn.addEventListener('pointerdown', start);
      ['pointerup','pointerleave','pointercancel'].forEach(ev=>btn.addEventListener(ev, ()=>stop(false)));
      btn.addEventListener('keydown', e=>{ if(e.key===' '||e.key==='Enter'){ if(!e.repeat) start(e); } });
      btn.addEventListener('keyup', e=>{ if(e.key===' '||e.key==='Enter') stop(false); });
    }
    /* What the tip is in. Learn names the layer, Practice says what it feels like. */
    function readout(r, what){
      const el=$('pxs-read'); if(!r){ el.classList.remove('on'); return; }
      let line='';
      if(what==='blade' && r.layer){ const f=sim.feelOf(r.layer); line=(mode==='learn'?`<b>${(r.depth||0).toFixed(1)} mm</b>${esc(f.learn)}. `:'')+esc(f.feel||''); }
      else if((what==='rod'||what==='rodback') && sim.state.rod){ line=`<b>${(sim.state.rod.depth/10).toFixed(1)} cm</b>`+(r.click?esc(r.text):''); }
      else if((what==='tube'||what==='tubeback') && sim.state.tube){ line=mode==='learn' ? (sim.cuffIn()?'The cuff is inside the trachea.':'The cuff is not inside the trachea yet.') : ''; }
      else if(what==='syringe'||what==='syringe_out'){ line=''; }
      if(r.kind==='error') line=esc(r.text);
      if(!line){ return; }
      el.innerHTML=line; el.classList.add('on');
      clearTimeout(readout.t); readout.t=setTimeout(()=>el.classList.remove('on'), 2600);
    }

    /* ---- pointer on the neck ---- */
    const rc=new THREE.Raycaster(), ndc=new THREE.Vector2();
    let down=null;
    function pick(ev){
      const r=canvas.getBoundingClientRect();
      ndc.set(((ev.clientX-r.left)/r.width)*2-1, -((ev.clientY-r.top)/r.height)*2+1);
      rc.setFromCamera(ndc, camera);
      const h=rc.intersectObjects(G.skinMeshes, false)[0];
      if(!h) return null;
      const x=-h.point.x;                 /* back to the pack's x */
      if(view.cut && (sim.state.side==='right' ? x<0 : x>0)) return null;
      return {x, z:h.point.z, top:h.point.y};
    }
    canvas.addEventListener('pointermove', ev=>{
      if(!view.tool) return;
      const k=tools[view.tool].kind;
      if(k!=='finger' && k!=='blade') return;
      view.hover=pick(ev);
      if(k==='finger' && view.hover){
        const f=sim.feel(view.hover.x, view.hover.z), el=$('pxs-read');
        if(f.feel){ el.innerHTML=(mode==='learn'?`<b>${esc(f.name)}</b>`:'')+esc(f.feel); el.classList.add('on'); clearTimeout(readout.t); }
      }
      drawInstruments();
    });
    canvas.addEventListener('pointerleave', ()=>{ view.hover=null; drawInstruments(); });
    canvas.addEventListener('pointerdown', ev=>{ down={x:ev.clientX, y:ev.clientY}; });
    canvas.addEventListener('pointerup', ev=>{
      if(!down) return; const moved=Math.hypot(ev.clientX-down.x, ev.clientY-down.y); down=null;
      if(moved>5 || !view.tool) return;
      const k=tools[view.tool].kind, p=pick(ev); if(!p) return;
      if(k==='finger') say(sim.palpate(p.x, p.z));
      else if(k==='blade' && !sim.state.blade) say(sim.placeBlade(p.x, p.z, sim.named(view.preEdge)));
      else return;
      after();
    });

    /* ---- capnograph ---- */
    function capno(t){
      const cv=$('pxs-capcv'); if(!cv || $('pxs-capno').hidden) return;
      const g=cv.getContext('2d'), W=cv.width, H=cv.height;
      g.fillStyle='#0b141a'; g.fillRect(0,0,W,H); g.strokeStyle='#ffe46b'; g.lineWidth=2; g.beginPath();
      for(let x=0;x<W;x++){ const ph=((x+t*0.06)%110)/110;
        const y= ph<0.12?0 : ph<0.2?(ph-0.12)/0.08 : ph<0.55?1+0.08*(ph-0.2)/0.35 : ph<0.6?1.08-(ph-0.55)/0.05*1.08 : 0;
        const py=H-8-y*(H-22); if(x===0) g.moveTo(x,py); else g.lineTo(x,py); }
      g.stroke();
    }

    /* ---- the debrief ---- */
    function debrief(){
      const d=sim.debrief();
      cfg.onFinish && cfg.onFinish(d);
      const mm=String(Math.floor(d.seconds/60)).padStart(2,'0')+':'+String(Math.floor(d.seconds%60)).padStart(2,'0');
      const src=(pack.sources||[]).filter(s=>s.url).map(s=>`<li class="src">${esc(s.cite)} <a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a>. ${esc(s.note||'')}</li>`).join('');
      const errs=d.errors.map(e=>{ const st=pack.steps.find(x=>x.id===e.step); return `<li class="bad">${esc(st?st.label:'')}: ${esc(e.text)}${e.severity==='critical'?' <b>(critical)</b>':''}</li>`; }).join('');
      const box=document.createElement('div'); box.className='pxs-deb';
      box.innerHTML=`<div class="pxs-debc" role="document">
        <h2>${esc(pack.card.title)}: ${d.critical?'finished with a critical error':'done'}</h2>
        <div class="pxs-note">${mode==='learn'?'Learn mode. Prompts were shown.':'Practice mode. No prompts.'}</div>
        <div class="pxs-stats">
          <div class="pxs-stat"><b>${mm}</b><span>time</span></div>
          <div class="pxs-stat"><b>${d.clean} of ${d.total}</b><span>steps with no error</span></div>
          <div class="pxs-stat"><b>${d.errors.length}</b><span>errors</span></div>
          <div class="pxs-stat"><b>${d.critical}</b><span>critical</span></div>
        </div>
        ${errs?`<h3>What went wrong</h3><ol>${errs}</ol>`:'<p>No errors.</p>'}
        <h3>Take away</h3><ol>${((pack.debrief||{}).points||[]).map(p=>`<li>${esc(p)}</li>`).join('')}</ol>
        <h3>Sources</h3><ul>${src}</ul>
        <p class="pxs-note">${esc(pack.review||'')}</p>
        <div class="pxs-ctl"><button class="pxs-btn pri" data-again="learn">Learn again</button><button class="pxs-btn" data-again="practice">Practice</button><button class="pxs-btn" data-close="1">Close</button></div>
      </div>`;
      $('pxs-mid').appendChild(box);
      box.querySelectorAll('[data-again]').forEach(b=>b.onclick=()=>{ box.remove(); start(b.dataset.again, hand); });
      box.querySelector('[data-close]').onclick=close;
      const f=box.querySelector('[data-again]'); if(f) f.focus();
    }

    /* ---- start ---- */
    function chooser(){
      const box=document.createElement('div'); box.className='pxs-start';
      box.innerHTML=`<div class="pxs-startc">
        <h2>${esc(pack.card.title)}</h2><p>${esc(pack.card.blurb||'')}</p>
        <div class="pxs-n" style="margin-bottom:6px">Mode</div>
        <div class="pxs-seg" role="radiogroup" aria-label="Mode">
          <button class="pxs-btn" role="radio" data-mode="learn" aria-checked="${mode!=='practice'}">Learn<small>Each step prompted, with why.</small></button>
          <button class="pxs-btn" role="radio" data-mode="practice" aria-checked="${mode==='practice'}">Practice<small>No prompts. Errors in the debrief.</small></button></div>
        <div class="pxs-n" style="margin-bottom:6px">Your dominant hand</div>
        <div class="pxs-seg" role="radiogroup" aria-label="Dominant hand">
          <button class="pxs-btn" role="radio" data-hand="right" aria-checked="${hand!=='left'}">Right</button>
          <button class="pxs-btn" role="radio" data-hand="left" aria-checked="${hand==='left'}">Left</button></div>
        <div class="pxs-ctl"><button class="pxs-btn pri" data-go="1">Start</button><button class="pxs-btn" data-close="1">Cancel</button></div>
        <p class="pxs-note" style="margin-top:12px">${esc(pack.review||'')}</p></div>`;
      $('pxs-mid').appendChild(box);
      const paint=()=>{ box.querySelectorAll('[data-mode]').forEach(b=>{ b.setAttribute('aria-checked',String(b.dataset.mode===mode)); b.setAttribute('aria-pressed',String(b.dataset.mode===mode)); });
        box.querySelectorAll('[data-hand]').forEach(b=>{ b.setAttribute('aria-checked',String(b.dataset.hand===hand)); b.setAttribute('aria-pressed',String(b.dataset.hand===hand)); }); };
      box.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{ mode=b.dataset.mode; paint(); });
      box.querySelectorAll('[data-hand]').forEach(b=>b.onclick=()=>{ hand=b.dataset.hand; paint(); });
      box.querySelector('[data-go]').onclick=()=>{ box.remove(); start(mode, hand); };
      box.querySelector('[data-close]').onclick=close;
      paint(); box.querySelector('[data-go]').focus();
    }
    function start(m, h){
      mode=m; hand=h;
      sim=PXCORE.create(pack, G, {mode, hand, now:()=>performance.now()});
      Object.assign(view, {tool:null, preEdge:'-z', twist:true, msg:null, hover:null, ended:false});
      $('pxs-capno').hidden=true;
      $('pxs-mode').textContent=mode==='learn'?'Learn':'Practice'; $('pxs-mode').className='pxs-pill'+(mode==='practice'?' pr':'');
      view.startedAt=performance.now(); view.started=true;
      cfg.onStart && cfg.onStart({mode, hand});
      resetView(); tray(); card(); bindLayers(); applyLayers(); drawInstruments();
    }

    /* ---- frame ---- */
    let alive=true;
    function size(){
      const r=$('pxs-mid').getBoundingClientRect();
      renderer.setSize(Math.max(1,r.width), Math.max(1,r.height), false);
      camera.aspect=Math.max(1,r.width)/Math.max(1,r.height); camera.updateProjectionMatrix();
    }
    const ro=(typeof ResizeObserver!=='undefined')?new ResizeObserver(size):null; if(ro) ro.observe($('pxs-mid'));
    function frame(t){
      if(!alive) return;
      controls.update();
      if(sim && view.started && !sim.state.finished){ const s=(performance.now()-sim.state.t0)/1000;
        $('pxs-time').textContent=String(Math.floor(s/60)).padStart(2,'0')+':'+String(Math.floor(s%60)).padStart(2,'0'); }
      if(ring.visible) ring.material.opacity=0.55+0.35*Math.sin(t/260);
      capno(t);
      renderer.render(scene, camera);
      requestAnimationFrame(frame);
    }
    function close(){
      if(!alive) return; alive=false;
      if(ro) ro.disconnect();
      controls.dispose(); renderer.dispose();
      scene.traverse(o=>{ if(o.geometry) o.geometry.dispose(); });
      root.innerHTML=''; root.className=''; root.hidden=true;
      document.removeEventListener('keydown', onKey);
      cfg.onClose && cfg.onClose();
    }
    function onKey(e){ if(e.key==='Escape' && !root.querySelector('.pxs-deb')){ e.preventDefault(); close(); } }
    document.addEventListener('keydown', onKey);
    $('pxs-exit').onclick=close;
    $('pxs-reset').onclick=()=>resetView();
    $('pxs-lay').onclick=()=>{ const L=$('pxs-layers'); L.hidden=!L.hidden; $('pxs-lay').setAttribute('aria-pressed',String(!L.hidden)); };
    root.hidden=false;
    sim=PXCORE.create(pack, G, {mode, hand, now:()=>performance.now()});
    $('pxs-card').hidden=true; $('pxs-mode').textContent=mode==='practice'?'Practice':'Learn';
    size(); resetView(); bindLayers(); applyLayers();
    requestAnimationFrame(frame);
    if(cfg.skipChooser) start(mode, hand); else chooser();
    /* For the browser tests. */
    return {close, get sim(){ return sim; }, view, G, start, refresh:()=>after(), camera, controls, scenery, applyLayers:()=>{ bindLayers(); applyLayers(); },
      /* Where a point of the pack lands on the screen, for the browser tests. */
      screenOf(x,y,z){ const v=new THREE.Vector3(-x,y,z).project(camera), r=canvas.getBoundingClientRect();
        return {x:r.left+(v.x+1)/2*r.width, y:r.top+(1-v.y)/2*r.height}; }};
  }
  return {open};
})();
