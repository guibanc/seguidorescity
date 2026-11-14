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
let AO_VIVO = null;              // seguidores agora (tabela "contador" no Supabase)

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
  const c = VILA.lista_casas[m.casa - 1], P = VILA.pontos;
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
  const ca = VILA.lista_casas[a.casa - 1].rua, cb = VILA.lista_casas[b.casa - 1].rua, out = [];
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
function minS() { return Math.min(W / 540, H / 960) * 0.92; }
function ajustarTela() {
  DPR = Math.min(devicePixelRatio || 1, 2); W = innerWidth; H = innerHeight;
  cv.width = Math.round(W * DPR); cv.height = Math.round(H * DPR);
  cam.s = clamp(cam.s, minS(), 6); limitarCam();
}
function limitarCam() {
  // não deixa sobrar muito fundo fora do mapa (margem de ~120 px de tela)
  const m = 120 / cam.s, hx = W / 2 / cam.s, hy = H / 2 / cam.s;
  cam.x = 540 + 2 * m > 2 * hx ? clamp(cam.x, hx - m, 540 - hx + m) : 270;
  cam.y = 960 + 2 * m > 2 * hy ? clamp(cam.y, hy - m, 960 - hy + m) : 480;
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

let ultimoNoite = 0, encontrosAvisados = new Set();
function desenhar(agoraReal) {
  const ms = simMs(), t = br(ms), nf = noiteFator(t.min), noite = nf > 0.5;
  estados = MORADORES.map(m => estado(m, ms));
  // câmera segue
  if (seguindo) {
    const e = estados[seguindo - 1], f = focoTela();
    const alvoX = e.x - (f.x - W / 2) / cam.s, alvoY = e.y - (f.y - H / 2) / cam.s;
    cam.x += (alvoX - cam.x) * 0.12; cam.y += (alvoY - cam.y) * 0.12; limitarCam();
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = nf > 0.5 ? '#1d2b2a' : '#3f7a34'; ctx.fillRect(0, 0, cv.width, cv.height);
  const k = DPR * cam.s, tx = Math.round(DPR * (W / 2 - cam.x * cam.s)), ty = Math.round(DPR * (H / 2 - cam.y * cam.s));
  ctx.setTransform(k, 0, 0, k, tx, ty);
  ctx.imageSmoothingEnabled = false;
  if (nf < 1) ctx.drawImage(IMG.dia, 0, 0);
  if (nf > 0) { ctx.globalAlpha = nf; ctx.drawImage(IMG.noite, 0, 0); ctx.globalAlpha = 1; }

  // quem aparece: seguido, eu, amigos, registrados, depois sorteio fixo — máx. MAX_BONECOS
  const v0 = telaPraMapa(0, 0), v1 = telaPraMapa(W, H);
  const prio = id => id === seguindo || id === selecionado ? 0 : (EU && id === EU.morador) ? 1 : amigoMeu(id) ? 2 : ocupado(id) ? 3 : 4;
  desenhados = estados.filter(e => e.vis && e.x > v0.x - 16 && e.x < v1.x + 16 && e.y > v0.y - 24 && e.y < v1.y + 24)
    .sort((a, b) => prio(a.id) - prio(b.id) || hashId(a.id) - hashId(b.id)).slice(0, MAX_BONECOS)
    .sort((a, b) => a.y - b.y);

  const quadro = Math.floor(agoraReal / 125) % 4;
  for (const e of desenhados) {
    const x = Math.round(e.x), y = Math.round(e.y);
    if (e.id === selecionado || e.id === seguindo) {
      ctx.strokeStyle = '#f6c836'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.ellipse(x, y + 3, 7, 3, 0, 0, Math.PI * 2); ctx.stroke();
    }
    const f = fonteSprite(e.id, noite), fr = e.anda ? (quadro + e.id) % 4 : 0;
    ctx.drawImage(f.img, f.ox + fr * 12, f.oy + DIRI[e.dir || 'down'] * 18, 12, 18, x - 6, y - 14, 12, 18);
  }

  // textos em escala de tela
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  const alvo = selecionado || seguindo;
  if (cam.s >= 2) {
    ctx.font = '700 11px Nunito, system-ui, sans-serif';
    for (const e of desenhados) {
      if (e.id === alvo || !ocupado(e.id) || !nomeDe(e.id)) continue;
      const p = mapaPraTela(e.x, e.y - 16), n = nomeDe(e.id), w = ctx.measureText(n).width + 10;
      const meu = EU && e.id === EU.morador, am = amigoMeu(e.id);
      ctx.fillStyle = meu ? 'rgba(246,200,54,.95)' : am ? 'rgba(255,214,222,.95)' : 'rgba(30,24,36,.72)';
      pilula(p.x - w / 2, p.y - 8, w, 15, 7); ctx.fill();
      ctx.fillStyle = meu || am ? '#1e1824' : '#fff8e7'; ctx.fillText(n, p.x, p.y);
    }
  }
  // corações: meu morador perto de um amigo
  if (EU && MEUS.segue.size) {
    const eu = estados[EU.morador - 1];
    if (eu.vis) for (const id of MEUS.segue) {
      const o = estados[id - 1];
      if (!o || !o.vis || Math.hypot(o.x - eu.x, o.y - eu.y) > 28) continue;
      const pulso = 1 + Math.sin(agoraReal / 180) * 0.12;
      for (const q of [eu, o]) coracao(mapaPraTela(q.x, q.y - 22 - (alvo === q.id ? 10 : 0)), 7 * pulso);
      const chave = id + ':' + t.dia + ':' + o.onde;
      if (!encontrosAvisados.has(chave)) { encontrosAvisados.add(chave); toast(`❤ ${rotulo(EU.morador)} encontrou ${rotulo(id)} ${LUGAR[o.onde] ? LUGAR[o.onde].em : 'na rua'}!`); }
    }
  }
  // plaquinha vermelha do morador seguido/selecionado (igual ao vídeo)
  if (alvo) {
    const e = estados[alvo - 1];
    const p = mapaPraTela(e.x, e.y - (e.vis ? 17 : 4));
    let txt = rotulo(alvo);
    if (!e.vis) txt += ' · ' + (LUGAR[e.onde] ? LUGAR[e.onde].em.replace('em casa', 'em casa') : 'dentro');
    ctx.font = '700 13px "Pixelify Sans", Nunito, sans-serif';
    const w = ctx.measureText(txt).width + 16, y = p.y - 16 - Math.abs(Math.sin(agoraReal / 300)) * 3;
    ctx.fillStyle = '#1e1824'; pilula(p.x - w / 2 - 2, y - 13, w + 4, 26 + 2, 7); ctx.fill();
    ctx.fillStyle = '#d63838'; pilula(p.x - w / 2, y - 11, w, 22, 6); ctx.fill();
    ctx.beginPath(); ctx.moveTo(p.x - 6, y + 10); ctx.lineTo(p.x + 6, y + 10); ctx.lineTo(p.x, y + 17); ctx.closePath();
    ctx.fillStyle = '#d63838'; ctx.fill(); ctx.strokeStyle = '#1e1824'; ctx.lineWidth = 2; ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.fillText(txt, p.x, y);
  }
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
  ultimoQuadro = now;
  desenhar(now);
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
  const m = telaPraMapa(sx, sy), tol = Math.max(7, 16 / cam.s);
  let melhor = null, md = 1e9;
  for (const e of desenhados) {
    const cx = e.x, cy = e.y - 6, d = Math.hypot((m.x - cx) / tol, (m.y - cy) / Math.max(11, 20 / cam.s));
    if (d < 1 && d < md) { md = d; melhor = e; }
  }
  if (melhor) return escolherNoMapa(melhor.id);
  const casa = VILA.lista_casas.find(c => m.x >= c.lote[0] && m.x <= c.lote[0] + c.tamanho[0] && m.y >= c.lote[1] && m.y <= c.lote[1] + c.tamanho[1]);
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
// topo: relógio e números
// ---------------------------------------------------------------------
function atualizarRelogio(t, nf) {
  $('#hudHora').textContent = fmt(t.min);
  $('#hudIcone').textContent = nf >= 1 ? '🌙' : nf > 0 ? '🌅' : '☀️';
  const v = relogio.vel;
  $('#hudVel').textContent = v === 1 ? '' : v > 1.5 ? 'x' + Math.round(v) : 'outro horário';
}
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
    $('#hudMarcoTxt').textContent = `🎉 Desbloqueou: ${liberado.construcao}! Chega no próximo episódio ›`;
    $('#hudMarcoBarra').style.width = '100%';
  } else if (pm) {
    const falta = Math.max(0, pm.seguidores - seg), ant = Math.max(...(VILA.marcos || [{ seguidores: 0 }]).map(m => m.seguidores).filter(s => s <= seg), 0);
    $('#hudMarcoTxt').textContent = `faltam ${falta} pra ${pm.construcao} ›`;
    $('#hudMarcoBarra').style.width = clamp(100 * (seg - ant) / Math.max(1, pm.seguidores - ant), 3, 100) + '%';
  } else $('#hudMarco').hidden = true;
  $('#menuEuTxt').textContent = EU ? 'Eu' : 'Entrar';
  $('#menuRegTxt').textContent = EU ? 'Meu boneco' : 'Registrar';
  $('#zoomMeu').hidden = !EU;
}
$('#hudMarco').onclick = () => mostrar('regras', {}, false);
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
const ed = { orig: null, look: null, nome: '', nomeOrig: '', dir: 'down', modo: 'editar', salvoAgora: false };
const sujo = () => telaAtual && telaAtual.tela === 'editor' && ed.modo === 'editar' &&
  (JSON.stringify(ed.look) !== JSON.stringify(ed.orig) || ed.nome.trim() !== ed.nomeOrig);

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
    const abas = [['rua', 'Na rua agora'], ['nome', 'Com nome'], ['livres', 'Livres']];
    if (EU) abas.push(['amigos', 'Meus amigos']);
    const c = corpo(`<div class="abas">${abas.map(([k, t]) => `<button data-a="${k}" class="${k === aba ? 'ativo' : ''}">${t}</button>`).join('')}</div><div id="conteudoAba"></div>`);
    c.querySelectorAll('.abas button').forEach(b => b.onclick = () => { telaAtual.args = { aba: b.dataset.a }; TELAS.moradores(telaAtual.args); });
    const cont = c.querySelector('#conteudoAba');
    let ids = [], topo = '';
    if (aba === 'rua') {
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
    cont.innerHTML = topo + `<ul class="lista">${ids.slice(0, 80).map(id => itemLista(id, aba === 'amigos' && MEUS.seguidores.has(id) ? '★ mútuo' : (aba !== 'livres' && !ocupado(id) ? '' : ''))).join('')}</ul>`
      + (mais ? `<p class="mini" style="text-align:center;margin-top:8px">Mostrando 80 de ${ids.length}. Use a busca pra achar alguém.</p>` : '')
      + (!ids.length && aba !== 'amigos' ? `<p class="vazio">${aba === 'nome' ? 'Ninguém registrou ainda.' : 'Todo mundo está em casa agora.'}</p>` : '');
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
            <span class="etq">#${id}</span><span class="etq">Casa ${m.casa}</span><span class="etq">Chegou no ep. ${m.chegou_no_ep}</span>
            ${eu ? '<span class="etq etq-eu">Você</span>' : !p.ocupado ? '<span class="etq etq-livre">Livre</span>' : ''}
          </div>
        </div>
      </div>
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
    const vizinhos = VILA.lista_casas[m.casa - 1].moradores.filter(x => x !== id);
    const lc = c.querySelector('#fichaCasa'); lc.innerHTML = vizinhos.map(v => itemLista(v)).join(''); ligarLista(lc, irPara);
    renderAmigos(id);
  },

  // ------------------------------------------------ casa
  casa({ n }) {
    const casa = VILA.lista_casas[n - 1];
    titulo(`Casa ${n}`);
    const dentro = casa.moradores.filter(id => estados[id - 1] && estados[id - 1].onde === 'casa').length;
    const c = corpo(`<p class="mini">Rua ${casa.rua} · ${dentro} de ${casa.moradores.length} em casa agora${escolhendo ? ' · toque num livre pra escolher' : ''}.</p>
      <ul class="lista">${casa.moradores.map(id => itemLista(id, ocupado(id) ? '' : '<span class="etq etq-livre">livre</span>')).join('')}</ul>`);
    ligarLista(c, id => {
      if (escolhendo) return escolherNoMapa(id);
      irPara(id);
    });
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
      ${modo === 'editar' ? `<label class="campo"><span>Nome que aparece no boneco</span><input id="edNome" maxlength="20" value="${esc(ed.nome)}"></label>` : ''}
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
      const inp = c.querySelector('#edNome');
      inp.oninput = () => {
        ed.nome = inp.value; ed.salvoAgora = false;
        const s = sujo();
        c.querySelector('#btnSalvar').disabled = !s; c.querySelector('#btnDescartar').disabled = !s;
        const lado = c.querySelector('.palco-lado'), tag = lado.querySelector('.nao-salvo, .salvo-ok');
        if (tag) tag.remove();
        if (s) lado.insertAdjacentHTML('beforeend', '<span class="nao-salvo">● Alterações não salvas</span>');
      };
      c.querySelector('#btnDescartar').onclick = () => { ed.nome = ed.nomeOrig; mudar(ed.orig); };
      c.querySelector('#btnSalvar').onclick = async ev => {
        ev.target.disabled = true; ev.target.textContent = 'Salvando…';
        const r = await Api.rpc('salvar_perfil', { p_token: token(), p_nome: ed.nome.trim(), p_aparencia: ed.look });
        if (!r || !r.ok) {
          c.querySelector('#edErro').innerHTML = `<div class="erro">${esc((r && r.erro) || 'Não deu pra salvar')}</div>`;
          if (r && r.erro === 'Entre de novo') sairConta();
          ev.target.disabled = false; ev.target.textContent = '💾 Salvar'; return;
        }
        EU.nome = ed.nome.trim(); EU.aparencia = { ...ed.look };
        PUB[EU.morador] = { ...(PUB[EU.morador] || {}), id: EU.morador, nome: EU.nome, aparencia: EU.aparencia, ocupado: true, usuario: EU.usuario };
        ed.orig = { ...ed.look }; ed.nomeOrig = EU.nome; ed.salvoAgora = true;
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
    const pend = [...MEUS.seguidores].filter(x => !MEUS.segue.has(x));
    const c = corpo(`<ul class="lista">${itemLista(id, '<span class="etq etq-eu">você</span>')}</ul>
      <div class="etiquetas" style="margin-top:4px"><span class="etq">❤ ${MEUS.segue.size} amigos</span><span class="etq">★ ${mut} mútuos</span></div>
      ${pend.length ? `<div class="secao"><h3>Te adicionaram <small>adicione de volta!</small></h3><ul class="lista" id="euPend">${pend.map(x => itemLista(x, '<span class="etq etq-livre">novo</span>')).join('')}</ul></div>` : ''}
      <div class="botoes">
        <button class="btn btn-flex" id="euVer">📍 Ver na vila</button>
        <button class="btn btn-flex" id="euLink">🔗 Meu link</button>
        <button class="btn btn-a btn-larga" id="euEditar">🎨 Personalizar visual e nome</button>
        <button class="btn btn-flex" id="euAmigos">❤ Meus amigos</button>
        <button class="btn btn-flex" id="euSair">Sair</button>
      </div>`);
    ligarLista(c, irPara);
    c.querySelector('#euVer').onclick = () => irPara(id);
    c.querySelector('#euLink').onclick = () => compartilhar(id);
    c.querySelector('#euEditar').onclick = () => mostrar('editor', { modo: 'editar' });
    c.querySelector('#euAmigos').onclick = () => mostrar('moradores', { aba: 'amigos' });
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
  const onde = e.onde === 'passeio_rua' ? ' · rua ' + VILA.lista_casas[m.casa - 1].rua
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
}

// ---------------------------------------------------------------------
// sessão
// ---------------------------------------------------------------------
const token = () => { try { return localStorage.getItem('vila_token'); } catch { return null; } };
function entrou(r) {
  try { localStorage.setItem('vila_token', r.token); } catch {}
  EU = { morador: r.morador, nome: r.nome, usuario: r.usuario, aparencia: r.aparencia || null };
  atualizarHud(); carregarMeusAmigos();
}
function sairConta() {
  try { localStorage.removeItem('vila_token'); } catch {}
  EU = null; MEUS = { segue: new Set(), seguidores: new Set() }; atualizarHud();
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
  } catch (e) { console.warn(e); toast('Não consegui carregar os nomes (banco fora do ar?)'); }
}
async function iniciar() {
  ajustarTela();
  const [v, m, dia, noite, atlas] = await Promise.all([
    fetch('dados/vila.json').then(r => r.json()), fetch('dados/moradores.json').then(r => r.json()),
    carregarImg('img/vila_dia.png'), carregarImg('img/vila_noite.png'), carregarImg('img/moradores.png')]);
  VILA = v; MORADORES = m; IMG.dia = dia; IMG.noite = noite; IMG.atlas = atlas;
  IMG.atlasNoite = tingir(atlas, atlas.width, atlas.height);
  for (const k of ['A', 'B', 'C']) RY[k] = VILA.ruas[k].de[1];
  await Promise.all([carregarPublicos(), atualizarContador()]);
  setInterval(() => { if (!document.hidden) atualizarContador(); }, 60000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) atualizarContador(); });
  if (token()) {
    const r = await Api.rpc('meu_perfil', { p_token: token() });
    if (r && r.ok) { EU = { morador: r.morador, nome: r.nome, usuario: r.usuario, aparencia: r.aparencia || null }; await carregarMeusAmigos(); }
    else if (r && r.erro === 'Entre de novo') sairConta();
  }
  atualizarHud();
  cam.s = PC() ? 2.2 : 2;
  const q = Number(new URLSearchParams(location.search).get('m'));
  estados = MORADORES.map(mm => estado(mm, simMs()));
  if (q >= 1 && q <= MORADORES.length) { const e = estados[q - 1]; cam.x = e.x; cam.y = e.y; seguir(q); mostrar('ficha', { id: q }); }
  $('#carregando').classList.add('some');
  setTimeout(() => { $('#carregando').hidden = true; }, 450);
  requestAnimationFrame(loop);
  setInterval(async () => { await carregarPublicos(); atualizarHud(); }, 90000);
  if (Api.modo === 'local') console.info('Vila em modo LOCAL (servidor_local.js). Configure site/config.js pra usar o Supabase.');
}
addEventListener('resize', ajustarTela);
addEventListener('beforeunload', e => { if (sujo()) { e.preventDefault(); e.returnValue = ''; } });
iniciar().catch(e => { console.error(e); $('#carregando').innerHTML = '<div class="carregando-caixa">Não consegui abrir a vila 😢<br><small>' + esc(e.message) + '</small></div>'; });
})();
