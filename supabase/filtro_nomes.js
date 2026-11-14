// Mesma regra da função nome_permitido() do banco (1_criar_banco.sql).
const DE = 'áàâãäéêëíïóôõöúüç@43105$7*', PARA = 'aaaaaeeeiioooouuc' + 'aaeiosstu';

function normalizar(t) {
  return [...String(t || '').toLowerCase()].map(c => { const i = DE.indexOf(c); return i >= 0 ? PARA[i] : c; }).join('')
    .replace(/(.)\1+/g, '$1');
}

function criarFiltro(lista) {
  const curtas = [], longas = [];
  for (const w of lista) {
    const igual = w.startsWith('='), p = (igual ? w.slice(1) : w).replace(/(.)\1+/g, '$1');
    if (igual || p.replace(/ /g, '').length <= 4) curtas.push({ p, re: new RegExp('(^|[^a-z])' + p.replace(/[^a-z ]/g, '') + '([^a-z]|$)') });
    else longas.push(p.replace(/ /g, ''));
  }
  return function permitido(texto) {
    const s = normalizar(texto), junto = s.replace(/[^a-z]/g, '');
    const tokens = s.split(/\s+/).map(x => x.replace(/[^a-z]/g, ''));     // "p.u.t.a" -> "puta"
    return !curtas.some(c => c.re.test(s) || tokens.includes(c.p) || junto === c.p) && !longas.some(p => junto.includes(p));
  };
}

module.exports = { normalizar, criarFiltro };
