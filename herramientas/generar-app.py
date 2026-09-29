# -*- coding: utf-8 -*-
"""Genera la app de pedidos de General Distribution en un solo archivo HTML."""
import json, io, os, re

# Rutas relativas a esta carpeta: el molde viaja junto con el repositorio.
AQUI   = os.path.dirname(os.path.abspath(__file__))
SRC    = os.path.join(AQUI, "catalogo-shopify-2026-09-28.json")   # <- cambiar al bajar catalogo nuevo
OUTDIR = os.path.dirname(AQUI)                                    # index.html se escribe arriba
if not os.path.isdir(OUTDIR):
    os.makedirs(OUTDIR)

raw = json.load(io.open(SRC, encoding="utf-8"))
LOGO = io.open(os.path.join(AQUI, "logo_datauri.txt"), encoding="utf-8").read().strip()

prods = []
for p in raw:
    v = (p.get("variants") or [{}])[0]
    try:
        price = float(v.get("price") or 0)
    except Exception:
        price = 0.0
    imgs = p.get("images") or []
    src = imgs[0]["src"] if imgs else ""
    if src and "?" in src:
        src = src + "&width=300"
    elif src:
        src = src + "?width=300"
    cat = (p.get("product_type") or "").strip() or "Otros"
    prods.append({
        "i": p["id"],
        "t": (p.get("title") or "").strip(),
        "p": round(price, 2),
        "c": cat,
        "f": src,
        "d": 1 if v.get("available") else 0,
    })

prods.sort(key=lambda x: x["t"].lower())

cats = {}
for p in prods:
    cats[p["c"]] = cats.get(p["c"], 0) + 1
cat_list = sorted(cats.items(), key=lambda kv: -kv[1])

data_js = json.dumps(prods, ensure_ascii=False, separators=(",", ":"))
cats_js = json.dumps([c for c, n in cat_list], ensure_ascii=False)

HTML = u"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>Pedidos &middot; General Distribution</title>
<link rel="icon" href="logo-gd.png">
<link rel="apple-touch-icon" href="logo-gd.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Pedidos GD">
<meta name="theme-color" content="#1f2937">
<style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
     background:#f4f5f7;color:#16191d;font-size:15px;padding-bottom:78px}
header{background:#1f2937;color:#fff;padding:10px 12px;position:sticky;top:0;z-index:50;
       box-shadow:0 1px 6px rgba(0,0,0,.25)}
