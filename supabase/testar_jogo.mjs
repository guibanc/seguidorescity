// Testa o banco do JOGO num Postgres local (PGlite), simulando uma partida.
//   node supabase/testar_jogo.mjs
import { PGlite } from '@electric-sql/pglite';
import { pgcrypto } from '@electric-sql/pglite/contrib/pgcrypto';
import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
const R = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const db = await PGlite.create({ extensions: { pgcrypto } });
await db.exec(`create schema if not exists extensions; create extension if not exists pgcrypto with schema extensions;
  do $$ begin create role anon; exception when duplicate_object then null; end $$;
  do $$ begin create role authenticated; exception when duplicate_object then null; end $$;
  create publication supabase_realtime;`);
for (const f of ['1_criar_banco.sql', '2_palavras_bloqueadas.sql', '3_contador.sql', '5_bio_e_pedidos.sql', '6_chat_online_casa.sql', '7_32bits_eleicao.sql', '8_jogo.sql', '9_mundo_explorar.sql'])
  await db.exec(fs.readFileSync(path.join(R, 'supabase', f), 'utf8'));
await db.exec(fs.readFileSync(path.join(R, 'site/dados/novos_moradores.sql'), 'utf8'));
const q1 = async (s, p) => (await db.query(s, p)).rows[0];
const rpc = async (fn, args) => (await q1(`select ${fn}(${args.map((_, i) => '$' + (i + 1)).join(',')}) r`, args)).r;
let falhas = 0; const ok = (cond, msg, extra) => { console.log((cond ? '  ✓ ' : '  ✗ ') + msg + (extra ? '  ' + JSON.stringify(extra) : '')); if (!cond) falhas++; };
const libera = () => db.exec(`update jogador set ultima_quebra = now() - interval '1 hour', ultimo_abate = now() - interval '1 hour'`);
const inv = async tk => (await rpc('meu_jogo', [tk])).inv;
const conta = async (tk, item) => (await inv(tk)).filter(s => s.i === item).reduce((a, s) => a + s.q, 0);

const tk = (await rpc('registrar', [205, 'gui', 'Gui', '583920', null])).token;
const tk2 = (await rpc('registrar', [206, 'ana', 'Ana', '583921', null])).token;
console.log('catálogo / jogador');
const cat = await rpc('jogo_catalogo', []);
ok(cat.itens.length > 50 && cat.receitas.length > 30 && cat.ranks.length === 6, 'catálogo carrega', { itens: cat.itens.length, receitas: cat.receitas.length });
ok((await rpc('meu_jogo', [tk])).moedas === 0, 'jogador novo com 0 moedas e mochila vazia');

console.log('explorar: quebrar na mão');
const { id: arbusto } = await q1(`select id from mundo_obj where tipo = 'arbusto' limit 1`);
let r = await rpc('quebrar_obj', [tk, arbusto, -1]); ok(r.ok, 'quebra arbusto na mão', r.ganhou);
r = await rpc('quebrar_obj', [tk2, arbusto, -1]); ok(!r.ok && r.sumiu, 'o mesmo arbusto some pra outra pessoa (mundo compartilhado)', r.erro);
const { id: arv } = await q1(`select id from mundo_obj where tipo = 'carvalho' limit 1`);
r = await rpc('quebrar_obj', [tk, arv, -1]); ok(!r.ok && /devagar/.test(r.erro), 'não deixa quebrar rápido demais (anti-trapaça)', r.erro);
await libera(); r = await rpc('quebrar_obj', [tk, arv, -1]); ok(r.ok && r.ganhou.madeira >= 3, 'corta árvore na mão (madeira)', r.ganhou);
const { id: rocha } = await q1(`select id from mundo_obj where tipo = 'rocha' limit 1`);
await libera(); r = await rpc('quebrar_obj', [tk, rocha, -1]); ok(!r.ok && /picareta/.test(r.erro), 'pedra exige picareta', r.erro);

console.log('crafting');
for (let i = 0; i < 3; i++) { const { id } = await q1(`select id from mundo_obj where tipo = 'carvalho' and quebrado_ate is null limit 1`); await libera(); await rpc('quebrar_obj', [tk, id, -1]); }
ok(await conta(tk, 'madeira') >= 12, 'juntou madeira', await conta(tk, 'madeira'));
r = await rpc('craftar', [tk, 'tabua', 3]); ok(r.ok && await conta(tk, 'tabua') === 12, 'madeira -> 12 tábuas', r);
const gAntes = await conta(tk, 'graveto'); r = await rpc('craftar', [tk, 'graveto', 2]); ok(r.ok && await conta(tk, 'graveto') === gAntes + 8, 'tábuas -> 8 gravetos', r);
r = await rpc('craftar', [tk, 'picareta_madeira', 1]); ok(r.ok, 'faz picareta de madeira', r);
r = await rpc('craftar', [tk, 'espada_ferro', 1]); ok(!r.ok && /rank/.test(r.erro), 'espada de ferro pede rank', r.erro);
r = await rpc('craftar', [tk, 'machado_pedra', 1]); ok(!r.ok && /Falta/.test(r.erro), 'sem pedra não faz machado de pedra', r.erro);
const pic = (await inv(tk)).find(s => s.i === 'picareta_madeira'); ok(pic && pic.d === 60, 'picareta nova com 60 de durabilidade', pic);

