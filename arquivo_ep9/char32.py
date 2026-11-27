# Moradores em 32 BITS (ep. 7): desenho novo, 32x48, a partir do MESMO visual do site
# (npc_look / registrados.json). Rosto com olhos, sobrancelha, nariz e boca; cabelo com brilho;
# roupa com dobras e sombra; braços e pernas animados; acessórios.
# Ep. 7 (site): opções novas no look — cabelo moicano/trancas/cacheado/topete, chapéu boina/coroa/bandana,
# estampa xadrez/time, e 'acessorio' (mochila, cachecol, colar, fone, oculos_sol) com 'cor_acessorio'.
# Looks sem essas opções saem exatamente como antes. O site desenha igual (site/js/char32.js + formas32.js).
from PIL import Image, ImageDraw
import numpy as np
from world16 import SKIN16, HAIR16, SHIRT16, PANTS16, SHOES16

W32, H32 = 32, 48
OUT = (34, 28, 40)
def A(c, a=255): return tuple(int(v) for v in c[:3])+(a,)
def sh(c, f):
    if f <= 1: return tuple(int(v*f) for v in c[:3])
    return tuple(int(v+(255-v)*(f-1)) for v in c[:3])

def _outline(im):
    a = np.array(im); al = a[:, :, 3] > 0
    o = np.zeros_like(al)
    o[1:, :] |= al[:-1, :]; o[:-1, :] |= al[1:, :]; o[:, 1:] |= al[:, :-1]; o[:, :-1] |= al[:, 1:]
    o &= ~al
    a[o] = A(OUT)
    return Image.fromarray(a)

