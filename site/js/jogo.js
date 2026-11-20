// =====================================================================
//  MODO JOGO — explorar (floresta com biomas), minas em camadas,
//  inventário com armadura, crafting, lojas, rank e ranking.
//  O banco (supabase/8_jogo.sql) confere tudo que dá item ou dinheiro;
//  aqui é o desenho, o controle e os bichos.
// =====================================================================
// DESLIGADO por enquanto: o site virou mais "de ver". Sem portal (Explorar
// e mina), sem Terrenos e Lotes, sem mochila e sem lojas. Pra religar,
// troque JOGO_LIGADO pra true.
const JOGO_LIGADO = false;
(function () {
'use strict';
const V = window.VilaAPI;
if (!V || !JOGO_LIGADO) return;
const $ = s => document.querySelector(s);
const esc = V.esc, clamp = V.clamp;
const PORTAL_CIDADE = [60, 943];            // ao lado da cidade (coordenadas do mapa de cima)
const ARCO_LOTES = [42, 943];               // entrada dos Terrenos e Lotes na cidade
const TW = 32, TH = 16, CH = 16;            // losango do chão e tamanho do pedaço de chão em cache
const MINA_N = 25, MINA_ESCADA = 12, MINA_CAMADAS = 12;
const ALCANCE = 1.7;                        // até onde alcança pra quebrar/atacar (em blocos)
const VEL = 3.4;                            // blocos por segundo
// Terrenos e Lotes: lotes de 16x16, 8 por fileira, ruas de 4 entre eles, praça em cima
const LT = 16, LT_PASSO = 20, LT_COLS = 8, LT_X0 = 4, LT_Y0 = 10;
const LT_PORTAL = [78, 4], LT_FEIRA = [86, 4], LT_SPAWN = [82, 6];
const som = n => window.Sons && Sons.tocar(n);

// ---------------------------------------------------------------------
// estado
// ---------------------------------------------------------------------
let CAT = null, ITENS = {}, RECEITAS = [], RANKS = [], QUEB = {};
let JOG = { moedas: 0, rank: 0, inv: new Array(40).fill(null) };
let SEL = 0;                                // slot da barra selecionado
let modo = null;                            // null | 'explorar' | 'mina' | 'lotes'
let CHAO = null;                            // chão do lugar atual ({w, h, chao})
let LOTES = [], MEU_LOTE = null, LBLOCOS = new Map(), MUNDO_L = null, mouseTela = null;
let MUNDO = null, OBJ = new Map(), OBJ_TILE = new Map(), QUEBRADOS = new Set();
let MINA = { z: 0, cam: {}, gerada: null, proxima: null };
let voltaCidade = null, acao = null, pendente = false, alvoTocado = null;
let ents = [], idEnt = 1, textos = [], ultimoGolpe = 0, ultimoDano = 0, ultimaPollTela = 0;
let cachePedacos = new Map(), spritesObj = new Map(), folhasMob = new Map(), vestidos = new Map();
let retangulos = [];                        // o que foi desenhado (pra tocar)
const ctx = V.ctx;

const iso = (x, y) => ({ X: (x - y) * 16, Y: (x + y) * 8 });
const daIso = (X, Y) => ({ x: (X / 16 + Y / 8) / 2, y: (Y / 8 - X / 16) / 2 });
const hash = (x, y, s = 0) => { let h = Math.imul(x, 374761393) + Math.imul(y, 668265263) + Math.imul(s, 2147483647); h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
const tkn = () => V.token();
const rpc = (fn, p) => window.Api.rpc(fn, p);
const nomeItem = id => (ITENS[id] && ITENS[id].nome) || id;
const fmtM = n => Number(n || 0).toLocaleString('pt-BR');
function flutua(x, y, texto, cor) { textos.push({ x, y, texto, cor: cor || '#fff8e7', t: performance.now() }); }

// ---------------------------------------------------------------------
// catálogo, inventário, dinheiro
// ---------------------------------------------------------------------
async function carregarCatalogo() {
  if (CAT) return CAT;
  const c = await rpc('jogo_catalogo', {});
  if (!c || !c.itens) throw new Error('o banco do jogo ainda não foi instalado (8_jogo.sql)');
  CAT = c; ITENS = {}; for (const i of c.itens) ITENS[i.id] = i;
  RECEITAS = c.receitas; RANKS = c.ranks; QUEB = c.quebraveis;
  return CAT;
}
async function carregarJogo() {
  if (!V.EU) return;
  const r = await rpc('meu_jogo', { p_token: tkn() });
  if (!r || !r.ok) return;
  JOG.moedas = r.moedas; JOG.rank = r.rank; JOG.inv = new Array(40).fill(null);
  for (const s of r.inv) JOG.inv[s.s] = { i: s.i, q: s.q, d: s.d };
  atualizarHUD(); desenharBarra();
  if (modalAberto) renderModal();
}
const itemNaMao = () => JOG.inv[SEL];
const rankAtual = () => RANKS[JOG.rank] || { nome: 'Morador', camada_max: 3, bonus_venda: 0, cor: '#aaa' };
function defesaTotal() { let d = 0; for (let s = 36; s <= 39; s++) if (JOG.inv[s]) d += (ITENS[JOG.inv[s].i] || {}).defesa || 0; return d; }
function armadura() {                       // material de cada peça (pra desenhar no boneco)
  const m = id => id ? id.split('_').pop() : null;
  return [36, 37, 38, 39].map(s => m(JOG.inv[s] && JOG.inv[s].i));
}

// ---------------------------------------------------------------------
// ÍCONES dos itens (pixel art 16x16 desenhada aqui)
// ---------------------------------------------------------------------
const MAT = { madeira: ['#b07a44', '#7a4e26'], pedra: ['#a8a8ae', '#6e6e76'], ferro: ['#e2e6ec', '#9aa1ab'], cristal: ['#7cf0f4', '#2aa9b5'],
              couro: ['#9a6236', '#5e3a1e'], ouro: ['#f6d04a', '#b9871c'] };
const cacheIcone = new Map();
function icone(id) {
  if (cacheIcone.has(id)) return cacheIcone.get(id);
  const c = document.createElement('canvas'); c.width = 16; c.height = 16; const g = c.getContext('2d');
  const P = (x, y, w, h, cor) => { g.fillStyle = cor; g.fillRect(x, y, w, h); };
  const it = ITENS[id] || {}, partes = id.split('_'), mat = MAT[partes[partes.length - 1]] || MAT.madeira;
  const cabo = () => { for (let i = 0; i < 9; i++) P(3 + i, 12 - i, 2, 2, i % 3 === 0 ? '#6b4423' : '#8a5a2b'); };
  if (it.ferramenta === 'picareta') {            // cabeça em arco, atravessada no cabo
    cabo();
    for (let i = 0; i <= 10; i++) { const x = 4 + i, y = 1 + i - Math.round(2.6 * Math.sin(Math.PI * i / 10)); P(x, y, 2, 2, i < 2 || i > 8 ? mat[1] : mat[0]); }
  } else if (it.ferramenta === 'machado') {      // lâmina larga de um lado só
    cabo(); P(8, 1, 3, 7, mat[1]); P(11, 0, 3, 9, mat[0]); P(14, 1, 1, 7, mat[0]); P(13, 1, 2, 1, '#ffffff55');
  }
  else if (it.ferramenta === 'espada') { for (let i = 0; i < 8; i++) P(6 + i, 9 - i, 2, 2, i % 2 ? mat[1] : mat[0]); P(3, 10, 6, 2, '#5e3a1e'); P(4, 12, 2, 3, '#7a4e26'); P(13, 1, 2, 2, mat[0]); }
  else if (it.tipo === 'bloco') {               // construção: o próprio bloco/móvel em miniatura
    const sp = it.forma === 'objeto' ? spriteMovel(id) : { c: cuboBloco(id, it.forma) };
    const w = sp.c.width, h = sp.c.height, k = Math.min(15 / w, 15 / h);
    g.imageSmoothingEnabled = false; g.drawImage(sp.c, Math.round((16 - w * k) / 2), Math.round((16 - h * k) / 2), Math.round(w * k), Math.round(h * k));
  }
  else if (it.tipo === 'armadura') {
    const [a, b] = mat;
    if (it.slot_armadura === 'cabeca') { P(3, 4, 10, 6, a); P(3, 9, 3, 3, a); P(10, 9, 3, 3, a); P(4, 5, 8, 1, b); P(5, 3, 6, 1, a); }
    else if (it.slot_armadura === 'peito') { P(2, 3, 12, 4, a); P(4, 6, 8, 8, a); P(6, 3, 4, 2, '#00000000'); g.clearRect(6, 3, 4, 2); P(4, 13, 8, 1, b); P(7, 6, 2, 6, b); }
    else if (it.slot_armadura === 'pernas') { P(3, 2, 10, 4, a); P(3, 5, 4, 9, a); P(9, 5, 4, 9, a); P(3, 2, 10, 1, b); P(6, 6, 1, 8, b); }
    else { P(2, 8, 5, 6, a); P(9, 8, 5, 6, a); P(2, 12, 6, 2, b); P(9, 12, 6, 2, b); }
  } else {
    const desenhos = {
      madeira: () => { P(3, 4, 10, 9, '#8a5a2b'); P(3, 4, 10, 2, '#c8955a'); P(5, 5, 6, 1, '#a87444'); P(3, 9, 10, 1, '#6b4423'); },
      tabua: () => { P(2, 5, 12, 3, '#c8955a'); P(2, 9, 12, 3, '#b07a44'); P(2, 7, 12, 1, '#7a4e26'); P(2, 11, 12, 1, '#7a4e26'); },
      graveto: () => { for (let i = 0; i < 10; i++) P(3 + i, 12 - i, 2, 1, '#8a5a2b'); },
      fibra: () => { for (let i = 0; i < 4; i++) P(4 + i * 2, 4 + (i % 2), 1, 9, i % 2 ? '#7bbf4c' : '#5c9e3a'); },
      pedra: () => { P(3, 5, 10, 7, '#9a9aa2'); P(4, 4, 7, 2, '#b8b8c0'); P(5, 9, 6, 2, '#76767e'); },
      terra: () => { P(3, 5, 10, 7, '#8a5a32'); P(4, 4, 7, 2, '#a8733f'); P(6, 8, 2, 2, '#5e3a1e'); },
      areia: () => { P(3, 6, 10, 6, '#e6cf8a'); P(5, 5, 6, 2, '#f2dfa6'); },
      carvao: () => { P(3, 5, 10, 7, '#2a2a30'); P(5, 4, 5, 2, '#44444c'); P(7, 7, 2, 1, '#55555e'); },
      ferro: () => { P(2, 7, 12, 5, '#d6dbe1'); P(4, 5, 8, 3, '#eef1f4'); P(2, 11, 12, 1, '#9aa1ab'); },
      ouro: () => { P(2, 7, 12, 5, '#f2c43a'); P(4, 5, 8, 3, '#ffe28a'); P(2, 11, 12, 1, '#b9871c'); },
      cristal: () => { P(6, 2, 4, 2, '#bff8fa'); P(4, 4, 8, 6, '#6ee6ee'); P(6, 10, 4, 3, '#2aa9b5'); P(5, 5, 2, 3, '#e8feff'); },
      rubi: () => { P(6, 3, 4, 2, '#ff9aa8'); P(4, 5, 8, 5, '#e3263f'); P(6, 10, 4, 3, '#9c1028'); P(5, 6, 2, 2, '#ffd0d6'); },
      couro: () => { P(3, 4, 10, 9, '#9a6236'); P(2, 6, 1, 5, '#9a6236'); P(13, 5, 1, 6, '#9a6236'); P(5, 6, 4, 1, '#b97a46'); },
      la: () => { P(3, 5, 10, 7, '#f2efe6'); P(4, 4, 3, 2, '#ffffff'); P(9, 4, 3, 2, '#ffffff'); P(4, 10, 8, 2, '#d8d4c8'); },
      pena: () => { for (let i = 0; i < 9; i++) P(4 + i, 12 - i, 3, 1, i < 2 ? '#c8c0b0' : '#f4f1ea'); },
      cacto: () => { P(6, 2, 4, 12, '#3f9a4a'); P(3, 6, 3, 2, '#3f9a4a'); P(10, 5, 3, 2, '#3f9a4a'); P(7, 3, 1, 10, '#62bf6a'); },
      gosma: () => { P(3, 6, 10, 7, '#5fd86a'); P(5, 4, 6, 3, '#7fe88a'); P(5, 8, 2, 2, '#1e1824'); P(9, 8, 2, 2, '#1e1824'); },
      osso: () => { P(5, 7, 6, 2, '#efe9da'); P(3, 6, 3, 2, '#efe9da'); P(3, 8, 3, 2, '#efe9da'); P(10, 6, 3, 2, '#efe9da'); P(10, 8, 3, 2, '#efe9da'); },
      maca: () => { P(4, 5, 8, 8, '#d8333a'); P(5, 4, 6, 1, '#d8333a'); P(5, 6, 2, 2, '#f58a8a'); P(8, 2, 1, 3, '#6b4423'); P(9, 2, 2, 1, '#4f9a3a'); },
      frutinha: () => { for (const [x, y] of [[4, 6], [8, 5], [6, 9], [10, 9]]) { P(x, y, 3, 3, '#7a3fb8'); P(x, y, 1, 1, '#c7a0ec'); } },
      carne_crua: () => { P(3, 5, 9, 7, '#e2727a'); P(4, 6, 6, 4, '#f29aa0'); P(11, 8, 3, 2, '#efe9da'); },
      carne_assada: () => { P(3, 5, 9, 7, '#9a5a2a'); P(4, 6, 6, 4, '#b97a3e'); P(11, 8, 3, 2, '#efe9da'); },
      frango_cru: () => { P(5, 4, 7, 7, '#f0b0a4'); P(4, 10, 3, 3, '#efe9da'); P(3, 12, 2, 2, '#efe9da'); },
      frango_assado: () => { P(5, 4, 7, 7, '#c9853f'); P(4, 10, 3, 3, '#efe9da'); P(3, 12, 2, 2, '#efe9da'); },
      carne_podre: () => { P(3, 5, 9, 7, '#7a8a4a'); P(5, 7, 3, 2, '#556a2e'); P(11, 8, 3, 2, '#c8c2a8'); },
      pao: () => { P(2, 6, 12, 6, '#d39a4e'); P(3, 5, 10, 2, '#e8b86a'); P(4, 7, 1, 3, '#a8733f'); P(8, 7, 1, 3, '#a8733f'); },
      suco: () => { P(5, 3, 6, 11, '#e6eef4'); P(6, 6, 4, 7, '#f08a3a'); P(9, 1, 1, 4, '#d8333a'); },
    };
    const minerio = { minerio_ferro: '#e0a070', minerio_ouro: '#f6d04a' };
    if (minerio[id]) { P(3, 5, 10, 7, '#8a8a92'); P(4, 4, 7, 2, '#a8a8b0'); for (const [x, y] of [[5, 6], [9, 7], [6, 9], [10, 10]]) P(x, y, 2, 2, minerio[id]); }
    else (desenhos[id] || (() => P(4, 4, 8, 8, '#c9a')))();
  }
  // contorno
  const d = g.getImageData(0, 0, 16, 16), a = i => d.data[i * 4 + 3], add = [];
  for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) { const i = y * 16 + x; if (a(i)) continue; if ((x > 0 && a(i - 1)) || (x < 15 && a(i + 1)) || (y > 0 && a(i - 16)) || (y < 15 && a(i + 16))) add.push(i); }
  for (const i of add) { d.data[i * 4] = 30; d.data[i * 4 + 1] = 24; d.data[i * 4 + 2] = 36; d.data[i * 4 + 3] = 255; }
  g.putImageData(d, 0, 0);
  const url = c.toDataURL(); cacheIcone.set(id, url); return url;
}
const imgIcone = id => `<img class="ic" src="${icone(id)}" alt="">`;

// ---------------------------------------------------------------------
// ARMADURA no boneco 32 bits (pinta a peça por cima, com a luz original)
// ---------------------------------------------------------------------
const COR_ARM = { couro: [154, 98, 54], ferro: [206, 212, 220], cristal: [96, 222, 232], ouro: [240, 196, 70] };
function vestir(folha, arm) {
  if (!arm || !arm.some(Boolean)) return folha;
  const k = folha.__id || (folha.__id = Math.random().toString(36).slice(2));
  const chave = k + arm.join(','); if (vestidos.has(chave)) return vestidos.get(chave);
  const c = document.createElement('canvas'); c.width = 128; c.height = 192; const g = c.getContext('2d'); g.drawImage(folha, 0, 0);
  const d = g.getImageData(0, 0, 128, 192), px = d.data;
  const DIRS = ['down', 'left', 'right', 'up'];
  const pinta = (ox, oy, x0, x1, y0, y1, cor, espelho) => {
    for (let y = Math.max(0, y0); y <= Math.min(47, y1); y++) for (let xx = x0; xx <= x1; xx++) {
      const x = espelho ? 31 - xx : xx; if (x < 0 || x > 31) continue;
      const i = ((oy + y) * 128 + ox + x) * 4; if (px[i + 3] < 255) continue;
      if (px[i] === 34 && px[i + 1] === 28 && px[i + 2] === 40) continue;            // contorno fica
      const l = (px[i] * 0.3 + px[i + 1] * 0.59 + px[i + 2] * 0.11) / 255, f = 0.55 + 0.7 * l;
      px[i] = clamp(cor[0] * f, 0, 255); px[i + 1] = clamp(cor[1] * f, 0, 255); px[i + 2] = clamp(cor[2] * f, 0, 255);
    }
  };
  DIRS.forEach((dir, di) => {
    for (let fr = 0; fr < 4; fr++) {
      const ox = fr * 32, oy = di * 48, y0 = (fr === 1 || fr === 3) ? 1 : 0, lado = dir === 'left' || dir === 'right', esp = dir === 'left';
      const hy0 = 2 + y0, ty0 = 17 + y0, ty1 = 31 + y0, tx0 = lado ? 12 : 10, tx1 = lado ? 20 : 21;
      if (arm[0] && COR_ARM[arm[0]]) pinta(ox, oy, 6, 25, hy0 - 4, hy0 + (dir === 'up' ? 8 : 3), COR_ARM[arm[0]], esp);
      if (arm[1] && COR_ARM[arm[1]]) { pinta(ox, oy, tx0, tx1, ty0, ty1 - 3, COR_ARM[arm[1]], esp); pinta(ox, oy, tx0 - 4, tx1 + 4, ty0, ty0 + 5, COR_ARM[arm[1]], esp); }
      if (arm[2] && COR_ARM[arm[2]]) pinta(ox, oy, 9, 23, 30 + y0, 39 + y0, COR_ARM[arm[2]], esp);
      if (arm[3] && COR_ARM[arm[3]]) pinta(ox, oy, 7, 25, 40 + y0, 47, COR_ARM[arm[3]], esp);
    }
  });
  g.putImageData(d, 0, 0);
  if (vestidos.size > 60) vestidos.delete(vestidos.keys().next().value);
  vestidos.set(chave, c); return c;
}
function folhaJogador(m, arm, noite) {
  const f = V.folha32(V.lookDe(m)); if (!f) return null;
  return vestir(noite ? f.noite : f.dia, arm);
}

// ---------------------------------------------------------------------
// CHÃO do explorar: pedaços de 16x16 blocos desenhados uma vez (cache)
// ---------------------------------------------------------------------
const COR_CHAO = { g: [98, 176, 78], f: [66, 138, 60], t: [104, 152, 118], a: [226, 206, 140], p: [138, 138, 146], w: [56, 116, 196], c: [176, 136, 92],
                   r: [170, 164, 156], l: [110, 184, 88], b: [92, 160, 72] };          // r = rua dos lotes, l = lote, b = borda do lote
const chaoEm = (x, y) => (!CHAO || x < 0 || y < 0 || x >= CHAO.w || y >= CHAO.h) ? 'w' : CHAO.chao[y * CHAO.w + x];
function losango(g, X, Y, cor) {                      // losango 32x16 em pixels inteiros
  g.fillStyle = cor;
  for (let r = 0; r < 16; r++) { const hw = r < 8 ? (r + 1) * 2 : (16 - r) * 2; g.fillRect(X + 16 - hw, Y + r, hw * 2, 1); }
}
const rgb = (c, f = 1) => `rgb(${clamp(c[0] * f, 0, 255) | 0},${clamp(c[1] * f, 0, 255) | 0},${clamp(c[2] * f, 0, 255) | 0})`;
function pedaco(cx, cy) {
  const k = cx + ',' + cy; let p = cachePedacos.get(k);
  if (p) return p;
  const x0 = cx * CH, y0 = cy * CH;
  const minX = (x0 - (y0 + CH - 1)) * 16 - 16, minY = (x0 + y0) * 8 - 8;
  const c = document.createElement('canvas'); c.width = CH * 32 + 32; c.height = CH * 16 + 24; const g = c.getContext('2d');
  for (let s = 0; s < CH * 2 - 1; s++) for (let x = x0; x < x0 + CH; x++) {
    const y = y0 + s - (x - x0); if (y < y0 || y >= y0 + CH) continue;
    const t = chaoEm(x, y), base = COR_CHAO[t] || COR_CHAO.g, { X, Y } = iso(x, y), px = X - 16 - minX, py = Y - 8 - minY;
    const h = hash(x, y, 7);
    losango(g, px, py, rgb(base, 0.94 + h * 0.12));
    // textura
    for (let j = 0; j < 7; j++) {
      const r1 = hash(x, y, 20 + j), r2 = hash(x, y, 40 + j), rr = Math.floor(r2 * 15), hw = rr < 8 ? (rr + 1) * 2 : (16 - rr) * 2;
      const xx = px + 16 - hw + Math.floor(r1 * hw * 2), yy = py + rr;
      g.fillStyle = t === 'w' ? rgb([150, 200, 240]) : t === 'a' ? rgb(base, 0.85) : t === 't' && j < 2 ? '#f4f8fa' : rgb(base, j % 2 ? 0.82 : 1.12);
      g.fillRect(xx, yy, t === 'w' ? 3 : 1, 1);
    }
    if (t === 'g' && h < 0.08) { g.fillStyle = h < 0.04 ? '#f6e05a' : '#f08ab0'; g.fillRect(px + 14, py + 6, 2, 2); }
    // barranco onde a terra encontra a água
    if (t !== 'w') {
      const lado = (dx, dy, x1, x2, f) => { if (chaoEm(x + dx, y + dy) !== 'w') return;
        g.fillStyle = rgb(t === 'a' || t === 'c' ? [180, 150, 100] : [120, 86, 52], f);
        for (let xx = x1; xx < x2; xx++) { const yy = xx < 16 ? 8 + xx / 2 : 16 - (xx - 16) / 2; g.fillRect(px + xx, py + Math.floor(yy), 1, 5); } };
      lado(0, 1, 0, 16, 0.85); lado(1, 0, 16, 32, 0.65);
    }
  }
  p = { c, minX, minY }; cachePedacos.set(k, p);
  if (cachePedacos.size > 40) cachePedacos.delete(cachePedacos.keys().next().value);
  return p;
}

// ---------------------------------------------------------------------
// SPRITES de objetos (árvores, pedras...) e bichos — pixel art feita aqui
// ---------------------------------------------------------------------
function tela(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')]; }
function contorno(c) {
  const g = c.getContext('2d'), w = c.width, h = c.height, d = g.getImageData(0, 0, w, h), a = i => d.data[i * 4 + 3] > 0, add = [];
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const i = y * w + x; if (a(i)) continue; if ((x > 0 && a(i - 1)) || (x < w - 1 && a(i + 1)) || (y > 0 && a(i - w)) || (y < h - 1 && a(i + w))) add.push(i); }
  for (const i of add) { d.data[i * 4] = 30; d.data[i * 4 + 1] = 24; d.data[i * 4 + 2] = 36; d.data[i * 4 + 3] = 255; }
  g.putImageData(d, 0, 0); return c;
}
function disco(g, cx, cy, rx, ry, cores, seed) {          // bola com luz de cima/esquerda
  for (let y = -ry; y <= ry; y++) for (let x = -rx; x <= rx; x++) {
    const d = (x * x) / (rx * rx) + (y * y) / (ry * ry); if (d > 1) continue;
    const luz = (-x / rx - y / ry) * 0.5 + (hash(cx + x, cy + y, seed) - 0.5) * 0.5;
    g.fillStyle = cores[luz > 0.35 ? 3 : luz > 0.05 ? 2 : luz > -0.3 ? 1 : 0]; g.fillRect(cx + x, cy + y, 1, 1);
  }
}
function spriteObj(tipo, v) {
  const k = tipo + v; if (spritesObj.has(k)) return spritesObj.get(k);
  let c, g, ax, ay;
  const VERDE = ['#2c6b34', '#3f8a40', '#5aa84c', '#86c96a'], PINHO = ['#1f4f3a', '#2c6a4a', '#3f8a5c', '#6db08a'];
  if (tipo === 'carvalho') {
    [c, g] = tela(44, 60); g.fillStyle = '#6b4423'; g.fillRect(19, 34, 6, 22); g.fillStyle = '#8a5a2b'; g.fillRect(19, 34, 2, 22);
    disco(g, 22, 22, 16, 14, VERDE, v); disco(g, 12, 28, 9, 8, VERDE, v + 1); disco(g, 32, 28, 9, 8, VERDE, v + 2);
    if (v === 1) for (const [x, y] of [[14, 20], [28, 16], [24, 30]]) { g.fillStyle = '#d8333a'; g.fillRect(x, y, 3, 3); }
    ax = 22; ay = 56;
  } else if (tipo === 'pinheiro') {
    [c, g] = tela(36, 66); g.fillStyle = '#6b4423'; g.fillRect(16, 50, 5, 12);
    for (let i = 0; i < 4; i++) { const y0 = 4 + i * 12, w = 7 + i * 4; for (let r = 0; r < 16; r++) { const hw = Math.min(w, Math.floor(r * w / 12)); for (let x = -hw; x <= hw; x++) { g.fillStyle = PINHO[x < -hw / 3 ? 3 : x < hw / 3 ? 2 : 1]; g.fillRect(18 + x, y0 + r, 1, 1); } } }
    if (v !== 2) { g.fillStyle = '#f4f8fa'; g.fillRect(17, 4, 3, 2); g.fillRect(12, 18, 3, 1); g.fillRect(22, 30, 4, 1); }
    ax = 18; ay = 62;
  } else if (tipo === 'palmeira') {
    [c, g] = tela(40, 58); for (let i = 0; i < 26; i++) { g.fillStyle = i % 4 < 2 ? '#a8733f' : '#8a5a2b'; g.fillRect(19 + Math.round(Math.sin(i / 8) * 3), 28 + i, 4, 1); }
    for (const [dx, dy] of [[-1, 0.2], [1, 0.2], [-0.7, -0.6], [0.7, -0.6], [0, -1]]) for (let i = 0; i < 16; i++) { g.fillStyle = i % 3 ? '#3f9a4a' : '#5ab85a'; g.fillRect(21 + Math.round(dx * i), 26 + Math.round(dy * i + (i * i) / 30), 3, 2); }
    g.fillStyle = '#7a4e26'; g.fillRect(19, 26, 3, 3); g.fillRect(23, 27, 3, 3);
    ax = 21; ay = 54;
  } else if (tipo === 'arbusto') {
    [c, g] = tela(28, 22); disco(g, 14, 12, 11, 8, VERDE, v + 5);
    for (const [x, y] of [[8, 9], [16, 7], [19, 13], [11, 14]]) { g.fillStyle = v === 2 ? '#e8e8f0' : '#7a3fb8'; g.fillRect(x, y, 2, 2); }
    ax = 14; ay = 19;
  } else if (tipo === 'capim') {
    [c, g] = tela(18, 14); for (let i = 0; i < 6; i++) { const x = 3 + i * 2, h = 6 + ((i * 7 + v) % 5); g.fillStyle = i % 2 ? '#5aa84c' : '#86c96a'; g.fillRect(x, 13 - h, 1, h); }
    ax = 9; ay = 12;
  } else if (tipo === 'cacto') {
    [c, g] = tela(22, 34); g.fillStyle = '#2f8a3e'; g.fillRect(8, 4, 6, 28); g.fillRect(3, 12, 4, 3); g.fillRect(3, 8, 3, 6); g.fillRect(15, 15, 4, 3); g.fillRect(16, 10, 3, 7);
    g.fillStyle = '#4fb05a'; g.fillRect(9, 5, 2, 26); g.fillStyle = '#e8f0c0'; for (let y = 6; y < 30; y += 5) g.fillRect(13, y, 1, 1);
    ax = 11; ay = 31;
  } else {                                               // rochas
    [c, g] = tela(30, 22); disco(g, 15, 13, 13, 8, ['#5e5e66', '#7e7e88', '#9e9ea8', '#c4c4cc'], v + 9);
    const pinta = { rocha_carvao: '#18181c', rocha_ferro: '#e0a070' }[tipo];
    if (pinta) for (const [x, y] of [[8, 10], [14, 8], [19, 13], [11, 15], [21, 9]]) { g.fillStyle = pinta; g.fillRect(x, y, 3, 2); }
    ax = 15; ay = 19;
  }
  contorno(c); const s = { c, ax, ay }; spritesObj.set(k, s); return s;
}
// bichos (2 quadros de andar) e o portal
function spriteBicho(tipo, fr) {
  const k = tipo + fr; if (spritesObj.has(k)) return spritesObj.get(k);
  let c, g, ax, ay; const pe = fr ? 1 : 0;
  if (tipo === 'galinha') {
    [c, g] = tela(16, 16); g.fillStyle = '#f4f1ea'; g.fillRect(3, 5, 9, 6); g.fillRect(9, 2, 4, 5); g.fillStyle = '#d8d2c4'; g.fillRect(3, 8, 6, 3);
    g.fillStyle = '#d8333a'; g.fillRect(10, 1, 2, 2); g.fillStyle = '#f2a83a'; g.fillRect(13, 4, 2, 1); g.fillStyle = '#1e1824'; g.fillRect(11, 3, 1, 1);
    g.fillStyle = '#f2a83a'; g.fillRect(6 - pe, 11, 1, 3); g.fillRect(9 + pe, 11, 1, 3); ax = 8; ay = 14;
  } else if (tipo === 'vaca') {
    [c, g] = tela(34, 24); g.fillStyle = '#f4f1ea'; g.fillRect(4, 6, 22, 11); g.fillRect(25, 4, 7, 8);
    g.fillStyle = '#2a2420'; g.fillRect(8, 7, 6, 5); g.fillRect(18, 11, 5, 4); g.fillRect(25, 4, 3, 3);
    g.fillStyle = '#f0a8a8'; g.fillRect(29, 9, 3, 3); g.fillStyle = '#1e1824'; g.fillRect(28, 6, 1, 1);
    g.fillStyle = '#d8d2c4'; for (const x of [6, 10, 19, 23]) g.fillRect(x + ((x % 2) ? pe : -pe), 17, 2, 5); ax = 17; ay = 22;
  } else if (tipo === 'ovelha') {
    [c, g] = tela(30, 22); disco(g, 13, 10, 11, 7, ['#cfc9bc', '#e2ddd2', '#f2efe6', '#ffffff'], 3); g.fillStyle = '#3a3430'; g.fillRect(22, 6, 6, 6);
    g.fillStyle = '#1e1824'; g.fillRect(25, 8, 1, 1); g.fillStyle = '#3a3430'; for (const x of [6, 10, 15, 19]) g.fillRect(x + ((x % 2) ? pe : -pe), 16, 2, 5); ax = 14; ay = 20;
  } else if (tipo === 'gosma') {
    const h = fr ? 9 : 12, w = fr ? 20 : 16; [c, g] = tela(22, 16);
    for (let y = 0; y < h; y++) { const hw = Math.round(w / 2 * Math.sqrt(1 - Math.pow((y - h) / h, 2))); g.fillStyle = y < 3 ? '#9ff0a6' : '#5fd86a'; g.fillRect(11 - hw, 15 - h + y, hw * 2, 1); }
    g.fillStyle = '#1e1824'; g.fillRect(8, 15 - h + 4, 2, 2); g.fillRect(13, 15 - h + 4, 2, 2); ax = 11; ay = 15;
  }
  contorno(c); const s = { c, ax, ay }; spritesObj.set(k, s); return s;
}
// zumbi e esqueleto: moradores 32 bits com a pele trocada
function folhaMob(tipo) {
  if (folhasMob.has(tipo)) return folhasMob.get(tipo);
  const look = tipo === 'zumbi'
    ? { pele: 1, cabelo: 'raspado', cor_cabelo: 0, camisa: 1, estampa: 'regata', camisa2: 1, baixo: 'calca', cor_baixo: 0, sapato: 0, oculos: false, chapeu: null, cor_chapeu: 0, barba: false }
    : { pele: 0, cabelo: 'careca', cor_cabelo: 6, camisa: 9, estampa: 'regata', camisa2: 9, baixo: 'bermuda', cor_baixo: 2, sapato: 0, oculos: false, chapeu: null, cor_chapeu: 0, barba: false };
  const px = Char32.folha(Sprites.normalizar(look));
  const pele = Sprites.SKIN16[look.pele];
  for (let i = 0; i < px.length; i += 4) {
    if (px[i + 3] < 255) continue;
    const r = px[i], g = px[i + 1], b = px[i + 2], parece = Math.abs(r / pele[0] - g / pele[1]) < 0.12 && Math.abs(r / pele[0] - b / pele[2]) < 0.18 && r > 60;
    if (!parece) continue;
    const f = r / pele[0];
    if (tipo === 'zumbi') { px[i] = 110 * f; px[i + 1] = 170 * f; px[i + 2] = 90 * f; } else { px[i] = 232 * f; px[i + 1] = 228 * f; px[i + 2] = 214 * f; }
  }
  const [c] = tela(128, 192); c.getContext('2d').putImageData(new ImageData(px, 128, 192), 0, 0);
  folhasMob.set(tipo, c); return c;
}

// ---------------------------------------------------------------------
// ENTRAR / SAIR
// ---------------------------------------------------------------------
// ---------------------------------------------------------------------
// BLOCOS DE CONSTRUÇÃO: cubo 32x32 com textura em cada face (cache)
// u, v = posição na face (0..15); face 0 = topo, 1 = lado esquerdo, 2 = lado direito
// ---------------------------------------------------------------------
const TEX = {
  tronco: (u, v, f) => f === 0 ? (((Math.round(Math.hypot(u - 7.5, v - 7.5)) % 3) === 0) ? [150, 108, 62] : [196, 152, 98])
                                : ((u % 4 === 0) ? [84, 54, 30] : (u % 4 === 2 && v % 5 === 1) ? [96, 62, 34] : [118, 78, 42]),
  parede_madeira: (u, v, f) => (v % 4 === 3) ? [132, 90, 52] : ((u + (v >> 2) * 5) % 8 === 0 ? [150, 104, 60] : [198, 150, 96]),
  parede_pedra: (u, v) => { const lin = v % 6 === 5, col = (u + ((v / 6 | 0) % 2) * 4) % 8 === 7; return lin || col ? [104, 104, 112] : [168, 168, 176]; },
  parede_reboco: (u, v, f, h) => h < 0.08 ? [214, 206, 190] : [238, 232, 218],
  tijolo: (u, v) => { const lin = v % 4 === 3, col = (u + ((v >> 2) % 2) * 4) % 8 === 7; return lin || col ? [214, 204, 190] : [180, 78, 54]; },
  vidro: (u, v) => (u === 0 || v === 0 || u === 15 || v === 15) ? [236, 244, 248] : (Math.abs(u - v - 3) < 2 || Math.abs(u - v + 5) < 1) ? [236, 250, 255] : [150, 210, 236],
  telha: (u, v, f) => { const lin = v % 4 === 3, onda = (u + (v >> 2) * 2) % 4 === 0; return lin ? [126, 40, 32] : onda ? [168, 58, 42] : [204, 82, 58]; },
  piso_madeira: (u, v) => (v % 4 === 3) ? [146, 100, 58] : ((u + (v >> 2) * 7) % 16 === 0 ? [150, 104, 60] : [206, 160, 104]),
  piso_pedra: (u, v) => (u % 8 === 7 || v % 8 === 7) ? [118, 118, 126] : [182, 182, 190],
  tapete: (u, v) => (u < 2 || v < 2 || u > 13 || v > 13) ? [236, 196, 90] : ((u + v) % 6 < 2 ? [150, 40, 60] : [196, 56, 76]),
  canteiro: (u, v, f, h) => h < 0.1 ? [246, 214, 74] : h < 0.2 ? [240, 120, 170] : h < 0.27 ? [250, 250, 250] : (h < 0.6 ? [84, 150, 62] : [110, 74, 44]),
};
const cubosB = new Map();
function cuboBloco(tipo, forma) {
  const k = tipo + forma; if (cubosB.has(k)) return cubosB.get(k);
  const tex = TEX[tipo] || TEX.parede_reboco, piso = forma === 'piso';
  const [c, g] = tela(32, piso ? 18 : 32), d = g.createImageData(32, piso ? 18 : 32), px = d.data;
  const put = (x, y, cor, luz, a = 255) => { const i = (y * 32 + x) * 4; px[i] = clamp(cor[0] * luz, 0, 255); px[i + 1] = clamp(cor[1] * luz, 0, 255); px[i + 2] = clamp(cor[2] * luz, 0, 255); px[i + 3] = a; };
  const alfa = tipo === 'vidro' ? 150 : 255;
  for (let py = 0; py < 16; py++) {                                     // topo (losango)
    const hw = py < 8 ? (py + 1) * 2 : (16 - py) * 2;
    for (let x = 16 - hw; x < 16 + hw; x++) {
      const X = x + 0.5 - 16, Y = py + 0.5, a = (X / 16 + Y / 8) / 2, b = (Y / 8 - X / 16) / 2;
      const u = clamp(Math.floor(a * 16), 0, 15), v = clamp(Math.floor(b * 16), 0, 15), cor = tex(u, v, 0, hash(u, v, 5));
      const borda = (a < 0.04 || b < 0.04) && !piso ? 1.12 : 1;
      put(x, py + (piso ? 1 : 0), cor, borda, (tipo === 'vidro' && u > 0 && v > 0 && u < 15 && v < 15) ? alfa : 255);
    }
  }
  if (piso) {                                                           // piso: só uma beiradinha
    for (let x = 0; x < 32; x++) { const yt = x < 16 ? 8 + Math.floor(x / 2) : 16 - Math.floor((x - 15) / 2); const cor = tex(0, 0, 1, 0); put(x, Math.min(17, yt + 1), cor, x < 16 ? 0.7 : 0.55); }
  } else {
    for (let x = 0; x < 32; x++) {                                      // laterais
      const esq = x < 16, yt = esq ? 8 + x / 2 : 16 - (x - 15.5) / 2;
      for (let v = 0; v < 16; v++) {
        const y = Math.floor(yt + v); if (y < 0 || y > 31) continue;
        const u = esq ? x : x - 16, cor = tex(u, v, esq ? 1 : 2, hash(u, v, esq ? 6 : 7));
        const borda = v === 15 ? 0.8 : 1, vid = tipo === 'vidro' && u > 0 && v > 0 && u < 15 && v < 15;
        put(x, y, cor, (esq ? 0.84 : 0.66) * borda, vid ? alfa : 255);
      }
    }
  }
  g.putImageData(d, 0, 0); cubosB.set(k, c); return c;
}
// móveis e decoração (objeto em cima do bloco; âncora = centro do bloco)
function spriteMovel(tipo) {
  const k = 'm_' + tipo; if (spritesObj.has(k)) return spritesObj.get(k);
  let c, g, ax, ay; const P = (x, y, w, h, cor) => { g.fillStyle = cor; g.fillRect(x, y, w, h); };
  const MAD = '#a8733f', MAD2 = '#7a4e26', MAD3 = '#c8955a';
  if (tipo === 'porta') {
    [c, g] = tela(20, 34); P(1, 0, 18, 34, MAD2); P(3, 2, 14, 32, MAD); P(4, 4, 5, 12, MAD3); P(11, 4, 5, 12, MAD3); P(4, 19, 5, 12, MAD3); P(11, 19, 5, 12, MAD3); P(13, 17, 2, 2, '#f6c836'); ax = 10; ay = 32;
  } else if (tipo === 'cerca') {
    [c, g] = tela(30, 20); for (const x of [2, 13, 24]) { P(x, 2, 4, 18, MAD); P(x, 2, 4, 2, MAD3); } P(0, 6, 30, 3, MAD3); P(0, 13, 30, 3, MAD); ax = 15; ay = 17;
  } else if (tipo === 'mesa') {
    [c, g] = tela(28, 20); P(1, 3, 26, 6, MAD3); P(1, 8, 26, 2, MAD2); P(3, 10, 3, 9, MAD2); P(22, 10, 3, 9, MAD2); P(12, 10, 3, 7, MAD); P(10, 1, 6, 3, '#e8eef2'); ax = 14; ay = 16;
  } else if (tipo === 'cadeira') {
    [c, g] = tela(16, 24); P(3, 0, 10, 12, MAD); P(4, 2, 8, 2, MAD3); P(4, 6, 8, 2, MAD3); P(2, 12, 12, 4, MAD3); P(3, 16, 2, 8, MAD2); P(11, 16, 2, 8, MAD2); ax = 8; ay = 21;
  } else if (tipo === 'cama') {
    [c, g] = tela(30, 22); P(0, 4, 4, 18, MAD2); P(26, 8, 4, 14, MAD2); P(2, 10, 26, 8, MAD); P(3, 6, 10, 6, '#f4f1ea'); P(12, 7, 16, 9, '#3668d6'); P(12, 7, 16, 2, '#5a8ae6'); ax = 15; ay = 18;
  } else if (tipo === 'estante') {
    [c, g] = tela(24, 36); P(0, 0, 24, 36, MAD2); P(2, 2, 20, 32, '#5e3a1e');
    const cores = ['#d63838', '#3668d6', '#40a456', '#f6c836', '#a855f7', '#f4f1ea'];
    for (let s = 0; s < 3; s++) { P(2, 11 + s * 11, 20, 2, MAD); for (let i = 0; i < 6; i++) P(3 + i * 3, 3 + s * 11 + (i % 3), 2, 8 - (i % 3), cores[(i + s * 2) % 6]); }
    ax = 12; ay = 33;
  } else if (tipo === 'lampiao') {
    [c, g] = tela(14, 34); P(6, 10, 3, 24, '#3a3440'); P(3, 32, 9, 2, '#3a3440'); P(3, 2, 9, 9, '#3a3440'); P(4, 3, 7, 7, '#ffe08a'); P(5, 4, 3, 3, '#fff6d0'); P(2, 1, 11, 2, '#2a2430'); ax = 7; ay = 32;
  } else if (tipo === 'vaso_flor') {
    [c, g] = tela(16, 20); P(3, 12, 10, 8, '#c0643a'); P(2, 11, 12, 2, '#d8784a'); P(7, 4, 2, 8, '#3f8a40'); P(4, 6, 3, 2, '#5aa84c'); P(9, 7, 3, 2, '#5aa84c');
    P(5, 1, 6, 4, '#f08ab0'); P(7, 2, 2, 2, '#f6e05a'); ax = 8; ay = 18;
  } else if (tipo === 'arvorezinha') {
    [c, g] = tela(22, 30); P(9, 18, 4, 11, '#6b4423'); disco(g, 11, 11, 9, 9, ['#2c6b34', '#3f8a40', '#5aa84c', '#86c96a'], 11); ax = 11; ay = 28;
  } else if (tipo === 'balcao') {
    [c, g] = tela(30, 34); P(1, 18, 28, 14, MAD); P(1, 18, 28, 3, MAD3); P(3, 23, 24, 7, MAD2);
    for (let i = 0; i < 7; i++) P(1 + i * 4, 4, 4, 5, i % 2 ? '#f4f1ea' : '#d63838'); P(2, 9, 2, 10, MAD2); P(26, 9, 2, 10, MAD2);
    P(11, 12, 8, 5, '#f6c836'); P(13, 13, 4, 3, '#b9871c'); ax = 15; ay = 30;
  } else { [c, g] = tela(16, 16); P(2, 2, 12, 12, '#c9a'); ax = 8; ay = 13; }
  contorno(c); const s = { c, ax, ay }; spritesObj.set(k, s); return s;
}

function exigeLogin() { if (V.EU) return true; V.toast('Entre com seu morador pra jogar!'); V.mostrar('entrar'); return false; }
async function entrarExplorar(ponto) {
  if (!exigeLogin()) return;
  try { await carregarCatalogo(); } catch (e) { return V.toast('⚠️ ' + e.message); }
  if (!MUNDO) {
    V.toast('🌲 Abrindo o portal…');
    MUNDO = await (await fetch('dados/mundo.json')).json();
    OBJ.clear(); OBJ_TILE.clear();
    for (const [id, x, y, tipo] of MUNDO.objs) { const o = { id, x, y, tipo, v: id % 3 }; OBJ.set(id, o); OBJ_TILE.set(x + ',' + y, o); }
  }
  if (!V.ctrl.ativo) V.iniciarControle();
  const deFora = !modo;
  if (deFora) { voltaCidade = PORTAL_CIDADE; som('portal'); } else if (modo === 'mina') som('subir');
  modo = 'explorar'; CHAO = MUNDO; ents = []; acao = null; cachePedacos.clear();
  const p = ponto || [MUNDO.spawn[0] + 0.5, MUNDO.spawn[1] + 0.5];
  V.ctrl.x = p[0]; V.ctrl.y = p[1]; V.ctrl.dir = 'down';
  V.cam.s = V.PC() ? 2.2 : 1.7;
  document.body.classList.add('explorando'); mostrarHUD(true);
  await Promise.all([carregarJogo(), atualizarQuebrados()]);
  V.enviarPos(); if (deFora) V.toast('🌲 Bem-vindo à Floresta! Quebre árvores e pedras, faça ferramentas e venda na cidade.');
}
// ---------------------------------------------------------------------
// TERRENOS E LOTES (lugar separado): monta o chão a partir da lista de lotes
// ---------------------------------------------------------------------
const origemLote = id => { const i = id - 1; return [LT_X0 + (i % LT_COLS) * LT_PASSO, LT_Y0 + Math.floor(i / LT_COLS) * LT_PASSO]; };
function loteEm(x, y) {                                 // qual lote tem esse bloco (e a posição dentro dele)
  const cx = Math.floor((x - LT_X0) / LT_PASSO), cy = Math.floor((y - LT_Y0) / LT_PASSO);
  if (cx < 0 || cy < 0 || cx >= LT_COLS) return null;
  const id = cy * LT_COLS + cx + 1, [ox, oy] = origemLote(id), lx = Math.floor(x) - ox, ly = Math.floor(y) - oy;
  if (lx < 0 || ly < 0 || lx >= LT || ly >= LT || !LOTES[id - 1]) return null;
  return { id, lx, ly, ox, oy };
}
function montarMundoLotes() {
  const linhas = Math.ceil(Math.max(1, LOTES.length) / LT_COLS), w = LT_X0 * 2 + LT_COLS * LT_PASSO - (LT_PASSO - LT), h = LT_Y0 + linhas * LT_PASSO;
  const a = new Array(w * h).fill('r');
  for (const l of LOTES) {
    const [ox, oy] = origemLote(l.id);
    for (let y = 0; y < LT; y++) for (let x = 0; x < LT; x++) a[(oy + y) * w + ox + x] = (x === 0 || y === 0 || x === LT - 1 || y === LT - 1) ? 'b' : 'l';
  }
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (x < 2 || x >= w - 2) a[y * w + x] = 'g';
  MUNDO_L = { w, h, chao: a.join('') };
}
async function carregarLotes() {
  const r = await rpc('lotes_lista', {});
  if (!Array.isArray(r)) return false;
  const mudouQtd = r.length !== LOTES.length;
  LOTES = r; MEU_LOTE = (r.find(l => V.EU && l.dono === V.EU.morador) || {}).id || null;
  if (mudouQtd || !MUNDO_L) { montarMundoLotes(); if (modo === 'lotes') { CHAO = MUNDO_L; cachePedacos.clear(); } }
  return true;
}
let ultimaBusca = 0;
async function carregarBlocosPerto(forcar) {
  const c = V.ctrl, ids = [];
  for (const l of LOTES) { const [ox, oy] = origemLote(l.id); if (Math.hypot(ox + 8 - c.x, oy + 8 - c.y) < 34) ids.push(l.id); }
  if (!ids.length) return;
  ids.sort((a, b) => { const A = origemLote(a), B = origemLote(b); return Math.hypot(A[0] + 8 - c.x, A[1] + 8 - c.y) - Math.hypot(B[0] + 8 - c.x, B[1] + 8 - c.y); });
  const pedir = ids.slice(0, 12), t0 = Date.now(); ultimaBusca = t0;
  const r = await rpc('lote_blocos', { p_lotes: pedir });
  if (!r || typeof r !== 'object' || r.ok === false || (ultimaBusca !== t0 && !forcar)) return;
  for (const id of pedir) {
    const m = new Map(); for (const [x, y, z, t] of (r[id] || [])) m.set(x + ',' + y + ',' + z, t);
    LBLOCOS.set(id, m);
  }
}
async function entrarLotes(ponto) {
  if (!exigeLogin()) return;
  try { await carregarCatalogo(); } catch (e) { return V.toast('⚠️ ' + e.message); }
  if (!(await carregarLotes())) return V.toast('⚠️ Os Terrenos e Lotes ainda não foram instalados no banco (11_terrenos.sql)');
  if (!V.ctrl.ativo) V.iniciarControle();
  if (!modo) { voltaCidade = ARCO_LOTES; som('portal'); }
  modo = 'lotes'; CHAO = MUNDO_L; ents = []; acao = null; cachePedacos.clear();
  const p = ponto || [LT_SPAWN[0] + 0.5, LT_SPAWN[1] + 0.5];
  V.ctrl.x = p[0]; V.ctrl.y = p[1]; V.ctrl.dir = 'down';
  V.cam.s = V.PC() ? 2.2 : 1.7;
  document.body.classList.add('explorando'); mostrarHUD(true);
  await Promise.all([carregarJogo(), carregarBlocosPerto(true)]);
  V.enviarPos();
  V.toast(MEU_LOTE ? `🏡 Terrenos e Lotes! Seu lote é o nº ${MEU_LOTE}.` : '🏡 Terrenos e Lotes! Escolha um lote livre (placa verde) e pegue de graça.');
}
function irProLote(id) {
  const [ox, oy] = origemLote(id); V.ctrl.x = ox + 7.5; V.ctrl.y = oy + LT + 1.5; V.ctrl.dir = 'up';
  carregarBlocosPerto(true); V.enviarPos();
}
async function entrarMina(z = 0) {
  if (!exigeLogin()) return;
  try { await carregarCatalogo(); } catch (e) { return V.toast('⚠️ ' + e.message); }
  if (z > rankAtual().camada_max) return V.toast(`🔒 Seu rank (${rankAtual().nome}) só deixa ir até a camada ${rankAtual().camada_max}`);
  som('descer');
  modo = 'mina'; MINA.z = z; ents = []; acao = null;
  await carregarMina(z);
  V.ctrl.x = MINA_ESCADA + 0.5; V.ctrl.y = MINA_ESCADA + 1.5; V.ctrl.dir = 'down';
  if (celula(z, Math.floor(V.ctrl.x), Math.floor(V.ctrl.y)) !== '.') { V.ctrl.x = MINA_ESCADA + 0.5; V.ctrl.y = MINA_ESCADA + 0.5; }
  V.cam.s = V.PC() ? 2.4 : 1.9;
  mostrarHUD(true); V.enviarPos();
}
function sairParaCidade() {
  if (!modo) return;
  modo = null; acao = null; ents = []; som('portal');
  document.body.classList.remove('explorando');
  const volta = voltaCidade || PORTAL_CIDADE;
  V.ctrl.x = volta[0] + (volta === ARCO_LOTES ? -6 : 14); V.ctrl.y = volta[1] + 6; V.ctrl.dir = 'down';
  V.cam.s = V.PC() ? 1.6 : 1.3;
  V.setSeguindo(V.EU ? V.EU.morador : null);
  mostrarHUD(false); V.enviarPos();
}

// ---------------------------------------------------------------------
// dados do mundo e da mina (o banco é a verdade; aqui só atualiza)
// ---------------------------------------------------------------------
async function atualizarQuebrados() {
  const r = await rpc('explorar_estado', {});
  if (Array.isArray(r)) QUEBRADOS = new Set(r);
}
async function carregarMina(z) {
  const r = await rpc('mina_camadas', { p_z: z });
  if (!r || !r.camadas) return;
  const nova = MINA.gerada && r.gerada_em !== MINA.gerada;
  MINA.cam[z] = r.camadas[String(z)]; MINA.cam[z + 1] = r.camadas[String(z + 1)] || null;
  MINA.gerada = r.gerada_em; MINA.proxima = Date.parse(r.proxima_em);
  if (nova && modo === 'mina') {
    V.toast('⛏️ A mina foi regenerada!'); som('regenera');
    if (celula(MINA.z, Math.floor(V.ctrl.x), Math.floor(V.ctrl.y)) !== '.') { V.ctrl.x = MINA_ESCADA + 0.5; V.ctrl.y = MINA_ESCADA + 0.5; }
  }
}
const celula = (z, x, y) => { if (x < 0 || y < 0 || x >= MINA_N || y >= MINA_N) return 'p'; const s = MINA.cam[z]; return s ? s[y * MINA_N + x] : 'p'; };
const MINA_TIPO = { t: 'b_terra', p: 'b_pedra', c: 'b_carvao', f: 'b_ferro', o: 'b_ouro', k: 'b_cristal', r: 'b_rubi' };
const MINA_COR = { t: [[140, 96, 56], null], p: [[124, 124, 132], null], c: [[124, 124, 132], [24, 24, 28]], f: [[124, 124, 132], [226, 160, 112]],
                   o: [[124, 124, 132], [246, 208, 74]], k: [[110, 116, 130], [110, 232, 238]], r: [[110, 110, 120], [227, 38, 63]] };
const cubos = new Map();
function cubo(ch) {
  if (cubos.has(ch)) return cubos.get(ch);
  const [c, g] = tela(32, 32), [base, pinta] = MINA_COR[ch] || MINA_COR.p;
  losango(g, 0, 0, rgb(base, 1.15));
  for (let xx = 0; xx < 32; xx++) {                          // laterais
    const yy = xx < 16 ? 8 + xx / 2 : 16 - (xx - 16) / 2;
    g.fillStyle = rgb(base, xx < 16 ? 0.82 : 0.62); g.fillRect(xx, Math.floor(yy), 1, 16);
  }
  for (let j = 0; j < 14; j++) {                             // textura e minério
    const x = Math.floor(hash(j, ch.charCodeAt(0), 3) * 28) + 2, y = Math.floor(hash(j, ch.charCodeAt(0), 4) * 26) + 3;
    g.fillStyle = pinta && j % 2 === 0 ? rgb(pinta) : rgb(base, j % 3 ? 0.7 : 1.3); g.fillRect(x, y, pinta && j % 2 === 0 ? 2 : 1, pinta && j % 2 === 0 ? 2 : 1);
  }
  cubos.set(ch, c); return c;
}

// ---------------------------------------------------------------------
// MOVIMENTO e colisão
// ---------------------------------------------------------------------
function bloqueadoJogo(x, y) {
  const tx = Math.floor(x), ty = Math.floor(y);
  if (modo === 'explorar') {
    if (x < 1 || y < 1 || x > MUNDO.w - 1 || y > MUNDO.h - 1) return true;
    if (chaoEm(tx, ty) === 'w') return true;
    const o = OBJ_TILE.get(tx + ',' + ty);
    if (o && !QUEBRADOS.has(o.id) && o.tipo !== 'capim') {
      const dx = x - (tx + 0.5), dy = y - (ty + 0.5); if (dx * dx + dy * dy < 0.16) return true;     // tronco no meio do bloco
    }
    return false;
  }
  if (modo === 'mina') {
    if (celula(MINA.z, tx, ty) !== '.') return true;
    // buraco: só deixa entrar se o rank permite descer
    const furo = !(tx === MINA_ESCADA && ty === MINA_ESCADA) && MINA.cam[MINA.z + 1] && celula(MINA.z + 1, tx, ty) === '.';
    if (furo && MINA.z + 1 > rankAtual().camada_max) return true;
    return false;
  }
  if (modo === 'lotes') {
    if (!CHAO || x < 2 || y < 0.6 || x > CHAO.w - 2 || y > CHAO.h - 0.6) return true;
    const t = blocoEm(tx, ty, 0);
    return !!t && !!ITENS[t] && ITENS[t].solido !== false;
  }
  return false;
}
function blocoEm(wx, wy, z) {                         // tipo do bloco nessa posição do mundo dos lotes (ou undefined)
  const lt = loteEm(wx, wy); if (!lt) return undefined;
  const m = LBLOCOS.get(lt.id); return m && m.get(lt.lx + ',' + lt.ly + ',' + z);
}
function mover(ix, iy, mag, dt) {
  const c = V.ctrl;
  if (mag < 0.15) { if (c.anda) { c.anda = false; V.enviarPos(); } return; }
  if (mag > 1) { ix /= mag; iy /= mag; }
  // na tela: pra cima = pra cima. Converte pro chão isométrico
  const sx = ix, sy = iy, mx = (sx + 2 * sy) / 2, my = (2 * sy - sx) / 2, n = Math.hypot(mx, my) || 1, f = Math.min(1, Math.hypot(sx, sy));
  const vx = mx / n * f, vy = my / n * f, passo = VEL * dt * (V.VIDA <= 20 ? 0.6 : 1);
  const nx = c.x + vx * passo, ny = c.y + vy * passo;
  if (!bloqueadoJogo(nx, c.y)) c.x = nx;
  if (!bloqueadoJogo(c.x, ny)) c.y = ny;
  c.dir = Math.abs(sx) > Math.abs(sy) ? (sx > 0 ? 'right' : 'left') : (sy > 0 ? 'down' : 'up');
  c.vx = vx; c.vy = vy; c.anda = true;
  { const ch = modo === 'mina' ? 'p' : modo === 'lotes' ? (blocoEm(Math.floor(c.x), Math.floor(c.y), -1) ? 'm' : chaoEm(Math.floor(c.x), Math.floor(c.y))) : chaoEm(Math.floor(c.x), Math.floor(c.y));
    som(ch === 'p' || ch === 'r' || ch === 'm' ? 'passo_pedra' : 'passo'); }
  if (acao && acao.dist && distAlvo(acao) > ALCANCE + 0.6) acao = null;     // saiu de perto: para de quebrar
  // caiu num buraco da mina
  if (modo === 'mina') {
    const tx = Math.floor(c.x), ty = Math.floor(c.y);
    if (!(tx === MINA_ESCADA && ty === MINA_ESCADA) && MINA.cam[MINA.z + 1] && celula(MINA.z + 1, tx, ty) === '.' && MINA.z + 1 <= rankAtual().camada_max) descer(false);
  }
  V.enviarPos();
}
async function descer(pelaEscada) {
  if (pendente) return;
  const z = MINA.z + 1;
  if (z >= MINA_CAMADAS) return V.toast('Essa é a camada mais funda');
  if (z > rankAtual().camada_max) { som('erro'); return V.toast(`🔒 Seu rank (${rankAtual().nome}) só deixa ir até a camada ${rankAtual().camada_max}`); }
  pendente = true; som('descer');
  await carregarMina(z); MINA.z = z;
  if (pelaEscada) { V.ctrl.x = MINA_ESCADA + 0.5; V.ctrl.y = MINA_ESCADA + 0.5; }
  flutua(V.ctrl.x, V.ctrl.y, `⬇️ Camada ${z} (−${z * 2} m)`, '#f6c836');
  pendente = false; ents = []; V.enviarPos();
}
async function subir() {
  if (MINA.z === 0) { return entrarExplorar([MUNDO.mina[0] + 0.5, MUNDO.mina[1] + 1.5]); }
  if (pendente) return; pendente = true; som('subir');
  const z = MINA.z - 1; await carregarMina(z); MINA.z = z;
  V.ctrl.x = MINA_ESCADA + 0.5; V.ctrl.y = MINA_ESCADA + 0.5; pendente = false; ents = [];
  flutua(V.ctrl.x, V.ctrl.y, `⬆️ Camada ${z} (−${z * 2} m)`, '#f6c836'); V.enviarPos();
}

// ---------------------------------------------------------------------
// QUEBRAR / ATACAR
// ---------------------------------------------------------------------
function tempoQuebra(q) {
  const it = itemNaMao(), info = it && ITENS[it.i];
  if (q.nivel_min > 0 && (!info || info.ferramenta !== q.ferramenta || info.nivel < q.nivel_min))
    return { erro: `Precisa de ${q.ferramenta} de ${['', 'madeira', 'pedra', 'ferro', 'cristal'][q.nivel_min]} ou melhor` };
  if (info && q.ferramenta && info.ferramenta === q.ferramenta) return { t: q.dureza / (1 + info.nivel * 1.25) };
  return { t: q.dureza * (q.ferramenta ? 1.6 : 1) };
}
function centroAlvo(a) {
  if (a.tipo === 'obj') return [a.o.x + 0.5, a.o.y + 0.5];
  if (a.tipo === 'bloco') return [a.x + 0.5, a.y + 0.5];
  if (a.tipo === 'desmonta') return [a.p.wx + 0.5, a.p.wy + 0.5];
  return [a.e.x, a.e.y];
}
function distAlvo(a) { const [x, y] = centroAlvo(a); return a.chao ? 0 : Math.hypot(x - V.ctrl.x, y - V.ctrl.y); }
// o que está na frente (pro botão de ação / tecla E)
function alvoNaFrente() {
  const c = V.ctrl, fx = c.vx || 0, fy = c.vy || 1, cands = [];
  for (const e of ents) { const d = Math.hypot(e.x - c.x, e.y - c.y); if (d < ALCANCE) cands.push({ tipo: 'mob', e, d }); }
  if (modo === 'explorar') {
    for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
      const o = OBJ_TILE.get((Math.floor(c.x) + dx) + ',' + (Math.floor(c.y) + dy)); if (!o || QUEBRADOS.has(o.id)) continue;
      const d = Math.hypot(o.x + 0.5 - c.x, o.y + 0.5 - c.y); if (d < ALCANCE) cands.push({ tipo: 'obj', o, d });
    }
  } else if (modo === 'mina') {
    for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
      const x = Math.floor(c.x) + dx, y = Math.floor(c.y) + dy; if (celula(MINA.z, x, y) === '.' || x < 0 || y < 0 || x >= MINA_N || y >= MINA_N) continue;
      const d = Math.hypot(x + 0.5 - c.x, y + 0.5 - c.y); if (d < ALCANCE) cands.push({ tipo: 'bloco', z: MINA.z, x, y, d });
    }
  }
  let melhor = null, ms = 1e9;
  for (const k of cands) {
    const [x, y] = centroAlvo(k), dx = x - c.x, dy = y - c.y, n = Math.hypot(dx, dy) || 1;
    const s = k.d - 0.7 * ((dx * fx + dy * fy) / n) - (k.tipo === 'mob' ? 0.8 : 0);
    if (s < ms) { ms = s; melhor = k; }
  }
  return melhor;
}
function comecar(alvo) {
  if (!alvo || pendente) return;
  if (alvo.tipo === 'mob') return golpe(alvo.e);
  if (!alvo.chao && distAlvo(alvo) > ALCANCE + 0.3) return V.toast('Chega mais perto');
  const q = QUEB[alvo.tipo === 'obj' ? alvo.o.tipo : MINA_TIPO[celula(alvo.z, alvo.x, alvo.y)]];
  if (!q) return;
  const tq = tempoQuebra(q); if (tq.erro) { som('erro'); return V.toast('⛏️ ' + tq.erro); }
  if (alvo.tipo === 'bloco' && alvo.z > rankAtual().camada_max) return V.toast(`🔒 Seu rank só deixa cavar até a camada ${rankAtual().camada_max}`);
  acao = { ...alvo, t0: performance.now(), dur: tq.t * 1000, dist: !alvo.chao };
}
async function terminar(a) {
  if (a.tipo === 'desmonta') return desmontarAgora(a.p);
  pendente = true;
  const slot = itemNaMao() ? SEL : -1;
  const r = a.tipo === 'obj' ? await rpc('quebrar_obj', { p_token: tkn(), p_obj: a.o.id, p_slot: slot })
                             : await rpc('minerar', { p_token: tkn(), p_z: a.z, p_x: a.x, p_y: a.y, p_slot: slot });
  pendente = false;
  const [cx, cy] = centroAlvo(a);
  if (r && r.ok) {
    if (a.tipo === 'obj') { QUEBRADOS.add(a.o.id); window.Rt && Rt.pos({ m: V.EU.morador, ev: 'quebra', w: 'x', id: a.o.id }); }
    else { marcarMinerado(a.z, a.x, a.y); window.Rt && Rt.pos({ m: V.EU.morador, ev: 'minera', w: 'm', z: a.z, x: a.x, y: a.y }); }
    som('quebrou'); setTimeout(() => som('pegar'), 140);
    let i = 0; for (const [it, n] of Object.entries(r.ganhou || {})) flutua(cx, cy - i++ * 0.35, `+${n} ${nomeItem(it)}`, '#b6f0a4');
    await carregarJogo();
    if (a.chao) descer(false);
  } else {
    if (r && r.sumiu) { if (a.tipo === 'obj') QUEBRADOS.add(a.o.id); else marcarMinerado(a.z, a.x, a.y); }
    som('erro'); V.toast('⛏️ ' + ((r && r.erro) || 'Não deu certo'));
  }
}
function marcarMinerado(z, x, y) { const s = MINA.cam[z]; if (!s) return; const i = y * MINA_N + x; MINA.cam[z] = s.slice(0, i) + '.' + s.slice(i + 1); }
function golpe(e) {
  const agora = performance.now(); if (agora - ultimoGolpe < 420) return; ultimoGolpe = agora;
  if (Math.hypot(e.x - V.ctrl.x, e.y - V.ctrl.y) > ALCANCE + 0.3) return V.toast('Chega mais perto');
  const it = itemNaMao(), info = it && ITENS[it.i], dano = info ? (info.ferramenta === 'espada' ? info.dano : Math.ceil(info.dano / 2)) : 1;
  e.hp -= dano; e.bate = agora; som('golpe');
  const dx = e.x - V.ctrl.x, dy = e.y - V.ctrl.y, n = Math.hypot(dx, dy) || 1; e.kx = dx / n * 0.5; e.ky = dy / n * 0.5;
  flutua(e.x, e.y - 0.6, '-' + dano, '#ff8080');
  if (e.manso) e.foge = agora + 3000;
  if (e.hp <= 0) morreuBicho(e);
}
async function morreuBicho(e) {
  ents = ents.filter(x => x !== e); som('morre');
  const r = await rpc('abater', { p_token: tkn(), p_tipo: e.tipo });
  if (r && r.ok) { let i = 0; for (const [it, n] of Object.entries(r.ganhou || {})) flutua(e.x, e.y - i++ * 0.35, `+${n} ${nomeItem(it)}`, '#b6f0a4'); carregarJogo(); }
  else if (r && r.erro && !/devagar/.test(r.erro)) V.toast(r.erro);
}

