# Motor ISOMÉTRICO da Cidade dos Seguidores (ep. 6 em diante).
# Mesmo mapa lógico (x, y) do site; aqui só muda o desenho.
#   P(x, y, z) -> pixel na "tela iso" (resolução baixa, 1 unidade lógica = 2 px na horizontal)
#   Cada construção vira um sprite em cache; a cada quadro só se cola o que está na câmera.
import math, random, numpy as np
from PIL import Image, ImageDraw
from world import W as MW, MAINX0, MAINX1
from world16 import ROOF16, WALL16, npc_sprite, S, make_ground16_h
from font import draw_text, text_width
import scene as SC
from scene import lot, MH6, ROADD, ROADE, ROADF

MH = MH6
TOP = 80
OX, OY = MH*2+40, TOP
IW, IH = (MW+MH)*2+80, MW+MH+TOP+60
_ox, _oy = OX, OY
d = None
def P(x, y, z=0): return (_ox+(x-y)*2, _oy+(x+y)-z)
def PW(x, y, z=0): return (OX+(x-y)*2, OY+(x+y)-z)          # coordenada global na tela iso
def sh(c, f):
    if f <= 1: return tuple(int(v*f) for v in c[:3])
    return tuple(int(v+(255-v)*(f-1)) for v in c[:3])
OUT = (34, 28, 40)

# ---------------- primitivas ----------------
def quad(pts, fill, outline=None): d.polygon(pts, fill=fill, outline=outline)
def shadow(x0, y0, x1, y1, h):
    o = h*0.35
    d.polygon([P(x0, y0), P(x1, y0), P(x1+o, y0+o*0.2), P(x1+o, y1+o), P(x0+o*0.2, y1+o), P(x0, y1)], fill=(0, 20, 0, 70))
def box(x0, y0, x1, y1, h, cs, cw, z0=0, outline=True):
    """paredes sul (cs, clara) e leste (cw, escura)"""
    quad([P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z0+h), P(x0, y1, z0+h)], cs)
    quad([P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z0+h), P(x1, y0, z0+h)], cw)
    if outline:
        d.line([P(x0, y1, z0), P(x1, y1, z0), P(x1, y0, z0)], fill=OUT)
        d.line([P(x1, y1, z0), P(x1, y1, z0+h)], fill=sh(cw, 0.7))
        d.line([P(x0, y1, z0), P(x0, y1, z0+h)], fill=OUT)
def top(x0, y0, x1, y1, h, c): quad([P(x0, y0, h), P(x1, y0, h), P(x1, y1, h), P(x0, y1, h)], c)
def win_s(x, y1, u0, u1, v0, v1, glass=(126, 184, 232), frame=(250, 250, 246), curtain=None):
    """janela na parede sul (plano y=y1): u ao longo de x, v altura"""
    quad([P(x+u0-0.6, y1, v0-1), P(x+u1+0.6, y1, v0-1), P(x+u1+0.6, y1, v1+1), P(x+u0-0.6, y1, v1+1)], frame)
    quad([P(x+u0, y1, v0), P(x+u1, y1, v0), P(x+u1, y1, v1), P(x+u0, y1, v1)], glass)
    d.line([P(x+u0+0.5, y1, v1-1), P(x+u0+0.5, y1, v0+2)], fill=(214, 236, 252))
    um = (u0+u1)/2; d.line([P(x+um, y1, v0), P(x+um, y1, v1)], fill=frame)
    if curtain: quad([P(x+u0, y1, v1), P(x+u0+0.9, y1, v1), P(x+u0+0.9, y1, v0+1), P(x+u0, y1, v0+1)], curtain)
    quad([P(x+u0-1, y1, v0-1), P(x+u1+1, y1, v0-1), P(x+u1+1, y1+0.8, v0-1), P(x+u0-1, y1+0.8, v0-1)], (200, 196, 186))
def win_e(x1, y, u0, u1, v0, v1, glass=(98, 150, 200), frame=(226, 224, 218)):
    quad([P(x1, y+u0-0.6, v0-1), P(x1, y+u1+0.6, v0-1), P(x1, y+u1+0.6, v1+1), P(x1, y+u0-0.6, v1+1)], frame)
    quad([P(x1, y+u0, v0), P(x1, y+u1, v0), P(x1, y+u1, v1), P(x1, y+u0, v1)], glass)
    um = (u0+u1)/2; d.line([P(x1, y+um, v0), P(x1, y+um, v1)], fill=frame)
def door_s(x, y1, u0, u1, h, c=(124, 76, 42)):
    quad([P(x+u0-0.6, y1, 0), P(x+u1+0.6, y1, 0), P(x+u1+0.6, y1, h+1), P(x+u0-0.6, y1, h+1)], (240, 236, 226))
    quad([P(x+u0, y1, 0), P(x+u1, y1, 0), P(x+u1, y1, h), P(x+u0, y1, h)], c)
    d.line([P(x+u0+0.6, y1, h-1), P(x+u0+0.6, y1, 1)], fill=sh(c, 1.3))
    d.point(P(x+u1-1.2, y1, h/2), fill=(250, 210, 90))
    quad([P(x+u0-1.5, y1, 0), P(x+u1+1.5, y1, 0), P(x+u1+1.5, y1+2.2, 0), P(x+u0-1.5, y1+2.2, 0)], (190, 186, 176))
