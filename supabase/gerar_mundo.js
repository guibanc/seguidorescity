// =====================================================================
//  Gera o mundo do modo EXPLORAR (sempre igual pra mesma semente):
//    node supabase/gerar_mundo.js
//  Saídas:
//    site/dados/mundo.json           -> o site desenha o chão e os objetos
//    supabase/9_mundo_explorar.sql   -> o banco sabe o que existe em cada lugar
//  Biomas: planície, floresta, taiga (pinheiros), deserto, montanha, lagos com praia.
// =====================================================================
const fs = require('fs'), path = require('path');
const SEMENTE = 20261117, N = 128, CX = 64, CY = 64;

function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const hash = (x, y, s) => { let h = Math.imul(x, 374761393) + Math.imul(y, 668265263) + Math.imul(s, 2147483647); h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
// ruído suave em camadas
function ruido(x, y, escala, s, oitavas = 4) {
  let soma = 0, amp = 1, tot = 0, f = 1 / escala;
  for (let o = 0; o < oitavas; o++) {
    const X = x * f, Y = y * f, x0 = Math.floor(X), y0 = Math.floor(Y), fx = X - x0, fy = Y - y0;
    const sm = t => t * t * (3 - 2 * t), a = hash(x0, y0, s + o), b = hash(x0 + 1, y0, s + o), c = hash(x0, y0 + 1, s + o), d = hash(x0 + 1, y0 + 1, s + o);
    const v = (a + (b - a) * sm(fx)) * (1 - sm(fy)) + (c + (d - c) * sm(fx)) * sm(fy);
    soma += v * amp; tot += amp; amp *= 0.5; f *= 2;
  }
  return soma / tot;
}

// ---------- chão ----------
// g planície · f floresta · t taiga · a areia (deserto/praia) · p pedra (montanha) · w água · c caminho
const chao = [];
for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
  const dc = Math.hypot(x - CX, y - CY);
  let E = ruido(x, y, 26, SEMENTE), T = ruido(x, y, 48, SEMENTE + 77), U = ruido(x, y, 36, SEMENTE + 155);
  const borda = Math.min(x, y, N - 1 - x, N - 1 - y);
  if (borda < 6) E -= (6 - borda) * 0.06;                     // o mundo termina em água
  if (dc < 12) E = Math.max(E, 0.45 + (12 - dc) * 0.01);      // ilha segura no centro
  let t;
  if (E < 0.33) t = 'w';
  else if (E < 0.37) t = 'a';
  else if (E > 0.64 && dc > 14) t = 'p';
  else if (dc < 9) t = 'g';
  else if (T < 0.38) t = 't';
  else if (T > 0.56 && U < 0.52) t = 'a';
  else if (U > 0.55) t = 'f';
  else t = 'g';
  chao.push(t);
}
// caminho de terra do centro até a entrada da mina e pras 4 direções curtas
const MINA = [CX + 6, CY], PORTAL = [CX, CY - 4];
for (let x = CX; x <= MINA[0]; x++) chao[CY * N + x] = 'c';
for (let y = PORTAL[1]; y <= CY; y++) chao[y * N + CX] = 'c';

// ---------- objetos ----------
const TABELA = {
  f: [['carvalho', 0.20], ['arbusto', 0.05], ['capim', 0.05]],
  g: [['carvalho', 0.025], ['arbusto', 0.035], ['capim', 0.13], ['rocha', 0.008]],
  t: [['pinheiro', 0.17], ['rocha', 0.03], ['arbusto', 0.02], ['capim', 0.03]],
  a: [['cacto', 0.045], ['rocha', 0.012], ['palmeira', 0.012]],
  p: [['rocha', 0.15], ['rocha_carvao', 0.045], ['rocha_ferro', 0.02]],
};
const objs = []; let id = 1;
for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) {
  const t = chao[y * N + x], dc = Math.hypot(x - CX, y - CY);
  if (dc < 8 || t === 'w' || t === 'c') continue;
  const lista = TABELA[t]; if (!lista) continue;
  const r = hash(x, y, SEMENTE + 999); let acc = 0;
  for (const [tipo, p] of lista) {
    acc += p;
    if (r < acc) {
      // palmeira só perto de água
      if (tipo === 'palmeira' && ![[1, 0], [-1, 0], [0, 1], [0, -1], [2, 0], [0, 2]].some(([dx, dy]) => chao[(y + dy) * N + x + dx] === 'w')) break;
      objs.push([id++, x, y, tipo]); break;
    }
  }
}

const mundo = { versao: 1, semente: SEMENTE, w: N, h: N, chao: chao.join(''), spawn: [CX, CY + 2], portal: PORTAL, mina: MINA, objs };
const raiz = path.join(__dirname, '..');
fs.writeFileSync(path.join(raiz, 'site/dados/mundo.json'), JSON.stringify(mundo));
const linhas = objs.map(([i, x, y, t]) => `(${i},${x},${y},'${t}')`);
fs.writeFileSync(path.join(raiz, 'supabase/9_mundo_explorar.sql'),
  `-- Objetos do mundo do EXPLORAR (${objs.length}). Gerado por supabase/gerar_mundo.js — não edite à mão.\n` +
  `-- Pode rodar de novo à vontade (atualiza sem perder o que já foi quebrado).\n` +
  `insert into mundo_obj (id, x, y, tipo) values\n${linhas.join(',\n')}\n` +
  `on conflict (id) do update set x = excluded.x, y = excluded.y, tipo = excluded.tipo;\n` +
  `delete from mundo_obj where id > ${objs.length};\n`);
const cont = {}; for (const o of objs) cont[o[3]] = (cont[o[3]] || 0) + 1;
const bio = {}; for (const c of chao) bio[c] = (bio[c] || 0) + 1;
console.log('objetos:', objs.length, JSON.stringify(cont)); console.log('chão:', JSON.stringify(bio));
