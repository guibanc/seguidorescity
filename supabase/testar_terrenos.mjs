// Testa TERRENOS E LOTES + lojas dos jogadores num Postgres local (PGlite).
//   node supabase/testar_terrenos.mjs
import { PGlite } from '@electric-sql/pglite';
import { pgcrypto } from '@electric-sql/pglite/contrib/pgcrypto';
import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
const R = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const db = await PGlite.create({ extensions: { pgcrypto } });
await db.exec(`create schema if not exists extensions; create extension if not exists pgcrypto with schema extensions;
  do $$ begin create role anon; exception when duplicate_object then null; end $$;
  do $$ begin create role authenticated; exception when duplicate_object then null; end $$;
  create publication supabase_realtime;`);
for (const f of ['1_criar_banco.sql', '2_palavras_bloqueadas.sql', '3_contador.sql', '5_bio_e_pedidos.sql', '6_chat_online_casa.sql', '7_32bits_eleicao.sql', '8_jogo.sql', '9_mundo_explorar.sql', '11_terrenos.sql'])
  await db.exec(fs.readFileSync(path.join(R, 'supabase', f), 'utf8'));
// rodar de novo tem que funcionar (o usuário roda o 8 de novo e depois o 11)
await db.exec(fs.readFileSync(path.join(R, 'supabase', '8_jogo.sql'), 'utf8'));
await db.exec(fs.readFileSync(path.join(R, 'supabase', '11_terrenos.sql'), 'utf8'));
await db.exec(fs.readFileSync(path.join(R, 'site/dados/novos_moradores.sql'), 'utf8'));
const q1 = async (s, p) => (await db.query(s, p)).rows[0];
const rpc = async (fn, args) => (await q1(`select ${fn}(${args.map((_, i) => '$' + (i + 1)).join(',')}) r`, args)).r;
let falhas = 0; const ok = (cond, msg, extra) => { console.log((cond ? '  ✓ ' : '  ✗ ') + msg + (extra ? '  ' + JSON.stringify(extra) : '')); if (!cond) falhas++; };
const inv = async tk => (await rpc('meu_jogo', [tk])).inv;
const conta = async (tk, item) => (await inv(tk)).filter(s => s.i === item).reduce((a, s) => a + s.q, 0);
const slotDe = async (tk, item) => ((await inv(tk)).find(s => s.i === item) || {}).s;

const tk = (await rpc('registrar', [205, 'gui', 'Gui', '583920', null])).token;
const tk2 = (await rpc('registrar', [206, 'ana', 'Ana', '583921', null])).token;

console.log('ranks');
const cat = await rpc('jogo_catalogo', []);
ok(cat.ranks.length === 40 && cat.ranks[39].nome === 'Dono da Cidade', '40 ranks', { ultimo: cat.ranks[39] });
ok(cat.ranks.every((r, i) => i === 0 || r.custo > cat.ranks[i - 1].custo), 'cada rank custa mais que o anterior', cat.ranks.slice(0, 6).map(r => r.custo));
ok(cat.ranks[0].camada_max === 3 && cat.ranks[32].camada_max === 11, 'mina libera camadas aos poucos (3 → 11)');
ok(cat.itens.find(i => i.id === 'vidro').forma === 'cubo', 'itens de construção no catálogo');

console.log('lotes');
let r = await rpc('pegar_lote', [tk, 5]); ok(r.ok, 'pega o lote 5 de graça', r);
r = await rpc('pegar_lote', [tk, 6]); ok(!r.ok, 'só 1 lote por pessoa', r.erro);
r = await rpc('pegar_lote', [tk2, 5]); ok(!r.ok, 'lote com dono não pode ser pego', r.erro);
r = await rpc('pegar_lote', [tk2, 6]); ok(r.ok, 'a Ana pega o lote 6');
const lista = await rpc('lotes_lista', []); ok(lista.length === 64 && lista[4].nome === 'Gui', 'lista dos lotes com o nome do dono', lista[4]);

