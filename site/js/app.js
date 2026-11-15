// =====================================================================
//  A Cidade dos Seguidores — site da vila
// =====================================================================
(() => {
'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const MAX_BONECOS = 60;          // máximo de moradores desenhados por quadro
const PX = 263;                  // x da rua principal
const VEL_ANDAR = 300;           // px por minuto da vila (5 px/s ao vivo)
const NOITE = [0.5, 0.56, 0.8];  // tinta dos bonecos à noite
const PC = () => innerWidth >= 900;

let VILA, MORADORES, RY = {};
const IMG = {};
let PUB = {};                    // id -> {nome, usuario, aparencia, ocupado}
let EU = null;                   // perfil logado
let MEUS = { segue: new Set(), seguidores: new Set() };
let seguindo = null, selecionado = null;
let preview = null;              // {id, look} visual em edição (ainda não salvo)
let escolhendo = false;          // modo "toque num morador no mapa"
let estados = [], desenhados = [];
let AO_VIVO = null;
let CASAS = [];                 // casas prontas + casas em obra que já têm moradores
let TEM_BIO = false;            // banco já tem bio + recusar pedido (5_bio_e_pedidos.sql)              // seguidores agora (tabela "contador" no Supabase)

// ---------------------------------------------------------------------
// tempo (hora de Brasília, UTC-3 sem horário de verão)
// ---------------------------------------------------------------------
const relogio = { real: Date.now(), sim: Date.now(), vel: 1 };
const simMs = () => relogio.sim + (Date.now() - relogio.real) * relogio.vel;
function setVel(v) { relogio.sim = simMs(); relogio.real = Date.now(); relogio.vel = v; if (v === 1) relogio.sim = Date.now(); }
function pular(min) { relogio.sim = simMs() + min * 60000; relogio.real = Date.now(); if (relogio.vel === 1) relogio.vel = 1.0000001; }
function br(ms) {
  const t = ms - 3 * 3600e3, dia = Math.floor(t / 864e5);
  return { dia, sem: (dia + 4) % 7, min: (t - dia * 864e5) / 60000 };
}
const toMin = s => { const [h, m] = s.split(':').map(Number); return h * 60 + m; };
const fmt = m => { m = ((Math.round(m) % 1440) + 1440) % 1440; return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); };
function noiteFator(min) {
  if (min >= 1120 || min < 360) return 1;
  if (min >= 1100) return (min - 1100) / 20;
  if (min < 380) return 1 - (min - 360) / 20;
  return 0;
}

// ---------------------------------------------------------------------
// aleatório com semente
// ---------------------------------------------------------------------
function rng(seed) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
const hashId = id => (Math.imul(id, 2654435761) >>> 0);

// ---------------------------------------------------------------------
// agenda do dia (com variação diária e missa de domingo)
// ---------------------------------------------------------------------
const LUGAR = {
  casa:        { ico: '🏠', em: 'em casa',          ir: 'indo pra casa' },
  mercadinho:  { ico: '🛒', em: 'no mercadinho',    ir: 'indo pro mercadinho' },
  vendinha:    { ico: '🏪', em: 'na vendinha',      ir: 'indo pra vendinha' },
  praca:       { ico: '⛲', em: 'na praça',         ir: 'indo pra praça' },
  passeio_rua: { ico: '🚶', em: 'passeando na rua', ir: 'saindo pra passear' },
  igreja:      { ico: '⛪', em: 'na igreja',        ir: 'indo pra igreja' },
};
const cacheBlocos = new Map();
function blocosDoDia(m, dia, sem) {
  const k = m.id * 100000 + dia;
  let bl = cacheBlocos.get(k);
  if (bl) return bl;
  if (cacheBlocos.size > 8000) cacheBlocos.clear();
  const off = ((m.id * 37 + dia * 53) % 11 + 11) % 11 - 5;
  bl = m.agenda.map(b => ({ de: b.de === '00:00' ? 0 : toMin(b.de) + off, ate: b.ate === '23:59' ? 1440 : toMin(b.ate) + off, onde: b.onde, faz: b.faz }));
  if (sem === 0 && m.domingo) {
    const D = toMin(m.domingo.de) + off, A = D + m.domingo.duracao_min, out = [];
    for (const b of bl) {
      if (b.ate <= D - 20 || b.de >= A + 20) { out.push(b); continue; }
      if (b.de < D - 20) out.push({ ...b, ate: D - 20 });
      if (b.ate > A + 20) out.push({ ...b, de: A + 20 });
    }
    out.push({ de: D, ate: A, onde: 'igreja', faz: 'na missa' });
    bl = out.filter(b => b.ate - b.de >= 5 || b.de === 0).sort((a, b) => a.de - b.de);
  }
  cacheBlocos.set(k, bl);
  return bl;
}

// ---------------------------------------------------------------------
// lugares e caminhos (sempre pelas ruas)
// ---------------------------------------------------------------------
function nosCasa(c) {
  const [px, py] = c.porta, [rx, ry] = c.ponto_na_rua;
  if (py <= ry) return [c.porta, c.ponto_na_rua];
  const lx = c.lote[0] - 3;              // casa abaixo da rua: contorna pela lateral
  return [c.porta, [px, py + 5], [lx, py + 5], [lx, ry], c.ponto_na_rua];
}
function lugar(m, b, k) {
  const c = CASAS[m.casa - 1], P = VILA.pontos;
  switch (b.onde) {
    case 'mercadinho': case 'vendinha':
      return { nos: [P[b.onde].porta, P[b.onde].rua], rua: 'B', dentro: true, porta: P[b.onde].porta };
    case 'igreja':
      return { nos: [P.igreja.porta, [PX, P.igreja.porta[1] + 6]], rua: 'P', dentro: true, porta: P.igreja.porta };
    case 'praca': {
      const r = rng(m.id * 31 + 7), [[x0, y0], [x1, y1]] = P.praca.area;
      const s = [Math.round(x0 + 10 + r() * (x1 - x0 - 20)), Math.round(y0 + 16 + r() * (y1 - y0 - 22))];
      return { nos: [s, [PX, RY.B]], rua: 'B', dentro: false, base: s, A: 2 + Math.floor(r() * 5), v: 2.5, pausa: 4 + r() * 10, seed: m.id };
    }
    case 'passeio_rua': {
      const r = rng(m.id * 131 + k * 17), A = 20 + Math.floor(r() * 61), rua = VILA.ruas[c.rua];
      const x = clamp(c.ponto_na_rua[0] + (r() - 0.5) * 140, rua.de[0] + A + 4, rua.ate[0] - A - 4);
      const s = [Math.round(x), RY[c.rua] + Math.round((r() - 0.5) * 6)];
      return { nos: [s], rua: c.rua, dentro: false, base: s, A, v: 5 * m.velocidade, pausa: 1 + r() * 4, seed: m.id + k };
    }
    default:
      return { nos: nosCasa(c), rua: c.rua, dentro: true, porta: c.porta };
  }
}
function caminho(m, bl, i) {
  const b = bl[i];
  if (b._cam) return b._cam;
  const a = lugar(m, b, i), z = lugar(m, bl[i + 1], i + 1);
  const pa = a.nos, pb = z.nos.slice().reverse();
  const pts = (a.rua === z.rua && a.rua !== 'P') ? [...pa, ...pb]
    : [...pa, [PX, pa[pa.length - 1][1]], [PX, pb[0][1]], ...pb];
  const acc = [0];
  for (let j = 1; j < pts.length; j++) acc.push(acc[j - 1] + Math.hypot(pts[j][0] - pts[j - 1][0], pts[j][1] - pts[j - 1][1]));
  return (b._cam = { pts, acc, len: acc[acc.length - 1] });
}
function noCaminho(cam, f) {
  const d = clamp(f, 0, 1) * cam.len;
  let j = 1;
  while (j < cam.pts.length - 1 && cam.acc[j] < d) j++;
  const p0 = cam.pts[j - 1], p1 = cam.pts[j], seg = cam.acc[j] - cam.acc[j - 1] || 1;
  const t = clamp((d - cam.acc[j - 1]) / seg, 0, 1), dx = p1[0] - p0[0], dy = p1[1] - p0[1];
  return { x: p0[0] + dx * t, y: p0[1] + dy * t, dir: Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up') };
}
// vai e volta devagar (praça / passeio)
function vaivem(L, seg) {
  const T = (2 * L.A) / L.v, ciclo = 2 * T + 2 * L.pausa;
  const ph = ((seg + L.seed * 13.7) % ciclo + ciclo) % ciclo;
  if (ph < T) return { dx: -L.A + L.v * ph, dir: 'right', anda: true };
  if (ph < T + L.pausa) return { dx: L.A, dir: 'down', anda: false };
  if (ph < 2 * T + L.pausa) return { dx: L.A - L.v * (ph - T - L.pausa), dir: 'left', anda: true };
  return { dx: -L.A, dir: 'down', anda: false };
}
function noLugar(m, bl, i, seg) {
  const b = bl[i], L = lugar(m, b, i);
  const base = { id: m.id, onde: b.onde, faz: b.faz, bloco: i, ate: b.ate };
  if (L.dentro) return { ...base, vis: false, x: L.porta[0], y: L.porta[1] };
  const v = vaivem(L, seg);
  return { ...base, vis: true, x: L.base[0] + v.dx, y: L.base[1], dir: v.dir, anda: v.anda };
}
// posição = função da hora. Todo mundo vê o mesmo morador no mesmo lugar.
function estado(m, ms) {
  const { dia, sem, min } = br(ms), seg = min * 60;
  const bl = blocosDoDia(m, dia, sem);
  let i = bl.length - 1;
  for (let k = 0; k < bl.length; k++) { if (min < bl[k].de) { i = k - 1; break; } }
  if (i < 0) i = 0;
  if (min < bl[i].ate || i === bl.length - 1) return noLugar(m, bl, i, seg);
  const prox = bl[i + 1], cam = caminho(m, bl, i);
  const viagem = cam.len / (VEL_ANDAR * m.velocidade);
  const sai = Math.max(bl[i].ate, prox.de - viagem);
  if (min < sai) return noLugar(m, bl, i, seg);
  const p = noCaminho(cam, (min - sai) / (prox.de - sai));
  return { id: m.id, vis: true, x: p.x, y: p.y, dir: p.dir, anda: true, onde: 'andando', faz: LUGAR[prox.onde].ir, bloco: i, ate: prox.de, destino: prox.onde };
}

// encontros: dois moradores no mesmo lugar ao mesmo tempo (>= 10 min)
function encontrosNoDia(a, b, dia, sem) {
  const A = blocosDoDia(a, dia, sem), B = blocosDoDia(b, dia, sem);
  const ca = CASAS[a.casa - 1].rua, cb = CASAS[b.casa - 1].rua, out = [];
  for (const x of A) for (const y of B) {
    if (x.onde !== y.onde || x.onde === 'casa') continue;
    if (x.onde === 'passeio_rua' && ca !== cb) continue;
    const de = Math.max(x.de, y.de), ate = Math.min(x.ate, y.ate);
    if (ate - de >= 10) out.push({ onde: x.onde, de, ate });
  }
  return out;
}
function nivelAmizade(a, b) {
  const { dia } = br(simMs());
  let dias = 0;
  for (let d = dia - 6; d <= dia; d++) if (encontrosNoDia(a, b, d, (d + 4) % 7).length) dias++;
  return dias;
}

// ---------------------------------------------------------------------
// sprites (atlas do vídeo ou visual personalizado)
// ---------------------------------------------------------------------
const DIRI = { down: 0, left: 1, right: 2, up: 3 };
const cacheFolhas = new Map();
function tingir(src, w, h) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const x = c.getContext('2d'); x.drawImage(src, 0, 0);
  const d = x.getImageData(0, 0, w, h);
  for (let i = 0; i < d.data.length; i += 4) { d.data[i] *= NOITE[0]; d.data[i + 1] *= NOITE[1]; d.data[i + 2] *= NOITE[2]; }
  x.putImageData(d, 0, 0); return c;
}
function folhaDe(look) {
  const k = JSON.stringify(Sprites.normalizar(look));
  let f = cacheFolhas.get(k);
  if (f) return f;
  const c = document.createElement('canvas'); c.width = 48; c.height = 72;
  c.getContext('2d').putImageData(new ImageData(Sprites.folha(Sprites.normalizar(look)), 48, 72), 0, 0);
  f = { dia: c, noite: tingir(c, 48, 72) };
  cacheFolhas.set(k, f); return f;
}
function lookDe(id) {
  if (preview && preview.id === id) return preview.look;
  return (PUB[id] && PUB[id].aparencia) || MORADORES[id - 1].aparencia;
}
function fonteSprite(id, noite) {
  const custom = (preview && preview.id === id) ? preview.look : (PUB[id] && PUB[id].aparencia);
  if (custom) return { img: noite ? folhaDe(custom).noite : folhaDe(custom).dia, ox: 0, oy: 0 };
  const a = MORADORES[id - 1].atlas;
  return { img: noite ? IMG.atlasNoite : IMG.atlas, ox: a.col * 48, oy: a.lin * 72 };
}
function pintar(canvas, look, dir = 'down', frame = 0) {
  const x = canvas.getContext('2d');
  x.clearRect(0, 0, canvas.width, canvas.height);
  const tmp = document.createElement('canvas'); tmp.width = 12; tmp.height = 18;
  tmp.getContext('2d').putImageData(new ImageData(Sprites.desenhar(Sprites.normalizar(look), dir, frame), 12, 18), 0, 0);
  x.imageSmoothingEnabled = false;
  x.drawImage(tmp, Math.floor((canvas.width - 12) / 2), canvas.height >= 18 ? Math.floor((canvas.height - 18) / 2) : 0);
}
const nomeDe = id => (PUB[id] && PUB[id].nome) || null;
const rotulo = id => nomeDe(id) || `Morador #${id}`;
const ocupado = id => !!(PUB[id] && PUB[id].ocupado);
const amigoMeu = id => MEUS.segue.has(id);

// ---------------------------------------------------------------------
// câmera, desenho
// ---------------------------------------------------------------------
const cv = $('#mapa'), ctx = cv.getContext('2d');
let W = 0, H = 0, DPR = 1;
const cam = { x: 264, y: 490, s: 2 };
// tamanho do mapa vem do vila.json (o mapa pode crescer nos próximos episódios)
const MW = () => ISO() ? VILA.iso.largura : (VILA && VILA.mapa && VILA.mapa.largura) || 540;
const MH = () => ISO() ? VILA.iso.altura : (VILA && VILA.mapa && VILA.mapa.altura) || 960;
// limites do MUNDO (mapa de cima), usados pelo boneco controlado
const MUNDO_W = () => (VILA && VILA.mapa && VILA.mapa.largura) || 540, MUNDO_H = () => (VILA && VILA.mapa && VILA.mapa.altura) || 960;
function minS() { return Math.min(W / MW(), H / MH()) * 0.92; }
function ajustarTela() {
  DPR = Math.min(devicePixelRatio || 1, 2); W = innerWidth; H = innerHeight;
  cv.width = Math.round(W * DPR); cv.height = Math.round(H * DPR);
  cam.s = clamp(cam.s, minS(), 6); limitarCam();
}
function limitarCam() {
  // não deixa sobrar muito fundo fora do mapa (margem de ~120 px de tela)
  const m = 120 / cam.s, hx = W / 2 / cam.s, hy = H / 2 / cam.s;
  cam.x = MW() + 2 * m > 2 * hx ? clamp(cam.x, hx - m, MW() - hx + m) : MW() / 2;
  cam.y = MH() + 2 * m > 2 * hy ? clamp(cam.y, hy - m, MH() - hy + m) : MH() / 2;
}
function focoTela() {
  const hud = $('#hud').getBoundingClientRect(), p = $('#painel');
  let top = hud.bottom - 10, bot = H - ($('#menu').getBoundingClientRect().height && !PC() ? $('#menu').getBoundingClientRect().height : 0), right = W;
  if (!p.hidden) { const r = p.getBoundingClientRect(); if (PC()) right = r.left; else bot = r.top; }
  return { x: right / 2, y: (top + bot) / 2 };
}
const telaPraMapa = (sx, sy) => ({ x: cam.x + (sx - W / 2) / cam.s, y: cam.y + (sy - H / 2) / cam.s });
const mapaPraTela = (mx, my) => ({ x: (mx - cam.x) * cam.s + W / 2, y: (my - cam.y) * cam.s + H / 2 });
function zoomEm(sx, sy, novo) {
  const m = telaPraMapa(sx, sy);
  cam.s = clamp(novo, minS(), 6);
  cam.x = m.x - (sx - W / 2) / cam.s; cam.y = m.y - (sy - H / 2) / cam.s; limitarCam();
}

// ---------------------------------------------------------------------
// VISÃO: isométrica (ep. 6+) ou de cima. A rotina, os caminhos e o controle
// usam sempre as coordenadas "do mundo" (as do mapa de cima, em px do vila.json);
// proj() converte pra imagem de fundo da visão atual.
// ---------------------------------------------------------------------
let VISTA = (() => { try { return localStorage.getItem('vila_vista') || 'iso'; } catch { return 'iso'; } })();
const ISO = () => VISTA === 'iso' && !!(VILA && VILA.iso && IMG.iso);
const ESC = () => (VILA && VILA.mapa && VILA.mapa.escala_logica) || 2;
function proj(x, y) {
  if (!ISO()) return { x, y };
  const o = VILA.iso.origem, lx = x / ESC(), ly = y / ESC();
  return { x: o[0] + (lx - ly) * 2, y: o[1] + (lx + ly) };
}
function desproj(X, Y) {
  if (!ISO()) return { x: X, y: Y };
  const o = VILA.iso.origem, a = (X - o[0]) / 2, b = Y - o[1];        // a = lx - ly, b = lx + ly
  return { x: (a + b) / 2 * ESC(), y: (b - a) / 2 * ESC() };
}
const mundoPraTela = (x, y) => { const p = proj(x, y); return mapaPraTela(p.x, p.y); };
function trocarVista(nova) {
  if (nova === VISTA) return;
  const centro = desproj(cam.x, cam.y);                               // mantém o mesmo lugar no centro
  VISTA = nova; try { localStorage.setItem('vila_vista', nova); } catch {}
  const p = proj(centro.x, centro.y); cam.x = p.x; cam.y = p.y;
  cam.s = clamp(cam.s, minS(), 6); limitarCam(); atualizarBotaoVista();
}
function atualizarBotaoVista() {
  const b = $('#btnVista'); if (!b) return;
  b.hidden = !(VILA && VILA.iso && IMG.iso);
  b.textContent = ISO() ? '🗺️' : '🧊';
  b.title = b.ariaLabel = ISO() ? 'Ver de cima' : 'Ver em isométrico';
}
$('#btnVista').onclick = () => trocarVista(ISO() ? 'cima' : 'iso');

let ultimoNoite = 0, encontrosAvisados = new Set();
function desenhar(agoraReal) {
  const ms = simMs(), t = br(ms), nf = noiteFator(t.min), noite = nf > 0.5, iso = ISO();
  estados = MORADORES.map(m => estado(m, ms));
  if (ctrl.ativo && EU) estados[EU.morador - 1] = INTERIOR ? { ...estados[EU.morador - 1], vis: false, onde: 'casa', faz: INTERIOR.tipo === 'casa' ? 'dentro de casa' : 'no mercadinho' }
    : { ...estados[EU.morador - 1], vis: true, x: ctrl.x, y: ctrl.y, dir: ctrl.dir, anda: ctrl.anda && !ctrl.sentado, onde: 'controle', faz: ctrl.sentado ? 'sentado na praça' : 'controlado por você' };
  aplicarRemotos();
  if (INTERIOR) { desenharInterior(agoraReal, t, nf); if (!$('#hudHora').textContent.startsWith(fmt(t.min))) atualizarRelogio(t, nf); return; }
  for (const e of estados) { const p = proj(e.x, e.y); e.px = p.x; e.py = p.y; }
  // câmera segue
  if (seguindo) {
    const e = estados[seguindo - 1], f = focoTela();
    const alvoX = e.px - (f.x - W / 2) / cam.s, alvoY = e.py - (f.y - H / 2) / cam.s;
    cam.x += (alvoX - cam.x) * 0.12; cam.y += (alvoY - cam.y) * 0.12; limitarCam();
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = nf > 0.5 ? '#1d2b2a' : '#3f7a34'; ctx.fillRect(0, 0, cv.width, cv.height);
  const k = DPR * cam.s, tx = Math.round(DPR * (W / 2 - cam.x * cam.s)), ty = Math.round(DPR * (H / 2 - cam.y * cam.s));
  ctx.setTransform(k, 0, 0, k, tx, ty);
  ctx.imageSmoothingEnabled = false;
  if (iso) {
    ctx.drawImage(IMG.iso, 0, 0);
    if (nf > 0) {                                                        // noite: tinta azulada por cima
      ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = nf;
      ctx.fillStyle = 'rgb(97,115,184)'; ctx.fillRect(0, 0, IMG.iso.width, IMG.iso.height);
      ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
    }
  } else {
    if (nf < 1) ctx.drawImage(IMG.dia, 0, 0);
    if (nf > 0) { ctx.globalAlpha = nf; ctx.drawImage(IMG.noite, 0, 0); ctx.globalAlpha = 1; }
  }

  // quem aparece: seguido, eu, amigos, registrados, depois sorteio fixo — máx. MAX_BONECOS
  const v0 = telaPraMapa(0, 0), v1 = telaPraMapa(W, H);
  const prio = id => id === seguindo || id === selecionado ? 0 : (EU && id === EU.morador) ? 1 : (amigoMeu(id) || estaOnline(id)) ? 2 : ocupado(id) ? 3 : 4;
  desenhados = estados.filter(e => e.vis && e.px > v0.x - 16 && e.px < v1.x + 16 && e.py > v0.y - 24 && e.py < v1.y + 24)
    .sort((a, b) => prio(a.id) - prio(b.id) || hashId(a.id) - hashId(b.id)).slice(0, MAX_BONECOS)
    .sort((a, b) => a.py - b.py);                                        // mais ao fundo primeiro (vale nas duas visões)

  const quadro = Math.floor(agoraReal / 125) % 4, topo = iso ? 17 : 14;
  for (const e of desenhados) {
    const x = Math.round(e.px), y = Math.round(e.py);
    if (iso) { ctx.fillStyle = 'rgba(0,30,0,.3)'; ctx.beginPath(); ctx.ellipse(x, y, 4, 1.6, 0, 0, Math.PI * 2); ctx.fill(); }
    if (e.id === selecionado || e.id === seguindo) {
      ctx.strokeStyle = '#f6c836'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.ellipse(x, y + (iso ? 0 : 3), 7, iso ? 3.5 : 3, 0, 0, Math.PI * 2); ctx.stroke();
    }
    const f = fonteSprite(e.id, noite), fr = e.anda ? (quadro + e.id) % 4 : 0;
    ctx.drawImage(f.img, f.ox + fr * 12, f.oy + DIRI[e.dir || 'down'] * 18, 12, 18, x - 6, y - topo, 12, 18);
  }

  // textos em escala de tela
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  const alvo = selecionado || seguindo, acima = (e, d) => mapaPraTela(e.px, e.py - d);
  if (cam.s >= 2) {
    ctx.font = '700 11px Nunito, system-ui, sans-serif';
    for (const e of desenhados) {
      if (e.id === alvo || !ocupado(e.id) || !nomeDe(e.id)) continue;
      const p = acima(e, topo + 2), n = nomeDe(e.id), w = ctx.measureText(n).width + 10;
      const meu = EU && e.id === EU.morador, am = amigoMeu(e.id);
      ctx.fillStyle = meu ? 'rgba(246,200,54,.95)' : am ? 'rgba(255,214,222,.95)' : 'rgba(30,24,36,.72)';
      pilula(p.x - w / 2, p.y - 8, w, 15, 7); ctx.fill();
      ctx.fillStyle = meu || am ? '#1e1824' : '#fff8e7'; ctx.fillText(n, p.x, p.y);
      if (estaOnline(e.id)) { ctx.fillStyle = '#2ecc71'; ctx.beginPath(); ctx.arc(p.x - w / 2 + 1, p.y - 6, 3.5, 0, Math.PI * 2); ctx.fill(); ctx.strokeStyle = '#1e1824'; ctx.lineWidth = 1; ctx.stroke(); }
    }
  }
  // corações: meu morador perto de um amigo (distância medida no mundo)
  if (EU && MEUS.segue.size) {
    const eu = estados[EU.morador - 1];
    if (eu.vis) for (const id of MEUS.segue) {
      const o = estados[id - 1];
      if (!o || !o.vis || Math.hypot(o.x - eu.x, o.y - eu.y) > 28) continue;
      const pulso = 1 + Math.sin(agoraReal / 180) * 0.12;
      for (const q of [eu, o]) coracao(acima(q, topo + 8 + (alvo === q.id ? 10 : 0)), 7 * pulso);
      const chave = id + ':' + t.dia + ':' + o.onde;
      if (!encontrosAvisados.has(chave)) { encontrosAvisados.add(chave); toast(`❤ ${rotulo(EU.morador)} encontrou ${rotulo(id)} ${LUGAR[o.onde] ? LUGAR[o.onde].em : 'na rua'}!`); }
    }
  }
  // plaquinha vermelha do morador seguido/selecionado (igual ao vídeo)
  if (alvo) {
    const e = estados[alvo - 1];
    const p = acima(e, e.vis ? topo + 3 : 4);
    let txt = rotulo(alvo);
    if (!e.vis) txt += ' · ' + (LUGAR[e.onde] ? LUGAR[e.onde].em : 'dentro');
    ctx.font = '700 13px "Pixelify Sans", Nunito, sans-serif';
    const w = ctx.measureText(txt).width + 16, y = p.y - 16 - Math.abs(Math.sin(agoraReal / 300)) * 3;
    ctx.fillStyle = '#1e1824'; pilula(p.x - w / 2 - 2, y - 13, w + 4, 26 + 2, 7); ctx.fill();
    ctx.fillStyle = '#d63838'; pilula(p.x - w / 2, y - 11, w, 22, 6); ctx.fill();
    ctx.beginPath(); ctx.moveTo(p.x - 6, y + 10); ctx.lineTo(p.x + 6, y + 10); ctx.lineTo(p.x, y + 17); ctx.closePath();
    ctx.fillStyle = '#d63838'; ctx.fill(); ctx.strokeStyle = '#1e1824'; ctx.lineWidth = 2; ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.fillText(txt, p.x, y);
  }
  if (EU) { const eu = estados[EU.morador - 1]; if (eu && eu.vis && desenhados.includes(eu)) desenharVidaNoBoneco(eu); }
  if (Math.abs(nf - ultimoNoite) > 0.01 || !$('#hudHora').textContent.startsWith(fmt(t.min))) atualizarRelogio(t, nf);
  ultimoNoite = nf;
}
function pilula(x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
function coracao(p, r) {
  ctx.save(); ctx.translate(p.x, p.y); ctx.scale(r / 7, r / 7);
  ctx.beginPath(); ctx.moveTo(0, 5); ctx.bezierCurveTo(-9, -1, -5, -9, 0, -4); ctx.bezierCurveTo(5, -9, 9, -1, 0, 5); ctx.closePath();
  ctx.fillStyle = '#ff4d6d'; ctx.fill(); ctx.strokeStyle = '#1e1824'; ctx.lineWidth = 1.5; ctx.stroke(); ctx.restore();
}

let ultimoQuadro = 0;
function loop(now) {
  requestAnimationFrame(loop);
  if (now - ultimoQuadro < 31) return;          // ~30 fps
  const dt = Math.min(0.1, (now - ultimoQuadro) / 1000);
  ultimoQuadro = now;
  passoControle(dt);
  desenhar(now);
  atualizarAcoes();
}

// ---------------------------------------------------------------------
// toque / mouse: arrastar, pinça, roda, tocar num morador
// ---------------------------------------------------------------------
const toques = new Map();
let arr = null, pinca = null;
cv.addEventListener('pointerdown', e => {
  cv.setPointerCapture(e.pointerId);
  toques.set(e.pointerId, { x: e.clientX, y: e.clientY });
  $('#relogioPainel').hidden = true;
  if (toques.size === 1) arr = { x: e.clientX, y: e.clientY, cx: cam.x, cy: cam.y, moveu: false };
  if (toques.size === 2) {
    const [a, b] = [...toques.values()];
    pinca = { d: Math.hypot(a.x - b.x, a.y - b.y), s: cam.s, m: telaPraMapa((a.x + b.x) / 2, (a.y + b.y) / 2) };
    if (arr) arr.moveu = true;
  }
});
cv.addEventListener('pointermove', e => {
  if (!toques.has(e.pointerId)) return;
  toques.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (toques.size >= 2 && pinca) {
    const [a, b] = [...toques.values()], mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
    cam.s = clamp(pinca.s * Math.hypot(a.x - b.x, a.y - b.y) / pinca.d, minS(), 6);
    cam.x = pinca.m.x - (mx - W / 2) / cam.s; cam.y = pinca.m.y - (my - H / 2) / cam.s; limitarCam();
    seguindo = null; return;
  }
  if (!arr) return;
  const dx = e.clientX - arr.x, dy = e.clientY - arr.y;
  if (!arr.moveu && Math.hypot(dx, dy) > 7) { arr.moveu = true; cv.classList.add('arrastando'); if (seguindo) { seguindo = null; atualizarBotaoSeguir(); } }
  if (arr.moveu) { cam.x = arr.cx - dx / cam.s; cam.y = arr.cy - dy / cam.s; limitarCam(); }
});
function soltar(e) {
  if (!toques.has(e.pointerId)) return;
  toques.delete(e.pointerId);
  if (toques.size < 2) pinca = null;
  if (toques.size === 0) {
    cv.classList.remove('arrastando');
    if (arr && !arr.moveu && e.type === 'pointerup') tocar(e.clientX, e.clientY);
    arr = null;
  } else if (toques.size === 1) {
    const [p] = [...toques.values()]; arr = { x: p.x, y: p.y, cx: cam.x, cy: cam.y, moveu: true };
  }
}
cv.addEventListener('pointerup', soltar);
cv.addEventListener('pointercancel', soltar);
cv.addEventListener('wheel', e => { e.preventDefault(); zoomEm(e.clientX, e.clientY, cam.s * Math.exp(-e.deltaY * 0.0015)); }, { passive: false });

function tocar(sx, sy) {
  if (INTERIOR) return tocarInterior(sx, sy);
  const m = telaPraMapa(sx, sy), tol = Math.max(7, 16 / cam.s);
  let melhor = null, md = 1e9;
  for (const e of desenhados) {
    const cx = e.px, cy = e.py - 6, d = Math.hypot((m.x - cx) / tol, (m.y - cy) / Math.max(11, 20 / cam.s));
    if (d < 1 && d < md) { md = d; melhor = e; }
  }
  if (melhor) return escolherNoMapa(melhor.id);
  const chao = desproj(m.x, m.y); m.x = chao.x; m.y = chao.y;
  const casa = CASAS.find(c => m.x >= c.lote[0] && m.x <= c.lote[0] + c.tamanho[0] && m.y >= c.lote[1] && m.y <= c.lote[1] + c.tamanho[1]);
  if (casa) return mostrar('casa', { n: casa.casa });
  if (selecionado && !seguindo) { selecionado = null; }
}
function escolherNoMapa(id) {
  if (escolhendo) {
    if (ocupado(id)) return toast(`${rotulo(id)} já tem dono. Escolhe outro!`);
    sairEscolha(); reg.id = id; selecionado = id; return mostrar('registrar', { passo: 1 });
  }
  selecionado = id; mostrar('ficha', { id });
}
function sairEscolha() { escolhendo = false; $('#avisoEscolher').hidden = true; cv.classList.remove('escolhendo'); $('#painel').hidden = false; }
$('#avisoCancelar').onclick = () => { sairEscolha(); mostrar('registrar', { passo: 1 }, false); };

$('#zoomMais').onclick = () => { const f = focoTela(); zoomEm(f.x, f.y, cam.s * 1.4); };
$('#zoomMenos').onclick = () => { const f = focoTela(); zoomEm(f.x, f.y, cam.s / 1.4); };
$('#zoomMeu').onclick = () => { if (EU) { seguir(EU.morador); mostrar('ficha', { id: EU.morador }); } };
function seguir(id) {
  seguindo = id; selecionado = id;
  if (cam.s < 2.5) cam.s = PC() ? 3 : 2.6;
  history.replaceState(null, '', '?m=' + id);
  atualizarBotaoSeguir();
}

// ---------------------------------------------------------------------
// CONTROLE do meu morador (só logado): analógico no celular, WASD/setas no PC.
// O movimento é local (só na tela de quem joga); os outros veem a rotina.
// ---------------------------------------------------------------------
const VEL_CONTROLE = 72;                 // px do mapa por segundo
const ctrl = { ativo: false, x: 0, y: 0, dir: 'down', anda: false, teclas: new Set(), joy: { x: 0, y: 0 } };
const tocaTela = matchMedia('(pointer: coarse)').matches;
if (tocaTela) document.body.classList.add('toque');

// vida (minigames vão mexer aqui depois). Guarda por morador neste aparelho.
const vidaChave = () => EU ? 'vila_vida_' + EU.morador : null;
function lerVida() { try { const v = Number(localStorage.getItem(vidaChave())); return Number.isFinite(v) && localStorage.getItem(vidaChave()) !== null ? clamp(v, 0, 100) : 100; } catch { return 100; } }
let VIDA = 100;
function mudarVida(v) {
  VIDA = clamp(Math.round(v), 0, 100);
  try { if (vidaChave()) localStorage.setItem(vidaChave(), VIDA); } catch {}
  atualizarVida();
}
function atualizarVida() {
  const box = $('#vida'), btn = $('#btnJogar');
  box.hidden = !EU; btn.hidden = !EU;
  if (!EU) { if (ctrl.ativo) pararControle(); return; }
  $('#vidaNome').textContent = EU.nome;
  $('#vidaPct').textContent = VIDA + '%';
  const b = $('#vidaEnche'); b.style.width = VIDA + '%';
  b.className = 'vida-enche' + (VIDA <= 25 ? ' baixa' : VIDA <= 60 ? ' media' : '');
  pintar($('#vidaAvatar'), lookDe(EU.morador));
}

// o que não dá pra atravessar: casas, prédios, igreja, rio e a borda do mapa
let OBSTACULOS = [];
function montarObstaculos() {
  const r = [], P = VILA.pontos;
  for (const c of CASAS) if (!c.hospedado) r.push([c.lote[0] + 2, c.lote[1] + 12, 38, 34]);
  for (const k of ['mercadinho', 'vendinha']) if (P[k]) r.push([P[k].porta[0] - 20, P[k].porta[1] - 46, 40, 42]);
  if (P.mercadinho2 && P.mercadinho2.lote) r.push([P.mercadinho2.lote[0] + 2, P.mercadinho2.lote[1] + 12, 38, 34]);
  for (const k of ['escola', 'prefeitura', 'prefeitura_reservada', 'posto']) if (P[k] && P[k].lotes) for (const l of P[k].lotes) r.push([l[0] + 2, l[1] + 12, 38, 34]);
  if (P.igreja) r.push([P.igreja.porta[0] - 34, P.igreja.porta[1] - 80, 70, 76]);
  OBSTACULOS = r;
}
function bloqueado(x, y) {
  if (x < 8 || x > MUNDO_W() - 8 || y < 24 || y > MUNDO_H() - 8) return true;   // borda do mapa
  if (x > 446 && x < 510) return true;                                // rio (ainda sem ponte)
  for (const [ox, oy, w, h] of OBSTACULOS) if (x > ox && x < ox + w && y > oy && y < oy + h) return true;
  return false;
}

function iniciarControle() {
  if (!EU) return;
  const m = MORADORES[EU.morador - 1], e = estado(m, simMs());
  let x = e.x, y = e.y;
  if (!e.vis || bloqueado(x, y)) { const c = CASAS[m.casa - 1]; x = c.ponto_na_rua[0]; y = c.ponto_na_rua[1]; }   // sai pela rua da casa
  Object.assign(ctrl, { ativo: true, x, y, dir: 'down', anda: false });
  ctrl.teclas.clear(); ctrl.joy.x = ctrl.joy.y = 0;
  fecharPainel();
  seguindo = selecionado = EU.morador;
  if (cam.s < 3) cam.s = PC() ? 3.4 : 3;
  $('#btnJogar').classList.add('ativo'); $('#btnJogar').innerHTML = '✋ Parar';
  $('#joystick').hidden = !tocaTela; $('#dicaTeclas').hidden = tocaTela;
  document.body.classList.add('jogando');
  toast(tocaTela ? '🎮 Use o analógico pra andar' : '🎮 Use WASD ou as setas pra andar');
  ctrl.cansaco = 0; ctrl.sentado = false; ctrl.portaBloq = false; enviarPos();
}
function pararControle() {
  if (INTERIOR && !INTERIOR.espectador) sairInterior();
  ctrl.sentado = false; enviarPos(true);
  ctrl.ativo = false; ctrl.anda = false; ctrl.teclas.clear(); ctrl.joy.x = ctrl.joy.y = 0;
  $('#btnJogar').classList.remove('ativo'); $('#btnJogar').innerHTML = '🎮 Mover meu boneco';
  $('#joystick').hidden = true; $('#dicaTeclas').hidden = true;
  document.body.classList.remove('jogando');
}
$('#btnJogar').onclick = () => ctrl.ativo ? pararControle() : iniciarControle();

function passoControle(dt) {
  if (!ctrl.ativo) return;
  // descansar (sentado ou deitado) recupera 1% a cada 2 s; dormir 3 s na própria cama enche a vida
  if (ctrl.sentado || (INTERIOR && INTERIOR.deitado)) { ctrl.descanso = (ctrl.descanso || 0) + dt; if (ctrl.descanso >= 2) { ctrl.descanso = 0; if (VIDA < 100) mudarVida(VIDA + 1); } }
  if (INTERIOR && INTERIOR.deitado && performance.now() - INTERIOR.deitado.t0 > 3000) { INTERIOR.deitado = null; mudarVida(100); toast('😴 Dormiu bem! Vida 100%'); }
  const k = ctrl.teclas;
  let ix = ctrl.joy.x + ((k.has('d') || k.has('arrowright')) ? 1 : 0) - ((k.has('a') || k.has('arrowleft')) ? 1 : 0);
  let iy = ctrl.joy.y + ((k.has('s') || k.has('arrowdown')) ? 1 : 0) - ((k.has('w') || k.has('arrowup')) ? 1 : 0);
  const mag = Math.hypot(ix, iy);
  if (mag < 0.15) { if (ctrl.anda) { ctrl.anda = false; enviarPos(true); } return; }
  if (ctrl.sentado) levantar();
  if (INTERIOR && INTERIOR.deitado) INTERIOR.deitado = null;
  if (mag > 1) { ix /= mag; iy /= mag; }
  const lento = VIDA <= 20 ? 0.6 : 1;
  const passo = VEL_CONTROLE * dt * lento * (INTERIOR ? 0.6 : 1), sx = ix, sy = iy;
  if (!INTERIOR && ISO()) { const mx = (sx + 2 * sy) / 2, my = (2 * sy - sx) / 2, n = Math.hypot(mx, my) || 1, f = Math.min(1, Math.hypot(sx, sy)); ix = mx / n * f; iy = my / n * f; }
  const bloq = INTERIOR ? bloqueadoInterior : bloqueado;
  const nx = ctrl.x + ix * passo, ny = ctrl.y + iy * passo;
  if (!bloq(nx, ctrl.y)) ctrl.x = nx;            // desliza na parede: tenta x e y separados
  if (!bloq(ctrl.x, ny)) ctrl.y = ny;
  ctrl.dir = Math.abs(sx) > Math.abs(sy) ? (sx > 0 ? 'right' : 'left') : (sy > 0 ? 'down' : 'up');   // virado pra onde anda na tela
  // andar cansa: -1% a cada 40 s andando (nunca abaixo de 5%)
  ctrl.cansaco = (ctrl.cansaco || 0) + dt;
  if (ctrl.cansaco > 40) { ctrl.cansaco = 0; if (VIDA > 5) mudarVida(VIDA - 1); if (VIDA <= 25 && !ctrl.avisouCansaco) { ctrl.avisouCansaco = true; toast('😮‍💨 Cansado! Come algo no mercadinho ou descansa em casa.'); } }
  if (ctrl.portaBloq && !INTERIOR && ctrl.portaPos && distP(ctrl.portaPos, ctrl.x, ctrl.y) > 14) ctrl.portaBloq = false;
  ctrl.anda = true;
  if (!INTERIOR) seguindo = EU.morador;           // voltou a andar: câmera volta a seguir
  enviarPos();
}

// teclado (PC)
const TECLAS = ['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'];
addEventListener('keydown', e => {
  if (!ctrl.ativo || /input|textarea|select/i.test(e.target.tagName)) return;
  const t = e.key.toLowerCase();
  if (TECLAS.includes(t)) { ctrl.teclas.add(t); e.preventDefault(); }
  if (t === 'escape') pararControle();
});
addEventListener('keyup', e => ctrl.teclas.delete(e.key.toLowerCase()));
addEventListener('blur', () => ctrl.teclas.clear());

// analógico (celular)
(() => {
  const base = $('#joyBase'), pino = $('#joyPino'); let id = null;
  const mover = e => {
    const r = base.getBoundingClientRect(), raio = r.width / 2;
    let dx = e.clientX - (r.left + raio), dy = e.clientY - (r.top + raio);
    const d = Math.hypot(dx, dy); if (d > raio) { dx *= raio / d; dy *= raio / d; }
    pino.style.transform = `translate(${dx}px, ${dy}px)`;
    ctrl.joy.x = dx / raio; ctrl.joy.y = dy / raio;
  };
  const soltar = () => { id = null; pino.style.transform = ''; ctrl.joy.x = ctrl.joy.y = 0; };
  base.addEventListener('pointerdown', e => { id = e.pointerId; base.setPointerCapture(id); mover(e); e.preventDefault(); });
  base.addEventListener('pointermove', e => { if (e.pointerId === id) mover(e); });
  base.addEventListener('pointerup', soltar); base.addEventListener('pointercancel', soltar);
})();

// barrinha de vida em cima do meu boneco (tela)
function desenharVidaNoBoneco(e) {
  const p = mapaPraTela(e.px, e.py - (ISO() ? 20 : 17)), w = 30, h = 5, x = Math.round(p.x - w / 2), y = Math.round(p.y - 8);
  ctx.fillStyle = '#1e1824'; ctx.fillRect(x - 1, y - 1, w + 2, h + 2);
  ctx.fillStyle = '#5a1f2a'; ctx.fillRect(x, y, w, h);
  ctx.fillStyle = VIDA <= 25 ? '#ff4d4d' : VIDA <= 60 ? '#f6c836' : '#40c463';
  ctx.fillRect(x, y, Math.round(w * VIDA / 100), h);
}

// =====================================================================
// TEMPO REAL: quem está online, bonecos controlados por outras pessoas
// =====================================================================
let ONLINE = new Map(), VISITANTES = 0;        // morador -> {m, nome}
const REMOTO = new Map();                      // morador -> {x, y, dir, anda, dentro, t}
let ultimaPosEnviada = 0;
function iniciarTempoReal() {
  if (!window.Rt) { atualizarChatUI(); return; }
  Rt.conectar({
    onOnline: o => {
      ONLINE = new Map((o.moradores || []).map(p => [p.m, p])); VISITANTES = o.visitantes || 0;
      for (const m of [...REMOTO.keys()]) if (!ONLINE.has(m)) REMOTO.delete(m);
      atualizarOnline();
    },
    onPos: p => { if (!p || !p.m || (EU && p.m === EU.morador)) return; if (p.fim) REMOTO.delete(p.m); else REMOTO.set(p.m, { ...p, t: performance.now() }); },
    onChat: msg => chatReceber(msg),
    onHistorico: msgs => { for (const m of msgs) chatReceber(m, true); },
  });
  atualizarPresenca(); atualizarChatUI();
}
function atualizarPresenca() { if (window.Rt) Rt.presenca(EU ? { m: EU.morador, nome: EU.nome } : null); }
function atualizarOnline() {
  const n = ONLINE.size, chip = $('#hudOnlineChip');
  chip.hidden = !(n || VISITANTES); $('#hudOnline').textContent = n;
  chip.title = `${n} com nome online · ${VISITANTES} visitando sem login`;
  if (telaAtual && telaAtual.tela === 'moradores' && telaAtual.args.aba === 'online') TELAS.moradores(telaAtual.args);
}
const estaOnline = id => ONLINE.has(id);
function enviarPos(final) {
  if (!window.Rt || !EU) return;
  const agora = performance.now();
  if (!final && agora - ultimaPosEnviada < 200) return;
  ultimaPosEnviada = agora;
  Rt.pos(final ? { m: EU.morador, fim: true }
    : { m: EU.morador, x: Math.round(ctrl.x), y: Math.round(ctrl.y), dir: ctrl.dir, anda: ctrl.anda, dentro: !!INTERIOR });
}
// aplica nos estados os bonecos que outras pessoas estão controlando agora
function aplicarRemotos() {
  const agora = performance.now();
  for (const [m, r] of REMOTO) {
    if (agora - r.t > 6000) { REMOTO.delete(m); continue; }
    const e = estados[m - 1]; if (!e) continue;
    estados[m - 1] = r.dentro ? { ...e, vis: false, onde: 'casa', faz: 'dentro de algum lugar' }
      : { ...e, vis: true, x: r.x, y: r.y, dir: r.dir || 'down', anda: !!r.anda && agora - r.t < 600, onde: 'controle', faz: 'passeando pela cidade (ao vivo)' };
  }
}

// =====================================================================
// CHAT ao vivo (estilo live: só logado escreve, mensagens somem com o tempo)
// =====================================================================
const CHAT_MAX = 40;
function chatReceber(msg, historico) {
  const box = $('#chatMsgs'); if (!box || !msg || !msg.texto) return;
  if (box.querySelector(`[data-id="${msg.id}"]`)) return;
  const el = document.createElement('div'); el.className = 'msg'; el.dataset.id = msg.id;
  el.dataset.t = historico ? String(Date.parse(msg.criado_em) || Date.now()) : String(Date.now());
  const meu = EU && msg.morador_id === EU.morador;
  el.innerHTML = `<b class="${meu ? 'eu' : ''}">${esc(msg.nome)}</b>${esc(msg.texto)}`;
  el.querySelector('b').onclick = () => { if (!INTERIOR && MORADORES[msg.morador_id - 1]) irPara(msg.morador_id); };
  box.appendChild(el);
  while (box.children.length > CHAT_MAX) box.firstChild.remove();
  envelhecerChat();
}
function envelhecerChat() {
  const box = $('#chatMsgs'); if (!box) return;
  const agora = Date.now(), lendo = $('#chat').matches(':hover, :focus-within');
  for (const el of box.children) {
    const idade = agora - Number(el.dataset.t);
    el.classList.toggle('velha', idade > 25000 && !lendo);
    el.classList.toggle('sumindo', idade > 60000 && !lendo);
  }
}
setInterval(envelhecerChat, 1000);
async function chatEnviar() {
  const inp = $('#chatInput'), t = inp.value.trim(); if (!t || !EU) return;
  inp.value = ''; const b = $('#chatEnviar'); b.disabled = true;
  const r = await Api.rpc('enviar_chat', { p_token: token(), p_texto: t });
  b.disabled = false; inp.focus();
  if (!r || !r.ok) { toast((r && r.erro) || 'Não deu pra enviar'); inp.value = t; return; }
  // se o tempo real não devolver em 1,5 s, mostra pelo menos pra mim
  setTimeout(() => { if (!$('#chatMsgs').querySelector(`[data-id="${r.id}"]`)) chatReceber({ id: r.id, morador_id: EU.morador, nome: EU.nome, texto: t, criado_em: new Date().toISOString() }); }, 1500);
}
function atualizarChatUI() {
  const c = $('#chat'); c.hidden = !window.Rt;
  $('#chatForm').hidden = !EU; $('#chatEntrar').hidden = !!EU;
  let fechado = false; try { fechado = localStorage.getItem('vila_chat') === '0'; } catch {}
  c.classList.toggle('fechado', fechado);
}
$('#chatEnviar').onclick = chatEnviar;
$('#chatInput').onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); chatEnviar(); } e.stopPropagation(); };
$('#chatToggle').onclick = () => { const c = $('#chat'); c.classList.toggle('fechado'); try { localStorage.setItem('vila_chat', c.classList.contains('fechado') ? '0' : '1'); } catch {} };
$('#chatEntrar').onclick = () => mostrar('entrar');

