// =====================================================================
//  Servidor LOCAL pra testar o site no seu PC:
//    npm install            (1 vez)
//    node servidor_local.js -> http://localhost:3003
//  Roda os MESMOS arquivos SQL do Supabase num Postgres local (PGlite),
//  então o que funciona aqui funciona igual no ar. Os dados ficam na
//  pasta banco_local_pg/ (não vai pro GitHub).
//  Quando o site/config.js tiver a URL do Supabase, o site usa o Supabase.
//  Opções:  ELEICAO=votacao node servidor_local.js   (fase da eleição pra testar)
// =====================================================================
const http = require('http'), fs = require('fs'), path = require('path');
const PORTA = Number(process.env.PORT) || 3003;
const SITE = path.join(__dirname, 'site');
const SQL = ['1_criar_banco.sql', '2_palavras_bloqueadas.sql', '3_contador.sql', '5_bio_e_pedidos.sql', '6_chat_online_casa.sql',
             '7_32bits_eleicao.sql', '8_jogo.sql', '9_mundo_explorar.sql', '11_terrenos.sql'];   // (4 e 10 usam coisas que só o Supabase tem)
let db;

async function abrirBanco() {
  const { PGlite } = await import('@electric-sql/pglite');
  const { pgcrypto } = await import('@electric-sql/pglite/contrib/pgcrypto');
  db = await PGlite.create({ dataDir: path.join(__dirname, 'banco_local_pg'), extensions: { pgcrypto } });
  // o que o Supabase já tem pronto
  await db.exec(`create schema if not exists extensions; create extension if not exists pgcrypto with schema extensions;
    do $$ begin create role anon; exception when duplicate_object then null; end $$;
    do $$ begin create role authenticated; exception when duplicate_object then null; end $$;
    do $$ begin create publication supabase_realtime; exception when duplicate_object then null; end $$;`);
  for (const f of SQL) {
    try { await db.exec(fs.readFileSync(path.join(__dirname, 'supabase', f), 'utf8')); }
    catch (e) { console.error('ERRO no', f, '->', e.message); throw e; }
  }
  await db.exec(fs.readFileSync(path.join(SITE, 'dados', 'novos_moradores.sql'), 'utf8'));
  if (process.env.ELEICAO) await db.query(`update eleicao set fase = $1 where id = 1`, [process.env.ELEICAO]);
  // "cron" da mina
  const tick = async () => {
    const r = (await db.query(`select gerada_em + make_interval(mins => intervalo_min) <= now() as vence from mina_estado where id = 1`)).rows[0];
    if (r && r.vence) { await db.exec('select gerar_mina()'); emitir('mina', { regenerada: true }); console.log('mina regenerada'); }
  };
  setInterval(() => tick().catch(e => console.error(e)), 20000);
}

// ---------- RPC genérico: chama a função do Postgres com os parâmetros nomeados ----------
const assinaturas = new Map();
async function assinatura(fn) {
  if (assinaturas.has(fn)) return assinaturas.get(fn);
  const r = (await db.query(`
    select p.proretset as conjunto, p.proargnames as nomes,
           array(select format_type(t, null) from unnest(p.proargtypes) t) as tipos
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = $1 and has_function_privilege('anon', p.oid, 'execute')`, [fn])).rows;
  assinaturas.set(fn, r); return r;
}
async function chamar(fn, corpo) {
  const sigs = await assinatura(fn);
  if (!sigs.length) return { status: 404, json: { ok: false, erro: 'função não existe' } };
  const chaves = Object.keys(corpo || {});
  const sig = sigs.find(s => chaves.every(k => (s.nomes || []).includes(k))) || sigs[0];
  const args = [], params = [];
  (sig.nomes || []).forEach((nome, i) => {
    if (!(nome in corpo)) return;
    let v = corpo[nome];
    if (v !== null && typeof v === 'object') v = JSON.stringify(v);
    params.push(v); args.push(`${nome} => $${params.length}::${sig.tipos[i]}`);
  });
  const chamada = `${fn}(${args.join(', ')})`;
  if (sig.conjunto) return { status: 200, json: (await db.query(`select * from ${chamada}`, params)).rows };
  return { status: 200, json: (await db.query(`select ${chamada} as r`, params)).rows[0].r };
}