console.log('inventário');
r = await rpc('mover_item', [tk, pic.s, 0]); ok(r.ok && (await inv(tk)).find(s => s.s === 0).i === 'picareta_madeira', 'move a picareta pra barra (slot 0)');
r = await rpc('mover_item', [tk, 0, 36]); ok(!r.ok, 'picareta não vai no slot de capacete', r.erro);
const outro = (await inv(tk)).find(s => s.s !== 0); r = await rpc('mover_item', [tk, 0, outro.s]); ok(r.ok && (await inv(tk)).find(s => s.s === outro.s).i === 'picareta_madeira', 'troca dois slots de lugar');
await rpc('mover_item', [tk, outro.s, 0]);

console.log('mina');
r = await rpc('mina_camadas', [0]); ok(r.camadas['0'].length === 625 && r.camadas['1'].length === 625, 'camadas 0 e 1 com 25x25', { centro: r.camadas['0'][12 * 25 + 12] });
const c0 = r.camadas['0']; const alvo = [...c0].findIndex(ch => ch === 'p' || ch === 'c');
const ax = alvo % 25, ay = Math.floor(alvo / 25), tipoAlvo = c0[alvo];
await libera(); r = await rpc('minerar', [tk, 0, ax, ay, 0]);
ok(tipoAlvo === 'f' ? !r.ok : r.ok, `minera bloco '${tipoAlvo}' na camada 0 com picareta de madeira`, r);
await libera(); r = await rpc('minerar', [tk, 0, ax, ay, 0]); ok(!r.ok, 'bloco já minerado não dá de novo', r.erro);
r = await rpc('minerar', [tk, 5, 3, 3, 0]); ok(!r.ok && /rank/.test(r.erro), 'rank 0 não cava na camada 5', r.erro);
const durAntes = 60, durDepois = (await inv(tk)).find(s => s.s === 0).d; ok(durDepois === durAntes - 1, 'a picareta gastou 1 de durabilidade', durDepois);
await db.exec(`select gerar_mina()`); ok((await rpc('mina_camadas', [0])).camadas['0'][alvo] !== '.' || tipoAlvo === '.', 'regenerar a mina devolve os blocos');

console.log('economia');
await db.exec(`select jogo_add(205, 'minerio_ferro', 20); select jogo_add(205, 'carne_crua', 5); select jogo_add(205, 'maca', 3)`);
r = await rpc('vender', [tk, 'carne_crua', 5, 'mina']); ok(!r.ok, 'loja da mina não compra carne', r.erro);
r = await rpc('vender', [tk, 'minerio_ferro', 20, 'mina']); ok(r.ok && r.ganhou === 160, 'vende 20 minérios de ferro na mina = 160', r);
r = await rpc('vender', [tk, 'minerio_ferro', 1, 'mina']); ok(!r.ok, 'não vende o que não tem', r.erro);
r = await rpc('vender', [tk, 'carne_crua', 5, 'mercado']); ok(r.ok && r.ganhou === 15, 'mercadinho compra carne', r);
r = await rpc('comprar', [tk, 'pao', 2]); ok(r.ok && r.moedas === 175 - 18, 'compra 2 pães no mercadinho', r);
r = await rpc('comprar', [tk, 'cristal', 1]); ok(!r.ok, 'mercadinho não vende cristal', r.erro);
r = await rpc('comprar', [tk2, 'pao', 1]); ok(!r.ok && /insuficiente/.test(r.erro), 'sem dinheiro não compra', r.erro);
r = await rpc('rankup', [tk]); ok(!r.ok && /Faltam/.test(r.erro), 'rankup pede 300 moedas', r.erro);
await db.exec(`update jogador set moedas = 1000 where morador_id = 205`);
r = await rpc('rankup', [tk]); ok(r.ok && r.nome === 'Minerador', 'sobe pra Minerador', r);
ok((await rpc('meu_jogo', [tk])).moedas === 700, 'o rank custou 300');
r = await rpc('vender', [tk, 'maca', 3, 'mercado']); ok(r.ok && r.ganhou === 6, 'bônus do rank (5%) arredonda pra baixo: 3 maçãs = 6', r);
const rk = await rpc('ranking', []); ok(rk.ricos[0].nome === 'Gui', 'ranking dos mais ricos', rk.ricos[0]);

console.log('comida e bichos');
const pao = (await inv(tk)).find(s => s.i === 'pao'); r = await rpc('usar_item', [tk, pao.s]); ok(r.ok && r.cura === 12, 'comer pão cura 12', r);
r = await rpc('usar_item', [tk, 0]); ok(!r.ok, 'picareta não se come', r.erro);
await libera(); r = await rpc('abater', [tk, 'vaca']); ok(r.ok && r.ganhou.couro >= 1, 'abate vaca (couro + carne)', r.ganhou);
r = await rpc('abater', [tk, 'vaca']); ok(!r.ok, 'abater de novo na hora é bloqueado', r.erro);
r = await rpc('abater', [tk, 'dragao']); ok(!r.ok, 'bicho inventado é recusado', r.erro);

console.log('mudar de casa leva o jogo junto');
const moedasAntes = (await rpc('meu_jogo', [tk])).moedas, itensAntes = (await inv(tk)).length;
r = await rpc('trocar_casa', [tk, 3, JSON.stringify({ pele: 2, cabelo: 'curto', cor_cabelo: 0, camisa: 2, estampa: 'lisa', camisa2: 3, baixo: 'calca', cor_baixo: 0, sapato: 1, oculos: false, chapeu: null, cor_chapeu: 0, barba: false })]);
ok(r.ok, 'troca de casa', r);
const depois = await rpc('meu_jogo', [tk]); ok(depois.moedas === moedasAntes && depois.inv.length === itensAntes && depois.rank === 1, 'dinheiro, rank e inventário foram junto', { moedas: depois.moedas, itens: depois.inv.length });

console.log(falhas ? `\n${falhas} FALHA(S)` : '\nTUDO CERTO');
process.exit(falhas ? 1 : 0);
