/* ---------- procedure geometry (28 October 2026) ----------
   Turns a procedure pack's layers into three.js meshes, and answers the one question the
   procedure engine asks of them: going straight down from a point on the skin, which layer
   is where.

   Nothing here names a procedure, a structure or a drug. A pack describes each layer as one
   of four kinds, in millimeters, with x to the patient's left, y anterior (toward the ceiling,
   patient supine) and z toward the head:

     slab     a solid sheet lofted through stations along z. Each station gives an outer and
              an inner cross-section (or an outer one and an offset). Open sheets get side
              strips, so a ray that crosses one crosses it twice.
     surface  a closed loop lofted the same way, with no thickness: an air column.
     tube     a closed tube of one radius along a path of points.
     repeat   a slab template placed at each z in a list.

   A cross-section is an ellipse arc {ellipse:[cx,cy,rx,ry], from, to} in degrees, where 0 is
   anterior (+y) and 90 is the patient's left (+x), or a polyline {poly:[[x,y],...], offset}.
   An offset puts the inner face that many millimeters to the right of the line's direction.
   A layer with mirror_of copies another layer across the midline.

   Uses THREE for its math and its raycaster only, so it runs in node for the tests. */
const PXGEOM = (function(){
  const N_DEFAULT = 40;

  function isClosed(s){ return (!!s.ellipse && Math.abs((s.to-s.from)) >= 359.999) || (!!s.poly && !!s.closed); }
  function ellipsePts(s, n){
    const [cx,cy,rx,ry]=s.ellipse, closed=isClosed(s), out=[];
    const m = closed ? n : n-1;
    for(let i=0;i<n;i++){
      const a=(s.from+(s.to-s.from)*i/m)*Math.PI/180;
      out.push([cx+rx*Math.sin(a), cy+ry*Math.cos(a)]);
    }
    return out;
  }
  function resample(pts, n){
    const L=[0];
    for(let i=1;i<pts.length;i++) L.push(L[i-1]+Math.hypot(pts[i][0]-pts[i-1][0], pts[i][1]-pts[i-1][1]));
    const tot=L[L.length-1], out=[];
    let k=0;
    for(let i=0;i<n;i++){
      const d=tot*i/(n-1);
      while(k<pts.length-2 && L[k+1]<d) k++;
      const seg=(L[k+1]-L[k])||1, f=Math.min(1,Math.max(0,(d-L[k])/seg));
      out.push([pts[k][0]+(pts[k+1][0]-pts[k][0])*f, pts[k][1]+(pts[k+1][1]-pts[k][1])*f]);
    }
    return out;
  }
  /* The inner face of a polyline: each point moved along the mean of its segments' right
     normals. */
  function offsetPts(pts, d){
    return pts.map((p,i)=>{
      let nx=0, ny=0;
      for(const [a,b] of [[i-1,i],[i,i+1]]){
        if(a<0||b>=pts.length) continue;
        const dx=pts[b][0]-pts[a][0], dy=pts[b][1]-pts[a][1], l=Math.hypot(dx,dy)||1;
        nx+=dy/l; ny+=-dx/l;
      }
      const l=Math.hypot(nx,ny)||1;
      return [p[0]+nx/l*d, p[1]+ny/l*d];
    });
  }
  function shapePts(s, n){
    if(s.ellipse) return ellipsePts(s, n);
    /* A fixed poly is used point for point, so stations built at the same angles line up
       and the loft between them does not twist. Every station of the layer must have the
       same number of points. */
    if(s.poly && s.fixed){ const p=s.poly.slice(); if(s.closed && p.length>1 && p[0][0]===p[p.length-1][0] && p[0][1]===p[p.length-1][1]) p.pop(); return p; }
    if(s.poly) return s.closed ? resample(s.poly, n+1).slice(0, n) : resample(s.poly, n);
    throw new Error('unknown cross-section');
  }
  function mirrorShape(s){
    if(s.ellipse){ const [cx,cy,rx,ry]=s.ellipse; return Object.assign({}, s, {ellipse:[-cx,cy,rx,ry], from:-s.to, to:-s.from}); }
    if(s.poly) return Object.assign({}, s, {poly:s.poly.map(p=>[-p[0],p[1]]).reverse()});
    return s;
  }
  function mirrorLayer(src, def){
    const L=JSON.parse(JSON.stringify(src));
    Object.assign(L, def); delete L.mirror_of;
    if(L.stations) L.stations=L.stations.map(st=>{
      const o={z:st.z};
      if(st.outer) o.outer=mirrorShape(st.outer);
      if(st.inner) o.inner=mirrorShape(st.inner);
      if(st.shape) o.shape=mirrorShape(st.shape);
      return o;
    });
    if(L.template) L.template=L.template.map(st=>({z:st.z, outer:mirrorShape(st.outer), inner:st.inner&&mirrorShape(st.inner)}));
    if(L.path) L.path=L.path.map(p=>[-p[0],p[1],p[2]]);
    return L;
  }
  /* Every layer with mirrors expanded, in pack order. */
  function resolve(pack){
    const byId={};
    const out=[];
    for(const def of pack.layers){
      let L=def;
      if(def.mirror_of){
        if(!byId[def.mirror_of]) throw new Error(def.id+': mirror_of names a layer that does not come first: '+def.mirror_of);
        L=mirrorLayer(byId[def.mirror_of], def);
      }
      byId[L.id]=L; out.push(L);
    }
    return out;
  }

  /* ---- geometry ---- */
  function grid(rows, closed){
    /* rows[i][j] = THREE.Vector3. Quads between consecutive rows, around each row. */
    const pos=[], idx=[], n=rows[0].length;
    rows.forEach(r=>r.forEach(v=>pos.push(v.x,v.y,v.z)));
    const cols = closed ? n : n-1;
    for(let i=0;i<rows.length-1;i++) for(let j=0;j<cols;j++){
      const a=i*n+j, b=i*n+(j+1)%n, c=(i+1)*n+j, d=(i+1)*n+(j+1)%n;
      idx.push(a,c,b, b,c,d);
    }
    const g=new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos,3));
    g.setIndex(idx); g.computeVertexNormals();
    return g;
  }
  function stationRows(stations, n){
    const outer=[], inner=[];
    let closed=null;
    for(const st of stations){
      const s=st.outer||st.shape;
      const c=isClosed(s); if(closed===null) closed=c;
      const o=shapePts(s, n);
      outer.push(o.map(p=>new THREE.Vector3(p[0],p[1],st.z)));
      if(st.outer){
        const inn = st.inner ? shapePts(st.inner, n) : offsetPts(o, st.outer.offset||0);
        inner.push(inn.map(p=>new THREE.Vector3(p[0],p[1],st.z)));
      }
    }
    return {outer, inner, closed};
  }
  function slabParts(stations, n){
    const {outer, inner, closed}=stationRows(stations, n);
    const parts=[{name:'outer', g:grid(outer, closed)}, {name:'inner', g:grid(inner, closed)}];
    if(!closed){
      for(const j of [0, n-1]) parts.push({name:'side', g:grid(outer.map((r,i)=>[r[j], inner[i][j]]), false)});
    }
    for(const i of [0, outer.length-1]) parts.push({name:'cap', g:grid([outer[i], inner[i]], closed)});
    return parts;
  }
  function material(L){
    return new THREE.MeshStandardMaterial({color:L.color||'#cccccc', roughness:0.72, metalness:0.0,
      side:THREE.DoubleSide, transparent:(L.opacity!=null&&L.opacity<1), opacity:(L.opacity==null?1:L.opacity),
      depthWrite:!(L.opacity!=null&&L.opacity<1)});
  }
  function buildLayer(L, n){
    const grp=new THREE.Group(); grp.name=L.id; grp.userData.layer=L.id;
    const mat=material(L);
    const add=(g,part)=>{ const m=new THREE.Mesh(g, mat); m.userData.layer=L.id; m.userData.part=part; grp.add(m); };
    if(L.kind==='slab') slabParts(L.stations, n).forEach(p=>add(p.g, p.name));
    else if(L.kind==='surface'){ const {outer, closed}=stationRows(L.stations, n); add(grid(outer, closed), 'outer'); }
    else if(L.kind==='tube'){
      const curve=new THREE.CatmullRomCurve3(L.path.map(p=>new THREE.Vector3(p[0],p[1],p[2])));
      add(new THREE.TubeGeometry(curve, Math.max(8,L.path.length*6), L.radius, 14, false), 'outer');
      /* Rounded ends, for a tube that stands for a limb or a bump rather than a vessel. */
      if(L.caps) for(const p of [L.path[0], L.path[L.path.length-1]]){
        const g=new THREE.SphereGeometry(L.radius, 20, 14); g.translate(p[0],p[1],p[2]); add(g, 'outer'); }
    }
    else if(L.kind==='repeat'){
      for(const z0 of L.at) slabParts(L.template.map(st=>Object.assign({}, st, {z:st.z+z0})), n).forEach(p=>add(p.g, p.name));
    }
    else throw new Error(L.id+': unknown layer kind '+L.kind);
    return grp;
  }

  function build(pack, opts){
    const n=(opts&&opts.segments)||N_DEFAULT;
    const layers=resolve(pack);
    const root=new THREE.Group(); root.name='procedure';
    const groups={}, hit=[];
    for(const L of layers){
      const g=buildLayer(L, L.segments||n); g.userData.def=L;
      groups[L.id]=g; root.add(g);
      if(L.hit) g.traverse(o=>{ if(o.isMesh) hit.push(o); });
    }
    root.updateMatrixWorld(true);
    const ray=new THREE.Raycaster();
    const skinId=(layers[0]||{}).id;

    /* Straight down from above the patient at (x, z): each hit layer as the intervals of y
       it occupies, top first. A layer crossed an odd number of times (a grazing ray) loses
       its last crossing. */
    function column(x, z){
      ray.set(new THREE.Vector3(x, 400, z), new THREE.Vector3(0,-1,0));
      ray.far=1000;
      const hits=ray.intersectObjects(hit, false);
      const per={};
      for(const h of hits){
        const id=h.object.userData.layer, y=h.point.y, a=per[id]||(per[id]=[]);
        if(a.length && Math.abs(a[a.length-1]-y)<0.05) continue;   /* a seam between two faces */
        a.push(y);
      }
      const iv=[];
      for(const id in per){
        const ys=per[id].sort((a,b)=>b-a);
        for(let i=0;i+1<ys.length;i+=2) iv.push({layer:id, top:ys[i], bottom:ys[i+1]});
      }
      iv.sort((a,b)=>b.top-a.top);
      const skin=iv.find(v=>v.layer===skinId);
      return {x, z, top: skin ? skin.top : null, intervals: iv};
    }
    /* The layer at a depth below the skin: the thinnest interval that holds that point. */
    function layerAt(col, depth){
      if(col.top==null) return null;
      const y=col.top-depth;
      let best=null;
      for(const v of col.intervals) if(y<=v.top+1e-6 && y>=v.bottom-1e-6 && (!best || (v.top-v.bottom)<(best.top-best.bottom))) best=v;
      return best ? best.layer : null;
    }
    function interval(col, id, which){
      const a=col.intervals.filter(v=>v.layer===id);
      return a.length ? (which==='last' ? a[a.length-1] : a[0]) : null;
    }
    /* The path a semi-rigid rod (a bougie) or a tube over it takes once it has been turned
       to run down the airway: straight through the tract from the skin to the inner face of
       the opening and straight_mm beyond it, at tract_deg from the skin plane, tipped toward the feet; then one arc of
       radius bend_mm inside the air column until it runs along the airway; then along the
       airway, easing toward its axis. A bougie bends, but not sharply: the tract holds the
       first part straight and the airway gives the arc its room. Points from the skin
       inward, every 0.5 mm, with their distance from the skin. */
    function rodPath(x0, z0, opts){
      opts=opts||{};
      const air=opts.air, col=column(x0, z0), a0=(opts.tract_deg||65)*Math.PI/180, R=opts.bend_mm||16;
      const ai=interval(col, air);
      if(col.top==null || !ai) return null;
      const pts=[], ds=0.5;
      let x=x0, y=col.top, z=z0, s=0, phi=a0;
      const push=()=>pts.push({x, y, z, s});
      push();
      const L1=(col.top-ai.top)/Math.sin(a0);
      for(; s<L1-1e-9; ){ const d=Math.min(ds, L1-s); y-=Math.sin(a0)*d; z-=Math.cos(a0)*d; s+=d; push(); }
      const airEntry=s;
      /* A little further straight into the air before the arc, so the arc clears the ring
         below the opening. */
      const L2=s+(opts.straight_mm||0);
      for(; s<L2-1e-9; ){ const d=Math.min(ds, L2-s); y-=Math.sin(a0)*d; z-=Math.cos(a0)*d; s+=d; push(); }
      const arcStart=s, arcLen=R*a0, xStart=x;
      for(let k=0; phi>1e-6; k++){
        const d=Math.min(ds, phi*R); phi-=d/R;
        y-=Math.sin(phi)*d; z-=Math.cos(phi)*d; s+=d;
        x=xStart*(1-Math.min(1,(s-arcStart)/arcLen)); push();
      }
      const yArc=y, len=opts.length||420;
      while(s<len){ const k=Math.min(1,(s-arcStart-arcLen)/40); y=yArc*(1-k*k*(3-2*k)); z-=ds; s+=ds; push(); }
      return {pts, airEntry, top:col.top, dir:[0, Math.sin(a0), Math.cos(a0)]};
    }
    /* A point a distance s along such a path. */
    function along(path, s){
      const P=path.pts; if(s<=0) return P[0];
      const i=Math.min(P.length-1, Math.round(s/0.5)); return P[i];
    }
    return {root, groups, layers, column, layerAt, interval, skinId, rodPath, along,
            /* What a drape rests on: the skin and any layer marked under_drape. */
            drapeMeshes: layers.filter(L=>L.under_drape||L.id===skinId).flatMap(L=>groups[L.id].children.filter(m=>m.userData.part==='outer')),
            skinMeshes: groups[skinId] ? groups[skinId].children.filter(m=>m.userData.part==='outer') : []};
  }

  return {build, resolve, shapePts, offsetPts};
})();
if(typeof module!=='undefined') module.exports=PXGEOM;