// ---------- tempo real (imita o Realtime do Supabase): Server-Sent Events ----------
const clientes = new Map();            // cid -> { res, m, nome, visto }
function emitir(tipo, dados, menos) {
  const linha = 'event: ' + tipo + '\ndata: ' + JSON.stringify(dados) + '\n\n';
  for (const [cid, c] of clientes) if (cid !== menos) { try { c.res.write(linha); } catch { clientes.delete(cid); } }
}
function listaOnline() {
  const m = new Map(); let anon = 0;
  for (const c of clientes.values()) { if (c.m) m.set(c.m, { m: c.m, nome: c.nome }); else anon++; }
  return { moradores: [...m.values()], visitantes: anon };
}
setInterval(() => { let mudou = false; for (const [cid, c] of clientes) if (Date.now() - c.visto > 45000) { try { c.res.end(); } catch {} clientes.delete(cid); mudou = true; } if (mudou) emitir('online', listaOnline()); }, 15000);

const TIPOS = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
                '.json': 'application/json; charset=utf-8', '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
                '.webmanifest': 'application/manifest+json' };
const json = (res, code, obj) => { res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }); res.end(JSON.stringify(obj)); };
const lerCorpo = req => new Promise((ok, erro) => { let b = ''; req.on('data', c => { b += c; if (b.length > 2e5) req.destroy(); }); req.on('end', () => { try { ok(JSON.parse(b || '{}')); } catch (e) { erro(e); } }); });

async function tratar(req, res) {
  const url = new URL(req.url, 'http://x');
  if (url.pathname === '/api/publicos') return json(res, 200, (await db.query('select * from moradores_publicos order by id')).rows);
  if (url.pathname === '/api/contador') return json(res, 200, (await db.query('select * from contador_publico')).rows[0] || null);
  if (url.pathname === '/api/eventos') {
    const cid = url.searchParams.get('cid') || String(Math.random());
    res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store', Connection: 'keep-alive' });
    res.write('retry: 2000\n\n');
    clientes.set(cid, { res, m: null, nome: null, visto: Date.now() });
    const hist = (await db.query('select id, morador_id, nome, texto, criado_em from chat order by id desc limit 30')).rows.reverse();
    res.write('event: chat_historico\ndata: ' + JSON.stringify(hist) + '\n\n');
    emitir('online', listaOnline());
    req.on('close', () => { clientes.delete(cid); emitir('online', listaOnline()); });
    return;
  }
  if (url.pathname === '/api/presenca' || url.pathname === '/api/pos') {
    const d = await lerCorpo(req), c = clientes.get(d.cid);
    if (c) {
      c.visto = Date.now();
      if (url.pathname === '/api/presenca') { const mudou = c.m !== (d.m || null); c.m = d.m || null; c.nome = d.nome || null; if (mudou) emitir('online', listaOnline()); }
      else emitir('pos', d.p, d.cid);
    }
    return json(res, 200, { ok: true });
  }
  const m = url.pathname.match(/^\/api\/rpc\/(\w+)$/);
  if (m) {
    if (req.method !== 'POST') return json(res, 405, { ok: false, erro: 'use POST' });
    const corpo = await lerCorpo(req);
    const r = await chamar(m[1], corpo);
    if (m[1] === 'enviar_chat' && r.json && r.json.ok) {
      const msg = (await db.query('select id, morador_id, nome, texto, criado_em from chat where id = $1', [r.json.id])).rows[0];
      if (msg) emitir('chat', msg);
    }
    return json(res, r.status, r.json);
  }
  // arquivos do site
  let arq = path.normalize(path.join(SITE, decodeURIComponent(url.pathname)));
  if (!arq.startsWith(SITE)) { res.writeHead(403); return res.end(); }
  if (fs.existsSync(arq) && fs.statSync(arq).isDirectory()) arq = path.join(arq, 'index.html');
  fs.readFile(arq, (e, dados) => {
    if (e) { res.writeHead(404); return res.end('não achei'); }
    res.writeHead(200, { 'Content-Type': TIPOS[path.extname(arq)] || 'application/octet-stream', 'Cache-Control': 'no-cache' });
    res.end(dados);
  });
}

abrirBanco().then(() => {
  http.createServer((req, res) => tratar(req, res).catch(e => { console.error(e); try { json(res, 500, { ok: false, erro: 'erro no servidor: ' + e.message }); } catch {} }))
    .listen(PORTA, () => console.log(`Vila rodando em http://localhost:${PORTA}  (banco local: banco_local_pg/)`));
}).catch(e => { console.error('Não consegui abrir o banco local:', e); process.exit(1); });