.hd{display:table;width:100%}
.hd .lg{display:table-cell;width:46px;vertical-align:middle}
.hd .lg img{width:42px;height:42px;display:block;border-radius:50%}
.hd .tx{display:table-cell;vertical-align:middle;padding-left:10px}
.brand{font-weight:700;font-size:17px;letter-spacing:.2px;line-height:1.15}
.sub{opacity:.6;font-weight:400;font-size:12.5px}
.tienda{margin-top:8px;display:block;width:100%;padding:11px 12px;border:0;border-radius:8px;
        font-size:16px;background:#fff;color:#16191d}
.tienda::placeholder{color:#9aa1ab}
.tools{background:#fff;padding:9px 12px;border-bottom:1px solid #e3e6ea;position:sticky;top:0;z-index:40}
#q{width:100%;padding:11px 12px;font-size:16px;border:1px solid #d5d9df;border-radius:8px;background:#f8f9fa}
.chips{display:block;white-space:nowrap;overflow-x:auto;margin-top:9px;padding-bottom:2px}
.chip{display:inline-block;padding:7px 13px;margin-right:6px;border-radius:999px;background:#eef0f3;
      color:#48505a;font-size:13px;font-weight:600;border:0}
.chip.on{background:#1f2937;color:#fff}
.count{padding:9px 13px;color:#6b7280;font-size:13px}
.grid{padding:0 8px}
.card{background:#fff;border-radius:10px;margin-bottom:8px;padding:9px;display:table;width:100%;
      box-shadow:0 1px 2px rgba(16,24,40,.07)}
.cell{display:table-cell;vertical-align:middle}
.ph{width:68px}
.ph img{width:60px;height:60px;object-fit:contain;border-radius:6px;background:#f4f5f7;display:block}
.noimg{width:60px;height:60px;border-radius:6px;background:#f0f1f3;display:block}
.info{padding:0 8px}
.name{font-weight:600;line-height:1.25;font-size:14px}
.meta{color:#6b7280;font-size:12px;margin-top:3px}
.price{font-weight:700;color:#0f7b3f;font-size:15px;margin-top:3px}
.nop{font-weight:600;color:#b45309;font-size:12px;margin-top:3px}
.agot{color:#b91c1c;font-size:11px;font-weight:700}
.stp{width:104px;text-align:right;white-space:nowrap}
.b{width:32px;height:32px;border-radius:8px;border:1px solid #d5d9df;background:#fff;
   font-size:19px;font-weight:700;color:#1f2937;line-height:1;padding:0;vertical-align:middle}
.b:active{background:#eef0f3}
.b.add{background:#1f2937;color:#fff;border-color:#1f2937}
.qty{display:inline-block;width:34px;text-align:center;font-weight:700;font-size:16px;vertical-align:middle}
.card.sel{box-shadow:0 0 0 2px #1f2937}
.bar{position:fixed;left:0;right:0;bottom:0;background:#1f2937;color:#fff;padding:11px 13px;z-index:60;
     display:table;width:100%}
.bar.hide{display:none}
.bar .l{display:table-cell;vertical-align:middle}
.bar .r{display:table-cell;vertical-align:middle;text-align:right;width:120px}
.bar b{font-size:17px}
.bar small{display:block;opacity:.72;font-size:12px}
.go{background:#22c55e;color:#04240f;border:0;border-radius:8px;padding:11px 15px;font-weight:700;font-size:15px}
.sheet{position:fixed;left:0;right:0;top:0;bottom:0;background:#fff;z-index:100;overflow-y:auto;display:none}
.sheet.on{display:block}
.sh{background:#1f2937;color:#fff;padding:12px 13px;position:sticky;top:0;display:table;width:100%}
.sh .l{display:table-cell;font-weight:700;font-size:17px;vertical-align:middle}
.sh .r{display:table-cell;text-align:right;width:70px;vertical-align:middle}
.x{background:transparent;border:0;color:#fff;font-size:26px;line-height:1;padding:0 4px}
.ln{padding:10px 13px;border-bottom:1px solid #eceef1;display:table;width:100%}
.ln .a{display:table-cell;vertical-align:middle}
.ln .b2{display:table-cell;vertical-align:middle;width:112px;text-align:right;white-space:nowrap}
.tot{padding:14px 13px;font-size:19px;font-weight:700;display:table;width:100%}
.tot .r{display:table-cell;text-align:right}
.acts{padding:0 13px 22px}
.big{display:block;width:100%;padding:15px;border:0;border-radius:10px;font-size:16px;font-weight:700;margin-bottom:9px}
.wa{background:#22c55e;color:#04240f}
.cp{background:#eef0f3;color:#1f2937}
.cl{background:#fff;color:#b91c1c;border:1px solid #f0c8c8}
.dest{text-align:center;color:#6b7280;font-size:12.5px;margin:-3px 0 11px}
.ok{background:#dcfce7;color:#065f2b;padding:12px 13px;border-radius:9px;font-weight:600;margin-bottom:11px;display:none;line-height:1.35}
.nuevo{background:#1f2937;color:#fff;display:none}
.pend{background:#fef3c7;color:#7c4a03;padding:9px 13px;font-size:13px;border-bottom:1px solid #fde68a;display:none;line-height:1.35}
.note{width:100%;padding:11px;border:1px solid #d5d9df;border-radius:8px;font-size:15px;
      font-family:inherit;margin-bottom:11px}
.empty{padding:44px 20px;text-align:center;color:#8b929c}
.tip{padding:10px 13px;color:#6b7280;font-size:12.5px;background:#fffbeb;border-bottom:1px solid #fde68a}
</style>
</head>
<body>

<header>
  <div class="hd">
    <div class="lg"><img src="__LOGO__" alt="General Distribution"></div>
    <div class="tx"><div class="brand">General Distribution</div><div class="sub">Pedidos</div></div>
  </div>
  <input class="tienda" id="tienda" placeholder="&iquest;Para cu&aacute;l tienda? (escribe el nombre)" autocomplete="off">
</header>

<div class="tools">
  <input id="q" placeholder="Buscar dulce, bebida, botana..." autocomplete="off">
  <div class="chips" id="chips"></div>
</div>

<div class="pend" id="pend"></div>
<div class="tip" id="tip">Toca <b>+</b> en lo que haga falta. El pedido se va guardando solo.</div>
<div class="count" id="count"></div>
<div class="grid" id="grid"></div>

<div class="bar hide" id="bar">
  <div class="l"><b id="barn">0 productos</b><small id="bart">$0.00</small></div>
  <div class="r"><button class="go" id="vp">Ver pedido</button></div>
</div>

<div class="sheet" id="sheet">
  <div class="sh"><div class="l">El pedido</div><div class="r"><button class="x" id="cx">&times;</button></div></div>
  <div id="lines"></div>
  <div class="tot"><span>Total</span><span class="r" id="stot">$0.00</span></div>
  <div class="acts">
    <div class="ok" id="aviso"></div>
    <textarea class="note" id="nota" rows="2" placeholder="Nota para el pedido (opcional)"></textarea>
    <button class="big wa" id="wa">Enviar el pedido por WhatsApp</button>
    <div class="dest">Se va al WhatsApp de General Distribution &middot; 801 898 6304</div>
    <button class="big cp" id="cp">Copiar el pedido</button>
    <button class="big nuevo" id="nuevo">Empezar otro pedido</button>
    <button class="big cl" id="cl">Vaciar el pedido</button>
  </div>
</div>

<script>
/* JS a la antigua a proposito: tiene que correr en telefonos viejos. */
/* A DONDE SE VAN LAS ORDENES. Para cambiarlo, cambia solo esta linea.
   Formato: clave de pais + numero, sin +, sin espacios y sin guiones.
   1 = Estados Unidos.  8018986304 = el numero de General Distribution. */
var WHATSAPP = '18018986304';

/* ---- La base de datos. Llave PUBLICA: solo permite ESCRIBIR pedidos, nunca leerlos. ---- */
var SB_URL = 'https://pwcpjaibjigqppyidtse.supabase.co/rest/v1';
var SB_KEY = 'sb_publishable_n4vrzEbspo0D0OYvDge7qg_DvQ5X7J_';

/* uuid v4 hecho a mano: crypto.randomUUID no existe en telefonos viejos */
function uuid(){
  var h = '0123456789abcdef', s = '', i;
  for(i=0;i<36;i++){
    if(i===8||i===13||i===18||i===23) s += '-';
    else if(i===14) s += '4';
    else if(i===19) s += h.charAt(Math.floor(Math.random()*4)+8);
    else s += h.charAt(Math.floor(Math.random()*16));
  }
  return s;
}

/* 409 = ya existia. Como el id lo generamos nosotros, reintentar es seguro:
   si el pedido ya se habia subido, la base lo rechaza por repetido y eso ES exito. */
function post(tabla, cuerpo, ok, falla){
  var x = new XMLHttpRequest();
  x.open('POST', SB_URL + '/' + tabla, true);
  x.setRequestHeader('apikey', SB_KEY);
  x.setRequestHeader('Authorization', 'Bearer ' + SB_KEY);
  x.setRequestHeader('Content-Type', 'application/json');
  x.setRequestHeader('Prefer', 'return=minimal');
  x.onreadystatechange = function(){
    if(x.readyState !== 4) return;
    if((x.status >= 200 && x.status < 300) || x.status === 409) ok(); else falla(x.status);
  };
  try { x.send(JSON.stringify(cuerpo)); } catch(e){ falla(0); }
}

function cola(){ try { return JSON.parse(localStorage.getItem('gd_cola') || '[]'); } catch(e){ return []; } }
function ponCola(c){ try { localStorage.setItem('gd_cola', JSON.stringify(c)); } catch(e){} }

function pintaPend(){
  var n = cola().length, el = document.getElementById('pend');
  if(n > 0){
    el.innerHTML = '<b>' + n + (n===1 ? ' pedido sin subir' : ' pedidos sin subir') + '.</b> ' +
      (n===1 ? 'Est&aacute; guardado en el tel&eacute;fono y se sube solo en cuanto haya se&ntilde;al.'
             : 'Est&aacute;n guardados en el tel&eacute;fono y se suben solos en cuanto haya se&ntilde;al.');
    el.style.display = 'block';
  } else { el.style.display = 'none'; }
}

function subirUno(ped, hecho){
  post('gd_pedidos',
    {id:ped.id, tienda:ped.tienda, nota:ped.nota, articulos:ped.articulos, total:ped.total, es_prueba:false},
    function(){
      if(!ped.lineas || !ped.lineas.length){ hecho(true); return; }
      post('gd_pedido_lineas', ped.lineas, function(){ hecho(true); }, function(){ hecho(false); });
    },
    function(){ hecho(false); });
}

/* Sube de uno en uno. Si uno falla, se detiene y lo deja para despues. */
function vaciarCola(){
  var c = cola();
  if(!c.length){ pintaPend(); return; }
  subirUno(c[0], function(ok){
    if(ok){ var d = cola(); d.shift(); ponCola(d); pintaPend(); vaciarCola(); }
    else { pintaPend(); }
  });
}

function guardarPedido(){
  var pid = uuid(), lineas = [], tot = 0, n = 0, i;
  for(i=0;i<P.length;i++){
    var pr = P[i], c = cart[pr.i] || 0;
    if(c <= 0) continue;
    n += c; tot += pr.p * c;
    lineas.push({id:uuid(), pedido_id:pid, producto_id:'' + pr.i, producto:pr.t,
                 categoria:pr.c, precio:pr.p, cantidad:c,
                 importe:Math.round(pr.p * c * 100) / 100});
  }
  var nt = document.getElementById('nota').value;
  var ped = {id:pid, tienda:document.getElementById('tienda').value,
             nota:(nt ? nt : null), articulos:n, total:Math.round(tot*100)/100, lineas:lineas};
  var q = cola(); q.push(ped); ponCola(q);
  pintaPend(); vaciarCola();
}

/* Los avisos van DENTRO de la app: alert() y confirm() pueden estar bloqueados. */
function aviso(html){
  var el = document.getElementById('aviso');
  el.innerHTML = html; el.style.display = 'block';
}

var P = __DATA__;
var CATS = __CATS__;
var cart = {}, cat = '', q = '', shown = [];

function money(n){ return '$' + (Math.round(n*100)/100).toFixed(2); }
function save(){
  try{
    localStorage.setItem('gd_cart', JSON.stringify(cart));
    localStorage.setItem('gd_tienda', document.getElementById('tienda').value);
    localStorage.setItem('gd_nota', document.getElementById('nota').value);
  }catch(e){}
}
function load(){
  try{
    var c = localStorage.getItem('gd_cart'); if(c) cart = JSON.parse(c) || {};
    var t = localStorage.getItem('gd_tienda'); if(t) document.getElementById('tienda').value = t;
    var n = localStorage.getItem('gd_nota'); if(n) document.getElementById('nota').value = n;
  }catch(e){ cart = {}; }
}
function byId(id){ for(var i=0;i<P.length;i++){ if(P[i].i == id) return P[i]; } return null; }

function totals(){
  var n=0, t=0;
  for(var k in cart){ if(cart.hasOwnProperty(k) && cart[k]>0){
    var p = byId(k); n += cart[k]; if(p) t += p.p * cart[k];
  }}
  return {n:n, t:t};
}
function paintBar(){
  var x = totals(), bar = document.getElementById('bar');
  if(x.n > 0){
    bar.className = 'bar';
    document.getElementById('barn').innerHTML = x.n + (x.n==1 ? ' producto' : ' productos');
    document.getElementById('bart').innerHTML = money(x.t);
  } else { bar.className = 'bar hide'; }
  document.getElementById('stot').innerHTML = money(x.t);
}
function chips(){
  var h = '<button class="chip' + (cat===''?' on':'') + '" data-c="">Todo</button>';
  for(var i=0;i<CATS.length;i++){
    h += '<button class="chip' + (cat===CATS[i]?' on':'') + '" data-c="' + CATS[i] + '">' + CATS[i] + '</button>';
  }
  document.getElementById('chips').innerHTML = h;
}
function norm(s){
  s = (s||'').toLowerCase();
  s = s.replace(/[\\u00e1\\u00e0\\u00e4\\u00e2]/g,'a').replace(/[\\u00e9\\u00e8\\u00eb\\u00ea]/g,'e')
       .replace(/[\\u00ed\\u00ec\\u00ef\\u00ee]/g,'i').replace(/[\\u00f3\\u00f2\\u00f6\\u00f4]/g,'o')
       .replace(/[\\u00fa\\u00f9\\u00fc\\u00fb]/g,'u').replace(/\\u00f1/g,'n');
  return s;
}
function render(){
  var nq = norm(q), out = [], i, p;
  for(i=0;i<P.length;i++){
    p = P[i];
    if(cat && p.c !== cat) continue;
    if(nq && norm(p.t).indexOf(nq) < 0) continue;
    out.push(p);
  }
  shown = out;
  document.getElementById('count').innerHTML = out.length + (out.length===1 ? ' producto' : ' productos') + (cat ? ' en ' + cat : '');
  var lim = Math.min(out.length, 200), h = '';
  for(i=0;i<lim;i++){
    p = out[i];
    var n = cart[p.i] || 0;
    h += '<div class="card' + (n>0?' sel':'') + '" id="c' + p.i + '">';
    h += '<div class="cell ph">' + (p.f ? '<img src="' + p.f + '" loading="lazy" alt="">' : '<span class="noimg"></span>') + '</div>';
    h += '<div class="cell info"><div class="name">' + p.t + '</div>';
    h += '<div class="meta">' + p.c + (p.d ? '' : ' &middot; <span class="agot">AGOTADO</span>') + '</div>';
    h += p.p > 0 ? '<div class="price">' + money(p.p) + '</div>' : '<div class="nop">Precio por confirmar</div>';
    h += '</div>';
    h += '<div class="cell stp">';
    if(n > 0){
      h += '<button class="b" data-m="' + p.i + '">&minus;</button>';
      h += '<span class="qty" id="q' + p.i + '">' + n + '</span>';
    }
    h += '<button class="b add" data-a="' + p.i + '">+</button>';
    h += '</div></div>';
  }
  if(!out.length) h = '<div class="empty">No encontr&eacute; nada con eso.<br>Prueba con menos letras.</div>';
  else if(out.length > lim) h += '<div class="empty">Hay ' + (out.length-lim) + ' m&aacute;s. Usa el buscador para acotar.</div>';
  document.getElementById('grid').innerHTML = h;
}
/* Repinta SOLO el renglon tocado. Redibujar los 551 se come los toques en telefonos viejos. */
function paintCard(id){
  var el = document.getElementById('c' + id);
  if(!el) return;
  var n = cart[id] || 0, h = '';
  el.className = 'card' + (n>0 ? ' sel' : '');
  var stp = el.getElementsByTagName('div');
  var box = null, j;
  for(j=0;j<stp.length;j++){ if(stp[j].className.indexOf('stp')>=0){ box = stp[j]; break; } }
  if(!box) return;
  if(n > 0){
    h += '<button class="b" data-m="' + id + '">&minus;</button>';
    h += '<span class="qty">' + n + '</span>';
  }
  h += '<button class="b add" data-a="' + id + '">+</button>';
  box.innerHTML = h;
}
function bump(id, d){
  var n = (cart[id] || 0) + d;
  if(n <= 0) delete cart[id]; else cart[id] = n;
  save(); paintBar(); paintCard(id);
}
function lines(){
  var h = '', any = false;
  for(var i=0;i<P.length;i++){
    var p = P[i], n = cart[p.i] || 0;
    if(n <= 0) continue;
    any = true;
    h += '<div class="ln"><div class="a"><div class="name">' + p.t + '</div>';
    h += '<div class="meta">' + (p.p>0 ? money(p.p) + ' c/u &middot; ' + money(p.p*n) : 'precio por confirmar') + '</div></div>';
    h += '<div class="b2"><button class="b" data-m="' + p.i + '">&minus;</button>';
    h += '<span class="qty">' + n + '</span>';
    h += '<button class="b add" data-a="' + p.i + '">+</button></div></div>';
  }
  if(!any) h = '<div class="empty">Todav&iacute;a no has puesto nada.</div>';
  document.getElementById('lines').innerHTML = h;
}
function texto(){
  var t = document.getElementById('tienda').value || '(sin nombre de tienda)';
  var d = new Date();
  var s = 'PEDIDO - General Distribution\\n';
  s += 'Tienda: ' + t + '\\n';
  s += 'Fecha: ' + d.getDate() + '/' + (d.getMonth()+1) + '/' + d.getFullYear() + '\\n\\n';
  var tot = 0;
  for(var i=0;i<P.length;i++){
    var p = P[i], n = cart[p.i] || 0;
    if(n <= 0) continue;
    s += n + ' x ' + p.t;
    if(p.p > 0){ s += '  (' + money(p.p*n) + ')'; tot += p.p*n; }
    else { s += '  (precio por confirmar)'; }
    s += '\\n';
  }
  s += '\\nTOTAL: ' + money(tot);
  var nt = document.getElementById('nota').value;
  if(nt) s += '\\n\\nNota: ' + nt;
  return s;
}
/* ---- eventos, con delegacion para que funcione en navegadores viejos ---- */
document.addEventListener('click', function(e){
  var el = e.target;
  while(el && el !== document.body){
    if(el.getAttribute){
      var a = el.getAttribute('data-a'), m = el.getAttribute('data-m'), c = el.getAttribute('data-c');
      if(a){ bump(a, 1); if(document.getElementById('sheet').className.indexOf('on')>=0) lines(); return; }
      if(m){ bump(m, -1); if(document.getElementById('sheet').className.indexOf('on')>=0) lines(); return; }
      if(c !== null && c !== undefined && el.className.indexOf('chip')>=0){ cat = c; chips(); render(); window.scrollTo(0,0); return; }
    }
    el = el.parentNode;
  }
}, false);

/* onkeyup solo NO basta: se cae con pegado, autocompletado y dictado por voz. */
var qEl = document.getElementById('q');
function onQ(){ if(q !== qEl.value){ q = qEl.value; render(); } }
qEl.onkeyup = onQ; qEl.oninput = onQ; qEl.onchange = onQ;
var tEl = document.getElementById('tienda');
tEl.onkeyup = save; tEl.oninput = save; tEl.onchange = save;
var nEl = document.getElementById('nota');
nEl.onkeyup = save; nEl.oninput = save; nEl.onchange = save;
document.getElementById('vp').onclick = function(){ lines(); document.getElementById('sheet').className = 'sheet on'; };
document.getElementById('cx').onclick = function(){ document.getElementById('sheet').className = 'sheet'; };
document.getElementById('wa').onclick = function(){
  var x = totals();
  if(x.n === 0){ aviso('El pedido est\\u00e1 vac\\u00edo. Toca <b>+</b> en lo que haga falta.'); return; }
  var t = document.getElementById('tienda').value;
  if(!t){
    aviso('Falta poner <b>para cu\\u00e1l tienda</b> es el pedido. Est\\u00e1 hasta arriba de la pantalla.');
    document.getElementById('sheet').className = 'sheet';
    document.getElementById('tienda').focus();
    return;
  }
  guardarPedido();
  aviso('&#10003; <b>Pedido guardado.</b> Ahora se abre WhatsApp: ah\\u00ed dale <b>enviar</b>.');
  document.getElementById('nuevo').style.display = 'block';
  window.open('https://wa.me/' + WHATSAPP + '?text=' + encodeURIComponent(texto()), '_blank');
};
document.getElementById('nuevo').onclick = function(){
  cart = {}; save(); paintBar(); render();
  document.getElementById('nota').value = ''; save();
  document.getElementById('aviso').style.display = 'none';
  document.getElementById('nuevo').style.display = 'none';
  document.getElementById('sheet').className = 'sheet';
  window.scrollTo(0, 0);
};
document.getElementById('cp').onclick = function(){
  var s = texto(), ta = document.createElement('textarea');
  ta.value = s; document.body.appendChild(ta); ta.select();
  try{ document.execCommand('copy'); alert('Pedido copiado. P\\u00e9galo donde quieras.'); }
  catch(err){ alert('Copia a mano:\\n\\n' + s); }
  document.body.removeChild(ta);
};
document.getElementById('cl').onclick = function(){
  if(confirm('\\u00bfVaciar el pedido? No se puede deshacer.')){
    cart = {}; save(); paintBar(); lines(); render();
    document.getElementById('sheet').className = 'sheet';
  }
};
load(); chips(); render(); paintBar(); pintaPend(); vaciarCola();
</script>
</body>
</html>
"""

HTML = HTML.replace("__DATA__", data_js).replace("__CATS__", cats_js).replace("__LOGO__", LOGO)

out = os.path.join(OUTDIR, "index.html")
io.open(out, "w", encoding="utf-8").write(HTML)
print("escrito:", out)
print("tamano: %.0f KB" % (os.path.getsize(out) / 1024.0))
print("productos:", len(prods))
print("categorias:", cat_list)
print("sin foto:", sum(1 for p in prods if not p["f"]))
print("precio 0:", sum(1 for p in prods if p["p"] == 0))
