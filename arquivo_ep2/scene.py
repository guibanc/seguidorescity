import numpy as np, random, math, json, os
from PIL import Image, ImageDraw
from world import *
from font import draw_text, text_width

# =====================================================================
#  EPISÓDIO 2  (267 -> 320 seguidores, marco 300 = mercadinho)
#  Linha do tempo PROVISÓRIA: quando a narração chegar, só ajustar T{}
# =====================================================================
EP=2; C0=267; C1=320
T=dict(
    titulo=(0.2,3.9), recap=(4.0,10.4),
    h27=(10.5,15.0),           # "ficou pronta!" ~14.3
    cresce=(15.1,20.9),        # 270->295
    quase=(21.0,23.8),         # "bateu trezentos" -> 300 em ~23.4
    desbloq=(23.8,27.6),
    obra=(27.6,35.1),          # fundação 29.2 / parede 30.3 / telhado 31.2 / toldo 32.2 / prateleira 33.2
    clientes=(35.1,38.2),
    ruac=(38.3,46.6),          # "passou da praça" 43.4
    resumo=(46.7,52.6),        # moradores 47.8 / casas 49.7 / mercadinho 51.2
    proximo=(52.7,58.9),       # "uma escola!" 57.3
    nome=(59.0,68.3),          # "comenta lá" 63.8
    cta=(68.4,72.0),
)
DUR=72.0

# ---------- contador ----------
CK=[(0,C0),(12.0,C0),(14.3,270),(15.3,270),(20.6,295),(21.4,295),(23.4,300),(38.6,300),(44.5,C1)]
def count_at(t):
    if t>=CK[-1][0]: return CK[-1][1]
    if t<CK[0][0]: return C0
    for (a,va),(b,vb) in zip(CK,CK[1:]):
        if a<=t<b:
            f=(t-a)/(b-a) if b>a else 1
            return int(va+(vb-va)*f)
    return C1
def time_reach(n):
    if n<=C0: return -100.0
    lo,hi=0,DUR
    if count_at(hi)<n: return None
    for _ in range(40):
        m=(lo+hi)/2
        if count_at(m)>=n: hi=m
        else: lo=m
    return hi

# ---------- lotes ----------
LX_L=[104,82,60,38,16]; LX_R=[140,162,184,206]
def lot(x,road,side):
    return (x-1, road-24 if side=='a' else road+12)
lots=[]
for road in (ROADA,ROADB,ROADC):
    for i in range(5):
        for xs in (LX_L,LX_R):
            if i<len(xs):
                for side in ('a','b'):
                    x=xs[i]
                    if road==ROADB and x in (104,140): continue
                    lots.append((x,road,side))
VENDA=(82,ROADB,'a'); MERCADO=(162,ROADB,'a')
ESCOLA=[(162,ROADC,'a'),(184,ROADC,'a')]   # reservado p/ marco 400 (2 lotes)
RESERV=[VENDA,MERCADO]+ESCOLA
house_lots=[l for l in lots if l not in RESERV]
NH=C1//10                                   # 32 casas
house_var=[(i*5+2)%6 for i in range(len(house_lots))]
def house_p(i,C): return clamp((C-(10*i+5))/5)
def house_done_time(i): return time_reach(10*(i+1))
T300=time_reach(300)
MP=[(29.2,0.0),(30.3,0.2),(31.2,0.5),(32.2,0.85),(33.2,0.99),(33.9,1.0)]
def mercado_p(t):
    if t<MP[0][0]: return 0.0 if t<T['obra'][0] else 0.001
    for (a,va),(b,vb) in zip(MP,MP[1:]):
        if a<=t<b: return va+(vb-va)*(t-a)/(b-a)
    return 1.0

# ---------- árvores (só as da borda; o miolo já foi cortado no ep. 1) ----------
trees=[]
tr=random.Random(7)
for _ in range(400):
    x=tr.randint(2,W-3); y=tr.randint(2,H-3)
    border = x<14 or y<62 or y>466 or (x>254) or (219<x<229)
    if y>466 and 112<x<152: continue
    if 228<=x<=254: continue
    if border: trees.append(dict(x=x,y=y,r=tr.choice([5,6,6,7]),k=tr.randint(0,1),chop=None))
trees.sort(key=lambda d:d['y'])
TREE_SPR={}
def tree_img(r,k):
    if (r,k) not in TREE_SPR: TREE_SPR[(r,k)]=tree_sprite(r,k,r*10+k)
    return TREE_SPR[(r,k)]

# ---------- moradores ----------
ROADSEG={'A':((16,ROADA+5),(217,ROADA+5)),'B':((16,ROADB+5),(217,ROADB+5)),
         'C':((16,ROADC+5),(217,ROADC+5)),'M1':((131.5,330),(131.5,470)),'M2':((131.5,112),(131.5,330))}
