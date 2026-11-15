# Visão em primeira pessoa (ep. 4): andando pela rua C, passando pela escola.
# Pseudo-3D estilo jogo antigo: o chão é o próprio mapa 16 bits "deitado" (mode 7)
# e as fachadas são os mesmos sprites das casas/escola em pé dos lados da rua.
import numpy as np, math, random
from PIL import Image, ImageDraw
from world import ROADC, clamp, smooth
from world16 import S, npc_sprite
import vila16 as V
from scene import T, house_lots, house_var, house_p, count_at, NH, ESCOLA, lot, escola_p, bell_swing

BW, BH = 270, 480            # buffer (vira 1080x1920)
F = 150.0; CAMH = 6.0; PXH = 0.45
ROADY = ROADC+5
U0, U1 = 222.0, 158.0        # anda de leste pra oeste
SKY_T, SKY_B = np.array([96, 150, 236]), np.array([196, 226, 250])
FOG = np.array([186, 214, 236])

def cam_u(t):
    a, b = T['fp']; f = clamp((t-a)/(b-a))
    return U0+(U1-U0)*f

_GROUND = None
def ground():
    global _GROUND
    if _GROUND is None:
        img, _ = V.static(False, False)
        _GROUND = np.array(img.convert('RGB'))
    return _GROUND

def buildings(t):
    C = count_at(t); out = []
    for i, l in enumerate(house_lots[:NH]):
        if l[1] != ROADC or house_p(i, C) < 1: continue
        x, y = lot(*l)
        side = 'R' if l[2] == 'a' else 'L'
        r = ROADY-(y+20.5) if side == 'R' else ROADY-y
        out.append(dict(u0=x, u1=x+21, r=r, side=side, spr=V.HOUSE(house_var[i], 1, False)))
        out[-1]['arr']=np.array(out[-1]['spr'])
    x, y = lot(*ESCOLA[0])
    out.append(dict(u0=x, u1=x+43, r=ROADY-(y+20.5), side='R', spr=V.ESC(escola_p(t), False, bell_swing(t), int(t*6)), escola=True))
    out[-1]['arr']=np.array(out[-1]['spr'])
    return out

KIDS = []
_r = random.Random(77)
for k in range(9):
    KIDS.append(dict(id=_r.randint(1, 400), u=_r.uniform(158, 184), r=_r.uniform(3.0, 6.0), sp=_r.uniform(1.5, 3.0), ph=_r.uniform(0, 6)))
WALKERS = [dict(id=_r.randint(1, 400), u=_r.uniform(150, 170), r=_r.choice([-4.5, 4.0]), ph=_r.uniform(0, 6)) for _ in range(2)]

def render_fp(t):
    a = np.zeros((BH, BW, 3), np.float32)
    uc = cam_u(t)
    bob = math.sin((t-T['fp'][0])*2*math.pi*2.2)*1.6
    hor = 196+bob
    # céu
    ys = np.arange(BH)[:, None]
    g = np.clip(ys/hor, 0, 1)
    a[:] = SKY_T[None, None, :]*(1-g[:, :, None])+SKY_B[None, None, :]*g[:, :, None]
    # nuvens
    for k in range(5):
        cx = (k*71+t*4) % (BW+60)-30; cy = 40+k*23
        for j in range(4):
            yy, xx = np.ogrid[:BH, :BW]
            m = ((xx-(cx+j*9))**2/(14+j*2)**2+(yy-cy-(j % 2)*3)**2/36) < 1
            a[m] = [250, 252, 255]
    # linha de árvores no horizonte
    xs = np.arange(BW)
    th = 9+4*np.sin(xs*0.21+1.3)+3*np.sin(xs*0.53)+2*np.sin(xs*1.7)
    for x in range(BW):
        y0 = int(hor-th[x]); a[max(0, y0):int(hor)+1, x] = [44, 104, 56]
        a[max(0, y0):max(0, y0)+2, x] = [70, 140, 70]
    # chão (mapa deitado)
    G = ground(); gh, gw = G.shape[:2]
    rows = np.arange(int(hor)+1, BH)
    z = F*CAMH/(rows-hor)
    rr = (xs[None, :]-BW/2)*z[:, None]/F
    U = uc-z[:, None]; Y = ROADY-rr
    px = np.clip((U*S).astype(int), 0, gw-1); py = np.clip((Y*S).astype(int), 0, gh-1)
    col = G[py, px].astype(np.float32)
    fog = np.clip((z-60)/160, 0, 0.75)[:, None, None]
    col = col*(1-fog)+FOG*fog
    a[int(hor)+1:] = col
    zbuf = np.full(BW, 1e9)
    # fachadas (planos dos dois lados da rua)
    B = buildings(t)
    for x in range(BW):
        dxs = x+0.5-BW/2
        if abs(dxs) < 0.5: continue
        side = 'R' if dxs > 0 else 'L'
        for b in B:
            if b['side'] != side: continue
            zz = F*b['r']/dxs
            if zz <= 0.4: continue
            u = uc-zz
            if not (b['u0'] <= u < b['u1']): continue
            spr = b['spr']; sw, sh_ = spr.size
            tc = int((u-b['u0'])/(b['u1']-b['u0'])*sw)
            if side == 'L': tc = sw-1-tc
            tc = min(sw-1, max(0, tc))
            colm = b['arr'][:, tc]
            ybot = hor+F*CAMH/zz
            hpx = F*PXH/zz            # tamanho de 1 px do sprite na tela
            base_row = 42
            y_top = ybot-base_row*hpx; y_end = ybot+(sh_-base_row)*hpx
            y0 = max(0, int(y_top)); y1 = min(BH, int(y_end)+1)
            if y1 <= y0: continue
            rws = ((np.arange(y0, y1)+0.5-y_top)/hpx).astype(int)
            ok = (rws >= 0) & (rws < sh_)
            px_ = colm[np.clip(rws, 0, sh_-1)]
            al = (px_[:, 3] > 0) & ok
            ff = clamp((zz-60)/160, 0, 0.75)
            cc = px_[:, :3].astype(np.float32)*(1-ff)+FOG*ff
            sel = np.arange(y0, y1)[al]
            if len(sel) and zz < zbuf[x]:
                a[sel, x] = cc[al]; zbuf[x] = zz
    # cache das colunas
    # moradores (billboards)
    tt = t-T['fp'][0]
    sprites = []
    for k in KIDS:
        u = k['u']
        rr_ = k['r']+min(tt*k['sp'], 10)            # andando pro pátio (pra direita)
        if rr_ > 8.0: continue
        sprites.append((uc-u, rr_, k['id'], 'right', int(t*8+k['ph']) % 4))
    for w in WALKERS:
        u = w["u"]-tt*14
        sprites.append((uc-u, w['r'], w['id'], 'up', int(t*8+w['ph']) % 4))
    sprites.sort(key=lambda s: -s[0])
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    for zz, r, pid, dr, fr in sprites:
        if zz < 14: continue
        sx = BW/2+F*r/zz
        h = F*8.1/zz
        if h < 2 or h > 400: continue
        s = V.NPC(pid, dr, fr)
        w_ = max(1, int(round(h*12/18))); h_ = max(1, int(round(h)))
        s2 = s.resize((w_, h_), Image.NEAREST)
        ybot = hor+F*CAMH/zz
        ix = int(sx-w_/2)
        # oclusão simples pelas fachadas
        img.paste(s2, (ix, int(ybot-h_*16/18)), s2)
    return img.resize((1080, 1920), Image.NEAREST)