// ---------------------------------------------------------------------
// BICHOS: aparecem perto de você (só na sua tela) e o banco dá o drop
// ---------------------------------------------------------------------
const MOBS = {
  galinha: { hp: 4, vel: 1.2, manso: true }, vaca: { hp: 10, vel: 0.9, manso: true }, ovelha: { hp: 8, vel: 1.0, manso: true },
  zumbi: { hp: 20, vel: 1.5, dano: 6 }, gosma: { hp: 10, vel: 1.2, dano: 4 }, esqueleto: { hp: 16, vel: 1.7, dano: 5 },
};
function livre(x, y) {
  if (modo === 'explorar') { const t = chaoEm(Math.floor(x), Math.floor(y)); if (t === 'w') return false; const o = OBJ_TILE.get(Math.floor(x) + ',' + Math.floor(y)); return !o || QUEBRADOS.has(o.id) || o.tipo === 'capim'; }
  return celula(MINA.z, Math.floor(x), Math.floor(y)) === '.' && !(MINA.cam[MINA.z + 1] && celula(MINA.z + 1, Math.floor(x), Math.floor(y)) === '.');
}
function nascer(noite) {
  const c = V.ctrl, perto = ents.filter(e => Math.hypot(e.x - c.x, e.y - c.y) < 22);
  ents = perto;
  if (modo === 'explorar') {
    if (Math.hypot(c.x - MUNDO.spawn[0], c.y - MUNDO.spawn[1]) < 9) return;              // área segura
    const bioma = chaoEm(Math.floor(c.x), Math.floor(c.y));
    const mansos = ents.filter(e => MOBS[e.tipo].manso).length, bravos = ents.length - mansos;
    let tipo = null;
    if (mansos < 6 && Math.random() < 0.5 && (bioma === 'g' || bioma === 'f')) tipo = ['galinha', 'vaca', 'ovelha'][Math.floor(Math.random() * 3)];
    else if (bravos < (noite ? 5 : 1) && Math.random() < (noite ? 0.6 : 0.15)) tipo = noite ? (Math.random() < 0.7 ? 'zumbi' : 'esqueleto') : (bioma === 'f' ? 'gosma' : null);
    if (!tipo) return;
    for (let k = 0; k < 8; k++) {
      const a = Math.random() * Math.PI * 2, d = 8 + Math.random() * 6, x = c.x + Math.cos(a) * d, y = c.y + Math.sin(a) * d;
      if (livre(x, y)) { ents.push({ id: idEnt++, tipo, x, y, hp: MOBS[tipo].hp, manso: MOBS[tipo].manso, dir: 1, t: Math.random() * 10, alvo: null }); return; }
    }
  } else if (modo === 'mina' && MINA.z >= 2 && ents.length < 3 && Math.random() < 0.3) {
    for (let k = 0; k < 12; k++) {
      const x = Math.floor(Math.random() * MINA_N) + 0.5, y = Math.floor(Math.random() * MINA_N) + 0.5;
      if (Math.hypot(x - c.x, y - c.y) > 5 && livre(x, y)) { const tipo = Math.random() < 0.5 ? 'zumbi' : 'esqueleto'; ents.push({ id: idEnt++, tipo, x, y, hp: MOBS[tipo].hp, dir: 1, t: 0 }); return; }
    }
  }
}
function andarBichos(dt) {
  const c = V.ctrl, agora = performance.now();
  for (const e of ents) {
    const M = MOBS[e.tipo]; e.t += dt;
    if (e.kx) { const nx = e.x + e.kx, ny = e.y + e.ky; if (livre(nx, ny)) { e.x = nx; e.y = ny; } e.kx = e.ky = 0; }
    let vx = 0, vy = 0;
    const dx = c.x - e.x, dy = c.y - e.y, d = Math.hypot(dx, dy);
    if (!M.manso && d < 8) { vx = dx / d; vy = dy / d; }                                   // persegue
    else if (e.foge > agora) { vx = -dx / d; vy = -dy / d; }                              // foge
    else { if (!e.rumo || e.t > e.troca) { e.t = 0; e.troca = 2 + Math.random() * 3; const a = Math.random() * 7; e.rumo = Math.random() < 0.4 ? [0, 0] : [Math.cos(a), Math.sin(a)]; } [vx, vy] = e.rumo; vx *= 0.5; vy *= 0.5; }
    const v = M.vel * dt * (e.foge > agora ? 1.8 : 1);
    if (vx || vy) { if (livre(e.x + vx * v, e.y)) e.x += vx * v; if (livre(e.x, e.y + vy * v)) e.y += vy * v; e.dir = (vx - vy) >= 0 ? 1 : -1; e.anda = true; } else e.anda = false;
    // ataque
    if (!M.manso && d < 0.9 && agora - (e.ataque || 0) > 1000) {
      e.ataque = agora; const def = Math.min(0.8, defesaTotal() * 0.04), dano = Math.max(1, Math.round(M.dano * (1 - def)));
      V.mudarVida(V.VIDA - dano); ultimoDano = agora; som('dano'); flutua(c.x, c.y - 1.2, '-' + dano, '#ff6060');
      if (V.VIDA <= 0) morrer();
    }
  }
}
function morrer() {
  V.toast('💀 Você desmaiou! Voltou pro início com metade da vida.');
  V.mudarVida(50); acao = null; ents = [];
  if (modo === 'mina') { MINA.z = 0; carregarMina(0).then(() => { V.ctrl.x = MINA_ESCADA + 0.5; V.ctrl.y = MINA_ESCADA + 0.5; }); }
  else { V.ctrl.x = MUNDO.spawn[0] + 0.5; V.ctrl.y = MUNDO.spawn[1] + 0.5; }
}