pr=random.Random(42)
people=[]
for k in range(C1):
    ts=time_reach(k+1)
    d=dict(ts=ts,skin=pr.choice(SKINS)+(255,),hair=pr.choice(HAIRS)+(255,),shirt=pr.choice(SHIRTS)+(255,),pants=pr.choice(PANTS)+(255,),
           sx=131.5+pr.uniform(-3,3),spd=pr.uniform(26,36),amp=pr.uniform(8,40),wspd=pr.uniform(5,12),ph=pr.uniform(0,6.28),off=pr.uniform(-3,3))
    if pr.random()<0.10: d['seg']='P'; d['tx']=pr.uniform(104,160); d['ty']=pr.uniform(216,272)
    else:
        s=pr.choice(list('AAABBBCC')+['M1','M2'] if k>=C0 else list('AAAABBBC')+['M1','M2'])
        d['seg']=s; (x0,y0),(x1,y1)=ROADSEG[s]; f=pr.uniform(0.05,0.95)
        d['tx']=x0+(x1-x0)*f; d['ty']=y0+(y1-y0)*f
    people.append(d)

def path_pos(pts,dist):
    for (a,b) in zip(pts,pts[1:]):
        L=math.hypot(b[0]-a[0],b[1]-a[1])
        if dist<=L:
            f=dist/L if L else 0; return (a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f),False
        dist-=L
    return pts[-1],True
def plen(pts): return sum(math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(pts,pts[1:]))

def person_state(d,t):
    if d['ts'] is None or t<d['ts']: return None
    el=t-d['ts']
    tx,ty=d['tx'],d['ty']
    if d['seg'] in ('A','B','C','P'):
        if d['seg']!='P': ty=ty+d['off']
        pts=[(d['sx'],484),(131.5+d['off'],ty),(tx,ty)]
    else:
        tx=tx+d['off']; pts=[(d['sx'],484),(tx,ty)]
    L=plen(pts); dd=el*d['spd']
    if dd<L:
        (x,y),_=path_pos(pts,dd); return (x,y,True,None)
    tt=el-L/d['spd']
    if d['seg']=='P':
        return (tx+math.sin(tt*0.7+d['ph'])*2,ty,(int(tt*1.3+d['ph'])%4==0),None)
    s=d['amp']*math.sin(tt*d['wspd']/d['amp']+d['ph'])
    if d['seg'] in('A','B','C'): x,y=tx+s,ty
    else: x,y=tx,ty+s
    return (clamp(x,16,217),clamp(y,112,470),True,None)

# clientes do mercadinho: saem da praça/rua, entram, saem com sacola
SHOPPERS=[]
sr=random.Random(300)
for k in range(9):
    SHOPPERS.append(dict(skin=sr.choice(SKINS)+(255,),hair=sr.choice(HAIRS)+(255,),shirt=sr.choice(SHIRTS)+(255,),pants=sr.choice(PANTS)+(255,),
                         t0=T['obra'][1]+0.2+k*0.55,x0=sr.choice([60,100,131.5,200,215]),ph=sr.uniform(0,6)))

PSPR={}
def pimg(d,frame,tool=None,log=False):
    key=(d['skin'],d['hair'],d['shirt'],d['pants'],frame,tool,log)
    if key not in PSPR: PSPR[key]=person_sprite(d['skin'],d['hair'],d['shirt'],d['pants'],frame,tool,log)
    return PSPR[key]
WORKERS=[dict(skin=SKINS[i%5]+(255,),hair=HAIRS[i%6]+(255,),shirt=[(240,130,40),(60,110,220),(220,60,60),(70,170,90)][i%4]+(255,),pants=(60,60,80,255)) for i in range(6)]

# ---------- câmera ----------
WIDE=(135,240,270)
def lot_center(l,dy=16):
    x,y=lot(*l); return (x+10,y+dy)
_h27=lot_center(house_lots[26],20); _m=lot_center(MERCADO); _c=(122,168); _e=lot_center(ESCOLA[0]); _s=(149,446)
CAM=[(0,(131,300,150)),(T['recap'][0],(131,300,150)),(T['recap'][1]-0.6,WIDE),
     (T['h27'][0],(_h27[0],_h27[1],96)),(T['h27'][1],(_h27[0],_h27[1],96)),
     (T['cresce'][0]+0.4,WIDE),(T['quase'][1],WIDE),
     (T['desbloq'][1],(_m[0],_m[1],140)),(T['obra'][0]+0.3,(_m[0],_m[1],96)),(T['obra'][1],(_m[0],_m[1],96)),
     (T['clientes'][0]+0.8,(150,245,140)),(T['clientes'][1],(150,245,140)),
     (T['ruac'][0]+0.8,(_c[0],_c[1],150)),(T['ruac'][1],(_c[0],_c[1],150)),
     (T['resumo'][0]+0.8,WIDE),(T['resumo'][1],WIDE),
     (T['proximo'][0]+0.8,(_e[0]+10,_e[1],130)),(T['proximo'][1],(_e[0]+10,_e[1],130)),
     (T['nome'][0]+0.8,(_s[0],_s[1]-20,110)),(T['nome'][1],(_s[0],_s[1]-20,110)),
     (T['cta'][0]+0.6,WIDE),(99,WIDE)]
def cam_at(t,targets=None):
    for (a,va),(b,vb) in zip(CAM,CAM[1:]):
        if a<=t<b:
            f=smooth((t-a)/(b-a)); return tuple(va[i]+(vb[i]-va[i])*f for i in range(3))
    return CAM[-1][1]
