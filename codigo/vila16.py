# vila em 16 bits (ep. 3 em diante). Saída: array 960x540 (2x o mapa lógico)
import numpy as np, math, random, json, os
from PIL import Image, ImageDraw
from world import W, H, ROADA, ROADB, ROADC, clamp, smooth
from world16 import *
from world16 import _sil_outline
from scene import *

_est = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'estado_vila.json')))
NOME_VILA = _est.get('nome_vila')
CHURCH = (115, 61); PILE = (86, 412); SIGN = (142, 442)
LAMPS = [(x, y) for y in range(124, 460, 34) for x in (123, 140) if not (205 < y < 285) and not (ROADA-8 < y < ROADA+16) and not (ROADC-8 < y < ROADC+16)]
def L2(x, y): return int(round(x*S)), int(round(y*S))

# ---------------- cenário estático (pré-desenhado 1x) ----------------
def _static(lit):
    g, river = make_ground16()
    img = Image.fromarray(g).convert('RGBA'); d = ImageDraw.Draw(img)
    # pilha de madeira
    px, py = L2(*PILE)
    for row, cnt in enumerate([4, 3, 2, 1]):
        for j in range(cnt):
            x = px+j*12+row*6; y = py-row*5
            d.rectangle([x, y, x+11, y+4], fill=(148, 98, 56, 255)); d.line([x, y, x+11, y], fill=(176, 126, 80, 255))
            d.line([x, y+4, x+11, y+4], fill=(96, 62, 34, 255))
            d.ellipse([x, y, x+4, y+4], fill=(222, 186, 134, 255)); d.point((x+2, y+2), fill=(170, 126, 80, 255))
    # placa da entrada
    sx, sy = L2(*SIGN)
    for x in (sx+2, sx+24): d.rectangle([x, sy, x+2, sy+19], fill=(104, 66, 36, 255))
    d.rectangle([sx-1, sy-1, sx+28, sy+13], fill=OUT + (255,))
    d.rectangle([sx, sy, sx+27, sy+12], fill=(214, 174, 116, 255))
    for y in range(sy+3, sy+12, 3): d.line([sx+1, y, sx+26, y], fill=(194, 152, 96, 255))
    d.line([sx, sy, sx+27, sy], fill=(236, 204, 150, 255))
    # escola: lote cercado (marco 400)
    ex, ey = L2(*lot(*ESCOLA[0]))
    for (qx, qy) in [(ex+2, ey+6), (ex+84, ey+6), (ex+2, ey+40), (ex+84, ey+40)]:
        d.line([qx, qy-5, qx, qy], fill=(120, 80, 40, 255)); d.point((qx, qy-5), fill=(176, 130, 80, 255))
    for fx in range(ex+2, ex+85, 4): d.point((fx, ey+4), fill=(250, 250, 250, 255)); d.point((fx, ey+38), fill=(250, 250, 250, 255))
    for fy in range(ey+4, ey+39, 4): d.point((ex+2, fy), fill=(250, 250, 250, 255)); d.point((ex+84, fy), fill=(250, 250, 250, 255))
    # árvores da borda
    for tr_ in trees:
        im, (ax, ay) = TREE16(tr_['r'], tr_['k'], tr_['x'] % 3)
        img.paste(im, (tr_['x']*S-ax, tr_['y']*S-ay), im)
    # praça: canteiros, bancos, poço
    for fx, fy in ((102, 215), (158, 215), (102, 271), (158, 271)):
        X, Y = L2(fx, fy)
        d.rectangle([X-2, Y-2, X+5, Y+5], fill=(110, 76, 46, 255)); d.rectangle([X-1, Y-1, X+4, Y+4], fill=(76, 52, 32, 255))
        for k, c in enumerate([(240, 80, 100), (250, 220, 70), (240, 140, 200), (250, 250, 250)]):
            d.point((X+(k % 2)*2, Y+(k//2)*2), fill=c+(255,)); d.point((X+(k % 2)*2+1, Y+(k//2)*2+1), fill=(70, 150, 70, 255))
    for bx, by in ((108, 266), (148, 266), (108, 222)):
        X, Y = L2(bx, by)
        d.rectangle([X-1, Y-1, X+14, Y+5], fill=OUT + (255,))
        d.rectangle([X, Y, X+13, Y+1], fill=(176, 120, 70, 255)); d.rectangle([X, Y+2, X+13, Y+3], fill=(150, 98, 56, 255))
        d.line([X, Y, X+13, Y], fill=(206, 152, 96, 255))
        for lx in (X+1, X+12): d.line([lx, Y+4, lx, Y+5], fill=(60, 56, 60, 255))
    cx, cy = L2(117, 226)
    d.ellipse([cx-11, cy-8, cx+11, cy+9], fill=OUT + (255,)); d.ellipse([cx-10, cy-7, cx+10, cy+8], fill=(150, 146, 140, 255))
    for k in range(0, 360, 30):
        a = math.radians(k); d.point((cx+math.cos(a)*9, cy+math.sin(a)*6.5), fill=(118, 114, 108, 255))
    d.ellipse([cx-6, cy-4, cx+6, cy+4], fill=(30, 56, 120, 255)); d.ellipse([cx-4, cy-3, cx+1, cy], fill=(60, 100, 170, 255))
    d.rectangle([cx-11, cy-14, cx+11, cy-11], fill=(120, 72, 36, 255)); d.line([cx-11, cy-14, cx+11, cy-14], fill=(160, 104, 60, 255))
    for x in (cx-10, cx+9): d.rectangle([x, cy-11, x+1, cy+1], fill=(100, 60, 30, 255))
    d.line([cx, cy-11, cx, cy-6], fill=(90, 90, 96, 255)); d.rectangle([cx-2, cy-6, cx+2, cy-3], fill=(140, 100, 60, 255))
    # postes
    for (lx, ly) in LAMPS:
        X, Y = L2(lx, ly)
        d.rectangle([X-1, Y-9, X+1, Y+1], fill=OUT + (255,)); d.line([X, Y-8, X, Y], fill=(80, 84, 96, 255))
        d.rectangle([X-2, Y-12, X+2, Y-9], fill=OUT + (255,))
        d.rectangle([X-1, Y-11, X+1, Y-10], fill=(255, 226, 130, 255) if lit else (210, 214, 200, 255))
        d.point((X+1, Y+2), fill=(0, 0, 0, 60)); d.point((X+2, Y+2), fill=(0, 0, 0, 40))
    # igreja
    ci = church16(lit)
    img.paste(ci, L2(*CHURCH), ci)
    return img, river

TREE_C = {}
def TREE16(r, k, v):
    if (r, k, v) not in TREE_C: TREE_C[(r, k, v)] = tree16(r, k, r*100+k*10+v)
    return TREE_C[(r, k, v)]
_ST = {}
def static(lit):
    if lit not in _ST: _ST[lit] = _static(lit)
    return _ST[lit]

# ---------------- caches de sprites ----------------
_HC = {}
def HOUSE(var, p, lit=False, venda=False):
    k = (var, round(p*40)/40, lit, venda)
    if k not in _HC: _HC[k] = house16(var, k[1], lit, venda)
    return _HC[k]
_MC = {}
def MERC(lit):
    if lit not in _MC: _MC[lit] = mercado16(1, lit)
    return _MC[lit]
_NC = {}
LOOKS = {}
def look_of(seed):
    if seed not in LOOKS: LOOKS[seed] = npc_look(seed)
    return LOOKS[seed]
def NPC(seed, dirc, frame, unif=None, tool=None, carry=None):
    k = (seed, dirc, frame, unif, tool, carry)
    if k not in _NC: _NC[k] = npc_sprite(look_of(seed), dirc, frame, unif, tool, carry)
    return _NC[k]
def dir_of(dx, dy):
    if abs(dx) < 1e-3 and abs(dy) < 1e-3: return 'down'
    if abs(dx) > abs(dy): return 'right' if dx > 0 else 'left'
    return 'down' if dy > 0 else 'up'

HEN = None
def hen(frame):
    im = Image.new('RGBA', (7, 7), (0, 0, 0, 0)); p = im.load()
    for (x, y) in [(2, 2), (3, 2), (1, 3), (2, 3), (3, 3), (4, 3), (1, 4), (2, 4), (3, 4), (4, 4), (2, 5), (3, 5)]: p[x, y] = (250, 250, 246, 255)
    p[4, 1] = (250, 250, 246, 255); p[5, 1] = (250, 250, 246, 255); p[4, 0] = (220, 40, 40, 255); p[6, 1] = (240, 160, 40, 255)
    p[5, 2] = (250, 250, 246, 255); p[1, 4] = (220, 220, 214, 255); p[3, 4] = (220, 220, 214, 255)
    p[2, 6] = (240, 160, 40, 255) if frame else (0, 0, 0, 0); p[3, 6] = (240, 160, 40, 255)
    return _sil_outline(im).copy()
HENS = [hen(0), hen(1)]

def is_night(hour): return hour is not None and (hour >= 18.6 or hour < 6)
def night_amt(hour):
    if hour is None: return 0.0
    if hour < 6: return 1.0
    return clamp((hour-17.6)/2.4)

# ---------------- composição ----------------
MAX_NPC = 50   # máximo de moradores desenhados por vez (o resto 'está em casa')
def prio(pid): return ((pid*2654435761) % 4294967296)/4294967296

def compose16(t, hour=None, view=None):
    lit = is_night(hour)
    base, river = static(lit)
    img = base.copy(); d = ImageDraw.Draw(img)
    # brilho do rio
    if not hasattr(compose16, 'rv'):
        ry, rx = np.nonzero(river); compose16.rv = (ry, rx)
    ry, rx = compose16.rv
    a = np.array(img)
    m = ((ry*3 - int(t*60) + (rx*7) % 13) % 29) == 0; a[ry[m], rx[m], :3] = [170, 214, 250]
    m2 = ((ry*5 - int(t*40) + (rx*11) % 17) % 37) == 0; a[ry[m2], rx[m2], :3] = [92, 150, 222]
    img = Image.fromarray(a); d = ImageDraw.Draw(img)
    C = count_at(t); objs = []
    # casas
    active = None
    for i, l in enumerate(house_lots[:NH]):
        p = house_p(i, C)
        if p <= 0: continue
        if p < 1 and active is None: active = (i, l)
        x, y = L2(*lot(*l))
        hi = HOUSE(house_var[i], p, lit and p >= 1)
        objs.append((y+42, lambda hi=hi, x=x, y=y: img.paste(hi, (x, y), hi)))
        if p < 1:
            for k, wx in enumerate((x-8, x+36)):
                fr = int(t*6+k) % 2
                s = NPC(8000+(i+k) % 6, 'down', 0, 'pedreiro', 'up' if fr else 'down')
                objs.append((y+44, lambda s=s, wx=wx, y=y: img.paste(s, (wx, y+28), s)))
            if int(t*8) % 2:
                objs.append((y+60, lambda x=x, y=y, t=t: [d.rectangle([x+6+((t*37+k*29) % 28), y+26+((t*23+k*5) % 14)]*1+[x+7+((t*37+k*29) % 28), y+27+((t*23+k*5) % 14)], fill=(224, 206, 166)) for k in range(4)]))
        else:
            tdn = house_done_time(i)
            if tdn and 0 <= t-tdn < 0.7:
                f = (t-tdn)/0.7
                objs.append((9999, lambda x=x, y=y, f=f: [d.rectangle([x+20+math.cos(k*0.524)*(8+f*26)-1, y+20+math.sin(k*0.524)*(8+f*26)-1, x+20+math.cos(k*0.524)*(8+f*26)+1, y+20+math.sin(k*0.524)*(8+f*26)+1], fill=[(255, 240, 120), (250, 250, 250), (120, 230, 110)][k % 3]) for k in range(12)]))
            # fumaça da chaminé
            for k in range(3):
                ph = ((t+k*0.9+i*0.37) % 2.7)/2.7
                sx = x+30+ph*7; sy = y-2-ph*22; c = int(238-ph*60); r_ = 1+ph*2.2
                if ph < 0.9: objs.append((9998, lambda sx=sx, sy=sy, c=c, r_=r_: d.ellipse([sx-r_, sy-r_, sx+r_, sy+r_], fill=(c, c, c+4))))
            if i % 3 == 1 and (tdn is None or t > tdn+1.5):
                def fence(x=x, y=y):
                    for fx in range(x+1, x+41, 3):
                        if x+12 <= fx <= x+27: continue
                        d.line([fx, y+44, fx, y+47], fill=(250, 246, 236)); d.point((fx, y+48), fill=(0, 0, 0, 60))
                    d.line([x+1, y+45, x+11, y+45], fill=(214, 206, 190)); d.line([x+28, y+45, x+40, y+45], fill=(214, 206, 190))
                objs.append((y+49, fence))
    # vendinha e mercadinho
    x, y = L2(*lot(*VENDA)); vi = HOUSE(5, 1, lit, True)
    objs.append((y+42, lambda vi=vi, x=x, y=y: img.paste(vi, (x, y), vi)))
    MX, MY = L2(*lot(*MERCADO)); mi = MERC(lit)
    objs.append((MY+42, lambda: img.paste(mi, (MX, MY), mi)))
    # árvore da praça (com profundidade)
    ti, (ax, ay) = TREE16(6, 0, 0)
    objs.append((231*S, lambda: img.paste(ti, (153*S-ax, 231*S-ay), ti)))
    # galinhas
    for k in range(6):
        bx = 40+k*31; by = ROADA+18 if k % 2 else ROADA-6
        cx = bx+math.sin(t*0.9+k)*6; cy = by+math.sin(t*1.3+k*2)*2; hop = int(t*4+k) % 5 == 0
        hm = HENS[int(t*5+k) % 2]
        if math.cos(t*0.9+k) < 0: hm = hm.transpose(Image.FLIP_LEFT_RIGHT)
        X, Y = L2(cx, cy-(0.5 if hop else 0))
        objs.append((Y+6, lambda hm=hm, X=X, Y=Y: img.paste(hm, (X-3, Y-3), hm)))
    # carrinho de mão na rua principal
    ph = ((t+5)/14.0) % 2; up = ph < 1; f = smooth(ph if up else 2-ph); cy = 468-f*350; cx = 133
    def cart(cx=cx, cy=cy, up=up):
        X, Y = L2(cx, cy)
        d.rectangle([X-5, Y-1, X+5, Y+12], fill=OUT); d.rectangle([X-4, Y, X+4, Y+11], fill=(150, 100, 56))
        d.rectangle([X-3, Y+1, X+3, Y+6], fill=(226, 196, 86)); d.point((X-1, Y+2), fill=(250, 226, 130))
        for (wx, wy) in ((X-6, Y+2), (X+5, Y+2), (X-6, Y+9), (X+5, Y+9)): d.rectangle([wx, wy, wx+1, wy+2], fill=(40, 32, 28))
        s = NPC(8100, 'up' if up else 'down', int(t*6) % 4)
        img.paste(s, (X-6, Y+12 if up else Y-17), s)
    objs.append((L2(cx, cy)[1]+14, cart))
    # moradores
    nfrac = night_amt(hour)
    dest_on = T['npc'][0] <= t < T['npc'][1]
    vis = []
    for pp in people:
        if dest_on and pp['id'] == DESTAQUE_ID: continue
        if nfrac > 0 and prio(pp['id']*7) < nfrac*0.88: continue
        st = person_state(pp, t)
        if st is None: continue
        x, y = st[0], st[1]
        if view and not (view[0]-6 <= x <= view[2]+6 and view[1]-10 <= y <= view[3]+10): continue
        chegando = pp['ts'] is not None and 0 <= t-pp['ts'] < 9
        vis.append((0 if chegando else 1, prio(pp['id']), pp, st))
    vis.sort(key=lambda v: (v[0], v[1]))
    for _, _, pp, st in vis[:(22 if dest_on else MAX_NPC)]:
        x, y, mv, _ = st
        st0 = person_state(pp, t-0.08)
        dx, dy = (x-st0[0], y-st0[1]) if st0 else (0, 1)
        moving = abs(dx)+abs(dy) > 0.05
        dr = dir_of(dx, dy) if moving else 'down'
        fr = (int(t*8+pp['ph']*3) % 4) if moving else 0
        s = NPC(pp['id'], dr, fr)
        X, Y = L2(x, y)
        objs.append((Y+7, lambda s=s, X=X, Y=Y: img.paste(s, (X-6, Y-14), s)))
    # clientes do mercadinho
    door = (lot(*MERCADO)[0]+9.5, ROADB+3)
    if nfrac < 0.9:
        for sp in SHOPPERS:
            pts = [(sp['x0'], ROADB+6), (door[0], ROADB+6), door]
            L = plen(pts); per = 7.0; ph_ = ((t-sp['t0']) % per)/per
            if ph_ < 0.4: (x, y), _ = path_pos(pts, L*ph_/0.4); bag = False; dr = 'right' if sp['x0'] < door[0] else 'left'
            elif ph_ < 0.55: continue
            else:
                (x, y), _ = path_pos(pts, L*(1-(ph_-0.55)/0.45)); bag = True; dr = 'left' if sp['x0'] < door[0] else 'right'
                if y < ROADB+5.5: dr = 'down'
            if y < ROADB+5.5 and ph_ < 0.4: dr = 'up'
            s = NPC(sp['seed'], dr, int(t*8+sp['ph']) % 4, carry='sacola' if bag else None)
            X, Y = L2(x, y)
            objs.append((Y+7, lambda s=s, X=X, Y=Y: img.paste(s, (X-6, Y-14), s)))
    # carregadores de tábua pra obra ativa
    if active:
        i, l = active; hx, hy = lot(*l); roady = l[1]+5
        pts = [(PILE[0]+12, PILE[1]+4), (131.5, PILE[1]+4), (131.5, roady), (hx+10, roady)]
        L = plen(pts)
        for k in range(2):
            per = (t+k*1.5) % 3.0; go = per < 1.5; f = per/1.5 if go else (3.0-per)/1.5
            (x, y), _ = path_pos(pts, L*f)
            (x2, y2), _ = path_pos(pts, L*clamp(f+(0.01 if go else -0.01)))
            s = NPC(8004+k, dir_of(x2-x, y2-y), int(t*8) % 4, 'pedreiro', carry='tabua' if go else None)
            X, Y = L2(x, y)
            objs.append((Y+7, lambda s=s, X=X, Y=Y: img.paste(s, (X-6, Y-14), s)))
    # morador em destaque
    st = destaque_state(t)
    if st:
        x, y, acao, sac = st
        if acao not in ('entra', 'casa'):
            st0 = destaque_state(max(T['npc'][0], t-0.06))
            dx, dy = (x-st0[0], y-st0[1]) if st0 else (0, 1)
            moving = acao in ('anda', 'sai') and abs(dx)+abs(dy) > 0.02
            dr = dir_of(dx, dy) if moving else 'down'
            fr = int(t*8) % 4 if moving else 0
            s = NPC(DESTAQUE_ID, dr, fr, carry='sacola' if sac else None)
            X, Y = L2(x, y)
            pul = 1+int(t*6) % 2
            def drw(s=s, X=X, Y=Y, pul=pul):
                d.ellipse([X-8-pul, Y+1-pul//2, X+7+pul, Y+6+pul//2], outline=(255, 214, 70))
                img.paste(s, (X-6, Y-14), s)
            objs.append((Y+7, drw))
    objs.sort(key=lambda o: o[0])
    for _, fn in objs: fn()
    out = np.array(img.convert('RGB')).astype(np.float32)
    # noite: tinta azulada + janelas e postes acesos
    if nfrac > 0:
        lm = np.zeros(out.shape[:2], bool)
        for c in LITW + [(255, 226, 130)]:
            lm |= (out[:, :, 0] == c[0]) & (out[:, :, 1] == c[1]) & (out[:, :, 2] == c[2])
        tint = np.array([1-0.62*nfrac, 1-0.55*nfrac, 1-0.28*nfrac], np.float32)
        orig = out.copy()
        out *= tint
        out[lm] = orig[lm]
        if lit:
            yy, xx = np.mgrid[-14:15, -14:15]; glow = np.clip(1-np.hypot(xx, yy)/14, 0, 1)**2
            for (lx, ly) in LAMPS:
                X, Y = L2(lx, ly-5)
                y0, y1, x0, x1 = Y-14, Y+15, X-14, X+15
                if y0 < 0 or x0 < 0 or y1 > out.shape[0] or x1 > out.shape[1]: continue
                out[y0:y1, x0:x1] += glow[:, :, None]*np.array([90, 70, 20])*nfrac
    return np.clip(out, 0, 255).astype(np.uint8)
