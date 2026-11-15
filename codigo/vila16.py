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
def _static(lit, rd=True, pv=False):
    g, river = make_ground16((ROADD,) if rd else (), pv)
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
def static(lit, rd=True, pv=False):
    if (lit, rd, pv) not in _ST: _ST[(lit, rd, pv)] = _static(lit, rd, pv)
    return _ST[(lit, rd, pv)]
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

_PM = {}
def static_at(t, lit=False):
    f = pave_f(t)
    if f <= 0: return static(lit, True, False)
    if f >= 1: return static(lit, True, True)
    pre, river = static(lit, True, False); post, _ = static(lit, True, True)
    if lit not in _PM:
        A_ = np.array(pre); B_ = np.array(post)
        diff = np.any(A_ != B_, axis=2)
        yy, xx = np.mgrid[0:A_.shape[0], 0:A_.shape[1]]
        dist = np.hypot(xx/S-PAVE_C[0], yy/S-PAVE_C[1])
        _PM[lit] = (A_, B_, diff, dist)
    A_, B_, diff, dist = _PM[lit]
    a = A_.copy(); m = diff & (dist < f*PAVE_R)
    a[m] = B_[m]
    return Image.fromarray(a), river
PAVE_C = (161, 410); PAVE_R = 330.0

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


from world16 import prefeitura16
_PF = {}
def PREF(p, lit, flag):
    k = (round(p*60)/60, lit, flag % 4)
    if k not in _PF: _PF[k] = prefeitura16(k[0], lit, flag)
    return _PF[k]

def night_tint(a, k):
    """a: array RGB do mapa; k: 0..1. Janelas/postes acesos ficam com a cor."""
    if k <= 0: return a
    f = a.astype(np.float32)
    lm = np.zeros(a.shape[:2], bool)
    if k > 0.5:
        for c in LITW+[(255, 226, 130)]: lm |= (a[:, :, 0] == c[0]) & (a[:, :, 1] == c[1]) & (a[:, :, 2] == c[2])
    mul = 1-(1-np.array([0.38, 0.45, 0.72]))*k
    o = f*mul
    o[lm] = f[lm]
    return np.clip(o, 0, 255).astype(np.uint8)

LUZES = [(255, 70, 90), (80, 200, 255), (255, 214, 70), (170, 90, 255), (90, 240, 140)]
def show_overlay(a, t):
    """luzes do show por cima do mapa já escurecido (array 2x)"""
    if not (SHOW0 <= t < SHOWWIN[1]): return a
    f = a.astype(np.float32)
    H_, W_ = a.shape[:2]
    on = clamp((t-51.4)/0.4)
    pulse = 0.75+0.25*math.sin(t*9)
    # luz quente do palco
    yy, xx = np.ogrid[0:H_, 0:W_]
    cx, cy = 132*S, 220*S
    g = np.exp(-(((xx-cx)/(46*S))**2+((yy-cy)/(16*S))**2))
    f += g[:, :, None]*np.array([90, 70, 40])*clamp((t-SHOW0)/0.3)
    if on > 0:
        for k in range(4):
            ang = math.sin(t*(1.1+k*0.23)+k*1.7)*0.6+(-0.25+k*0.17)
            col = np.array(LUZES[(k+int(t*1.5)) % len(LUZES)])
            ox, oy = (116+k*11)*S, 214*S
            L = 52*S
            ex, ey = ox+math.sin(ang)*L, oy+math.cos(ang)*L
            # cone: distância ao segmento com largura crescendo
            vx, vy = ex-ox, ey-oy; ll = vx*vx+vy*vy
            u = np.clip(((xx-ox)*vx+(yy-oy)*vy)/ll, 0, 1)
            dx = xx-(ox+u*vx); dy = yy-(oy+u*vy)
            w = 2+u*16*S
            m = np.clip(1-np.sqrt(dx*dx+dy*dy)/w, 0, 1)*(u > 0.02)*(1-u*0.6)
            f += m[:, :, None]*col*0.9*on*pulse
    return np.clip(f, 0, 255).astype(np.uint8)

