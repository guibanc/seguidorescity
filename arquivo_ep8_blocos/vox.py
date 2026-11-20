# Ep. 8: Pindamonhangaba EM BLOCOS (tudo quadrado, faces lisas, sem aresta).
# Mesmo mapa lógico e mesma projeção do iso.py; aqui só muda o DESENHO.
#   iso.VOX = True  -> objetos(), chão e árvores saem em blocos (B = 1,5 unidade lógica)
#   vchar(look, dir, quadro) -> morador quadradinho (sprite pronto pro render_view)
import math, random, numpy as np
from PIL import Image, ImageDraw
import iso
import scene as SC
from scene import lot
from world16 import SKIN16, HAIR16, SHIRT16, PANTS16, SHOES16

B = 1.5

def sh(c, f): return tuple(max(0, min(255, int(round(v*f)))) for v in c[:3])
def jit(c, i, j, k, a=0.045):
    h = ((i*73856093) ^ (j*19349663) ^ (k*83492791)) & 0xffff
    return sh(c, 1+a*((h/65535.0)*2-1))

class Vox:
    """grade de blocos -> desenho isométrico (só as faces visíveis, sem contorno)"""
    def __init__(self): self.c = {}
    def put(self, i, j, k, col): self.c[(i, j, k)] = col
    def fill(self, xa, xb, ya, yb, za, zb, col):
        """caixa em unidades lógicas (snap pra grade); col = cor ou função(i,j,k)"""
        I0, I1 = int(round(xa/B)), int(round(xb/B)); J0, J1 = int(round(ya/B)), int(round(yb/B))
        K0, K1 = int(round(za/B)), int(round(zb/B))
        for i in range(I0, max(I0+1, I1)):
            for j in range(J0, max(J0+1, J1)):
                for k in range(K0, max(K0+1, K1)):
                    c = col(i, j, k) if callable(col) else col
                    if c is not None: self.c[(i, j, k)] = c
    def draw(self, jitter=True, n=3):
        """faces com textura de pixel (n x n), sem contorno"""
        P = iso.P; d = iso.d; cs = self.c
        def face(c, o, ua, va, i, j, k, f):
            # o = canto, ua/va = vetores das bordas; subdivide em n x n com variação de tom
            for a in range(n):
                for b in range(n):
                    h = ((i*73856093) ^ (j*19349663) ^ (k*83492791) ^ (a*2654435761) ^ (b*40503) ^ (f*97)) & 0xff
                    m = 1+0.07*((h/255.0)*2-1)
                    if h < 26: m -= 0.06
                    cc = sh(c, m)
                    p0 = (o[0]+ua[0]*a/n+va[0]*b/n, o[1]+ua[1]*a/n+va[1]*b/n, o[2]+ua[2]*a/n+va[2]*b/n)
                    pts = [p0, (p0[0]+ua[0]/n, p0[1]+ua[1]/n, p0[2]+ua[2]/n),
                           (p0[0]+(ua[0]+va[0])/n, p0[1]+(ua[1]+va[1])/n, p0[2]+(ua[2]+va[2])/n),
                           (p0[0]+va[0]/n, p0[1]+va[1]/n, p0[2]+va[2]/n)]
                    q = [P(*p) for p in pts]
                    d.polygon(q, fill=cc, outline=cc)
        for (i, j, k) in sorted(cs, key=lambda q: (q[0]+q[1]+q[2], q[2])):
            col = cs[(i, j, k)]
            if col is None: continue
            c = jit(col, i, j, k) if jitter else col
            x0, y0, z0 = i*B, j*B, k*B; x1, y1, z1 = x0+B, y0+B, z0+B
            ao = 0.9 if (i, j, k+1) in cs or (i-1, j, k+1) in cs else 1.0
            if (i, j+1, k) not in cs:
                face(sh(c, .84*ao), (x0, y1, z1), (B, 0, 0), (0, 0, -B), i, j, k, 1)
            if (i+1, j, k) not in cs:
                face(sh(c, .68*ao), (x1, y0, z1), (0, B, 0), (0, 0, -B), i, j, k, 2)
            if (i, j, k+1) not in cs:
                face(c, (x0, y0, z1), (B, 0, 0), (0, B, 0), i, j, k, 3)

def gi(v): return int(round(v/B))
def gable(v, I0, I1, J0, J1, H, c1, c2, along='x', ov=1):
    """telhado em degraus, cumeeira ao longo de x (ou y), com as pontas fechadas"""
    if along == 'x':
        a, b, lvl = J0-ov, J1-1+ov, 0
        while a <= b:
            c = c1 if lvl % 2 == 0 else c2
            for i in range(I0-ov, I1+ov):
                for j in range(a, b+1):
                    if j in (a, b) or i in (I0-ov, I1+ov-1): v.put(i, j, H+lvl, c if j in (a, b) else sh(c1, .96))
            a += 1; b -= 1; lvl += 1
    else:
        a, b, lvl = I0-ov, I1-1+ov, 0
        while a <= b:
            c = c1 if lvl % 2 == 0 else c2
            for j in range(J0-ov, J1+ov):
                for i in range(a, b+1):
                    if i in (a, b) or j in (J0-ov, J1+ov-1): v.put(i, j, H+lvl, c if i in (a, b) else sh(c1, .96))
            a += 1; b -= 1; lvl += 1
    return lvl

# ---------------- construções ----------------
WALLS = [(236, 214, 170), (226, 196, 150), (240, 232, 214), (214, 176, 128)]
TABUA = (190, 140, 88)
ROOFS = [(200, 60, 50), (60, 110, 190), (60, 150, 80), (230, 140, 40), (150, 80, 180), (120, 80, 50)]
GLASS = (150, 206, 236); DOOR = (110, 70, 40); WHITE = (246, 246, 242); STONE = (150, 150, 158)

