// roda os SQL do Supabase num Postgres local (PGlite), com os "enfeites" do Supabase simulados
import { PGlite } from '@electric-sql/pglite';
import { pgcrypto } from '@electric-sql/pglite/contrib/pgcrypto';
import fs from 'fs';
const R = process.argv[2];
const db = await PGlite.create({ extensions: { pgcrypto } });
await db.exec(`create schema if not exists extensions; create extension if not exists pgcrypto with schema extensions;
  do $$ begin create role anon; exception when duplicate_object then null; end $$;
  do $$ begin create role authenticated; exception when duplicate_object then null; end $$;
  create publication supabase_realtime;`);
for (const f of ['1_criar_banco.sql', '2_palavras_bloqueadas.sql', '3_contador.sql', '5_bio_e_pedidos.sql', '6_chat_online_casa.sql', '7_32bits_eleicao.sql']) {
  try { await db.exec(fs.readFileSync(R + '/supabase/' + f, 'utf8')); console.log('OK  ', f); }
  catch (e) { console.log('ERRO', f, '->', e.message); }
}
await db.exec(fs.readFileSync(R + '/site/dados/novos_moradores.sql', 'utf8'));
const q = async (s, p) => (await db.query(s, p)).rows;
console.log('moradores:', (await q('select count(*)::int n from moradores'))[0].n);
const reg = (await q(`select registrar(205, 'gui', 'Gui', '583920', null) r`))[0].r; console.log('registrar:', reg.ok, '| token', !!reg.token);
const tk = reg.token;
console.log('salvar_perfil c/ visual novo:', (await q(`select salvar_perfil($1,'Gui',$2::jsonb,'oi') r`, [tk, JSON.stringify({pele:2,cabelo:'moicano',cor_cabelo:0,camisa:2,estampa:'time',camisa2:3,baixo:'calca',cor_baixo:0,sapato:1,oculos:false,chapeu:'coroa',cor_chapeu:0,barba:false,acessorio:'fone',cor_acessorio:3})]))[0].r);
console.log('chat:', (await q(`select enviar_chat($1,'oi galera') r`, [tk]))[0].r);
console.log('candidatar:', (await q(`select candidatar($1,'Campo pra todos') r`, [tk]))[0].r);
console.log('trocar_casa:', (await q(`select trocar_casa($1, 3, $2::jsonb) r`, [tk, JSON.stringify({pele:2,cabelo:'moicano',cor_cabelo:0,camisa:2,estampa:'time',camisa2:3,baixo:'calca',cor_baixo:0,sapato:1,oculos:false,chapeu:'coroa',cor_chapeu:0,barba:false,acessorio:'fone',cor_acessorio:3})]))[0].r);
console.log('perfil depois:', (await q(`select meu_perfil($1) r`, [tk]))[0].r);
console.log('eleicao:', JSON.stringify((await q(`select eleicao_info() r`))[0].r));
