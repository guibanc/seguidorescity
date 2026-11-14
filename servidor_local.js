// =====================================================================
//  Servidor LOCAL pra testar o site no seu PC (sem Supabase).
//    node servidor_local.js        -> http://localhost:3003
//  Faz as mesmas funções do Supabase (registrar, entrar, salvar_perfil,
//  amizades, buscar...) e guarda tudo em banco_local.json.
//  Quando o site/config.js tiver a URL do Supabase, o site usa o Supabase.
// =====================================================================
const http = require('http'), fs = require('fs'), path = require('path'), crypto = require('crypto');
const PORTA = Number(process.env.PORT) || 3003;
const SITE = path.join(__dirname, 'site');
const BANCO = path.join(__dirname, 'banco_local.json');
const Sprites = require('./site/js/sprites.js');

const moradores = JSON.parse(fs.readFileSync(path.join(SITE, 'dados', 'moradores.json'), 'utf8'));
const existe = new Set(moradores.map(m => m.id));
let db = { registros: {}, sessoes: {}, amizades: [] };
try { db = Object.assign(db, JSON.parse(fs.readFileSync(BANCO, 'utf8'))); } catch {}
const salvar = () => fs.writeFileSync(BANCO, JSON.stringify(db, null, 1));

// mesma lista e mesma regra do Supabase (gerada por: npm run palavras)
const nomePermitido = require('./supabase/filtro_nomes.js').criarFiltro(require('./supabase/palavras_bloqueadas.json'));
function aparenciaOk(a) {
  if (a == null) return true;
  if (typeof a !== 'object') return false;
  const n = Sprites.normalizar(a);
  return Object.keys(a).every(k => k in n) && Object.keys(n).every(k => JSON.stringify(n[k]) === JSON.stringify(a[k] === undefined ? null : a[k]));
}
const hashPin = pin => { const sal = crypto.randomBytes(16).toString('hex'); return sal + ':' + crypto.scryptSync(pin, sal, 32).toString('hex'); };
const pinOk = (pin, h) => { const [sal, v] = h.split(':'); return crypto.timingSafeEqual(Buffer.from(v, 'hex'), crypto.scryptSync(String(pin), sal, 32)); };
const sha = t => crypto.createHash('sha256').update(String(t || '')).digest('hex');
const limpaUser = u => String(u || '').trim().replace(/^@+|@+$/g, '').toLowerCase();
const limpaNome = n => String(n || '').replace(/\s+/g, ' ').trim();
const regPorUser = u => Object.values(db.registros).find(r => r.usuario === u);
function sessaoMorador(tok) {
  const s = db.sessoes[sha(tok)];
  return s && s.expira > Date.now() ? s.morador : null;
}
function novaSessao(mid) {
  const tok = crypto.randomBytes(24).toString('hex');
  db.sessoes[sha(tok)] = { morador: mid, expira: Date.now() + 30 * 864e5 };
  const r = db.registros[mid]; salvar();
  return { ok: true, token: tok, morador: mid, nome: r.nome, usuario: r.usuario, aparencia: r.aparencia, bio: r.bio || null };
}
const erro = e => ({ ok: false, erro: e });
const publico = id => {
  const r = db.registros[id], m = moradores[id - 1];
  return { id, casa: m.casa, chegou_no_ep: m.chegou_no_ep, nome: r && !r.oculto ? r.nome : null,
           usuario: r && !r.oculto ? r.usuario : null, aparencia: r && !r.oculto ? r.aparencia : null,
           bio: r && !r.oculto ? (r.bio || null) : null, ocupado: !!r };
};

