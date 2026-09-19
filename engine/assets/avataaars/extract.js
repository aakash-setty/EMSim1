/* Derives engine/patient-art.json from the avataaars React library.

   Run once, offline, whenever the artwork needs regenerating. The simulator never
   loads avataaars, React or this script: it ships the JSON this writes.

     git clone https://github.com/fangpenlin/avataaars && cd avataaars      (93aa902 was used)
     # upstream ships FrownNatural.tsx but never registers it; register it:
     #   src/avatar/face/eyebrow/index.tsx: import FrownNatural, add <FrownNatural /> to the Selector
     npm i --ignore-scripts && npx tsc
     cd <somewhere with: npm i react@17 react-dom@17 jsdom>
     node extract.js /path/to/avataaars/dist /path/to/engine/patient-art.json

   How it works. Every option is rendered server-side inside a whole avatar and the one
   group of interest is cut out of the markup, so nothing here depends on the library's
   internals beyond the order of four groups. Colours: each coloured part is rendered
   twice with two different palette entries, the hex is swapped for a {slot} token in
   both, and the two results must be identical, which proves the token landed only where
   the colour option acts. Ids: React's per-render ids become @@0, @@1 ... and patient.js
   prefixes them per instance, so two patients on one page cannot share a mask.
   ShortHairShaggy is absent because upstream marks it broken and disables it.
   Numbers are rounded to two decimals, which is well under a pixel at any size drawn. */
const React=require('react'),S=require('react-dom/server'),{JSDOM}=require('jsdom'),fs=require('fs');
console.error=()=>{};
if(!process.argv[2]){console.log('usage: node extract.js <avataaars/dist> [out.json]');process.exit(2);}
const Avatar=require(require('path').resolve(process.argv[2])).default;
const OUT=process.argv[3]||'patient-art.json';
const O={
 top:'NoHair Eyepatch Hat Hijab Turban WinterHat1 WinterHat2 WinterHat3 WinterHat4 LongHairBigHair LongHairBob LongHairBun LongHairCurly LongHairCurvy LongHairDreads LongHairFrida LongHairFro LongHairFroBand LongHairNotTooLong LongHairShavedSides LongHairMiaWallace LongHairStraight LongHairStraight2 LongHairStraightStrand ShortHairDreads01 ShortHairDreads02 ShortHairFrizzle ShortHairShaggyMullet ShortHairShortCurly ShortHairShortFlat ShortHairShortRound ShortHairShortWaved ShortHairSides ShortHairTheCaesar ShortHairTheCaesarSidePart'.split(' '),
 accessories:'Blank Kurt Prescription01 Prescription02 Round Sunglasses Wayfarers'.split(' '),
 facialHair:'Blank BeardLight BeardMedium BeardMajestic MoustacheFancy MoustacheMagnum'.split(' '),
 clothes:'BlazerShirt BlazerSweater CollarSweater GraphicShirt Hoodie Overall ShirtCrewNeck ShirtScoopNeck ShirtVNeck'.split(' '),
 graphic:'Bat Cumbia Deer Diamond Hola Pizza Resist Selena Bear SkullOutline Skull'.split(' '),
 eyes:'Close Cry Default Dizzy EyeRoll Happy Hearts Side Squint Surprised Wink WinkWacky'.split(' '),
 eyebrow:'Angry AngryNatural Default DefaultNatural FlatNatural FrownNatural RaisedExcited RaisedExcitedNatural SadConcerned SadConcernedNatural UnibrowNatural UpDown UpDownNatural'.split(' '),
 mouth:'Concerned Default Disbelief Eating Grimace Sad ScreamOpen Serious Smile Tongue Twinkle Vomit'.split(' ')
};
// two probe colours per slot; a part is rendered with each and the results must agree once tokenised
const C={hair:['Auburn','#A55728','Red','#C93305'],hat:['Pink','#FF488E','PastelGreen','#A7FFC4'],
  fhair:['Auburn','#A55728','Red','#C93305'],cloth:['Pink','#FF488E','PastelGreen','#A7FFC4']};