def gable_roof(x0, y0, x1, y1, h, r, ramp, e=1.4):
    ym = (y0+y1)/2
    quad([P(x0-e, y0-e, h-1), P(x1+e, y0-e, h-1), P(x1+e, ym, h+r), P(x0-e, ym, h+r)], ramp[1])
    # empena leste
    quad([P(x1, y0, h), P(x1, y1, h), P(x1, ym, h+r)], sh(ramp[2], 0.75))
    # água sul com fileiras de telha
    S0 = [P(x0-e, y1+e, h-1), P(x1+e, y1+e, h-1), P(x1+e, ym, h+r), P(x0-e, ym, h+r)]
    quad(S0, ramp[2])
    n = 6
    for k in range(1, n):
        f = k/n; yk = y1+e+(ym-(y1+e))*f; zk = h-1+(r+1)*f
        d.line([P(x0-e, yk, zk), P(x1+e, yk, zk)], fill=ramp[1])
        for j in np.arange(x0-e+(1.5 if k % 2 else 0), x1+e, 3):
            d.line([P(j, yk, zk), P(j, yk+(ym-(y1+e))/n, zk+(r+1)/n)], fill=sh(ramp[1], 0.95))
    d.line([P(x0-e, ym, h+r), P(x1+e, ym, h+r)], fill=ramp[3])
    d.line([P(x0-e, y1+e, h-1), P(x1+e, y1+e, h-1)], fill=OUT)
    d.line([P(x1+e, y1+e, h-1), P(x1+e, ym, h+r)], fill=OUT); d.line([P(x0-e, y1+e, h-1), P(x0-e, ym, h+r)], fill=OUT)
    d.line([P(x0-e, ym, h+r), P(x0-e, y0-e, h-1)], fill=OUT)
def hip_roof(x0, y0, x1, y1, h, r, ramp, e=1.4):
    xm, ym = (x0+x1)/2, (y0+y1)/2; inset = min(x1-x0, y1-y0)/2
    a0, a1 = x0+inset, x1-inset
    quad([P(x0-e, y0-e, h), P(x1+e, y0-e, h), P(a1, ym, h+r), P(a0, ym, h+r)], ramp[1])
    quad([P(x0-e, y1+e, h), P(x1+e, y1+e, h), P(a1, ym, h+r), P(a0, ym, h+r)], ramp[2])
    quad([P(x1+e, y0-e, h), P(x1+e, y1+e, h), P(a1, ym, h+r)], sh(ramp[2], 0.78))
    for k in range(1, 5):
        f = k/5; yk = y1+e+(ym-y1-e)*f; zk = h+r*f
        xa = x0-e+(a0-x0+e)*f; xb = x1+e+(a1-x1-e)*f
        d.line([P(xa, yk, zk), P(xb, yk, zk)], fill=ramp[1])
    d.line([P(x0-e, y1+e, h), P(x1+e, y1+e, h), P(x1+e, y0-e, h)], fill=OUT)
    d.line([P(a0, ym, h+r), P(a1, ym, h+r)], fill=ramp[3])