const RPC = {
  registrar({ p_morador, p_usuario, p_nome, p_pin, p_aparencia = null }) {
    const u = limpaUser(p_usuario), n = limpaNome(p_nome), pin = String(p_pin || '');
    if (!/^[0-9]{6}$/.test(pin)) return erro('PIN precisa ter 6 números');
    if (/^(\d)\1{5}$/.test(pin) || ['123456','654321','121212'].includes(pin)) return erro('PIN muito fácil');
    if (!nomePermitido(n) || !nomePermitido(u)) return erro('Nome não permitido');
    if (!aparenciaOk(p_aparencia)) return erro('Aparência inválida');
    if (!existe.has(p_morador)) return erro('Morador não existe');
    if (db.registros[p_morador]) return erro('Esse morador já tem dono, escolhe outro');
    if (regPorUser(u)) return erro('Esse @ já está em uso');
    if (!/^[a-z0-9_.]{3,20}$/.test(u) || n.length < 2 || n.length > 20) return erro('@ (3-20 letras/números) ou nome (2-20) inválido');
    db.registros[p_morador] = { morador: p_morador, usuario: u, nome: n, pin: hashPin(pin), aparencia: p_aparencia,
                                criado_em: new Date().toISOString(), tentativas: 0, bloqueado_ate: 0, oculto: false };
    return novaSessao(p_morador);
  },
  entrar({ p_usuario, p_pin }) {
    const r = regPorUser(limpaUser(p_usuario));
    if (!r) return erro('@ ou PIN errado');
    if (r.bloqueado_ate > Date.now()) return erro('Muitas tentativas. Tenta de novo em alguns minutos');
    if (!pinOk(p_pin, r.pin)) {
      r.tentativas++;
      if (r.tentativas >= 5) { r.tentativas = 0; r.bloqueado_ate = Date.now() + 15 * 60e3; }
      salvar(); return erro('@ ou PIN errado');
    }
    r.tentativas = 0; r.bloqueado_ate = 0;
    return novaSessao(r.morador);
  },
  meu_perfil({ p_token }) {
    const mid = sessaoMorador(p_token); if (!mid) return erro('Entre de novo');
    const r = db.registros[mid];
    return { ok: true, morador: mid, nome: r.nome, usuario: r.usuario, aparencia: r.aparencia, bio: r.bio || null };
  },
  salvar_perfil({ p_token, p_nome, p_aparencia, p_bio = null }) {
    const mid = sessaoMorador(p_token); if (!mid) return erro('Entre de novo');
    const n = limpaNome(p_nome), b = p_bio == null ? undefined : (limpaNome(p_bio) || null);
    if (!nomePermitido(n)) return erro('Nome não permitido');
    if (b && !nomePermitido(b)) return erro('Essa frase não é permitida');
    if (b && b.length > 90) return erro('A frase pode ter até 90 letras');
    if (n.length < 2 || n.length > 20) return erro('Nome com 2 a 20 letras');
    if (!aparenciaOk(p_aparencia)) return erro('Aparência inválida');
    Object.assign(db.registros[mid], { nome: n, aparencia: p_aparencia }, b === undefined ? {} : { bio: b }); salvar();
    return { ok: true };
  },
  sair({ p_token }) { delete db.sessoes[sha(p_token)]; salvar(); return { ok: true }; },
  adicionar_amigo({ p_token, p_amigo }) {
    const mid = sessaoMorador(p_token); if (!mid) return erro('Entre de novo');
    if (mid === p_amigo) return erro('Esse é você :)');
    if (!existe.has(p_amigo)) return erro('Morador não existe');
    if (db.amizades.filter(a => a.de === mid).length >= 100) return erro('Limite de 100 amigos');
    if (!db.amizades.some(a => a.de === mid && a.para === p_amigo)) { db.amizades.push({ de: mid, para: p_amigo }); salvar(); }
    return { ok: true, mutuo: db.amizades.some(a => a.de === p_amigo && a.para === mid) };
  },
  recusar_amizade({ p_token, p_de }) {
    const mid = sessaoMorador(p_token); if (!mid) return erro('Entre de novo');
    db.amizades = db.amizades.filter(a => !(a.de === p_de && a.para === mid)); salvar();
    return { ok: true };
  },
  remover_amigo({ p_token, p_amigo }) {
    const mid = sessaoMorador(p_token); if (!mid) return erro('Entre de novo');
    db.amizades = db.amizades.filter(a => !(a.de === mid && a.para === p_amigo)); salvar();
    return { ok: true };
  },
  amigos_de({ p_morador }) {
    const vis = id => !db.registros[id] || !db.registros[id].oculto;
    return { segue: db.amizades.filter(a => a.de === p_morador && vis(a.para)).map(a => a.para),
             seguidores: db.amizades.filter(a => a.para === p_morador && db.registros[a.de] && vis(a.de)).map(a => a.de) };
  },
  buscar({ p_texto }) {
    const t = String(p_texto || '').toLowerCase(), u = limpaUser(t);
    return Object.values(db.registros).filter(r => !r.oculto && (r.nome.toLowerCase().includes(t) || r.usuario.includes(u)))
      .sort((a, b) => a.nome.localeCompare(b.nome)).slice(0, 20).map(r => publico(r.morador));
  },
};

const TIPOS = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
                '.json': 'application/json; charset=utf-8', '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
                '.webmanifest': 'application/manifest+json' };
const json = (res, code, obj) => { res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }); res.end(JSON.stringify(obj)); };

http.createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  if (url.pathname === '/api/publicos') return json(res, 200, moradores.map(m => publico(m.id)));
  if (url.pathname === '/api/contador') return json(res, 200, { seguidores: db.seguidores || moradores.length, plataforma: 'local', atualizado_em: new Date().toISOString() });
  const m = url.pathname.match(/^\/api\/rpc\/(\w+)$/);
  if (m) {
    if (req.method !== 'POST' || !RPC[m[1]]) return json(res, 404, erro('função não existe'));
    let body = '';
    req.on('data', c => { body += c; if (body.length > 1e5) req.destroy(); });
    req.on('end', () => {
      try { json(res, 200, RPC[m[1]](JSON.parse(body || '{}'))); }
      catch (e) { console.error(e); json(res, 400, erro('pedido inválido')); }
    });
    return;
  }
  let arq = path.normalize(path.join(SITE, decodeURIComponent(url.pathname)));
  if (!arq.startsWith(SITE)) { res.writeHead(403); return res.end(); }
  if (fs.existsSync(arq) && fs.statSync(arq).isDirectory()) arq = path.join(arq, 'index.html');
  fs.readFile(arq, (e, dados) => {
    if (e) { res.writeHead(404); return res.end('não achei'); }
    res.writeHead(200, { 'Content-Type': TIPOS[path.extname(arq)] || 'application/octet-stream', 'Cache-Control': 'no-cache' });
    res.end(dados);
  });
}).listen(PORTA, () => console.log(`Vila rodando em http://localhost:${PORTA}  (banco local: banco_local.json)`));