// ---------------------------------------------------------------------
// DESENHO
// ---------------------------------------------------------------------
let ultimoQuadro = 0, ultimoNascer = 0, ultimaPoll = 0, pollLotes = 0;
function desenhar(agoraReal, t, nf) {
  const dt = Math.min(0.1, (agoraReal - (ultimoQuadro || agoraReal)) / 1000); ultimoQuadro = agoraReal;
  const c = V.ctrl, W = V.W, H = V.H, DPR = V.DPR, s = V.cam.s;
  // regras do jogo a cada quadro
  if (agoraReal - ultimoNascer > 1500) { ultimoNascer = agoraReal; nascer(modo === 'explorar' ? nf > 0.5 : true); }
  andarBichos(dt);
  if (acao && !pendente && agoraReal - acao.t0 >= acao.dur) { const a = acao; acao = null; terminar(a); }
  if (agoraReal - ultimaPoll > (modo === 'mina' ? 5000 : modo === 'lotes' ? 6000 : 20000)) { ultimaPoll = agoraReal; if (modo === 'mina') carregarMina(MINA.z); else if (modo === 'lotes') { carregarBlocosPerto(); if (++pollLotes % 5 === 0) carregarLotes(); } else atualizarQuebrados(); }
  if (window.Sons) Sons.ambiente(modo, nf > 0.5);
  if (agoraReal - ultimaPollTela > 500) { ultimaPollTela = agoraReal; atualizarTopoJogo(); V.atualizarAcoes(); }

  const P = iso(c.x, c.y), k = DPR * s;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = modo === 'mina' ? '#0c0a10' : (nf > 0.5 ? '#14202a' : '#2f6b3a'); ctx.fillRect(0, 0, V.cv.width, V.cv.height);
  const tx = Math.round(DPR * W / 2 - P.X * k), ty = Math.round(DPR * H / 2 - (P.Y - 10) * k);
  ctx.setTransform(k, 0, 0, k, tx, ty); ctx.imageSmoothingEnabled = false;
  const telaDe = (X, Y) => ({ x: (X * k + tx) / DPR, y: (Y * k + ty) / DPR });
  const v0 = { X: P.X - W / 2 / s - 40, Y: P.Y - H / 2 / s - 80 }, v1 = { X: P.X + W / 2 / s + 40, Y: P.Y + H / 2 / s + 80 };
  const lista = []; retangulos = [];
  const noite = nf > 0.5;

  const textosTela = [], luzes = [];
  if (modo === 'explorar' || modo === 'lotes') {
    // chão (pedaços em cache)
    const tl = daIso(v0.X, v0.Y), tr = daIso(v1.X, v0.Y), bl = daIso(v0.X, v1.Y), brr = daIso(v1.X, v1.Y);
    const minx = Math.floor(Math.min(tl.x, bl.x) / CH) - 1, maxx = Math.floor(Math.max(tr.x, brr.x) / CH) + 1, miny = Math.floor(Math.min(tl.y, tr.y) / CH) - 1, maxy = Math.floor(Math.max(bl.y, brr.y) / CH) + 1;
    for (let cy = Math.max(0, miny); cy <= Math.min(Math.ceil(CHAO.h / CH) - 1, maxy); cy++) for (let cx = Math.max(0, minx); cx <= Math.min(Math.ceil(CHAO.w / CH) - 1, maxx); cx++) {
      const p = pedaco(cx, cy); ctx.drawImage(p.c, p.minX, p.minY);
    }
  }
  if (modo === 'lotes') {
    const depEu = c.x + c.y;
    for (const l of LOTES) {
      const [ox, oy] = origemLote(l.id), Ic = iso(ox + 8, oy + 8);
      if (Ic.X < v0.X - 280 || Ic.X > v1.X + 280 || Ic.Y < v0.Y - 160 || Ic.Y > v1.Y + 200) continue;
      const pl = iso(ox + 7.5, oy + LT + 0.9);
      lista.push({ d: ox + oy + LT + 8.4, f: () => placaLote(pl.X, pl.Y, l, textosTela) });
      const m = LBLOCOS.get(l.id); if (!m) continue;
      for (const [chave, tipo] of m) {
        const [x, y, z] = chave.split(',').map(Number), wx = ox + x, wy = oy + y, it = ITENS[tipo]; if (!it) continue;
        const I = iso(wx, wy);
        if (I.X < v0.X - 20 || I.X > v1.X + 20 || I.Y < v0.Y - 80 || I.Y > v1.Y + 20) continue;
        if (z === -1) { lista.push({ d: wx + wy - 1.5, f: () => ctx.drawImage(cuboBloco(tipo, 'piso'), I.X - 16, I.Y - 1) }); continue; }
        const d = wx + wy + 1 + z * 0.01, atras = d > depEu + 0.6;
        if (it.forma === 'cubo') {
          lista.push({ d, f: () => {
            const y0 = I.Y - 16 - z * 16, tapa = atras && Math.abs(I.X - P.X) < 30 && y0 < P.Y + 2 && y0 + 32 > P.Y - 46;
            if (tapa) ctx.globalAlpha = 0.38;
            ctx.drawImage(cuboBloco(tipo, 'cubo'), I.X - 16, y0); ctx.globalAlpha = 1;
            retangulos.push({ a: { tipo: 'lbloco', wx, wy }, x: I.X - 16, y: y0, w: 32, h: 32 });
          } });
        } else {
          const Ic2 = iso(wx + 0.5, wy + 0.5), sp = spriteMovel(tipo);
          if (tipo === 'lampiao') luzes.push([Ic2.X, Ic2.Y - 26 - z * 16]);
          lista.push({ d, f: () => {
            const x0 = Math.round(Ic2.X - sp.ax), y0 = Math.round(Ic2.Y - sp.ay - z * 16 + 2);
            const tapa = atras && Math.abs(Ic2.X - P.X) < 24 && y0 < P.Y && y0 + sp.c.height > P.Y - 46;
            if (tapa) ctx.globalAlpha = 0.45; ctx.drawImage(sp.c, x0, y0); ctx.globalAlpha = 1;
            retangulos.push({ a: { tipo: 'lbloco', wx, wy }, x: x0, y: y0, w: sp.c.width, h: sp.c.height });
          } });
        }
      }
    }
    // portal de volta e a feira
    const pt = iso(LT_PORTAL[0] + 0.5, LT_PORTAL[1] + 0.5), fe = iso(LT_FEIRA[0] + 0.5, LT_FEIRA[1] + 0.5);
    lista.push({ d: LT_PORTAL[0] + LT_PORTAL[1] + 1, f: () => { portal(pt.X, pt.Y, 1, agoraReal); textosTela.push({ X: pt.X, Y: pt.Y - 46, txt: '🏙️ Voltar pra cidade' }); } });
    lista.push({ d: LT_FEIRA[0] + LT_FEIRA[1] + 1, f: () => { quadroFeira(fe.X, fe.Y); textosTela.push({ X: fe.X, Y: fe.Y - 44, txt: '📋 Feira dos lotes', bg: '#b9871c' }); } });
    // fantasma do que vai construir (ou o bloco que vai tirar)
    const pl = alvoConstrucao();
    if (pl && !pl.vazio) {
      const I = iso(pl.wx, pl.wy), Ic = iso(pl.wx + 0.5, pl.wy + 0.5);
      lista.push({ d: pl.wx + pl.wy + 1 + (pl.z || 0) * 0.01 + 0.005, f: () => {
        if (pl.colocar) {
          ctx.globalAlpha = 0.55;
          if (pl.forma === 'piso') ctx.drawImage(cuboBloco(pl.tipo, 'piso'), I.X - 16, I.Y - 1);
          else if (pl.forma === 'cubo') ctx.drawImage(cuboBloco(pl.tipo, 'cubo'), I.X - 16, I.Y - 16 - pl.z * 16);
          else { const sp = spriteMovel(pl.tipo); ctx.drawImage(sp.c, Math.round(Ic.X - sp.ax), Math.round(Ic.Y - sp.ay - pl.z * 16 + 2)); }
          ctx.globalAlpha = 1;
        }
        const zz = pl.z < 0 ? 0 : pl.z, yy = I.Y - (pl.forma === 'piso' || (pl.colocar === false && pl.z < 0) ? 0 : 16 + zz * 16);
        ctx.strokeStyle = !pl.ok ? '#ff5050' : pl.colocar ? '#7CFF8A' : '#f6c836'; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(I.X, yy); ctx.lineTo(I.X + 16, yy + 8); ctx.lineTo(I.X, yy + 16); ctx.lineTo(I.X - 16, yy + 8); ctx.closePath(); ctx.stroke();
      } });
    }
  }
  if (modo === 'explorar') {
    // objetos visíveis
    const r0 = Math.floor(c.x) - 26, r1 = Math.floor(c.x) + 26, q0 = Math.floor(c.y) - 26, q1 = Math.floor(c.y) + 26;
    for (let y = Math.max(0, q0); y <= Math.min(MUNDO.h - 1, q1); y++) for (let x = Math.max(0, r0); x <= Math.min(MUNDO.w - 1, r1); x++) {
      const o = OBJ_TILE.get(x + ',' + y); if (!o || QUEBRADOS.has(o.id)) continue;
      const I = iso(x + 0.5, y + 0.5); if (I.X < v0.X || I.X > v1.X || I.Y < v0.Y || I.Y > v1.Y) continue;
      lista.push({ d: x + y + 1, f: () => { const sp = spriteObj(o.tipo, o.v); ctx.drawImage(sp.c, Math.round(I.X - sp.ax), Math.round(I.Y - sp.ay + 4)); retangulos.push({ a: { tipo: 'obj', o }, x: I.X - sp.ax, y: I.Y - sp.ay + 4, w: sp.c.width, h: sp.c.height }); } });
    }
    // portal de volta e entrada da mina
    const pt = iso(MUNDO.portal[0] + 0.5, MUNDO.portal[1] + 0.5), mn = iso(MUNDO.mina[0] + 0.5, MUNDO.mina[1] + 0.5);
    lista.push({ d: MUNDO.portal[0] + MUNDO.portal[1] + 1, f: () => portal(pt.X, pt.Y, 1, agoraReal) });
    lista.push({ d: MUNDO.mina[0] + MUNDO.mina[1] + 1, f: () => entradaMina(mn.X, mn.Y) });
  } else if (modo === 'mina') {
    // mina: a camada atual (cubos) e o chão (camada de baixo)
    for (let s2 = 0; s2 < MINA_N * 2 - 1; s2++) for (let x = 0; x < MINA_N; x++) {
      const y = s2 - x; if (y < 0 || y >= MINA_N) continue;
      const I = iso(x, y), ch = celula(MINA.z, x, y);
      if (ch === '.') {
        const baixo = MINA.cam[MINA.z + 1] ? celula(MINA.z + 1, x, y) : 'p';
        lista.push({ d: x + y - 1, f: () => {
          if (x === MINA_ESCADA && y === MINA_ESCADA) { losango(ctx, I.X - 16, I.Y, '#3a2a1c'); ctx.fillStyle = '#c8955a'; for (let i = 0; i < 4; i++) ctx.fillRect(I.X - 6, I.Y + 3 + i * 3, 12, 1); ctx.fillRect(I.X - 7, I.Y + 2, 1, 12); ctx.fillRect(I.X + 6, I.Y + 2, 1, 12); }
          else if (baixo === '.') losango(ctx, I.X - 16, I.Y, '#08060a');
          else { const [b] = MINA_COR[baixo] || MINA_COR.p; losango(ctx, I.X - 16, I.Y, rgb(b, 0.72)); }
        } });
      } else {
        lista.push({ d: x + y + 1, f: () => { ctx.drawImage(cubo(ch), I.X - 16, I.Y - 16); retangulos.push({ a: { tipo: 'bloco', z: MINA.z, x, y }, x: I.X - 16, y: I.Y - 16, w: 32, h: 32 }); } });
      }
    }
    if (MINA.z === 0) { const lj = iso(10.5, 10.5); lista.push({ d: 21, f: () => vendedor(lj.X, lj.Y, agoraReal) }); }
  }
  // bichos
  const quadro = Math.floor(agoraReal / 125) % 4;
  for (const e of ents) {
    const I = iso(e.x, e.y); if (I.X < v0.X || I.X > v1.X || I.Y < v0.Y || I.Y > v1.Y) continue;
    lista.push({ d: e.x + e.y, f: () => {
      ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.beginPath(); ctx.ellipse(I.X, I.Y, 7, 3, 0, 0, 7); ctx.fill();
      const pisca = e.bate && agoraReal - e.bate < 150;
      if (e.tipo === 'zumbi' || e.tipo === 'esqueleto') {
        const fo = folhaMob(e.tipo), di = e.dir > 0 ? 2 : 1, fr = e.anda ? quadro : 0;
        if (pisca) ctx.globalAlpha = 0.5; ctx.drawImage(fo, fr * 32, di * 48, 32, 48, Math.round(I.X - 16), Math.round(I.Y - 46), 32, 48); ctx.globalAlpha = 1;
        retangulos.push({ a: { tipo: 'mob', e }, x: I.X - 16, y: I.Y - 46, w: 32, h: 48 });
      } else {
        const sp = spriteBicho(e.tipo, e.anda ? quadro % 2 : 0);
        ctx.save(); ctx.translate(Math.round(I.X), Math.round(I.Y)); if (e.dir < 0) ctx.scale(-1, 1); if (pisca) ctx.globalAlpha = 0.5;
        ctx.drawImage(sp.c, -sp.ax, -sp.ay); ctx.restore();
        retangulos.push({ a: { tipo: 'mob', e }, x: I.X - sp.ax, y: I.Y - sp.ay, w: sp.c.width, h: sp.c.height });
      }
    } });
  }
  // outros jogadores no mesmo lugar
  const meuW = modo === 'explorar' ? 'x' : modo === 'lotes' ? 'l' : 'm' + MINA.z;
  for (const [m, r] of V.REMOTO) {
    if (r.w !== meuW || performance.now() - r.t > 6000) continue;
    const I = iso(r.x, r.y);
    lista.push({ d: r.x + r.y, f: () => {
      const fo = folhaJogador(m, r.arm, noite); if (!fo) return;
      const fr = r.anda ? quadro : 0, di = { down: 0, left: 1, right: 2, up: 3 }[r.dir] || 0;
      ctx.drawImage(fo, fr * 32, di * 48, 32, 48, Math.round(I.X - 16), Math.round(I.Y - 46), 32, 48);
      textosTela.push({ X: I.X, Y: I.Y - 50, txt: V.rotulo(m) });
    } });
  }
  // eu
  lista.push({ d: c.x + c.y, f: () => {
    ctx.fillStyle = 'rgba(0,0,0,.28)'; ctx.beginPath(); ctx.ellipse(P.X, P.Y + 1, 8, 3, 0, 0, 7); ctx.fill();
    const fo = folhaJogador(V.EU.morador, armadura(), noite);
    const fr = c.anda ? quadro : 0, di = { down: 0, left: 1, right: 2, up: 3 }[c.dir] || 0;
    if (agoraReal - ultimoDano < 160) ctx.globalAlpha = 0.55;
    if (fo) ctx.drawImage(fo, fr * 32, di * 48, 32, 48, Math.round(P.X - 16), Math.round(P.Y - 46), 32, 48);
    ctx.globalAlpha = 1;
    // o que está na mão
    const it = itemNaMao(); if (it && ITENS[it.i] && ITENS[it.i].tipo !== 'material') {
      const img = imgCache(it.i); if (img) { const lado = c.dir === 'left' ? -1 : 1, bal = acao ? Math.sin(agoraReal / 60) * 3 : 0; ctx.drawImage(img, Math.round(P.X + lado * 8 - 6), Math.round(P.Y - 26 + bal), 12, 12); }
    }
  } });
  lista.sort((a, b) => a.d - b.d);
  for (const it of lista) it.f();
  // mina: setinha apontando pra escada quando ela está longe
  if (modo === 'mina') {
    const dx = MINA_ESCADA + 0.5 - c.x, dy = MINA_ESCADA + 0.5 - c.y, dist = Math.hypot(dx, dy);
    if (dist > 3) {
      const E = iso(MINA_ESCADA + 0.5, MINA_ESCADA + 0.5), ang = Math.atan2(E.Y - P.Y, E.X - P.X), r = 24;
      ctx.save(); ctx.translate(P.X + Math.cos(ang) * r, P.Y - 18 + Math.sin(ang) * r); ctx.rotate(ang);
      ctx.fillStyle = '#f6c836'; ctx.strokeStyle = '#1e1824'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(6, 0); ctx.lineTo(-4, -4); ctx.lineTo(-2, 0); ctx.lineTo(-4, 4); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore();
    }
  }

  // alvo e progresso
  if (acao && agoraReal - (acao.somT || 0) > 330) { acao.somT = agoraReal; som(somDaBatida(acao)); }
  const alvo = acao || alvoNaFrente();
  if (alvo) {
    const [ax, ay] = centroAlvo(alvo), I = iso(ax, ay);
    ctx.strokeStyle = acao ? '#f6c836' : 'rgba(255,248,231,.7)'; ctx.lineWidth = 1.5;
    if (alvo.tipo === 'bloco') { ctx.strokeRect(I.X - 12, I.Y - 22, 24, 24); }
    else { ctx.beginPath(); ctx.ellipse(I.X, I.Y, 10, 5, 0, 0, 7); ctx.stroke(); }
    if (acao) {
      const p = clamp((agoraReal - acao.t0) / acao.dur, 0, 1);
      ctx.fillStyle = '#1e1824'; ctx.fillRect(I.X - 13, I.Y - 32, 26, 6); ctx.fillStyle = '#f6c836'; ctx.fillRect(I.X - 12, I.Y - 31, 24 * p, 4);
      // rachaduras
      ctx.strokeStyle = 'rgba(20,16,24,.8)'; ctx.lineWidth = 1; ctx.beginPath();
      for (let i = 0; i < Math.floor(p * 6); i++) { const a2 = i * 1.7; ctx.moveTo(I.X, I.Y - 10); ctx.lineTo(I.X + Math.cos(a2) * 8, I.Y - 10 + Math.sin(a2) * 6); }
      ctx.stroke();
    }
  }
  // noite / escuro da mina
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  if (modo === 'mina' || nf > 0) {
    const luz = luzCanvas(W, H), g2 = luz.getContext('2d'), eu = telaDe(P.X, P.Y - 20);
    g2.globalCompositeOperation = 'source-over'; g2.clearRect(0, 0, W, H);
    g2.fillStyle = modo === 'mina' ? `rgba(4,3,8,${Math.min(0.88, 0.62 + MINA.z * 0.025)})` : `rgba(10,14,40,${0.55 * nf})`; g2.fillRect(0, 0, W, H);
    g2.globalCompositeOperation = 'destination-out';
    const raio = (modo === 'mina' ? 7 : 4.5) * 16 * s, gr = g2.createRadialGradient(eu.x, eu.y, raio * 0.25, eu.x, eu.y, raio);
    gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); g2.fillStyle = gr; g2.beginPath(); g2.arc(eu.x, eu.y, raio, 0, 7); g2.fill();
    for (const [lx, ly] of luzes) {                 // lampiões acesos
      const p = telaDe(lx, ly), rl = 3.2 * 16 * s, gl = g2.createRadialGradient(p.x, p.y, rl * 0.15, p.x, p.y, rl);
      gl.addColorStop(0, 'rgba(0,0,0,.95)'); gl.addColorStop(1, 'rgba(0,0,0,0)'); g2.fillStyle = gl; g2.beginPath(); g2.arc(p.x, p.y, rl, 0, 7); g2.fill();
    }
    ctx.drawImage(luz, 0, 0, W, H);
  }
  // textos (nomes, números)
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.font = '700 11px Nunito, system-ui, sans-serif';
  for (const tt of textosTela) { const p = telaDe(tt.X, tt.Y), w = ctx.measureText(tt.txt).width + 10; ctx.fillStyle = tt.bg || 'rgba(30,24,36,.72)'; V.pilula(p.x - w / 2, p.y - 8, w, 15, 7); ctx.fill(); ctx.fillStyle = '#fff8e7'; ctx.fillText(tt.txt, p.x, p.y); }
  const agora = performance.now(); textos = textos.filter(f => agora - f.t < 1400);
  ctx.font = '800 13px "Pixelify Sans", Nunito, sans-serif';
  for (const f of textos) { const I = iso(f.x, f.y), p = telaDe(I.X, I.Y - 40 - (agora - f.t) / 40); ctx.globalAlpha = 1 - (agora - f.t) / 1400; ctx.fillStyle = '#1e1824'; ctx.fillText(f.texto, p.x + 1, p.y + 1); ctx.fillStyle = f.cor; ctx.fillText(f.texto, p.x, p.y); ctx.globalAlpha = 1; }
  // minha vida em cima do boneco
  const pv = telaDe(P.X, P.Y - 52), w = 30;
  ctx.fillStyle = '#1e1824'; ctx.fillRect(pv.x - w / 2 - 1, pv.y - 1, w + 2, 7); ctx.fillStyle = '#5a1f2a'; ctx.fillRect(pv.x - w / 2, pv.y, w, 5);
  ctx.fillStyle = V.VIDA <= 25 ? '#ff4d4d' : V.VIDA <= 60 ? '#f6c836' : '#40c463'; ctx.fillRect(pv.x - w / 2, pv.y, Math.round(w * V.VIDA / 100), 5);
  desenhar.telaDe = telaDe; desenhar.k = k; desenhar.tx = tx; desenhar.ty = ty;
}
let _luz = null; function luzCanvas(W, H) { if (!_luz || _luz.width !== W || _luz.height !== H) { _luz = document.createElement('canvas'); _luz.width = W; _luz.height = H; } return _luz; }
const imgs = new Map(); function imgCache(id) { if (imgs.has(id)) return imgs.get(id); const im = new Image(); im.src = icone(id); imgs.set(id, im); return im; }
function portal(X, Y, esc_, agoraReal) {
  ctx.fillStyle = '#5e5e66'; ctx.fillRect(X - 13, Y - 34, 5, 34); ctx.fillRect(X + 8, Y - 34, 5, 34); ctx.fillRect(X - 13, Y - 38, 26, 5);
  ctx.fillStyle = '#8a8a94'; ctx.fillRect(X - 12, Y - 34, 2, 34); ctx.fillRect(X + 9, Y - 34, 2, 34); ctx.fillRect(X - 12, Y - 37, 24, 2);
  const a = agoraReal / 300;
  for (let i = 0; i < 26; i++) { const ang = a + i * 0.48, r = 2 + (i % 7); ctx.fillStyle = i % 3 ? '#a855f7' : '#e0b8ff'; ctx.fillRect(Math.round(X + Math.cos(ang) * r * 0.9) - 1, Math.round(Y - 17 + Math.sin(ang) * r * 1.8) - 1, 2, 2); }
  ctx.fillStyle = 'rgba(168,85,247,.25)'; ctx.fillRect(X - 8, Y - 33, 16, 33);
}
function entradaMina(X, Y) {
  ctx.fillStyle = '#4a3a2a'; ctx.fillRect(X - 14, Y - 22, 28, 22); ctx.fillStyle = '#0c0a10'; ctx.fillRect(X - 9, Y - 17, 18, 17);
  ctx.fillStyle = '#8a5a2b'; ctx.fillRect(X - 15, Y - 24, 30, 4); ctx.fillRect(X - 15, Y - 24, 4, 24); ctx.fillRect(X + 11, Y - 24, 4, 24);
  ctx.fillStyle = '#f6c836'; ctx.fillRect(X - 3, Y - 30, 6, 5); ctx.fillStyle = '#1e1824'; ctx.fillRect(X - 1, Y - 29, 2, 3);
}
function placaLote(X, Y, l, textosTela) {
  ctx.fillStyle = '#6b4423'; ctx.fillRect(X - 1, Y - 18, 3, 18);
  const livre = !l.dono, cor = livre ? '#40a456' : l.dono === (V.EU && V.EU.morador) ? '#f6c836' : '#c8955a';
  ctx.fillStyle = '#1e1824'; ctx.fillRect(X - 12, Y - 27, 24, 12); ctx.fillStyle = cor; ctx.fillRect(X - 11, Y - 26, 22, 10);
  ctx.fillStyle = '#1e1824'; ctx.font = '700 7px Nunito, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(String(l.id), X, Y - 21);
  textosTela.push({ X, Y: Y - 34, txt: livre ? `Lote ${l.id} · LIVRE` : (l.nome || 'Lote ' + l.id) + (l.loja ? ' · 🛒' : ''), bg: livre ? 'rgba(45,122,63,.9)' : undefined });
}
function quadroFeira(X, Y) {
  ctx.fillStyle = '#6b4423'; ctx.fillRect(X - 13, Y - 26, 3, 26); ctx.fillRect(X + 10, Y - 26, 3, 26);
  ctx.fillStyle = '#1e1824'; ctx.fillRect(X - 16, Y - 36, 32, 20); ctx.fillStyle = '#c8955a'; ctx.fillRect(X - 15, Y - 35, 30, 18);
  ctx.fillStyle = '#f4f1ea'; for (const [x, y] of [[-12, -33], [-1, -32], [-11, -25], [2, -25]]) ctx.fillRect(X + x, Y + y, 9, 6);
  ctx.fillStyle = '#d63838'; for (const [x, y] of [[-8, -33], [3, -32], [-7, -25], [6, -25]]) ctx.fillRect(X + x, Y + y, 1, 1);
}
function arcoLotes(X, Y) {                       // entrada dos Terrenos e Lotes (na cidade)
  ctx.fillStyle = '#7a4e26'; ctx.fillRect(X - 16, Y - 34, 5, 34); ctx.fillRect(X + 11, Y - 34, 5, 34);
  ctx.fillStyle = '#a8733f'; ctx.fillRect(X - 15, Y - 34, 2, 34); ctx.fillRect(X + 12, Y - 34, 2, 34);
  ctx.fillStyle = '#1e1824'; ctx.fillRect(X - 19, Y - 44, 38, 12); ctx.fillStyle = '#c8955a'; ctx.fillRect(X - 18, Y - 43, 36, 10);
  ctx.fillStyle = '#40a456'; ctx.fillRect(X - 6, Y - 41, 12, 6); ctx.fillStyle = '#d63838'; ctx.fillRect(X - 7, Y - 42, 14, 2);
  ctx.fillStyle = '#f4f1ea'; ctx.fillRect(X - 2, Y - 39, 3, 4);
}
function somDaBatida(a) {
  if (a.tipo === 'desmonta') return 'colocar';
  if (a.tipo === 'obj') { const t = a.o.tipo; return /carvalho|pinheiro|palmeira/.test(t) ? 'madeira' : /rocha/.test(t) ? 'pedra' : 'folha'; }
  if (a.tipo === 'bloco') return celula(a.z, a.x, a.y) === 't' ? 'terra' : 'pedra';
  return 'golpe';
}
// ---------------------------------------------------------------------
// CONSTRUIR nos lotes
// ---------------------------------------------------------------------
function telaParaTile(sx, sy) {
  if (!desenhar.k) return null;
  const wx = (sx * V.DPR - desenhar.tx) / desenhar.k, wy = (sy * V.DPR - desenhar.ty) / desenhar.k, t = daIso(wx, wy);
  return { x: Math.floor(t.x), y: Math.floor(t.y) };
}
function planoNoTile(tx, ty) {
  const lt = loteEm(tx, ty); if (!lt) return null;
  const meu = lt.id === MEU_LOTE, it = itemNaMao(), info = it && ITENS[it.i];
  const m = LBLOCOS.get(lt.id) || new Map(), em = z => m.get(lt.lx + ',' + lt.ly + ',' + z);
  let topo = -2; for (let z = 3; z >= -1; z--) if (em(z)) { topo = z; break; }
  if (info && info.tipo === 'bloco') {
    let z, ok = meu;
    if (info.forma === 'piso') { z = -1; ok = ok && !em(-1); }
    else if (topo < 0) z = 0;
    else { const de = ITENS[em(topo)]; z = topo + 1; ok = ok && !!de && de.forma === 'cubo' && z <= 3; }
    const c = V.ctrl;
    if (z === 0 && info.solido !== false && Math.floor(c.x) === tx && Math.floor(c.y) === ty) ok = false;    // não prende você dentro do bloco
    return { wx: tx, wy: ty, lt, z, tipo: it.i, forma: info.forma, colocar: true, ok };
  }
  if (topo === -2) return { wx: tx, wy: ty, lt, vazio: true, ok: false };
  return { wx: tx, wy: ty, lt, z: topo, tipo: em(topo), forma: (ITENS[em(topo)] || {}).forma, colocar: false, ok: meu };
}
function alvoConstrucao() {
  if (modo !== 'lotes') return null;
  const c = V.ctrl;
  if (mouseTela && performance.now() - mouseTela.t < 5000) { const t = telaParaTile(mouseTela.x, mouseTela.y); if (t && Math.hypot(t.x + 0.5 - c.x, t.y + 0.5 - c.y) < 7) return planoNoTile(t.x, t.y); }
  const fx = c.vx == null ? 0 : c.vx, fy = c.vy == null ? 1 : c.vy;
  let tx = Math.floor(c.x + fx * 1.05), ty = Math.floor(c.y + fy * 1.05);
  if (tx === Math.floor(c.x) && ty === Math.floor(c.y)) { tx = Math.floor(c.x + fx * 1.6); ty = Math.floor(c.y + fy * 1.6); }
  return planoNoTile(tx, ty);
}
let recarregaInv = null;
const agendarInv = () => { clearTimeout(recarregaInv); recarregaInv = setTimeout(carregarJogo, 900); };
async function construirAqui(p) {
  if (!p || pendente) return;
  if (!MEU_LOTE) { som('erro'); return V.toast('🏡 Pegue um lote primeiro: ande até uma placa verde "LIVRE"'); }
  if (p.lt.id !== MEU_LOTE) { som('erro'); return V.toast(`Esse lote não é seu. O seu é o nº ${MEU_LOTE}`); }
  if (p.vazio) return V.toast('🧱 Escolha um bloco na barra (crie em 🔨 Criar → Construção)');
  if (Math.hypot(p.wx + 0.5 - V.ctrl.x, p.wy + 0.5 - V.ctrl.y) > 7) return V.toast('Chega mais perto');
  if (!p.colocar) { acao = { tipo: 'desmonta', p, t0: performance.now(), dur: 380, dist: false }; return; }
  if (!p.ok) { som('erro'); return V.toast(p.z > 3 ? 'Altura máxima: 4 blocos' : 'Não dá pra pôr aí'); }
  const m = LBLOCOS.get(p.lt.id) || new Map(), chave = p.lt.lx + ',' + p.lt.ly + ',' + p.z; LBLOCOS.set(p.lt.id, m);
  m.set(chave, p.tipo); som('colocar');
  const s = JOG.inv[SEL], slot = SEL; if (s) { s.q--; if (s.q <= 0) JOG.inv[SEL] = null; desenharBarra(); }
  const r = await rpc('construir', { p_token: tkn(), p_lote: p.lt.id, p_x: p.lt.lx, p_y: p.lt.ly, p_z: p.z, p_slot: slot });
  if (!r || !r.ok) { m.delete(chave); som('erro'); V.toast((r && r.erro) || 'Não deu'); return carregarJogo(); }
  window.Rt && Rt.pos({ m: V.EU.morador, ev: 'constroi', w: 'l', lote: p.lt.id, x: p.lt.lx, y: p.lt.ly, z: p.z, t: p.tipo });
  agendarInv();
}
async function desmontarAgora(p) {
  pendente = true;
  const r = await rpc('desmontar', { p_token: tkn(), p_lote: p.lt.id, p_x: p.lt.lx, p_y: p.lt.ly, p_z: p.z });
  pendente = false;
  const m = LBLOCOS.get(p.lt.id);
  if (r && (r.ok || r.sumiu)) {
    if (m) m.delete(p.lt.lx + ',' + p.lt.ly + ',' + p.z);
    if (r.ok) { som('quebrou'); flutua(p.wx + 0.5, p.wy + 0.5, '+1 ' + nomeItem(r.tipo), '#b6f0a4'); window.Rt && Rt.pos({ m: V.EU.morador, ev: 'constroi', w: 'l', lote: p.lt.id, x: p.lt.lx, y: p.lt.ly, z: p.z, t: null }); agendarInv(); }
  } else { som('erro'); V.toast((r && r.erro) || 'Não deu'); }
}
function vendedor(X, Y, agoraReal) {
  ctx.fillStyle = '#8a5a2b'; ctx.fillRect(X - 14, Y - 12, 28, 10); ctx.fillStyle = '#c8955a'; ctx.fillRect(X - 14, Y - 13, 28, 2);
  const look = { pele: 3, cabelo: 'curto', cor_cabelo: 0, camisa: 6, estampa: 'listrada', camisa2: 2, baixo: 'calca', cor_baixo: 1, sapato: 2, oculos: true, chapeu: 'bone', cor_chapeu: 2, barba: true };
  const f = V.folha32(look); if (f) ctx.drawImage(f.dia, 0, 0, 32, 48, X - 16, Y - 52, 32, 48);
  ctx.fillStyle = '#f6c836'; ctx.font = '700 9px Nunito, sans-serif'; ctx.textAlign = 'center'; ctx.fillText('💰 LOJA', X, Y - 56);
}

