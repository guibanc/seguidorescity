# =====================================================================
#  VILA EM 16 BITS  (ep. 3 em diante)
#  Mesmo mapa lógico do 8 bits (270x480); tudo é desenhado em 2x
#  (540x960) com mais cores, contorno, sombreado e detalhe.
# =====================================================================
import numpy as np, random, math
from PIL import Image, ImageDraw
from world import W, H, MAINX0, MAINX1, ROADA, ROADB, ROADC, river_x, clamp, smooth

S = 2
W2, H2 = W*S, H*S
OUT = (30, 24, 36)          # contorno padrão

def sh(c, f):
    """escurece (f<1) ou clareia (f>1) uma cor"""
    if f <= 1: return tuple(int(v*f) for v in c[:3])
    return tuple(int(v + (255-v)*(f-1)) for v in c[:3])
def A(c, a=255): return tuple(c[:3]) + (a,)

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0

def value_noise(h, w, cell, seed):
    r = np.random.RandomState(seed)
    gh, gw = h//cell+2, w//cell+2
    g = r.rand(gh, gw)
    ys = np.arange(h)/cell; xs = np.arange(w)/cell
    y0 = ys.astype(int); x0 = xs.astype(int)
    fy = ys-y0; fx = xs-x0
    fy = fy*fy*(3-2*fy); fx = fx*fx*(3-2*fx)
    a = g[y0][:, x0]; b = g[y0][:, x0+1]; c = g[y0+1][:, x0]; d = g[y0+1][:, x0+1]
    top = a+(b-a)*fx[None, :]; bot = c+(d-c)*fx[None, :]
    return top+(bot-top)*fy[:, None]

# ---------------- chão ----------------
GRASS = [(66, 138, 58), (82, 158, 66), (98, 176, 78), (118, 192, 92)]
DIRT = [(146, 102, 64), (170, 126, 82), (188, 146, 98), (206, 168, 120)]
WATER = [(38, 86, 168), (50, 108, 194), (70, 136, 216), (110, 172, 232)]
SAND = [(176, 154, 98), (204, 186, 128), (224, 208, 150)]

