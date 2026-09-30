#!/usr/bin/env python3
"""
Card Studio - turn screenshots into rounded, captioned cards for your GitHub README.

Run it:
    python card_studio.py

It starts a small server on your own computer (127.0.0.1 only) and opens your browser.
There you can import images, write a title and description for each one, change every
color, and export a zip of SVG files (or SVG + PNG + a ready-made README snippet).

Uses only Python's standard library. No pip install needed.
Press Ctrl+C in the terminal to stop it.
"""
import http.server
import json
import threading
import webbrowser
from pathlib import Path

SETTINGS_FILE = Path(__file__).with_name("card_studio_settings.json")
PORTS = (8765, 8766, 8767, 0)  # 0 = let the OS pick a free one

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Card Studio</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--bg:#0b1414;--panel:#101d1d;--panel2:#152626;--line:#213838;--fog:#c9d6d0;--muted:#7f9b91;--accent:#8fb3a5}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--fog);font:14px/1.45 'Segoe UI',system-ui,-apple-system,sans-serif;display:grid;grid-template-columns:330px 1fr;min-height:100vh}
aside{background:var(--panel);border-right:1px solid var(--line);padding:18px 18px 28px;position:sticky;top:0;height:100vh;overflow:auto}
main{padding:22px 26px 60px;min-width:0}
h1{font:600 21px Georgia,serif;margin:0 0 2px;letter-spacing:.5px}
.sub{color:var(--muted);font-size:12px;margin-bottom:6px}
h2{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin:20px 0 8px;font-weight:600}
.row{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:7px 0}
.rg{display:flex;gap:8px;align-items:center}
input[type=color]{width:44px;height:26px;padding:0;border:1px solid var(--line);background:none;border-radius:6px;cursor:pointer}
input[type=range]{width:140px;accent-color:var(--accent)}
input[type=text],select,textarea{background:var(--bg);color:var(--fog);border:1px solid var(--line);border-radius:8px;padding:7px 9px;font:inherit;width:100%}
select{width:auto;min-width:120px}
textarea{resize:vertical;min-height:70px}
input:focus,select:focus,textarea:focus{outline:1px solid var(--accent);border-color:var(--accent)}
button{font:inherit;color:var(--fog);background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:7px 12px;cursor:pointer}
button:hover:not(:disabled){border-color:var(--accent)}
button:disabled{opacity:.5;cursor:default}
button.primary{background:var(--accent);color:#0b1414;border-color:var(--accent);font-weight:600}
.presets{display:flex;flex-wrap:wrap;gap:6px}
.presets button{padding:4px 10px;font-size:12px}
.val{color:var(--muted);width:30px;text-align:right;font-variant-numeric:tabular-nums}
.stack{display:flex;flex-direction:column;gap:8px}
.stack label{color:var(--muted);font-size:12px;margin-bottom:-4px}
#drop{border:2px dashed var(--line);border-radius:14px;padding:26px;text-align:center;color:var(--muted);cursor:pointer;transition:.15s}
#drop.over,#drop:hover{border-color:var(--accent);color:var(--fog);background:var(--panel)}
#drop b{color:var(--fog)}
.item{display:grid;grid-template-columns:minmax(220px,340px) 1fr;gap:20px;margin-top:18px;padding:16px;background:var(--panel);border:1px solid var(--line);border-radius:14px}
.pv{border-radius:10px;padding:14px;display:flex;align-items:flex-start;justify-content:center}
.pv img{width:100%;display:block}
.fields{display:flex;flex-direction:column;gap:9px;min-width:0}
.top{display:flex;justify-content:space-between;align-items:center;gap:8px}
.fname{color:var(--muted);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.btns{display:flex;gap:4px}
.btns button{padding:3px 9px}
.hint{color:var(--muted);font-size:12px;margin-top:4px}
#status{margin-top:12px;font-size:12px;color:var(--accent);min-height:16px}
.empty{color:var(--muted);text-align:center;padding:40px 0}
@media(max-width:900px){body{grid-template-columns:1fr}aside{position:static;height:auto}.item{grid-template-columns:1fr}}
</style>
</head>
<body>
<aside>
  <h1>Card Studio</h1>
  <div class="sub">Screenshots in, rounded cards out.</div>

  <h2>Presets</h2>
  <div class="presets" id="presets"></div>

  <h2>Colors</h2>
  <div class="row"><span>Card background</span><input type="color" data-k="bg"></div>
  <div class="row"><span>Title</span><input type="color" data-k="title"></div>
  <div class="row"><span>Description</span><input type="color" data-k="desc"></div>
  <div class="row"><span>Border</span><input type="color" data-k="border"></div>
  <div class="row"><span>Border strength</span><div class="rg"><input type="range" min="0" max="1" step="0.05" data-k="borderOpacity"><span class="val" data-v="borderOpacity"></span></div></div>
  <div class="row"><span>Preview background</span><input type="color" data-k="pvbg"></div>

  <h2>Shape and text</h2>
  <div class="row"><span>Corner radius</span><div class="rg"><input type="range" min="0" max="90" data-k="radius"><span class="val" data-v="radius"></span></div></div>
  <div class="row"><span>Title size</span><div class="rg"><input type="range" min="24" max="64" data-k="titleSize"><span class="val" data-v="titleSize"></span></div></div>
  <div class="row"><span>Description size</span><div class="rg"><input type="range" min="20" max="52" data-k="descSize"><span class="val" data-v="descSize"></span></div></div>
  <div class="row"><span>Max description lines</span><div class="rg"><input type="range" min="1" max="5" data-k="maxLines"><span class="val" data-v="maxLines"></span></div></div>
  <div class="row"><span>Font</span><select data-k="font"><option value="sans">Sans (Segoe UI)</option><option value="serif">Serif (Georgia)</option><option value="mono">Mono (Consolas)</option></select></div>

  <h2>Export</h2>
  <div class="row"><span>PNG size</span><select data-k="scale"><option value="1">1x (720 px)</option><option value="2">2x (1440 px)</option><option value="3">3x (2160 px)</option></select></div>
  <div class="stack">
    <label>Folder in your repo</label><input type="text" data-k="folder">
    <label>Where the cards link to</label><input type="text" data-k="link">
  </div>
  <div class="row"><span>Snippet uses</span><select data-k="snipFmt"><option value="png">PNG</option><option value="svg">SVG</option></select></div>
  <div class="stack" style="margin-top:12px">
    <button class="primary exp" id="expAll">Export all (.zip)</button>
    <button class="exp" id="expSvg">Export SVG files (.zip)</button>
  </div>
  <div class="hint">All = SVG + PNG + a README snippet with your links already filled in.</div>
  <div id="status"></div>
</aside>

<main>
  <div id="drop"><b>Drop screenshots here</b>, paste them, or click to import
    <div class="hint">JPG, PNG or WebP. Add as many as you like.</div>
    <input id="file" type="file" accept="image/*" multiple hidden>
  </div>
  <div id="list"></div>
</main>

<script>
// ==PURE==
const W=720, IMG_H=405, PAD=32, GAP_T=14, LINE_GAP=8;
const FONTS={
  sans:"'Segoe UI', -apple-system, 'Helvetica Neue', Arial, sans-serif",
  serif:"Georgia, 'Times New Roman', serif",
  mono:"ui-monospace, Consolas, Menlo, monospace"
};
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

function wrapText(text, measure, maxW, maxLines){
  const words=text.split(/\s+/).filter(Boolean);
  let lines=[], cur='';
  for(const w of words){
    const t=cur?cur+' '+w:w;
    if(!cur||measure(t)<=maxW){cur=t;}else{lines.push(cur);cur=w;}
  }
  if(cur)lines.push(cur);
  const cut=l=>{ while(l.length>1&&measure(l)>maxW) l=l.slice(0,-1).replace(/\s+$/,''); return l; };
  if(lines.length>maxLines){
    lines=lines.slice(0,maxLines);
    let l=lines[maxLines-1];
    while(l.length>1&&measure(l+'…')>maxW) l=l.slice(0,-1);
    lines[maxLines-1]=l.replace(/\s+$/,'')+'…';
  }
  return lines.map(l=>measure(l)>maxW?cut(l.replace(/…$/,''))+'…':l);
}

function computeLayout(cards, S, mk){
  const fam=FONTS[S.font]||FONTS.sans;
  const mt=mk(700,S.titleSize,fam), md=mk(400,S.descSize,fam);
  const maxW=(W-2*PAD)*0.93;              // safety margin: other people's fonts differ a little
  const titles=cards.map(c=>c.title.trim()?wrapText(c.title.trim(),mt,maxW,1)[0]:'');
  const lines=cards.map(c=>c.desc.trim()?wrapText(c.desc.trim(),md,maxW,S.maxLines):[]);
  const hasTitle=titles.some(Boolean);
  const nl=Math.max(0,...lines.map(l=>l.length));
  let cap=0;
  if(hasTitle||nl){
    cap=PAD+(hasTitle?S.titleSize:0);
    if(nl) cap+=(hasTitle?GAP_T:0)+nl*S.descSize+(nl-1)*LINE_GAP;
    cap+=PAD;
  }
  return {H:IMG_H+cap, hasTitle, titles, lines, fam};
}

function buildSvg(i, card, S, L, imgSrc){
  const H=L.H, R=Math.max(0,Math.min(S.radius,H/2,W/2));
  const id='c'+i, fam=esc(L.fam);
  let y=IMG_H+PAD, body='';
  if(L.hasTitle){
    if(L.titles[i]) body+=`<text x="${PAD}" y="${(y+S.titleSize*0.8).toFixed(1)}" font-family="${fam}" font-size="${S.titleSize}" font-weight="700" fill="${S.title}">${esc(L.titles[i])}</text>`;
    y+=S.titleSize+GAP_T;
  }
  for(const ln of L.lines[i]){
    body+=`<text x="${PAD}" y="${(y+S.descSize*0.8).toFixed(1)}" font-family="${fam}" font-size="${S.descSize}" fill="${S.desc}">${esc(ln)}</text>`;
    y+=S.descSize+LINE_GAP;
  }
  const par=card.fit==='contain'?'xMidYMid meet':'xMidYMid slice';
  return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">`
   +`<defs><clipPath id="${id}"><rect width="${W}" height="${H}" rx="${R}"/></clipPath></defs>`
   +`<g clip-path="url(#${id})"><rect width="${W}" height="${H}" fill="${S.bg}"/>`
   +`<image xlink:href="${imgSrc}" x="0" y="0" width="${W}" height="${IMG_H}" preserveAspectRatio="${par}"/>${body}</g>`
   +`<rect x="1" y="1" width="${W-2}" height="${H-2}" rx="${Math.max(R-1,0)}" fill="none" stroke="${S.border}" stroke-opacity="${S.borderOpacity}" stroke-width="2"/></svg>`;
}

const CRC=(()=>{const t=[];for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;})();
function crc32(b){let c=0xFFFFFFFF;for(let i=0;i<b.length;i++)c=CRC[(c^b[i])&255]^(c>>>8);return(c^0xFFFFFFFF)>>>0;}
function zip(files){               // files: [{name, data:Uint8Array}] -> Blob (no compression)
  const enc=new TextEncoder(), parts=[], central=[]; let off=0;
  for(const f of files){
    const name=enc.encode(f.name), d=f.data, crc=crc32(d);
    const l=new DataView(new ArrayBuffer(30));
    l.setUint32(0,0x04034b50,true);l.setUint16(4,20,true);l.setUint16(6,0x0800,true);l.setUint16(8,0,true);
    l.setUint16(10,0,true);l.setUint16(12,0x21,true);l.setUint32(14,crc,true);l.setUint32(18,d.length,true);
    l.setUint32(22,d.length,true);l.setUint16(26,name.length,true);l.setUint16(28,0,true);
    parts.push(new Uint8Array(l.buffer),name,d);
    const c=new DataView(new ArrayBuffer(46));
    c.setUint32(0,0x02014b50,true);c.setUint16(4,20,true);c.setUint16(6,20,true);c.setUint16(8,0x0800,true);
    c.setUint16(10,0,true);c.setUint16(12,0,true);c.setUint16(14,0x21,true);c.setUint32(16,crc,true);
    c.setUint32(20,d.length,true);c.setUint32(24,d.length,true);c.setUint16(28,name.length,true);
    c.setUint32(42,off,true);
    central.push(new Uint8Array(c.buffer),name);
    off+=30+name.length+d.length;
  }
  const size=central.reduce((a,b)=>a+b.length,0);
  const e=new DataView(new ArrayBuffer(22));
  e.setUint32(0,0x06054b50,true);e.setUint16(8,files.length,true);e.setUint16(10,files.length,true);
  e.setUint32(12,size,true);e.setUint32(16,off,true);
  return new Blob([...parts,...central,new Uint8Array(e.buffer)],{type:'application/zip'});
}

function makeSnippet(bases, ext, S){
  const per=4, w=((100-1.42*(per-1))/per).toFixed(3);
  const sp=`<img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg'></svg>" width="1.42%" />`;
  const rows=[];
  for(let i=0;i<bases.length;i+=per){
    const items=bases.slice(i,i+per).map(b=>`<a href="${S.link}"><img src="./${S.folder}/${b}.${ext}" width="${w}%" /></a>`);
    rows.push(`<div align="center">\n  <nobr>\n    ${items.join(`<!--\n-->${sp}<!--\n-->`)}\n  </nobr>\n</div>`);
  }
  return rows.join('\n\n')+'\n';
}
// ==END PURE==

const $=s=>document.querySelector(s);
const DEFAULTS={bg:'#0e1c1c',title:'#c9d6d0',desc:'#7f9b91',border:'#c9d6d0',borderOpacity:0.22,pvbg:'#0d1117',
  radius:36,titleSize:40,descSize:32,maxLines:3,font:'sans',scale:2,folder:'Assets',link:'https://abirockgames.itch.io/',snipFmt:'png'};
const NUM=new Set(['borderOpacity','radius','titleSize','descSize','maxLines','scale']);
const PRESETS={
  Forest:{bg:'#0e1c1c',title:'#c9d6d0',desc:'#7f9b91',border:'#c9d6d0'},
  Midnight:{bg:'#0a1220',title:'#d5e2f5',desc:'#7d93b3',border:'#7d93b3'},
  Ember:{bg:'#1c100c',title:'#f0d9c8',desc:'#a88b78',border:'#e8a06a'},
  Blood:{bg:'#160a0a',title:'#f2dada',desc:'#a37f7f',border:'#a63d2f'},
  Ash:{bg:'#161616',title:'#ececec',desc:'#8c8c8c',border:'#ffffff'}
};
const S={...DEFAULTS};
let cards=[], nextId=1;

const cx=document.createElement('canvas').getContext('2d');
const mk=(weight,size,fam)=>t=>{cx.font=`${weight} ${size}px ${fam}`;return cx.measureText(t).width;};
const say=m=>{$('#status').textContent=m;};

let saveT; function save(){clearTimeout(saveT);saveT=setTimeout(()=>fetch('/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(S)}).catch(()=>{}),400);}
let raf; function schedule(){cancelAnimationFrame(raf);raf=requestAnimationFrame(renderPreviews);}

function syncControls(){
  document.querySelectorAll('[data-k]').forEach(el=>{
    el.value=S[el.dataset.k];
    const v=document.querySelector(`[data-v="${el.dataset.k}"]`); if(v)v.textContent=S[el.dataset.k];
  });
  document.querySelectorAll('.pv').forEach(p=>p.style.background=S.pvbg);
}
document.querySelectorAll('[data-k]').forEach(el=>{
  el.addEventListener('input',()=>{
    const k=el.dataset.k; S[k]=NUM.has(k)?+el.value:el.value;
    const v=document.querySelector(`[data-v="${k}"]`); if(v)v.textContent=S[k];
    if(k==='pvbg')document.querySelectorAll('.pv').forEach(p=>p.style.background=S.pvbg);
    save(); schedule();
  });
});
for(const [name,p] of Object.entries(PRESETS)){
  const b=document.createElement('button'); b.textContent=name;
  b.onclick=()=>{Object.assign(S,p);syncControls();save();schedule();};
  $('#presets').appendChild(b);
}

function renderPreviews(){
  const L=computeLayout(cards,S,mk);
  cards.forEach((c,i)=>{
    const img=document.getElementById('pv'+c.id); if(!img)return;
    const u=URL.createObjectURL(new Blob([buildSvg(i,c,S,L,c.thumb)],{type:'image/svg+xml'}));
    const old=img.dataset.u; img.src=u; img.dataset.u=u;
    if(old)setTimeout(()=>URL.revokeObjectURL(old),500);
  });
}
function renderList(){
  const list=$('#list');
  if(!cards.length){list.innerHTML='<div class="empty">No images yet. Import some to get started.</div>';return;}
  list.innerHTML=cards.map(c=>`<div class="item" data-id="${c.id}">
    <div class="pv" style="background:${S.pvbg}"><img id="pv${c.id}" alt=""></div>
    <div class="fields">
      <div class="top"><span class="fname">${esc(c.name)}</span><span class="btns"><button data-a="up" title="Move up">↑</button><button data-a="down" title="Move down">↓</button><button data-a="del" title="Remove">✕</button></span></div>
      <input type="text" data-f="title" placeholder="Title (e.g. The Jungle Area)" value="${esc(c.title)}">
      <textarea data-f="desc" placeholder="Description (e.g. Shows the Jungle Area at night)">${esc(c.desc)}</textarea>
      <div class="row"><span>Image fit</span><select data-f="fit"><option value="cover">Fill (crop to fit)</option><option value="contain">Show whole image</option></select></div>
    </div></div>`).join('');
  cards.forEach(c=>{list.querySelector(`[data-id="${c.id}"] select`).value=c.fit;});
  renderPreviews();
}
$('#list').addEventListener('input',e=>{
  const f=e.target.dataset.f; if(!f)return;
  const c=cards.find(c=>c.id===+e.target.closest('.item').dataset.id); c[f]=e.target.value; schedule();
});
$('#list').addEventListener('click',e=>{
  const b=e.target.closest('button[data-a]'); if(!b)return;
  const id=+b.closest('.item').dataset.id, i=cards.findIndex(c=>c.id===id), a=b.dataset.a;
  if(a==='del')cards.splice(i,1);
  else if(a==='up'&&i>0)[cards[i-1],cards[i]]=[cards[i],cards[i-1]];
  else if(a==='down'&&i<cards.length-1)[cards[i+1],cards[i]]=[cards[i],cards[i+1]];
  renderList();
});

async function addFiles(files){
  const imgs=[...files].filter(f=>f.type.startsWith('image/')); if(!imgs.length)return;
  say(`Importing ${imgs.length}...`);
  for(const f of imgs){
    try{
      const bmp=await createImageBitmap(f), jpg=f.type==='image/jpeg';
      const enc=maxW=>{
        const s=Math.min(1,maxW/bmp.width), c=document.createElement('canvas');
        c.width=Math.round(bmp.width*s); c.height=Math.round(bmp.height*s);
        const g=c.getContext('2d'); g.imageSmoothingQuality='high'; g.drawImage(bmp,0,0,c.width,c.height);
        return jpg?c.toDataURL('image/jpeg',0.88):c.toDataURL('image/png');
      };
      cards.push({id:nextId++,name:f.name.replace(/\.[^.]+$/,'')||'image',title:'',desc:'',fit:'cover',full:enc(1440),thumb:enc(720)});
    }catch(err){say('Could not read '+f.name);}
  }
  say(''); renderList();
}
const drop=$('#drop'), fileIn=$('#file');
drop.onclick=()=>fileIn.click();
fileIn.onchange=()=>{addFiles(fileIn.files);fileIn.value='';};
drop.addEventListener('dragover',e=>{e.preventDefault();drop.classList.add('over');});
drop.addEventListener('dragleave',()=>drop.classList.remove('over'));
drop.addEventListener('drop',e=>{e.preventDefault();drop.classList.remove('over');addFiles(e.dataTransfer.files);});
window.addEventListener('paste',e=>{if(e.clipboardData&&e.clipboardData.files.length)addFiles(e.clipboardData.files);});
window.addEventListener('dragover',e=>e.preventDefault());
window.addEventListener('drop',e=>e.preventDefault());

function baseNames(){
  const used=new Map();
  return cards.map(c=>{
    const b='card-'+(c.name.replace(/[^\w.-]+/g,'-')||'image'), n=used.get(b)||0; used.set(b,n+1);
    return n?`${b}-${n+1}`:b;
  });
}
function svgToPng(svg,H,scale){
  return new Promise((res,rej)=>{
    const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml;charset=utf-8'})), img=new Image();
    img.onload=()=>{
      const c=document.createElement('canvas'); c.width=W*scale; c.height=H*scale;
      c.getContext('2d').drawImage(img,0,0,c.width,c.height); URL.revokeObjectURL(url);
      c.toBlob(b=>b?res(b):rej(new Error('PNG failed')),'image/png');
    };
    img.onerror=()=>{URL.revokeObjectURL(url);rej(new Error('Could not render a card to PNG'));};
    img.src=url;
  });
}
function download(blob,name){
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name;
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(a.href),4000);
}
async function doExport(kind){
  if(!cards.length){say('Import some images first.');return;}
  const btns=[...document.querySelectorAll('.exp')]; btns.forEach(b=>b.disabled=true); say('Building files...');
  try{
    const L=computeLayout(cards,S,mk), bases=baseNames(), enc=new TextEncoder(), files=[], all=kind==='all';
    for(let i=0;i<cards.length;i++){
      const svg=buildSvg(i,cards[i],S,L,cards[i].full);
      files.push({name:(all?'svg/':'')+bases[i]+'.svg',data:enc.encode(svg)});
      if(all){
        const png=await svgToPng(svg,L.H,S.scale);
        files.push({name:'png/'+bases[i]+'.png',data:new Uint8Array(await png.arrayBuffer())});
        say(`Rendered ${i+1} of ${cards.length}...`);
      }
    }
    if(all)files.push({name:'README-snippet.md',data:enc.encode(makeSnippet(bases,S.snipFmt,S))});
    download(zip(files),all?'cards-export.zip':'cards-svg.zip');
    say(all?'Done. cards-export.zip has svg/, png/ and README-snippet.md.':'Done. cards-svg.zip downloaded.');
  }catch(err){console.error(err);say('Export failed: '+err.message);}
  finally{btns.forEach(b=>b.disabled=false);}
}
$('#expAll').onclick=()=>doExport('all');
$('#expSvg').onclick=()=>doExport('svg');

(async()=>{
  try{
    const r=await fetch('/settings');
    if(r.ok){const d=await r.json();for(const k of Object.keys(DEFAULTS))if(k in d)S[k]=d[k];}
  }catch(e){}
  syncControls(); renderList();
})();
</script>
</body>
</html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the terminal quiet

    def _send(self, code, body, ctype):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, HTML, "text/html; charset=utf-8")
        elif self.path == "/settings":
            try:
                text = SETTINGS_FILE.read_text(encoding="utf-8")
                json.loads(text)
            except Exception:
                text = "{}"
            self._send(200, text, "application/json")
        else:
            self._send(404, "Not found", "text/plain")

    def do_POST(self):
        if self.path != "/settings":
            return self._send(404, "Not found", "text/plain")
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if not 0 < n < 20000:
                raise ValueError("bad size")
            data = json.loads(self.rfile.read(n))
            ok = isinstance(data, dict) and len(data) < 40 and all(
                isinstance(k, str) and len(k) < 40 and isinstance(v, (str, int, float)) and len(str(v)) < 500
                for k, v in data.items()
            )
            if not ok:
                raise ValueError("bad settings")
            SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self._send(200, "{}", "application/json")
        except Exception:
            self._send(400, "{}", "application/json")


def main():
    server = None
    for port in PORTS:
        try:
            server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    if server is None:
        raise SystemExit("Could not open a local port.")
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Card Studio is running at {url}")
    print("Your browser should open by itself. Press Ctrl+C here to stop.")
    threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()