function render(p){
  const h=S.renderToStaticMarkup(React.createElement(Avatar,Object.assign({avatarStyle:'Transparent',
    topType:'NoHair',accessoriesType:'Blank',facialHairType:'Blank',clotheType:'ShirtCrewNeck',
    eyeType:'Default',eyebrowType:'Default',mouthType:'Default',skinColor:'Light'},p)));
  const doc=new JSDOM(h).window.document;
  const root=[...doc.querySelectorAll('g')].find(g=>g.getAttribute('id')==='Avataaar'&&g.getAttribute('mask'));
  return {doc,root,kids:[...root.children]};
}
const byId=(root,pre)=>[...root.querySelectorAll('g')].find(g=>(g.getAttribute('id')||'').startsWith(pre));
function chain(el,stop){const t=[];for(let e=el.parentElement;e&&e!==stop;e=e.parentElement){const x=e.getAttribute('transform');if(x)t.unshift(x.trim());}return t.join(' ');}
function num(s){return s.replace(/-?\d*\.\d{3,}(e-?\d+)?/g,m=>{let v=(+parseFloat(m).toFixed(2));return String(Object.is(v,-0)?0:v);});}
function clean(html,slots){
  // stable local ids
  const ids={};let n=0;
  html=html.replace(/react-(mask|path|filter)-\d+/g,m=>ids[m]||(ids[m]='@@'+(n++)));
  html=html.replace(/ id="(?!@@)[^"]*"/g,'');
  html=html.replace(/<desc>.*?<\/desc>/g,'').replace(/ xmlns:xlink="[^"]*"/g,'');
  html=html.replace(/(\d)\.0+(?=[\s,)"])/g,'$1');
  html=num(html);
  for(const [hex,tok] of slots) html=html.split(hex).join(tok).split(hex.toLowerCase()).join(tok);
  return html;
}
function two(mk,slotsFor){ // render with probe A and B, tokenise, assert equal
  const a=clean(mk(0),slotsFor(0)), b=clean(mk(1),slotsFor(1));
  if(a!==b) throw new Error('colour slot collision');
  return a;
}
const P={top:{},accessories:{},facialHair:{},clothes:{},graphic:{},eyes:{},eyebrow:{},mouth:{}},META={topUses:{},chains:{}};
const hex=(k,i)=>C[k][i*2+1], name=(k,i)=>C[k][i*2];
for(const t of O.top){
  P.top[t]=two(i=>render({topType:t,hairColor:name('hair',i),hatColor:name('hat',i)}).kids[3].outerHTML,
               i=>[[hex('hair',i),'{hair}'],[hex('hat',i),'{hat}']]);
  META.topUses[t]={hair:P.top[t].includes('{hair}'),hat:P.top[t].includes('{hat}')};
  // where do facial hair and accessories sit under this top?
  const r=render({topType:t,facialHairType:'BeardLight',accessoriesType:'Round'});
  const f=byId(r.root,'Facial-Hair/'),a=byId(r.root,'Top/_Resources/');
  META.chains[t]={f:f?chain(f,r.root)+'|'+(f.parentElement.closest('[mask]')!==null&&f.parentElement.closest('[mask]')!==r.root):null,
                  a:a?chain(a,r.root):null};
}
for(const v of O.facialHair){ if(v==='Blank'){P.facialHair[v]='';continue;}
  P.facialHair[v]=two(i=>byId(render({facialHairType:v,facialHairColor:name('fhair',i)}).root,'Facial-Hair/').outerHTML,i=>[[hex('fhair',i),'{fhair}']]);}
for(const v of O.accessories){ if(v==='Blank'){P.accessories[v]='';continue;}
  P.accessories[v]=clean(byId(render({accessoriesType:v}).root,'Top/_Resources/').outerHTML,[]);}
for(const v of O.clothes){
  P.clothes[v]=two(i=>{const r=render({clotheType:v,clotheColor:name('cloth',i),graphicType:'Bat'});const g=byId(r.root,'Clothing/Graphic/');if(g)g.outerHTML='<!--G-->';return r.kids[1].outerHTML;},
    i=>[[hex('cloth',i),'{cloth}']]);}
// A hospital gown. Not part of avataaars: the crew neck's outline with a print and a neck seam,
// added here so the art file stays the single vocabulary of what can be drawn.
{let dots='';for(let y=34;y<112;y+=13)for(let x=34+(((y/13)|0)%2)*9;x<232;x+=18)dots+='<circle cx="'+x+'" cy="'+y+'" r="1.7"></circle>';
 const base=P.clothes.ShirtCrewNeck,tail='</g></g></g>';
 if(!base.endsWith(tail)||!base.includes('id="@@1"')) throw new Error('crew neck changed shape; redo the gown');
 P.clothes.HospitalGown=base.slice(0,-tail.length)+'</g></g><g mask="url(#@@1)" fill="#fff" fill-opacity=".55">'+dots+'</g><path d="M99 29.4 C99 42.2 114 51.8 132.5 51.8 C151 51.8 166 42.2 166 30" fill="none" stroke="#000" stroke-opacity=".14" stroke-width="3" mask="url(#@@1)"></path></g>';
 O.clothes.unshift('HospitalGown');}
for(const v of O.graphic){const r=render({clotheType:'GraphicShirt',graphicType:v});const g=byId(r.root,'Clothing/Graphic/');
  // Upstream masks each graphic with the SHIRT's mask. Cut out on its own, that reference
  // points at an id the graphic does not carry and patient.js prefixes differently, so it
  // dangled. Every graphic sits well inside the shirt, so the mask did nothing: drop it.
  g.removeAttribute('mask');
  P.graphic[v]=clean(g.outerHTML,[]);}
// no part may reference an id it does not define: parts are prefixed one at a time
for(const grp in P){if(typeof P[grp]==='string')continue;for(const k in P[grp]){const src=P[grp][k];
  const ids=new Set([...src.matchAll(/id="(@@\d+)"/g)].map(m=>m[1]));
  const bad=[...src.matchAll(/#(@@\d+)/g)].map(m=>m[1]).filter(x=>!ids.has(x));
  if(bad.length) throw new Error('dangling reference in '+grp+'/'+k+': '+bad.join());}}
[['eyes','eyeType',2],['eyebrow','eyebrowType',3],['mouth','mouthType',0]].forEach(([k,prop,idx])=>{
  for(const v of O[k]){const r=render({[prop]:v});P[k][v]=clean(r.kids[2].children[idx].outerHTML,[]);}});
// Two eye drawings avataaars does not have, for reduced alertness: a heavy upper lid over
// the default eye, and a lid so low only a sliver shows. Same coordinates, group transform
// and opacity as eyes/Default, so they swap in place. The lid is the top of the eye cut off
// along a chord with a rounded line laid on the cut.
{const eye=(cx,c)=>{const w=Math.sqrt(36-(c-22)*(c-22)).toFixed(2),big=c<22?1:0;   // from the right end of the chord, clockwise through the bottom, to the left end
   return '<path d="M'+(cx+ +w).toFixed(2)+','+c+' A6,6 0 '+big+' 1 '+(cx-w).toFixed(2)+','+c+' Z"></path>'
     +'<path d="M'+(cx-w-1.2).toFixed(2)+','+(c+0.3)+' Q'+cx+','+(c-1.3)+' '+(cx+ +w+1.2).toFixed(2)+','+(c+0.3)+'" fill="none" stroke="#000000" stroke-width="1.8" stroke-linecap="round"></path>';};
 const mk=c=>'<g transform="translate(0, 8)" fill-opacity="0.6">'+eye(30,c)+eye(82,c)+'</g>';
 P.eyes.Drowsy=mk(19.6); P.eyes.Heavy=mk(24.2); O.eyes.push('Drowsy','Heavy');}
const r0=render({});
P.nose=clean(r0.kids[2].children[1].outerHTML,[]);
const bodyDefs=r0.doc.querySelector('defs').outerHTML;
P.body=clean(bodyDefs+r0.kids[0].outerHTML,[['#EDB98A','{skin}']]);

const defsPaths=[...r0.doc.querySelector('defs').querySelectorAll('path')].map(p=>num(p.getAttribute('d')));
const B={clip:defsPaths[0],body:defsPaths[1],neck:num([...r0.kids[0].querySelectorAll('path')].pop().getAttribute('d'))};
delete P.body;
const noFacialHair=Object.keys(META.chains).filter(t=>META.chains[t].f===null),noAccessories=Object.keys(META.chains).filter(t=>META.chains[t].a===null);
console.log('noFacialHair',noFacialHair,'noAccessories',noAccessories);
const COLORS={
 skin:{Tanned:'#FD9841',Yellow:'#F8D25C',Pale:'#FFDBB4',Light:'#EDB98A',Brown:'#D08B5B',DarkBrown:'#AE5D29',Black:'#614335'},
 hair:{Auburn:'#A55728',Black:'#2C1B18',Blonde:'#B58143',BlondeGolden:'#D6B370',Brown:'#724133',BrownDark:'#4A312C',PastelPink:'#F59797',Blue:'#000fdb',Platinum:'#ECDCBF',Red:'#C93305',SilverGray:'#E8E1E1'},
 facialHair:{Auburn:'#A55728',Black:'#2C1B18',Blonde:'#B58143',BlondeGolden:'#D6B370',Brown:'#724133',BrownDark:'#4A312C',Platinum:'#ECDCBF',Red:'#C93305',SilverGray:'#E8E1E1'},
 fabric:{Black:'#262E33',Blue01:'#65C9FF',Blue02:'#5199E4',Blue03:'#25557C',Gray01:'#E6E6E6',Gray02:'#929598',Heather:'#3C4F5C',PastelBlue:'#B1E2FF',PastelGreen:'#A7FFC4',PastelOrange:'#FFDEB5',PastelRed:'#FFAFB9',PastelYellow:'#FFFFB1',Pink:'#FF488E',Red:'#FF5C5C',White:'#FFFFFF'}};
fs.writeFileSync(OUT,JSON.stringify({added:{clothes:['HospitalGown'],eyebrow:['FrownNatural'],eyes:['Drowsy','Heavy']},source:'github.com/fangpenlin/avataaars @93aa902, MIT, (c) 2017 Pablo Stanley, Fang-Pen Lin',parts:P,body:B,options:O,colors:COLORS,topUses:META.topUses,noFacialHair,noAccessories}));

const sz=k=>JSON.stringify(P[k]).length;
console.log(Object.keys(P).map(k=>k+':'+sz(k)).join(' '),'total',JSON.stringify(P).length);
const cf=new Set(Object.values(META.chains).map(c=>c.f)),ca=new Set(Object.values(META.chains).map(c=>c.a));
console.log('facial chains',[...cf]);console.log('acc chains',[...ca]);
console.log(Object.entries(META.topUses).map(([k,v])=>k+':'+(v.hair?'H':'')+(v.hat?'T':'')).join(' '));
