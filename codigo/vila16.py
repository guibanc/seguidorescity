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
def _lamps(rd):
    return [(x, y) for y in range(124, 460, 34) for x in (123, 140) if not (205 < y < 285) and not (ROADA-8 < y < ROADA+16)
            and not (ROADC-8 < y < ROADC+16) and not (rd and ROADD-26 < y < ROADD+16)]
LAMPS = _lamps(True)
def L2(x, y): return int(round(x*S)), int(round(y*S))
REGLOOK = {i: (dict(r['aparencia'], seed=i) if r.get('aparencia') else None) for i, r in REG.items()}

# ---------------- cenário estático (pré-desenhado 1x) ----------------
def _static(lit, rd=True):
    g, river = make_ground16((ROADD,) if rd else ())
    img = Image.fromarray(g).convert('RGBA'); d = ImageDraw.Draw(img)
    # placa da entrada
    sx, sy = L2(*SIGN)
    for x in (sx+2, sx+24): d.rectangle([x, sy, x+2, sy+19], fill=(104, 66, 36, 255))
    d.rectangle([sx-1, sy-1, sx+28, sy+13], fill=OUT + (255,))
    d.rectangle([sx, sy, sx+27, sy+12], fill=(214, 174, 116, 255))
    for y in range(sy+3, sy+12, 3): d.line([sx+1, y, sx+26, y], fill=(194, 152, 96, 255))
    d.line([sx, sy, sx+27, sy], fill=(236, 204, 150, 255))
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
    for (lx, ly) in _lamps(rd):
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
def static(lit, rd=True):
    if (lit, rd) not in _ST: _ST[(lit, rd)] = _static(lit, rd)
    return _ST[(lit, rd)]
_ES = {}
def ESC(p, lit, bell, flag):
    k = (round(p*60)/60, lit, bell, flag % 4)
    if k not in _ES: _ES[k] = escola16(k[0], lit, bell, flag)
    return _ES[k]

def draw_pile(d, n):
    px, py = L2(*PILE); k = 0
    for row, cnt in enumerate([4, 3, 2, 1]):
        for j in range(cnt):
            k += 1
            if k > n: return
            x = px+j*12+row*6; y = py-row*5
            d.rectangle([x, y, x+11, y+4], fill=(148, 98, 56, 255)); d.line([x, y, x+11, y], fill=(176, 126, 80, 255))
            d.line([x, y+4, x+11, y+4], fill=(96, 62, 34, 255))
            d.ellipse([x, y, x+4, y+4], fill=(222, 186, 134, 255)); d.point((x+2, y+2), fill=(170, 126, 80, 255))

def draw_fence(d, lots_, f=1.0, label=None):
    ex, ey = L2(*lot(*lots_[0])); w = 42*len(lots_)
    n = int(f*4)
    for k, (qx, qy) in enumerate([(ex+2, ey+6), (ex+w, ey+6), (ex+2, ey+40), (ex+w, ey+40)]):
        if k >= n: break
        d.line([qx, qy-5, qx, qy], fill=(120, 80, 40, 255)); d.point((qx, qy-5), fill=(176, 130, 80, 255))
    if f >= 1:
        for fx in range(ex+2, ex+w+1, 4): d.point((fx, ey+4), fill=(250, 250, 250, 255)); d.point((fx, ey+38), fill=(250, 250, 250, 255))
        for fy in range(ey+4, ey+39, 4): d.point((ex+2, fy), fill=(250, 250, 250, 255)); d.point((ex+w, fy), fill=(250, 250, 250, 255))

def draw_stakes(d, l):
    x, y = L2(*lot(*l))
    for (qx, qy) in [(x+3, y+8), (x+38, y+8), (x+3, y+42), (x+38, y+42)]:
        d.line([qx, qy-5, qx, qy], fill=(120, 80, 40, 255)); d.point((qx, qy-5), fill=(176, 130, 80, 255))
    for fx in range(x+3, x+39, 3): d.point((fx, y+5), fill=(250, 250, 250, 200)); d.point((fx, y+39), fill=(250, 250, 250, 200))
    for fy in range(y+5, y+40, 3): d.point((x+3, fy), fill=(250, 250, 250, 200)); d.point((x+38, fy), fill=(250, 250, 250, 200))

