// =====================================================================
//  Moradores 16 bits — porta fiel de codigo/world16.py (npc_sprite)
//  Gera o boneco 12x18 a partir da "aparencia", igual ao vídeo.
//  Funciona no navegador e no Node (só mexe em arrays).
// =====================================================================
(function (root) {
  const SKIN16 = [[252,218,186],[238,192,150],[214,160,116],[178,120,80],[136,86,54],[98,60,38]];
  const HAIR16 = [[36,26,22],[70,44,26],[112,70,36],[196,150,70],[236,204,120],[150,56,30],[176,176,180],[24,22,30]];
  const SHIRT16 = [[214,56,56],[54,104,214],[246,200,54],[64,164,86],[240,240,236],[150,76,196],[238,126,40],
                   [36,172,186],[228,104,156],[44,52,70],[126,196,96],[176,120,72]];
  const PANTS16 = [[46,60,108],[70,50,40],[36,36,44],[98,100,112],[150,120,84],[60,90,70]];
  const SHOES16 = [[40,30,26],[230,230,226],[120,70,40],[200,60,50]];
  const HAIRSTYLES = ['curto','raspado','longo','rabo','coque','afro','careca','franja'];
  const ESTAMPAS = ['lisa','listrada','regata','duas_cores'];
  const BAIXOS = ['calca','bermuda','saia','vestido'];
  const CHAPEUS = [null,'bone','palha','gorro'];
  const OUT = [30,24,36];
  const DIRS = ['down','left','right','up'];
  const W = 12, H = 18;

  function sh(c, f) {
    if (f <= 1) return [Math.trunc(c[0]*f), Math.trunc(c[1]*f), Math.trunc(c[2]*f)];
    return [Math.trunc(c[0]+(255-c[0])*(f-1)), Math.trunc(c[1]+(255-c[1])*(f-1)), Math.trunc(c[2]+(255-c[2])*(f-1))];
  }

  function desenhar(look, dirc, frame) {
    if (dirc === 'left') {
      const r = desenhar(look, 'right', frame), o = new Uint8ClampedArray(W*H*4);
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++)
        for (let k = 0; k < 4; k++) o[(y*W+x)*4+k] = r[(y*W+(W-1-x))*4+k];
      return o;
    }
    const p = new Uint8ClampedArray(W*H*4);
    const set = (x, y, r, g, b, a) => { const i = (y*W+x)*4; p[i]=r; p[i+1]=g; p[i+2]=b; p[i+3]=a; };
    const P = (x, y, c) => { if (x >= 0 && x < W && y >= 0 && y < H) set(x, y, c[0], c[1], c[2], 255); };
    const skin = SKIN16[look.pele], hair = HAIR16[look.cor_cabelo];
    const shirt = SHIRT16[look.camisa], shirt2 = SHIRT16[look.camisa2];
    const bot = PANTS16[look.cor_baixo], shoe = SHOES16[look.sapato];
    const hat = look.chapeu, hatc = SHIRT16[look.cor_chapeu];
    const bob = (frame === 1 || frame === 3) ? 1 : 0;
    const y0 = 1 + bob;
    for (let x = 3; x < 9; x++) set(x, 17, 0, 0, 0, 60);
    set(2, 17, 0, 0, 0, 30); set(9, 17, 0, 0, 0, 30);
    // pernas
    const vestido = look.baixo === 'vestido';
    const legc = ['bermuda','saia','vestido'].includes(look.baixo) ? skin : bot;
    if (dirc === 'down' || dirc === 'up') {
      const L = {0:[0,0],1:[-1,1],2:[0,0],3:[1,-1]}[frame];
      [[0,4],[1,7]].forEach(([side, x]) => {
        const lift = L[side];
        for (let y = 12+y0-1; y < 15+y0-1-(lift < 0 ? 1 : 0); y++)
          P(x, y, (y > 12+y0-1 || look.baixo === 'calca') ? legc : bot);
        P(x, 15+y0-1-(lift < 0 ? 1 : 0), shoe);
      });
      if (look.baixo === 'calca') for (let x = 4; x < 8; x++) P(x, 11+y0, bot);
    } else {
      const L = {0:[5,6],1:[4,7],2:[5,6],3:[7,4]}[frame];
      const mx = Math.max(L[0], L[1]);
      for (const x of L) {
        for (let y = 12+y0-1; y < 15+y0-1; y++) P(x, y, look.baixo !== 'calca' ? legc : sh(bot, x === L[0] ? 0.9 : 1));
        P(x, 15+y0-1, shoe);
        if ((frame === 1 || frame === 3) && x === mx) P(x+1, 15+y0-1, shoe);
      }
    }
    // tronco
    const top = 6 + y0;
    for (let y = top; y < top+5; y++) for (let x = 4; x < 8; x++) {
      let c = shirt;
      if (look.estampa === 'listrada' && (y-top) % 2 === 1) c = shirt2;
      if (look.estampa === 'duas_cores' && x >= 6) c = shirt2;
      P(x, y, c);
    }
    if (look.estampa !== 'listrada') for (let x = 4; x < 8; x++) P(x, top+4, sh(shirt, 0.8));
    if (dirc === 'down') { P(5, top, sh(skin, 0.85)); P(6, top, sh(skin, 0.85)); }
    if (look.baixo === 'saia' || look.baixo === 'vestido') {
      const sc = vestido ? shirt : bot;
      for (let x = 4; x < 8; x++) P(x, top+5, sc);
      for (let x = 3; x < 9; x++) P(x, top+6, sc);
      if (vestido) for (let x = 3; x < 9; x++) P(x, top+7, sh(sc, 0.82));
    } else if (look.baixo === 'bermuda') {
      for (let x = 4; x < 8; x++) P(x, top+5, bot);
      P(4, top+6, bot); P(7, top+6, bot);
    } else {
      for (let x = 4; x < 8; x++) P(x, top+5, bot);
    }
    // braços
    const swing = {0:0,1:1,2:0,3:-1}[frame];
    const sl = look.estampa === 'regata' ? skin : shirt;
    if (dirc === 'down' || dirc === 'up') {
      [[-1,3],[1,8]].forEach(([side, x]) => {
        const dy = swing*side;
        P(x, top+dy, sl); P(x, top+dy+1, sh(sl, 0.9));
        P(x, top+dy+2, skin); P(x, top+dy+3, sh(skin, 0.9));
      });
    } else {
      const ax = 6 + swing;
      P(ax, top+1, sh(sl, 0.85)); P(ax, top+2, sh(sl, 0.85)); P(ax, top+3, skin);
    }
    // cabeça
    const hy = y0;
    for (let y = hy; y < hy+6; y++) for (let x = 3; x < 9; x++) P(x, y, skin);
    const hs = look.cabelo;
    const EYE = [40,30,34], GL = [30,30,40];
    if (dirc === 'down') {
      P(4, hy+3, EYE); P(7, hy+3, EYE);
      const brow = hs !== 'careca' ? sh(hair, 0.8) : sh(skin, 0.8);
      P(4, hy+2, brow); P(7, hy+2, brow);
      P(5, hy+5, sh(skin, 0.8)); P(6, hy+5, sh(skin, 0.8));
      P(3, hy+4, sh(skin, 0.9)); P(8, hy+4, sh(skin, 0.9));
      if (look.oculos) {
        for (const x of [3,4,7,8]) P(x, hy+3, GL);
        P(5, hy+3, GL); P(6, hy+3, GL); P(4, hy+3, [120,170,220]); P(7, hy+3, [120,170,220]);
      }
      if (look.barba) { for (let x = 3; x < 9; x++) P(x, hy+5, hair); P(3, hy+4, hair); P(8, hy+4, hair); }
    } else if (dirc === 'right') {
      P(7, hy+3, EYE); P(8, hy+4, sh(skin, 0.9)); P(9, hy+3, skin);
      if (look.oculos) { P(7, hy+3, GL); P(8, hy+3, GL); }
      if (look.barba) for (let x = 5; x < 9; x++) P(x, hy+5, hair);
    }
    const hp = (x, y, c) => P(x, y, c || hair);
    const hl = sh(hair, 1.25);
    if (hs !== 'careca') {
      const rows = hs === 'raspado' ? 1 : 2;
      for (let y = hy-1; y < hy+rows; y++) for (let x = 3; x < 9; x++) hp(x, y);
      hp(4, hy-1, hl); hp(5, hy-1, hl);
      if (dirc === 'down') {
        if (['curto','franja','afro','rabo','coque'].includes(hs)) { hp(3, hy+2); hp(8, hy+2); }
        if (hs === 'franja') for (let x = 3; x < 8; x++) hp(x, hy+2);
        if (hs === 'longo') { for (let y = hy+1; y < hy+9; y++) { hp(2, y); hp(9, y); } hp(3, hy+2); hp(8, hy+2); }
      }
      if (dirc === 'up') {
        for (let y = hy; y < hy+6; y++) for (let x = 3; x < 9; x++) hp(x, y, y < hy+5 ? hair : sh(hair, 0.85));
        if (hs === 'raspado') for (let y = hy+2; y < hy+6; y++) for (let x = 3; x < 9; x++) P(x, y, sh(skin, 0.85));
        if (hs === 'longo') for (let y = hy+6; y < hy+9; y++) for (let x = 3; x < 9; x++) hp(x, y);
        if (hs === 'rabo') { hp(5, hy+6); hp(6, hy+6); hp(5, hy+7); hp(6, hy+7); }
      }
      if (dirc === 'right') {
        for (let y = hy; y < hy+4; y++) { hp(3, y); hp(4, y); }
        hp(5, hy+1);
        if (hs === 'longo') for (let y = hy+4; y < hy+9; y++) { hp(3, y); hp(4, y); }
        if (hs === 'rabo') { hp(2, hy+2); hp(1, hy+3); hp(2, hy+3); hp(1, hy+4); }
      }
      if (hs === 'coque') { for (const x of [5,6]) { hp(x, hy-2); hp(x, hy-3); } hp(4, hy-2); hp(7, hy-2); }
      if (hs === 'afro') { for (let y = hy-2; y < hy+3; y++) { hp(2, y); hp(9, y); } for (let x = 3; x < 9; x++) hp(x, hy-2); }
    } else {
      P(4, hy, sh(skin, 1.2)); P(5, hy, sh(skin, 1.2));
    }
    if (hs !== 'afro') { set(3, hy-1, 0,0,0,0); set(8, hy-1, 0,0,0,0); }
    if (!look.barba && !(hs === 'longo' && dirc !== 'right')) { set(3, hy+5, 0,0,0,0); set(8, hy+5, 0,0,0,0); }
    // chapéu
    if (hat === 'bone') {
      for (let x = 3; x < 9; x++) { P(x, hy-1, hatc); P(x, hy, hatc); }
      P(4, hy-1, sh(hatc, 1.3));
      if (dirc === 'down') for (let x = 3; x < 9; x++) P(x, hy+1, sh(hatc, 0.75));
      else if (dirc === 'right') { P(9, hy+1, sh(hatc, 0.75)); P(10, hy+1, sh(hatc, 0.75)); }
    } else if (hat === 'palha') {
      const c = [226,196,112];
      for (let x = 1; x < 11; x++) P(x, hy+1, sh(c, 0.85));
      for (let x = 3; x < 9; x++) { P(x, hy, c); P(x, hy-1, c); }
      P(4, hy-1, sh(c, 1.2));
    } else if (hat === 'gorro') {
      for (let x = 3; x < 9; x++) { P(x, hy-1, hatc); P(x, hy, hatc); P(x, hy+1, sh(hatc, 0.8)); }
      P(5, hy-2, [250,250,250]); P(6, hy-2, [250,250,250]);
    }
    // contorno escuro por fora da silhueta
    const a = i => p[i*4+3];
    const add = [];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const i = y*W+x;
      if (a(i) > 200) continue;
      if ((y > 0 && a(i-W) === 255) || (y < H-1 && a(i+W) === 255) || (x > 0 && a(i-1) === 255) || (x < W-1 && a(i+1) === 255)) add.push(i);
    }
    for (const i of add) { p[i*4] = OUT[0]; p[i*4+1] = OUT[1]; p[i*4+2] = OUT[2]; p[i*4+3] = 255; }
    return p;
  }

  // folha 48x72 (4 direções x 4 quadros), mesmo layout da célula do atlas
  function folha(look) {
    const out = new Uint8ClampedArray(48*72*4);
    DIRS.forEach((d, di) => {
      for (let fr = 0; fr < 4; fr++) {
        const s = desenhar(look, d, fr);
        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
          const si = (y*W+x)*4, oi = ((di*18+y)*48 + fr*12+x)*4;
          for (let k = 0; k < 4; k++) out[oi+k] = s[si+k];
        }
      }
    });
    return out;
  }

  // ep. 7 (32 bits): opções novas. O desenho de 16 bits ignora o que não conhece (cabelo vira o padrão,
  // chapéu/acessório não aparecem); o de 32 bits (char32.js) desenha tudo.
  const HAIRSTYLES_32 = [...HAIRSTYLES, 'moicano', 'trancas', 'cacheado', 'topete'];
  const ESTAMPAS_32 = [...ESTAMPAS, 'xadrez', 'time'];
  const CHAPEUS_32 = [...CHAPEUS, 'boina', 'coroa', 'bandana'];
  const ACESSORIOS = [null, 'mochila', 'cachecol', 'colar', 'fone', 'oculos_sol'];
  function normalizar(l) {
    const n = (v, max, d) => (Number.isInteger(v) && v >= 0 && v < max) ? v : d;
    const out = {
      pele: n(l.pele, 6, 0), cabelo: HAIRSTYLES_32.includes(l.cabelo) ? l.cabelo : 'curto', cor_cabelo: n(l.cor_cabelo, 8, 0),
      camisa: n(l.camisa, 12, 0), estampa: ESTAMPAS_32.includes(l.estampa) ? l.estampa : 'lisa', camisa2: n(l.camisa2, 12, 0),
      baixo: BAIXOS.includes(l.baixo) ? l.baixo : 'calca', cor_baixo: n(l.cor_baixo, 6, 0), sapato: n(l.sapato, 4, 0),
      oculos: !!l.oculos, chapeu: CHAPEUS_32.includes(l.chapeu) ? l.chapeu : null, cor_chapeu: n(l.cor_chapeu, 12, 0), barba: !!l.barba,
    };
    // acessório só entra no visual quando existe (assim os visuais antigos continuam idênticos)
    if (ACESSORIOS.includes(l.acessorio) && l.acessorio) { out.acessorio = l.acessorio; out.cor_acessorio = n(l.cor_acessorio, 12, 0); }
    return out;
  }

  const api = { desenhar, folha, normalizar, SKIN16, HAIR16, SHIRT16, PANTS16, SHOES16, HAIRSTYLES, ESTAMPAS, BAIXOS, CHAPEUS, DIRS,
                HAIRSTYLES_32, ESTAMPAS_32, CHAPEUS_32, ACESSORIOS };
  if (typeof module !== 'undefined') module.exports = api; else root.Sprites = api;
})(this);