def casa_vox(v, x0, x1, y0, y1, h, wall, roof, front=True, p=1.0, chamine=True, toldo=None):
    I0, I1, J0, J1 = gi(x0), gi(x1), gi(y0), gi(y1)
    H = int(h)
    if p <= 0: return
    if p < 0.3:                                      # fundação
        for i in range(I0, I1):
            for j in range(J0, J1): v.put(i, j, 0, (150, 150, 156))
        return
    hw = H if p >= 0.7 else max(1, int((p-0.3)/0.4*H))
    for i in range(I0, I1):
        for j in range(J0, J1):
            for k in range(hw):
                if I0 < i < I1-1 and J0 < j < J1-1: continue
                c = wall
                if k == 0: c = sh(wall, .8)
                if j == J1-1:      # parede da frente (sul)
                    if front and i in (I0+(I1-I0)//2-1, I0+(I1-I0)//2) and k < 3: c = DOOR
                    elif k in (2, 3) and (i-I0) % 4 in (1, 2) and not (front and abs(i-(I0+(I1-I0)//2)) < 3): c = GLASS
                if i == I1-1 and k in (2, 3) and (j-J0) % 4 in (1, 2): c = GLASS
                v.put(i, j, k, c)
    if p < 0.7:
        for i in range(I0, I1, 3):
            for k in range(H+1): v.put(i, J1, k, (124, 82, 46))           # andaime
        return
    lvl = gable(v, I0, I1, J0, J1, H, roof, sh(roof, .9))
    if chamine:
        ci, cj = I1-3, J0+1
        for k in range(H, H+lvl+1): v.put(ci, cj, k, (168, 82, 62))
    if toldo:
        for i in range(I0, I1): v.put(i, J1, 4, toldo[(i-I0) % 2]); v.put(i, J1+1, 4, toldo[(i-I0) % 2])

def house(l, var, p=1.0, venda=False):
    lx, ly = lot(*l)
    v = Vox()
    wall = TABUA if var % 3 == 0 else WALLS[(var//2) % 4]
    casa_vox(v, lx+1.5, lx+19.5, ly+4.5, ly+19.5, 7, wall, ROOFS[var % 6], front=(l[2] == 'a'), p=p,
             toldo=((214, 50, 50), (250, 250, 246)) if venda else None)
    if p >= 1 and var % 3 == 1 and l[2] == 'a':                         # arbustos na frente
        J = gi(ly+19.5)
        for i in (gi(lx+1.5), gi(lx+1.5)+1, gi(lx+19.5)-2, gi(lx+19.5)-1): v.put(i, J, 0, (60, 140, 54))
    v.draw()

def mercadinho(l=None, aw=(40, 150, 80), sign=(214, 50, 50)):
    lx, ly = lot(*(l or SC.MERCADO)); v = Vox()
    I0, I1, J0, J1 = gi(lx+1.5), gi(lx+19.5), gi(ly+4.5), gi(ly+19.5)
    for i in range(I0, I1):
        for j in range(J0, J1):
            for k in range(7):
                if I0 < i < I1-1 and J0 < j < J1-1 and k < 6: continue
                c = WHITE
                if j == J1-1 and 0 < k < 4 and I0 < i < I1-1: c = GLASS
                if k == 6: c = (200, 200, 206)
                v.put(i, j, k, c)
    for i in range(I0, I1): v.put(i, J1, 4, aw if (i-I0) % 2 == 0 else WHITE)
    for i in range(I0+3, I1-3): v.put(i, J1-1, 7, sign); v.put(i, J1-1, 8, sign)
    v.draw()
def mercado2(): mercadinho(SC.MERCADO2, (40, 110, 200), (40, 90, 190))

def escola():
    v = Vox()
    x0, x1, y0, y1 = 162.5, 203.5, 131, 146
    I0, I1, J0, J1 = gi(x0), gi(x1), gi(y0), gi(y1); H = 7
    for i in range(I0, I1):
        for j in range(J0, J1):
            for k in range(H):
                if I0 < i < I1-1 and J0 < j < J1-1: continue
                c = (252, 222, 128) if k else (214, 120, 70)
                if j == J1-1 and k in (2, 3, 4) and (i-I0) % 4 in (1, 2): c = GLASS
                if j == J1-1 and abs(i-(I0+I1)//2) < 2 and k < 4: c = (40, 132, 70)
                v.put(i, j, k, c)
    a, b, c_, e = I0-1, I1, J0-1, J1; lvl = 0
    while a <= b and c_ <= e:
        for i in range(a, b+1):
            for j in range(c_, e+1):
                if i in (a, b) or j in (c_, e): v.put(i, j, H+lvl, (230, 140, 40) if lvl % 2 == 0 else (210, 120, 34))
        a += 1; b -= 1; c_ += 1; e -= 1; lvl += 1
    ti, tj = (I0+I1)//2-1, J1-3                       # torre do sino
    for k in range(H+lvl, H+lvl+5):
        for i in (ti, ti+1, ti+2):
            for j in (tj, tj+1, tj+2):
                v.put(i, j, k, (214, 168, 56) if (k == H+lvl+2 and i == ti+1 and j == tj+2) else WHITE)
    for i in (ti, ti+1, ti+2):
        for j in (tj, tj+1, tj+2): v.put(i, j, H+lvl+5, (230, 140, 40))
    v.put(ti+1, tj+1, H+lvl+6, (230, 140, 40))
    v.draw()
    cx, cy = iso.P(x0+20.5, y1, 17)
    iso.d.rectangle([cx-20, cy-12, cx+20, cy-3], fill=(250, 250, 244))
    from font import draw_text
    draw_text(iso.d, "ESCOLA", cx+1, cy-10, 1, (40, 70, 160, 255), outline=None)

def church():
    v = Vox(); x0, x1, y0, y1 = 117, 146, 72, 100
    I0, I1, J0, J1 = gi(x0), gi(x1), gi(y0), gi(y1); H = 12
    for i in range(I0, I1):
        for j in range(J0, J1):
            for k in range(H):
                if I0 < i < I1-1 and J0 < j < J1-1: continue
                c = (244, 240, 232)
                if i == I1-1 and k in range(4, 9) and (j-J0) % 4 in (1, 2): c = (200, 120, 70)
                v.put(i, j, k, c)
    lvl = gable(v, I0, I1, J0, J1, H, (64, 76, 120), (52, 62, 100), along='y')
    ci = (I0+I1)//2-2; cj = J1-2                     # torre
    for k in range(H+lvl+8):
        for i in range(ci, ci+5):
            for j in range(cj, cj+4):
                c = (250, 248, 242)
                if j == cj+3 and i in (ci+1, ci+2, ci+3) and k < 4: c = (110, 60, 36)
                if j == cj+3 and i == ci+2 and k in (H+3, H+4): c = (60, 50, 50)
                v.put(i, j, k, c)
    top = H+lvl+8
    for k in range(top, top+3):
        w = 2-(k-top)
        for i in range(ci+2-w, ci+3+w):
            for j in range(cj+1-max(0, w-1), cj+3+max(0, w-1)): v.put(i, j, k, (64, 76, 120))
    for k in range(top+3, top+7): v.put(ci+2, cj+1, k, (240, 200, 60))
    v.put(ci+1, cj+1, top+5, (240, 200, 60)); v.put(ci+3, cj+1, top+5, (240, 200, 60))
    v.draw()

def prefeitura():
    v = Vox(); x0, x1, y0, y1 = 141, 181.5, 401, 416
    I0, I1, J0, J1 = gi(x0), gi(x1), gi(y0), gi(y1); H = 9
    for i in range(I0, I1):
        for j in range(J0, J1):
            for k in range(H):
                if I0 < i < I1-1 and J0 < j < J1-1: continue
                c = (248, 244, 234)
                if k in (0, H-1): c = (60, 92, 160)
                elif j == J1-1 and k in range(2, 7) and (i-I0) % 4 in (1, 2): c = GLASS
                v.put(i, j, k, c)
    a, b, c_, e, lvl = I0-1, I1, J0-1, J1, 0
    while a <= b and c_ <= e and lvl < 6:
        for i in range(a, b+1):
            for j in range(c_, e+1):
                if i in (a, b) or j in (c_, e): v.put(i, j, H+lvl, (78, 88, 112) if lvl % 2 else (104, 116, 142))
        a += 1; b -= 1; c_ += 1; e -= 1; lvl += 1
    pm = (I0+I1)//2                                       # pórtico com colunas
    for i in (pm-5, pm-3, pm+2, pm+4):
        for k in range(H+1): v.put(i, J1+2, k, WHITE)
    for i in range(pm-6, pm+6):
        for j in range(J1, J1+3): v.put(i, j, H+1, (236, 232, 222))
    for lv in range(4):
        for i in range(pm-5+lv, pm+5-lv): v.put(i, J1+2, H+2+lv, WHITE)
    for i in (pm-1, pm):
        for k in range(4): v.put(i, J1-1, k, (120, 72, 40))
    for (fi, sg, cols) in ((I0-2, 1, [(30, 150, 70), (250, 214, 50)]), (I1+1, -1, [(40, 90, 170), (250, 250, 250), (200, 40, 50)])):
        for k in range(16): v.put(fi, J1+3, k, (170, 170, 180))
        for di in range(1, 4):
            for n_, c in enumerate(cols): v.put(fi+sg*di, J1+3, 15-n_, c)
    v.draw()
    from font import draw_text
    cx, cy = iso.P((x0+x1)/2, y1+4.5, 23)
    iso.d.rectangle([cx-32, cy-10, cx+32, cy-1], fill=(250, 250, 244))
    draw_text(iso.d, "PREFEITURA", cx+1, cy-8, 1, (40, 60, 130, 255), outline=None)

def posto():
    lx, ly = lot(*SC.POSTO[0]); v = Vox()
    I0, I1, J0, J1 = gi(lx+1.5), gi(lx+41.5), gi(ly+4.5), gi(ly+19.5)
    for i in range(I0, I1):
        for j in range(J0, J1):
            for k in range(8):
                if I0 < i < I1-1 and J0 < j < J1-1 and k < 7: continue
                c = WHITE
                if k == 4: c = (40, 160, 90)
                if j == J1-1 and k in (1, 2, 3) and abs(i-(I0+I1)//2) < 3: c = GLASS
                elif j == J1-1 and k in (5, 6) and (i-I0) % 4 in (1, 2): c = GLASS
                if k == 7: c = (196, 200, 204)
                v.put(i, j, k, c)
    ci, cj = (I0+I1)//2, (J0+J1)//2
    for d_ in range(-2, 3): v.put(ci+d_, cj, 8, (40, 160, 90)); v.put(ci, cj+d_, 8, (40, 160, 90))
    v.draw()

def tree(x, y, r):
    v = Vox(); i, j = gi(x), gi(y); rr = random.Random(i*31+j*17)
    hgt = 3+(r > 7)
    for k in range(hgt): v.put(i, j, k, (120, 84, 50))
    rad = 1 if r < 8 else 2
    for k in range(hgt, hgt+3):
        rk = rad if k < hgt+2 else rad-1
        for a in range(-rk, rk+1):
            for b in range(-rk, rk+1):
                if abs(a) == rk and abs(b) == rk and rr.random() < 0.6: continue
                v.put(i+a, j+b, k, (60, 140, 54) if rr.random() < .6 else (72, 156, 60))
    v.put(i, j, hgt+3, (78, 162, 64))
    if rr.random() < 0.3:
        v.put(i+rad, j, hgt+1, (220, 50, 50))
    v.draw()

def fonte():
    v = Vox(); ci, cj = gi(132), gi(245)
    for a in range(-3, 4):
        for b in range(-3, 4):
            if max(abs(a), abs(b)) == 3: v.put(ci+a, cj+b, 0, (176, 172, 166))
            else: v.put(ci+a, cj+b, 0, (80, 140, 214))
    for k in (1, 2): v.put(ci, cj, k, (190, 186, 180))
    v.put(ci, cj, 3, (120, 180, 230))
    v.draw()

def stakes(l):
    lx, ly = lot(*l); v = Vox()
    for (x, y) in ((lx+2, ly+5), (lx+18, ly+5), (lx+2, ly+19), (lx+18, ly+19)):
        v.put(gi(x), gi(y), 0, (130, 88, 46)); v.put(gi(x), gi(y), 1, (150, 104, 56))
    v.draw()

def portal():
    """pórtico PINDAMONHANGABA em blocos (texto pintado depois, em alta)"""
    v = Vox(); I0, I1, J = gi(SC.PLACA_X0), gi(SC.PLACA_X1), gi(SC.PLACA_Y)-1
    for i in (I0, I1):
        for k in range(26): v.put(i, J, k, (120, 80, 44))
    for i in range(I0, I1+1):
        for k in range(17, 26): v.put(i, J, k, (176, 122, 70) if k not in (17, 25) else (110, 72, 40))
    v.draw()
PORTAL_Y = (gi(466)-1)*B+B           # face da frente do letreiro (y)

def posters():
    v = Vox(); cols = [(214, 50, 50), (40, 90, 190), (40, 150, 80), (240, 180, 40), (150, 80, 180), (230, 120, 40)]
    for n_, x in enumerate(range(142, 181, 4)):
        i = gi(x); j = gi(416)+1
        for k in range(3, 6): v.put(i, j, k, cols[n_ % 6])
    ui, uj = gi(158), gi(424)
    for k in range(3): v.put(ui, uj, k, (250, 250, 250))
    v.put(ui, uj, 3, (40, 150, 80))
    v.draw()

# ---------------- campo de futebol (marco 700) ----------------
def campo_rect():
    lx, ly = lot(*SC.CAMPO[0]); return (lx+3, ly+3, lx+87, ly+43)      # gramado (x0,y0,x1,y1)
def traves(lado):
    x0, y0, x1, y1 = campo_rect(); v = Vox(); jm = gi((y0+y1)/2)
    i = gi(x0)-1 if lado < 0 else gi(x1)
    for j in (jm-3, jm+3):
        for k in range(5): v.put(i, j, k, WHITE)
    for j in range(jm-3, jm+4): v.put(i, j, 5, WHITE)
    ib = i-1 if lado < 0 else i+1
    for j in range(jm-3, jm+4):
        for k in range(5):
            if (j+k) % 2 == 0: v.put(ib, j, k, (226, 226, 230))
    v.draw()
def cerca():
    x0, y0, x1, y1 = campo_rect(); v = Vox()
    I0, I1, J0, J1 = gi(x0)-1, gi(x1)+1, gi(y0)-1, gi(y1)+1
    for i in range(I0, I1+1):
        for j in (J0, J1):
            v.put(i, j, 0, (150, 104, 56))
            if i % 3 == 0: v.put(i, j, 1, (130, 88, 46))
    for j in range(J0, J1+1):
        for i in (I0, I1):
            v.put(i, j, 0, (150, 104, 56))
            if j % 3 == 0: v.put(i, j, 1, (130, 88, 46))
    ci = (I0+I1)//2                                  # plaquinha 700
    for k in range(4): v.put(ci, J1, k, (110, 72, 40))
    for a in range(-2, 3):
        for k in (4, 5): v.put(ci+a, J1, k, (250, 214, 60))
    v.draw()
def arquibancada():
    x0, y0, x1, y1 = campo_rect(); v = Vox()
    for n_, (dj, hh) in enumerate(((1, 1), (2, 2), (3, 3), (4, 4))):
        j = gi(y1)+dj
        for i in range(gi(x0)+2, gi(x1)-2):
            for k in range(hh): v.put(i, j, k, (164, 164, 170) if (i+k) % 2 else (150, 150, 158))
    v.draw()
def campo_cor(lx, ly, p):
    """cor do gramado pra (lx, ly) (arrays). p: 0..1 progresso da obra. Devolve (máscara, cores)"""
    x0, y0, x1, y1 = campo_rect()
    m = (lx >= x0-1.5) & (lx < x1+1.5) & (ly >= y0-1.5) & (ly < y1+1.5)
    if not m.any() or p <= 0: return m & False, None
    gx = lx[m]; gy = ly[m]
    rev = np.clip((p-0.0)/0.3, 0, 1)                                   # grama nova (de x0 até x1)
    out = np.zeros((m.sum(), 3), np.float32)
    has = gx < x0+(x1-x0)*rev
    est = (np.floor((gx-x0)/6) % 2 == 0)
    out[:] = np.where(est[:, None], np.array([86, 170, 70]), np.array([72, 150, 58]))
    out[~has] = (130, 96, 60)
    if p >= 0.35:                                                       # linhas
        lf = np.clip((p-0.35)/0.25, 0, 1)
        xm, ym = (x0+x1)/2, (y0+y1)/2
        lin = (np.abs(gx-x0) < 1.0) | (np.abs(gx-x1) < 1.0) | (np.abs(gy-y0) < 1.0) | (np.abs(gy-y1) < 1.0) | (np.abs(gx-xm) < 0.8)
        r = np.hypot(gx-xm, gy-ym); lin |= (np.abs(r-8) < 0.8)
        for xs in (x0, x1):                                             # áreas
            lin |= (np.abs(gx-xs) < 11) & ((np.abs(gy-(ym-11)) < 0.8) | (np.abs(gy-(ym+11)) < 0.8))
            lin |= (np.abs(np.abs(gx-xs)-11) < 0.8) & (np.abs(gy-ym) < 11)
        lin &= ((gx-x0)/(x1-x0) < lf)
        out[lin] = (240, 240, 236)
    return m, out

# ---------------- fazenda (fora do mapa, lado oeste) ----------------
FARM = dict(celeiro=(-92, 318), silo=(-70, 316), trator=(-60, 352), plantio=(-150, 360, -50, 430), placa=(-40, 350))
def celeiro():
    v = Vox(); x, y = FARM['celeiro']
    I0, I1, J0, J1 = gi(x), gi(x+24), gi(y), gi(y+18); H = 8
    for i in range(I0, I1):
        for j in range(J0, J1):
            for k in range(H):
                if I0 < i < I1-1 and J0 < j < J1-1: continue
                c = (176, 44, 40)
                if (i in (I0, I1-1)) or k in (0, H-1): c = WHITE
                if j == J1-1 and abs(i-(I0+I1)//2+0.5) < 3 and k < 6: c = WHITE if (i+k) % 3 == 0 else (150, 36, 32)
                v.put(i, j, k, c)
    gable(v, I0, I1, J0, J1, H, (120, 60, 46), (96, 50, 40))
    v.draw()
def silo():
    v = Vox(); x, y = FARM['silo']; ci, cj = gi(x), gi(y)
    for k in range(16):
        for a in range(-2, 3):
            for b in range(-2, 3):
                if abs(a)+abs(b) > 3: continue
                v.put(ci+a, cj+b, k, (196, 200, 206) if k % 4 else (170, 174, 180))
    for a in range(-1, 2):
        for b in range(-1, 2): v.put(ci+a, cj+b, 16, (150, 60, 50))
    v.draw()
def trator():
    v = Vox(); x, y = FARM['trator']; i, j = gi(x), gi(y)
    for a in range(5):
        for b in range(3):
            v.put(i+a, j+b, 1, (40, 150, 70));
            if a < 2: v.put(i+a, j+b, 2, (40, 150, 70)); v.put(i+a, j+b, 3, GLASS if b == 2 else (40, 150, 70))
    v.put(i, j, 4, (40, 150, 70)); v.put(i+1, j, 4, (40, 150, 70)); v.put(i, j+2, 4, (40, 150, 70)); v.put(i+1, j+2, 4, (40, 150, 70))
    for (a, b) in ((0, -1), (0, 3), (4, -1), (4, 3)):
        v.put(i+a, j+b, 0, (30, 30, 34)); v.put(i+a, j+b, 1, (30, 30, 34))
    v.put(i+4, j+1, 2, (60, 60, 64)); v.put(i+4, j+1, 3, (60, 60, 64))
    v.draw()
def plantio_linha(jrow):
    """uma fileira da plantação (constante em y)"""
    x0, y0, x1, y1 = FARM['plantio']; v = Vox()
    milho = jrow % 4 < 2
    for i in range(gi(x0), gi(x1)):
        if milho:
            v.put(i, jrow, 0, (70, 150, 60)); v.put(i, jrow, 1, (86, 168, 70))
            if i % 3 == 0: v.put(i, jrow, 2, (240, 200, 70))
        else: v.put(i, jrow, 0, (230, 198, 92) if i % 2 else (214, 182, 80))
    v.draw()
def placa_fazenda():
    v = Vox(); x, y = FARM['placa']; i, j = gi(x), gi(y)
    for k in range(5): v.put(i, j, k, (110, 72, 40)); v.put(i+5, j, k, (110, 72, 40))
    for a in range(-1, 7):
        for k in range(5, 9): v.put(i+a, j, k, (214, 174, 116))
    v.draw()
    from font import draw_text
    cx, cy = iso.P(x+4, (j+1)*B, 10.5)
    draw_text(iso.d, "CONTRATA-SE!", cx, cy-5, 1, (120, 40, 20, 255), outline=None)

# ---------------- montagem dos objetos ----------------
def objetos(t, C):
    spr = iso.spr; out = []
    lot_box = iso.lot_box
    for i, l in enumerate(SC.house_lots):
        p = SC.house_p(i, C); lx_, ly_ = lot(*l)
        if p <= 0:
            if l[1] >= SC.ROADD and l not in SC.CAMPO: out.append((lx_+ly_+20, spr(('vst', l), lambda l=l: stakes(l), lot_box(l), 10)))
            continue
        pk = 1.0 if p >= 1 else round(p*20)/20
        out.append((lx_+ly_+40, spr(('vh', i, pk), lambda l=l, i=i, pk=pk: house(l, SC.house_var[i], pk), lot_box(l), 46)))
    lx_, ly_ = lot(*SC.VENDA); out.append((lx_+ly_+40, spr('vvenda', lambda: house(SC.VENDA, 5, 1, True), lot_box(SC.VENDA), 46)))
    lx_, ly_ = lot(*SC.MERCADO); out.append((lx_+ly_+40, spr('vmerc', mercadinho, lot_box(SC.MERCADO), 40)))
    lx_, ly_ = lot(*SC.MERCADO2); out.append((lx_+ly_+40, spr('vmerc2', mercado2, lot_box(SC.MERCADO2), 40)))
    lx_, ly_ = lot(*SC.POSTO[0]); out.append((lx_+ly_+45, spr('vposto', posto, (lx_-2, ly_, lx_+46, ly_+30), 40)))
    out.append((246, spr('vigreja', church, (110, 60, 150, 108), 110)))
    out.append((349, spr('vescola', escola, (158, 126, 210, 150), 70)))
    out.append((181+420, spr('vpref', prefeitura, (130, 396, 192, 430), 70)))
    out.append((181+427, spr('vposters', posters, (138, 410, 186, 430), 20)))
    for k, tr in enumerate(SC.TREES6): out.append((tr['x']+tr['y'], spr(('vtr', k), lambda tr=tr: tree(tr['x'], tr['y'], tr['r']+2), (tr['x']-8, tr['y']-8, tr['x']+8, tr['y']+8), 40)))
    out.append((153+231, spr('varvp', lambda: tree(153, 231, 8), (145, 223, 161, 239), 40)))
    out.append((132+245, spr('vfonte', fonte, (122, 237, 142, 253), 12)))
    out.append((SC.PLACA_X1+SC.PLACA_Y, spr('vportal', portal, (SC.PLACA_X0-3, SC.PLACA_Y-6, SC.PLACA_X1+3, SC.PLACA_Y+3), 50)))
    # campo
    p = SC.campo_p(t); x0, y0, x1, y1 = campo_rect()
    if p <= 0.02:
        out.append((x0+y1, spr('vcerca', cerca, (x0-3, y0-3, x1+3, y1+3), 12)))
    if p >= 0.62:
        out.append((x0+(y0+y1)/2, spr('vtrave0', lambda: traves(-1), (x0-6, y0, x0+2, y1), 14)))
        out.append((x1+(y0+y1)/2+2, spr('vtrave1', lambda: traves(1), (x1-2, y0, x1+6, y1), 14)))
    if p >= 0.85:
        out.append((x0+y1+10, spr('varq', arquibancada, (x0, y1, x1, y1+8), 12)))
    # fazenda
    fx, fy = FARM['celeiro']; out.append((fx+fy+40, spr('vceleiro', celeiro, (fx-2, fy-2, fx+26, fy+20), 40)))
    fx, fy = FARM['silo']; out.append((fx+fy, spr('vsilo', silo, (fx-5, fy-5, fx+5, fy+5), 30)))
    fx, fy = FARM['trator']; out.append((fx+fy+4, spr('vtrator', trator, (fx-2, fy-3, fx+9, fy+7), 12)))
    fx, fy = FARM['placa']; out.append((fx+fy, spr('vplacaf', placa_fazenda, (fx-3, fy-2, fx+12, fy+2), 20)))
    x0f, y0f, x1f, y1f = FARM['plantio']
    for j in range(gi(y0f), gi(y1f)):
        if j % 2: continue
        out.append(((x0f+x1f)/2+j*B, spr(('vpl', j), lambda j=j: plantio_linha(j), (x0f, j*B-1, x1f, j*B+2), 8)))
    return out

# ---------------- chão em blocos ----------------
def terreno_vox(lx, ly, base_fn):
    I = np.floor(lx/B); J = np.floor(ly/B)
    qx = (I+0.5)*B; qy = (J+0.5)*B
    c = base_fn(qx, qy).astype(np.float32)
    h = ((I.astype(np.int64)*73856093) ^ (J.astype(np.int64)*19349663)) & 0xffff
    c *= (0.955+0.09*(h/65535.0))[:, :, None]
    su = np.floor((lx/B-I)*3).astype(np.int64); sv = np.floor((ly/B-J)*3).astype(np.int64)
    h2 = ((I.astype(np.int64)*2654435761) ^ (J.astype(np.int64)*40503) ^ (su*97) ^ (sv*31337)) & 0xff
    tex = 1+0.075*((h2/255.0)*2-1)-0.07*(h2 < 30)
    c *= tex[:, :, None]
    m, cc = campo_cor(qx, qy, SC.campo_p(SC.T_ATUAL[0]))
    if cc is not None: c[m] = cc*(0.97+0.06*(h[m]/65535.0))[:, None]*(1+0.04*((h2[m]/255.0)*2-1))[:, None]
    return np.clip(c, 0, 255).astype(np.uint8)

# ---------------- moradores em bloco ----------------
def _boxdraw(d, P, parts):
    """parts: (x,y,z,dx,dy,dz,cor) em unidades lógicas, ordenadas por profundidade"""
    for (x, y, z, dx, dy, dz, c, *extra) in sorted(parts, key=lambda q: (q[0]+q[1]+(q[3]+q[4])/2, q[2])):
        x1, y1, z1 = x+dx, y+dy, z+dz
        f = sh(c, .84); d.polygon([P(x, y1, z1), P(x1, y1, z1), P(x1, y1, z), P(x, y1, z)], fill=f, outline=f)
        f = sh(c, .68); d.polygon([P(x1, y, z1), P(x1, y1, z1), P(x1, y1, z), P(x1, y, z)], fill=f, outline=f)
        d.polygon([P(x, y, z1), P(x1, y, z1), P(x1, y1, z1), P(x, y1, z1)], fill=c, outline=c)
        for e in extra: e(d, P, x, y, z, x1, y1, z1)

_VC = {}
def vchar(look, dr='down', fr=0, uniforme=None, carry=None, kr=2, tool=None, cache=None):
    key = (cache, dr, fr, uniforme, carry, tool, kr) if cache is not None else None
    if key is not None and key in _VC: return _VC[key]
    q = 0.72*kr
    Wc, Hc = int(36*q)+4, int(32*q)+4; fx, fy = Wc//2, Hc-int(5*q)
    im = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def P(x, y, z): return (fx+(x-y)*2*q, fy+(x+y)*q-z*q)
    skin = SKIN16[look['pele']]; hair = HAIR16[look['cor_cabelo']]
    shirt = SHIRT16[look['camisa']]; shirt2 = SHIRT16[look['camisa2']]
    bot = PANTS16[look['cor_baixo']]; shoe = SHOES16[look['sapato']]
    hat = look.get('chapeu'); hatc = SHIRT16[look.get('cor_chapeu', 0) or 0]
    est = look.get('estampa', 'lisa'); baixo = look.get('baixo', 'calca'); hs = look.get('cabelo', 'curto')
    aces = look.get('acessorio'); acc = SHIRT16[look.get('cor_acessorio', 0) or 0]
    if uniforme == 'pedreiro': shirt = (240, 128, 30); shirt2 = (250, 220, 60); hat = 'capacete'; hatc = (250, 206, 40); est = 'lisa'
    if uniforme == 'fazendeiro': shirt = (200, 50, 50); shirt2 = (200, 50, 50); bot = (50, 90, 170); baixo = 'macacao'; hat = 'palha'; est = 'xadrez'
    if uniforme == 'jogador': shirt = (40, 150, 70); shirt2 = (250, 214, 50); est = 'time'; bot = (250, 250, 250); baixo = 'bermuda'; hat = None if hat in ('palha', 'coroa') else hat
    if uniforme == 'rival': shirt = (214, 50, 50); shirt2 = (250, 250, 250); est = 'time'; bot = (30, 30, 40); baixo = 'bermuda'
    if uniforme == 'goleiro': shirt = (250, 150, 30); shirt2 = (30, 30, 40); est = 'lisa'; bot = (30, 30, 40); baixo = 'bermuda'
    face = {'down': 's', 'left': 's', 'right': 'e', 'up': None}[dr]
    sw = [0, 1.2, 0, -1.2][fr % 4]
    ax = (1, 0) if face == 'e' else (0, 1)          # eixo de "pra frente"
    def mv(off): return (ax[0]*off, ax[1]*off)
    parts = []
    # pernas
    if face == 'e':
        L = [(-1.5, -2.0, sw), (-1.5, 0.5, -sw)]
    else:
        L = [(-2.0, -1.5, sw), (0.5, -1.5, -sw)]
    for (lx, ly, o) in L:
        ox, oy = mv(o*0.6)
        lc = skin if baixo in ('bermuda', 'saia', 'vestido') else bot
        parts.append((lx+ox, ly+oy, 0, 1.5 if face != 'e' else 2.5, 2.5 if face != 'e' else 1.5, 1.2, shoe))
        parts.append((lx+ox, ly+oy, 1.2, 1.5 if face != 'e' else 2.5, 2.5 if face != 'e' else 1.5, 2.6, lc))
        if baixo in ('calca', 'macacao') or baixo not in ('bermuda', 'saia', 'vestido'):
            parts.append((lx+ox, ly+oy, 3.8, 1.5 if face != 'e' else 2.5, 2.5 if face != 'e' else 1.5, 2.2, bot))
        else:
            parts.append((lx+ox, ly+oy, 3.8, 1.5 if face != 'e' else 2.5, 2.5 if face != 'e' else 1.5, 2.2, bot if baixo == 'bermuda' else skin))
    # tronco
    bw, bd = (4.5, 2.5) if face != 'e' else (2.5, 4.5)
    tx, ty = -bw/2, -bd/2
    def estampa(d_, P_, x, y, z, x1, y1, z1):
        if est in ('listrada', 'xadrez'):
            for zz in (z+1.5, z+3.0, z+4.5):
                d_.line([P_(x, y1, zz), P_(x1, y1, zz), P_(x1, y, zz)], fill=shirt2, width=max(1, int(q)))
        if est == 'time':
            if face != 'e': d_.line([P_((x+x1)/2, y1, z), P_((x+x1)/2, y1, z1)], fill=shirt2, width=max(1, int(2*q)))
            else: d_.line([P_(x1, (y+y1)/2, z), P_(x1, (y+y1)/2, z1)], fill=shirt2, width=max(1, int(2*q)))
        if est == 'duas_cores':
            pass
        if uniforme == 'fazendeiro':
            for xx in ((x+0.8, x+1.6) if face != 'e' else ()): pass
    if baixo == 'vestido': parts.append((tx-0.4, ty-0.4, 4.5, bw+0.8, bd+0.8, 2.0, shirt2 if est != 'lisa' else shirt))
    if baixo == 'saia': parts.append((tx-0.4, ty-0.4, 4.5, bw+0.8, bd+0.8, 1.6, bot))
    if est == 'duas_cores':
        parts.append((tx, ty, 6.0, bw, bd, 2.6, shirt2)); parts.append((tx, ty, 8.6, bw, bd, 3.2, shirt, estampa))
    elif uniforme == 'fazendeiro':
        parts.append((tx, ty, 6.0, bw, bd, 3.0, bot)); parts.append((tx, ty, 9.0, bw, bd, 2.8, shirt, estampa))
    else:
        parts.append((tx, ty, 6.0, bw, bd, 5.8, shirt, estampa))
    if aces == 'mochila':
        if face == 'e': parts.append((tx-1.6, ty+0.5, 7.0, 1.6, bd-1, 4.0, acc))
        else: parts.append((tx+0.5, ty-1.6, 7.0, bw-1, 1.6, 4.0, acc))
    # braços
    sleeve = skin if est == 'regata' else (shirt2 if est == 'time' else shirt)
    if face == 'e': A_ = [(tx+0.5, ty-1.4, -sw), (tx+0.5, ty+bd, sw)]
    else: A_ = [(tx-1.4, ty+0.5, -sw), (tx+bw, ty+0.5, sw)]
    for (axx, ayy, o) in A_:
        ox, oy = mv(o*0.7)
        parts.append((axx+ox, ayy+oy, 6.6, 1.4, 1.4, 1.2, skin))
        parts.append((axx+ox, ayy+oy, 7.8, 1.4, 1.4, 3.8, sleeve))
    if tool == 'enxada':
        ox, oy = mv(1.5)
        parts.append((A_[1][0]+ox, A_[1][1]+oy, 3.0, 0.5, 0.5, 6.5, (120, 80, 40)))
        parts.append((A_[1][0]+ox-0.4, A_[1][1]+oy-0.4, 2.4, 1.3, 1.3, 0.6, (150, 150, 160)))
    if carry == 'sacola':
        parts.append((A_[1][0], A_[1][1], 4.4, 1.6, 1.6, 2.2, (250, 250, 244)))
    # cabeça
    hx, hy, hz, hsz = -2.2, -2.2, 11.8, 4.4
    def rosto(d_, P_, x, y, z, x1, y1, z1):
        if face is None: return
        kr_ = max(1, int(round(q)))
        def F(u, v):   # u: 0..1 ao longo da face, v: altura
            return P_(x+(x1-x)*u, y1, z+v) if face == 's' else P_(x1, y+(y1-y)*u, z+v)
        eyc = (24, 24, 32)
        if aces == 'oculos_sol' or look.get('oculos'):
            c_ = (24, 24, 32) if aces == 'oculos_sol' else (40, 40, 50)
            d_.polygon([F(.12, 3.3), F(.88, 3.3), F(.88, 2.5), F(.12, 2.5)], fill=c_)
        for u in (.3, .7):
            a = F(u, 2.9); d_.rectangle([a[0]-kr_, a[1]-kr_, a[0]+kr_-1, a[1]+kr_-1], fill=eyc)
            a = F(u, 3.6); d_.line([a[0]-kr_*1.5, a[1], a[0]+kr_*1.5, a[1]], fill=sh(hair, .9), width=kr_)
        if look.get('barba'):
            d_.polygon([F(.1, 1.7), F(.9, 1.7), F(.9, 0), F(.1, 0)], fill=sh(hair, .95))
        a = F(.5, 1.3); d_.line([a[0]-kr_*2, a[1], a[0]+kr_*2, a[1]], fill=(150, 70, 60), width=kr_)
        a = F(.5, 2.0); d_.rectangle([a[0]-kr_//2, a[1]-kr_//2, a[0]+kr_//2, a[1]+kr_//2], fill=sh(skin, .8))
    parts.append((hx, hy, hz, hsz, hsz, hsz, skin, rosto))
    if aces == 'cachecol': parts.append((hx+0.3, hy+0.3, 11.2, hsz-0.6, hsz-0.6, 1.0, acc))
    # cabelo
    if hs != 'careca':
        th = {'afro': 2.4, 'cacheado': 1.8, 'raspado': 0.5, 'moicano': 0.5}.get(hs, 1.2)
        ex = 0.6 if hs in ('afro', 'cacheado') else 0.25
        parts.append((hx-ex, hy-ex, hz+hsz-0.6, hsz+2*ex, hsz+2*ex, th+0.6, hair))
        if hs == 'moicano': parts.append((hx+1.8, hy-0.2, hz+hsz, 1.4, hsz+0.4, 2.2, hair))
        if hs == 'topete': parts.append((hx+0.5, hy+0.5, hz+hsz+0.5, hsz-1, hsz-1, 1.6, hair))
        if hs == 'coque': parts.append((hx+1.5, hy+1.5, hz+hsz+1.0, 2, 2, 1.8, hair))
        back = (hx-0.3, hy-0.3)
        long_ = hs in ('longo', 'rabo', 'trancas', 'cacheado', 'afro')
        if face is None:
            parts.append((hx-0.3, hy-0.3, hz+(0.0 if long_ else 1.8), hsz+0.6, hsz+0.6, hsz-(0.0 if long_ else 1.8), hair))
            if long_: parts.append((hx+0.5, hy+0.5, hz-2.4, hsz-1, hsz-1, 2.6, hair))
        elif long_:
            if face == 's': parts.append((hx-0.4, hy-0.3, hz-1.6, 0.6, hsz, hsz+1.0, hair)); parts.append((hx+hsz-0.2, hy-0.3, hz-1.6, 0.6, hsz-0.4, hsz+1.0, hair))
            else: parts.append((hx-0.3, hy-0.4, hz-1.6, hsz, 0.6, hsz+1.0, hair)); parts.append((hx-0.3, hy+hsz-0.2, hz-1.6, hsz-0.4, 0.6, hsz+1.0, hair))
        else:
            if face == 's': parts.append((hx+hsz-0.1, hy-0.2, hz+2.0, 0.4, hsz, hsz-2.0, hair))
            else: parts.append((hx-0.2, hy+hsz-0.1, hz+2.0, hsz, 0.4, hsz-2.0, hair))
    # chapéu
    if hat:
        if hat == 'palha': parts.append((hx-1.4, hy-1.4, hz+hsz, hsz+2.8, hsz+2.8, 0.6, (226, 196, 110))); parts.append((hx+0.2, hy+0.2, hz+hsz+0.6, hsz-0.4, hsz-0.4, 1.8, (214, 182, 96)))
        elif hat == 'coroa':
            parts.append((hx, hy, hz+hsz+0.4, hsz, hsz, 1.4, (240, 200, 60)))
        elif hat == 'capacete': parts.append((hx-0.4, hy-0.4, hz+hsz-0.6, hsz+0.8, hsz+0.8, 2.0, hatc))
        else:
            parts.append((hx-0.3, hy-0.3, hz+hsz-0.3, hsz+0.6, hsz+0.6, 1.6, hatc))
            if hat == 'bone' and face is not None:
                if face == 's': parts.append((hx, hy+hsz, hz+hsz-0.3, hsz, 2.0, 0.5, sh(hatc, .85)))
                else: parts.append((hx+hsz, hy, hz+hsz-0.3, 2.0, hsz, 0.5, sh(hatc, .85)))
    if aces == 'fone':
        parts.append((hx-0.6, hy+1.5, hz+1.8, 0.6, 2.0, 2.0, (40, 40, 50)) if face == 's' else (hx+1.5, hy-0.6, hz+1.8, 2.0, 0.6, 2.0, (40, 40, 50)))
    # sombra quadrada
    d.polygon([P(-3, -3, 0), P(3, -3, 0), P(3, 3, 0), P(-3, 3, 0)], fill=(0, 30, 0, 70))
    _boxdraw(d, P, parts)
    im.info['foot'] = Hc-fy
    if key is not None: _VC[key] = im
    return im

def cachorro(dr='right', fr=0, kr=2, bola=False):
    Wc, Hc = 26*kr, 16*kr; fx, fy = Wc//2, Hc-kr
    im = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def P(x, y, z): return (fx+(x-y)*2*kr, fy+(x+y)*kr-z*kr)
    c = (196, 150, 96); sw = [0, .8, 0, -.8][fr % 4]
    e = dr in ('right', 'down')
    parts = []
    if dr in ('right', 'left'):
        s_ = 1 if dr == 'right' else -1
        parts += [(-3, -1, 2, 6, 2.4, 2.6, c), (s_*3-(1.4 if s_ < 0 else 0) + (0 if s_ > 0 else -1.6), -1.2, 3.6, 3, 2.8, 2.8, c,
                   lambda d_, P_, x, y, z, x1, y1, z1: d_.rectangle([*P_(x1 if s_ > 0 else x, y1, z+2.0), *(np.array(P_(x1 if s_ > 0 else x, y1, z+2.0))+kr)], fill=(30, 30, 30)))]
        for (lx, o) in ((-2.6, sw), (1.8, -sw)):
            parts.append((lx+o, -1, 0, 1, 1, 2, sh(c, .8))); parts.append((lx-o, 0.4, 0, 1, 1, 2, sh(c, .8)))
        parts.append((-s_*3.6-0.5, -0.4, 4.0, 1, 1, 1, c))
        if bola: parts.append((s_*5-0.6, -0.6, 3.2, 1.8, 1.8, 1.8, (250, 250, 250)))
    else:
        parts += [(-1.2, -3, 2, 2.4, 6, 2.6, c), (-1.4, 2.6, 3.6, 2.8, 3, 2.8, c)]
        for (ly_, o) in ((-2.6, sw), (1.8, -sw)):
            parts.append((-1, ly_+o, 0, 1, 1, 2, sh(c, .8))); parts.append((0.4, ly_-o, 0, 1, 1, 2, sh(c, .8)))
    d.polygon([P(-3, -2, 0), P(3, -2, 0), P(3, 2, 0), P(-3, 2, 0)], fill=(0, 30, 0, 60))
    _boxdraw(d, P, parts)
    im.info['foot'] = Hc-fy
    return im