// ---------------------------------------------------------------------
// PORTAL na cidade
// ---------------------------------------------------------------------
function desenharNaCidade(agoraReal) {
  if (window.Sons) Sons.ambiente('cidade', false);
  const W = V.W, H = V.H, z = Math.max(1, Math.min(4, V.cam.s * 1.4)), rets = {};
  const placa = (p, txt, cor) => {
    ctx.font = '800 12px "Pixelify Sans", Nunito, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    const w = ctx.measureText(txt).width + 14, y = p.y - 50 * z;
    ctx.fillStyle = '#1e1824'; V.pilula(p.x - w / 2 - 2, y - 11, w + 4, 22, 8); ctx.fill(); ctx.fillStyle = cor; V.pilula(p.x - w / 2, y - 9, w, 18, 7); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.fillText(txt, p.x, y);
  };
  const p = V.mundoPraTela(PORTAL_CIDADE[0], PORTAL_CIDADE[1]);
  if (!(p.x < -80 || p.x > W + 80 || p.y < -100 || p.y > H + 60)) {
    ctx.save(); ctx.translate(p.x, p.y); ctx.scale(z, z); portal(0, 0, 1, agoraReal); ctx.restore();
    placa(p, '🌀 Portal · Explorar', '#7c3aed'); rets.portal = { x: p.x - 20 * z, y: p.y - 56 * z, w: 40 * z, h: 60 * z };
  }
  const q = V.mundoPraTela(ARCO_LOTES[0], ARCO_LOTES[1]);
  if (!(q.x < -80 || q.x > W + 80 || q.y < -100 || q.y > H + 60)) {
    ctx.save(); ctx.translate(q.x, q.y); ctx.scale(z, z); arcoLotes(0, 0); ctx.restore();
    placa(q, '🏡 Terrenos e Lotes', '#2d7a3f'); rets.lotes = { x: q.x - 20 * z, y: q.y - 56 * z, w: 40 * z, h: 60 * z };
  }
  desenharNaCidade.rets = rets;
}
function tocarNaCidade(sx, sy) {
  const R = desenharNaCidade.rets || {}, den = r => r && sx >= r.x && sx <= r.x + r.w && sy >= r.y && sy <= r.y + r.h;
  if (den(R.portal)) { entrarExplorar(); return true; }
  if (den(R.lotes)) { entrarLotes(); return true; }
  return false;
}
function acoesCidade(x, y) {
  const a = [];
  if (Math.hypot(x - PORTAL_CIDADE[0], y - PORTAL_CIDADE[1]) < 14) a.push({ rotulo: '🌀 Entrar no portal (explorar)', fn: () => entrarExplorar() });
  if (Math.hypot(x - ARCO_LOTES[0], y - ARCO_LOTES[1]) < 14) a.push({ rotulo: '🏡 Terrenos e Lotes', fn: () => entrarLotes() });
  return a;
}

