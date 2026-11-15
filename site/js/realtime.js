// =====================================================================
//  Tempo real: quem está online, chat ao vivo e posição dos bonecos
//  controlados. Supabase Realtime (site publicado) ou SSE do servidor local.
//  API: Rt.conectar({onOnline, onChat, onHistorico, onPos}) · Rt.presenca(perfil|null)
//       Rt.pos(dados) · (o envio de chat é pelo Api.rpc('enviar_chat'))
// =====================================================================
(function () {
  const C = window.VILA_CONFIG || {};
  const sb = !!(C.SUPABASE_URL && C.SUPABASE_ANON_KEY);
  const base = sb ? C.SUPABASE_URL.trim().replace(/\/+$/, '').replace(/\/rest\/v1$/, '') : '';
  const h = location.hostname, local = h === 'localhost' || h === '127.0.0.1' || /^(192\.168|10\.|172\.(1[6-9]|2\d|3[01]))\./.test(h);
  if (!sb && !local) { window.Rt = null; return; }          // publicado sem banco: sem tempo real
  const cid = Math.random().toString(36).slice(2) + Date.now().toString(36);
  let H = {}, perfil = null, pronto = false;

  // ---------------- Supabase ----------------
  function supabase() {
    let canal = null, cliente = null;
    const carregar = () => new Promise((ok, erro) => {
      if (window.supabase) return ok();
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.118.0/dist/umd/supabase.min.js';
      s.onload = ok; s.onerror = erro; document.head.appendChild(s);
    });
    function sincronizar() {
      const st = canal.presenceState(), m = new Map(); let anon = 0;
      for (const lista of Object.values(st)) for (const p of lista) { if (p.m) m.set(p.m, { m: p.m, nome: p.nome }); else anon++; }
      H.onOnline && H.onOnline({ moradores: [...m.values()], visitantes: anon });
    }
    async function conectar() {
      await carregar();
      cliente = window.supabase.createClient(base, C.SUPABASE_ANON_KEY, { realtime: { params: { eventsPerSecond: 8 } } });
      canal = cliente.channel('vila', { config: { presence: { key: cid }, broadcast: { self: false } } });
      canal.on('presence', { event: 'sync' }, sincronizar)
        .on('broadcast', { event: 'pos' }, p => H.onPos && H.onPos(p.payload))
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'chat' }, p => H.onChat && H.onChat(p.new))
        .subscribe(async st => {
          if (st !== 'SUBSCRIBED') return;
          pronto = true; await rastrear();
          try {
            const r = await fetch(`${base}/rest/v1/chat?select=id,morador_id,nome,texto,criado_em&order=id.desc&limit=30`,
              { headers: { apikey: C.SUPABASE_ANON_KEY, Authorization: 'Bearer ' + C.SUPABASE_ANON_KEY } });
            if (r.ok) { const d = await r.json(); H.onHistorico && H.onHistorico(d.reverse()); }
          } catch {}
        });
    }
    async function rastrear() { if (pronto) await canal.track(perfil ? { m: perfil.m, nome: perfil.nome } : { anon: true }); }
    return {
      conectar, rastrear,
      pos: d => { if (pronto) canal.send({ type: 'broadcast', event: 'pos', payload: d }); },
    };
  }

  // ---------------- servidor local (SSE) ----------------
  function localSSE() {
    let es = null;
    const post = (url, body) => fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).catch(() => {});
    async function rastrear() { if (pronto) await post('/api/presenca', { cid, m: perfil && perfil.m, nome: perfil && perfil.nome }); }
    function conectar() {
      es = new EventSource('/api/eventos?cid=' + cid);
      es.onopen = () => { pronto = true; rastrear(); };
      es.addEventListener('chat', e => H.onChat && H.onChat(JSON.parse(e.data)));
      es.addEventListener('chat_historico', e => H.onHistorico && H.onHistorico(JSON.parse(e.data)));
      es.addEventListener('online', e => H.onOnline && H.onOnline(JSON.parse(e.data)));
      es.addEventListener('pos', e => H.onPos && H.onPos(JSON.parse(e.data)));
      setInterval(rastrear, 20000);
    }
    return { conectar, rastrear, pos: d => { if (pronto) post('/api/pos', { cid, p: d }); } };
  }

  const impl = sb ? supabase() : localSSE();
  window.Rt = {
    modo: sb ? 'supabase' : 'local',
    conectar(handlers) { H = handlers || {}; impl.conectar().catch(e => console.warn('tempo real indisponível', e)); },
    presenca(p) { perfil = p || null; impl.rastrear(); },
    pos(d) { impl.pos(d); },
  };
})();