def draw_stage(d, t, objs, put):
    if t < SHOW0 or t >= SHOWWIN[1]: return
    p = clamp((t-SHOW0)/0.35)
    x0, y0, x1, y1 = [v*S for v in STAGE]
    drop = int((1-p)*-30)
    def stage(drop=drop):
        # treliça de luz
        d.rectangle([x0, y0-14+drop, x1, y0-11+drop], fill=(60, 60, 70)); d.line([x0, y0-14+drop, x1, y0-14+drop], fill=(120, 120, 130))
        for x in range(x0, x1, 6): d.line([x, y0-14+drop, x+3, y0-11+drop], fill=(100, 100, 110))
        for k in range(4):
            lx = (116+k*11)*S
            c = LUZES[(k+int(t*1.5)) % len(LUZES)] if t > 51.4 else (90, 90, 90)
            d.rectangle([lx-2, y0-11+drop, lx+2, y0-7+drop], fill=(30, 30, 36)); d.rectangle([lx-1, y0-8+drop, lx+1, y0-7+drop], fill=c)
        for x in (x0, x1-3): d.rectangle([x, y0-14+drop, x+3, y1], fill=(70, 70, 80))
        # fundo e piso
        d.rectangle([x0+3, y0-10+drop, x1-3, y0+6+drop], fill=(28, 22, 44))
        for k in range(0, x1-x0-6, 5): d.line([x0+3+k, y0-10+drop, x0+3+k, y0+6+drop], fill=(38, 30, 58))
        d.rectangle([x0, y0+6, x1, y1], fill=(110, 72, 44)); d.line([x0, y0+6, x1, y0+6], fill=(150, 104, 66))
        for y in range(y0+9, y1, 3): d.line([x0, y, x1, y], fill=(96, 62, 38))
        d.rectangle([x0, y1, x1, y1+3], fill=(70, 44, 26)); d.line([x0, y1+4, x1, y1+4], fill=(0, 0, 0))
        # caixas de som
        for sx_ in (x0-10, x1+2):
            d.rectangle([sx_, y0+4, sx_+8, y1+2], fill=(24, 22, 28)); d.rectangle([sx_, y0+4, sx_+8, y1+2], outline=(70, 70, 80))
            bb = 1 if (t > 50.5 and int(t*8) % 2) else 0
            d.ellipse([sx_+1-bb, y0+7-bb, sx_+7+bb, y0+13+bb], fill=(60, 60, 70)); d.ellipse([sx_+2, y1-6, sx_+6, y1-2], fill=(60, 60, 70))
        # bateria
        bx, by = 143*S, 219*S
        d.ellipse([bx-6, by+2, bx+6, by+10], fill=(200, 40, 50)); d.ellipse([bx-4, by+3, bx+4, by+9], fill=(230, 230, 236))
        for cxx in (bx-10, bx+8): d.ellipse([cxx, by-2, cxx+5, by+1], fill=(226, 196, 86))
    objs.append((y0, stage))
    if p >= 1:
        for (bx, by, kind) in BANDA:
            play = t > 50.5
            fr = int(t*8) % 4 if play and kind != 'voz' else (1 if play and int(t*3) % 2 else 0)
            s = NPC(8300+len(kind), 'down', fr if kind != 'bateria' else 0, 'mercado' if kind == 'voz' else None)
            X, Y = L2(bx, by)
            def band(s=s, X=X, Y=Y, kind=kind, play=play):
                hop = 2 if (play and kind == 'voz' and int(t*4) % 2) else 0
                img_paste(s, X-6, Y-14-hop)
                if kind == 'guitarra':
                    d.line([X-5, Y-4, X+5, Y-8], fill=(80, 50, 30)); d.ellipse([X-6, Y-6, X-1, Y-1], fill=(200, 60, 40))
                if kind == 'voz':
                    d.line([X+5, Y-2, X+5, Y+4], fill=(150, 150, 160)); d.point((X+5, Y-3), fill=(40, 40, 40))
            objs.append((Y+8, band))
    # notinhas
    if t > 50.5:
        for k in range(6):
            q = ((t*0.8+k*0.37) % 1.0)
            nx = (116+k*7+math.sin(t*2+k)*4)*S; ny = (214-q*26)*S
            c = LUZES[k % len(LUZES)]
            def note(nx=nx, ny=ny, c=c):
                d.ellipse([nx, ny+4, nx+4, ny+7], fill=c); d.line([nx+3, ny-3, nx+3, ny+5], fill=c); d.line([nx+3, ny-3, nx+6, ny-1], fill=c)
            objs.append((9996, note))