// ---------------------------------------------------------------------
// TOQUE e TECLAS no jogo
// ---------------------------------------------------------------------
function tocar(sx, sy) {
  if (!desenhar.telaDe) return;
  const wx = (sx * V.DPR - desenhar.tx) / desenhar.k, wy = (sy * V.DPR - desenhar.ty) / desenhar.k;
  if (modo === 'lotes') {                     // toque: põe o bloco ali (ou tira o de cima)
    for (let i = retangulos.length - 1; i >= 0; i--) {
      const r = retangulos[i];
      if (r.a.tipo === 'lbloco' && wx >= r.x && wx <= r.x + r.w && wy >= r.y && wy <= r.y + r.h) return construirAqui(planoNoTile(r.a.wx, r.a.wy));
    }
    const t = daIso(wx, wy); return construirAqui(planoNoTile(Math.floor(t.x), Math.floor(t.y)));
  }
  // de trás pra frente: o que está desenhado por cima ganha
  for (let i = retangulos.length - 1; i >= 0; i--) {
    const r = retangulos[i];
    if (wx >= r.x && wx <= r.x + r.w && wy >= r.y && wy <= r.y + r.h) { comecar(r.a.tipo === 'mob' ? r.a : { ...r.a }); return; }
  }
}
// mouse no PC: o fantasma do bloco segue o mouse
V.cv.addEventListener('pointermove', e => { if (e.pointerType === 'mouse' && modo === 'lotes') mouseTela = { x: e.clientX, y: e.clientY, t: performance.now() }; });
function apertarAcao() {
  if (modo === 'lotes') return construirAqui(alvoConstrucao());
  comecar(alvoNaFrente());
}
let segurandoE = false;
addEventListener('keydown', e => {
  if (!modo || /input|textarea|select/i.test(e.target.tagName)) return;
  const t = e.key.toLowerCase();
  if (t === 'escape' && modalAberto) { fecharModal(); e.preventDefault(); e.stopImmediatePropagation(); return; }
  if (t === 'e' || t === ' ') { e.preventDefault(); if (!segurandoE) { segurandoE = true; mouseTela = null; apertarAcao(); } }
  if (t === 'f') { const a = acoes()[0]; if (a) { a.fn(); e.preventDefault(); } }
  if (t === 'i' || t === 'tab') { e.preventDefault(); modalAberto ? fecharModal() : abrirModal('inv'); }
  if (/^[1-9]$/.test(t)) { SEL = Number(t) - 1; desenharBarra(); som('clique'); }
}, true);
addEventListener('keyup', e => { if (e.key.toLowerCase() === 'e' || e.key === ' ') segurandoE = false; });
setInterval(() => { if (modo && modo !== 'lotes' && segurandoE && !acao && !pendente) comecar(alvoNaFrente()); }, 250);

