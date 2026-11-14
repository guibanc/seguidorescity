import numpy as np, random, math
from PIL import Image, ImageDraw
W,H=270,480
rng=random.Random(267)
MAINX0,MAINX1=127,136
ROADA,ROADB,ROADC=330,240,150

def clamp(x,a=0,b=1): return max(a,min(b,x))
def smooth(x): x=clamp(x); return x*x*(3-2*x)

# ---------------- base: grama + rio ----------------
def river_x(y): return 238+6*math.sin(y/40.0)
def make_base():
    a=np.zeros((H,W,3),np.uint8)
    G1=np.array([92,168,72]);G2=np.array([80,152,64]);G3=np.array([108,182,82])
    a[:]=G1
    r=np.random.RandomState(1)
    n=r.rand(H,W)
    a[n<0.12]=G2; a[n>0.9]=G3
    # tufos
    for _ in range(900):
        x,y=r.randint(1,W-2),r.randint(1,H-2)
        a[y,x]=[62,130,54]; a[y-1,x-1]=[70,140,58]; a[y-1,x+1]=[70,140,58]
    # florzinhas
    for _ in range(160):
        x,y=r.randint(0,W),r.randint(0,H)
        if x<W and y<H:
            a[y,x]=[[244,236,120],[240,150,170],[250,250,250],[180,160,240]][r.randint(0,4)]
    river=np.zeros((H,W),bool); bank=np.zeros((H,W),bool)
    for y in range(H):
        c=river_x(y)
        for x in range(W):
            d=abs(x-c)
            if d<7: river[y,x]=True
            elif d<9: bank[y,x]=True
    a[bank]=[206,190,128]
    a[river]=[60,120,200]
    # borda mais escura da água
    for y in range(H):
        c=river_x(y)
        for x in range(W):
            if 5.5<abs(x-c)<7: a[y,x]=[48,100,176]
    return a,river

# ---------------- camadas de chão (ruas/praça) ----------------
DIRT=np.array([178,134,86]);DIRT2=np.array([156,112,70]);PEB=np.array([200,166,118])
COB1=np.array([184,176,160]);COB2=np.array([156,148,136])
def road_layer(x0,y0,x1,y1,mode):
    lay=np.zeros((H,W,4),np.uint8); order=np.full((H,W),9.0)
    r=np.random.RandomState(x0*7+y0)
    for y in range(y0,y1):
        for x in range(x0,x1):
            c=DIRT.copy()
            edge = (x in (x0,x1-1)) if mode in('up',) else (y in (y0,y1-1))
            if edge: c=DIRT2
            elif r.rand()<0.07: c=PEB
            elif r.rand()<0.05: c=DIRT2
            lay[y,x,:3]=c; lay[y,x,3]=255
            if mode=='up': order[y,x]=(y1-y)/(y1-y0)
            else: order[y,x]=abs(x-131.5)/max(131.5-x0,x1-131.5)
    return lay,order