console.log('construir');
await db.exec(`select jogo_add(205, 'parede_madeira', 10); select jogo_add(205, 'piso_madeira', 4); select jogo_add(205, 'mesa', 1);`);
await rpc('mover_item', [tk, await slotDe(tk, 'parede_madeira'), 0]);
await rpc('mover_item', [tk, await slotDe(tk, 'piso_madeira'), 1]);
await rpc('mover_item', [tk, await slotDe(tk, 'mesa'), 2]);
r = await rpc('construir', [tk, 5, 3, 3, 0, 0]); ok(r.ok, 'põe parede no chão', r);
r = await rpc('construir', [tk, 5, 3, 3, 1, 0]); ok(r.ok, 'empilha parede em cima (andar 2)', r);
r = await rpc('construir', [tk, 5, 4, 4, 2, 0]); ok(!r.ok && /embaixo/.test(r.erro), 'não flutua no ar', r.erro);
r = await rpc('construir', [tk, 5, 3, 3, 1, 0]); ok(!r.ok, 'não põe 2 coisas no mesmo lugar', r.erro);
r = await rpc('construir', [tk, 6, 1, 1, 0, 0]); ok(!r.ok && /seu lote/.test(r.erro), 'não constrói no lote dos outros', r.erro);
r = await rpc('construir', [tk, 5, 3, 3, 4, 0]); ok(!r.ok, 'altura máxima de 4', r.erro);
r = await rpc('construir', [tk, 5, 5, 5, 0, 1]); ok(!r.ok, 'piso não vai como bloco', r.erro);
r = await rpc('construir', [tk, 5, 5, 5, -1, 1]); ok(r.ok, 'põe piso', r);
r = await rpc('construir', [tk, 5, 5, 5, 0, 2]); ok(r.ok, 'mesa em cima do piso', r);
r = await rpc('construir', [tk, 5, 5, 5, 1, 0]); ok(!r.ok, 'nada em cima da mesa', r.erro);
ok(await conta(tk, 'parede_madeira') === 8, 'gastou 2 paredes da mochila');
const bl = await rpc('lote_blocos', [[5, 6]]); ok(bl['5'].length === 4 && !bl['6'], 'blocos do lote', bl['5']);
r = await rpc('desmontar', [tk, 5, 3, 3, 0]); ok(!r.ok && /cima/.test(r.erro), 'tira de cima pra baixo', r.erro);
r = await rpc('desmontar', [tk, 5, 3, 3, 1]); ok(r.ok && await conta(tk, 'parede_madeira') === 9, 'desmontar devolve o bloco', r);
r = await rpc('desmontar', [tk2, 5, 3, 3, 0]); ok(!r.ok, 'outra pessoa não desmonta', r.erro);
r = await rpc('largar_lote', [tk]); ok(!r.ok, 'não larga lote com coisas', r.erro);

console.log('loja do jogador');
await db.exec(`select jogo_add(205, 'cristal', 10); select jogo_add(205, 'picareta_ferro', 1);`);
r = await rpc('loja_por', [tk, await slotDe(tk, 'cristal'), 5, 100]); ok(!r.ok && /balcão/.test(r.erro), 'precisa de balcão pra vender', r.erro);
await db.exec(`insert into lote_bloco values (5, 8, 8, 0, 'balcao')`);
r = await rpc('loja_por', [tk, await slotDe(tk, 'cristal'), 5, 100]); ok(r.ok && await conta(tk, 'cristal') === 5, 'põe 5 cristais a 100 cada', r);
await db.exec(`update inventario set dur = 77 where morador_id = 205 and item = 'picareta_ferro'`);
r = await rpc('loja_por', [tk, await slotDe(tk, 'picareta_ferro'), 1, 300]); ok(r.ok, 'põe a picareta usada a 300', r);
const lj = await rpc('loja_ofertas', [5]); ok(lj.ofertas.length === 2 && lj.nome === 'Gui', 'a loja mostra as ofertas', lj.ofertas);
ok((await rpc('feira', [])).length === 2, 'a feira lista tudo');
const ofC = lj.ofertas.find(o => o.item === 'cristal').id, ofP = lj.ofertas.find(o => o.item === 'picareta_ferro').id;
r = await rpc('loja_comprar', [tk2, ofC, 2]); ok(!r.ok && /insuficiente/.test(r.erro), 'sem dinheiro não compra', r.erro);
await db.exec(`update jogador set moedas = 1000 where morador_id = 206`);
const antesGui = (await rpc('meu_jogo', [tk])).moedas;
r = await rpc('loja_comprar', [tk2, ofC, 2]); ok(r.ok && r.moedas === 800, 'Ana compra 2 cristais por 200', r);
ok((await rpc('meu_jogo', [tk])).moedas === antesGui + 200, 'o dinheiro vai pro dono da loja');
ok(await conta(tk2, 'cristal') === 2, 'os cristais vão pra mochila da Ana');
r = await rpc('loja_comprar', [tk2, ofC, 9]); ok(!r.ok, 'não compra mais do que tem', r.erro);
r = await rpc('loja_comprar', [tk, ofC, 1]); ok(!r.ok, 'não compra da própria loja', r.erro);
r = await rpc('loja_comprar', [tk2, ofP, 1]); ok(r.ok, 'compra a picareta', r);
ok((await inv(tk2)).find(s => s.i === 'picareta_ferro').d === 77, 'a picareta chega com a durabilidade que tinha (77)');
r = await rpc('loja_tirar', [tk, ofC]); ok(r.ok && await conta(tk, 'cristal') === 8, 'o dono tira o resto da loja', r);
ok((await rpc('loja_ofertas', [5])).ofertas.length === 0, 'loja vazia');

console.log('mudar de casa leva o lote');
r = await rpc('trocar_casa', [tk, 3, JSON.stringify({ pele: 2, cabelo: 'curto', cor_cabelo: 0, camisa: 2, estampa: 'lisa', camisa2: 3, baixo: 'calca', cor_baixo: 0, sapato: 1, oculos: false, chapeu: null, cor_chapeu: 0, barba: false })]);
ok(r.ok, 'troca de casa', r);
const l5 = (await rpc('lotes_lista', [])).find(l => l.id === 5); ok(l5.dono === r.morador && l5.nome === 'Gui', 'o lote continua do Gui', l5);

console.log(falhas ? `\n${falhas} FALHA(S)` : '\nTUDO CERTO');
process.exit(falhas ? 1 : 0);