img_paste = None
def compose16(t, night=0.0, view=None):
    global img_paste
    lit = night > 0.5
    base, river = static_at(t, lit)
    img = base.copy()
    if not hasattr(compose16, 'rv'):
        ry, rx = np.nonzero(river); compose16.rv = (ry, rx)
    ry, rx = compose16.rv
    a = np.array(img)
    m = ((ry*3 - int(t*60) + (rx*7) % 13) % 29) == 0; a[ry[m], rx[m], :3] = [170, 214, 250]
    m2 = ((ry*5 - int(t*40) + (rx*11) % 17) % 37) == 0; a[ry[m2], rx[m2], :3] = [92, 150, 222]
    img = Image.fromarray(a); d = ImageDraw.Draw(img)
    img_paste = lambda s, x, y: img.paste(s, (x, y), s)
    C = count_at(t); objs = []
    show = SHOWWIN[0] <= t < SHOWWIN[1]
    def put(s, x, y):
        X, Y = L2(x, y); objs.append((Y+7, lambda s=s, X=X, Y=Y: img.paste(s, (X-6, Y-14), s)))
    # estacas nos lotes ainda vazios da rua D
    for i, l in enumerate(house_lots):
        if l[1] == ROADD and house_p(i, C) <= 0: draw_stakes(d, l)
    # escola (pronta)
    ex, ey = L2(*lot(*ESCOLA[0])); ei = ESC(1, lit, 0, int(t*6))
    objs.append((ey+42, lambda ei=ei, ex=ex, ey=ey: img.paste(ei, (ex, ey), ei)))
    # prefeitura
    pp_ = pref_p(t); px, py = L2(*lot(*PREFEITURA[0]))
    if pp_ <= 0: draw_fence(d, PREFEITURA)
    else:
        pim = PREF(pp_, lit and pp_ >= 1, int(t*6))
        objs.append((py+42, lambda pim=pim: img.paste(pim, (px, py), pim)))
        if pp_ < 1:
            for k, wx in enumerate((px-8, px+20, px+52, px+82)):
                s_ = NPC(8000+k % 6, 'down', 0, 'pedreiro', 'up' if int(t*6+k) % 2 else 'down')
                objs.append((py+44, lambda s_=s_, wx=wx: img.paste(s_, (wx, py+30), s_)))
            if int(t*8) % 2:
                objs.append((py+60, lambda: [d.rectangle([px+6+((t*37+k*29) % 70), py+26+((t*23+k*5) % 14), px+7+((t*37+k*29) % 70), py+27+((t*23+k*5) % 14)], fill=(224, 206, 166)) for k in range(7)]))
        elif 0 <= t-25.0 < 0.9:
            f = (t-25.0)/0.9
            objs.append((9999, lambda f=f: [d.rectangle([px+42+math.cos(k*0.39)*(10+f*44)-1, py+20+math.sin(k*0.39)*(8+f*34)-1, px+42+math.cos(k*0.39)*(10+f*44)+1, py+20+math.sin(k*0.39)*(8+f*34)+1], fill=[(255, 240, 120), (250, 250, 250), (120, 230, 110)][k % 3]) for k in range(16)]))
    # casas
    active = None
    for i, l in enumerate(house_lots):
        p = house_p(i, C)
        if p <= 0: continue
        if p < 1 and active is None: active = (i, l)
        x, y = L2(*lot(*l))
        hi = HOUSE(house_var[i], p, lit and p >= 1)
        objs.append((y+42, lambda hi=hi, x=x, y=y: img.paste(hi, (x, y), hi)))
        if p < 1:
            for k, wx in enumerate((x-8, x+36)):
                s = NPC(8000+(i+k) % 6, 'down', 0, 'pedreiro', 'up' if int(t*6+k) % 2 else 'down')
                objs.append((y+44, lambda s=s, wx=wx, y=y: img.paste(s, (wx, y+28), s)))
            if int(t*8) % 2:
                objs.append((y+60, lambda x=x, y=y: [d.rectangle([x+6+((t*37+k*29) % 28), y+26+((t*23+k*5) % 14), x+7+((t*37+k*29) % 28), y+27+((t*23+k*5) % 14)], fill=(224, 206, 166)) for k in range(4)]))
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
    x, y = L2(*lot(*VENDA)); vi = HOUSE(5, 1, lit, True)
    objs.append((y+42, lambda vi=vi, x=x, y=y: img.paste(vi, (x, y), vi)))
    MX, MY = L2(*lot(*MERCADO)); mi = MERC(lit)
    objs.append((MY+42, lambda: img.paste(mi, (MX, MY), mi)))
    ti, (ax, ay) = TREE16(6, 0, 0)
    objs.append((231*S, lambda: img.paste(ti, (153*S-ax, 231*S-ay), ti)))
    for k in range(6):
        bx = 40+k*31; by = ROADA+18 if k % 2 else ROADA-6
        cx = bx+math.sin(t*0.9+k)*6; cy = by+math.sin(t*1.3+k*2)*2; hop = int(t*4+k) % 5 == 0
        hm = HENS[int(t*5+k) % 2]
        if math.cos(t*0.9+k) < 0: hm = hm.transpose(Image.FLIP_LEFT_RIGHT)
        X, Y = L2(cx, cy-(0.5 if hop else 0))
        objs.append((Y+6, lambda hm=hm, X=X, Y=Y: img.paste(hm, (X-3, Y-3), hm)))
    draw_stage(d, t, objs, put)
    if not show:
        ph = ((t+5)/14.0) % 2; up = ph < 1; f = smooth(ph if up else 2-ph); cy = 468-f*350; cx = 133
        def cart(cx=cx, cy=cy, up=up):
            X, Y = L2(cx, cy)
            d.rectangle([X-5, Y-1, X+5, Y+12], fill=OUT); d.rectangle([X-4, Y, X+4, Y+11], fill=(150, 100, 56))
            d.rectangle([X-3, Y+1, X+3, Y+6], fill=(226, 196, 86)); d.point((X-1, Y+2), fill=(250, 226, 130))
            for (wx, wy) in ((X-6, Y+2), (X+5, Y+2), (X-6, Y+9), (X+5, Y+9)): d.rectangle([wx, wy, wx+1, wy+2], fill=(40, 32, 28))
            s = NPC(8100, 'up' if up else 'down', int(t*6) % 4)
            img.paste(s, (X-6, Y+12 if up else Y-17), s)
        if night < 0.5: objs.append((L2(cx, cy)[1]+14, cart))
        vis = []
        for pp in people:
            st = person_state(pp, t)
            if st is None: continue
            x, y = st[0], st[1]
            if view and not (view[0]-6 <= x <= view[2]+6 and view[1]-10 <= y <= view[3]+10): continue
            if night > 0.5 and prio(pp['id']*7) < 0.55: continue
            chegando = pp['ts'] is not None and 0 <= t-pp['ts'] < 9
            vis.append((0 if chegando else 1, prio(pp['id']), pp, st))
        vis.sort(key=lambda v: (v[0], v[1]))
        for _, _, pp, st in vis[:MAX_NPC]:
            x, y, mv, _ = st
            st0 = person_state(pp, t-0.08)
            dx, dy = (x-st0[0], y-st0[1]) if st0 else (0, 1)
            moving = abs(dx)+abs(dy) > 0.05
            put(NPC(pp['id'], dir_of(dx, dy) if moving else 'down', (int(t*8+pp['ph']*3) % 4) if moving else 0), x, y)
        if night < 0.5:
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
        for c in PLATEIA:
            st = plateia_state(c, t)
            if st is None: continue
            x, y, walking, hop = st
            if walking:
                st0 = plateia_state(c, t-0.06)
                dx, dy = (x-st0[0], y-st0[1]) if st0 else (0, -1)
                put(NPC(c['id'], dir_of(dx, dy), int(t*8+c['ph']*3) % 4), x, y)
            else:
                fr = (int(t*5+c['ph']) % 2)*2 if hop > 0.3 else 0
                put(NPC(c['id'], 'up', fr), x, y-hop)
    if active and not show and night < 0.5:
        i, l = active; hx, hy = lot(*l); roady = l[1]+5
    # poeira do calçamento
    pf = pave_f(t)
    if 0 < pf < 1:
        r = pf*PAVE_R
        for k in range(40):
            ang = k/40*2*math.pi+t
            qx, qy = PAVE_C[0]+math.cos(ang)*r, PAVE_C[1]+math.sin(ang)*r
            onroad = (MAINX0-2 <= qx <= MAINX1+3 and 104 <= qy <= 480) or any(ry_-3 <= qy <= ry_+13 and 12 <= qx <= 221 for ry_ in (ROADA, ROADB, ROADC, ROADD))
            if not onroad: continue
            q = (t*7+k*0.3) % 1
            X, Y = L2(qx, qy); c_ = int(220-q*40)
            objs.append((9997, lambda X=X, Y=Y, c_=c_, q=q: d.ellipse([X-2-q*3, Y-2-q*3, X+2+q*3, Y+2+q*3], fill=(c_, c_-6, c_-14))))
    objs.sort(key=lambda o: o[0])
    for _, fn in objs: fn()
    out = np.array(img.convert('RGB'))
    return out