// =====================================================================
// AÇÕES perto do boneco (portas, banco, fonte, móveis) — botão na tela ou tecla E
// =====================================================================
let acoesAtuais = [];
const distP = (p, x, y) => Math.hypot(p[0] - x, p[1] - y);
function acoesPerto() {
  if (!ctrl.ativo || !EU) return [];
  if (INTERIOR) return acoesInterior();
  const a = [], P = VILA.pontos, x = ctrl.x, y = ctrl.y;
  if (!ctrl.portaBloq) {
    for (const c of CASAS) if (!c.hospedado && distP(c.porta, x, y) < 11) { a.push({ rotulo: `🚪 Entrar na ${nomeCasa(c.casa).toLowerCase()}`, fn: () => entrarInterior('casa', c.casa) }); break; }
    if (P.mercadinho && distP(P.mercadinho.porta, x, y) < 12) a.push({ rotulo: '🛒 Entrar no mercadinho', fn: () => entrarInterior('mercadinho', 1) });
    if (P.mercadinho2 && distP(P.mercadinho2.porta, x, y) < 12) a.push({ rotulo: '🛒 Entrar no mercadinho 2', fn: () => entrarInterior('mercadinho', 2) });
  }
  if (P.praca) {
    for (const b of P.praca.bancos) if (distP(b, x, y) < 9) { a.push(ctrl.sentado ? { rotulo: '🧍 Levantar', fn: levantar } : { rotulo: '🪑 Sentar no banco', fn: () => sentar(b[0], b[1] - 2, 'down') }); break; }
    if (P.praca.centro && distP(P.praca.centro, x, y) < 16) a.push({ rotulo: '🪙 Jogar moeda na fonte', fn: jogarMoeda });
  }
  return a.slice(0, 2);
}
function sentar(x, y, dir) { ctrl.sentado = true; ctrl.x = x; ctrl.y = y; ctrl.dir = dir || 'down'; ctrl.anda = false; enviarPos(true); enviarPos(); toast('🪑 Sentou. Descansar recupera vida aos poucos.'); }
function levantar() { ctrl.sentado = false; }
const SORTES = ['Hoje alguém vai te adicionar como amigo.', 'Um morador novo vai chegar na sua rua.', 'O dia pede um lanche no mercadinho.', 'A praça vai estar cheia à tarde.', 'Cuidado com a fila do caixa às 9h.',
  'Sua casa vai ganhar visita.', 'Boa hora pra personalizar o visual.', 'O próximo marco está mais perto do que parece.', 'Vai ter show na praça de novo… um dia.', 'Alguém falou de você no chat.'];