def npc32(look, dirc='down', frame=0, uniforme=None, tool=None, carry=None):
    if dirc == 'left':
        return npc32(look, 'right', frame, uniforme, tool, carry).transpose(Image.FLIP_LEFT_RIGHT)
    im = Image.new('RGBA', (W32, H32), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    skin = SKIN16[look['pele']]; hair = HAIR16[look['cor_cabelo']]
    shirt = SHIRT16[look['camisa']]; shirt2 = SHIRT16[look['camisa2']]
    bot = PANTS16[look['cor_baixo']]; shoe = SHOES16[look['sapato']]
    hat = look.get('chapeu'); hatc = SHIRT16[look.get('cor_chapeu', 0)]
    est = look.get('estampa', 'lisa'); baixo = look.get('baixo', 'calca'); hs = look.get('cabelo', 'curto')
    aces = look.get('acessorio'); acc = SHIRT16[look.get('cor_acessorio', 0) or 0]
    if uniforme == 'pedreiro': shirt = (240, 128, 30); shirt2 = (250, 220, 60); hat = 'capacete'; hatc = (250, 206, 40); est = 'colete'
    if uniforme == 'mercado': est = 'avental'
    side = dirc == 'right'; back = dirc == 'up'
    bob = 1 if frame in (1, 3) else 0
    sw = [0, 2, 0, -2][frame % 4]                    # balanço de braço/perna
    y0 = bob
    # ---------- pernas ----------
    lx = (12, 17) if not side else (14, 15)
    for k, x in enumerate(lx):
        off = (sw if k == 0 else -sw) if not side else (sw if k == 0 else -sw)
        xo = x+(off if side else 0); yo = 30+y0
        leg_len = 13-(abs(off)//2 if not side else 0)
        lc = skin if baixo in ('bermuda', 'saia', 'vestido') else bot
        d.rectangle([xo, yo, xo+3, yo+leg_len], fill=A(lc))
        d.line([xo+3, yo, xo+3, yo+leg_len], fill=A(sh(lc, 0.8)))
        if baixo == 'bermuda': d.rectangle([xo, yo, xo+3, yo+5], fill=A(bot)); d.line([xo+3, yo, xo+3, yo+5], fill=A(sh(bot, 0.8)))
        if baixo == 'calca': d.point((xo+1, yo+7), fill=A(sh(bot, 0.85)))
        # sapato
        sy = yo+leg_len+1
        if side: d.rectangle([xo, sy, xo+5, sy+2], fill=A(shoe)); d.line([xo, sy+2, xo+5, sy+2], fill=A(sh(shoe, 0.6)))
        else: d.rectangle([xo-1, sy, xo+4, sy+2], fill=A(shoe)); d.line([xo-1, sy+2, xo+4, sy+2], fill=A(sh(shoe, 0.6))); d.point((xo, sy), fill=A(sh(shoe, 1.3)))
    # ---------- tronco ----------
    tx0, tx1 = (10, 21) if not side else (12, 20)
    ty0, ty1 = 17+y0, 31+y0
    if aces == 'mochila' and side:
        d.rectangle([tx0-4, ty0+2, tx0, ty0+11], fill=A(acc)); d.line([tx0-4, ty0+5, tx0, ty0+5], fill=A(sh(acc, 0.75)))
    tc = shirt
    d.rounded_rectangle([tx0, ty0, tx1, ty1], radius=3, fill=A(tc))
    if est == 'listrada':
        for y in range(ty0+2, ty1, 3): d.line([tx0+1, y, tx1-1, y], fill=A(shirt2))
    elif est == 'duas_cores':
        d.rectangle([tx0, ty0+7, tx1, ty1-1], fill=A(shirt2)); d.line([tx0, ty0+7, tx1, ty0+7], fill=A(sh(shirt2, 0.8)))
    elif est == 'xadrez':
        for y in range(ty0+2, ty1, 3): d.line([tx0+1, y, tx1-1, y], fill=A(shirt2))
        for x in range(tx0+2, tx1, 3): d.line([x, ty0+1, x, ty1-3], fill=A(shirt2))
    elif est == 'time':
        d.rectangle([15, ty0+1, 16, ty1-3], fill=A(shirt2))
    elif est == 'colete':
        d.rectangle([tx0+1, ty0+1, tx0+3, ty1-1], fill=A(shirt2)); d.rectangle([tx1-3, ty0+1, tx1-1, ty1-1], fill=A(shirt2))
        d.line([tx0, ty0+8, tx1, ty0+8], fill=A((250, 250, 250)))
    elif est == 'avental':
        d.rectangle([tx0+2, ty0+3, tx1-2, ty1+3], fill=A((40, 150, 70))); d.line([tx0+2, ty0+3, tx0+1, ty0], fill=A((40, 150, 70))); d.line([tx1-2, ty0+3, tx1-1, ty0], fill=A((40, 150, 70)))
    if baixo == 'vestido':
        d.polygon([(tx0, ty1-4), (tx1, ty1-4), (tx1+3, ty1+6), (tx0-3, ty1+6)], fill=A(shirt2 if est != 'lisa' else shirt))
        d.line([(tx1, ty1-4), (tx1+3, ty1+6)], fill=A(sh(shirt, 0.75)))
    elif baixo == 'saia':
        d.polygon([(tx0, ty1-2), (tx1, ty1-2), (tx1+2, ty1+5), (tx0-2, ty1+5)], fill=A(bot))
        for x in range(tx0, tx1+1, 3): d.line([x, ty1-1, x+(1 if x > 16 else -1), ty1+5], fill=A(sh(bot, 0.82)))
    else:
        d.rectangle([tx0, ty1-2, tx1, ty1+1], fill=A(bot)); d.line([tx0, ty1-2, tx1, ty1-2], fill=A(sh(bot, 0.7)))
        d.point(((tx0+tx1)//2, ty1-1), fill=A((220, 190, 90)))
    # sombra e luz no tronco + dobra
    d.line([tx1, ty0+2, tx1, ty1-3], fill=A(sh(tc, 0.72))); d.line([tx1-1, ty0+3, tx1-1, ty1-3], fill=A(sh(tc, 0.86)))
    d.line([tx0+1, ty0+2, tx0+1, ty0+6], fill=A(sh(tc, 1.18)))
    d.line([(tx0+tx1)//2+2, ty0+8, (tx0+tx1)//2+3, ty0+11], fill=A(sh(tc, 0.85)))
    if not side and not back:   # gola
        if est == 'regata': d.polygon([(14, ty0), (18, ty0), (17, ty0+3), (15, ty0+3)], fill=A(skin))
        else: d.line([14, ty0, 16, ty0+2], fill=A(sh(tc, 0.7))); d.line([18, ty0, 16, ty0+2], fill=A(sh(tc, 0.7)))
    if est == 'time' and not side and not back:
        d.polygon([(13, ty0), (19, ty0), (16, ty0+3)], fill=A(shirt2))
        for (rx, ry) in ((12, 5), (12, 6), (12, 7), (12, 8), (12, 9), (18, 5), (19, 5), (18, 9), (19, 9), (18, 6), (18, 7), (18, 8), (20, 5), (20, 6), (20, 7), (20, 8), (20, 9)):
            d.point((rx, ty0+ry), fill=A((250, 250, 250)))
    if est == 'time' and back:
        d.rectangle([13, ty0+3, 14, ty0+9], fill=A((250, 250, 250))); d.rectangle([17, ty0+3, 18, ty0+9], fill=A((250, 250, 250)))
    if aces == 'colar' and not side and not back:
        for (cx_, cy_) in ((13, 1), (14, 2), (15, 3), (16, 3), (17, 2), (18, 1)): d.point((cx_, ty0+cy_), fill=A((240, 200, 60)))
        d.rectangle([15, ty0+4, 16, ty0+5], fill=A(acc))
    if aces == 'mochila' and back:
        d.rounded_rectangle([tx0+1, ty0+1, tx1-1, ty0+12], radius=2, fill=A(acc)); d.line([tx0+2, ty0+5, tx1-2, ty0+5], fill=A(sh(acc, 0.7)))
        d.rectangle([14, ty0+7, 17, ty0+10], fill=A(sh(acc, 1.25)))
    # ---------- braços ----------
    arms = [(tx0-3, -sw), (tx1+1, sw)] if not side else [(15+sw//2, sw)]
    for (ax, a_sw) in arms:
        ay = ty0+1
        sleeve = skin if est == 'regata' else (shirt2 if est == 'time' else tc)
        d.rounded_rectangle([ax, ay, ax+2, ay+5], radius=1, fill=A(sleeve))
        d.rectangle([ax, ay+5, ax+2, ay+10+(a_sw//2 if side else 0)], fill=A(skin))
        d.line([ax+2, ay+1, ax+2, ay+10], fill=A(sh(skin, 0.8)))
        hy = ay+11+(a_sw//2 if side else 0)
        d.ellipse([ax-1+(a_sw if side else 0), hy-1, ax+3+(a_sw if side else 0), hy+2], fill=A(skin))
    if aces == 'mochila' and not side and not back:
        d.line([tx0+2, ty0, tx0+2, ty0+9], fill=A(sh(acc, 0.8))); d.line([tx1-2, ty0, tx1-2, ty0+9], fill=A(sh(acc, 0.8)))
    # ---------- pescoço e cabeça ----------
    d.rectangle([14, 14+y0, 17, 17+y0], fill=A(sh(skin, 0.85)))
    if aces == 'cachecol':
        d.rectangle([12, ty0-2, 19, ty0+1], fill=A(acc)); d.line([12, ty0, 19, ty0], fill=A(sh(acc, 0.8)))
        if side: d.rectangle([12, ty0+1, 13, ty0+6], fill=A(sh(acc, 0.9)))
        elif not back: d.rectangle([17, ty0+1, 18, ty0+7], fill=A(acc)); d.point((17, ty0+7), fill=A(sh(acc, 0.7)))
    hx0, hx1, hy0, hy1 = (9, 22, 2+y0, 16+y0) if not side else (10, 22, 2+y0, 16+y0)
    if hs == 'afro' and not back:      # o black power fica atrás da cabeça
        d.ellipse([hx0-4, hy0-4, hx1+4, hy0+13], fill=A(hair))
        d.arc([hx0-3, hy0-3, hx1+3, hy0+12], 200, 260, fill=A(sh(hair, 1.35)))
    d.ellipse([hx0, hy0, hx1, hy1], fill=A(skin))
    d.arc([hx0, hy0, hx1, hy1], 300, 80, fill=A(sh(skin, 0.82)))      # sombra lado direito / queixo
    if not side:
        d.ellipse([hx0-1, hy0+6, hx0+1, hy0+9], fill=A(skin)); d.ellipse([hx1-1, hy0+6, hx1+1, hy0+9], fill=A(sh(skin, 0.9)))
    else:
        d.ellipse([13, hy0+6, 15, hy0+9], fill=A(sh(skin, 0.9))); d.point((14, hy0+7), fill=A(sh(skin, 0.7)))
    # ---------- rosto ----------
    ey = hy0+7
    if not back:
        if not side:
            for ex in (12, 18):
                d.rectangle([ex, ey, ex+1, ey+1], fill=A((250, 250, 250))); d.point((ex+1, ey), fill=A((30, 30, 40))); d.point((ex+1, ey+1), fill=A((30, 30, 40)))
                d.point((ex+1, ey), fill=A((60, 90, 140)))
                d.line([ex-1, ey-2, ex+1, ey-2], fill=A(sh(hair, 0.9)))                 # sobrancelha
            d.point((15, ey+3), fill=A(sh(skin, 0.75))); d.point((16, ey+3), fill=A(sh(skin, 0.85)))   # nariz
            d.line([14, ey+5, 17, ey+5], fill=A((150, 70, 60))); d.point((14, ey+4), fill=A((150, 70, 60)))   # boca (sorriso)
            d.point((17, ey+4), fill=A((150, 70, 60)))
            d.point((11, ey+3), fill=A(sh(skin, 0.92)+(0,)) if False else A((min(255, skin[0]+10), max(0, skin[1]-30), max(0, skin[2]-30), 150)))
            d.point((20, ey+3), fill=A((min(255, skin[0]+10), max(0, skin[1]-30), max(0, skin[2]-30), 150)))
        else:
            d.rectangle([19, ey, 20, ey+1], fill=A((250, 250, 250))); d.point((20, ey), fill=A((30, 30, 40))); d.point((20, ey+1), fill=A((30, 30, 40)))
            d.line([18, ey-2, 20, ey-2], fill=A(sh(hair, 0.9)))
            d.point((23, ey+3), fill=A(skin)); d.point((23, ey+2), fill=A(skin)); d.point((22, ey+3), fill=A(sh(skin, 0.8)))
            d.line([20, ey+5, 22, ey+5], fill=A((150, 70, 60)))
        if look.get('barba'):
            d.polygon([(hx0+2, ey+3), (hx1-2, ey+3), (hx1-3, hy1), ((hx0+hx1)//2, hy1+1), (hx0+3, hy1)], fill=A(sh(hair, 0.95)))
            d.line([14, ey+5, 17, ey+5], fill=A((150, 70, 60)) if not side else A(sh(hair, 0.95)))
        if look.get('oculos'):
            if not side:
                d.rectangle([11, ey-1, 14, ey+2], outline=A((30, 30, 40))); d.rectangle([17, ey-1, 20, ey+2], outline=A((30, 30, 40)))
                d.line([14, ey, 17, ey], fill=A((30, 30, 40))); d.point((12, ey), fill=A((210, 230, 250)))
            else:
                d.rectangle([18, ey-1, 21, ey+2], outline=A((30, 30, 40))); d.line([14, ey, 18, ey], fill=A((30, 30, 40)))
        if aces == 'oculos_sol':
            if not side:
                d.rectangle([11, ey-1, 14, ey+2], fill=A((24, 24, 32))); d.rectangle([17, ey-1, 20, ey+2], fill=A((24, 24, 32)))
                d.line([14, ey, 17, ey], fill=A((24, 24, 32))); d.point((12, ey), fill=A((110, 130, 170))); d.point((18, ey), fill=A((110, 130, 170)))
            else:
                d.rectangle([18, ey-1, 21, ey+2], fill=A((24, 24, 32))); d.line([14, ey, 18, ey], fill=A((24, 24, 32))); d.point((19, ey), fill=A((110, 130, 170)))
    # ---------- cabelo ----------
    hc, hl, hd = A(hair), A(sh(hair, 1.35)), A(sh(hair, 0.7))
    if hs == 'careca':
        d.point((12, hy0+2), fill=A((255, 255, 255, 160))); d.point((13, hy0+2), fill=A((255, 255, 255, 110)))
    elif hs == 'raspado':
        d.chord([hx0, hy0, hx1, hy1-4], 180, 360, fill=A(sh(hair, 1.0), 170))
    elif hs == 'moicano':
        d.chord([hx0, hy0, hx1, hy1-4], 180, 360, fill=A(sh(hair, 1.0), 170))
        d.rectangle([14, hy0-4, 17, hy0+5], fill=hc); d.line([14, hy0-4, 14, hy0+3], fill=hl); d.line([17, hy0-3, 17, hy0+5], fill=hd)
    else:
        if hs == 'afro':
            if back: d.ellipse([hx0-4, hy0-4, hx1+4, hy0+13], fill=hc)
            else: d.chord([hx0-3, hy0-4, hx1+3, hy0+8], 180, 360, fill=hc)
            for (px_, py_) in ((11, hy0-1), (15, hy0-2), (19, hy0), (10, hy0+3), (21, hy0+4)): d.point((px_, py_), fill=hl)
        else:
            if hs == 'cacheado': d.chord([hx0-3, hy0-3, hx1+3, hy1-1], 175, 365, fill=hc)
            d.chord([hx0-1, hy0-1, hx1+1, hy1-3], 175, 365, fill=hc)                          # topo
            if back:   # (ep. 7: antes o 'longo' cobria o rosto na frente e de lado)
                d.rectangle([hx0-1, hy0+5, hx1+1, hy0+(16 if hs == 'longo' else 10)], fill=hc)
            if not back and not side:
                if hs == 'franja': d.rectangle([hx0, hy0+3, hx1, hy0+5], fill=hc); d.line([hx0+2, hy0+6, hx1-3, hy0+6], fill=hc)
                else: d.polygon([(hx0, hy0+6), (hx0+5, hy0+3), (hx1-2, hy0+3), (hx1, hy0+6), (hx1, hy0+2), (hx0, hy0+2)], fill=hc)
                d.rectangle([hx0-1, hy0+4, hx0, hy0+9 if hs != 'longo' else hy0+18], fill=hc); d.rectangle([hx1, hy0+4, hx1+1, hy0+9 if hs != 'longo' else hy0+18], fill=hd)
            if side:
                d.polygon([(hx0-1, hy0+2), (hx1, hy0+2), (hx1-1, hy0+5), (17, hy0+5), (15, hy0+9), (hx0-1, hy0+11)], fill=hc)
                if hs == 'longo': d.rectangle([hx0-1, hy0+6, hx0+3, hy0+18], fill=hc)
            if hs == 'rabo':
                if side: d.polygon([(hx0-1, hy0+5), (hx0-5, hy0+9), (hx0-4, hy0+15), (hx0+1, hy0+9)], fill=hc)
                elif back: d.rectangle([14, hy0+8, 17, hy0+18], fill=hc); d.ellipse([14, hy0+7, 17, hy0+10], fill=A((220, 60, 90)))
            if hs == 'coque': d.ellipse([12, hy0-6, 19, hy0+1], fill=hc); d.point((14, hy0-4), fill=hl)
            if hs == 'topete' and not back:
                d.ellipse([11, hy0-5, 19, hy0+2], fill=hc); d.arc([12, hy0-4, 18, hy0+1], 200, 280, fill=hl)
            if hs == 'trancas':
                bxs = (12, 17) if back else ((hx0-1,) if side else (hx0-1, hx1-1))
                for bx in bxs:
                    d.rectangle([bx, hy0+8, bx+2, hy0+20], fill=hc)
                    for yy in range(hy0+10, hy0+20, 3): d.line([bx, yy, bx+2, yy], fill=hd)
                    d.rectangle([bx, hy0+20, bx+2, hy0+21], fill=A(acc if aces else (220, 60, 90)))
            if hs == 'cacheado':
                for (px_, py_) in ((hx0-2, hy0+3), (hx0, hy0-1), (14, hy0-3), (18, hy0-2), (hx1+1, hy0+1), (hx1+2, hy0+5), (hx0-2, hy0+7)): d.point((px_, py_), fill=hl)
            # brilho e sombra do cabelo
            d.arc([hx0+1, hy0, hx1-3, hy1-6], 200, 260, fill=hl)
            d.arc([hx0, hy0-1, hx1+1, hy1-3], 300, 350, fill=hd)
    # ---------- chapéu ----------
    if hat == 'bone':
        d.chord([hx0-1, hy0-2, hx1+1, hy0+9], 180, 360, fill=A(hatc)); d.arc([hx0+2, hy0-1, hx1-4, hy0+6], 200, 260, fill=A(sh(hatc, 1.3)))
        if side: d.rectangle([hx1-2, hy0+3, hx1+4, hy0+4], fill=A(sh(hatc, 0.75)))
        elif not back: d.rectangle([hx0+1, hy0+3, hx1-1, hy0+5], fill=A(sh(hatc, 0.75)))
    elif hat == 'palha':
        d.ellipse([hx0-5, hy0+1, hx1+5, hy0+6], fill=A((226, 196, 110))); d.chord([hx0+1, hy0-4, hx1-1, hy0+6], 180, 360, fill=A((214, 182, 96)))
        d.line([hx0+1, hy0+2, hx1-1, hy0+2], fill=A((170, 60, 50)))
    elif hat == 'gorro':
        d.chord([hx0-1, hy0-3, hx1+1, hy0+10], 180, 360, fill=A(hatc))
        for x in range(hx0, hx1+1, 2): d.point((x, hy0+3), fill=A(sh(hatc, 0.75)))
        d.ellipse([14, hy0-6, 17, hy0-3], fill=A(sh(hatc, 1.3)))
    elif hat == 'capacete':
        d.chord([hx0-1, hy0-3, hx1+1, hy0+9], 180, 360, fill=A(hatc)); d.rectangle([hx0-2, hy0+3, hx1+2, hy0+4], fill=A(sh(hatc, 0.8)))
        d.line([15, hy0-2, 15, hy0+2], fill=A(sh(hatc, 1.3)))
    elif hat == 'boina':
        d.ellipse([hx0-2, hy0-2, hx1+1, hy0+5], fill=A(hatc)); d.line([hx0, hy0+4, hx1-1, hy0+4], fill=A(sh(hatc, 0.7)))
        d.arc([hx0, hy0-1, hx1-3, hy0+3], 200, 260, fill=A(sh(hatc, 1.3))); d.point((15, hy0-2), fill=A(sh(hatc, 0.8)))
    elif hat == 'coroa':
        gold = (238, 190, 40)
        d.rectangle([hx0+1, hy0+1, hx1-1, hy0+4], fill=A(gold))
        for sx_ in (hx0+1, (hx0+hx1)//2-1, hx1-3): d.polygon([(sx_, hy0+1), (sx_+2, hy0+1), (sx_+1, hy0-2)], fill=A(gold))
        d.line([hx0+1, hy0+4, hx1-1, hy0+4], fill=A(sh(gold, 0.7))); d.point(((hx0+hx1)//2, hy0+2), fill=A((220, 40, 60)))
        d.point((hx0+3, hy0+2), fill=A((60, 140, 230))); d.point((hx1-3, hy0+2), fill=A((60, 180, 90)))
    elif hat == 'bandana':
        d.chord([hx0-1, hy0-2, hx1+1, hy0+7], 180, 360, fill=A(hatc)); d.rectangle([hx0-1, hy0+2, hx1+1, hy0+3], fill=A(sh(hatc, 0.8)))
        for (px_, py_) in ((12, hy0), (16, hy0-1), (19, hy0+1), (14, hy0+2)): d.point((px_, py_), fill=A(sh(hatc, 1.45)))
        if side or back: d.polygon([(hx0-1, hy0+2), (hx0-5, hy0+5), (hx0-3, hy0+7), (hx0+1, hy0+4)], fill=A(hatc))
    if aces == 'fone':
        d.arc([hx0-2, hy0-3, hx1+2, hy0+12], 180, 360, fill=A((44, 44, 52)))
        if side: d.rounded_rectangle([13, hy0+5, 17, hy0+11], radius=1, fill=A(acc))
        else: d.rectangle([hx0-3, hy0+5, hx0, hy0+10], fill=A(acc)); d.rectangle([hx1, hy0+5, hx1+3, hy0+10], fill=A(sh(acc, 0.85)))
    # ---------- coisas na mão ----------
    if carry == 'sacola':
        bx = tx1+1 if not side else 18
        d.rectangle([bx, ty0+11, bx+5, ty0+17], fill=A((250, 250, 244))); d.arc([bx+1, ty0+8, bx+4, ty0+13], 180, 360, fill=A((200, 200, 200)))
        d.point((bx+2, ty0+13), fill=A((230, 60, 60))); d.point((bx+3, ty0+14), fill=A((90, 180, 80)))
    elif carry == 'balde':
        bx = tx1+1 if not side else 18
        d.polygon([(bx, ty0+11), (bx+6, ty0+11), (bx+5, ty0+18), (bx+1, ty0+18)], fill=A((150, 156, 166)))
        d.line([(bx, ty0+11), (bx+6, ty0+11)], fill=A((90, 150, 230))); d.arc([bx, ty0+7, bx+6, ty0+14], 180, 360, fill=A((80, 80, 90)))
    elif carry == 'panfleto':
        bx = tx1 if not side else 18
        d.rectangle([bx, ty0+6, bx+6, ty0+14], fill=A((250, 250, 244)), outline=A((60, 90, 180)))
        d.line([(bx+1, ty0+9), (bx+5, ty0+9)], fill=A((60, 90, 180))); d.line([(bx+1, ty0+11), (bx+4, ty0+11)], fill=A((200, 40, 50)))
    elif carry == 'tabua':
        d.polygon([(4, ty0-2), (28, ty0-6), (28, ty0-3), (4, ty0+1)], fill=A((190, 140, 86)))
    if tool in ('up', 'down'):
        mx, my = (tx1+2, ty0-4) if tool == 'up' else (tx1+3, ty0+8)
        d.line([mx, my, mx+2, my+8], fill=A((120, 80, 40))); d.rectangle([mx-2, my-1, mx+3, my+1], fill=A((150, 150, 160)))
    # sombra no chão
    sim = Image.new('RGBA', (W32, H32), (0, 0, 0, 0)); sd = ImageDraw.Draw(sim)
    sd.ellipse([8, 44, 24, 47], fill=(0, 0, 0, 70))
    out = _outline(im)
    sim.alpha_composite(out)
    return sim