# ---------------- construções ----------------
def house(l, var, p=1.0, venda=False):
    lx_, ly_ = lot(*l)
    x0, x1, y0, y1 = lx_+1.5, lx_+19.5, ly_+5, ly_+20
    ramp = ROOF16[var % 6]; wc = WALL16[(var//2) % 4]
    if p < 1:
        for (qx, qy) in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]: d.line([P(qx, qy), P(qx, qy, 6)], fill=(120, 80, 40))
        hh = int(p*12)
        if p > 0.2:
            top(x0, y0, x1, y1, 0, (150, 150, 156)); box(x0, y0, x1, y1, max(1, hh), wc, sh(wc, 0.8))
            d.line([P(x0, y1, hh+3), P(x1, y1, hh+3)], fill=(124, 82, 46)); d.line([P(x1, y1, hh+3), P(x1, y0, hh+3)], fill=(124, 82, 46))
        return
    shadow(x0, y0, x1, y1, 22)
    H_ = 13
    box(x0, y0, x1, y1, H_, wc, sh(wc, 0.78))
    # rodapé
    quad([P(x0, y1, 0), P(x1, y1, 0), P(x1, y1, 2), P(x0, y1, 2)], sh(wc, 0.7))
    quad([P(x1, y0, 0), P(x1, y1, 0), P(x1, y1, 2), P(x1, y0, 2)], sh(wc, 0.58))
    cur = [(214, 90, 90), (90, 150, 214), (240, 200, 90), (140, 200, 120)][var % 4]
    front = l[2] == 'a'
    if front:
        door_s(x0, y1, 7.5, 11, 9)
        win_s(x0, y1, 2, 5.6, 4, 9, curtain=cur); win_s(x0, y1, 13, 16.6, 4, 9, curtain=cur)
    else:
        win_s(x0, y1, 2.5, 6.5, 4, 9, curtain=cur); win_s(x0, y1, 11.5, 15.5, 4, 9, curtain=cur)
    win_e(x1, y0, 4.5, 9.5, 4, 9)
    gable_roof(x0, y0, x1, y1, H_, 10, ramp)
    # chaminé
    cx0, cy0 = x1-5, y0+4
    box(cx0, cy0, cx0+2.5, cy0+2.5, 8, (168, 82, 62), (128, 60, 46), z0=H_+6)
    top(cx0, cy0, cx0+2.5, cy0+2.5, H_+14, (90, 50, 40))
    if venda:
        aw = [(214, 50, 50), (250, 250, 246)]
        for k in range(8):
            u = 1+k*2.1
            quad([P(x0+u, y1, 11), P(x0+u+2.1, y1, 11), P(x0+u+2.1, y1+3, 8), P(x0+u, y1+3, 8)], aw[k % 2])
        d.line([P(x0+1, y1+3, 8), P(x0+17.8, y1+3, 8)], fill=OUT)
    # cerquinha
    if var % 3 == 1 and front:
        for u in np.arange(0, 19, 1.5):
            if 6 < u < 12: continue
            d.line([P(x0+u, y1+3.5), P(x0+u, y1+3.5, 4)], fill=(250, 248, 240))
        d.line([P(x0, y1+3.5, 3), P(x0+6, y1+3.5, 3)], fill=(214, 210, 200)); d.line([P(x0+12, y1+3.5, 3), P(x0+18.5, y1+3.5, 3)], fill=(214, 210, 200))

def church():
    x0, x1, y0, y1 = 117, 146, 72, 100
    shadow(x0, y0, x1, y1, 40)
    wall = (242, 238, 230)
    box(x0, y0, x1, y1, 22, wall, sh(wall, 0.8))
    for k in range(3): win_e(x1, y0, 4+k*8, 7+k*8, 7, 17, glass=(200, 120, 70))
    ramp = [(40, 48, 84), (64, 76, 120), (92, 106, 156), (134, 148, 196)]
    xm = (x0+x1)/2; e = 1.5; h = 22; r = 16
    quad([P(x0-e, y0, h), P(x0-e, y1+e, h), P(xm, y1+e, h+r), P(xm, y0, h+r)], ramp[1])
    quad([P(x1+e, y0, h), P(x1+e, y1+e, h), P(xm, y1+e, h+r), P(xm, y0, h+r)], ramp[2])
    for k in range(1, 6):
        f = k/6; xk = x1+e+(xm-x1-e)*f; zk = h+r*f
        d.line([P(xk, y0, zk), P(xk, y1+e, zk)], fill=ramp[1])
    quad([P(x0, y1, h), P(x1, y1, h), P(xm, y1, h+r)], wall)
    d.line([P(x1+e, y1+e, h), P(xm, y1+e, h+r), P(x0-e, y1+e, h)], fill=OUT)
    # torre
    tx0, tx1, ty0, ty1 = xm-5, xm+5, y1-4, y1+5
    box(tx0, ty0, tx1, ty1, 46, (250, 248, 242), (210, 206, 198))
    quad([P(tx0+3, ty1, 30), P(tx1-3, ty1, 30), P(tx1-3, ty1, 40), P(tx0+3, ty1, 40)], (60, 50, 50))
    quad([P(tx0+3.5, ty1, 31), P(tx1-3.5, ty1, 31), P(tx1-4.5, ty1, 37), P(tx0+4.5, ty1, 37)], (214, 168, 56))
    door_s(tx0, ty1, 3, 7, 11, (110, 60, 36))
    cx_, cy_ = P(xm, ty1, 20); d.ellipse([cx_-3, cy_-3, cx_+3, cy_+3], fill=(200, 120, 70), outline=OUT)
    quad([P(tx0-1, ty0-1, 46), P(tx1+1, ty0-1, 46), P(tx1+1, ty1+1, 46), P(tx0-1, ty1+1, 46)], ramp[1])
    apex = P(xm, (ty0+ty1)/2, 62)
    quad([P(tx0-1, ty1+1, 46), P(tx1+1, ty1+1, 46), apex], ramp[2]); quad([P(tx1+1, ty0-1, 46), P(tx1+1, ty1+1, 46), apex], ramp[1])
    cx_, cy_ = apex; d.line([cx_, cy_, cx_, cy_-9], fill=(240, 200, 60), width=2); d.line([cx_-3, cy_-6, cx_+3, cy_-6], fill=(240, 200, 60), width=2)

def escola():
    x0, x1, y0, y1 = 162.5, 203.5, 131, 146
    shadow(x0, y0, x1, y1, 26)
    wc = (252, 222, 128)
    box(x0, y0, x1, y1, 15, wc, sh(wc, 0.78))
    quad([P(x0, y1, 0), P(x1, y1, 0), P(x1, y1, 3), P(x0, y1, 3)], (214, 120, 70))
    for u in (3, 10, 28, 35): win_s(x0, y1, u, u+4, 5, 11)
    door_s(x0, y1, 18.5, 22.5, 10, (40, 132, 70))
    win_e(x1, y0, 3, 7, 5, 11); win_e(x1, y0, 9, 13, 5, 11)
    hip_roof(x0, y0, x1, y1, 15, 10, ROOF16[3])
    # torre do sino
    tx0, ty0 = 180.5, 140
    box(tx0, ty0, tx0+6, ty0+6, 14, (250, 250, 244), (214, 210, 200), z0=20)
    quad([P(tx0+1.5, ty0+6, 25), P(tx0+4.5, ty0+6, 25), P(tx0+4.5, ty0+6, 31), P(tx0+1.5, ty0+6, 31)], (60, 50, 50))
    quad([P(tx0+2, ty0+6, 26), P(tx0+4, ty0+6, 26), P(tx0+3.5, ty0+6, 30), P(tx0+2.5, ty0+6, 30)], (214, 168, 56))
    ap = P(tx0+3, ty0+3, 42)
    quad([P(tx0-0.5, ty0+6.5, 34), P(tx0+6.5, ty0+6.5, 34), ap], ROOF16[3][2]); quad([P(tx0+6.5, ty0-0.5, 34), P(tx0+6.5, ty0+6.5, 34), ap], ROOF16[3][1])
    # placa
    sx_, sy_ = P(x0+20.5, y1, 17)
    d.rectangle([sx_-20, sy_-12, sx_+20, sy_-3], fill=(250, 250, 244), outline=OUT)
    draw_text(d, "ESCOLA", sx_+1, sy_-10, 1, (40, 70, 160, 255), outline=None)
    # mastro
    fx, fy = P(x1+3, y1+3); d.line([fx, fy, fx, fy-34], fill=(170, 170, 180))
    d.rectangle([fx-11, fy-34, fx-1, fy-27], fill=(30, 150, 70)); d.polygon([(fx-6, fy-33), (fx-2, fy-30), (fx-6, fy-28), (fx-10, fy-30)], fill=(250, 214, 50))

def mercadinho(l=None, aw_c=(40, 150, 80), sign_c=(214, 50, 50)):
    lx_, ly_ = lot(*(l or SC.MERCADO)); x0, x1, y0, y1 = lx_+1, lx_+20, ly_+5, ly_+20
    shadow(x0, y0, x1, y1, 18)
    box(x0, y0, x1, y1, 14, (250, 250, 246), (210, 210, 206))
    top(x0, y0, x1, y1, 14, (180, 180, 186))
    box(x0, y0, x1, y1, 2, (230, 230, 226), (196, 196, 192), z0=14)
    quad([P(x0+1.5, y1, 0), P(x1-1.5, y1, 0), P(x1-1.5, y1, 8), P(x0+1.5, y1, 8)], (150, 206, 236))
    for u in np.arange(x0+3, x1-1, 3.5): d.line([P(u, y1, 0), P(u, y1, 8)], fill=(240, 246, 250))
    for k in range(9):
        u = 0.5+k*2.1
        quad([P(x0+u, y1, 12), P(x0+u+2.1, y1, 12), P(x0+u+2.1, y1+3.5, 9), P(x0+u, y1+3.5, 9)], [aw_c, (250, 250, 246)][k % 2])
    sx_, sy_ = P(x0+9.5, y1, 17)
    d.rectangle([sx_-14, sy_-11, sx_+14, sy_-1], fill=sign_c, outline=OUT)
    d.rectangle([sx_-5, sy_-8, sx_+4, sy_-4], outline=(255, 255, 255)); d.point((sx_-3, sy_-2), fill=(255, 255, 255)); d.point((sx_+2, sy_-2), fill=(255, 255, 255))

def prefeitura():
    x0, x1, y0, y1 = 141, 181.5, 401, 416
    shadow(x0, y0, x1, y1, 30)
    wc = (248, 244, 234)
    box(x0, y0, x1, y1, 16, wc, sh(wc, 0.8))
    quad([P(x0, y1, 0), P(x1, y1, 0), P(x1, y1, 2.5), P(x0, y1, 2.5)], (60, 92, 160))
    quad([P(x0, y1, 14.5), P(x1, y1, 14.5), P(x1, y1, 16), P(x0, y1, 16)], (60, 92, 160))
    for u in (2.5, 7.5, 30, 35): win_s(x0, y1, u, u+3, 4, 12)
    win_e(x1, y0, 3, 6, 4, 12); win_e(x1, y0, 9, 12, 4, 12)
    hip_roof(x0, y0, x1, y1, 16, 9, [(52, 58, 78), (78, 88, 112), (104, 116, 142), (146, 158, 184)])
    # pórtico com colunas e frontão
    px0, px1, py = x0+12.5, x1-12.5, y1+4
    top(px0, y1, px1, py, 0, (210, 206, 196))
    for k in range(3): quad([P(px0-1-k, py+k, 0), P(px1+1+k, py+k, 0), P(px1+1+k, py+k+1, 0), P(px0-1-k, py+k+1, 0)], (200-k*15, 198-k*15, 190-k*15))
    door_s(x0, y1, 18, 22.5, 11, (120, 72, 40))
    for u in np.linspace(px0+0.5, px1-0.5, 4):
        box(u-0.6, py-1.2, u+0.6, py, 16, (252, 252, 250), (214, 212, 206), outline=False)
    top(px0-1, y1, px1+1, py+0.5, 16, (236, 232, 222))
    box(px0-1, y1, px1+1, py+0.5, 2, (240, 236, 226), (200, 196, 188), z0=16)
    pm = (px0+px1)/2
    quad([P(px0-1, py+0.5, 18), P(px1+1, py+0.5, 18), P(pm, py+0.5, 28)], (250, 250, 246))
    d.line([P(px0-1, py+0.5, 18), P(pm, py+0.5, 28), P(px1+1, py+0.5, 18)], fill=OUT)
    quad([P(px1+1, y1, 18), P(px1+1, py+0.5, 18), P(pm, py+0.5, 28), P(pm, y1, 28)], (98, 110, 136))
    cx_, cy_ = P(pm, py+0.5, 22); d.ellipse([cx_-3, cy_-3, cx_+3, cy_+3], fill=(250, 246, 220), outline=OUT); d.line([cx_, cy_, cx_, cy_-2], fill=OUT); d.line([cx_, cy_, cx_+2, cy_], fill=OUT)
    sx_, sy_ = P(pm, py+0.5, 34)
    d.rectangle([sx_-32, sy_-10, sx_+32, sy_-1], fill=(250, 250, 244), outline=OUT)
    draw_text(d, "PREFEITURA", sx_+1, sy_-8, 1, (40, 60, 130, 255), outline=None)
    for (fxl, col) in ((x0-2, [(30, 150, 70), (250, 214, 50)]), (x1+2, [(40, 90, 170), (250, 250, 250), (200, 40, 50)])):
        fx, fy = P(fxl, y1+4); d.line([fx, fy, fx, fy-38], fill=(170, 170, 180))
        for j, c in enumerate(col): d.rectangle([fx+1, fy-38+j*(8//len(col)+1), fx+11, fy-38+(j+1)*(8//len(col)+1)], fill=c)

def tree(x, y, r):
    rr = random.Random(int(x*7+y*13))
    bx, by = P(x, y)
    d.ellipse([bx-r, by-r*0.35, bx+r+2, by+r*0.45], fill=(0, 30, 0, 70))
    d.rectangle([bx-1, by-r-2, bx+1, by], fill=(104, 70, 44)); d.line([bx+1, by-r-2, bx+1, by], fill=(70, 46, 30))
    cy_ = by-r-6
    blobs = [(bx, cy_, r)]+[(bx+math.cos(k*1.05+rr.random())*r*0.55, cy_+math.sin(k*1.05)*r*0.4, r*0.6) for k in range(6)]
    for (cx, cy, rad) in blobs: d.ellipse([cx-rad-1, cy-rad-1, cx+rad+1, cy+rad+1], fill=(24, 70, 40))
    for (cx, cy, rad) in blobs: d.ellipse([cx-rad, cy-rad, cx+rad, cy+rad], fill=(52, 132, 60))
    for (cx, cy, rad) in blobs: d.ellipse([cx-rad*0.75-1, cy-rad*0.8, cx+rad*0.35, cy+rad*0.2], fill=(86, 168, 74))
    for _ in range(int(r*1.5)):
        a = rr.uniform(0, 6.28); q = rr.uniform(0, r*0.8)
        px_, py_ = int(bx+math.cos(a)*q-2), int(cy_+math.sin(a)*q*0.8-2)
        d.point((px_, py_), fill=(140, 204, 104))
    if rr.random() < 0.4:
        for _ in range(4):
            d.point((int(bx+rr.uniform(-r*0.7, r*0.7)), int(cy_+rr.uniform(-r*0.6, r*0.5))), fill=(220, 50, 50))

def lamp(x, y):
    bx, by = P(x, y); d.line([bx, by, bx, by-16], fill=(60, 60, 70)); d.rectangle([bx-2, by-19, bx+2, by-15], fill=(250, 230, 150), outline=(50, 50, 60))
def fonte():
    cx, cy = P(132, 245)
    d.ellipse([cx-16, cy-8, cx+16, cy+8], fill=(160, 156, 150), outline=OUT); d.ellipse([cx-13, cy-6, cx+13, cy+5], fill=(90, 150, 214))
    d.rectangle([cx-2, cy-12, cx+2, cy-1], fill=(190, 186, 180)); d.ellipse([cx-6, cy-15, cx+6, cy-10], fill=(170, 166, 160)); d.ellipse([cx-4, cy-14, cx+4, cy-11], fill=(120, 180, 230))
def banco(x, y):
    quad([P(x-3, y, 3), P(x+3, y, 3), P(x+3, y+1.5, 3), P(x-3, y+1.5, 3)], (176, 116, 64))
    d.line([P(x-3, y, 3), P(x-3, y, 0)], fill=(80, 60, 50)); d.line([P(x+3, y+1.5, 3), P(x+3, y+1.5, 0)], fill=(80, 60, 50))
def stakes(l):
    lx_, ly_ = lot(*l)
    for (qx, qy) in [(lx_+2, ly_+5), (lx_+19, ly_+5), (lx_+2, ly_+20), (lx_+19, ly_+20)]: d.line([P(qx, qy), P(qx, qy, 5)], fill=(130, 88, 46))
def placa(txt=None):
    x, y = 142, 446
    for u in (1, 13): d.line([P(x+u, y), P(x+u, y, 9)], fill=(104, 66, 36))
    quad([P(x, y, 7), P(x+14, y, 7), P(x+14, y, 15), P(x, y, 15)], (214, 174, 116)); d.polygon([P(x, y, 7), P(x+14, y, 7), P(x+14, y, 15), P(x, y, 15)], outline=OUT)
    if txt:
        cx, cy = P(x+7, y, 11); draw_text(d, txt, int(cx)+1, int(cy)-6, 1, (110, 60, 30, 255), outline=None)


# ---------------- construções novas (ep. 6) ----------------
def posto():
    l0 = SC.POSTO[0]; lx_, ly_ = lot(*l0)
    x0, x1, y0, y1 = lx_+1.5, lx_+41.5, ly_+5, ly_+20
    shadow(x0, y0, x1, y1, 22)
    wc = (250, 250, 248)
    box(x0, y0, x1, y1, 15, wc, sh(wc, 0.8))
    quad([P(x0, y1, 6), P(x1, y1, 6), P(x1, y1, 8), P(x0, y1, 8)], (40, 160, 90))
    quad([P(x1, y0, 6), P(x1, y1, 6), P(x1, y1, 8), P(x1, y0, 8)], (30, 120, 70))
    top(x0, y0, x1, y1, 15, (196, 200, 204))
    box(x0, y0, x1, y1, 2, (236, 238, 240), (200, 204, 208), z0=15)
    for u in (3, 9, 29, 35): win_s(x0, y1, u, u+3.5, 9, 13, glass=(170, 214, 240))
    quad([P(x0+15, y1, 0), P(x0+25, y1, 0), P(x0+25, y1, 12), P(x0+15, y1, 12)], (150, 206, 236))
    d.line([P(x0+20, y1, 0), P(x0+20, y1, 12)], fill=(240, 246, 250))
    quad([P(x0+13, y1, 13), P(x0+27, y1, 13), P(x0+27, y1+4, 11), P(x0+13, y1+4, 11)], (40, 160, 90))
    win_e(x1, y0, 3, 7, 9, 13); win_e(x1, y0, 9, 13, 9, 13)
    # placa com a cruz verde
    cx, cy = P(x0+20, y1, 25)
    d.rectangle([cx-24, cy-9, cx+24, cy+3], fill=(250, 250, 248), outline=OUT)
    d.rectangle([cx-21, cy-6, cx-15, cy], fill=(40, 160, 90)); d.rectangle([cx-20, cy-7, cx-16, cy+1], fill=(40, 160, 90))
    d.rectangle([cx-19, cy-5, cx-17, cy-1], fill=(255, 255, 255)); d.rectangle([cx-20, cy-4, cx-16, cy-2], fill=(255, 255, 255))
    draw_text(d, "POSTO", cx+6, cy-6, 1, (30, 120, 70, 255), outline=None)
    # ambulância
    ax0, ay0 = x1-9, y1+3
    shadow(ax0, ay0, ax0+7, ay0+3.5, 6)
    box(ax0, ay0, ax0+7, ay0+3.5, 5, (252, 252, 252), (210, 210, 214), z0=1)
    top(ax0, ay0, ax0+7, ay0+3.5, 6, (236, 236, 240))
    quad([P(ax0, ay0+3.5, 3), P(ax0+7, ay0+3.5, 3), P(ax0+7, ay0+3.5, 4), P(ax0, ay0+3.5, 4)], (40, 160, 90))
    for (wx, wy) in ((ax0+1.5, ay0+3.5), (ax0+5.5, ay0+3.5)):
        X, Y = P(wx, wy, 1); d.ellipse([X-2, Y-2, X+2, Y+2], fill=(30, 30, 34))
    X, Y = P(ax0+3.5, ay0+1.7, 7); d.rectangle([X-2, Y-1, X+2, Y+1], fill=(220, 40, 40))

def mercado2(): mercadinho(SC.MERCADO2, (40, 110, 200), (40, 90, 190))

def campo(label=True):
    lx_, ly_ = lot(*SC.CAMPO[0])
    x0, y0, x1, y1 = lx_+1, ly_+2, lx_+88, ly_+50
    quad([P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)], (150, 120, 76))
    for k in range(0, int(y1-y0), 4):
        d.line([P(x0+1, y0+k+1), P(x1-1, y0+k+1)], fill=(160, 130, 84))
    for u in np.arange(x0, x1+0.1, 3):
        d.line([P(u, y1), P(u, y1, 4)], fill=(240, 236, 226)); d.line([P(u, y0), P(u, y0, 4)], fill=(240, 236, 226))
    for v in np.arange(y0, y1+0.1, 3):
        d.line([P(x0, v), P(x0, v, 4)], fill=(240, 236, 226)); d.line([P(x1, v), P(x1, v, 4)], fill=(240, 236, 226))
    for (a, b) in (((x0, y1), (x1, y1)), ((x1, y0), (x1, y1)), ((x0, y0), (x1, y0)), ((x0, y0), (x0, y1))):
        d.line([P(*a, 3), P(*b, 3)], fill=(214, 210, 200))
    if label:
        bx, by = (x0+x1)/2, y1
        for u in (-4, 4): d.line([P(bx+u, by+1), P(bx+u, by+1, 12)], fill=(104, 66, 36))
        quad([P(bx-7, by+1, 9), P(bx+7, by+1, 9), P(bx+7, by+1, 18), P(bx-7, by+1, 18)], (250, 214, 70))
        cx, cy = P(bx, by+1, 15); draw_text(d, "700", int(cx)+1, int(cy)-5, 1, (120, 40, 30, 255), outline=None)

def construcao(x0, y0, x1, y1, p, final, hfin=15, col=(250, 250, 246)):
    """obra genérica: estacas -> laje -> paredes -> prédio pronto (com andaime até p=1)"""
    if p <= 0: return
    if p < 0.3:
        for (qx, qy) in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]: d.line([P(qx, qy), P(qx, qy, 6)], fill=(120, 80, 40))
        f = p/0.3
        quad([P(x0, y0), P(x0+(x1-x0)*f, y0), P(x0+(x1-x0)*f, y1), P(x0, y1)], (150, 150, 156))
        return
    if p < 0.7:
        top(x0, y0, x1, y1, 0, (150, 150, 156))
        hh = max(1, (p-0.3)/0.4*hfin)
        box(x0, y0, x1, y1, hh, col, sh(col, 0.8))
        for u in np.linspace(x0, x1, 5):
            d.line([P(u, y1+1), P(u, y1+1, hfin+4)], fill=(124, 82, 46))
        d.line([P(x0, y1+1, hfin+2), P(x1, y1+1, hfin+2)], fill=(124, 82, 46))
        return
    final()
    if p < 1:
        for u in np.linspace(x0, x1, 5): d.line([P(u, y1+1.5), P(u, y1+1.5, hfin+6)], fill=(124, 82, 46))
        for z in (5, 11): d.line([P(x0, y1+1.5, z), P(x1, y1+1.5, z)], fill=(124, 82, 46))

# ---------------- cache de sprites ----------------
def sprite(fn, x0, y0, x1, y1, hz, pad=24):
    """desenha fn() num sprite próprio. Devolve (img, bx0, by0) em coordenadas globais da tela iso"""
    global d, _ox, _oy
    bx0 = int(PW(x0, y1)[0])-pad-int(hz*0.6); bx1 = int(PW(x1, y0)[0])+pad+int(hz*0.6)
    by0 = int(PW(x0, y0)[1])-hz-pad; by1 = int(PW(x1, y1)[1])+pad
    im = Image.new('RGBA', (bx1-bx0, by1-by0), (0, 0, 0, 0))
    od, oox, ooy = d, _ox, _oy
    d = ImageDraw.Draw(im, 'RGBA'); _ox, _oy = OX-bx0, OY-by0
    try: fn()
    finally: d, _ox, _oy = od, oox, ooy
    bb = im.getbbox()
    if bb is None: return None
    return (im.crop(bb), bx0+bb[0], by0+bb[1])

# ---------------- terreno infinito em volta da cidade ----------------
_G = None
def ground():
    """chão do mapa (680) em 2x + texturas pro terreno de fora"""
    global _G
    if _G is None:
        G = make_ground16_h(MH, (ROADD, ROADE, ROADF), True)[0]
        blk = G[70*S:110*S, 20*S:110*S]                       # um pedaço só de grama
        t2 = np.vstack([np.hstack([blk, blk[:, ::-1]]), np.hstack([blk[::-1], blk[::-1, ::-1]])])
        road = G[620*S:670*S, 122*S:142*S]                    # rua principal (pra estrada que sai da cidade)
        _G = (G, t2, road)
    return _G

FIELDS = [(-150, 90, -30, 200, 'arado'), (-160, 300, -40, 430, 'trigo'), (-140, 520, -30, 640, 'arado'),
          (15, 700, 110, 790, 'trigo'), (150, 712, 228, 800, 'arado'), (262, 120, 380, 260, 'trigo'),
          (262, 330, 390, 470, 'arado'), (262, 560, 380, 700, 'trigo'), (20, -140, 110, -40, 'arado'), (150, -150, 228, -30, 'trigo')]
from world import river_x
def terreno(vx0, vy0, w, h):
    """chão (cor por pixel) da janela da tela iso [vx0, vx0+w) x [vy0, vy0+h)"""
    yy, xx = np.mgrid[vy0:vy0+h, vx0:vx0+w].astype(np.float32)
    a_ = (xx-OX)/2; b_ = yy-OY
    lx = (a_+b_)/2; ly = (b_-a_)/2
    return Image.fromarray(terreno_l(lx, ly)).convert('RGBA')
def terreno_l(lx, ly):
    """cor do chão pra cada ponto lógico (lx, ly) — dentro do mapa é o mapa, fora é campo infinito"""
    G, T2, RD = ground()
    gx = np.floor(lx*S).astype(np.int64); gy = np.floor(ly*S).astype(np.int64)
    out = T2[gy % T2.shape[0], gx % T2.shape[1]].astype(np.float32)
    mod = 1+0.07*np.sin(lx/37+ly/53)*np.sin(ly/29-lx/71)+0.04*np.sin(lx/11-ly/17)
    out *= mod[:, :, None]
    # plantações
    for (x0, y0, x1, y1, k) in FIELDS:
        m = (lx >= x0) & (lx < x1) & (ly >= y0) & (ly < y1)
        if not m.any(): continue
        st = (np.floor(ly[m]/2.5) % 2) == 0
        c0, c1 = ((150, 104, 64), (124, 84, 50)) if k == 'arado' else ((230, 198, 92), (204, 170, 72))
        out[m] = np.where(st[:, None], np.array(c0, np.float32), np.array(c1, np.float32))
        edge = m & ((lx < x0+1) | (lx >= x1-1) | (ly < y0+1) | (ly >= y1-1))
        out[edge] = (110, 84, 52)
    # estrada saindo da cidade (rua principal continua pra baixo)
    m = (ly >= MH) & (lx >= 122) & (lx < 142)
    if m.any():
        out[m] = RD[((np.floor(ly[m]*S).astype(int)-MH*S) % RD.shape[0]), np.clip(np.floor((lx[m]-122)*S).astype(int), 0, RD.shape[1]-1)]
    # rio continua
    rx = 238+6*np.sin(ly/40.0)
    dist = np.abs(lx-rx)
    outside = ~((lx >= 0) & (lx < MW) & (ly >= 0) & (ly < MH))
    w_ = outside & (dist < 6.0); sd = outside & (dist >= 6.0) & (dist < 7.6)
    sp = (np.sin(lx*3.1+ly*1.7)*np.sin(ly*2.3-lx*0.9)) > 0.86
    out[w_] = np.where(sp[w_][:, None], np.array([170, 214, 250], np.float32), np.array([72, 132, 214], np.float32) + (dist[w_] < 3)[:, None]*np.array([-14, -10, 0], np.float32))
    out[sd] = (214, 190, 138)
    # dentro do mapa: o chão de verdade
    ins = ~outside
    out[ins] = G[np.clip(gy[ins], 0, G.shape[0]-1), np.clip(gx[ins], 0, G.shape[1]-1)]
    return np.clip(out, 0, 255).astype(np.uint8)

_TV = {}
def tree_var(k, r):
    """sprite de árvore genérico (variação k) ancorado no ponto lógico (0,0)"""
    if (k, r) not in _TV:
        _TV[(k, r)] = sprite(lambda: tree(k*0.37, 0, r), k*0.37-8, -8, k*0.37+8, 8, 34)
    im, bx, by = _TV[(k, r)]; ax, ay = PW(k*0.37, 0)
    return im, bx-ax, by-ay
def arvores_fora(lx0, ly0, lx1, ly1, cell=10):
    """árvores do terreno de fora (determinísticas por célula)"""
    out = []
    for i in range(int(math.floor(lx0/cell)), int(math.ceil(lx1/cell))+1):
        for j in range(int(math.floor(ly0/cell)), int(math.ceil(ly1/cell))+1):
            h = (i*73856093 ^ j*19349663) & 0xffffff
            if (h % 100) > 48: continue
            x = i*cell+((h >> 8) % cell); y = j*cell+((h >> 15) % cell)
            if -6 <= x <= MW+4 and -6 <= y <= MH+4: continue
            if abs(x-(238+6*math.sin(y/40.0))) < 11: continue
            if y > MH-4 and 116 <= x <= 148: continue
            if any(x0-3 <= x < x1+3 and y0-3 <= y < y1+3 for (x0, y0, x1, y1, _) in FIELDS): continue
            out.append((x, y, (h >> 20) % 12, 6+(h >> 4) % 3))
    return out

_SPR = {}
def sky(w, h, y0):
    yy = (np.arange(h)+y0)/IH
    g_ = np.clip(yy, -0.5, 1.5)[:, None]
    c = np.array([120, 186, 236])*(1-np.clip(g_, 0, 1))+np.array([196, 228, 248])*np.clip(g_, 0, 1)
    a = np.repeat(c[:, None, :], w, axis=1).reshape(h, w, 3)
    return Image.fromarray(np.dstack([a.astype(np.uint8), np.full((h, w), 255, np.uint8)]), 'RGBA')
def spr(key, fn, box_, hz):
    if key not in _SPR: _SPR[key] = sprite(fn, *box_, hz)
    return _SPR[key]

def lot_box(l, w=21, h=25): lx_, ly_ = lot(*l); return (lx_-2, ly_, lx_+w+2, ly_+h)

def objetos(t, C):
    """lista (profundidade, sprite) de tudo que é fixo/construído no instante t"""
    out = []
    for i, l in enumerate(SC.house_lots):
        p = SC.house_p(i, C); lx_, ly_ = lot(*l)
        if p <= 0:
            if l[1] >= ROADD: out.append((lx_+ly_+20, spr(('st', l), lambda l=l: stakes(l), lot_box(l), 10)))
            continue
        pk = 1.0 if p >= 1 else round(p*20)/20
        out.append((lx_+ly_+40, spr(('h', i, pk), lambda l=l, i=i, pk=pk: house(l, SC.house_var[i], pk), lot_box(l), 46)))
    lx_, ly_ = lot(*SC.VENDA); out.append((lx_+ly_+40, spr('venda', lambda: house(SC.VENDA, 5, 1, True), lot_box(SC.VENDA), 46)))
    lx_, ly_ = lot(*SC.MERCADO); out.append((lx_+ly_+40, spr('merc', lambda: mercadinho(), lot_box(SC.MERCADO), 40)))
    out.append((246, spr('igreja', church, (110, 60, 150, 108), 80)))
    out.append((349, spr('escola', escola, (158, 126, 210, 150), 60)))
    out.append((181+420, spr('pref', prefeitura, (136, 396, 186, 424), 60)))
    # marco 600
    lx_, ly_ = lot(*SC.MERCADO2); pm = round(SC.merc2_p(t)*20)/20
    if pm > 0: out.append((lx_+ly_+40, spr(('m2', pm), lambda pm=pm, lx_=lx_, ly_=ly_: construcao(lx_+1, ly_+5, lx_+20, ly_+20, pm, mercado2, 16), lot_box(SC.MERCADO2), 46)))
    lx_, ly_ = lot(*SC.POSTO[0]); pp = round(SC.posto_p(t)*20)/20
    if pp > 0: out.append((lx_+ly_+45, spr(('po', pp), lambda pp=pp, lx_=lx_, ly_=ly_: construcao(lx_+1.5, ly_+5, lx_+41.5, ly_+20, pp, posto, 17), (lx_-2, ly_, lx_+46, ly_+30), 50)))
    else:
        for l in SC.POSTO: out.append((lot(*l)[0]+lot(*l)[1]+20, spr(('st', l), lambda l=l: stakes(l), lot_box(l), 10)))
    if pm <= 0: out.append((lot(*SC.MERCADO2)[0]+lot(*SC.MERCADO2)[1]+20, spr(('st', SC.MERCADO2), lambda: stakes(SC.MERCADO2), lot_box(SC.MERCADO2), 10)))
    lx_, ly_ = lot(*SC.CAMPO[0]); out.append((lx_+ly_-10, spr('campo', campo, (lx_-2, ly_, lx_+92, ly_+54), 26)))
    for k, tr in enumerate(SC.TREES6): out.append((tr['x']+tr['y'], spr(('tr', k), lambda tr=tr: tree(tr['x'], tr['y'], tr['r']+2), (tr['x']-8, tr['y']-8, tr['x']+8, tr['y']+8), 34)))
    out.append((153+231, spr('arvp', lambda: tree(153, 231, 8), (145, 223, 161, 239), 34)))
    for k, (x, y) in enumerate(LAMPS6): out.append((x+y, spr(('lp', k), lambda x=x, y=y: lamp(x, y), (x-2, y-2, x+2, y+2), 24)))
    out.append((132+245, spr('fonte', fonte, (122, 237, 142, 253), 20)))
    for k, (x, y) in enumerate(((111, 265), (151, 265), (111, 221))): out.append((x+y, spr(('bc', k), lambda x=x, y=y: banco(x, y), (x-4, y-2, x+4, y+3), 8)))
    out.append((142+446, spr('placa', lambda: placa(), (140, 444, 158, 450), 20)))
    return out

LAMPS6 = [(x, y) for y in range(124, MH-10, 34) for x in (123, 140) if not (205 < y < 285) and
          all(not (r_-26 < y < r_+16) for r_ in (SC.ROADA, SC.ROADC, ROADD, ROADE, ROADF))]

def person_sprite(pid, dr, fr, carry=None, uniform=None):
    import vila16 as V
    return V.NPC(pid, dr, fr, uniform, carry=carry) if carry else V.NPC(pid, dr, fr, uniform)

def render_view(t, cam, people_list, extra=None, pop=None):
    """cam = (cx, cy, zoom) em px da tela iso. people_list: [(x, y, sprite)]. Devolve imagem 1080x1920."""
    cx, cy, z = cam
    vw, vh = 1080/z, 1920/z
    vx0, vy0 = int(cx-vw/2), int(cy-vh/2); vw_i, vh_i = int(math.ceil(vw))+2, int(math.ceil(vh))+2
    view = terreno(vx0, vy0, vw_i, vh_i)
    C = SC.count_at(t)
    objs = [o for o in objetos(t, C) if o[1] is not None]
    for (x, y, s) in people_list: objs.append((x+y+0.5, ('p', x, y, s)))
    # árvores do terreno de fora (só as que caem na janela)
    cs = [((vx0-OX)/2+(vy0-OY))/1, 0]
    corners = [(vx0, vy0), (vx0+vw_i, vy0), (vx0, vy0+vh_i), (vx0+vw_i, vy0+vh_i)]
    L = [(((X-OX)/2+(Y-OY))/2, ((Y-OY)-(X-OX)/2)/2) for X, Y in corners]
    lxs = [p[0] for p in L]; lys = [p[1] for p in L]
    for (x, y, k, r) in arvores_fora(min(lxs)-10, min(lys)-10, max(lxs)+10, max(lys)+40):
        im, ox_, oy_ = tree_var(k, r); X0, Y0 = PW(x, y)
        objs.append((x+y, (im, int(X0+ox_), int(Y0+oy_))))
    if extra: objs += extra
    objs.sort(key=lambda o: o[0])
    vd = ImageDraw.Draw(view, 'RGBA')
    for dep, o in objs:
        if o[0] == 'p':
            _, x, y, s = o; bx, by = PW(x, y)
            X, Y = int(bx-vx0), int(by-vy0)
            if -20 < X < vw_i+20 and -30 < Y < vh_i+20:
                vd.ellipse([X-4, Y-1, X+4, Y+2], fill=(0, 30, 0, 80)); view.alpha_composite(s, (X-6, Y-17)) if 0 <= X-6 and 0 <= Y-17 and X+6 < vw_i and Y+1 < vh_i else view.paste(s, (X-6, Y-17), s)
            continue
        if o[0] == 'fn':
            o[1](vd, vx0, vy0); continue
        im, bx, by = o
        X, Y = bx-vx0, by-vy0
        if X > vw_i or Y > vh_i or X+im.width < 0 or Y+im.height < 0: continue
        if pop is not None:
            s_ = pop(dep, bx, by)
            if s_ <= 0.01: continue
            if s_ < 0.999:
                nh = max(1, int(im.height*s_)); im2 = im.resize((im.width, nh), Image.NEAREST)
                view.paste(im2, (X, Y+im.height-nh), im2); continue
        view.paste(im, (X, Y), im)
    out = view.resize((int(vw_i*z), int(vh_i*z)), Image.NEAREST if z >= 1 else Image.BILINEAR)
    ox_, oy_ = int((cx-vw/2-vx0)*z), int((cy-vh/2-vy0)*z)
    return out.crop((ox_, oy_, ox_+1080, oy_+1920)).convert('RGB')

def imagem_completa(t, margem=40):
    """a cidade inteira em isométrico (sem moradores) + um pouco de campo em volta. Pro site."""
    x0 = int(PW(-margem, MH+margem)[0]); x1 = int(PW(MW+margem, -margem)[0])
    y0 = int(PW(-margem, -margem)[1])-90; y1 = int(PW(MW+margem, MH+margem)[1])+10
    w, h = x1-x0, y1-y0
    view = terreno(x0, y0, w, h)
    objs = [o for o in objetos(t, SC.count_at(t)) if o[1] is not None]
    L = [(-margem-20, -margem-20), (MW+margem+20, MH+margem+20)]
    for (x, y, k, r) in arvores_fora(-margem-20, -margem-20, MW+margem+20, MH+margem+20):
        im, ox_, oy_ = tree_var(k, r); X0, Y0 = PW(x, y)
        objs.append((x+y, (im, int(X0+ox_), int(Y0+oy_))))
    objs.sort(key=lambda o: o[0])
    for _, (im, bx, by) in objs: view.paste(im, (bx-x0, by-y0), im)
    return view.convert('RGB'), (OX-x0, OY-y0)