// ações do botão (contexto)
function acoes() {
  const a = [], c = V.ctrl, it = itemNaMao(), info = it && ITENS[it.i];
  if (info && info.tipo === 'comida') a.push({ rotulo: `🍖 Comer ${info.nome} (+${info.cura})`, fn: comer });
  if (modo === 'explorar') {
    if (Math.hypot(c.x - MUNDO.portal[0] - 0.5, c.y - MUNDO.portal[1] - 0.5) < 2.2) a.push({ rotulo: '🌀 Voltar pra cidade', fn: () => { sairParaCidade(); } });
    if (Math.hypot(c.x - MUNDO.mina[0] - 0.5, c.y - MUNDO.mina[1] - 0.5) < 2.2) a.push({ rotulo: '⛏️ Entrar na mina', fn: () => entrarMina(0) });
  } else if (modo === 'mina') {
    const tx = Math.floor(c.x), ty = Math.floor(c.y), naEscada = Math.hypot(c.x - MINA_ESCADA - 0.5, c.y - MINA_ESCADA - 0.5) < 1.3;
    if (MINA.z === 0 && Math.hypot(c.x - 10.5, c.y - 10.5) < 2) a.push({ rotulo: '💰 Loja da mina', fn: () => abrirModal('loja_mina') });
    if (naEscada) {
      a.push({ rotulo: MINA.z === 0 ? '🌲 Subir pra floresta' : '🪜 Subir uma camada', fn: subir });
      if (MINA.z + 1 < MINA_CAMADAS && MINA.z + 1 <= rankAtual().camada_max) a.push({ rotulo: '🪜 Descer pela escada', fn: () => descer(true) });
    } else if (MINA.z + 1 < MINA_CAMADAS && MINA.cam[MINA.z + 1] && celula(MINA.z + 1, tx, ty) !== '.') {
      a.push(MINA.z + 1 <= rankAtual().camada_max ? { rotulo: '⬇️ Cavar pra baixo', fn: () => comecar({ tipo: 'bloco', z: MINA.z + 1, x: tx, y: ty, chao: true }) }
                                                  : { rotulo: `🔒 Camada ${MINA.z + 1}: precisa de rank`, fn: () => abrirModal('rank') });
    }
  } else if (modo === 'lotes') {
    if (Math.hypot(c.x - LT_PORTAL[0] - 0.5, c.y - LT_PORTAL[1] - 0.5) < 2.4) a.push({ rotulo: '🏙️ Voltar pra cidade', fn: () => sairParaCidade() });
    if (Math.hypot(c.x - LT_FEIRA[0] - 0.5, c.y - LT_FEIRA[1] - 0.5) < 2.4) a.push({ rotulo: '📋 Feira: o que os lotes vendem', fn: () => abrirModal('feira') });
    const balc = balcaoPerto(); if (balc) a.push({ rotulo: balc.dono === (V.EU && V.EU.morador) ? '🛒 Minha loja (pôr à venda)' : `🛒 Loja de ${balc.nome || 'lote ' + balc.id}`, fn: () => abrirLojaLote(balc.id) });
    const lp = loteProximo();
    if (lp && !lp.dono && !MEU_LOTE) a.push({ rotulo: `🏡 Pegar o lote ${lp.id} (grátis)`, fn: () => pegarLote(lp.id) });
    if (MEU_LOTE && (!lp || lp.id !== MEU_LOTE)) a.push({ rotulo: '🏡 Ir pro meu lote', fn: () => irProLote(MEU_LOTE) });
  }
  return a.slice(0, 3);
}
function loteProximo() {
  const c = V.ctrl, lt = loteEm(c.x, c.y); if (lt) return LOTES[lt.id - 1];
  for (const l of LOTES) { const [ox, oy] = origemLote(l.id); if (Math.hypot(ox + 8 - c.x, oy + LT + 0.9 - c.y) < 2.6) return l; }
  return null;
}
function balcaoPerto() {
  const c = V.ctrl;
  for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
    const x = Math.floor(c.x) + dx, y = Math.floor(c.y) + dy;
    if (blocoEm(x, y, 0) === 'balcao' && Math.hypot(x + 0.5 - c.x, y + 0.5 - c.y) < 2.2) return LOTES[loteEm(x, y).id - 1];
  }
  return null;
}
async function pegarLote(id) {
  const r = await rpc('pegar_lote', { p_token: tkn(), p_lote: id });
  if (!r || !r.ok) { som('erro'); return V.toast((r && r.erro) || 'Não deu'); }
  som('rankup'); V.toast(`🏡 O lote ${id} é seu! Crie blocos em 🔨 Criar → Construção e monte sua casa.`);
  await carregarLotes(); V.atualizarAcoes();
}
async function comer() {
  const it = itemNaMao(); if (!it) return;
  if (V.VIDA >= 100) return V.toast('Sua vida já está cheia');
  const r = await rpc('usar_item', { p_token: tkn(), p_slot: SEL });
  if (!r || !r.ok) return V.toast((r && r.erro) || 'Não deu');
  som('comer'); V.mudarVida(V.VIDA + r.cura); flutua(V.ctrl.x, V.ctrl.y - 1, `+${r.cura} ❤`, '#ff9aa8'); carregarJogo();
}