def plaza_layer(x0,y0,x1,y1):
    lay=np.zeros((H,W,4),np.uint8); order=np.full((H,W),9.0)
    r=np.random.RandomState(5)
    for y in range(y0,y1):
        for x in range(x0,x1):
            c = COB2 if ((x//3+y//3)%2==0 and (x%3==0 or y%3==0)) else COB1
            if x in(x0,x1-1) or y in (y0,y1-1): c=np.array([120,112,104])
            lay[y,x,:3]=c; lay[y,x,3]=255
            order[y,x]=r.rand()*0.6+0.4*(abs(x-131.5)+abs(y-244.5))/80
    return lay,order

LAYERS=[]  # (layer, order, t0, t1)
def build_layers():
    L=[]
    l,o=road_layer(MAINX0,240,MAINX1+1,480,'up'); L.append((l,o,24.4,27.2))
    l,o=road_layer(14,ROADA,219,ROADA+10,'h'); L.append((l,o,26.6,29.6))
    l,o=road_layer(MAINX0,104,MAINX1+1,240,'up'); L.append((l,o,43.9,44.7))
    l,o=road_layer(14,ROADB,219,ROADB+10,'h'); L.append((l,o,43.95,44.8))
    l,o=road_layer(14,ROADC,219,ROADC+10,'h'); L.append((l,o,44.2,45.0))
    l,o=plaza_layer(100,213,164,277); L.append((l,o,44.8,45.6))
    return L

# ---------------- sprites ----------------
def tree_sprite(r,kind,seed):
    rr=random.Random(seed)
    w=2*r+5; h=2*r+6
    im=Image.new('RGBA',(w,h),(0,0,0,0)); p=im.load()
    cx,cy=r+1,r+1
    # sombra
    for y in range(h):
        for x in range(w):
            if ((x-cx-2)/(r+0.5))**2+((y-cy-3)/(r*0.8))**2<1: p[x,y]=(20,50,20,90)
    # tronco
    for y in range(cy+r-1,cy+r+2):
        p[cx,y]=(96,64,40,255); p[cx+1,y]=(76,50,32,255)
    pal=[(28,86,44),(44,116,54),(64,148,66),(104,184,86)] if kind==0 else [(30,90,64),(42,120,80),(60,150,96),(110,190,120)]
    for y in range(h):
        for x in range(w):
            d=math.hypot(x-cx,y-cy)
            if d<=r+0.3:
                s=(x-cx)+(y-cy)
                if d>r-0.8: c=pal[0]
                elif s<-r*0.7: c=pal[3]
                elif s<-r*0.1: c=pal[2]
                elif s<r*0.6: c=pal[1]
                else: c=pal[0]
                if rr.random()<0.12 and d<r-1: c=pal[min(3,pal.index(c)+1)] if c!=pal[3] else pal[2]
                p[x,y]=c+(255,)
    return im,(cx,cy+r+1)  # anchor = base

ROOFS=[((196,64,56),(150,44,40),(226,104,88)),((64,96,176),(44,68,136),(104,140,210)),
       ((72,140,80),(48,104,58),(110,180,110)),((212,128,56),(166,94,36),(240,168,96)),
       ((128,80,160),(94,58,124),(170,124,200)),((160,96,60),(120,70,44),(196,136,96))]
WALLS=[(236,220,180),(244,240,232),(214,190,150),(230,206,170)]
def house_sprite(var,p,lit=False,venda=False):
    # 20x24: chaminé linhas 0-3, telhado 3-13, parede 14-20, sombra
    im=Image.new('RGBA',(21,25),(0,0,0,0)); d=ImageDraw.Draw(im)
    rc,rd,rl=ROOFS[var%len(ROOFS)]; wc=WALLS[(var//2)%len(WALLS)]
    OX,RY,WY=1,3,14
    if p<=0: return im
    # lote/estacas
    if p<1:
        for (x,y) in [(OX,RY),(OX+17,RY),(OX,WY+6),(OX+17,WY+6)]: d.point((x,y),fill=(120,80,40,255))
    if p<0.25:
        f=p/0.25
        for x in range(OX,OX+18,2):
            d.point((x,RY),fill=(250,250,250,200)); d.point((x,WY+6),fill=(250,250,250,200))
        for y in range(RY,WY+7,2):
            d.point((OX,y),fill=(250,250,250,200)); d.point((OX+17,y),fill=(250,250,250,200))
        n=int(f*18)
        if n>0: d.rectangle([OX,RY+1,OX+n-1,WY+6],fill=(150,150,156,255))
        for x in range(OX,OX+n,3): d.point((x,RY+5),fill=(124,124,130,255)); d.point((x+1,RY+10),fill=(124,124,130,255))
        return im
    # fundação pronta
    d.rectangle([OX+1,RY+1,OX+16,WY+6],fill=(150,150,156,255))
    d.rectangle([OX+2,RY+2,OX+15,WY-1],fill=(168,124,80,255))  # piso de madeira
    for y in range(RY+3,WY,2): d.line([OX+2,y,OX+15,y],fill=(146,104,66,255))
    if p<0.6:
        f=(p-0.25)/0.35
        # postes da estrutura
        for x in (OX+1,OX+16,OX+8):
            d.line([x,RY+1,x,WY+6],fill=(110,70,36,255))
        hh=int(round(f*7))
        if hh>0: d.rectangle([OX+1,WY+7-hh,OX+16,WY+6],fill=wc+(255,))
        d.line([OX+1,RY+1,OX+16,RY+1],fill=(110,70,36,255))
        return im
    # parede completa
    d.rectangle([OX+1,WY,OX+16,WY+6],fill=wc+(255,))
    d.line([OX+1,WY+6,OX+16,WY+6],fill=tuple(int(c*0.75) for c in wc)+(255,))
    d.rectangle([OX+7,WY+2,OX+10,WY+6],fill=(110,66,36,255)); d.point((OX+9,WY+4),fill=(240,200,80,255))
    win=(255,214,100,255) if lit else (120,170,224,255)
    for wx in (OX+3,OX+13):
        d.rectangle([wx,WY+2,wx+1,WY+3],fill=win)
        if not lit: d.point((wx,WY+2),fill=(230,240,255,255))
    if venda:
        for x in range(OX,OX+18): d.line([x,WY,x,WY+1],fill=(220,50,50,255) if (x//2)%2 else (250,250,250,255))
        for i,c in enumerate([(230,60,50),(250,200,40),(90,190,70)]): d.point((OX+2+i*2,WY+7),fill=c+(255,)); d.point((OX+12+i*2,WY+7),fill=c+(255,))
    f=clamp((p-0.6)/0.4)
    rows=int(math.ceil(f*11)) if f<1 else 11
    # caibros onde ainda não tem telha
    for x in range(OX+1,OX+17,3): d.line([x,RY,x,WY-1],fill=(120,80,44,255))
    for k in range(rows):
        y=WY-1-k
        d.line([OX,y,OX+17,y],fill=rc+(255,))
        if (y-RY)%2==0:
            for x in range(OX+(y%4)//2,OX+18,2): d.point((x,y),fill=rd+(255,))
    if rows==11:
        d.line([OX,RY,OX+17,RY],fill=rl+(255,)); d.line([OX,RY+1,OX+17,RY+1],fill=rl+(255,))
        d.line([OX,RY,OX,WY-1],fill=rd+(255,)); d.line([OX+17,RY,OX+17,WY-1],fill=rd+(255,))
        d.line([OX,WY-1,OX+17,WY-1],fill=rd+(255,))
        # chaminé
        d.rectangle([OX+12,RY-3,OX+14,RY+2],fill=(140,130,128,255)); d.line([OX+12,RY-3,OX+14,RY-3],fill=(90,84,84,255))
    # sombra
    for y in range(RY+2,WY+8): im.putpixel((OX+18,y),(0,0,0,70))
    for x in range(OX+1,OX+19): im.putpixel((x,WY+7),(0,0,0,70)) if im.getpixel((x,WY+7))[3]==0 else None
    return im

def church_sprite(p,lit=False):
    im=Image.new('RGBA',(34,46),(0,0,0,0)); d=ImageDraw.Draw(im)
    if p<=0: return im
    OX,RY,WY=1,12,30
    rc,rd,rl=(84,96,140),(60,70,108),(120,134,180)
    if p<0.35:
        n=int(p/0.35*30)
        d.rectangle([OX,RY,OX+n,WY+12],fill=(150,150,156,255)); return im
    d.rectangle([OX+1,WY,OX+29,WY+12],fill=(236,232,224,255))
    hh=int(clamp((p-0.35)/0.3)*13)
    if p<0.65:
        d.rectangle([OX,RY,OX+30,WY+12],fill=(150,150,156,255))
        d.rectangle([OX+1,WY+12-hh,OX+29,WY+12],fill=(236,232,224,255)); return im
    d.rectangle([OX+12,WY+4,OX+17,WY+12],fill=(110,66,36,255)); d.line([OX+13,WY+3,OX+16,WY+3],fill=(110,66,36,255))
    gl=[(255,214,100)]*3 if lit else [(220,80,80),(80,140,230),(240,210,80)]
    for i,wx in enumerate((OX+4,OX+23)):
        d.rectangle([wx,WY+4,wx+2,WY+8],fill=gl[i]+(255,))
    rows=int(clamp((p-0.65)/0.35)*18)
    for k in range(rows):
        y=WY-1-k; d.line([OX,y,OX+30,y],fill=rc+(255,))
        if y%2==0:
            for x in range(OX+(y%4)//2,OX+31,2): d.point((x,y),fill=rd+(255,))
    if p>=1:
        # torre
        d.rectangle([OX+11,RY-8,OX+19,RY+8],fill=(230,226,218,255)); d.rectangle([OX+11,RY-8,OX+19,RY-6],fill=rl+(255,))
        d.rectangle([OX+13,RY-3,OX+17,RY+2],fill=(60,52,48,255)); d.point((OX+15,RY),fill=(230,190,60,255))
        d.line([OX+15,0,OX+15,RY-9],fill=(250,230,120,255)); d.line([OX+13,2,OX+17,2],fill=(250,230,120,255))
        for y in range(RY,WY+13): im.putpixel((OX+31,y),(0,0,0,70))
    return im

def person_sprite(skin,hair,shirt,pants,frame,tool=None,log=False):
    im=Image.new('RGBA',(6,8),(0,0,0,0)); p=im.load()
    o=1
    p[o+1,1]=hair; p[o,1]=(0,0,0,0)
    p[o,2]=hair; p[o+1,2]=skin; p[o+2,2]=hair
    p[o,3]=skin; p[o+1,3]=shirt; p[o+2,3]=skin
    p[o+1,4]=shirt; p[o,4]=shirt; p[o+2,4]=shirt
    if frame==0: p[o,5]=pants; p[o+2,5]=pants
    else: p[o+1,5]=pants
    p[o,6]=(0,0,0,70); p[o+1,6]=(0,0,0,70); p[o+2,6]=(0,0,0,70)
    if tool=='up': p[o+3,2]=(170,170,180,255); p[o+3,3]=(120,80,40,255)
    elif tool=='down': p[o+3,4]=(120,80,40,255); p[o+4,4]=(170,170,180,255)
    if log:
        for x in range(0,5): p[x,0]=(140,92,52,255)
        p[0,0]=(200,160,110,255)
    return im
SKINS=[(244,204,170),(222,172,128),(184,126,84),(140,90,58),(104,64,40)]
HAIRS=[(40,28,20),(90,56,30),(200,160,80),(20,20,24),(140,60,30),(200,200,200)]
SHIRTS=[(220,60,60),(60,110,220),(250,210,60),(70,170,90),(240,240,240),(160,80,200),(240,130,40),(40,180,190),(230,110,160)]
PANTS=[(50,60,100),(70,50,40),(40,40,48),(100,100,110)]

# ---------------- mercadinho (ep. 2, marco 300) ----------------
def mercado_sprite(p,lit=False):
    """21x25 como as casas. p: 0..1 (fundação, paredes, telhado, toldo, placa)"""
    im=Image.new('RGBA',(21,25),(0,0,0,0)); d=ImageDraw.Draw(im)
    OX,RY,WY=1,3,14
    if p<=0: return im
    if p<1:
        for (x,y) in [(OX,RY),(OX+17,RY),(OX,WY+6),(OX+17,WY+6)]: d.point((x,y),fill=(120,80,40,255))
    if p<0.2:
        n=int(p/0.2*18)
        for x in range(OX,OX+18,2):
            d.point((x,RY),fill=(250,250,250,200)); d.point((x,WY+6),fill=(250,250,250,200))
        if n>0: d.rectangle([OX,RY+1,OX+n-1,WY+6],fill=(150,150,156,255))
        return im
    d.rectangle([OX+1,RY+1,OX+16,WY+6],fill=(150,150,156,255))
    d.rectangle([OX+2,RY+2,OX+15,WY-1],fill=(210,206,196,255))  # piso claro
    for y in range(RY+3,WY,3):
        for x in range(OX+2,OX+16,3): d.point((x,y),fill=(186,182,172,255))
    WALL=(250,236,190)
    if p<0.5:
        f=(p-0.2)/0.3
        for x in (OX+1,OX+16,OX+8):
            d.line([x,RY+1,x,WY+6],fill=(110,110,118,255))
        hh=int(round(f*7))
        if hh>0: d.rectangle([OX+1,WY+7-hh,OX+16,WY+6],fill=WALL+(255,))
        return im
    # fachada
    d.rectangle([OX+1,WY,OX+16,WY+6],fill=WALL+(255,))
    d.line([OX+1,WY+6,OX+16,WY+6],fill=(196,180,140,255))
    glass=(255,214,100,255) if lit else (140,196,236,255)
    d.rectangle([OX+2,WY+2,OX+5,WY+5],fill=glass); d.rectangle([OX+12,WY+2,OX+15,WY+5],fill=glass)
    if not lit: d.point((OX+2,WY+2),fill=(235,245,255,255)); d.point((OX+12,WY+2),fill=(235,245,255,255))
    d.rectangle([OX+7,WY+2,OX+10,WY+6],fill=(70,80,92,255))
    d.rectangle([OX+8,WY+3,OX+9,WY+6],fill=glass)
    # telhado plano (visto de cima)
    f=clamp((p-0.5)/0.3)
    rows=int(math.ceil(f*11)) if f<1 else 11
    for x in range(OX+1,OX+17,4): d.line([x,RY,x,WY-1],fill=(130,130,138,255))
    for k in range(rows):
        y=WY-1-k
        d.line([OX,y,OX+17,y],fill=(196,192,184,255))
        if y%3==0: d.line([OX+1,y,OX+16,y],fill=(184,180,172,255))
    if rows==11:
        d.rectangle([OX,RY,OX+17,WY-1],outline=(150,146,140,255))
        d.rectangle([OX+3,RY+5,OX+5,RY+7],fill=(170,174,180,255)); d.point((OX+4,RY+6),fill=(110,114,120,255))  # ar-condicionado
    # toldo verde e branco
    if p>=0.85:
        for x in range(OX,OX+18):
            c=(46,150,70,255) if (x//2)%2 else (250,250,250,255)
            d.line([x,WY,x,WY+1],fill=c)
        d.line([OX,WY+1,OX+17,WY+1],fill=(30,110,50,255)) if False else None
    # placa no telhado + caixotes de fruta
    if p>=1:
        d.rectangle([OX+5,RY+1,OX+12,RY+4],fill=(214,52,48,255)); d.rectangle([OX+5,RY+1,OX+12,RY+4],outline=(150,30,30,255))
        # carrinho de compras
        for x in range(OX+7,OX+11): d.point((x,RY+2),fill=(255,255,255,255))
        d.point((OX+7,RY+3),fill=(255,255,255,255)); d.point((OX+10,RY+3),fill=(255,255,255,255))
        d.point((OX+6,RY+2),fill=(255,255,255,255))
        for cx,cols in ((OX+1,[(240,140,40),(230,60,50)]),(OX+13,[(90,190,70),(250,210,60)])):
            d.rectangle([cx,WY+7,cx+3,WY+8],fill=(140,96,56,255))
            for j in range(4): d.point((cx+j,WY+7),fill=cols[j%2]+(255,))
        for y in range(RY+2,WY+8): im.putpixel((OX+18,y),(0,0,0,70))
    return im
