// =====================================================================
//  Moradores 32 BITS (ep. 7+) — porta fiel de codigo/char32.py (npc32)
//  32x48 px. As formas curvas (elipse, arco, polígono...) vêm prontas do
//  formas32.js (gerado pelo Python), então o desenho sai pixel por pixel
//  igual ao vídeo. Funciona no navegador e no Node.
// =====================================================================
(function (root) {
  const S16 = (typeof module !== 'undefined') ? require('./sprites.js') : root.Sprites;
  const FORMAS = (typeof module !== 'undefined') ? require('./formas32.js') : root.FORMAS32;
  const { SKIN16, HAIR16, SHIRT16, PANTS16, SHOES16 } = S16;
  const W = 32, H = 48, OUT = [34, 28, 40];
  const faltando = new Set();

  const A = (c, a = 255) => [Math.trunc(c[0]), Math.trunc(c[1]), Math.trunc(c[2]), a];
  function sh(c, f) {
    if (f <= 1) return [Math.trunc(c[0] * f), Math.trunc(c[1] * f), Math.trunc(c[2] * f)];
    return [Math.trunc(c[0] + (255 - c[0]) * (f - 1)), Math.trunc(c[1] + (255 - c[1]) * (f - 1)), Math.trunc(c[2] + (255 - c[2]) * (f - 1))];
  }

  function npc32(look, dirc = 'down', frame = 0) {
    if (dirc === 'left') {
      const r = npc32(look, 'right', frame), o = new Uint8ClampedArray(W * H * 4);
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) for (let k = 0; k < 4; k++) o[(y * W + x) * 4 + k] = r[(y * W + (W - 1 - x)) * 4 + k];
      return o;
    }
    const p = new Uint8ClampedArray(W * H * 4);
    const set = (x, y, c) => { if (x >= 0 && x < W && y >= 0 && y < H) { const i = (y * W + x) * 4; p[i] = c[0]; p[i + 1] = c[1]; p[i + 2] = c[2]; p[i + 3] = c[3]; } };
    const forma = (tipo, nums, c) => {
      const k = tipo + ':' + nums.join(','), runs = FORMAS[k];
      if (!runs) { faltando.add(k); return; }
      for (let j = 0; j < runs.length; j += 2) for (let i = runs[j]; i < runs[j] + runs[j + 1]; i++) { const o = i * 4; p[o] = c[0]; p[o + 1] = c[1]; p[o + 2] = c[2]; p[o + 3] = c[3]; }
    };
    const d = {
      point: (x, y, c) => set(x, y, c),
      rect: (x0, y0, x1, y1, c) => { for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) set(x, y, c); },
      rectOut: (x0, y0, x1, y1, c) => forma('o', [x0, y0, x1, y1], c),
      ellipse: (x0, y0, x1, y1, c) => forma('e', [x0, y0, x1, y1], c),
      chord: (x0, y0, x1, y1, a, b, c) => forma('c', [x0, y0, x1, y1, a, b], c),
      arc: (x0, y0, x1, y1, a, b, c) => forma('a', [x0, y0, x1, y1, a, b], c),
      rrect: (x0, y0, x1, y1, r, c) => forma('r', [x0, y0, x1, y1, r], c),
      poly: (pts, c) => forma('p', pts, c),
      line: (pts, c) => forma('l', pts, c),
    };
    const g = (k, def) => (look[k] === undefined ? def : look[k]);
    const skin = SKIN16[look.pele], hair = HAIR16[look.cor_cabelo];
    const shirt = SHIRT16[look.camisa], shirt2 = SHIRT16[look.camisa2];
    const bot = PANTS16[look.cor_baixo], shoe = SHOES16[look.sapato];
    const hat = g('chapeu', null), hatc = SHIRT16[g('cor_chapeu', 0)];
    const est = g('estampa', 'lisa'), baixo = g('baixo', 'calca'), hs = g('cabelo', 'curto');
    const aces = g('acessorio', null), acc = SHIRT16[g('cor_acessorio', 0) || 0];
    const side = dirc === 'right', back = dirc === 'up';
    const bob = (frame === 1 || frame === 3) ? 1 : 0;
    const sw = [0, 2, 0, -2][frame % 4];
    const y0 = bob, fl = Math.floor;
    // ---------- pernas ----------
    const lx = !side ? [12, 17] : [14, 15];
    lx.forEach((x, k) => {
      const off = k === 0 ? sw : -sw;
      const xo = x + (side ? off : 0), yo = 30 + y0;
      const legLen = 13 - (!side ? fl(Math.abs(off) / 2) : 0);
      const lc = ['bermuda', 'saia', 'vestido'].includes(baixo) ? skin : bot;
      d.rect(xo, yo, xo + 3, yo + legLen, A(lc));
      d.line([xo + 3, yo, xo + 3, yo + legLen], A(sh(lc, 0.8)));
      if (baixo === 'bermuda') { d.rect(xo, yo, xo + 3, yo + 5, A(bot)); d.line([xo + 3, yo, xo + 3, yo + 5], A(sh(bot, 0.8))); }
      if (baixo === 'calca') d.point(xo + 1, yo + 7, A(sh(bot, 0.85)));
      const sy = yo + legLen + 1;
      if (side) { d.rect(xo, sy, xo + 5, sy + 2, A(shoe)); d.line([xo, sy + 2, xo + 5, sy + 2], A(sh(shoe, 0.6))); }
      else { d.rect(xo - 1, sy, xo + 4, sy + 2, A(shoe)); d.line([xo - 1, sy + 2, xo + 4, sy + 2], A(sh(shoe, 0.6))); d.point(xo, sy, A(sh(shoe, 1.3))); }
    });
    // ---------- tronco ----------
    const [tx0, tx1] = !side ? [10, 21] : [12, 20];
    const ty0 = 17 + y0, ty1 = 31 + y0;
    if (aces === 'mochila' && side) { d.rect(tx0 - 4, ty0 + 2, tx0, ty0 + 11, A(acc)); d.line([tx0 - 4, ty0 + 5, tx0, ty0 + 5], A(sh(acc, 0.75))); }
    const tc = shirt;
    d.rrect(tx0, ty0, tx1, ty1, 3, A(tc));
    if (est === 'listrada') { for (let y = ty0 + 2; y < ty1; y += 3) d.line([tx0 + 1, y, tx1 - 1, y], A(shirt2)); }
    else if (est === 'duas_cores') { d.rect(tx0, ty0 + 7, tx1, ty1 - 1, A(shirt2)); d.line([tx0, ty0 + 7, tx1, ty0 + 7], A(sh(shirt2, 0.8))); }
    else if (est === 'xadrez') {
      for (let y = ty0 + 2; y < ty1; y += 3) d.line([tx0 + 1, y, tx1 - 1, y], A(shirt2));
      for (let x = tx0 + 2; x < tx1; x += 3) d.line([x, ty0 + 1, x, ty1 - 3], A(shirt2));
    } else if (est === 'time') d.rect(15, ty0 + 1, 16, ty1 - 3, A(shirt2));
    if (baixo === 'vestido') {
      d.poly([tx0, ty1 - 4, tx1, ty1 - 4, tx1 + 3, ty1 + 6, tx0 - 3, ty1 + 6], A(est !== 'lisa' ? shirt2 : shirt));
      d.line([tx1, ty1 - 4, tx1 + 3, ty1 + 6], A(sh(shirt, 0.75)));
    } else if (baixo === 'saia') {
      d.poly([tx0, ty1 - 2, tx1, ty1 - 2, tx1 + 2, ty1 + 5, tx0 - 2, ty1 + 5], A(bot));
      for (let x = tx0; x <= tx1; x += 3) d.line([x, ty1 - 1, x + (x > 16 ? 1 : -1), ty1 + 5], A(sh(bot, 0.82)));
    } else {
      d.rect(tx0, ty1 - 2, tx1, ty1 + 1, A(bot)); d.line([tx0, ty1 - 2, tx1, ty1 - 2], A(sh(bot, 0.7)));
      d.point(fl((tx0 + tx1) / 2), ty1 - 1, A([220, 190, 90]));
    }
    d.line([tx1, ty0 + 2, tx1, ty1 - 3], A(sh(tc, 0.72))); d.line([tx1 - 1, ty0 + 3, tx1 - 1, ty1 - 3], A(sh(tc, 0.86)));
    d.line([tx0 + 1, ty0 + 2, tx0 + 1, ty0 + 6], A(sh(tc, 1.18)));
    d.line([fl((tx0 + tx1) / 2) + 2, ty0 + 8, fl((tx0 + tx1) / 2) + 3, ty0 + 11], A(sh(tc, 0.85)));
    if (!side && !back) {
      if (est === 'regata') d.poly([14, ty0, 18, ty0, 17, ty0 + 3, 15, ty0 + 3], A(skin));
      else { d.line([14, ty0, 16, ty0 + 2], A(sh(tc, 0.7))); d.line([18, ty0, 16, ty0 + 2], A(sh(tc, 0.7))); }
    }
    if (est === 'time' && !side && !back) {
      d.poly([13, ty0, 19, ty0, 16, ty0 + 3], A(shirt2));
      for (const [rx, ry] of [[12, 5], [12, 6], [12, 7], [12, 8], [12, 9], [18, 5], [19, 5], [18, 9], [19, 9], [18, 6], [18, 7], [18, 8], [20, 5], [20, 6], [20, 7], [20, 8], [20, 9]]) d.point(rx, ty0 + ry, A([250, 250, 250]));
    }
    if (est === 'time' && back) { d.rect(13, ty0 + 3, 14, ty0 + 9, A([250, 250, 250])); d.rect(17, ty0 + 3, 18, ty0 + 9, A([250, 250, 250])); }
    if (aces === 'colar' && !side && !back) {
      for (const [cx, cy] of [[13, 1], [14, 2], [15, 3], [16, 3], [17, 2], [18, 1]]) d.point(cx, ty0 + cy, A([240, 200, 60]));
      d.rect(15, ty0 + 4, 16, ty0 + 5, A(acc));
    }
    if (aces === 'mochila' && back) {
      d.rrect(tx0 + 1, ty0 + 1, tx1 - 1, ty0 + 12, 2, A(acc)); d.line([tx0 + 2, ty0 + 5, tx1 - 2, ty0 + 5], A(sh(acc, 0.7)));
      d.rect(14, ty0 + 7, 17, ty0 + 10, A(sh(acc, 1.25)));
    }
    // ---------- braços ----------
    const arms = !side ? [[tx0 - 3, -sw], [tx1 + 1, sw]] : [[15 + fl(sw / 2), sw]];
    for (const [ax, asw] of arms) {
      const ay = ty0 + 1, sleeve = est === 'regata' ? skin : (est === 'time' ? shirt2 : tc), s2 = side ? fl(asw / 2) : 0, so = side ? asw : 0;
      d.rrect(ax, ay, ax + 2, ay + 5, 1, A(sleeve));
      d.rect(ax, ay + 5, ax + 2, ay + 10 + s2, A(skin));
      d.line([ax + 2, ay + 1, ax + 2, ay + 10], A(sh(skin, 0.8)));
      const hy = ay + 11 + s2;
      d.ellipse(ax - 1 + so, hy - 1, ax + 3 + so, hy + 2, A(skin));
    }
    if (aces === 'mochila' && !side && !back) { d.line([tx0 + 2, ty0, tx0 + 2, ty0 + 9], A(sh(acc, 0.8))); d.line([tx1 - 2, ty0, tx1 - 2, ty0 + 9], A(sh(acc, 0.8))); }
    // ---------- pescoço e cabeça ----------
    d.rect(14, 14 + y0, 17, 17 + y0, A(sh(skin, 0.85)));
    if (aces === 'cachecol') {
      d.rect(12, ty0 - 2, 19, ty0 + 1, A(acc)); d.line([12, ty0, 19, ty0], A(sh(acc, 0.8)));
      if (side) d.rect(12, ty0 + 1, 13, ty0 + 6, A(sh(acc, 0.9)));
      else if (!back) { d.rect(17, ty0 + 1, 18, ty0 + 7, A(acc)); d.point(17, ty0 + 7, A(sh(acc, 0.7))); }
    }
    const [hx0, hx1, hy0, hy1] = !side ? [9, 22, 2 + y0, 16 + y0] : [10, 22, 2 + y0, 16 + y0];
    if (hs === 'afro' && !back) { d.ellipse(hx0 - 4, hy0 - 4, hx1 + 4, hy0 + 13, A(hair)); d.arc(hx0 - 3, hy0 - 3, hx1 + 3, hy0 + 12, 200, 260, A(sh(hair, 1.35))); }
    d.ellipse(hx0, hy0, hx1, hy1, A(skin));
    d.arc(hx0, hy0, hx1, hy1, 300, 80, A(sh(skin, 0.82)));
    if (!side) { d.ellipse(hx0 - 1, hy0 + 6, hx0 + 1, hy0 + 9, A(skin)); d.ellipse(hx1 - 1, hy0 + 6, hx1 + 1, hy0 + 9, A(sh(skin, 0.9))); }
    else { d.ellipse(13, hy0 + 6, 15, hy0 + 9, A(sh(skin, 0.9))); d.point(14, hy0 + 7, A(sh(skin, 0.7))); }
    // ---------- rosto ----------
    const ey = hy0 + 7;
    if (!back) {
      if (!side) {
        for (const ex of [12, 18]) {
          d.rect(ex, ey, ex + 1, ey + 1, A([250, 250, 250])); d.point(ex + 1, ey, A([30, 30, 40])); d.point(ex + 1, ey + 1, A([30, 30, 40]));
          d.point(ex + 1, ey, A([60, 90, 140]));
          d.line([ex - 1, ey - 2, ex + 1, ey - 2], A(sh(hair, 0.9)));
        }
        d.point(15, ey + 3, A(sh(skin, 0.75))); d.point(16, ey + 3, A(sh(skin, 0.85)));
        d.line([14, ey + 5, 17, ey + 5], A([150, 70, 60])); d.point(14, ey + 4, A([150, 70, 60]));
        d.point(17, ey + 4, A([150, 70, 60]));
        const bochecha = A([Math.min(255, skin[0] + 10), Math.max(0, skin[1] - 30), Math.max(0, skin[2] - 30)]);
        d.point(11, ey + 3, bochecha); d.point(20, ey + 3, bochecha);
      } else {
        d.rect(19, ey, 20, ey + 1, A([250, 250, 250])); d.point(20, ey, A([30, 30, 40])); d.point(20, ey + 1, A([30, 30, 40]));
        d.line([18, ey - 2, 20, ey - 2], A(sh(hair, 0.9)));
        d.point(23, ey + 3, A(skin)); d.point(23, ey + 2, A(skin)); d.point(22, ey + 3, A(sh(skin, 0.8)));
        d.line([20, ey + 5, 22, ey + 5], A([150, 70, 60]));
      }
      if (g('barba', false)) {
        d.poly([hx0 + 2, ey + 3, hx1 - 2, ey + 3, hx1 - 3, hy1, fl((hx0 + hx1) / 2), hy1 + 1, hx0 + 3, hy1], A(sh(hair, 0.95)));
        d.line([14, ey + 5, 17, ey + 5], !side ? A([150, 70, 60]) : A(sh(hair, 0.95)));
      }
      if (g('oculos', false)) {
        if (!side) {
          d.rectOut(11, ey - 1, 14, ey + 2, A([30, 30, 40])); d.rectOut(17, ey - 1, 20, ey + 2, A([30, 30, 40]));
          d.line([14, ey, 17, ey], A([30, 30, 40])); d.point(12, ey, A([210, 230, 250]));
        } else { d.rectOut(18, ey - 1, 21, ey + 2, A([30, 30, 40])); d.line([14, ey, 18, ey], A([30, 30, 40])); }
      }
      if (aces === 'oculos_sol') {
        if (!side) {
          d.rect(11, ey - 1, 14, ey + 2, A([24, 24, 32])); d.rect(17, ey - 1, 20, ey + 2, A([24, 24, 32]));
          d.line([14, ey, 17, ey], A([24, 24, 32])); d.point(12, ey, A([110, 130, 170])); d.point(18, ey, A([110, 130, 170]));
        } else { d.rect(18, ey - 1, 21, ey + 2, A([24, 24, 32])); d.line([14, ey, 18, ey], A([24, 24, 32])); d.point(19, ey, A([110, 130, 170])); }
      }
    }
    // ---------- cabelo ----------
    const hc = A(hair), hl = A(sh(hair, 1.35)), hd = A(sh(hair, 0.7));
    if (hs === 'careca') { d.point(12, hy0 + 2, A([255, 255, 255])); d.point(13, hy0 + 2, A([255, 255, 255])); }
    else if (hs === 'raspado') d.chord(hx0, hy0, hx1, hy1 - 4, 180, 360, A(sh(hair, 1.0), 170));
    else if (hs === 'moicano') {
      d.chord(hx0, hy0, hx1, hy1 - 4, 180, 360, A(sh(hair, 1.0), 170));
      d.rect(14, hy0 - 4, 17, hy0 + 5, hc); d.line([14, hy0 - 4, 14, hy0 + 3], hl); d.line([17, hy0 - 3, 17, hy0 + 5], hd);
    } else if (hs === 'afro') {
      if (back) d.ellipse(hx0 - 4, hy0 - 4, hx1 + 4, hy0 + 13, hc); else d.chord(hx0 - 3, hy0 - 4, hx1 + 3, hy0 + 8, 180, 360, hc);
      for (const [px, py] of [[11, hy0 - 1], [15, hy0 - 2], [19, hy0], [10, hy0 + 3], [21, hy0 + 4]]) d.point(px, py, hl);
    } else {
      if (hs === 'cacheado') d.chord(hx0 - 3, hy0 - 3, hx1 + 3, hy1 - 1, 175, 365, hc);
      d.chord(hx0 - 1, hy0 - 1, hx1 + 1, hy1 - 3, 175, 365, hc);
      if (back) d.rect(hx0 - 1, hy0 + 5, hx1 + 1, hy0 + (hs === 'longo' ? 16 : 10), hc);
      if (!back && !side) {
        if (hs === 'franja') { d.rect(hx0, hy0 + 3, hx1, hy0 + 5, hc); d.line([hx0 + 2, hy0 + 6, hx1 - 3, hy0 + 6], hc); }
        else d.poly([hx0, hy0 + 6, hx0 + 5, hy0 + 3, hx1 - 2, hy0 + 3, hx1, hy0 + 6, hx1, hy0 + 2, hx0, hy0 + 2], hc);
        d.rect(hx0 - 1, hy0 + 4, hx0, hs !== 'longo' ? hy0 + 9 : hy0 + 18, hc); d.rect(hx1, hy0 + 4, hx1 + 1, hs !== 'longo' ? hy0 + 9 : hy0 + 18, hd);
      }
      if (side) {
        d.poly([hx0 - 1, hy0 + 2, hx1, hy0 + 2, hx1 - 1, hy0 + 5, 17, hy0 + 5, 15, hy0 + 9, hx0 - 1, hy0 + 11], hc);
        if (hs === 'longo') d.rect(hx0 - 1, hy0 + 6, hx0 + 3, hy0 + 18, hc);
      }
      if (hs === 'rabo') {
        if (side) d.poly([hx0 - 1, hy0 + 5, hx0 - 5, hy0 + 9, hx0 - 4, hy0 + 15, hx0 + 1, hy0 + 9], hc);
        else if (back) { d.rect(14, hy0 + 8, 17, hy0 + 18, hc); d.ellipse(14, hy0 + 7, 17, hy0 + 10, A([220, 60, 90])); }
      }
      if (hs === 'coque') { d.ellipse(12, hy0 - 6, 19, hy0 + 1, hc); d.point(14, hy0 - 4, hl); }
      if (hs === 'topete' && !back) { d.ellipse(11, hy0 - 5, 19, hy0 + 2, hc); d.arc(12, hy0 - 4, 18, hy0 + 1, 200, 280, hl); }
      if (hs === 'trancas') {
        const bxs = back ? [12, 17] : (side ? [hx0 - 1] : [hx0 - 1, hx1 - 1]);
        for (const bx of bxs) {
          d.rect(bx, hy0 + 8, bx + 2, hy0 + 20, hc);
          for (let yy = hy0 + 10; yy < hy0 + 20; yy += 3) d.line([bx, yy, bx + 2, yy], hd);
          d.rect(bx, hy0 + 20, bx + 2, hy0 + 21, A(aces ? acc : [220, 60, 90]));
        }
      }
      if (hs === 'cacheado') for (const [px, py] of [[hx0 - 2, hy0 + 3], [hx0, hy0 - 1], [14, hy0 - 3], [18, hy0 - 2], [hx1 + 1, hy0 + 1], [hx1 + 2, hy0 + 5], [hx0 - 2, hy0 + 7]]) d.point(px, py, hl);
      d.arc(hx0 + 1, hy0, hx1 - 3, hy1 - 6, 200, 260, hl);
      d.arc(hx0, hy0 - 1, hx1 + 1, hy1 - 3, 300, 350, hd);
    }
    // ---------- chapéu ----------
    if (hat === 'bone') {
      d.chord(hx0 - 1, hy0 - 2, hx1 + 1, hy0 + 9, 180, 360, A(hatc)); d.arc(hx0 + 2, hy0 - 1, hx1 - 4, hy0 + 6, 200, 260, A(sh(hatc, 1.3)));
      if (side) d.rect(hx1 - 2, hy0 + 3, hx1 + 4, hy0 + 4, A(sh(hatc, 0.75)));
      else if (!back) d.rect(hx0 + 1, hy0 + 3, hx1 - 1, hy0 + 5, A(sh(hatc, 0.75)));
    } else if (hat === 'palha') {
      d.ellipse(hx0 - 5, hy0 + 1, hx1 + 5, hy0 + 6, A([226, 196, 110])); d.chord(hx0 + 1, hy0 - 4, hx1 - 1, hy0 + 6, 180, 360, A([214, 182, 96]));
      d.line([hx0 + 1, hy0 + 2, hx1 - 1, hy0 + 2], A([170, 60, 50]));
    } else if (hat === 'gorro') {
      d.chord(hx0 - 1, hy0 - 3, hx1 + 1, hy0 + 10, 180, 360, A(hatc));
      for (let x = hx0; x <= hx1; x += 2) d.point(x, hy0 + 3, A(sh(hatc, 0.75)));
      d.ellipse(14, hy0 - 6, 17, hy0 - 3, A(sh(hatc, 1.3)));
    } else if (hat === 'boina') {
      d.ellipse(hx0 - 2, hy0 - 2, hx1 + 1, hy0 + 5, A(hatc)); d.line([hx0, hy0 + 4, hx1 - 1, hy0 + 4], A(sh(hatc, 0.7)));
      d.arc(hx0, hy0 - 1, hx1 - 3, hy0 + 3, 200, 260, A(sh(hatc, 1.3))); d.point(15, hy0 - 2, A(sh(hatc, 0.8)));
    } else if (hat === 'coroa') {
      const gold = [238, 190, 40];
      d.rect(hx0 + 1, hy0 + 1, hx1 - 1, hy0 + 4, A(gold));
      for (const sx of [hx0 + 1, fl((hx0 + hx1) / 2) - 1, hx1 - 3]) d.poly([sx, hy0 + 1, sx + 2, hy0 + 1, sx + 1, hy0 - 2], A(gold));
      d.line([hx0 + 1, hy0 + 4, hx1 - 1, hy0 + 4], A(sh(gold, 0.7))); d.point(fl((hx0 + hx1) / 2), hy0 + 2, A([220, 40, 60]));
      d.point(hx0 + 3, hy0 + 2, A([60, 140, 230])); d.point(hx1 - 3, hy0 + 2, A([60, 180, 90]));
    } else if (hat === 'bandana') {
      d.chord(hx0 - 1, hy0 - 2, hx1 + 1, hy0 + 7, 180, 360, A(hatc)); d.rect(hx0 - 1, hy0 + 2, hx1 + 1, hy0 + 3, A(sh(hatc, 0.8)));
      for (const [px, py] of [[12, hy0], [16, hy0 - 1], [19, hy0 + 1], [14, hy0 + 2]]) d.point(px, py, A(sh(hatc, 1.45)));
      if (side || back) d.poly([hx0 - 1, hy0 + 2, hx0 - 5, hy0 + 5, hx0 - 3, hy0 + 7, hx0 + 1, hy0 + 4], A(hatc));
    }
    if (aces === 'fone') {
      d.arc(hx0 - 2, hy0 - 3, hx1 + 2, hy0 + 12, 180, 360, A([44, 44, 52]));
      if (side) d.rrect(13, hy0 + 5, 17, hy0 + 11, 1, A(acc));
      else { d.rect(hx0 - 3, hy0 + 5, hx0, hy0 + 10, A(acc)); d.rect(hx1, hy0 + 5, hx1 + 3, hy0 + 10, A(sh(acc, 0.85))); }
    }
    // ---------- contorno + sombra no chão (igual ao Pillow alpha_composite) ----------
    const out = new Uint8ClampedArray(p), add = [];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const i = y * W + x; if (p[i * 4 + 3] > 0) continue;
      if ((y > 0 && p[(i - W) * 4 + 3] > 0) || (y < H - 1 && p[(i + W) * 4 + 3] > 0) || (x > 0 && p[(i - 1) * 4 + 3] > 0) || (x < W - 1 && p[(i + 1) * 4 + 3] > 0)) add.push(i);
    }
    for (const i of add) { out[i * 4] = OUT[0]; out[i * 4 + 1] = OUT[1]; out[i * 4 + 2] = OUT[2]; out[i * 4 + 3] = 255; }
    const sim = new Uint8ClampedArray(W * H * 4), sr = FORMAS['e:8,44,24,47'] || [];
    for (let j = 0; j < sr.length; j += 2) for (let i = sr[j]; i < sr[j] + sr[j + 1]; i++) sim[i * 4 + 3] = 70;
    const D255 = v => (((v >> 8) + v) >> 8), PB = 7;
    for (let i = 0; i < W * H; i++) {
      const o = i * 4, sa = out[o + 3]; if (sa === 0) continue;
      const da = sim[o + 3];
      const blend = da * (255 - sa), outa = sa * 255 + blend;
      const c1 = Math.floor(sa * 255 * 255 * (1 << PB) / outa), c2 = 255 * (1 << PB) - c1;
      for (let k = 0; k < 3; k++) sim[o + k] = D255(out[o + k] * c1 + sim[o + k] * c2 + (0x80 << PB)) >> PB;
      sim[o + 3] = D255(outa + 0x80);
    }
    return sim;
  }

  // folha 128x192 (4 direções x 4 quadros de 32x48), mesmo layout do atlas de 16 bits
  const DIRS = ['down', 'left', 'right', 'up'];
  function folha(look) {
    const out = new Uint8ClampedArray(128 * 192 * 4);
    DIRS.forEach((dd, di) => {
      for (let fr = 0; fr < 4; fr++) {
        const s = npc32(look, dd, fr);
        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
          const si = (y * W + x) * 4, oi = ((di * H + y) * 128 + fr * W + x) * 4;
          for (let k = 0; k < 4; k++) out[oi + k] = s[si + k];
        }
      }
    });
    return out;
  }

  // opções da personalização maior (ep. 7)
  const OPCOES32 = {
    cabelo: ['curto', 'raspado', 'longo', 'rabo', 'coque', 'afro', 'careca', 'franja', 'moicano', 'trancas', 'cacheado', 'topete'],
    chapeu: [null, 'bone', 'palha', 'gorro', 'boina', 'coroa', 'bandana'],
    estampa: ['lisa', 'listrada', 'regata', 'duas_cores', 'xadrez', 'time'],
    acessorio: [null, 'mochila', 'cachecol', 'colar', 'fone', 'oculos_sol'],
  };
  const api = { npc32, folha, OPCOES32, faltando, W, H };
  if (typeof module !== 'undefined') module.exports = api; else root.Char32 = api;
})(this);
