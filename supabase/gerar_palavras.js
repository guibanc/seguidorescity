// =====================================================================
//  Gera a lista de nomes proibidos (palavrões, ofensas, termos pejorativos)
//    npm install        (1 vez)
//    npm run palavras
//  Fontes:
//   - biblioteca "naughty-words" (LDNOOBW — List of Dirty, Naughty, Obscene
//     and Otherwise Bad Words, CC-BY-4.0): listas pt e en
//   - lista própria abaixo (gírias e ofensas brasileiras que faltam lá)
//  Saídas:
//   - supabase/2_palavras_bloqueadas.sql  -> rodar no SQL Editor do Supabase
//   - supabase/palavras_bloqueadas.json   -> usada pelo servidor_local.js
//
//  Regra de busca (igual no banco e no servidor local):
//   - palavras com até 4 letras, ou que começam com "=", só contam como
//     palavra inteira  ("cu" não barra "Marcus", "=bicha" não barra "Bichara")
//   - o resto conta em qualquer lugar, ignorando acento, pontos, espaços,
//     números no lugar de letras e letras repetidas (p.u.t.a, puuuta, put4)
// =====================================================================
const fs = require('fs'), path = require('path');
const nw = require('naughty-words');
const { normalizar } = require('./filtro_nomes.js');

const PROPRIA = `
porra caralho merda bosta cacete foder fodase fodido fodida desgraca desgracado desgracada
puta puto putinha putaria puteiro fdp pqp vsf tnc vtnc krl crl cu cuzao cuzinho
arrombado arrombada filhodaputa escroto escrota babaca otario otaria imbecil idiota
retardado retardada mongoloide debilmental lixohumano corno chifrudo bostinha merdinha
buceta boceta xoxota xereca xavasca piroca pica rola =pau punheta punheteiro siririca gozada gozar
boquete chupeta safada safado vadia vagabunda vagabundo piranha prostituta rapariga quenga
porno putona sexo anal estupro estuprador estupradora pedofilo pedofilia
viado viadinho veado =bicha bichinha boiola baitola sapatao traveco travecao macaco macaca
crioulo crioula tiziu negrinho neguinho macumbeiro favelado judeusafado
nazi nazista hitler kkk aleijado mongol
`.split(/\s+/).filter(Boolean);

// da biblioteca, o que NÃO é ofensa (palavra comum, sobrenome ou termo de identidade — não discriminamos)
const EXCECOES = new Set([
  'amador', 'aranha', 'ariano', 'bissexual', 'bumbum', 'cerveja', 'comer', 'consolo', 'dum raio', 'frango assado',
  'grelho', 'heroina', 'heterosexual', 'homem gay', 'homosexual', 'homoerotico', 'inferno', 'lesbica', 'mama',
  'passar um cheque', 'saco', 'torneira', 'aborto', 'camisinha', 'cocaina', 'fecal', 'pinto', 'burro', 'balalao',
  'bicha', 'pau', 'sexual', 'gay', 'lesbian', 'bisexual', 'homosexual', 'heterosexual', 'transsexual', 'queer', 'jesus',
]);

const lista = new Set();
const daBiblioteca = new Set([...nw.pt, ...nw.en]);
for (const w of [...daBiblioteca, ...PROPRIA]) {
  const igual = w.startsWith('=');
  let n = normalizar(igual ? w.slice(1) : w).replace(/[^a-z ]/g, '').trim();
  if (!n || (daBiblioteca.has(w) && EXCECOES.has(n))) continue;   // exceções valem só pra biblioteca
  // juntando letras repetidas, "xxx" vira "x", "ass" vira "as", "kkk" vira "k": barraria nomes normais
  if (n.replace(/(.)\1+/g, '$1').replace(/ /g, '').length <= 2 && n !== 'cu') continue;
  if (!igual && n.replace(/ /g, '').length > 4) n = n.replace(/ /g, '');   // busca "colada"
  lista.add((igual ? '=' : '') + n);
}
const ord = [...lista].sort();
const sqlStr = s => "'" + s.replace(/'/g, "''") + "'";
fs.writeFileSync(path.join(__dirname, 'palavras_bloqueadas.json'), JSON.stringify(ord, null, 0));
fs.writeFileSync(path.join(__dirname, '2_palavras_bloqueadas.sql'),
  `-- Nomes proibidos (${ord.length} palavras). Gerado por supabase/gerar_palavras.js — não edite à mão.\n` +
  `-- Fonte: naughty-words (LDNOOBW, CC-BY-4.0) + lista própria. Pode rodar de novo à vontade.\n` +
  `delete from palavras_bloqueadas;\ninsert into palavras_bloqueadas (p) values\n` +
  ord.map(w => `(${sqlStr(w)})`).join(',\n') + `\non conflict do nothing;\n`);
console.log('ok:', ord.length, 'palavras');