def make_ground16(extra_roads=()):
    """grama + rio + ruas + praça, tudo estático (a vila já tem as ruas desde o ep. 1)"""
    n = value_noise(H2, W2, 24, 11)*0.6 + value_noise(H2, W2, 7, 12)*0.3 + np.random.RandomState(13).rand(H2, W2)*0.1
    yy, xx = np.mgrid[0:H2, 0:W2]
    q = n + (BAYER[yy % 4, xx % 4]-0.5)*0.12
    idx = np.clip(((q-0.22)/0.56*4).astype(int), 0, 3)
    a = np.array(GRASS, np.uint8)[idx]
    r = np.random.RandomState(14)
    # tufos de grama (forma de "v")
    for _ in range(2600):
        x, y = r.randint(2, W2-3), r.randint(3, H2-2)
        base = idx[y, x]
        dk = GRASS[max(0, base-1)]; lt = GRASS[min(3, base+1)]
        a[y, x] = dk; a[y-1, x-1] = dk; a[y-1, x+1] = dk
        if r.rand() < 0.5: a[y-2, x-1] = lt; a[y-2, x+1] = lt
    # florzinhas em grupinhos
    FL = [(250, 236, 120), (244, 150, 176), (252, 252, 252), (186, 166, 246), (250, 180, 80)]
    for _ in range(170):
        cx, cy = r.randint(4, W2-5), r.randint(4, H2-5); c = FL[r.randint(0, len(FL))]
        for _ in range(r.randint(2, 5)):
            x, y = cx+r.randint(-3, 4), cy+r.randint(-3, 4)
            a[y, x] = c; a[y+1, x] = GRASS[0]
            if r.rand() < 0.3: a[y, x+1] = (250, 220, 80)
    # pedrinhas
    for _ in range(140):
        x, y = r.randint(2, W2-3), r.randint(2, H2-3)
        a[y, x] = (150, 150, 140); a[y, x+1] = (176, 176, 166); a[y+1, x] = (110, 110, 104); a[y+1, x+1] = (130, 130, 122)

    # ---- rio ----
    river = np.zeros((H2, W2), bool)
    dist = np.abs(xx/S - np.array([river_x(y/S) for y in range(H2)])[:, None])
    wob = value_noise(H2, W2, 6, 15)*1.2
    d = dist + wob*0.5
    bank = (d >= 7) & (d < 9.6)
    wet = (d >= 6.3) & (d < 7)
    water = d < 6.3
    sv = value_noise(H2, W2, 3, 16)
    sand = np.array(SAND, np.uint8)[np.clip((sv*3).astype(int), 0, 2)]
    a[bank] = sand[bank]
    a[wet] = (150, 130, 84)
    depth = np.clip(1-d/6.3, 0, 1) + (BAYER[yy % 4, xx % 4]-0.5)*0.25
    widx = np.clip(3-(depth*3.6).astype(int), 0, 3)
    wcol = np.array(WATER, np.uint8)[widx]
    a[water] = wcol[water]
    river[water] = True
    # pedrinhas na margem
    by, bx = np.nonzero(bank)
    for k in r.choice(len(by), 260, replace=False):
        y, x = by[k], bx[k]
        if x+1 < W2 and y+1 < H2:
            a[y, x] = (140, 132, 116); a[y, x+1] = (168, 160, 142); a[y+1, x] = (110, 104, 92)

    # ---- ruas ----
    def road(x0, y0, x1, y1, vertical):
        X0, Y0, X1, Y1 = x0*S, y0*S, x1*S, y1*S
        rr = np.random.RandomState(x0*31+y0)
        ev = value_noise(H2, W2, 5, x0+y0)
        for y in range(Y0-2, Y1+2):
            for x in range(X0-2, X1+2):
                if not (0 <= x < W2 and 0 <= y < H2): continue
                if vertical: e = min(x-X0, X1-1-x); along = y
                else: e = min(y-Y0, Y1-1-y); along = x
                ee = e + (ev[y, x]-0.5)*3
                if ee < -0.5: continue
                if ee < 1.2: c = DIRT[0] if ee >= 0 else GRASS[0]
                else:
                    c = DIRT[2] if rr.rand() > 0.12 else DIRT[1]
                    if (BAYER[y % 4, x % 4]+ev[y, x]*0.5) > 1.15: c = DIRT[3]
                a[y, x] = c
        # sulcos de roda
        if vertical:
            for rx in (X0+5, X1-6):
                for y in range(Y0, Y1):
                    if rr.rand() < 0.85: a[y, rx] = DIRT[1]
        else:
            for ry_ in (Y0+5, Y1-6):
                for x in range(X0, X1):
                    if rr.rand() < 0.85: a[ry_, x] = DIRT[1]
        # cascalho
        for _ in range((X1-X0)*(Y1-Y0)//60):
            x, y = rr.randint(X0+2, X1-2), rr.randint(Y0+2, Y1-2)
            a[y, x] = (222, 196, 150); a[y+1, x] = DIRT[0]
    road(MAINX0, 104, MAINX1+1, 480, True)
    for ry in (ROADA, ROADB, ROADC)+tuple(extra_roads): road(14, ry, 219, ry+10, False)

    # ---- praça (pedra) ----
    X0, Y0, X1, Y1 = 100*S, 213*S, 164*S, 277*S
    rr = np.random.RandomState(21)
    a[Y0:Y1, X0:X1] = (120, 112, 104)
    for row, y in enumerate(range(Y0+2, Y1-2, 6)):
        off = 3 if row % 2 else 0
        for x in range(X0+2-off, X1-2, 6):
            sx0, sx1 = max(x, X0+2), min(x+5, X1-2)
            if sx1 <= sx0: continue
            base = [(186, 178, 162), (198, 190, 172), (172, 164, 150), (206, 196, 176)][rr.randint(0, 4)]
            a[y:y+5, sx0:sx1] = base
            a[y, sx0:sx1] = sh(base, 1.12); a[y:y+5, sx0] = sh(base, 1.08)
            a[y+4, sx0:sx1] = sh(base, 0.82); a[y:y+5, sx1-1] = sh(base, 0.86)
    a[Y0:Y0+2, X0:X1] = (150, 142, 132); a[Y1-2:Y1, X0:X1] = (98, 92, 86)
    a[Y0:Y1, X0:X0+2] = (140, 132, 124); a[Y0:Y1, X1-2:X1] = (104, 98, 90)
    return a, river

# ---------------- árvores ----------------
LEAF = [[(24, 70, 40), (36, 100, 50), (56, 134, 62), (88, 168, 76), (140, 200, 104)],
        [(22, 74, 58), (34, 104, 74), (52, 138, 92), (84, 172, 112), (136, 206, 146)]]
def tree16(r, kind, seed):
    rr = random.Random(seed)
    R = r*S
    w = 2*R+8; h = 2*R+12
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); p = im.load()
    cx, cy = R+3, R+3
    blobs = [(cx, cy, R*0.72)]
    for k in range(6):
        ang = k/6*2*math.pi + rr.uniform(-0.4, 0.4)
        blobs.append((cx+math.cos(ang)*R*0.42, cy+math.sin(ang)*R*0.42, R*rr.uniform(0.45, 0.6)))
    # sombra no chão
    for y in range(h):
        for x in range(w):
            if ((x-cx-3)/(R*0.95))**2+((y-cy-R*0.55)/(R*0.62))**2 < 1: p[x, y] = (16, 40, 20, 95)
    # tronco
    for y in range(cy+int(R*0.5), cy+R+5):
        for x in range(cx-2, cx+2):
            p[x, y] = A([(70, 46, 30), (104, 70, 44), (124, 86, 54), (88, 58, 36)][x-(cx-2)])
    pal = LEAF[kind]
    inside = np.zeros((h, w), bool); val = np.zeros((h, w))
    for y in range(h):
        for x in range(w):
            best = None
            for (bx, by, br) in blobs:
                dd = math.hypot(x-bx, y-by)/br
                if dd < 1 and (best is None or dd < best[0]): best = (dd, bx, by, br)
            if best:
                dd, bx, by, br = best
                inside[y, x] = True
                light = ((bx-x)+(by-y))/(br*1.6) + (1-dd)*0.55 - (y-cy)/(R*3)
                val[y, x] = light + (BAYER[y % 4, x % 4]-0.5)*0.35 + rr.uniform(-0.12, 0.12)
    for y in range(h):
        for x in range(w):
            if not inside[y, x]: continue
            edge = not (inside[y-1, x] and inside[y+1, x] and inside[y, x-1] and inside[y, x+1]) if 0 < y < h-1 and 0 < x < w-1 else True
            v = val[y, x]
            k = 0 if edge else (1 if v < 0.15 else 2 if v < 0.55 else 3 if v < 0.95 else 4)
            p[x, y] = A(pal[k])
    # tufos de folha (clusters claros)
    for _ in range(R//2+2):
        x, y = cx+rr.randint(-R//2, R//3), cy+rr.randint(-R//2, R//4)
        if inside[y, x] and inside[y+1, x+1]:
            p[x, y] = A(pal[4]); p[x+1, y] = A(pal[3]); p[x, y+1] = A(pal[3])
    return im, (cx, cy+R+4)

# ---------------- casas ----------------
ROOF16 = [[(120, 34, 30), (168, 52, 44), (204, 78, 62), (232, 120, 96)],
          [(34, 52, 112), (52, 84, 162), (78, 116, 196), (124, 160, 226)],
          [(30, 84, 44), (50, 120, 62), (76, 156, 82), (122, 192, 116)],
          [(136, 72, 22), (190, 110, 42), (220, 146, 70), (244, 186, 112)],
          [(74, 40, 104), (108, 66, 146), (144, 102, 184), (184, 148, 216)],
          [(94, 54, 32), (136, 82, 50), (172, 118, 78), (206, 158, 114)]]
WALL16 = [(238, 224, 186), (246, 242, 234), (222, 198, 158), (236, 212, 176)]
LITW = [(255, 216, 104), (255, 238, 164)]

def roof_tiles(d, x0, y0, x1, y1, ramp, rows_done=None):
    """telhado de telhas (3/4 de cima). rows_done: quantas fileiras (de baixo pra cima) já colocadas"""
    rows = list(range(y1, y0-1, -3))
    for k, yy in enumerate(rows):
        if rows_done is not None and k >= rows_done: break
        top = max(y0, yy-2)
        d.rectangle([x0, top, x1, yy], fill=A(ramp[2]))
        d.line([x0, yy, x1, yy], fill=A(ramp[1]))
        off = 2 if k % 2 else 0
        for x in range(x0+off, x1+1, 4):
            d.line([x, top, x, yy], fill=A(ramp[1]))
            if x+1 <= x1: d.point((x+1, top), fill=A(ramp[3]))
    return len(rows)

def house16(var, p, lit=False, venda=False):
    """42x50 (lote lógico 21x25). p: 0..1"""
    im = Image.new('RGBA', (42, 50), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ramp = ROOF16[var % 6]; wc = WALL16[(var//2) % 4]
    X0, X1 = 2, 37           # largura útil
    RY, WY, BY = 6, 28, 41   # telhado 6..27 / parede 28..40 / base 41
    if p <= 0: return im
    stake = (120, 80, 40)
    if p < 1:
        for (x, y) in [(X0, RY), (X1, RY), (X0, BY), (X1, BY)]:
            d.line([x, y-3, x, y], fill=A(stake)); d.point((x, y-3), fill=A(sh(stake, 1.4)))
    if p < 0.25:
        for x in range(X0, X1, 3): d.point((x, RY-1), fill=(250, 250, 250, 220)); d.point((x, BY-1), fill=(250, 250, 250, 220))
        for y in range(RY, BY, 3): d.point((X0, y), fill=(250, 250, 250, 220)); d.point((X1, y), fill=(250, 250, 250, 220))
        n = int(p/0.25*(X1-X0-2))
        if n > 0:
            d.rectangle([X0+1, RY+1, X0+n, BY-1], fill=(150, 150, 156, 255))
            for y in range(RY+3, BY-1, 4):
                for x in range(X0+2+(y % 8)//2, X0+n, 6): d.point((x, y), fill=(128, 128, 134, 255))
        return im
    # fundação + piso
    d.rectangle([X0, RY, X1, BY], fill=(140, 140, 146, 255))
    d.rectangle([X0+2, RY+2, X1-2, WY-1], fill=(176, 130, 84, 255))
    for y in range(RY+3, WY, 3): d.line([X0+2, y, X1-2, y], fill=(150, 108, 68, 255))
    wood = (124, 82, 46)
    if p < 0.6:
        f = (p-0.25)/0.35
        for x in (X0+1, X1-1, (X0+X1)//2):
            d.rectangle([x-1, RY, x, BY], fill=A(wood)); d.line([x-1, RY, x-1, BY], fill=A(sh(wood, 1.3)))
        d.rectangle([X0, RY, X1, RY+1], fill=A(wood))
        hh = int(round(f*(BY-WY+1)))
        if hh > 0:
            d.rectangle([X0+1, BY+1-hh, X1-1, BY], fill=A(wc))
            for y in range(BY+1-hh, BY+1, 2): d.line([X0+1, y, X1-1, y], fill=A(sh(wc, 0.93)))
        return im
    # ---- parede pronta ----
    d.rectangle([X0+1, WY, X1-1, BY], fill=A(wc))
    if var % 3 == 0:     # parede de tábuas
        for y in range(WY+1, BY, 3): d.line([X0+1, y, X1-1, y], fill=A(sh(wc, 0.9)))
    else:                # reboco com textura leve
        rr = random.Random(var)
        for _ in range(14): d.point((rr.randint(X0+2, X1-2), rr.randint(WY+2, BY-2)), fill=A(sh(wc, 0.92)))
    d.line([X0+1, BY, X1-1, BY], fill=A(sh(wc, 0.7))); d.line([X0+1, BY-1, X1-1, BY-1], fill=A(sh(wc, 0.82)))
    d.line([X0, WY, X0, BY], fill=A(OUT)); d.line([X1, WY, X1, BY], fill=A(OUT))
    # porta
    dx = (X0+X1)//2-3
    d.rectangle([dx-1, WY+3, dx+7, BY], fill=A(sh(wc, 0.62)))
    d.rectangle([dx, WY+4, dx+6, BY], fill=(118, 70, 38, 255))
    d.line([dx+3, WY+4, dx+3, BY], fill=(92, 52, 28, 255))
    d.line([dx, WY+4, dx+6, WY+4], fill=(150, 98, 58, 255))
    d.point((dx+5, WY+9), fill=(250, 210, 90, 255))
    d.rectangle([dx-1, BY+1, dx+7, BY+2], fill=(170, 168, 160, 255)); d.line([dx-1, BY+2, dx+7, BY+2], fill=(120, 118, 112, 255))
    # janelas
    for wx in (X0+4, X1-11):
        if venda and wx > dx: pass
        d.rectangle([wx-1, WY+3, wx+7, WY+10], fill=(250, 250, 246, 255))
        g = LITW[0] if lit else (110, 166, 222)
        d.rectangle([wx, WY+4, wx+6, WY+9], fill=A(g))
        if lit: d.rectangle([wx+1, WY+5, wx+3, WY+6], fill=A(LITW[1]))
        else: d.line([wx, WY+4, wx+2, WY+4], fill=(214, 236, 252, 255)); d.point((wx, WY+5), fill=(214, 236, 252, 255))
        d.line([wx+3, WY+4, wx+3, WY+9], fill=(250, 250, 246, 255)); d.line([wx, WY+6, wx+6, WY+6], fill=(250, 250, 246, 255))
        sc = ramp[1]
        d.rectangle([wx-3, WY+3, wx-2, WY+10], fill=A(sc)); d.rectangle([wx+8, WY+3, wx+9, WY+10], fill=A(sc))
        # floreira
        d.rectangle([wx-1, WY+11, wx+7, WY+12], fill=(130, 84, 50, 255))
        for k in range(5): d.point((wx+k*2-1, WY+10), fill=[(240, 80, 100), (250, 220, 80), (250, 250, 250), (70, 150, 70), (240, 120, 180)][(k+var) % 5] + (255,))
    if venda:
        for x in range(X0, X1+1):
            c = (214, 44, 44) if (x//4) % 2 else (250, 250, 250)
            d.line([x, WY, x, WY+2], fill=A(c))
            if x % 4 == 0: d.point((x, WY+3), fill=A(c))
        d.line([X0, WY+2, X1, WY+2], fill=(160, 30, 30, 255))
        for cx_, cols in ((X0+2, [(232, 64, 50), (250, 200, 50)]), (X1-9, [(96, 190, 70), (240, 140, 40)])):
            d.rectangle([cx_, BY+1, cx_+7, BY+4], fill=(150, 104, 60, 255)); d.line([cx_, BY+4, cx_+7, BY+4], fill=(104, 70, 38, 255))
            for j in range(4): d.rectangle([cx_+j*2, BY, cx_+j*2+1, BY+1], fill=A(cols[j % 2]))
    # ---- telhado ----
    f = clamp((p-0.6)/0.4)
    for x in range(X0, X1+1, 4): d.line([x, RY, x, WY-1], fill=A(wood))
    total = len(range(WY-1, RY-1, -3))
    done = total if f >= 1 else int(math.ceil(f*total))
    roof_tiles(d, X0-1, RY, X1+1, WY-1, ramp, done)
    if f >= 1:
        d.rectangle([X0-1, RY-1, X1+1, RY+1], fill=A(ramp[3])); d.line([X0-1, RY+2, X1+1, RY+2], fill=A(ramp[2]))
        d.line([X0-2, RY-1, X0-2, WY-1], fill=A(OUT)); d.line([X1+2, RY-1, X1+2, WY-1], fill=A(OUT))
        d.line([X0-2, RY-2, X1+2, RY-2], fill=A(OUT)); d.line([X0-2, WY-1, X1+2, WY-1], fill=A(ramp[0]))
        d.line([X0-1, WY-2, X1+1, WY-2], fill=A(ramp[1]))
        # chaminé de tijolo
        cx = X1-10
        d.rectangle([cx-1, RY-6, cx+6, RY+4], fill=A(OUT))
        d.rectangle([cx, RY-5, cx+5, RY+3], fill=(168, 82, 62, 255))
        for y in range(RY-4, RY+3, 2):
            off = 0 if y % 4 else 2
            for x in range(cx+off, cx+6, 4): d.point((x, y), fill=(128, 60, 46, 255))
        d.rectangle([cx, RY-5, cx+5, RY-4], fill=(110, 104, 104, 255)); d.line([cx+1, RY-5, cx+4, RY-5], fill=(40, 36, 36, 255))
        # sombra
        for y in range(RY, BY+3): im.putpixel((X1+3, y), (0, 0, 0, 70)); im.putpixel((X1+4, y), (0, 0, 0, 40))
        for x in range(X0, X1+5):
            if im.getpixel((x, BY+3))[3] == 0: im.putpixel((x, BY+3), (0, 0, 0, 60))
    return im

# ---------------- mercadinho ----------------
def mercado16(p, lit=False):
    im = Image.new('RGBA', (42, 50), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    X0, X1, RY, WY, BY = 2, 37, 6, 26, 41
    if p <= 0: return im
    if p < 1:
        b = house16(0, min(p, 0.59))
        if p < 0.6: return b
    d.rectangle([X0, WY, X1, BY], fill=(250, 238, 196, 255))
    d.line([X0, BY, X1, BY], fill=(196, 176, 130, 255)); d.line([X0, WY, X0, BY], fill=A(OUT)); d.line([X1, WY, X1, BY], fill=A(OUT))
    g = LITW[0] if lit else (150, 200, 236)
    for wx in (X0+2, X1-11):    # vitrines com prateleiras
        d.rectangle([wx, WY+5, wx+9, BY-2], fill=(90, 96, 108, 255))
        d.rectangle([wx+1, WY+6, wx+8, BY-3], fill=A(g))
        for k, yy in enumerate(range(WY+7, BY-3, 3)):
            for x in range(wx+1, wx+9):
                if (x+k) % 2: d.point((x, yy), fill=[(232, 72, 60), (250, 200, 60), (80, 170, 80), (240, 140, 40)][(x+k) % 4] + (255,))
        if not lit: d.line([wx+1, WY+6, wx+3, WY+6], fill=(230, 244, 255, 255))
    dx = (X0+X1)//2-4
    d.rectangle([dx, WY+5, dx+8, BY], fill=(70, 80, 92, 255)); d.rectangle([dx+1, WY+6, dx+7, BY], fill=A(g))
    d.line([dx+4, WY+6, dx+4, BY], fill=(70, 80, 92, 255))
    d.rectangle([dx-1, BY+1, dx+9, BY+2], fill=(180, 178, 170, 255))
    # toldo verde e branco
    for x in range(X0-1, X1+2):
        c = (40, 150, 70) if (x//4) % 2 else (250, 250, 250)
        d.line([x, WY, x, WY+3], fill=A(c))
        if x % 4 in (0, 1): d.point((x, WY+4), fill=A(c))
    d.line([X0-1, WY+3, X1+1, WY+3], fill=(24, 104, 48, 255))
    # telhado plano
    f = clamp((p-0.6)/0.3) if p < 1 else 1
    if f > 0:
        top = WY-1-int(f*(WY-RY))
        d.rectangle([X0-1, top, X1+1, WY-1], fill=(196, 194, 188, 255))
        for y in range(top, WY, 4): d.line([X0, y, X1, y], fill=(178, 176, 170, 255))
        for x in range(X0+6, X1, 8): d.line([x, top, x, WY-1], fill=(184, 182, 176, 255))
    if p >= 0.92:
        d.rectangle([X0-2, RY-1, X1+2, WY-1], outline=A(OUT))
        d.rectangle([X0+3, RY+11, X0+9, RY+16], fill=(164, 170, 178, 255)); d.rectangle([X0+4, RY+12, X0+8, RY+15], fill=(120, 126, 134, 255))
        for k in range(3): d.line([X0+4, RY+12+k, X0+8, RY+12+k], fill=(140, 146, 154, 255)) if k % 2 else None
        # placa vermelha com carrinho
        d.rectangle([X0+10, RY+1, X1-9, RY+9], fill=(206, 40, 40, 255)); d.rectangle([X0+10, RY+1, X1-9, RY+9], outline=(130, 20, 20, 255))
        cx = (X0+X1)//2-3
        d.line([cx-1, RY+3, cx, RY+3], fill=(255, 255, 255, 255)); d.rectangle([cx, RY+4, cx+6, RY+6], outline=(255, 255, 255, 255))
        d.point((cx+1, RY+8), fill=(255, 255, 255, 255)); d.point((cx+5, RY+8), fill=(255, 255, 255, 255))
        # caixotes de frutas na frente + carrinho
        for cx_, cols in ((X0+1, [(232, 64, 50), (250, 200, 50)]), (X1-8, [(96, 190, 70), (240, 140, 40)])):
            d.rectangle([cx_, BY+1, cx_+7, BY+4], fill=(150, 104, 60, 255)); d.line([cx_, BY+4, cx_+7, BY+4], fill=(104, 70, 38, 255))
            for j in range(4): d.rectangle([cx_+j*2, BY, cx_+j*2+1, BY+1], fill=A(cols[j % 2]))
        for y in range(RY, BY+3): im.putpixel((X1+3, y), (0, 0, 0, 70)); im.putpixel((X1+4, y), (0, 0, 0, 40))
    return im

# ---------------- igreja ----------------
def church16(lit=False):
    im = Image.new('RGBA', (68, 92), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    X0, X1, RY, WY, BY = 2, 62, 24, 60, 84
    ramp = [(40, 48, 84), (64, 76, 120), (92, 106, 156), (134, 148, 196)]
    wall = (240, 236, 228)
    d.rectangle([X0, WY, X1, BY], fill=A(wall)); d.line([X0, BY, X1, BY], fill=(190, 184, 172, 255))
    d.line([X0, WY, X0, BY], fill=A(OUT)); d.line([X1, WY, X1, BY], fill=A(OUT))
    for y in range(WY+2, BY, 4): d.line([X0+1, y, X1-1, y], fill=(230, 226, 216, 255))
    # vitrais em arco
    for wx in (X0+8, X1-14):
        d.rectangle([wx-1, WY+6, wx+6, WY+18], fill=(120, 116, 110, 255)); d.ellipse([wx-1, WY+3, wx+6, WY+10], fill=(120, 116, 110, 255))
        cols = [LITW[0]]*3 if lit else [(220, 70, 70), (70, 130, 226), (240, 206, 70)]
        d.rectangle([wx, WY+7, wx+5, WY+17], fill=A(cols[0])); d.ellipse([wx, WY+4, wx+5, WY+9], fill=A(cols[1]))
        d.rectangle([wx, WY+12, wx+5, WY+17], fill=A(cols[2])); d.line([wx+2, WY+5, wx+2, WY+17], fill=(90, 86, 80, 255))
    # porta dupla em arco
    cx = (X0+X1)//2
    d.rectangle([cx-7, WY+9, cx+7, BY], fill=(150, 146, 138, 255)); d.ellipse([cx-7, WY+4, cx+7, WY+16], fill=(150, 146, 138, 255))
    d.rectangle([cx-6, WY+10, cx+6, BY], fill=(112, 64, 34, 255)); d.ellipse([cx-6, WY+5, cx+6, WY+15], fill=(112, 64, 34, 255))
    d.line([cx, WY+6, cx, BY], fill=(80, 44, 24, 255)); d.point((cx-2, WY+17), fill=(240, 200, 80, 255)); d.point((cx+2, WY+17), fill=(240, 200, 80, 255))
    for k in range(3): d.rectangle([cx-9-k*2, BY+1+k, cx+9+k*2, BY+1+k], fill=(176-k*16, 172-k*16, 164-k*16, 255))
    # telhado
    roof_tiles(d, X0-1, RY, X1+1, WY-1, ramp)
    d.rectangle([X0-1, RY-1, X1+1, RY+1], fill=A(ramp[3]))
    d.line([X0-2, RY-2, X1+2, RY-2], fill=A(OUT)); d.line([X0-2, RY-2, X0-2, WY-1], fill=A(OUT)); d.line([X1+2, RY-2, X1+2, WY-1], fill=A(OUT))
    # torre com sino
    tx0, tx1 = cx-9, cx+9
    d.rectangle([tx0-1, 10, tx1+1, RY+16], fill=A(OUT))
    d.rectangle([tx0, 11, tx1, RY+15], fill=(236, 232, 224, 255)); d.line([tx1-2, 11, tx1-2, RY+15], fill=(212, 206, 196, 255))
    d.rectangle([tx0, 11, tx1, 14], fill=A(ramp[2])); d.line([tx0, 11, tx1, 11], fill=A(ramp[3]))
    d.rectangle([cx-4, 18, cx+4, 28], fill=(56, 48, 46, 255)); d.ellipse([cx-4, 15, cx+4, 21], fill=(56, 48, 46, 255))
    d.ellipse([cx-3, 20, cx+3, 26], fill=(214, 168, 56, 255)); d.point((cx-1, 21), fill=(250, 220, 120, 255)); d.point((cx, 27), fill=(150, 110, 30, 255))
    d.ellipse([cx-4, RY+5, cx+4, RY+12], fill=(250, 250, 246, 255)); d.ellipse([cx-4, RY+5, cx+4, RY+12], outline=(90, 86, 80, 255))
    d.line([cx, RY+8, cx, RY+6], fill=(40, 36, 36, 255)); d.line([cx, RY+8, cx+2, RY+8], fill=(40, 36, 36, 255))
    # cruz
    d.rectangle([cx-1, 0, cx+1, 10], fill=(140, 110, 30, 255)); d.rectangle([cx-4, 2, cx+4, 4], fill=(140, 110, 30, 255))
    d.line([cx, 0, cx, 9], fill=(250, 226, 120, 255)); d.line([cx-3, 3, cx+3, 3], fill=(250, 226, 120, 255))
    for y in range(RY, BY+4): im.putpixel((X1+3, y), (0, 0, 0, 70)); im.putpixel((X1+4, y), (0, 0, 0, 40))
    return im

# ---------------- moradores 16 bits ----------------
SKIN16 = [(252, 218, 186), (238, 192, 150), (214, 160, 116), (178, 120, 80), (136, 86, 54), (98, 60, 38)]
HAIR16 = [(36, 26, 22), (70, 44, 26), (112, 70, 36), (196, 150, 70), (236, 204, 120), (150, 56, 30), (176, 176, 180), (24, 22, 30)]
SHIRT16 = [(214, 56, 56), (54, 104, 214), (246, 200, 54), (64, 164, 86), (240, 240, 236), (150, 76, 196), (238, 126, 40),
           (36, 172, 186), (228, 104, 156), (44, 52, 70), (126, 196, 96), (176, 120, 72)]
PANTS16 = [(46, 60, 108), (70, 50, 40), (36, 36, 44), (98, 100, 112), (150, 120, 84), (60, 90, 70)]
SHOES16 = [(40, 30, 26), (230, 230, 226), (120, 70, 40), (200, 60, 50)]
HAIRSTYLES = ['curto', 'raspado', 'longo', 'rabo', 'coque', 'afro', 'careca', 'franja']

def npc_look(seed):
    """aparência aleatória determinística (o site usa o mesmo seed)"""
    r = random.Random(seed*7919+13)
    hs = r.choice(HAIRSTYLES)
    look = dict(seed=seed, pele=r.randrange(6), cabelo=hs, cor_cabelo=r.randrange(8),
                camisa=r.randrange(12), estampa=r.choice(['lisa', 'lisa', 'listrada', 'regata', 'duas_cores']),
                camisa2=r.randrange(12), baixo=r.choice(['calca', 'calca', 'calca', 'bermuda', 'saia', 'vestido']),
                cor_baixo=r.randrange(6), sapato=r.randrange(4),
                oculos=r.random() < 0.16, chapeu=(r.choice(['bone', 'palha', 'gorro']) if r.random() < 0.18 else None),
                cor_chapeu=r.randrange(12), barba=(r.random() < 0.18 and hs not in ('longo', 'coque', 'rabo')))
    return look

def _sil_outline(im):
    """contorno escuro por fora da silhueta (estilo 16 bits)"""
    a = np.array(im); al = a[:, :, 3] > 200
    sol = a[:, :, 3] == 255
    o = np.zeros_like(al)
    o[1:, :] |= sol[:-1, :]; o[:-1, :] |= sol[1:, :]; o[:, 1:] |= sol[:, :-1]; o[:, :-1] |= sol[:, 1:]
    o &= ~al
    a[o] = OUT + (255,)
    return Image.fromarray(a.copy()).copy()

def npc_sprite(look, dirc='down', frame=0, uniforme=None, tool=None, carry=None):
    """12x18 px. dirc: down/up/right/left. frame 0..3. uniforme: 'pedreiro'|'mercado'|None
       tool: 'up'/'down' (martelo). carry: 'tabua'|'sacola'|None"""
    if dirc == 'left':
        return npc_sprite(look, 'right', frame, uniforme, tool, carry).transpose(Image.FLIP_LEFT_RIGHT)
    im = Image.new('RGBA', (12, 18), (0, 0, 0, 0)); p = im.load()
    skin = SKIN16[look['pele']]; hair = HAIR16[look['cor_cabelo']]
    shirt = SHIRT16[look['camisa']]; shirt2 = SHIRT16[look['camisa2']]
    bot = PANTS16[look['cor_baixo']]; shoe = SHOES16[look['sapato']]
    hat = look['chapeu']; hatc = SHIRT16[look['cor_chapeu']]
    if uniforme == 'pedreiro': shirt = (240, 128, 30); shirt2 = (250, 220, 60); hat = 'capacete'; hatc = (250, 206, 40)
    if uniforme == 'mercado': shirt2 = (40, 150, 70)
    def P(x, y, c):
        if 0 <= x < 12 and 0 <= y < 18: p[x, y] = A(c)
    bob = 1 if frame in (1, 3) else 0
    y0 = 1+bob
    # sombra
    for x in range(3, 9): p[x, 17] = (0, 0, 0, 60)
    p[2, 17] = (0, 0, 0, 30); p[9, 17] = (0, 0, 0, 30)
    # ---- pernas ----
    vestido = look['baixo'] == 'vestido'
    legc = skin if look['baixo'] in ('bermuda', 'saia', 'vestido') else bot
    if dirc in ('down', 'up'):
        L = {0: (0, 0), 1: (-1, 1), 2: (0, 0), 3: (1, -1)}[frame]
        for side, x in ((0, 4), (1, 7)):
            lift = L[side]
            for y in range(12+y0-1, 15+y0-1 - (1 if lift < 0 else 0)):
                P(x, y, legc if y > 12+y0-1 or look['baixo'] in ('calca',) else bot)
            P(x, 15+y0-1 - (1 if lift < 0 else 0), shoe)
        if look['baixo'] in ('calca',):
            for x in range(4, 8): P(x, 11+y0, bot)
    else:
        L = {0: (5, 6), 1: (4, 7), 2: (5, 6), 3: (7, 4)}[frame]
        for x in L:
            for y in range(12+y0-1, 15+y0-1): P(x, y, legc if look['baixo'] != 'calca' else sh(bot, 0.9 if x == L[0] else 1))
            P(x, 15+y0-1, shoe); P(x+1, 15+y0-1, shoe) if frame in (1, 3) and x == max(L) else None
    # ---- tronco (ombros mais estreitos que a cabeça) ----
    top_s = 6+y0
    for y in range(top_s, top_s+5):
        for x in range(4, 8):
            c = shirt
            if look['estampa'] == 'listrada' and (y-top_s) % 2 == 1: c = shirt2
            if look['estampa'] == 'duas_cores' and x >= 6: c = shirt2
            if uniforme == 'pedreiro' and (y-top_s) == 2: c = shirt2
            P(x, y, c)
    for x in range(4, 8): P(x, top_s+4, sh(shirt, 0.8)) if look['estampa'] != 'listrada' else None
    if dirc == 'down': P(5, top_s, sh(skin, 0.85)); P(6, top_s, sh(skin, 0.85))   # gola
    if uniforme == 'mercado' and dirc != 'up':
        for y in range(top_s+1, top_s+7): P(5, y, shirt2); P(6, y, shirt2)
        P(4, top_s+1, shirt2); P(7, top_s+1, shirt2)
    # saia / vestido / bermuda / calça
    if look['baixo'] in ('saia', 'vestido'):
        sc = shirt if vestido else bot
        for x in range(4, 8): P(x, top_s+5, sc)
        for x in range(3, 9): P(x, top_s+6, sc)
        if vestido:
            for x in range(3, 9): P(x, top_s+7, sh(sc, 0.82))
    elif look['baixo'] == 'bermuda':
        for x in range(4, 8): P(x, top_s+5, bot)
        P(4, top_s+6, bot); P(7, top_s+6, bot)
    else:
        for x in range(4, 8): P(x, top_s+5, bot)
    # braços
    swing = {0: 0, 1: 1, 2: 0, 3: -1}[frame]
    sl = skin if look['estampa'] == 'regata' else shirt
    if dirc in ('down', 'up'):
        for side, x in ((-1, 3), (1, 8)):
            dy = swing*side
            P(x, top_s+dy, sl); P(x, top_s+dy+1, sh(sl, 0.9))
            P(x, top_s+dy+2, skin); P(x, top_s+dy+3, sh(skin, 0.9))
    else:
        ax = 6+swing
        P(ax, top_s+1, sh(sl, 0.85)); P(ax, top_s+2, sh(sl, 0.85)); P(ax, top_s+3, skin)
    # ---- cabeça ----
    hy = y0
    for y in range(hy, hy+6):
        for x in range(3, 9): P(x, y, skin)
    P(3, hy, (0, 0, 0, 0)) if False else None
    hs = look['cabelo']
    if dirc == 'down':
        P(4, hy+3, (40, 30, 34)); P(7, hy+3, (40, 30, 34))
        P(4, hy+2, sh(hair, 0.8) if hs != 'careca' else sh(skin, 0.8)); P(7, hy+2, sh(hair, 0.8) if hs != 'careca' else sh(skin, 0.8))
        P(5, hy+5, sh(skin, 0.8)); P(6, hy+5, sh(skin, 0.8))
        P(3, hy+4, sh(skin, 0.9)); P(8, hy+4, sh(skin, 0.9))
        if look['oculos']:
            for x in (3, 4, 7, 8): P(x, hy+3, (30, 30, 40))
            P(5, hy+3, (30, 30, 40)); P(6, hy+3, (30, 30, 40)); P(4, hy+3, (120, 170, 220)); P(7, hy+3, (120, 170, 220))
        if look['barba']:
            for x in range(3, 9): P(x, hy+5, hair)
            P(3, hy+4, hair); P(8, hy+4, hair)
    elif dirc == 'right':
        P(7, hy+3, (40, 30, 34)); P(8, hy+4, sh(skin, 0.9)); P(9, hy+3, skin)
        if look['oculos']: P(7, hy+3, (30, 30, 40)); P(8, hy+3, (30, 30, 40))
        if look['barba']:
            for x in range(5, 9): P(x, hy+5, hair)
    # cabelo
    def hairpx(x, y, c=None): P(x, y, c or hair)
    hl = sh(hair, 1.25)
    if hs != 'careca':
        rows = {'raspado': 1}.get(hs, 2)
        for y in range(hy-1, hy+rows):
            for x in range(3, 9): hairpx(x, y)
        hairpx(4, hy-1, hl); hairpx(5, hy-1, hl)
        if dirc in ('down',):
            if hs in ('curto', 'franja', 'afro', 'rabo', 'coque'): hairpx(3, hy+2); hairpx(8, hy+2)
            if hs == 'franja':
                for x in range(3, 8): hairpx(x, hy+2)
            if hs == 'longo':
                for y in range(hy+1, hy+9): hairpx(2, y); hairpx(9, y)
                hairpx(3, hy+2); hairpx(8, hy+2)
        if dirc == 'up':
            for y in range(hy, hy+6):
                for x in range(3, 9): hairpx(x, y, hair if y < hy+5 else sh(hair, 0.85))
            if hs == 'raspado':
                for y in range(hy+2, hy+6):
                    for x in range(3, 9): P(x, y, sh(skin, 0.85))
            if hs == 'longo':
                for y in range(hy+6, hy+9):
                    for x in range(3, 9): hairpx(x, y)
            if hs == 'rabo':
                hairpx(5, hy+6); hairpx(6, hy+6); hairpx(5, hy+7); hairpx(6, hy+7)
        if dirc == 'right':
            for y in range(hy, hy+4): hairpx(3, y); hairpx(4, y)
            hairpx(5, hy+1)
            if hs == 'longo':
                for y in range(hy+4, hy+9): hairpx(3, y); hairpx(4, y)
            if hs == 'rabo':
                hairpx(2, hy+2); hairpx(1, hy+3); hairpx(2, hy+3); hairpx(1, hy+4)
        if hs == 'coque':
            for x in (5, 6): hairpx(x, hy-2); hairpx(x, hy-3)
            hairpx(4, hy-2); hairpx(7, hy-2)
        if hs == 'afro':
            for y in range(hy-2, hy+3): hairpx(2, y); hairpx(9, y)
            for x in range(3, 9): hairpx(x, hy-2)
    else:
        P(4, hy, sh(skin, 1.2)); P(5, hy, sh(skin, 1.2))
    # cantos arredondados da cabeça
    if hs != 'afro':
        for (x, y) in ((3, hy-1), (8, hy-1)): p[x, y] = (0, 0, 0, 0)
    if not look['barba'] and not (hs == 'longo' and dirc != 'right'):
        for (x, y) in ((3, hy+5), (8, hy+5)): p[x, y] = (0, 0, 0, 0)
    # chapéu
    if hat == 'bone':
        for x in range(3, 9): P(x, hy-1, hatc); P(x, hy, hatc)
        P(4, hy-1, sh(hatc, 1.3))
        if dirc == 'down':
            for x in range(3, 9): P(x, hy+1, sh(hatc, 0.75))
        elif dirc == 'right': P(9, hy+1, sh(hatc, 0.75)); P(10, hy+1, sh(hatc, 0.75))
    elif hat == 'palha':
        c = (226, 196, 112)
        for x in range(1, 11): P(x, hy+1, sh(c, 0.85))
        for x in range(3, 9): P(x, hy, c); P(x, hy-1, c)
        for x in range(3, 9): P(x, hy, (170, 70, 50)) if x % 1 == 0 and False else None
        P(4, hy-1, sh(c, 1.2))
    elif hat == 'gorro':
        for x in range(3, 9): P(x, hy-1, hatc); P(x, hy, hatc); P(x, hy+1, sh(hatc, 0.8))
        P(5, hy-2, (250, 250, 250)); P(6, hy-2, (250, 250, 250))
    elif hat == 'capacete':
        for x in range(2, 10): P(x, hy+1, sh(hatc, 0.8))
        for x in range(3, 9): P(x, hy, hatc); P(x, hy-1, hatc)
        for x in range(4, 8): P(x, hy-2, hatc)
        P(4, hy-1, sh(hatc, 1.3)); P(5, hy-2, sh(hatc, 1.3))
    im = _sil_outline(im).copy()
    p = im.load()
    # ferramentas / carga (por cima do contorno)
    if tool == 'up':
        for y in range(top_s-4, top_s+1): p[10, y] = (130, 86, 46, 255)
        p[9, top_s-4] = (160, 160, 170, 255); p[10, top_s-5] = (190, 190, 200, 255); p[11, top_s-4] = (160, 160, 170, 255)
    elif tool == 'down':
        for x in range(9, 12): p[x, top_s+2] = (130, 86, 46, 255)
        p[11, top_s+1] = (190, 190, 200, 255); p[11, top_s+3] = (160, 160, 170, 255)
    if carry == 'tabua':
        for x in range(0, 12): p[x, y0-1 if y0 > 0 else 0] = (176, 122, 70, 255)
        for x in range(0, 12): p[x, y0] = (140, 92, 50, 255)
        p[0, y0-1 if y0 > 0 else 0] = (214, 170, 120, 255)
    elif carry == 'sacola':
        p[10, top_s+3] = (248, 240, 210, 255); p[10, top_s+4] = (248, 240, 210, 255); p[11, top_s+4] = (232, 220, 186, 255)
        p[10, top_s+5] = (232, 220, 186, 255); p[11, top_s+3] = (226, 64, 50, 255)
    return im


# ---------------- escola (marco 400, ep. 4) — ocupa 2 lotes ----------------
def escola16(p, lit=False, bell=0, flag=0):
    """86x50 (2 lotes lógicos). p: 0..1  bell: -1/0/1 (balanço do sino)  flag: quadro da bandeira"""
    from font import draw_text
    im = Image.new('RGBA', (86, 50), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    X0, X1, RY, WY, BY = 2, 77, 10, 28, 41
    TX0, TX1 = 33, 46                       # torre do sino
    ramp = ROOF16[3]; wc = (250, 224, 140); trim = (250, 250, 244)
    if p <= 0: return im
    stake = (120, 80, 40); wood = (124, 82, 46)
    if p < 1:
        for (x, y) in [(X0, RY), (X1, RY), (X0, BY), (X1, BY)]:
            d.line([x, y-3, x, y], fill=A(stake)); d.point((x, y-3), fill=A(sh(stake, 1.4)))
    if p < 0.2:
        for x in range(X0, X1, 3): d.point((x, RY-1), fill=(250, 250, 250, 220)); d.point((x, BY-1), fill=(250, 250, 250, 220))
        for y in range(RY, BY, 3): d.point((X0, y), fill=(250, 250, 250, 220)); d.point((X1, y), fill=(250, 250, 250, 220))
        n = int(p/0.2*(X1-X0-2))
        if n > 0:
            d.rectangle([X0+1, RY+1, X0+n, BY-1], fill=(150, 150, 156, 255))
            for y in range(RY+3, BY-1, 4):
                for x in range(X0+2+(y % 8)//2, X0+n, 6): d.point((x, y), fill=(128, 128, 134, 255))
        return im
    # fundação + piso
    d.rectangle([X0, RY, X1, BY], fill=(140, 140, 146, 255))
    d.rectangle([X0+2, RY+2, X1-2, WY-1], fill=(176, 130, 84, 255))
    for y in range(RY+3, WY, 3): d.line([X0+2, y, X1-2, y], fill=(150, 108, 68, 255))
    if p < 0.62:
        f = clamp((p-0.3)/0.32)
        for x in (X0+1, X1-1, TX0, TX1, 18, 62):
            d.rectangle([x-1, RY, x, BY], fill=A(wood)); d.line([x-1, RY, x-1, BY], fill=A(sh(wood, 1.3)))
        d.rectangle([X0, RY, X1, RY+1], fill=A(wood))
        hh = int(round(f*(BY-WY+1)))
        if hh > 0:
            d.rectangle([X0+1, BY+1-hh, X1-1, BY], fill=A(wc))
            for y in range(BY+1-hh, BY+1, 2): d.line([X0+1, y, X1-1, y], fill=A(sh(wc, 0.93)))
        return im
    # ---- paredes prontas ----
    d.rectangle([X0+1, WY, X1-1, BY], fill=A(wc))
    for y in range(WY+2, BY, 3): d.line([X0+1, y, X1-1, y], fill=A(sh(wc, 0.95)))
    d.rectangle([X0+1, BY-2, X1-1, BY], fill=(214, 120, 70, 255))          # rodapé
    d.line([X0+1, BY, X1-1, BY], fill=(160, 84, 50, 255))
    d.line([X0, WY, X0, BY], fill=A(OUT)); d.line([X1, WY, X1, BY], fill=A(OUT))
    # porta dupla verde
    cx = (X0+X1)//2
    d.rectangle([cx-6, WY+2, cx+6, BY], fill=A(trim))
    d.rectangle([cx-5, WY+3, cx+5, BY], fill=(40, 132, 70, 255))
    d.line([cx, WY+3, cx, BY], fill=(24, 90, 46, 255)); d.line([cx-5, WY+3, cx+5, WY+3], fill=(70, 170, 100, 255))
    d.point((cx-2, WY+8), fill=(250, 210, 90, 255)); d.point((cx+2, WY+8), fill=(250, 210, 90, 255))
    for k in range(2): d.line([cx-7-k, BY+1+k, cx+7+k, BY+1+k], fill=(180-k*20, 178-k*20, 170-k*20, 255))
    # janelas (4)
    g = LITW[0] if lit else (110, 166, 222)
    for wx in (X0+5, X0+19, X1-25, X1-11):
        d.rectangle([wx-1, WY+3, wx+7, WY+10], fill=A(trim))
        d.rectangle([wx, WY+4, wx+6, WY+9], fill=A(g))
        if lit: d.rectangle([wx+1, WY+5, wx+3, WY+6], fill=A(LITW[1]))
        else: d.line([wx, WY+4, wx+2, WY+4], fill=(214, 236, 252, 255)); d.point((wx, WY+5), fill=(214, 236, 252, 255))
        d.line([wx+3, WY+4, wx+3, WY+9], fill=A(trim)); d.line([wx, WY+6, wx+6, WY+6], fill=A(trim))
        d.rectangle([wx-1, WY+11, wx+7, WY+11], fill=(150, 150, 150, 255))
    # ---- telhado ----
    f = clamp((p-0.62)/0.23)
    for x in range(X0, X1+1, 4): d.line([x, RY, x, WY-1], fill=A(wood))
    total = len(range(WY-1, RY-1, -3))
    done = total if f >= 1 else int(math.ceil(f*total))
    roof_tiles(d, X0-1, RY, X1+1, WY-1, ramp, done)
    if f >= 1:
        d.rectangle([X0-1, RY-1, X1+1, RY+1], fill=A(ramp[3])); d.line([X0-1, RY+2, X1+1, RY+2], fill=A(ramp[2]))
        d.line([X0-2, RY-1, X0-2, WY-1], fill=A(OUT)); d.line([X1+2, RY-1, X1+2, WY-1], fill=A(OUT))
        d.line([X0-2, RY-2, X1+2, RY-2], fill=A(OUT)); d.line([X0-2, WY-1, X1+2, WY-1], fill=A(ramp[0]))
        d.line([X0-1, WY-2, X1+1, WY-2], fill=A(ramp[1]))
    # ---- torre do sino ----
    if p >= 0.85:
        d.rectangle([TX0-1, 0, TX1+1, WY-1], fill=A(OUT))
        d.rectangle([TX0, 1, TX1, WY-2], fill=A(trim)); d.line([TX1-2, 1, TX1-2, WY-2], fill=(220, 214, 204, 255))
        d.rectangle([TX0, 1, TX1, 4], fill=A(ramp[2])); d.line([TX0, 1, TX1, 1], fill=A(ramp[3]))
        bx = (TX0+TX1)//2
        d.rectangle([bx-4, 7, bx+4, 15], fill=(56, 48, 46, 255)); d.ellipse([bx-4, 5, bx+4, 10], fill=(56, 48, 46, 255))
        d.line([bx-3, 7, bx+3, 7], fill=(90, 80, 74, 255))
        o = bell
        d.polygon([(bx-3+o, 14), (bx+3+o, 14), (bx+2+o//2, 9), (bx-2+o//2, 9)], fill=(214, 168, 56, 255))
        d.ellipse([bx-2+o//2, 8, bx+2+o//2, 11], fill=(214, 168, 56, 255))
        d.point((bx-1+o//2, 10), fill=(250, 220, 120, 255)); d.point((bx+o, 15), fill=(150, 110, 30, 255))
        # placa ESCOLA
        d.rectangle([TX0-13, 17, TX1+13, 26], fill=A(OUT)); d.rectangle([TX0-12, 18, TX1+12, 25], fill=(250, 250, 244, 255))
        draw_text(d, "ESCOLA", (TX0+TX1)//2+1, 19, 1, (40, 70, 160, 255), outline=None)
    # ---- mastro com bandeira ----
    if p >= 0.93:
        px_ = 82
        d.line([px_, 2, px_, BY+2], fill=(150, 150, 160, 255)); d.line([px_+1, 2, px_+1, BY+2], fill=(100, 100, 110, 255))
        d.rectangle([px_-1, BY+1, px_+2, BY+3], fill=(120, 120, 126, 255))
        h = clamp((p-0.93)/0.07)
        fy = int(BY-4-(BY-8)*h)
        wav = [0, 1, 0, -1][flag % 4]
        for i_ in range(8):
            yo = fy+(1 if (i_+flag) % 4 in (1, 2) else 0)
            for j in range(6):
                d.point((px_-1-i_, yo+j), fill=(30, 150, 70, 255))
        d.polygon([(px_-5, fy+1), (px_-2, fy+3), (px_-5, fy+5), (px_-8, fy+3)], fill=(250, 214, 50, 255))
        d.point((px_-5, fy+3), fill=(40, 70, 160, 255)); d.point((px_-4, fy+3), fill=(40, 70, 160, 255))
    if p >= 1:
        for y in range(RY, BY+3): im.putpixel((X1+3, y), (0, 0, 0, 70)); im.putpixel((X1+4, y), (0, 0, 0, 40))
    return im