function jogarMoeda() {
  const t = br(simMs()), chave = 'vila_moeda_' + EU.morador; let ult = null;
  try { ult = localStorage.getItem(chave); } catch {}
  if (ult === String(t.dia)) return toast('🪙 Você já jogou sua moeda hoje. Amanhã tem mais!');
  try { localStorage.setItem(chave, String(t.dia)); } catch {}
  const r = rng(t.dia * 977 + EU.morador * 31);
  mudarVida(VIDA + 3); toast('✨ Sorte do dia: ' + SORTES[Math.floor(r() * SORTES.length)]);
}
function atualizarAcoes() {
  const box = $('#acoes'), novas = acoesPerto(), chave = novas.map(a => a.rotulo).join('|');
  if (chave === box.dataset.chave) return;
  box.dataset.chave = chave; acoesAtuais = novas;
  box.innerHTML = novas.map((a, i) => `<button data-i="${i}">${a.rotulo}${!tocaTela && i === 0 ? ' <kbd>E</kbd>' : ''}</button>`).join('');
  box.hidden = !novas.length;
  box.querySelectorAll('button').forEach(b => b.onclick = () => { const ac = acoesAtuais[Number(b.dataset.i)]; if (ac) ac.fn(); });
}
addEventListener('keydown', e => {
  if (!ctrl.ativo || /input|textarea|select/i.test(e.target.tagName)) return;
  if (e.key.toLowerCase() === 'e' && acoesAtuais[0]) { acoesAtuais[0].fn(); e.preventDefault(); }
});