def static_at(t, lit=False):
    f = roadd_f(t)
    if f <= 0: return static(lit, False)
    if f >= 1: return static(lit, True)
    pre, river = static(lit, False); post, _ = static(lit, True)
    a = np.array(pre); b = np.array(post)
    half = f*125*S; c = 131.5*S
    y0, y1 = (ROADD-6)*S, (ROADD+16)*S
    x0, x1 = int(max(0, c-half)), int(min(a.shape[1], c+half))
    a[y0:y1, x0:x1] = b[y0:y1, x0:x1]
    return Image.fromarray(a), river

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
    if seed not in LOOKS: LOOKS[seed] = REGLOOK.get(seed) or npc_look(seed)
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
    base, river = static_at(t, lit)
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
    sat = SAT[0] <= t < SAT[1]
    # pilha de madeira (vai sendo usada pra abrir a rua D)
    pn = pile_n(t)
    if pn > 0: draw_pile(d, pn)
    # lotes novos da rua D: estacas + cerca da prefeitura (500)
    sf = stakes_f(t)
    if sf > 0:
        free = [l for l in house_lots[NH:] if l[1] == ROADD]
        for k, l in enumerate(free):
            if k < sf*len(free)+0.01: draw_stakes(d, l)
        draw_fence(d, PREFEITURA, clamp(sf*1.5))
    # escola
    ep_ = escola_p(t)
    if ep_ <= 0: draw_fence(d, ESCOLA)
    else:
        ex, ey = L2(*lot(*ESCOLA[0]))
        ei = ESC(ep_, lit and ep_ >= 1, bell_swing(t), int(t*6))
        objs.append((ey+42, lambda ei=ei, ex=ex, ey=ey: img.paste(ei, (ex, ey), ei)))
        if ep_ < 1:
            for k, wx in enumerate((ex-8, ex+20, ex+52, ex+82)):
                fr = int(t*6+k) % 2
                s_ = NPC(8000+k % 6, 'down', 0, 'pedreiro', 'up' if fr else 'down')
                objs.append((ey+44, lambda s_=s_, wx=wx, ey=ey: img.paste(s_, (wx, ey+30), s_)))
            if int(t*8) % 2:
                objs.append((ey+60, lambda ex=ex, ey=ey, t=t: [d.rectangle([ex+6+((t*37+k*29) % 70), ey+26+((t*23+k*5) % 14), ex+7+((t*37+k*29) % 70), ey+27+((t*23+k*5) % 14)], fill=(224, 206, 166)) for k in range(7)]))
        else:
            tdn = 25.0
            if 0 <= t-tdn < 0.9:
                f = (t-tdn)/0.9
                objs.append((9999, lambda ex=ex, ey=ey, f=f: [d.rectangle([ex+42+math.cos(k*0.39)*(10+f*44)-1, ey+20+math.sin(k*0.39)*(8+f*34)-1, ex+42+math.cos(k*0.39)*(10+f*44)+1, ey+20+math.sin(k*0.39)*(8+f*34)+1], fill=[(255, 240, 120), (250, 250, 250), (120, 230, 110)][k % 3]) for k in range(16)]))
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
    def put(s, x, y):
        X, Y = L2(x, y); objs.append((Y+7, lambda s=s, X=X, Y=Y: img.paste(s, (X-6, Y-14), s)))
    if not sat:
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
        vis = []
        for pp in people:
            if nfrac > 0 and prio(pp['id']*7) < nfrac*0.88: continue
            st = person_state(pp, t)
            if st is None: continue
            x, y = st[0], st[1]
            if view and not (view[0]-6 <= x <= view[2]+6 and view[1]-10 <= y <= view[3]+10): continue
            chegando = pp['ts'] is not None and 0 <= t-pp['ts'] < 9
            vis.append((0 if chegando else 1, prio(pp['id']), pp, st))
        vis.sort(key=lambda v: (v[0], v[1]))
        for _, _, pp, st in vis[:MAX_NPC]:
            x, y, mv, _ = st
            st0 = person_state(pp, t-0.08)
            dx, dy = (x-st0[0], y-st0[1]) if st0 else (0, 1)
            moving = abs(dx)+abs(dy) > 0.05
            dr = dir_of(dx, dy) if moving else 'down'
            fr = (int(t*8+pp['ph']*3) % 4) if moving else 0
            put(NPC(pp['id'], dr, fr), x, y)
        # clientes do mercadinho
        door = (lot(*MERCADO)[0]+9.5, ROADB+3)
        for sp in SHOPPERS:
            pts = [(sp['x0'], ROADB+6), (door[0], ROADB+6), door]
            L = plen(pts); per = 7.0; ph_ = ((t-sp['t0']) % per)/per
            if ph_ < 0.4: (x, y), _ = path_pos(pts, L*ph_/0.4); bag = False; dr = 'right' if sp['x0'] < door[0] else 'left'
            elif ph_ < 0.55: continue
            else:
                (x, y), _ = path_pos(pts, L*(1-(ph_-0.55)/0.45)); bag = True; dr = 'left' if sp['x0'] < door[0] else 'right'
                if y < ROADB+5.5: dr = 'down'
            if y < ROADB+5.5 and ph_ < 0.4: dr = 'up'
            put(NPC(sp['seed'], dr, int(t*8+sp['ph']) % 4, carry='sacola' if bag else None), x, y)
    else:
        # sábado: a vila inteira desce pro mercadinho
        for c in CROWD:
            st = crowd_state(c, t)
            if st is None: continue
            x, y, bag = st
            st0 = crowd_state(c, t-0.06)
            dx, dy = (x-st0[0], y-st0[1]) if st0 else (0, 1)
            moving = abs(dx)+abs(dy) > 0.03
            dr = dir_of(dx, dy) if moving else ('right' if not bag else 'down')
            fr = int(t*8+c['ph']*3) % 4 if moving else 0
            put(NPC(c['id'], dr, fr, carry='sacola' if bag else None), x, y)
        # o dono da vendinha chamando cliente
        if t > 55.4:
            wave = int(t*5) % 2
            put(NPC(8200, 'down', 1 if wave else 3, 'mercado'), *VENDEDOR)
    # carregadores de tábua pra obra ativa
    if active and not sat:
        i, l = active; hx, hy = lot(*l); roady = l[1]+5
        pts = [(PILE[0]+12, PILE[1]+4), (131.5, PILE[1]+4), (131.5, roady), (hx+10, roady)]
        L = plen(pts)
        for k in range(2):
            per = (t+k*1.5) % 3.0; go = per < 1.5; f = per/1.5 if go else (3.0-per)/1.5
            (x, y), _ = path_pos(pts, L*f)
            (x2, y2), _ = path_pos(pts, L*clamp(f+(0.01 if go else -0.01)))
            put(NPC(8004+k, dir_of(x2-x, y2-y), int(t*8) % 4, 'pedreiro', carry='tabua' if go else None), x, y)
    # pedreiros levando a pilha de madeira pra rua nova
    if 41.3 <= t < 45.4:
        for k in range(6):
            tx_ = [40, 70, 100, 165, 190, 215][k]
            pts = [(PILE[0]+10, PILE[1]+6), (tx_, ROADD+5)]
            L = plen(pts); per = (t-41.3+k*0.27) % 1.6; go = per < 0.8
            f = per/0.8 if go else (1.6-per)/0.8
            (x, y), _ = path_pos(pts, L*f)
            put(NPC(8000+k, ('right' if tx_ > PILE[0] else 'left') if go else ('left' if tx_ > PILE[0] else 'right'), int(t*8+k) % 4, 'pedreiro', carry='tabua' if go else None), x, y)
    # poeira na frente da rua sendo aberta
    rf = roadd_f(t)
    if 0 < rf < 1:
        for side in (-1, 1):
            fx = 131.5+side*rf*125
            for k in range(8):
                q = (t*13+k*0.37) % 1
                X, Y = L2(fx+side*q*6, ROADD+1+((k*7) % 10))
                c_ = int(230-q*50)
                objs.append((9997, lambda X=X, Y=Y, c_=c_, q=q: d.ellipse([X-2-q*3, Y-2-q*3, X+2+q*3, Y+2+q*3], fill=(c_, c_-24, c_-60))))
    objs.sort(key=lambda o: o[0])
    for _, fn in objs: fn()
    out = np.array(img.convert('RGB'))
    return out