// ---------------------------------------------------------------------
// HUD: barra rápida, botão de ação, topo do jogo, dinheiro
// ---------------------------------------------------------------------
const DICA_CIDADE = $('#dicaTeclas') ? $('#dicaTeclas').innerHTML : '';
function mostrarHUD(sim) {
  const d = $('#dicaTeclas');
  if (d) d.innerHTML = sim ? '<kbd>WASD</kbd> andar · <kbd>E</kbd> segurar pra quebrar/atacar · <kbd>F</kbd> ação · <kbd>1</kbd>–<kbd>9</kbd> item · <kbd>I</kbd> mochila' : DICA_CIDADE;
  $('#jogoTopo').hidden = !sim; $('#hotbar').hidden = !V.EU; $('#btnAcao').hidden = !sim || !V.tocaTela;
  desenharBarra(); atualizarTopoJogo();
}
function desenharBarra() {
  const b = $('#hotbarSlots'); if (!b) return;
  b.innerHTML = Array.from({ length: 9 }, (_, i) => {
    const s = JOG.inv[i], info = s && ITENS[s.i];
    const dur = s && s.d != null && info && info.durabilidade ? `<i class="dur" style="width:${Math.round(100 * s.d / info.durabilidade)}%"></i>` : '';
    return `<button class="hs ${i === SEL ? 'sel' : ''}" data-i="${i}" title="${s ? esc(nomeItem(s.i)) : ''}">${s ? imgIcone(s.i) + (s.q > 1 ? `<b>${s.q}</b>` : '') + dur : ''}<small>${i + 1}</small></button>`;
  }).join('');
  b.querySelectorAll('.hs').forEach(x => x.onclick = () => { SEL = Number(x.dataset.i); desenharBarra(); V.atualizarAcoes(); });
}
function atualizarHUD() {
  const el = $('#vidaMoedas'); if (el) { const r = rankAtual(); el.innerHTML = `💰 ${fmtM(JOG.moedas)} · <span style="color:${r.cor}">${esc(r.nome)}</span>`; el.hidden = !CAT; }
}
function atualizarTopoJogo() {
  const el = $('#jogoTopoTxt'); if (!el || !modo) return;
  const bs = $('#btnSubir'), bd = $('#btnDescer');
  if (bs) { bs.hidden = modo !== 'mina'; bs.textContent = MINA.z === 0 ? '🌲 Sair' : '⬆️ Subir'; }
  if (bd) bd.hidden = modo !== 'mina' || MINA.z + 1 >= MINA_CAMADAS || MINA.z + 1 > rankAtual().camada_max;
  if (modo === 'explorar') {
    const b = { g: 'Planície', f: 'Floresta', t: 'Taiga', a: 'Deserto', p: 'Montanha', w: 'Água', c: 'Trilha' }[chaoEm(Math.floor(V.ctrl.x), Math.floor(V.ctrl.y))] || '';
    el.textContent = `🌲 Explorar · ${b}`;
  } else if (modo === 'lotes') {
    const lp = loteEm(V.ctrl.x, V.ctrl.y), l = lp && LOTES[lp.id - 1];
    el.textContent = l ? `🏡 Lote ${l.id} · ${l.dono ? (l.dono === (V.EU && V.EU.morador) ? 'seu lote' : 'de ' + (l.nome || '?')) : 'livre'}` : '🏡 Terrenos e Lotes';
  } else {
    const falta = Math.max(0, Math.round(((MINA.proxima || 0) - Date.now()) / 1000));
    el.textContent = `⛏️ Mina · Camada ${MINA.z} (−${MINA.z * 2} m) · regenera em ${Math.floor(falta / 60)}:${String(falta % 60).padStart(2, '0')}`;
  }
}