// =====================================================================
// INTERIORES: casas (sorteadas por número, sempre iguais) e mercadinho
// =====================================================================
let INTERIOR = null;   // { tipo, n, cena, volta, espectador, tv, sacola, deitado, portaPos }
const ICV = document.createElement('canvas'); const ic = ICV.getContext('2d');
const COR = { tinta: '#1e1824', paredes: ['#e8d9b5', '#d7e3f0', '#f0d8d8', '#dfe9d2', '#f1e4c4', '#e4d6ea'], pisos: [['#b98a56', '#a97a48'], ['#d9d2c3', '#cfc7b6'], ['#c9a97a', '#b8986a'], ['#9fb7c9', '#8fa7b9']],
  sofas: ['#c0392b', '#2f6db5', '#3e8e5a', '#8e5aa3', '#d4883a'], tapetes: [['#c86b5c', '#e4958a'], ['#4e7fb3', '#7faad6'], ['#6f9d5a', '#9fc78a'], ['#c9a227', '#e3c45a']], cobertas: ['#d8584f', '#3f79c4', '#52a05c', '#d2912b', '#8f63b8', '#2fa3a7'] };
const PRODUTOS = ['Maçã', 'Pão', 'Leite', 'Suco', 'Chocolate', 'Banana', 'Queijo', 'Refri', 'Biscoito', 'Café'];
const LOOK_ATENDENTE = Sprites.normalizar({ pele: 2, cabelo: 'coque', cor_cabelo: 1, camisa: 3, estampa: 'lisa', camisa2: 3, baixo: 'calca', cor_baixo: 2, sapato: 0, oculos: true, chapeu: null, cor_chapeu: 0, barba: false });

function gerarCena(tipo, n) {
  const r = rng(tipo === 'casa' ? n * 7919 + 101 : 500000 + n), pick = a => a[Math.floor(r() * a.length)];
  const c = { tipo, n, w: 192, h: 144, paredeY: 28, parede: pick(COR.paredes), piso: pick(COR.pisos), moveis: [], bloq: [], camas: [], assentos: [], passeios: [], janelas: [],
              porta: { cx: 96, w: 24 }, spawn: { x: 96, y: 128 } };
  const add = (m, bloqueia = true) => { c.moveis.push(m); if (bloqueia) c.bloq.push([m.x, m.y, m.w, m.h]); return m; };
  if (tipo === 'casa') {
    c.tapete = pick(COR.tapetes); c.sofaCor = pick(COR.sofas); c.coberta = pick(COR.cobertas); c.cortina = pick(COR.sofas);
    // parede: janelas, quadro, relógio
    const jx = pick([[60, 120], [72], [52, 116], [86]]); for (const x of jx) c.janelas.push({ x, y: 6, w: 22, h: 16 });
    c.relogio = { x: jx.includes(120) ? 150 : 128, y: 8 }; c.quadro = r() < 0.7 ? { x: jx[0] - 20 > 30 ? jx[0] - 18 : 160, y: 8 } : null;
    // fila encostada na parede (base y = 30)
    add({ tipo: 'estante', x: 6, y: 8, w: 20, h: 26 }); c.bloq.pop(); c.bloq.push([6, 24, 20, 10]);
    if (r() < 0.85) { add({ tipo: 'tv', x: 36, y: 12, w: 24, h: 22 }); c.bloq.pop(); c.bloq.push([36, 26, 24, 8]); c.temTV = true; }
    const cozinha = [['pia', 18], ['fogao', 16], ['geladeira', 16]]; if (r() < 0.5) cozinha.reverse();
    let cx = 122; for (const [t, w] of cozinha) { add({ tipo: t, x: cx, y: t === 'geladeira' ? 8 : 20, w, h: t === 'geladeira' ? 26 : 14 }); c.bloq.pop(); c.bloq.push([cx, 24, w, 10]); cx += w + 4; }
    // beliches na parede da esquerda
    const nb = 2 + Math.floor(r() * 2);
    for (let i = 0; i < nb; i++) { const y = 44 + i * 30; add({ tipo: 'beliche', x: 6, y, w: 20, h: 26 }); c.camas.push({ x: 16, y: y + 12, cima: true }, { x: 16, y: y + 24 }); }
    // sofá de frente pra TV, mesa com cadeiras, tapete, planta, luminária
    if (c.temTV) { add({ tipo: 'sofa', x: 34, y: 48, w: 28, h: 14 }); c.assentos.push({ x: 42, y: 60, dir: 'up' }, { x: 54, y: 60, dir: 'up' }); }
    const my = c.temTV ? 84 : 66; c.tapeteR = { x: 62, y: my - 14, w: 72, h: 46 };
    add({ tipo: 'mesa', x: 78, y: my, w: 40, h: 18 });
    add({ tipo: 'cadeira', x: 68, y: my + 4, w: 8, h: 10, dir: 'right' }, false); c.assentos.push({ x: 72, y: my + 14, dir: 'right' });
    add({ tipo: 'cadeira', x: 120, y: my + 4, w: 8, h: 10, dir: 'left' }, false); c.assentos.push({ x: 124, y: my + 14, dir: 'left' });
    add({ tipo: 'planta', x: 176, y: 118, w: 10, h: 16 });
    if (r() < 0.7) add({ tipo: 'luminaria', x: 68, y: 40, w: 8, h: 20 }, false);
    if (r() < 0.5) add({ tipo: 'planta', x: 150, y: 44, w: 10, h: 16 });
    c.passeios = [{ x: 100, y: 124, A: 28 }, { x: 150, y: 70, A: 14 }, { x: 60, y: 120, A: 14 }, { x: 150, y: 100, A: 16 }];
  } else {
    c.parede = '#f3e9d2'; c.piso = ['#e6e1d6', '#dcd6ca'];
    for (let i = 0; i < 3; i++) {
      const y = 50 + i * 28, prods = [pick(PRODUTOS), pick(PRODUTOS), pick(PRODUTOS)].filter((p, k, a) => a.indexOf(p) === k);
      add({ tipo: 'gondola', x: 44, y, w: 100, h: 12, prods, seed: r() });
      c.passeios.push({ x: 94, y: y + 24, A: 40 });
    }
    add({ tipo: 'freezer', x: 168, y: 36, w: 18, h: 76 });
    add({ tipo: 'caixa', x: 14, y: 116, w: 40, h: 14 });
    add({ tipo: 'cestas', x: 124, y: 126, w: 12, h: 12 });
    c.janelas.push({ x: 30, y: 6, w: 22, h: 16 }, { x: 140, y: 6, w: 22, h: 16 }); c.relogio = { x: 92, y: 6 };
    c.passeios.push({ x: 160, y: 124, A: 12 });
  }
  return c;
}
function bloqueadoInterior(x, y) {
  const c = INTERIOR.cena;
  if (x < 4 || x > c.w - 4 || y < c.paredeY + 8) return true;
  if (y > c.h - 3 && Math.abs(x - c.porta.cx) > c.porta.w / 2) return true;
  if (y > c.h) return true;
  for (const [bx, by, bw, bh] of c.bloq) if (x > bx - 1 && x < bx + bw + 1 && y - 2 > by && y - 2 < by + bh) return true;
  return false;
}
function entrarInterior(tipo, n, espectador) {
  const cena = gerarCena(tipo, n);
  const portaPos = tipo === 'casa' ? CASAS[n - 1].porta : (n === 2 ? VILA.pontos.mercadinho2 : VILA.pontos.mercadinho).porta;
  INTERIOR = { tipo, n, cena, espectador: !!espectador || !ctrl.ativo, tv: false, sacola: [], deitado: null, portaPos, volta: { x: ctrl.x, y: ctrl.y } };
  if (!INTERIOR.espectador) { ctrl.x = cena.spawn.x; ctrl.y = cena.spawn.y; ctrl.dir = 'up'; ctrl.sentado = false; ctrl.anda = false; }
  document.body.classList.add('interior'); $('#interiorTopo').hidden = false; fecharPainel();
  atualizarTituloInterior(); enviarPos(true); enviarPos();
}
function sairInterior() {
  if (!INTERIOR) return;
  const I = INTERIOR; INTERIOR = null;
  if (!I.espectador) { ctrl.x = I.portaPos[0]; ctrl.y = I.portaPos[1] + 5; ctrl.dir = 'down'; ctrl.sentado = false; ctrl.portaBloq = true; ctrl.portaPos = I.portaPos; }
  document.body.classList.remove('interior'); $('#interiorTopo').hidden = true;
  enviarPos(true); enviarPos();
}
$('#btnSairInterior').onclick = sairInterior;
function moradoresDentro() {
  const I = INTERIOR;
  if (I.tipo === 'casa') return MORADORES.filter(m => m.casa === I.n && estados[m.id - 1] && !estados[m.id - 1].vis && estados[m.id - 1].onde === 'casa' && !(EU && m.id === EU.morador && !I.espectador));
  const lista = estados.filter(e => !e.vis && e.onde === 'mercadinho' && !(EU && e.id === EU.morador && !I.espectador)).map(e => MORADORES[e.id - 1]);
  return I.n === 2 ? lista.filter((_, i) => i % 2 === 1).slice(0, 10) : lista.filter((_, i) => i % 2 === 0).slice(0, 10);
}
function atualizarTituloInterior() {
  if (!INTERIOR) return;
  const n = moradoresDentro().length, I = INTERIOR;
  $('#interiorTitulo').textContent = (I.tipo === 'casa' ? nomeCasa(I.n) : 'Mercadinho' + (I.n === 2 ? ' 2' : '')) + ` · ${n} ${n === 1 ? 'pessoa' : 'pessoas'} aqui dentro`
    + (I.sacola.length ? ` · 🛍️ ${I.sacola.length}` : '');
}
function posicoesDentro(seg) {
  const c = INTERIOR.cena, dorm = [], acord = [];
  for (const m of moradoresDentro()) ((estados[m.id - 1].faz === 'dormindo') ? dorm : acord).push(m);
  const out = [];
  dorm.forEach((m, i) => { const s = c.camas[i]; out.push(s ? { m, x: s.x, y: s.y, dir: 'down', dorme: true } : { m, x: 40 + (i % 6) * 14, y: 126, dir: 'down', dorme: true }); });
  acord.forEach((m, i) => {
    const a = c.assentos[i];
    if (a) { out.push({ m, x: a.x, y: a.y, dir: a.dir, sentado: true }); return; }
    const L = c.passeios[(i - c.assentos.length) % c.passeios.length], v = vaivem({ A: L.A, v: 3, pausa: 3 + (m.id % 5), seed: m.id * 3 + INTERIOR.n }, seg);
    out.push({ m, x: L.x + v.dx, y: L.y + ((m.id % 3) - 1) * 3, dir: v.dir, anda: v.anda });
  });
  return out;
}
function acoesInterior() {
  const I = INTERIOR, c = I.cena, x = ctrl.x, y = ctrl.y, a = [], minha = I.tipo === 'casa' && EU && MORADORES[EU.morador - 1].casa === I.n;
  const perto = m => x > m.x - 9 && x < m.x + m.w + 9 && y > m.y - 6 && y < m.y + m.h + 12;
  if (I.deitado) return [{ rotulo: '🙂 Levantar', fn: () => { I.deitado = null; } }];
  if (y > c.h - 9 && Math.abs(x - c.porta.cx) < 12) a.push({ rotulo: '🚪 Sair', fn: sairInterior });
  for (const m of c.moveis) {
    if (!perto(m)) continue;
    if (m.tipo === 'geladeira') a.push({ rotulo: '🧃 Pegar um lanche', fn: () => {
      if (!minha) return toast('😅 Essa geladeira não é sua!');
      if (ctrl.lancheT && performance.now() - ctrl.lancheT < 60000) return toast('🧃 Já comeu agora há pouco. Espera um minuto.');
      ctrl.lancheT = performance.now(); mudarVida(VIDA + 5); toast('🧃 Lanchinho! +5 de vida'); } });
    else if (m.tipo === 'tv') a.push({ rotulo: I.tv ? '📺 Desligar a TV' : '📺 Ligar a TV', fn: () => { I.tv = !I.tv; } });
    else if (m.tipo === 'beliche') a.push({ rotulo: '😴 Descansar', fn: () => {
      if (!minha) return toast('😅 Essa cama não é sua!');
      const cama = c.camas.find(k => k.y > m.y + 20) || c.camas[0]; I.deitado = { x: cama.x, y: cama.y, t0: performance.now() }; ctrl.anda = false; } });
    else if (m.tipo === 'sofa') a.push(ctrl.sentado ? { rotulo: '🧍 Levantar', fn: levantar } : { rotulo: '🛋️ Sentar no sofá', fn: () => sentar(m.x + 14, m.y + 12, 'up') });
    else if (m.tipo === 'gondola') { const p = m.prods[Math.min(m.prods.length - 1, Math.floor((x - m.x) / (m.w / m.prods.length)))];
      a.push({ rotulo: `🛒 Pegar ${p}`, fn: () => { if (I.sacola.length >= 4) return toast('🛍️ A sacola está cheia (4 itens). Passa no caixa!'); I.sacola.push(p); atualizarTituloInterior(); toast(`🛍️ ${p} na sacola (${I.sacola.length}/4)`); } }); }
    else if (m.tipo === 'caixa') a.push({ rotulo: I.sacola.length ? `💳 Pagar ${I.sacola.length} ${I.sacola.length === 1 ? 'item' : 'itens'}` : '💳 Caixa (sacola vazia)', fn: () => {
      if (!I.sacola.length) return toast('🛒 Pega alguma coisa nas prateleiras primeiro.');
      const ganho = 8 * I.sacola.length; mudarVida(VIDA + ganho); toast(`💳 Comprou ${I.sacola.join(', ')}. +${ganho} de vida!`); I.sacola = []; atualizarTituloInterior(); } });
    else if (m.tipo === 'freezer') a.push({ rotulo: '🍦 Pegar sorvete', fn: () => { if (I.sacola.length >= 4) return toast('🛍️ A sacola está cheia (4 itens). Passa no caixa!'); I.sacola.push('Sorvete'); atualizarTituloInterior(); toast(`🍦 Sorvete na sacola (${I.sacola.length}/4)`); } });
  }
  return a.slice(0, 2);
}

