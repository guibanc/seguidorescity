// Banco: Supabase (se configurado) ou o servidor local (node servidor_local.js)
(function () {
  const C = window.VILA_CONFIG || {};
  const sb = !!(C.SUPABASE_URL && C.SUPABASE_ANON_KEY);
  const base = sb ? C.SUPABASE_URL.replace(/\/+$/, '') : '';
  const H = sb ? { apikey: C.SUPABASE_ANON_KEY, Authorization: 'Bearer ' + C.SUPABASE_ANON_KEY, 'Content-Type': 'application/json' }
               : { 'Content-Type': 'application/json' };

  async function rpc(nome, params) {
    try {
      const r = await fetch(sb ? `${base}/rest/v1/rpc/${nome}` : `/api/rpc/${nome}`, { method: 'POST', headers: H, body: JSON.stringify(params || {}) });
      const d = await r.json().catch(() => null);
      if (!r.ok) return { ok: false, erro: (d && (d.message || d.erro)) || 'Erro no servidor (' + r.status + ')' };
      return d;
    } catch (e) { return { ok: false, erro: 'Sem conexão com o servidor' }; }
  }

  async function publicos() {
    if (!sb) return (await fetch('/api/publicos')).json();
    const todos = []; const passo = 1000;
    for (let i = 0; ; i += passo) {
      const r = await fetch(`${base}/rest/v1/moradores_publicos?select=*&order=id&offset=${i}&limit=${passo}`, { headers: H });
      if (!r.ok) throw new Error('Supabase ' + r.status);
      const d = await r.json(); todos.push(...d);
      if (d.length < passo) return todos;
    }
  }

  window.Api = { modo: sb ? 'supabase' : 'local', rpc, publicos };
})();