// ---------------------------------------------------------------------
// JANELA: inventário, criar, rank, ranking, lojas
// ---------------------------------------------------------------------
let modalAberto = null, slotSel = null;
async function abrirModal(aba) {
  if (!exigeLogin()) return;
  try { await carregarCatalogo(); } catch (e) { return V.toast('⚠️ ' + e.message); }
  modalAberto = aba; slotSel = null; $('#jogoModal').hidden = false; som('abrir');
  renderModal(); carregarJogo();
  if (aba === 'ranking') carregarRanking();
  if (aba === 'feira') carregarFeira();
  if (aba === 'lote') carregarLotes().then(() => modalAberto === 'lote' && renderModal());
}
function fecharModal() { modalAberto = null; $('#jogoModal').hidden = true; }
function renderModal() {
  const m = $('#jogoModalCorpo'); if (!m || !modalAberto) return;
  const abas = modalAberto.startsWith('loja') || modalAberto === 'feira' ? [] : [['inv', '🎒 Mochila'], ['criar', '🔨 Criar'], ['rank', '⭐ Rank'], ['ranking', '🏆 Ranking'], ['lote', '🏡 Lote']];
  $('#jogoModalAbas').innerHTML = abas.map(([k, t]) => `<button data-a="${k}" class="${k === modalAberto ? 'ativo' : ''}">${t}</button>`).join('');
  $('#jogoModalAbas').querySelectorAll('button').forEach(b => b.onclick = () => { modalAberto = b.dataset.a; slotSel = null; renderModal(); if (modalAberto === 'ranking') carregarRanking(); });
  $('#jogoModalTitulo').textContent = { inv: 'Inventário', criar: 'Criar itens', rank: 'Rank', ranking: 'Ranking da cidade', loja_mercado: '🛒 Mercadinho', loja_mina: '⛏️ Loja da mina', lote: 'Meu lote', feira: '📋 Feira dos lotes',
    loja_lote: LOJA && LOJA.nome ? '🛒 Loja de ' + LOJA.nome : '🛒 Loja' }[modalAberto];
  $('#jogoModalMoedas').textContent = '💰 ' + fmtM(JOG.moedas);
  if (modalAberto === 'inv') m.innerHTML = htmlInv(), ligarInv(m);
  else if (modalAberto === 'criar') m.innerHTML = htmlCriar(), ligarCriar(m);
  else if (modalAberto === 'rank') m.innerHTML = htmlRank(), ligarRank(m);
  else if (modalAberto === 'ranking') m.innerHTML = htmlRanking();
  else if (modalAberto === 'lote') m.innerHTML = htmlLote(), ligarLote(m);
  else if (modalAberto === 'feira') m.innerHTML = htmlFeira(), ligarFeira(m);
  else if (modalAberto === 'loja_lote') m.innerHTML = htmlLojaLote(), ligarLojaLote(m);
  else m.innerHTML = htmlLoja(modalAberto === 'loja_mina' ? 'mina' : 'mercado'), ligarLoja(m);
}
function slotHtml(i, extra = '') {
  const s = JOG.inv[i], info = s && ITENS[s.i];
  const dur = s && s.d != null && info && info.durabilidade ? `<i class="dur" style="width:${Math.round(100 * s.d / info.durabilidade)}%"></i>` : '';
  return `<button class="slot ${slotSel === i ? 'sel' : ''} ${extra}" data-s="${i}">${s ? imgIcone(s.i) + (s.q > 1 ? `<b>${s.q}</b>` : '') + dur : ''}</button>`;
}
function htmlInv() {
  const nomesArm = ['Capacete', 'Peitoral', 'Calça', 'Botas'], sel = slotSel != null && JOG.inv[slotSel], info = sel && ITENS[sel.i];
  return `<div class="inv-topo">
      <div class="inv-boneco"><canvas id="invBoneco" width="32" height="48"></canvas>
        <div class="inv-arm">${[36, 37, 38, 39].map((s, k) => `<div class="arm-linha">${slotHtml(s, 'arm')}<small>${nomesArm[k]}</small></div>`).join('')}</div></div>
      <div class="inv-info"><p>❤ Vida <b>${Math.round(V.VIDA)}%</b></p><p>🛡️ Defesa <b>${defesaTotal()}</b> <small>(−${Math.min(80, defesaTotal() * 4)}% de dano)</small></p>
        <p>⭐ ${esc(rankAtual().nome)}</p><p>💰 ${fmtM(JOG.moedas)}</p></div></div>
    <p class="mini">Mochila</p><div class="grade">${Array.from({ length: 27 }, (_, k) => slotHtml(9 + k)).join('')}</div>
    <p class="mini">Barra rápida <small>(1–9 no teclado)</small></p><div class="grade">${Array.from({ length: 9 }, (_, k) => slotHtml(k)).join('')}</div>
    <div class="inv-sel">${info ? `${imgIcone(sel.i)} <div><b>${esc(info.nome)}</b>${sel.q > 1 ? ' ×' + sel.q : ''}<br><small>${descricao(info, sel)}</small></div>
        <div class="inv-botoes">${info.tipo === 'comida' ? '<button class="btn btn-v" id="invComer">Comer</button>' : ''}<button class="btn" id="invFora">Jogar fora</button></div>`
      : '<small>Toque num item e depois em outro lugar pra mover. Armaduras vão nos espaços do boneco.</small>'}</div>`;
}
function descricao(info, s) {
  const p = [];
  if (info.ferramenta) p.push(`${info.ferramenta} nível ${info.nivel} · dano ${info.dano}`);
  if (info.tipo === 'armadura') p.push(`defesa ${info.defesa}`);
  if (info.cura) p.push(`recupera ${info.cura} de vida`);
  if (s.d != null && info.durabilidade) p.push(`durabilidade ${s.d}/${info.durabilidade}`);
  if (info.venda) p.push(`vale 💰${info.venda}`);
  return p.join(' · ');
}
function ligarInv(m) {
  const cv = m.querySelector('#invBoneco'); if (cv && V.EU) { const fo = folhaJogador(V.EU.morador, armadura(), false); if (fo) { const g = cv.getContext('2d'); g.imageSmoothingEnabled = false; g.drawImage(fo, 0, 0, 32, 48, 0, 0, 32, 48); } }
  m.querySelectorAll('.slot').forEach(b => b.onclick = async () => {
    const i = Number(b.dataset.s);
    if (slotSel == null) { if (JOG.inv[i]) { slotSel = i; renderModal(); } return; }
    if (slotSel === i) { slotSel = null; return renderModal(); }
    const de = slotSel; slotSel = null;
    const r = await rpc('mover_item', { p_token: tkn(), p_de: de, p_para: i });
    if (!r || !r.ok) V.toast((r && r.erro) || 'Não deu');
    await carregarJogo();
  });
  const c = m.querySelector('#invComer'); if (c) c.onclick = async () => { const s = slotSel; const r = await rpc('usar_item', { p_token: tkn(), p_slot: s }); if (!r || !r.ok) return V.toast((r && r.erro) || 'Não deu'); som('comer'); V.mudarVida(V.VIDA + r.cura); V.toast(`❤ +${r.cura} de vida`); await carregarJogo(); };
  const f = m.querySelector('#invFora'); if (f) f.onclick = async () => { if (!confirm('Jogar fora esse item? Ele some.')) return; const s = slotSel; slotSel = null; await rpc('descartar_item', { p_token: tkn(), p_slot: s }); await carregarJogo(); };
}
const conta = id => JOG.inv.reduce((a, s, i) => a + (s && s.i === id && i <= 35 ? s.q : 0), 0);
function htmlCriar() {
  const grupos = { basico: '🪵 Básico', construcao: '🧱 Construção (pro seu lote)', moveis: '🪑 Móveis e decoração', ferramentas: '⛏️ Ferramentas e armas', fornalha: '🔥 Fornalha (precisa de carvão)', armaduras: '🛡️ Armaduras', cozinha: '🍞 Cozinha' };
  let h = '';
  for (const [g, titulo] of Object.entries(grupos)) {
    const rs = RECEITAS.filter(r => r.grupo === g); if (!rs.length) continue;
    h += `<p class="mini">${titulo}</p><ul class="receitas">`;
    for (const r of rs) {
      const trava = JOG.rank < r.rank_min, ings = Object.entries(r.ingredientes), pode = !trava && ings.every(([i, n]) => conta(i) >= n);
      h += `<li class="${pode ? 'pode' : ''}">${imgIcone(r.resultado)}<div class="rc-txt"><b>${esc(nomeItem(r.resultado))}${r.qtd > 1 ? ' ×' + r.qtd : ''}</b>
        <span>${ings.map(([i, n]) => `<em class="${conta(i) >= n ? 'tem' : 'falta'}">${imgIcone(i)}${conta(i)}/${n}</em>`).join(' ')}</span></div>
        ${trava ? `<small class="trava">🔒 ${esc((RANKS[r.rank_min] || {}).nome || '')}</small>` : `<button class="btn btn-v" data-r="${r.id}" ${pode ? '' : 'disabled'}>Criar</button>`}</li>`;
    }
    h += '</ul>';
  }
  return h;
}
function ligarCriar(m) {
  m.querySelectorAll('[data-r]').forEach(b => b.onclick = async () => {
    b.disabled = true; const r = await rpc('craftar', { p_token: tkn(), p_receita: b.dataset.r, p_vezes: 1 });
    if (!r || !r.ok) { b.disabled = false; return V.toast((r && r.erro) || 'Não deu'); }
    som('criar'); V.toast(`🔨 Criou ${r.qtd > 1 ? r.qtd + ' ' : ''}${nomeItem(r.item)}`); await carregarJogo();
  });
}
function htmlRank() {
  const r = rankAtual(), prox = RANKS[JOG.rank + 1];
  return `<div class="rank-atual" style="border-color:${r.cor}"><b style="color:${r.cor}">⭐ ${esc(r.nome)}</b><br><small>Mina até a camada ${r.camada_max} · bônus de venda +${r.bonus_venda}%</small></div>
    ${prox ? `<p>Próximo: <b style="color:${prox.cor}">${esc(prox.nome)}</b> por <b>💰 ${fmtM(prox.custo)}</b></p>
      <div class="marco-barra rank-barra"><div class="marco-enche" style="width:${clamp(100 * JOG.moedas / prox.custo, 2, 100)}%"></div></div>
      <ul class="lista-rank"><li>⛏️ Mina até a camada ${prox.camada_max}</li><li>💰 Vende ${prox.bonus_venda}% mais caro</li><li>🔨 Libera receitas novas</li></ul>
      <div class="botoes"><button class="btn btn-p btn-larga" id="btnRankup" ${JOG.moedas >= prox.custo ? '' : 'disabled'}>Subir pra ${esc(prox.nome)}</button></div>`
      : '<p>Você está no rank máximo! 👑</p>'}
    <p class="mini">Ranks (${JOG.rank + 1} de ${RANKS.length})</p><ul class="lista-rank">${RANKS.slice(Math.max(0, JOG.rank - 2), JOG.rank + 9).map(k => `<li style="color:${k.cor}">${k.nivel <= JOG.rank ? '✅' : '🔒'} <b>${esc(k.nome)}</b> — 💰 ${fmtM(k.custo)} · camada ${k.camada_max} · +${k.bonus_venda}%</li>`).join('')}${JOG.rank + 9 < RANKS.length ? `<li>… até o rank ${RANKS.length}: <b>${esc(RANKS[RANKS.length - 1].nome)}</b> 👑</li>` : ''}</ul>`;
}
function ligarRank(m) {
  const b = m.querySelector('#btnRankup'); if (b) b.onclick = async () => {
    b.disabled = true; const r = await rpc('rankup', { p_token: tkn() });
    if (!r || !r.ok) { b.disabled = false; return V.toast((r && r.erro) || 'Não deu'); }
    som('rankup'); V.toast(`⭐ Agora você é ${r.nome}!`); await carregarJogo();
  };
}
let RANKING = null;
async function carregarRanking() { RANKING = await rpc('ranking', {}); if (modalAberto === 'ranking') renderModal(); }
function htmlRanking() {
  if (!RANKING) return '<p class="vazio">Carregando…</p>';
  const linha = (x, i, v) => `<li><span class="pos">${['🥇', '🥈', '🥉'][i] || i + 1 + 'º'}</span> <b>${esc(x.nome)}</b> <small>${esc((RANKS[x.rank] || {}).nome || '')}</small><span class="val">${v}</span></li>`;
  return `<p class="mini">💰 Mais ricos</p><ol class="ranking">${RANKING.ricos.map((x, i) => linha(x, i, '💰 ' + fmtM(x.moedas))).join('') || '<li class="vazio">Ninguém ainda</li>'}</ol>
    <p class="mini">⭐ Maiores ranks</p><ol class="ranking">${RANKING.ranks.map((x, i) => linha(x, i, '⭐ ' + esc((RANKS[x.rank] || {}).nome || ''))).join('') || '<li class="vazio">Ninguém subiu de rank ainda</li>'}</ol>`;
}
// ---------------- meu lote ----------------
function htmlLote() {
  if (!LOTES.length) return '<p class="vazio">Os Terrenos e Lotes ficam ao lado do portal da cidade (arco 🏡).</p>';
  const livres = LOTES.filter(l => !l.dono).length;
  if (!MEU_LOTE) return `<div class="rank-atual" style="border-color:#40a456"><b>🏡 Você ainda não tem lote</b><br><small>${livres} de ${LOTES.length} lotes livres. Cada pessoa pega 1, de graça.</small></div>
    <p>Vá nos <b>Terrenos e Lotes</b> (arco ao lado do portal, na cidade), ande até uma placa verde <b>LIVRE</b> e toque em <b>Pegar o lote</b>.</p>
    <div class="botoes"><button class="btn btn-v btn-larga" id="btnIrLotes">🏡 Ir pros Terrenos e Lotes</button></div>`;
  const qtd = (LBLOCOS.get(MEU_LOTE) || new Map()).size;
  return `<div class="rank-atual" style="border-color:#f6c836"><b>🏡 Lote nº ${MEU_LOTE}</b><br><small>16 × 16 blocos · até 4 de altura${qtd ? ` · ${qtd} blocos colocados` : ''}</small></div>
    <ul class="lista-rank"><li>🔨 Crie blocos em <b>Criar → Construção</b> (paredes, vidro, telhado, pisos) e <b>Móveis</b>.</li>
      <li>🧱 Ponha o bloco na barra rápida, segure ele e toque no chão do seu lote (no PC: mouse + clique ou <kbd>E</kbd>).</li>
      <li>⛏️ Pra tirar um bloco: fique com a mão vazia (ou uma ferramenta) e toque nele. Ele volta pra mochila.</li>
      <li>🛒 Coloque um <b>Balcão de loja</b> e venda suas coisas pros outros pelo preço que quiser.</li></ul>
    <div class="botoes"><button class="btn btn-v btn-flex" id="btnIrLote">🚶 Ir pro meu lote</button><button class="btn btn-flex" id="btnLargar">Largar o lote</button></div>`;
}
function ligarLote(m) {
  const ir = m.querySelector('#btnIrLotes'); if (ir) ir.onclick = () => { fecharModal(); entrarLotes(); };
  const il = m.querySelector('#btnIrLote'); if (il) il.onclick = async () => { fecharModal(); if (modo !== 'lotes') await entrarLotes(); irProLote(MEU_LOTE); };
  const lg = m.querySelector('#btnLargar'); if (lg) lg.onclick = async () => {
    if (!confirm('Largar o seu lote? Ele fica livre pra outra pessoa pegar.')) return;
    const r = await rpc('largar_lote', { p_token: tkn() }); if (!r || !r.ok) { som('erro'); return V.toast((r && r.erro) || 'Não deu'); }
    V.toast('Lote largado.'); await carregarLotes(); renderModal();
  };
}
// ---------------- feira (tudo que os lotes vendem) ----------------
let FEIRA = null;
async function carregarFeira() { FEIRA = await rpc('feira', {}); if (modalAberto === 'feira') renderModal(); }
function htmlFeira() {
  if (!Array.isArray(FEIRA)) return '<p class="vazio">Carregando…</p>';
  if (!FEIRA.length) return '<p class="vazio">Ninguém está vendendo nada ainda. Coloque um 🛒 Balcão de loja no seu lote e seja o primeiro!</p>';
  return `<p class="mini">Toque em "Ir até lá" pra ir até a loja e comprar.</p><ul class="receitas">${FEIRA.map(o => {
    const info = ITENS[o.item] || {};
    return `<li>${imgIcone(o.item)}<div class="rc-txt"><b>${esc(info.nome || o.item)}</b> <small>×${o.qtd}${o.dur != null && info.durabilidade ? ` · ${o.dur}/${info.durabilidade}` : ''}</small>
      <span>💰 ${fmtM(o.preco)} cada · Lote ${o.lote} · ${esc(o.nome || '')}</span></div><button class="btn btn-v" data-ir="${o.lote}">Ir até lá</button></li>`; }).join('')}</ul>`;
}
function ligarFeira(m) {
  m.querySelectorAll('[data-ir]').forEach(b => b.onclick = async () => { const id = Number(b.dataset.ir); fecharModal(); if (modo !== 'lotes') await entrarLotes(); irProLote(id); });
}
// ---------------- loja de um lote ----------------
let LOJA = null, lojaLoteId = null, formVenda = { slot: null, qtd: 1, preco: 10 };
async function abrirLojaLote(id) { lojaLoteId = id; LOJA = null; formVenda = { slot: null, qtd: 1, preco: 10 }; await abrirModal('loja_lote'); carregarLoja(); }
async function carregarLoja() { LOJA = await rpc('loja_ofertas', { p_lote: lojaLoteId }); if (modalAberto === 'loja_lote') renderModal(); }
function htmlLojaLote() {
  if (!LOJA || !LOJA.ofertas) return '<p class="vazio">Carregando…</p>';
  const dono = V.EU && LOJA.dono === V.EU.morador;
  const lista = LOJA.ofertas.map(o => {
    const info = ITENS[o.item] || {};
    const botoes = dono ? `<button class="btn" data-tirar="${o.id}">Tirar</button>`
      : `<button class="btn" data-comprar="${o.id}" data-q="1">Comprar 💰${fmtM(o.preco)}</button>${o.qtd > 1 ? `<button class="btn btn-v" data-comprar="${o.id}" data-q="${o.qtd}">Tudo 💰${fmtM(o.preco * o.qtd)}</button>` : ''}`;
    return `<li>${imgIcone(o.item)}<div class="rc-txt"><b>${esc(info.nome || o.item)}</b> <small>×${o.qtd}</small><span>💰 ${fmtM(o.preco)} cada${o.dur != null && info.durabilidade ? ` · durabilidade ${o.dur}/${info.durabilidade}` : ''}</span></div>${botoes}</li>`;
  }).join('') || `<li class="vazio">${dono ? 'Sua loja está vazia. Escolha um item aqui embaixo pra vender.' : 'Essa loja está vazia agora.'}</li>`;
  let h = `<ul class="receitas">${lista}</ul>`;
  if (dono) {
    const s = formVenda.slot != null && JOG.inv[formVenda.slot], info = s && ITENS[s.i];
    h += `<p class="mini">Pôr à venda (até 12 coisas). O dinheiro de cada venda vai direto pra você.</p>
      <div class="grade">${Array.from({ length: 36 }, (_, k) => slotHtml(k, formVenda.slot === k ? 'sel' : '')).join('')}</div>
      <div class="inv-sel">${info ? `${imgIcone(s.i)}<div><b>${esc(info.nome)}</b><br>
        <label>Qtd <input id="fvQtd" type="number" min="1" max="${s.q}" value="${Math.min(formVenda.qtd, s.q)}" ${s.d != null ? 'disabled' : ''} style="width:60px"></label>
        <label>Preço cada 💰 <input id="fvPreco" type="number" min="1" max="1000000" value="${formVenda.preco}" style="width:80px"></label></div>
        <div class="inv-botoes"><button class="btn btn-v" id="fvPor">Pôr</button></div>` : '<small>Toque num item da sua mochila.</small>'}</div>`;
  }
  return h;
}
function ligarLojaLote(m) {
  m.querySelectorAll('[data-comprar]').forEach(b => b.onclick = async () => {
    b.disabled = true; const r = await rpc('loja_comprar', { p_token: tkn(), p_oferta: Number(b.dataset.comprar), p_qtd: Number(b.dataset.q) });
    if (!r || !r.ok) { b.disabled = false; som('erro'); V.toast((r && r.erro) || 'Não deu'); return carregarLoja(); }
    som('moeda'); V.toast(`🛒 Comprado por 💰${fmtM(r.pagou)}`); await carregarJogo(); carregarLoja();
  });
  m.querySelectorAll('[data-tirar]').forEach(b => b.onclick = async () => {
    b.disabled = true; const r = await rpc('loja_tirar', { p_token: tkn(), p_oferta: Number(b.dataset.tirar) });
    if (!r || !r.ok) { b.disabled = false; som('erro'); return V.toast((r && r.erro) || 'Não deu'); }
    som('pegar'); await carregarJogo(); carregarLoja();
  });
  m.querySelectorAll('.slot').forEach(b => b.onclick = () => {
    const i = Number(b.dataset.s); if (!JOG.inv[i]) return;
    const info = ITENS[JOG.inv[i].i] || {};
    formVenda = { slot: i, qtd: JOG.inv[i].q, preco: Math.max(1, (info.venda || 1) * 2) }; renderModal();
  });
  const q = m.querySelector('#fvQtd'), p = m.querySelector('#fvPreco');
  if (q) q.oninput = () => { formVenda.qtd = Number(q.value) || 1; };
  if (p) p.oninput = () => { formVenda.preco = Number(p.value) || 1; };
  const por = m.querySelector('#fvPor'); if (por) por.onclick = async () => {
    por.disabled = true;
    const r = await rpc('loja_por', { p_token: tkn(), p_slot: formVenda.slot, p_qtd: formVenda.qtd, p_preco: formVenda.preco });
    if (!r || !r.ok) { por.disabled = false; som('erro'); return V.toast((r && r.erro) || 'Não deu'); }
    som('moeda'); V.toast('🛒 Posto à venda!'); formVenda = { slot: null, qtd: 1, preco: 10 }; await carregarJogo(); carregarLoja(); carregarLotes();
  };
}
let abaLoja = 'vender';
function htmlLoja(loja) {
  const bonus = rankAtual().bonus_venda, agreg = new Map();
  JOG.inv.forEach((s, i) => { if (!s || i > 35) return; const info = ITENS[s.i]; if (!info || !info.venda || (loja === 'mina' && !info.mina)) return; agreg.set(s.i, (agreg.get(s.i) || 0) + s.q); });
  const vendaHtml = [...agreg].map(([id, n]) => {
    const info = ITENS[id], preco = Math.floor(info.venda * (100 + bonus) / 100), unico = info.durabilidade > 0;
    return `<li>${imgIcone(id)}<div class="rc-txt"><b>${esc(info.nome)}</b> <small>×${n}</small><span>💰 ${preco} cada${bonus ? ` <em class="tem">(+${bonus}%)</em>` : ''}${unico ? ' (gasto vale menos)' : ''}</span></div>
      <button class="btn" data-v="${id}" data-q="1">Vender 1</button>${!unico && n > 1 ? `<button class="btn btn-v" data-v="${id}" data-q="${n}">Tudo 💰${preco * n}</button>` : ''}</li>`;
  }).join('') || `<li class="vazio">Você não tem nada que ${loja === 'mina' ? 'a loja da mina compra (minérios, carvão, pedra…)' : 'o mercadinho compre'}.</li>`;
  const compraHtml = Object.values(ITENS).filter(i => i.compra != null).map(i => `<li>${imgIcone(i.id)}<div class="rc-txt"><b>${esc(i.nome)}</b><span>💰 ${i.compra}${i.cura ? ` · cura ${i.cura}` : ''}</span></div>
      <button class="btn" data-c="${i.id}" data-q="1">Comprar 1</button><button class="btn" data-c="${i.id}" data-q="5">×5 💰${i.compra * 5}</button></li>`).join('');
  const abas = loja === 'mercado' ? `<div class="abas"><button data-l="vender" class="${abaLoja === 'vender' ? 'ativo' : ''}">Vender</button><button data-l="comprar" class="${abaLoja === 'comprar' ? 'ativo' : ''}">Comprar</button></div>` : '';
  return `${abas}<p class="mini">${loja === 'mina' ? 'O mineiro compra tudo que sai da mina.' : 'O mercadinho compra quase tudo e vende comida e madeira.'} Seu rank dá +${bonus}% na venda.</p>
    <ul class="receitas">${loja === 'mina' || abaLoja === 'vender' ? vendaHtml : compraHtml}</ul>`;
}
function ligarLoja(m) {
  m.querySelectorAll('[data-l]').forEach(b => b.onclick = () => { abaLoja = b.dataset.l; renderModal(); });
  m.querySelectorAll('[data-v]').forEach(b => b.onclick = async () => {
    b.disabled = true; const r = await rpc('vender', { p_token: tkn(), p_item: b.dataset.v, p_qtd: Number(b.dataset.q), p_loja: modalAberto === 'loja_mina' ? 'mina' : 'mercado' });
    if (!r || !r.ok) { b.disabled = false; return V.toast((r && r.erro) || 'Não deu'); }
    som('moeda'); V.toast(`💰 +${r.ganhou} moedas`); await carregarJogo();
  });
  m.querySelectorAll('[data-c]').forEach(b => b.onclick = async () => {
    b.disabled = true; const r = await rpc('comprar', { p_token: tkn(), p_item: b.dataset.c, p_qtd: Number(b.dataset.q) });
    if (!r || !r.ok) { b.disabled = false; return V.toast((r && r.erro) || 'Não deu'); }
    som('moeda'); V.toast('🛒 Comprado!'); await carregarJogo();
  });
}

// ---------------------------------------------------------------------
// eventos de outros jogadores (quebrou árvore, minerou bloco)
// ---------------------------------------------------------------------
function evento(p) {
  if (p.ev === 'quebra') QUEBRADOS.add(p.id);
  else if (p.ev === 'minera') marcarMinerado(p.z, p.x, p.y);
  else if (p.ev === 'constroi' && LBLOCOS.has(p.lote)) { const m = LBLOCOS.get(p.lote), k = p.x + ',' + p.y + ',' + p.z; if (p.t) m.set(k, p.t); else m.delete(k); }
}
function payload() {
  return { m: V.EU.morador, x: Math.round(V.ctrl.x * 100) / 100, y: Math.round(V.ctrl.y * 100) / 100, dir: V.ctrl.dir, anda: V.ctrl.anda,
           dentro: true, w: modo === 'explorar' ? 'x' : modo === 'lotes' ? 'l' : 'm' + MINA.z, arm: armadura() };
}

// ---------------------------------------------------------------------
// botões da tela
// ---------------------------------------------------------------------
$('#btnInv').onclick = () => modalAberto ? fecharModal() : abrirModal('inv');
$('#jogoModalFechar').onclick = fecharModal;
$('#btnCidade').onclick = () => sairParaCidade();
$('#btnSubir').onclick = () => subir();
$('#btnDescer').onclick = () => descer(true);
(() => {                                   // botão de ação (celular): segura pra quebrar
  const b = $('#btnAcao'); let seg = null;
  const ir = () => { if (!acao && !pendente) apertarAcao(); };
  b.addEventListener('pointerdown', e => { e.preventDefault(); ir(); seg = setInterval(ir, 250); });
  const solta = () => { clearInterval(seg); seg = null; };
  b.addEventListener('pointerup', solta); b.addEventListener('pointercancel', solta); b.addEventListener('pointerleave', solta);
})();
// quando entra/sai da conta: carrega o jogo e mostra a barra
let ultimoEU = null;
setInterval(() => {
  const eu = V.EU ? V.EU.morador : null;
  if (eu !== ultimoEU) { ultimoEU = eu; if (eu) carregarCatalogo().then(carregarJogo).catch(() => {}); $('#hotbar').hidden = !eu; if (!eu && modo) sairParaCidade(); }
}, 800);

window.Jogo = {
  ativo: () => !!modo, desenhar, mover, tocar, acoes, acoesCidade, desenharNaCidade, tocarNaCidade, sairParaCidade,
  abrirLoja: loja => abrirModal(loja === 'mina' ? 'loja_mina' : 'loja_mercado'), evento, payload, armadura,
  // pra testar no servidor local (?debug)
  _debug: { entrarExplorar, entrarMina, entrarLotes, irProLote, pegarLote, construirAqui, planoNoTile, abrirLojaLote, abrirModal, subir, descer,
            get JOG() { return JOG; }, get modo() { return modo; }, get MEU_LOTE() { return MEU_LOTE; }, get MINA() { return MINA; }, ctrl: V.ctrl,
            set SEL(v) { SEL = v; desenharBarra(); } },
};
})();