// ---------- desenho do interior ----------
const R = (x, y, w, h, cor) => { ic.fillStyle = cor; ic.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h)); };
const B = (x, y, w, h, cor) => { R(x - 1, y - 1, w + 2, h + 2, COR.tinta); R(x, y, w, h, cor); };   // com contorno
function desenharMovel(m, I, t, agoraReal) {
  const { x, y, w, h } = m, c = I.cena;
  switch (m.tipo) {
    case 'estante': B(x, y, w, h, '#8a5a2b'); for (let s = 0; s < 3; s++) { R(x + 1, y + 2 + s * 8, w - 2, 6, '#6e4520'); for (let k = 0; k < 5; k++) R(x + 2 + k * 3.5, y + 2 + s * 8, 3, 6, ['#c0392b', '#2f6db5', '#3e8e5a', '#d4883a', '#f1c40f'][(k + s + c.n) % 5]); } break;
    case 'tv': B(x + 2, y + 16, w - 4, 6, '#7a4e26'); B(x + 2, y, w - 4, 14, '#2b2b33'); {
      if (I.tv) { const f = Math.floor(agoraReal / 300); for (let k = 0; k < 4; k++) R(x + 4 + k * 4, y + 2, 4, 10, ['#5dade2', '#f5b7b1', '#82e0aa', '#f9e79f', '#bb8fce'][(f + k) % 5]); } else R(x + 4, y + 2, w - 8, 10, '#121218'); } break;
    case 'geladeira': B(x, y, w, h, '#eef1f4'); R(x, y + 9, w, 1, '#b8c0c8'); R(x + w - 4, y + 3, 1, 4, '#8a949e'); R(x + w - 4, y + 12, 1, 8, '#8a949e'); break;
    case 'fogao': B(x, y, w, h, '#dcdcdc'); R(x + 1, y + 1, w - 2, 5, '#444'); for (let k = 0; k < 2; k++) for (let j = 0; j < 2; j++) R(x + 3 + k * 7, y + 2 + j * 2, 3, 1, '#111'); R(x + 2, y + 8, w - 4, 4, '#555'); break;
    case 'pia': B(x, y, w, h, '#cbb089'); R(x + 3, y + 2, w - 6, 6, '#e6e6e6'); R(x + w / 2 - 1, y - 3, 2, 4, '#9aa'); R(x + w / 2 - 1, y - 4, 4, 1, '#9aa'); break;
    case 'beliche': B(x, y, w, h, '#8a5a2b'); for (const dy of [4, 16]) { R(x + 1, y + dy, w - 2, 7, '#f4efe4'); R(x + 1, y + dy, 5, 7, '#fff'); R(x + 6, y + dy + 1, w - 7, 6, c.coberta); } R(x + 1, y, 2, h, '#6e4520'); R(x + w - 3, y, 2, h, '#6e4520'); break;
    case 'sofa': B(x, y, w, h, c.sofaCor); R(x + 2, y + 5, w - 4, 7, shade(c.sofaCor)); R(x + w / 2 - 0.5, y + 5, 1, 7, c.sofaCor); break;
    case 'mesa': R(x + 2, y + h - 3, 2, 5, '#6e4520'); R(x + w - 4, y + h - 3, 2, 5, '#6e4520'); B(x, y, w, h - 4, '#c08a4a'); R(x + 4, y + 3, w - 8, 1, '#d9a564'); break;
    case 'cadeira': B(x, y, w, h - 2, '#a06a34'); R(m.dir === 'right' ? x : x + w - 2, y - 2, 2, h, '#7a4e26'); break;
    case 'planta': B(x + 1, y + 10, w - 2, 6, '#b5562c'); R(x, y + 2, w, 9, '#2e8b57'); R(x + 2, y, w - 4, 4, '#3cb371'); R(x + 4, y + 6, 2, 2, '#1f6b3f'); break;
    case 'luminaria': R(x + 3, y + 6, 2, h - 6, '#555'); B(x, y, w, 7, '#f6d78c'); if (ehNoite(t)) { ic.fillStyle = 'rgba(255,230,140,.18)'; ic.beginPath(); ic.ellipse(x + 4, y + 22, 22, 16, 0, 0, Math.PI * 2); ic.fill(); } break;
    case 'gondola': B(x, y, w, h, '#6d6d7a'); R(x, y + 5, w, 1, '#9a9aa8'); { const r = rng(Math.floor(m.seed * 1e6)); for (let lv = 0; lv < 2; lv++) for (let k = 0; k < 16; k++) R(x + 2 + k * 6, y + 1 + lv * 6, 4, 4, `hsl(${Math.floor(r() * 360)},65%,55%)`); } break;
    case 'freezer': B(x, y, w, h, '#f4f6f8'); R(x + 2, y + 2, w - 4, h - 4, 'rgba(120,190,240,.45)'); for (let k = 0; k < 6; k++) R(x + 4, y + 5 + k * 12, w - 8, 6, ['#f7c8e0', '#c8e6f7', '#f7eec8'][k % 3]); break;
    case 'caixa': B(x, y, w, h, '#8a5a2b'); B(x + w - 14, y - 8, 10, 8, '#555'); R(x + w - 12, y - 6, 6, 3, '#9fe0ff'); break;
    case 'cestas': for (let k = 0; k < 3; k++) B(x, y + 6 - k * 3, w, 5, '#c0392b'); break;
  }
}
const shade = c => c.replace('#', '#').length ? c + 'cc' : c;
const ehNoite = t => noiteFator(t.min) > 0.5;
function desenharInterior(agoraReal, t, nf) {
  const I = INTERIOR, c = I.cena, seg = t.min * 60;
  if (ICV.width !== c.w) { ICV.width = c.w; ICV.height = c.h; }
  ic.imageSmoothingEnabled = false;
  // parede e piso
  R(0, 0, c.w, c.paredeY, c.parede); R(0, c.paredeY, c.w, 3, '#8c6a3f');
  for (let y = c.paredeY + 3; y < c.h; y += 6) for (let x = 0; x < c.w; x += 16) R(x, y, 16, 6, c.piso[((x / 16 + y / 6) % 2) | 0]);
  for (let x = 0; x < c.w; x += 8) R(x, 2 + (x / 8 % 2) * 4, 1, 1, 'rgba(0,0,0,.08)');
  if (c.tapeteR) { const T = c.tapeteR; B(T.x, T.y, T.w, T.h, c.tapete[0]); R(T.x + 3, T.y + 3, T.w - 6, T.h - 6, c.tapete[1]); }
  // janelas (céu pela hora), quadro, relógio
  for (const j of c.janelas) { const ceu = nf >= 1 ? '#1b2140' : nf > 0 ? '#e4915a' : '#8fd0ff'; B(j.x, j.y, j.w, j.h, ceu); R(j.x + j.w / 2 - 0.5, j.y, 1, j.h, '#fff'); R(j.x, j.y + j.h / 2, j.w, 1, '#fff');
    if (nf >= 1) for (let k = 0; k < 4; k++) R(j.x + 3 + k * 5, j.y + 2 + (k * 7) % 11, 1, 1, '#fff'); if (c.cortina) { R(j.x - 3, j.y - 2, 4, j.h + 4, c.cortina); R(j.x + j.w - 1, j.y - 2, 4, j.h + 4, c.cortina); } }
  if (c.quadro) { B(c.quadro.x, c.quadro.y, 12, 10, '#8fd0ff'); R(c.quadro.x, c.quadro.y + 6, 12, 4, '#5fa04c'); R(c.quadro.x + 8, c.quadro.y + 2, 3, 3, '#f6c836'); }
  if (c.relogio) { const k = c.relogio; B(k.x, k.y, 10, 10, '#fff'); const hm = t.min / 60, ang = (h, r) => [k.x + 5 + Math.sin(h) * r, k.y + 5 - Math.cos(h) * r];
    ic.strokeStyle = '#1e1824'; ic.lineWidth = 1; ic.beginPath(); ic.moveTo(k.x + 5, k.y + 5); ic.lineTo(...ang((hm % 12) / 12 * Math.PI * 2, 2.5)); ic.moveTo(k.x + 5, k.y + 5); ic.lineTo(...ang((t.min % 60) / 60 * Math.PI * 2, 4)); ic.stroke(); }
  // objetos e pessoas, ordenados de trás pra frente
  const itens = c.moveis.map(m => ({ y: m.y + m.h, mv: m }));
  const pessoas = posicoesDentro(seg).map(p => ({ y: p.y + (p.dorme ? -6 : 0), p }));
  if (I.tipo === 'mercadinho') pessoas.push({ y: 118, p: { atendente: true, x: 34, y: 116, dir: 'down' } });
  if (!I.espectador) pessoas.push({ y: (I.deitado ? I.deitado.y - 6 : ctrl.y), p: { eu: true, x: I.deitado ? I.deitado.x : ctrl.x, y: I.deitado ? I.deitado.y : ctrl.y, dir: I.deitado ? 'down' : ctrl.dir, anda: ctrl.anda && !ctrl.sentado, dorme: !!I.deitado } });
  const quadro = Math.floor(agoraReal / 125) % 4;
  for (const o of [...itens, ...pessoas].sort((a, b) => a.y - b.y)) {
    if (o.mv) { desenharMovel(o.mv, I, t, agoraReal); continue; }
    const p = o.p, x = Math.round(p.x), y = Math.round(p.y);
    let img, ox = 0, oy = 0;
    if (p.atendente) { img = folhaDe(LOOK_ATENDENTE).dia; } else { const f = fonteSprite(p.eu ? EU.morador : p.m.id, false); img = f.img; ox = f.ox; oy = f.oy; }
    const fr = p.anda ? (quadro + (p.m ? p.m.id : 0)) % 4 : 0;
    if (!p.dorme) { ic.fillStyle = 'rgba(0,0,0,.18)'; ic.beginPath(); ic.ellipse(x, y, 4, 1.5, 0, 0, Math.PI * 2); ic.fill(); }
    ic.drawImage(img, ox + fr * 12, oy + DIRI[p.dir || 'down'] * 18, 12, 18, x - 6, y - 17, 12, 18);
    if (p.dorme) R(x - 6, y - 9, 12, 8, c.coberta || '#8f63b8');
    o.sx = x; o.sy = y;
  }
  // escuro quando é noite e não tem ninguém acordado
  const acordado = pessoas.some(o => !o.p.dorme);
  if (nf > 0 && !acordado) { ic.fillStyle = `rgba(10,12,40,${0.55 * nf})`; ic.fillRect(0, 0, c.w, c.h); }
  // porta
  B(c.porta.cx - c.porta.w / 2, c.h - 4, c.porta.w, 4, '#8a5a2b'); R(c.porta.cx - 3, c.h - 3, 6, 2, '#f6c836');

  // ---- blit na tela, centralizado, escala inteira
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  ctx.fillStyle = nf > 0.5 ? '#141a2a' : '#2a3b2a'; ctx.fillRect(0, 0, W, H);
  const topo = $('#hud').getBoundingClientRect().bottom + 8, base = H - (PC() ? 90 : 160);
  const z = Math.max(2, Math.min(Math.floor((W - 24) / c.w), Math.floor((base - topo) / c.h)));
  const ox0 = Math.round((W - c.w * z) / 2), oy0 = Math.round(topo + (base - topo - c.h * z) / 2);
  I.tela = { ox: ox0, oy: oy0, z };
  ctx.imageSmoothingEnabled = false;
  ctx.fillStyle = '#1e1824'; ctx.fillRect(ox0 - 4, oy0 - 4, c.w * z + 8, c.h * z + 8);
  ctx.drawImage(ICV, ox0, oy0, c.w * z, c.h * z);
  // nomes e zzz em escala de tela
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.font = '700 11px Nunito, system-ui, sans-serif';
  for (const o of pessoas) {
    if (o.sx == null) continue;
    const X = ox0 + o.sx * z, Y = oy0 + (o.sy - 19) * z;
    if (o.p.dorme) { ctx.fillStyle = '#fff8e7'; ctx.font = '700 11px Nunito, sans-serif'; ctx.fillText('z', X + 8 + Math.sin(agoraReal / 400) * 2, Y - 2 - (agoraReal / 60 % 10)); ctx.fillText('Z', X + 13, Y - 10 - (agoraReal / 60 % 10)); }
    const id = o.p.eu ? EU.morador : o.p.m ? o.p.m.id : null;
    const n = o.p.atendente ? 'Atendente' : (id && nomeDe(id));
    if (!n) continue;
    const w = ctx.measureText(n).width + 10;
    ctx.fillStyle = o.p.eu ? 'rgba(246,200,54,.95)' : 'rgba(30,24,36,.72)'; pilula(X - w / 2, Y - 8, w, 15, 7); ctx.fill();
    ctx.fillStyle = o.p.eu ? '#1e1824' : '#fff8e7'; ctx.fillText(n, X, Y);
  }
  I.pessoas = pessoas;
  if ((agoraReal | 0) % 60 === 0) atualizarTituloInterior();
}
function tocarInterior(sx, sy) {
  const I = INTERIOR; if (!I || !I.tela) return;
  const rx = (sx - I.tela.ox) / I.tela.z, ry = (sy - I.tela.oy) / I.tela.z;
  let melhor = null, md = 1e9;
  for (const o of I.pessoas || []) { if (!o.p.m) continue; const d = Math.hypot(o.p.x - rx, o.p.y - 8 - ry); if (d < 9 && d < md) { md = d; melhor = o.p.m.id; } }
  if (melhor) mostrar('ficha', { id: melhor });
}

// =====================================================================
// MUDAR DE CASA (troca de lugar com um morador sem nome da casa escolhida)
// =====================================================================
async function mudarDeCasa(n) {
  if (!EU) return mostrar('entrar');
  const casa = CASAS[n - 1]; if (!casa) return;
  if (casa.moradores.every(ocupado)) return toast('Essa casa já está cheia: os 10 moradores têm nome.');
  if (MORADORES[EU.morador - 1].casa === n) return toast('Você já mora nessa casa!');
  if (!confirm(`Mudar para a ${nomeCasa(n).toLowerCase()}?\n\nVocê troca de lugar com um morador sem nome dessa casa (ele vai pra sua casa antiga). Seu nome, visual, bio e amigos vão junto. Dá pra mudar 1 vez por dia.`)) return;
  const look = Sprites.normalizar(lookDe(EU.morador));
  const r = await Api.rpc('trocar_casa', { p_token: token(), p_casa: n, p_aparencia: look });
  if (!r || !r.ok) return toast((r && r.erro) || 'Não deu pra mudar');
  const antigo = EU.morador, novo = r.morador;
  PUB[antigo] = { id: antigo, casa: MORADORES[antigo - 1].casa, chegou_no_ep: MORADORES[antigo - 1].chegou_no_ep, nome: null, usuario: null, aparencia: null, bio: null, ocupado: false };
  PUB[novo] = { id: novo, casa: n, chegou_no_ep: MORADORES[novo - 1].chegou_no_ep, nome: EU.nome, usuario: EU.usuario, aparencia: look, bio: EU.bio || null, ocupado: true };
  try { const v = localStorage.getItem('vila_vida_' + antigo); if (v != null) localStorage.setItem('vila_vida_' + novo, v); } catch {}
  EU.morador = novo; EU.aparencia = look;
  if (ctrl.ativo) { if (INTERIOR) sairInterior(); ctrl.x = casa.ponto_na_rua[0]; ctrl.y = casa.ponto_na_rua[1]; }
  seguindo = selecionado = novo; history.replaceState(null, '', '?m=' + novo);
  atualizarHud(); atualizarPresenca(); await carregarMeusAmigos(); carregarPublicos();
  toast(`🏠 Mudou! Agora você é o morador #${novo}, na ${nomeCasa(n).toLowerCase()}.`);
  mostrar('ficha', { id: novo }, false);
}

// ---------------------------------------------------------------------
// topo: relógio e números
// ---------------------------------------------------------------------
function atualizarRelogio(t, nf) {
  $('#hudHora').textContent = fmt(t.min);
  $('#hudIcone').textContent = nf >= 1 ? '🌙' : nf > 0 ? '🌅' : '☀️';
  const v = relogio.vel;
  $('#hudVel').textContent = v === 1 ? '' : v > 1.5 ? 'x' + Math.round(v) : 'outro horário';
}
// nome do marco sem o comentário entre parênteses (cabe no celular)
const curto = t => String(t).replace(/\s*\([^)]*\)/g, '').trim();
function atualizarHud() {
  $('#hudEp').textContent = 'EP ' + VILA.episodio;
  $('#hudNome').textContent = VILA.nome_vila || 'A Cidade dos Seguidores';
  $('#hudMoradores').textContent = VILA.seguidores;
  $('#hudCasas').textContent = VILA.casas;
  const registrados = MORADORES.filter(m => ocupado(m.id)).length;
  $('#hudReg').textContent = registrados;
  $('#hudLivres').textContent = MORADORES.length - registrados;
  // número ao vivo (se houver) manda na barra do marco; o mapa é o do último episódio
  const seg = AO_VIVO ?? VILA.seguidores;
  const chegando = Math.max(0, seg - VILA.seguidores);
  $('#hudVivoChip').hidden = AO_VIVO == null;
  if (AO_VIVO != null) $('#hudVivo').textContent = AO_VIVO.toLocaleString('pt-BR');
  $('#hudChegandoChip').hidden = !chegando;
  $('#hudChegando').textContent = '+' + chegando;
  const marcos = (VILA.marcos || []).filter(m => m.seguidores > VILA.seguidores);
  const pm = marcos.find(m => m.seguidores > seg) || VILA.proximo_marco;
  const liberado = marcos.find(m => m.seguidores <= seg);   // passou do marco, mas o episódio ainda não saiu
  if (liberado) {
    $('#hudMarcoTxt').textContent = `🎉 Desbloqueou: ${curto(liberado.construcao)}! Chega no próximo episódio ›`;
    $('#hudMarcoBarra').style.width = '100%';
  } else if (pm) {
    const falta = Math.max(0, pm.seguidores - seg), ant = Math.max(...(VILA.marcos || [{ seguidores: 0 }]).map(m => m.seguidores).filter(s => s <= seg), 0);
    $('#hudMarcoTxt').textContent = `faltam ${falta} pra ${curto(pm.construcao)} ›`;
    $('#hudMarcoBarra').style.width = clamp(100 * (seg - ant) / Math.max(1, pm.seguidores - ant), 3, 100) + '%';
  } else $('#hudMarco').hidden = true;
  $('#menuEuTxt').textContent = EU ? 'Eu' : 'Entrar';
  $('#menuRegTxt').textContent = EU ? 'Meu boneco' : 'Registrar';
  $('#zoomMeu').hidden = !EU;
  if (EU) VIDA = lerVida();
  atualizarVida();
}
$('#hudMarco').onclick = () => mostrar('regras', {}, false);
$('#hudOnlineChip').onclick = () => mostrar('moradores', { aba: 'online' }, false);
$('#btnRelogio').onclick = () => {
  const p = $('#relogioPainel'); p.hidden = !p.hidden;
  p.querySelectorAll('[data-vel]').forEach(b => b.classList.toggle('ativo', Number(b.dataset.vel) === Math.round(relogio.vel) && (relogio.vel === 1 ? Math.abs(simMs() - Date.now()) < 60000 : true)));
};
$('#relogioPainel').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  if (b.dataset.vel) setVel(Number(b.dataset.vel));
  if (b.dataset.pula) pular(Number(b.dataset.pula));
  $('#btnRelogio').onclick(); $('#btnRelogio').onclick();
});

let toastT;
function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('on'); clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove('on'), 3200); }

// ---------------------------------------------------------------------
// painel (bottom sheet / lateral) e telas
// ---------------------------------------------------------------------
const pilha = [];
let telaAtual = null;
const reg = { id: null, look: null, nome: '', usuario: '' };
const ed = { orig: null, look: null, nome: '', nomeOrig: '', bio: '', bioOrig: '', dir: 'down', modo: 'editar', salvoAgora: false };
const sujo = () => telaAtual && telaAtual.tela === 'editor' && ed.modo === 'editar' &&
  (JSON.stringify(ed.look) !== JSON.stringify(ed.orig) || ed.nome.trim() !== ed.nomeOrig || ed.bio.trim() !== ed.bioOrig);

function podeSair() {
  if (!sujo()) return true;
  return confirm('Você tem alterações não salvas no seu morador. Sair sem salvar?');
}
function mostrar(tela, args = {}, empilhar = true) {
  if (telaAtual && telaAtual.tela === 'editor' && !(tela === 'editor')) { if (!podeSair()) return false; preview = null; }
  if (empilhar && telaAtual && telaAtual.tela !== tela) pilha.push(telaAtual);
  if (!empilhar) {}
  telaAtual = { tela, args };
  const p = $('#painel'); p.hidden = false; document.body.classList.add('com-painel');
  p.classList.remove('minimizado', 'meio');
  if (!PC() && (tela === 'ficha' || tela === 'casa')) p.classList.add('meio');
  $('#painelVoltar').hidden = pilha.length === 0;
  document.querySelectorAll('#menu button').forEach(b => b.classList.toggle('ativo', b.dataset.aba === ({ ficha: '', casa: '', editor: 'registrar', entrar: 'eu' }[tela] ?? tela)));
  TELAS[tela](args);
  $('#painelCorpo').scrollTop = 0;
  return true;
}
function fecharPainel() {
  if (telaAtual && telaAtual.tela === 'editor') { if (!podeSair()) return; preview = null; }
  $('#painel').hidden = true; document.body.classList.remove('com-painel');
  telaAtual = null; pilha.length = 0;
  document.querySelectorAll('#menu button').forEach(b => b.classList.remove('ativo'));
}
$('#painelFechar').onclick = fecharPainel;
$('#painelVoltar').onclick = () => {
  const ant = pilha.pop(); if (!ant) return;
  if (!mostrar(ant.tela, ant.args, false)) pilha.push(ant);
};
$('#painelAlca').onclick = () => {
  const p = $('#painel');
  if (p.classList.contains('minimizado')) p.classList.remove('minimizado');
  else if (p.classList.contains('meio')) { p.classList.remove('meio'); }
  else p.classList.add('minimizado');
};
document.querySelectorAll('#menu button').forEach(b => b.onclick = () => {
  const aba = b.dataset.aba;
  if (telaAtual && b.classList.contains('ativo')) return fecharPainel();
  pilha.length = 0; telaAtual && telaAtual.tela === 'editor' ? null : (telaAtual = null);
  if (aba === 'registrar' && EU) return mostrar('editor', { modo: 'editar' }, false);
  if (aba === 'eu') return mostrar(EU ? 'eu' : 'entrar', {}, false);
  mostrar(aba, {}, false);
});
function titulo(t) { $('#painelTitulo').textContent = t; }
function corpo(html) { $('#painelCorpo').innerHTML = html; return $('#painelCorpo'); }

function itemLista(id, direita = '') {
  const e = estados[id - 1], n = nomeDe(id), u = PUB[id] && PUB[id].usuario;
  const agora = e ? (e.onde === 'andando' ? e.faz : (LUGAR[e.onde] ? LUGAR[e.onde].em : '')) : '';
  return `<li><button data-id="${id}"><canvas width="12" height="15" data-look="${id}"></canvas>
    <span class="l-txt"><span class="l-nome">${esc(n || 'Morador #' + id)}</span>
    <span class="l-sub">${u ? '@' + esc(u) + ' · ' : ''}#${id} · ${esc(agora)}</span></span>
    <span class="l-dir">${direita}</span></button></li>`;
}
function ligarLista(raiz, aoClicar) {
  raiz.querySelectorAll('canvas[data-look]').forEach(c => pintar(c, lookDe(Number(c.dataset.look))));
  raiz.querySelectorAll('button[data-id]').forEach(b => b.onclick = () => aoClicar(Number(b.dataset.id)));
}
const irPara = id => { seguir(id); mostrar('ficha', { id }); };

const TELAS = {
  // ------------------------------------------------ buscar
  buscar() {
    titulo('Buscar morador');
    const c = corpo(`<div class="busca"><input id="qBusca" type="search" placeholder="Nome, @ ou número (ex: 205)" autocomplete="off" enterkeyhint="search"></div><ul class="lista" id="resBusca"></ul>`);
    const inp = c.querySelector('#qBusca'), res = c.querySelector('#resBusca');
    const rodar = () => {
      const q = inp.value.trim().toLowerCase().replace(/^#/, '');
      let ids;
      if (!q) {
        ids = Object.values(PUB).filter(p => p.ocupado && p.nome).map(p => p.id).slice(-30).reverse();
        res.innerHTML = (ids.length ? `<li class="texto-2" style="padding:6px 4px;font-size:13px">Moradores com nome:</li>` + ids.map(id => itemLista(id)).join('')
          : `<li class="vazio">Ninguém registrou ainda. Seja o primeiro!</li>`);
      } else {
        const num = /^\d+$/.test(q) ? Number(q) : null, u = q.replace(/^@/, '');
        ids = [];
        if (num && num >= 1 && num <= MORADORES.length) ids.push(num);
        for (const p of Object.values(PUB)) if (p.ocupado && p.id !== num && ((p.nome || '').toLowerCase().includes(q) || (p.usuario || '').includes(u))) ids.push(p.id);
        res.innerHTML = ids.length ? ids.slice(0, 40).map(id => itemLista(id)).join('') : `<li class="vazio">Não achei ninguém com “${esc(q)}”.</li>`;
      }
      ligarLista(res, irPara);
    };
    inp.oninput = rodar; rodar();
    if (PC()) setTimeout(() => inp.focus(), 50);
  },

  // ------------------------------------------------ moradores
  moradores(a) {
    titulo('Moradores');
    const aba = a.aba || 'rua';
    const abas = [['online', '🟢 Online'], ['rua', 'Na rua agora'], ['nome', 'Com nome'], ['livres', 'Livres']];
    if (EU) abas.push(['amigos', 'Meus amigos']);
    const c = corpo(`<div class="abas">${abas.map(([k, t]) => `<button data-a="${k}" class="${k === aba ? 'ativo' : ''}">${t}</button>`).join('')}</div><div id="conteudoAba"></div>`);
    c.querySelectorAll('.abas button').forEach(b => b.onclick = () => { telaAtual.args = { aba: b.dataset.a }; TELAS.moradores(telaAtual.args); });
    const cont = c.querySelector('#conteudoAba');
    let ids = [], topo = '';
    if (aba === 'online') {
      ids = [...ONLINE.keys()].filter(id => MORADORES[id - 1]);
      topo = `<p class="mini">${ids.length} ${ids.length === 1 ? 'morador com nome está' : 'moradores com nome estão'} no site agora · ${VISITANTES} visitando sem login.</p>` + (ids.length ? '' : '<div class="dica">Ninguém com nome online agora. Entra e chama os amigos!</div>');
    } else if (aba === 'rua') {
      ids = estados.filter(e => e.vis).sort((x, y) => (ocupado(y.id) - ocupado(x.id)) || x.id - y.id).map(e => e.id);
      topo = `<p class="mini">${ids.length} moradores fora de casa agora.</p>`;
    } else if (aba === 'nome') {
      ids = Object.values(PUB).filter(p => p.ocupado && p.nome).sort((x, y) => x.nome.localeCompare(y.nome)).map(p => p.id);
    } else if (aba === 'livres') {
      const livres = MORADORES.map(m => m.id).filter(id => !ocupado(id));
      const r = rng(Math.floor(Date.now() / 60000));
      ids = livres.sort(() => r() - 0.5).slice(0, 30);
      topo = `<p class="mini">${livres.length} moradores ainda sem dono. Toque num pra ver e registrar.</p>
        <div class="botoes"><button class="btn btn-a btn-larga" id="btnAleatorio">🎲 Me dá um aleatório</button></div>`;
    } else if (aba === 'amigos') {
      ids = [...MEUS.segue];
      topo = ids.length ? '' : `<div class="dica">Você ainda não adicionou ninguém. Abra a ficha de um morador e toque em <b>Adicionar amigo</b>.</div>`;
    }
    const mais = ids.length > 80;
    cont.innerHTML = topo + `<ul class="lista">${ids.slice(0, 80).map(id => itemLista(id, aba === 'amigos' && MEUS.seguidores.has(id) ? '★ mútuo' : estaOnline(id) ? '🟢 online' : '')).join('')}</ul>`
      + (mais ? `<p class="mini" style="text-align:center;margin-top:8px">Mostrando 80 de ${ids.length}. Use a busca pra achar alguém.</p>` : '')
      + (!ids.length && aba !== 'amigos' && aba !== 'online' ? `<p class="vazio">${aba === 'nome' ? 'Ninguém registrou ainda.' : 'Todo mundo está em casa agora.'}</p>` : '');
    ligarLista(cont, aba === 'livres' ? (id => { selecionado = id; seguir(id); mostrar('ficha', { id }); }) : irPara);
    const ba = cont.querySelector('#btnAleatorio');
    if (ba) ba.onclick = () => { const l = MORADORES.filter(m => !ocupado(m.id)); const id = l[Math.floor(Math.random() * l.length)].id; irPara(id); };
  },

  // ------------------------------------------------ ficha do morador
  ficha({ id }) {
    const m = MORADORES[id - 1], p = PUB[id] || {}, eu = EU && EU.morador === id;
    titulo(p.nome || `Morador #${id}`);
    const c = corpo(`
      <div class="ficha-topo">
        <canvas class="retrato" width="16" height="20" id="fichaRetrato"></canvas>
        <div class="ficha-info">
          <p class="ficha-nome">${esc(p.nome || 'Morador #' + id)}</p>
          ${p.usuario ? `<div class="ficha-user">@${esc(p.usuario)}</div>` : `<div class="texto-2" style="font-weight:700">Livre — ainda sem dono</div>`}
          <div class="etiquetas">
            <span class="etq">#${id}</span><span class="etq">${nomeCasa(m.casa)}</span><span class="etq">Chegou no ep. ${m.chegou_no_ep}</span>
            ${eu ? '<span class="etq etq-eu">Você</span>' : !p.ocupado ? '<span class="etq etq-livre">Livre</span>' : ''}${estaOnline(id) ? '<span class="etq etq-livre">🟢 online agora</span>' : ''}
          </div>
        </div>
      </div>
      <p class="bio">“${esc(p.bio || bioAuto(m))}”${p.bio ? '' : '<small>escrita pela vila</small>'}</p>
      <div class="agora" id="fichaAgora"></div>
      <div class="botoes">
        <button class="btn btn-flex" id="btnSeguir"></button>
        <button class="btn btn-flex" id="btnLink">🔗 Link</button>
        ${!p.ocupado && !EU ? `<button class="btn btn-p btn-larga" id="btnMeu">⭐ Esse é meu!</button>` : ''}
        ${eu ? `<button class="btn btn-a btn-larga" id="btnEditar">🎨 Personalizar meu morador</button>` : ''}
      </div>
      <div class="secao" id="fichaAmigos"></div>
      <div class="secao"><h3>Agenda de hoje <small id="fichaDia"></small></h3><ul class="agenda" id="fichaAgenda"></ul></div>
      <div class="secao"><h3>Mora com <small>casa ${m.casa}</small></h3><ul class="lista" id="fichaCasa"></ul></div>`);
    pintar(c.querySelector('#fichaRetrato'), lookDe(id));
    atualizarFicha();
    atualizarBotaoSeguir();
    c.querySelector('#btnSeguir').onclick = () => { if (seguindo === id) { seguindo = null; history.replaceState(null, '', location.pathname); atualizarBotaoSeguir(); } else seguir(id); };
    c.querySelector('#btnLink').onclick = () => compartilhar(id);
    const bm = c.querySelector('#btnMeu'); if (bm) bm.onclick = () => { reg.id = id; reg.look = null; mostrar('editor', { modo: 'registro' }); };
    const be = c.querySelector('#btnEditar'); if (be) be.onclick = () => mostrar('editor', { modo: 'editar' });
    const vizinhos = CASAS[m.casa - 1].moradores.filter(x => x !== id);
    const lc = c.querySelector('#fichaCasa'); lc.innerHTML = vizinhos.map(v => itemLista(v)).join(''); ligarLista(lc, irPara);
    renderAmigos(id);
  },

  // ------------------------------------------------ casa
  casa({ n }) {
    const casa = CASAS[n - 1];
    titulo(nomeCasa(n));
    const dentro = casa.moradores.filter(id => estados[id - 1] && estados[id - 1].onde === 'casa').length;
    const c = corpo(`<p class="mini">${casa.pronta ? '' : `Em obra — fica pronta com ${casa.pronta_em || 10 * n} seguidores. `}Rua ${casa.rua} · ${dentro} de ${casa.moradores.length} em casa agora${escolhendo ? ' · toque num livre pra escolher' : ''}.</p>
      ${EU && !escolhendo && MORADORES[EU.morador - 1].casa !== n && !casa.moradores.every(ocupado) ? '<p class="mini">Quer morar aqui? Você troca de lugar com um morador sem nome desta casa (1 mudança por dia).</p>' : ''}
      <div class="botoes">
        <button class="btn btn-flex" id="btnVerInterior">👀 Ver o interior</button>
        ${EU && !escolhendo ? (MORADORES[EU.morador - 1].casa === n ? '<span class="etq etq-eu" style="align-self:center">🏠 você mora aqui</span>'
          : casa.moradores.every(ocupado) ? '<button class="btn btn-flex" disabled>🏠 Casa cheia (10 com nome)</button>'
          : '<button class="btn btn-a btn-flex" id="btnMudar">🏠 Quero morar aqui</button>') : ''}
      </div>
      <ul class="lista">${casa.moradores.map(id => itemLista(id, ocupado(id) ? (estaOnline(id) ? '🟢' : '') : '<span class="etq etq-livre">livre</span>')).join('')}</ul>`);
    ligarLista(c, id => {
      if (escolhendo) return escolherNoMapa(id);
      irPara(id);
    });
    c.querySelector('#btnVerInterior').onclick = () => entrarInterior('casa', n, true);
    const bm = c.querySelector('#btnMudar'); if (bm) bm.onclick = () => mudarDeCasa(n);
  },

  // ------------------------------------------------ registrar
  registrar({ passo = 1 }) {
    if (EU) return mostrar('editor', { modo: 'editar' }, false);
    titulo('Registrar meu morador');
    if (passo === 1) {
      const id = reg.id, livre = id && !ocupado(id);
      const c = corpo(`<div class="passos"><span class="feito"></span><span></span><span></span></div>
        <p style="margin-top:0"><b>1. Escolha um morador</b> que ainda não tem dono. Depois você pode personalizar ele e colocar seu nome.</p>
        ${livre ? `<ul class="lista">${itemLista(id, '<span class="etq etq-livre">escolhido</span>')}</ul>` : id ? `<div class="erro">O #${id} já tem dono. Escolhe outro.</div>` : ''}
        <div class="botoes">
          <button class="btn btn-flex" id="btnNoMapa">👆 Escolher no mapa</button>
          <button class="btn btn-flex" id="btnSorteio">🎲 Aleatório</button>
        </div>
        <label class="campo"><span>Ou digite o número</span><input id="numMorador" inputmode="numeric" placeholder="1 a ${MORADORES.length}" value="${id || ''}"></label>
        <div class="botoes"><button class="btn btn-p btn-larga" id="btnPasso2" ${livre ? '' : 'disabled'}>Continuar →</button></div>
        <div class="dica">Já tem um? <a href="#" id="lnkEntrar">Entrar com @ e PIN</a></div>`);
      if (livre) ligarLista(c, irPara);
      c.querySelector('#btnNoMapa').onclick = () => {
        escolhendo = true; $('#avisoEscolher').hidden = false; cv.classList.add('escolhendo');
        $('#painel').hidden = true; if (cam.s < 2) cam.s = 2.4;
      };
      c.querySelector('#btnSorteio').onclick = () => {
        const l = MORADORES.filter(m => !ocupado(m.id)); reg.id = l[Math.floor(Math.random() * l.length)].id;
        seguir(reg.id); TELAS.registrar({ passo: 1 });
      };
      c.querySelector('#numMorador').onchange = e => { const v = Number(e.target.value); if (v >= 1 && v <= MORADORES.length) { reg.id = v; seguir(v); TELAS.registrar({ passo: 1 }); } };
      c.querySelector('#btnPasso2').onclick = () => { reg.look = null; mostrar('editor', { modo: 'registro' }); };
      c.querySelector('#lnkEntrar').onclick = e => { e.preventDefault(); mostrar('entrar'); };
    } else {
      const c = corpo(`<div class="passos"><span class="feito"></span><span class="feito"></span><span class="feito"></span></div>
        <ul class="lista">${itemLista(reg.id)}</ul>
        <p><b>3. Seus dados.</b> O PIN é a sua senha pra voltar e editar depois — anote!</p>
        <label class="campo"><span>Nome que aparece no boneco</span><input id="rNome" maxlength="20" value="${esc(reg.nome)}" placeholder="Ex: Gui" autocomplete="nickname"></label>
        <label class="campo"><span>Seu @</span><input id="rUser" maxlength="21" value="${esc(reg.usuario)}" placeholder="@seu_user" autocapitalize="off" autocomplete="username"><small>3 a 20 letras, números, _ ou .</small></label>
        <label class="campo"><span>PIN (6 números)</span><input id="rPin" type="password" inputmode="numeric" maxlength="6" autocomplete="new-password"></label>
        <label class="campo"><span>Repita o PIN</span><input id="rPin2" type="password" inputmode="numeric" maxlength="6" autocomplete="new-password"></label>
        <div id="rErro"></div>
        <div class="botoes"><button class="btn btn-p btn-larga" id="btnRegistrar">✅ Registrar morador #${reg.id}</button></div>`);
      ligarLista(c, () => {});
      c.querySelector('#rNome').oninput = e => reg.nome = e.target.value;
      c.querySelector('#rUser').oninput = e => reg.usuario = e.target.value;
      c.querySelector('#btnRegistrar').onclick = async ev => {
        const nome = c.querySelector('#rNome').value.trim(), user = c.querySelector('#rUser').value.trim();
        const pin = c.querySelector('#rPin').value, pin2 = c.querySelector('#rPin2').value;
        const err = t => c.querySelector('#rErro').innerHTML = `<div class="erro">${esc(t)}</div>`;
        if (nome.length < 2) return err('Coloca um nome com pelo menos 2 letras');
        if (!/^@?[a-zA-Z0-9_.]{3,20}$/.test(user)) return err('@ precisa ter 3 a 20 letras, números, _ ou .');
        if (!/^\d{6}$/.test(pin)) return err('O PIN precisa ter 6 números');
        if (pin !== pin2) return err('Os dois PINs não batem');
        ev.target.disabled = true;
        const r = await Api.rpc('registrar', { p_morador: reg.id, p_usuario: user, p_nome: nome, p_pin: pin, p_aparencia: reg.look });
        ev.target.disabled = false;
        if (!r || !r.ok) return err((r && r.erro) || 'Não deu certo');
        entrou(r);
        PUB[reg.id] = { id: reg.id, nome: r.nome, usuario: r.usuario, aparencia: r.aparencia, ocupado: true };
        atualizarHud(); toast(`🎉 Bem-vindo à vila, ${r.nome}!`);
        const id = reg.id; Object.assign(reg, { id: null, look: null, nome: '', usuario: '' });
        pilha.length = 0; seguir(id); mostrar('ficha', { id }, false);
      };
    }
  },

  // ------------------------------------------------ editor de aparência (com botão Salvar)
  editor({ modo }) {
    ed.modo = modo;
    const id = modo === 'editar' ? EU.morador : reg.id;
    if (!telaAtual.args._iniciado) {
      const base = modo === 'editar' ? (EU.aparencia || MORADORES[id - 1].aparencia) : (reg.look || MORADORES[id - 1].aparencia);
      ed.orig = Sprites.normalizar(base); ed.look = { ...ed.orig };
      ed.nomeOrig = modo === 'editar' ? EU.nome : ''; ed.nome = ed.nomeOrig; ed.salvoAgora = false;
      ed.bioOrig = modo === 'editar' ? (EU.bio || '') : ''; ed.bio = ed.bioOrig;
      telaAtual.args._iniciado = true;
      seguir(id);
    }
    preview = { id, look: ed.look };
    titulo(modo === 'editar' ? 'Personalizar meu morador' : 'Registrar meu morador');
    const S = Sprites, L = ed.look;
    const cores = (campo, pal) => `<div class="cores">${pal.map((c, i) => `<button class="cor ${L[campo] === i ? 'ativo' : ''}" style="background:rgb(${c})" data-campo="${campo}" data-v="${i}" aria-label="cor ${i + 1}"></button>`).join('')}</div>`;
    const ops = (campo, lista, nomes, prev = true) => `<div class="opcoes">${lista.map((v, i) => `<button class="op ${prev ? '' : 'op-txt'} ${L[campo] === v ? 'ativo' : ''}" data-campo="${campo}" data-v='${JSON.stringify(v)}'>${prev ? `<canvas width="12" height="18" data-prev='${JSON.stringify({ [campo]: v })}'></canvas>` : ''}${nomes[i]}</button>`).join('')}</div>`;
    const sujoAgora = modo === 'editar' && sujo();
    const scroll = $('#painelCorpo').scrollTop;
    const c = corpo(`
      ${modo === 'registro' ? '<div class="passos"><span class="feito"></span><span class="feito"></span><span></span></div><p style="margin-top:0"><b>2. Deixe ele com a sua cara</b> (ou pule e fique com o visual original).</p>' : ''}
      <div class="editor-palco">
        <canvas width="12" height="18" id="palco"></canvas>
        <div class="palco-lado">
          <div class="palco-giro"><button id="giraE" aria-label="Girar">⟲</button><button id="giraD" aria-label="Girar">⟳</button></div>
          <button class="btn" id="btnSortear">🎲 Aleatório</button>
          <button class="btn" id="btnOriginal">↺ Visual original</button>
          ${modo === 'editar' ? (sujoAgora ? '<span class="nao-salvo">● Alterações não salvas</span>' : ed.salvoAgora ? '<span class="salvo-ok">✓ Salvo</span>' : '') : ''}
        </div>
      </div>
      ${modo === 'editar' ? `<label class="campo"><span>Nome que aparece no boneco</span><input id="edNome" maxlength="20" value="${esc(ed.nome)}"></label>
        ${TEM_BIO ? `<label class="campo"><span>Bio — uma frase sobre você</span><input id="edBio" maxlength="90" value="${esc(ed.bio)}" placeholder="${esc(bioAuto(MORADORES[id - 1]))}"><small>Até 90 letras. Vazio = a vila escreve uma frase pela sua rotina.</small></label>` : ''}` : ''}
      <div class="ed-grupo"><b>Pele</b>${cores('pele', S.SKIN16)}</div>
      <div class="ed-grupo"><b>Cabelo</b>${ops('cabelo', S.HAIRSTYLES, ['Curto', 'Raspado', 'Longo', 'Rabo', 'Coque', 'Black', 'Careca', 'Franja'])}</div>
      ${L.cabelo !== 'careca' || L.barba ? `<div class="ed-grupo"><b>Cor do cabelo</b>${cores('cor_cabelo', S.HAIR16)}</div>` : ''}
      <div class="ed-grupo"><b>Rosto</b><div class="opcoes">
        <button class="op op-txt ${L.oculos ? 'ativo' : ''}" data-campo="oculos" data-v="${!L.oculos}">👓 Óculos</button>
        <button class="op op-txt ${L.barba ? 'ativo' : ''}" data-campo="barba" data-v="${!L.barba}">🧔 Barba</button></div></div>
      <div class="ed-grupo"><b>Chapéu</b>${ops('chapeu', S.CHAPEUS, ['Nenhum', 'Boné', 'Palha', 'Gorro'])}</div>
      ${L.chapeu === 'bone' || L.chapeu === 'gorro' ? `<div class="ed-grupo"><b>Cor do chapéu</b>${cores('cor_chapeu', S.SHIRT16)}</div>` : ''}
      <div class="ed-grupo"><b>Roupa de cima</b>${ops('estampa', S.ESTAMPAS, ['Lisa', 'Listrada', 'Regata', 'Duas cores'])}</div>
      <div class="ed-grupo"><b>Cor ${L.baixo === 'vestido' ? 'da roupa / vestido' : 'da camisa'}</b>${cores('camisa', S.SHIRT16)}</div>
      ${L.estampa === 'listrada' || L.estampa === 'duas_cores' ? `<div class="ed-grupo"><b>Segunda cor</b>${cores('camisa2', S.SHIRT16)}</div>` : ''}
      <div class="ed-grupo"><b>Roupa de baixo</b>${ops('baixo', S.BAIXOS, ['Calça', 'Bermuda', 'Saia', 'Vestido'])}</div>
      ${L.baixo !== 'vestido' ? `<div class="ed-grupo"><b>Cor da ${L.baixo === 'calca' ? 'calça' : L.baixo}</b>${cores('cor_baixo', S.PANTS16)}</div>` : ''}
      <div class="ed-grupo"><b>Sapato</b>${cores('sapato', S.SHOES16)}</div>
      <div class="editor-rodape" id="edRodape">
        ${modo === 'editar'
          ? `<button class="btn btn-flex" id="btnDescartar" ${sujoAgora ? '' : 'disabled'}>Descartar</button>
             <button class="btn btn-v btn-flex" id="btnSalvar" ${sujoAgora ? '' : 'disabled'}>💾 Salvar</button>`
          : `<button class="btn btn-flex" id="btnPular">Pular</button>
             <button class="btn btn-p btn-flex" id="btnPasso3">Continuar →</button>`}
      </div>
      <div id="edErro"></div>`);
    c.scrollTop = scroll;
    c.querySelectorAll('canvas[data-prev]').forEach(cv2 => pintar(cv2, { ...L, ...JSON.parse(cv2.dataset.prev) }));
    const palco = c.querySelector('#palco');
    const desenhaPalco = () => pintar(palco, L, ed.dir, 0);
    desenhaPalco();
    const dirs = ['down', 'left', 'up', 'right'];
    c.querySelector('#giraE').onclick = () => { ed.dir = dirs[(dirs.indexOf(ed.dir) + 1) % 4]; desenhaPalco(); };
    c.querySelector('#giraD').onclick = () => { ed.dir = dirs[(dirs.indexOf(ed.dir) + 3) % 4]; desenhaPalco(); };
    const mudar = novo => { ed.look = Sprites.normalizar(novo); ed.salvoAgora = false; TELAS.editor({ modo }); };
    c.querySelectorAll('[data-campo]').forEach(b => b.onclick = () => {
      const campo = b.dataset.campo; let v = b.dataset.v;
      v = (campo === 'oculos' || campo === 'barba') ? v === 'true' : JSON.parse(v);
      mudar({ ...ed.look, [campo]: v });
    });
    c.querySelector('#btnSortear').onclick = () => {
      const r = Math.random, S2 = Sprites, pick = a => a[Math.floor(r() * a.length)];
      const cab = pick(S2.HAIRSTYLES);
      mudar({ pele: Math.floor(r() * 6), cabelo: cab, cor_cabelo: Math.floor(r() * 8), camisa: Math.floor(r() * 12), estampa: pick(S2.ESTAMPAS),
              camisa2: Math.floor(r() * 12), baixo: pick(S2.BAIXOS), cor_baixo: Math.floor(r() * 6), sapato: Math.floor(r() * 4),
              oculos: r() < 0.25, chapeu: r() < 0.3 ? pick(['bone', 'palha', 'gorro']) : null, cor_chapeu: Math.floor(r() * 12),
              barba: r() < 0.2 && !['longo', 'coque', 'rabo'].includes(cab) });
    };
    c.querySelector('#btnOriginal').onclick = () => mudar(MORADORES[id - 1].aparencia);
    if (modo === 'editar') {
      const inp = c.querySelector('#edNome'), inpBio = c.querySelector('#edBio');
      inp.oninput = () => {
        ed.nome = inp.value; if (inpBio) ed.bio = inpBio.value; ed.salvoAgora = false;
        const s = sujo();
        c.querySelector('#btnSalvar').disabled = !s; c.querySelector('#btnDescartar').disabled = !s;
        const lado = c.querySelector('.palco-lado'), tag = lado.querySelector('.nao-salvo, .salvo-ok');
        if (tag) tag.remove();
        if (s) lado.insertAdjacentHTML('beforeend', '<span class="nao-salvo">● Alterações não salvas</span>');
      };
      if (inpBio) inpBio.oninput = inp.oninput;
      c.querySelector('#btnDescartar').onclick = () => { ed.nome = ed.nomeOrig; ed.bio = ed.bioOrig; mudar(ed.orig); };
      c.querySelector('#btnSalvar').onclick = async ev => {
        ev.target.disabled = true; ev.target.textContent = 'Salvando…';
        const params = { p_token: token(), p_nome: ed.nome.trim(), p_aparencia: ed.look };
        if (TEM_BIO) params.p_bio = ed.bio.trim();
        const r = await Api.rpc('salvar_perfil', params);
        if (!r || !r.ok) {
          c.querySelector('#edErro').innerHTML = `<div class="erro">${esc((r && r.erro) || 'Não deu pra salvar')}</div>`;
          if (r && r.erro === 'Entre de novo') sairConta();
          ev.target.disabled = false; ev.target.textContent = '💾 Salvar'; return;
        }
        EU.nome = ed.nome.trim(); EU.aparencia = { ...ed.look }; if (TEM_BIO) EU.bio = ed.bio.trim() || null;
        PUB[EU.morador] = { ...(PUB[EU.morador] || {}), id: EU.morador, nome: EU.nome, aparencia: EU.aparencia, bio: EU.bio || null, ocupado: true, usuario: EU.usuario };
        ed.orig = { ...ed.look }; ed.nomeOrig = EU.nome; ed.bioOrig = EU.bio || ''; ed.bio = ed.bioOrig; ed.salvoAgora = true;
        toast('💾 Morador salvo!'); TELAS.editor({ modo });
      };
    } else {
      c.querySelector('#btnPular').onclick = () => { reg.look = null; preview = null; mostrar('registrar', { passo: 3 }); };
      c.querySelector('#btnPasso3').onclick = () => {
        const igual = JSON.stringify(ed.look) === JSON.stringify(Sprites.normalizar(MORADORES[id - 1].aparencia));
        reg.look = igual ? null : { ...ed.look }; preview = null;
        mostrar('registrar', { passo: 3 });
      };
    }
  },

  // ------------------------------------------------ regras da vila
  regras() {
    titulo('Como a vila cresce');
    const seg = VILA.seguidores, pc = VILA.proxima_casa;
    const marcos = (VILA.marcos || []).map(m => {
      const feito = m.seguidores <= seg, prox = !feito && !(VILA.marcos || []).some(x => x.seguidores > seg && x.seguidores < m.seguidores);
      return `<li class="${prox ? 'atual' : feito ? 'passou' : ''}"><span class="hora">${m.seguidores.toLocaleString('pt-BR')}</span>
        <span>${feito ? '✅' : prox ? '🏗️' : '🔒'} ${esc(m.construcao)}${prox ? ` <b>· faltam ${m.seguidores - seg}</b>` : ''}</span></li>`;
    }).join('');
    corpo(`<p style="margin-top:0">Cada pessoa que segue o canal vira um morador da vila. Hoje são <b>${seg}</b> moradores em <b>${VILA.casas}</b> casas.</p>
      <div class="secao"><h3>Regras</h3><ul class="agenda">${(VILA.regras || []).map(r => `<li><span>🏠 ${esc(r)}</span></li>`).join('')}</ul></div>
      ${pc ? `<div class="encontro">🔨 Próxima casa: <b>#${pc.numero}</b> — obra começa com ${pc.comeca_em} e fica pronta com ${pc.pronta_em} seguidores</div>` : ''}
      <div class="secao"><h3>Marcos <small>construções novas</small></h3><ul class="agenda">${marcos}</ul></div>`);
  },

  // ------------------------------------------------ entrar
  entrar() {
    titulo('Entrar');
    const c = corpo(`<p style="margin-top:0">Entre com o <b>@</b> e o <b>PIN</b> que você usou pra registrar seu morador.</p>
      <label class="campo"><span>Seu @</span><input id="eUser" placeholder="@seu_user" autocapitalize="off" autocomplete="username"></label>
      <label class="campo"><span>PIN</span><input id="ePin" type="password" inputmode="numeric" maxlength="6" autocomplete="current-password"></label>
      <div id="eErro"></div>
      <div class="botoes"><button class="btn btn-p btn-larga" id="btnEntrar">Entrar</button></div>
      <div class="dica">Ainda não tem morador? <a href="#" id="lnkReg">Registrar um agora</a></div>`);
    const ir = async () => {
      const b = c.querySelector('#btnEntrar'); b.disabled = true;
      const r = await Api.rpc('entrar', { p_usuario: c.querySelector('#eUser').value, p_pin: c.querySelector('#ePin').value });
      b.disabled = false;
      if (!r || !r.ok) return c.querySelector('#eErro').innerHTML = `<div class="erro">${esc((r && r.erro) || 'Não deu certo')}</div>`;
      entrou(r); toast(`Oi, ${r.nome}!`); pilha.length = 0; seguir(r.morador); mostrar('ficha', { id: r.morador }, false);
    };
    c.querySelector('#btnEntrar').onclick = ir;
    c.querySelector('#ePin').onkeydown = e => { if (e.key === 'Enter') ir(); };
    c.querySelector('#lnkReg').onclick = e => { e.preventDefault(); mostrar('registrar', { passo: 1 }); };
  },

  // ------------------------------------------------ eu
  eu() {
    if (!EU) return mostrar('entrar', {}, false);
    titulo('Meu morador');
    const id = EU.morador, mut = [...MEUS.segue].filter(x => MEUS.seguidores.has(x)).length;
    const pend = pedidos();
    const c = corpo(`<ul class="lista">${itemLista(id, '<span class="etq etq-eu">você</span>')}</ul>
      <div class="etiquetas" style="margin-top:4px"><span class="etq">❤ ${MEUS.segue.size} amigos</span><span class="etq">★ ${mut} mútuos</span></div>
      <div class="secao"><h3>Pedidos de amizade <small>${pend.length ? pend.length + ' esperando' : 'nenhum agora'}</small></h3>
        ${pend.length ? `<ul class="lista pedidos" id="euPend">${pend.map(x => itemPedido(x)).join('')}</ul>` : '<p class="mini">Quando alguém te adicionar como amigo, aparece aqui.</p>'}</div>
      <div class="botoes">
        <button class="btn btn-flex" id="euVer">📍 Ver na vila</button>
        <button class="btn btn-flex" id="euLink">🔗 Meu link</button>
        <button class="btn btn-a btn-larga" id="euEditar">🎨 Personalizar visual e nome</button>
        <button class="btn btn-flex" id="euAmigos">❤ Meus amigos</button>
        <button class="btn btn-flex" id="euCasa">🏠 Minha casa</button>
        <button class="btn btn-flex" id="euSair">Sair</button>
      </div>`);
    ligarLista(c, irPara);
    ligarPedidos(c);
    c.querySelector('#euVer').onclick = () => irPara(id);
    c.querySelector('#euLink').onclick = () => compartilhar(id);
    c.querySelector('#euEditar').onclick = () => mostrar('editor', { modo: 'editar' });
    c.querySelector('#euAmigos').onclick = () => mostrar('moradores', { aba: 'amigos' });
    c.querySelector('#euCasa').onclick = () => mostrar('casa', { n: MORADORES[id - 1].casa });
    c.querySelector('#euSair').onclick = async () => { await Api.rpc('sair', { p_token: token() }); sairConta(); fecharPainel(); toast('Você saiu.'); };
  },
};

function atualizarBotaoSeguir() {
  const b = document.getElementById('btnSeguir');
  if (b && telaAtual && telaAtual.tela === 'ficha') b.textContent = seguindo === telaAtual.args.id ? '⏸ Parar de seguir' : '📍 Seguir na vila';
}
function atualizarFicha() {
  if (!telaAtual || telaAtual.tela !== 'ficha') return;
  const id = telaAtual.args.id, m = MORADORES[id - 1], e = estado(m, simMs()), t = br(simMs());
  const ag = document.getElementById('fichaAgora'); if (!ag) return;
  const L = LUGAR[e.onde] || LUGAR[e.destino] || { ico: '🚶' };
  const oque = e.faz;
  const onde = e.onde === 'passeio_rua' ? ' · rua ' + CASAS[m.casa - 1].rua
    : (e.onde === 'andando' || e.onde === 'casa' || LUGAR[e.onde].em === e.faz) ? '' : ' · ' + LUGAR[e.onde].em;
  ag.innerHTML = `<span class="ico">${e.onde === 'andando' ? '🚶' : L.ico}</span><span>Agora: <b>${esc(oque)}</b>${esc(onde)}<br><span style="opacity:.75;font-size:13px">${e.onde === 'andando' ? 'chega' : 'até'} ${fmt(e.ate)}</span></span>`;
  const bl = blocosDoDia(m, t.dia, t.sem);
  const dias = ['domingo', 'segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado'];
  document.getElementById('fichaDia').textContent = dias[t.sem];
  document.getElementById('fichaAgenda').innerHTML = bl.map((b, i) => {
    const cls = (e.onde !== 'andando' && i === e.bloco) ? 'atual' : b.ate <= t.min ? 'passou' : '';
    return `<li class="${cls}"><span class="hora">${fmt(b.de)}–${fmt(b.ate)}</span><span>${LUGAR[b.onde].ico} ${esc(b.faz)}</span></li>`;
  }).join('');
}
setInterval(() => { atualizarFicha(); }, 2000);

// ---------------------------------------------------------------------
// amigos
// ---------------------------------------------------------------------
const coracoes = n => '❤'.repeat(n) + '♡'.repeat(5 - n);
async function renderAmigos(id) {
  const box = document.getElementById('fichaAmigos'); if (!box) return;
  if (!EU) { box.innerHTML = `<h3>Amigos</h3><div class="dica">🔒 <a href="#" id="lnkAmigos">Entre</a> pra ver os amigos de ${esc(rotulo(id))} e fazer amizade.</div>`;
    box.querySelector('#lnkAmigos').onclick = e => { e.preventDefault(); mostrar('entrar'); }; return; }
  box.innerHTML = `<h3>Amigos</h3><p class="mini">Carregando…</p>`;
  const r = await Api.rpc('amigos_de', { p_morador: id });
  if (!document.getElementById('fichaAmigos') || telaAtual.args.id !== id) return;
  const segue = new Set((r && r.segue) || []), segs = new Set((r && r.seguidores) || []);
  const mutuos = [...segue].filter(x => segs.has(x));
  const eu = EU.morador === id;
  let html = `<h3>Amigos <small>${segue.size} adicionados · ${mutuos.length} mútuos</small></h3>`;
  if (!eu) {
    const euAdd = MEUS.segue.has(id), eleAdd = MEUS.seguidores.has(id) || segue.has(EU.morador);
    const n = nivelAmizade(MORADORES[EU.morador - 1], MORADORES[id - 1]);
    const t = br(simMs()), hoje = encontrosNoDia(MORADORES[EU.morador - 1], MORADORES[id - 1], t.dia, t.sem);
    const nv = clamp(Math.round(n * 5 / 7) + (euAdd && eleAdd ? 1 : 0), 0, 5);
    html += `<div class="dica" style="margin-top:0">
      ${euAdd && eleAdd ? '★ <b>Vocês são amigos!</b>' : euAdd ? 'Você adicionou. Quando adicionar de volta, vira amizade ★' : eleAdd ? `<b>${esc(rotulo(id))} te adicionou!</b> Adiciona de volta?` : 'Vocês ainda não são amigos.'}
      <div style="margin-top:6px"><span class="amigo-coracoes">${coracoes(nv)}</span> <span class="mini">se cruzaram em ${n} dos últimos 7 dias</span></div></div>
      ${hoje.map(x => `<div class="encontro">🤝 Hoje às <b>${fmt(x.de)}</b> vocês estão juntos ${LUGAR[x.onde].em}</div>`).join('')}
      <div class="botoes">${euAdd ? `<button class="btn btn-flex" id="btnAmigo">Remover amizade</button>` : `<button class="btn btn-p btn-larga" id="btnAmigo">❤ Adicionar amigo</button>`}</div>`;
  }
  const lista = [...segue];
  html += lista.length ? `<ul class="lista" style="margin-top:8px">${lista.slice(0, 30).map(x => itemLista(x, segs.has(x) ? '★' : '')).join('')}</ul>`
                       : `<p class="mini" style="margin-top:8px">${eu ? 'Você ainda não adicionou ninguém.' : esc(rotulo(id)) + ' ainda não adicionou ninguém.'}</p>`;
  box.innerHTML = html;
  ligarLista(box, irPara);
  const b = box.querySelector('#btnAmigo');
  if (b) b.onclick = async () => {
    b.disabled = true;
    const add = !MEUS.segue.has(id);
    const res = await Api.rpc(add ? 'adicionar_amigo' : 'remover_amigo', { p_token: token(), p_amigo: id });
    if (!res || !res.ok) { b.disabled = false; return toast((res && res.erro) || 'Não deu certo'); }
    if (add) { MEUS.segue.add(id); toast(res.mutuo ? `★ Agora vocês são amigos!` : `❤ Você adicionou ${rotulo(id)}`); }
    else { MEUS.segue.delete(id); toast('Amizade removida'); }
    renderAmigos(id);
  };
}
async function carregarMeusAmigos() {
  if (!EU) { MEUS = { segue: new Set(), seguidores: new Set() }; return; }
  const r = await Api.rpc('amigos_de', { p_morador: EU.morador });
  MEUS = { segue: new Set((r && r.segue) || []), seguidores: new Set((r && r.seguidores) || []) };
  atualizarBadge();
}

// ---------------------------------------------------------------------
// pedidos de amizade = quem me adicionou e eu ainda não adicionei de volta
// ---------------------------------------------------------------------
const pedidos = () => [...MEUS.seguidores].filter(x => !MEUS.segue.has(x));
function atualizarBadge() {
  const b = document.querySelector('#menu [data-aba="eu"]'); if (!b) return;
  let el = b.querySelector('.badge'); const n = EU ? pedidos().length : 0;
  if (!n) { if (el) el.remove(); return; }
  if (!el) { el = document.createElement('i'); el.className = 'badge'; b.appendChild(el); }
  el.textContent = n > 9 ? '9+' : n;
}
let pedidosAvisados = false;
function avisarPedidos() {
  const n = pedidos().length;
  if (n && !pedidosAvisados) { pedidosAvisados = true; toast(`❤ Você tem ${n} ${n === 1 ? 'pedido' : 'pedidos'} de amizade — veja em "Eu"`); }
}
function itemPedido(id) {
  return `<li class="pedido"><button class="pedido-quem" data-id="${id}"><canvas width="12" height="15" data-look="${id}"></canvas>
    <span class="l-txt"><span class="l-nome">${esc(rotulo(id))}</span><span class="l-sub">quer ser seu amigo</span></span></button>
    <span class="pedido-acoes"><button class="btn btn-v" data-aceitar="${id}">Aceitar</button>${TEM_BIO ? `<button class="btn" data-recusar="${id}">Recusar</button>` : ''}</span></li>`;
}
function ligarPedidos(raiz) {
  raiz.querySelectorAll('[data-aceitar]').forEach(b => b.onclick = async () => {
    const id = Number(b.dataset.aceitar); b.disabled = true;
    const r = await Api.rpc('adicionar_amigo', { p_token: token(), p_amigo: id });
    if (!r || !r.ok) { b.disabled = false; return toast((r && r.erro) || 'Não deu certo'); }
    MEUS.segue.add(id); atualizarBadge(); toast(`★ Agora você e ${rotulo(id)} são amigos!`); TELAS.eu();
  });
  raiz.querySelectorAll('[data-recusar]').forEach(b => b.onclick = async () => {
    const id = Number(b.dataset.recusar); b.disabled = true;
    const r = await Api.rpc('recusar_amizade', { p_token: token(), p_de: id });
    if (!r || !r.ok) { b.disabled = false; return toast((r && r.erro) || 'Não deu certo'); }
    MEUS.seguidores.delete(id); atualizarBadge(); toast('Pedido recusado'); TELAS.eu();
  });
}

// ---------------------------------------------------------------------
// bio automática (1 frase) a partir da rotina — pra quem não escreveu a sua
// ---------------------------------------------------------------------
function bioAuto(m) {
  const r = rng(m.id * 7477 + 3), ag = m.agenda;
  const acorda = ag[0].ate, dorme = ag[ag.length - 1].de, rua = CASAS[m.casa - 1].rua;
  const fora = {};
  for (const b of ag) if (b.onde !== 'casa') fora[b.onde] = (fora[b.onde] || 0) + toMin(b.ate) - toMin(b.de);
  const fav = Object.keys(fora).sort((a, b) => fora[b] - fora[a])[0];
  const FAV = { praca: 'a praça', mercadinho: 'o mercadinho', vendinha: 'a vendinha', passeio_rua: 'passear pela rua ' + rua };
  const opcoes = [
    `Acorda às ${acorda} e já sai pensando no almoço.`,
    `Lugar favorito da vila: ${FAV[fav] || 'a praça'}.`,
    `Dorme às ${dorme} em ponto, nem um minuto depois.`,
    `Mora na casa ${m.casa} e conhece todo mundo da rua ${rua}.`,
    `Chegou no episódio ${m.chegou_no_ep} e nunca mais quis sair.`,
  ];
  if (m.domingo) opcoes.push(`Nunca perde a missa de domingo às ${m.domingo.de}.`);
  if (toMin(acorda) < 400) opcoes.push('Primeiro a acordar na casa, antes do sol nascer.');
  if (toMin(dorme) > 1380) opcoes.push('Última luz acesa da rua toda noite.');
  return opcoes[Math.floor(r() * opcoes.length)];
}

// casas prontas + casas em obra. Ex.: com 577 inscritos, os moradores 571–577 já existem,
// mas a casa 58 só fica pronta com 580 — eles "moram" no lote da obra até lá.
function montarCasas() {
  const lista = VILA.lista_casas.map(c => ({ ...c, pronta: true }));
  const maior = Math.max(...MORADORES.map(m => m.casa));
  for (let n = lista.length + 1; n <= maior; n++) {
    const ids = MORADORES.filter(m => m.casa === n).map(m => m.id);
    const l = (VILA.lotes_livres || []).find(x => x.casa === n);
    if (l && RY[l.rua] != null) {
      const [x, y] = l.lote;
      lista.push({ casa: n, lote: l.lote, tamanho: [42, 50], porta: [x + 20, y + 44], rua: l.rua,
                   ponto_na_rua: [x + 20, RY[l.rua]], moradores: ids, pronta: false, pronta_em: l.pronta_em });
    } else {
      // sem lote ainda (mapa lotado): ficam hospedados na última casa pronta
      const ult = lista[VILA.lista_casas.length - 1];
      lista.push({ ...ult, casa: n, moradores: ids, pronta: false, hospedado: true });
    }
  }
  return lista;
}
const nomeCasa = n => { const c = CASAS[n - 1]; return c && !c.pronta ? `Casa ${n} (em obra)` : `Casa ${n}`; };

// ---------------------------------------------------------------------
// sessão
// ---------------------------------------------------------------------
const token = () => { try { return localStorage.getItem('vila_token'); } catch { return null; } };
function entrou(r) {
  try { localStorage.setItem('vila_token', r.token); } catch {}
  EU = { morador: r.morador, nome: r.nome, usuario: r.usuario, aparencia: r.aparencia || null, bio: r.bio || null };
  atualizarHud(); carregarMeusAmigos(); atualizarPresenca(); atualizarChatUI();
}
function sairConta() {
  try { localStorage.removeItem('vila_token'); } catch {}
  if (INTERIOR) sairInterior(); if (ctrl.ativo) pararControle();
  EU = null; MEUS = { segue: new Set(), seguidores: new Set() }; atualizarHud(); atualizarBadge(); atualizarPresenca(); atualizarChatUI();
}
async function compartilhar(id) {
  const url = location.origin + location.pathname + '?m=' + id;
  const txt = `${rotulo(id)} mora na Cidade dos Seguidores!`;
  try { if (navigator.share) return await navigator.share({ title: 'A Cidade dos Seguidores', text: txt, url }); } catch { return; }
  try { await navigator.clipboard.writeText(url); toast('🔗 Link copiado!'); } catch { prompt('Copie o link:', url); }
}

// ---------------------------------------------------------------------
// início
// ---------------------------------------------------------------------
async function atualizarContador() {
  const c = await Api.contador();
  if (!c || !Number.isFinite(c.seguidores)) return;
  const antes = AO_VIVO;
  AO_VIVO = c.seguidores;
  atualizarHud();
  if (antes != null && AO_VIVO > antes) {
    const b = $('#hudVivo'); b.classList.remove('subiu'); void b.offsetWidth; b.classList.add('subiu');
    const n = AO_VIVO - antes; toast(`🎉 +${n} ${n === 1 ? 'novo seguidor' : 'novos seguidores'}! A vila tá crescendo`);
  }
}
const carregarImg = src => new Promise((ok, erro) => { const i = new Image(); i.onload = () => ok(i); i.onerror = erro; i.src = src; });
async function carregarPublicos() {
  try {
    const l = await Api.publicos();
    const novo = {}; for (const p of l) novo[p.id] = p; PUB = novo;
    TEM_BIO = l.length > 0 && 'bio' in l[0];
  } catch (e) { console.warn(e); toast('Não consegui carregar os nomes (banco fora do ar?)'); }
}
async function iniciar() {
  ajustarTela();
  const [v, m, dia, noite, atlas] = await Promise.all([
    fetch('dados/vila.json').then(r => r.json()), fetch('dados/moradores.json').then(r => r.json()),
    carregarImg('img/vila_dia.png'), carregarImg('img/vila_noite.png'), carregarImg('img/moradores.png')]);
  VILA = v; MORADORES = m; IMG.dia = dia; IMG.noite = noite; IMG.atlas = atlas;
  IMG.atlasNoite = tingir(atlas, atlas.width, atlas.height);
  if (VILA.iso && VILA.iso.imagem) { try { IMG.iso = await carregarImg(VILA.iso.imagem); } catch (e) { console.warn('sem imagem isométrica', e); } }
  atualizarBotaoVista();
  for (const k of Object.keys(VILA.ruas)) if (k !== 'principal') RY[k] = VILA.ruas[k].de[1];
  CASAS = montarCasas();
  montarObstaculos();
  await Promise.all([carregarPublicos(), atualizarContador()]);
  setInterval(() => { if (!document.hidden) atualizarContador(); }, 60000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) atualizarContador(); });
  if (token()) {
    const r = await Api.rpc('meu_perfil', { p_token: token() });
    if (r && r.ok) { EU = { morador: r.morador, nome: r.nome, usuario: r.usuario, aparencia: r.aparencia || null, bio: r.bio || null }; await carregarMeusAmigos(); avisarPedidos(); }
    else if (r && r.erro === 'Entre de novo') sairConta();
  }
  atualizarHud();
  cam.s = PC() ? 2.2 : 2;
  const q = Number(new URLSearchParams(location.search).get('m'));
  estados = MORADORES.map(mm => estado(mm, simMs()));
  { const p = proj(264, 490); cam.x = p.x; cam.y = p.y; limitarCam(); }   // começa na praça
  if (q >= 1 && q <= MORADORES.length) { const e = estados[q - 1], p = proj(e.x, e.y); cam.x = p.x; cam.y = p.y; seguir(q); mostrar('ficha', { id: q }); }
  $('#carregando').classList.add('some');
  setTimeout(() => { $('#carregando').hidden = true; }, 450);
  requestAnimationFrame(loop);
  iniciarTempoReal();
  setInterval(async () => { await carregarPublicos(); atualizarHud(); if (EU) await carregarMeusAmigos(); }, 90000);
  // gancho de teste (só no servidor local com ?debug)
  if (Api.modo === 'local' && new URLSearchParams(location.search).has('debug')) window.__vila = { ctrl, entrarInterior, iniciarControle, chatReceber, get EU() { return EU; }, get INTERIOR() { return INTERIOR; } };
  if (Api.modo === 'local') console.info('Vila em modo LOCAL (servidor_local.js). Configure site/config.js pra usar o Supabase.');
}
addEventListener('resize', ajustarTela);
addEventListener('beforeunload', e => { if (sujo()) { e.preventDefault(); e.returnValue = ''; } });
iniciar().catch(e => { console.error(e); $('#carregando').innerHTML = '<div class="carregando-caixa">Não consegui abrir a vila 😢<br><small>' + esc(e.message) + '</small></div>'; });
})();
