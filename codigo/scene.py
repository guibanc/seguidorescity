import numpy as np, random, math, json, os
from PIL import Image, ImageDraw
from world import *
from font import draw_text, text_width

# =====================================================================
#  EPISÓDIO 6  (577 -> 617 seguidores)
#  Casas 58-61 (rua D lota), marco 600 (2º mercadinho + posto de saúde),
#  o MAPA CRESCE pra baixo (480 -> 680, ruas E e F) e a cidade EVOLUI pro
#  isométrico (iso.py). Campo (700) reservado, aviso dos minigames.
#  Tempos sincronizados com a narração (narracao_ep6.wav, 74,8 s).
# =====================================================================
EP=6; C0=577; C1=617
MH6=680                                   # altura nova do mapa (largura continua 270)
T=dict(
    titulo=(0.0,6.1), recap=(6.1,10.9),        # "três lotes" 9.5
    cresce1=(10.9,15.2),       # casa 58 12.6 / 59 13.1 / 60 13.7 / 61 14.3
    marco=(15.2,20.8),         # 600 16.3 / mercadinho 18.6 / posto 19.6
    lotado=(20.8,24.3),        # onde? 21.1 / nenhum lote 22.4
    cresce=(24.3,30.8),        # cresceu 26.1 / pra baixo 27.2 / duas ruas 29.1
    evolui=(30.8,40.4),        # isométrica 33.2 / telhado 35.5 / lateral 38.1
    obras=(40.4,44.2),         # mercadinho 41.9 / posto 43.2
    casa62=(44.2,48.0),
    campo=(48.0,54.5),         # 700 48.3 / campo 49.8 / jogador 50.9
    prefeito=(54.5,59.3),      # prefeito 54.8 / chegando 56.7 / fica de olho 58.2
    minigame=(59.3,64.9),      # minigame 60.7 / jogar 63.0
    resumo=(64.9,71.1),        # 617 65.8 / 61 casas 67.6 / mapa 69.1 / visual 70.0
    cta=(71.1,77.0),           # controle 73.6
)
DUR=77.0
ISO_T=33.0                                 # a partir daqui o vídeo é isométrico

# ---------- contador ----------
CK=[(0,C0),(11.6,C0),(12.6,580),(13.1,590),(13.7,600),(14.3,610),(15.2,612),(16.3,615),(30.0,615),(46.3,C1)]
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

def interp(t,keys):
    if t<=keys[0][0]: return keys[0][1]
    for (a,va),(b,vb) in zip(keys,keys[1:]):
        if a<=t<b: return va+(vb-va)*(t-a)/(b-a)
    return keys[-1][1]

# ---------- lotes (os antigos nunca mudam de ordem; novos entram no fim) ----------
ROADD=420                                   # rua D (ep. 4): entre a rua A e a entrada
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
LOTS_D=[]
for i in range(5):
    for xs in (LX_L,LX_R):
        if i<len(xs):
            for side in ('a','b'):
                x=xs[i]
                if x==140 and side=='b': continue      # placa da entrada
                LOTS_D.append((x,ROADD,side))
lots=lots+LOTS_D
ROADE,ROADF=510,600                         # ep. 6: o mapa cresceu pra baixo
LOTS_EF=[]
for road in (ROADE,ROADF):
    for i in range(5):
        for xs in (LX_L,LX_R):
            if i<len(xs):
                for side in ('a','b'):
                    LOTS_EF.append((xs[i],road,side))
lots=lots+LOTS_EF
VENDA=(82,ROADB,'a'); MERCADO=(162,ROADB,'a')
ESCOLA=[(162,ROADC,'a'),(184,ROADC,'a')]    # marco 400 (construída no ep. 4)
PREFEITURA=[(140,ROADD,'a'),(162,ROADD,'a')]  # reservado p/ marco 500
MERCADO2=(104,ROADE,'a')                    # marco 600
POSTO=[(140,ROADE,'a'),(162,ROADE,'a')]     # marco 600
CAMPO=[(140,ROADF,'b'),(162,ROADF,'b'),(184,ROADF,'b'),(206,ROADF,'b')]   # reservado: marco 700
RESERV=[VENDA,MERCADO]+ESCOLA+PREFEITURA+[MERCADO2]+POSTO+CAMPO
house_lots=[l for l in lots if l not in RESERV]
NH=C1//10                                   # 61 casas
house_var=[(i*5+2)%6 for i in range(len(house_lots))]
def house_p(i,C): return clamp((C-(10*i+5))/5)
def house_done_time(i): return time_reach(10*(i+1))

# ---------- obras do episódio ----------
def escola_p(t): return 1.0
def bell_swing(t): return 0
def pile_n(t): return 0
def roadd_f(t): return 1.0
def stakes_f(t): return 1.0
def pref_p(t): return 1.0
def pave_f(t): return 1.0
def night_f(t): return 0.0
SHOW0=1e9; SHOWWIN=(1e9,1e9); STAGE=(0,0,0,0); BANDA=[]; PLATEIA=[]
def plateia_state(c,t): return None
GROW=(26.1,30.4)                            # mapa "desenrolando" pra baixo
def grow_f(t): return interp(t,[(GROW[0],0.0),(GROW[1],1.0)])
M2_KEYS=[(40.9,0.0),(41.9,0.3),(42.6,0.7),(43.3,1.0)]
PO_KEYS=[(41.6,0.0),(42.6,0.3),(43.3,0.7),(44.0,1.0)]
def merc2_p(t): return interp(t,M2_KEYS)
def posto_p(t): return interp(t,PO_KEYS)

# ---------- árvores ----------
trees=[]
tr=random.Random(7)
for _ in range(400):
    x=tr.randint(2,W-3); y=tr.randint(2,H-3)
    border = x<14 or y<62 or y>466 or (x>254) or (219<x<229)
    if y>466 and 112<x<152: continue
    if 228<=x<=254: continue
    if border: trees.append(dict(x=x,y=y,r=tr.choice([5,6,6,7]),k=tr.randint(0,1),chop=None))
trees.sort(key=lambda d:d['y'])
TREES6=[]                                   # árvores do mapa novo (680): as da borda antiga de baixo saem
tr6=random.Random(8)
for d_ in trees:
    if d_['y']<=466: TREES6.append(d_)
for _ in range(500):
    x=tr6.randint(2,W-3); y=tr6.randint(467,MH6-3)
    if 228<=x<=254: continue
    if not (x<14 or y>MH6-14 or x>254 or 219<x<229): continue
    if y>MH6-14 and 112<x<152: continue
    TREES6.append(dict(x=x,y=y,r=tr6.choice([5,6,6,7]),k=tr6.randint(0,1),chop=None))
TREES6.sort(key=lambda d:d['y'])

# ---------- moradores (mesmo sorteio dos eps. anteriores: ninguém muda de lugar) ----------
ROADSEG={'A':((16,ROADA+5),(217,ROADA+5)),'B':((16,ROADB+5),(217,ROADB+5)),
         'C':((16,ROADC+5),(217,ROADC+5)),'M1':((131.5,330),(131.5,470)),'M2':((131.5,112),(131.5,330)),
         'D':((16,ROADD+5),(217,ROADD+5)),'E':((16,ROADE+5),(217,ROADE+5)),'M3':((131.5,470),(131.5,670))}
pr=random.Random(42)
people=[]
for k in range(C1):
    ts=time_reach(k+1)
    d=dict(id=k+1,casa=k//10,ts=ts,skin=pr.choice(SKINS)+(255,),hair=pr.choice(HAIRS)+(255,),shirt=pr.choice(SHIRTS)+(255,),pants=pr.choice(PANTS)+(255,),
           sx=131.5+pr.uniform(-3,3),spd=pr.uniform(26,36),amp=pr.uniform(8,40),wspd=pr.uniform(5,12),ph=pr.uniform(0,6.28),off=pr.uniform(-3,3))
    if pr.random()<0.10: d['seg']='P'; d['tx']=pr.uniform(104,160); d['ty']=pr.uniform(216,272)
    else:
        if k<267: lst=list('AAAABBBC')+['M1','M2']
        elif k<320: lst=list('AAABBBCC')+['M1','M2']
        elif k<C0: lst=list('ABCCCC')+['M1','M2']
        else: lst=list('DDEE')+['M3']
        s=pr.choice(lst)
        d['seg']=s; (x0,y0),(x1,y1)=ROADSEG[s]; f=pr.uniform(0.05,0.95)
        d['tx']=x0+(x1-x0)*f; d['ty']=y0+(y1-y0)*f
    d['y0']=484 if k<C0 else MH6+4         # quem chega no ep. 6 vem pela entrada nova
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
    if d['seg'] in ('A','B','C','D','E','P'):
        if d['seg']!='P': ty=ty+d['off']
        pts=[(d['sx'],d['y0']),(131.5+d['off'],ty),(tx,ty)]
    else:
        tx=tx+d['off']; pts=[(d['sx'],d['y0']),(tx,ty)]
    L=plen(pts); dd=el*d['spd']
    if dd<L:
        (x,y),_=path_pos(pts,dd); return (x,y,True,None)
    tt=el-L/d['spd']
    if d['seg']=='P':
        return (tx+math.sin(tt*0.7+d['ph'])*2,ty,(int(tt*1.3+d['ph'])%4==0),None)
    s=d['amp']*math.sin(tt*d['wspd']/d['amp']+d['ph'])
    if d['seg'] in('A','B','C','D','E'): x,y=tx+s,ty
    else: x,y=tx,ty+s
    return (clamp(x,16,217),clamp(y,112,MH6-10),True,None)

SHOPPERS=[]
sr=random.Random(300)
for k in range(9):
    SHOPPERS.append(dict(skin=sr.choice(SKINS)+(255,),hair=sr.choice(HAIRS)+(255,),shirt=sr.choice(SHIRTS)+(255,),pants=sr.choice(PANTS)+(255,),
                         t0=-20+k*0.55,x0=sr.choice([60,100,131.5,200,215]),ph=sr.uniform(0,6),seed=9000+k))

# ---------- moradores registrados no site (nome + visual escolhido) ----------
_REGF=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','dados_do_site','registrados.json')
REG={}
if os.path.exists(_REGF):
    for r_ in json.load(open(_REGF,encoding='utf-8')):
        if r_['id']<=C1: REG[r_['id']]=r_

def lot_center(l,dy=16):
    x,y=lot(*l); return (x+10,y+dy)

def nome_tela(n):
    from font import G, ACC
    s_=''.join(c for c in n.upper() if c in G or c in ACC or c==' ')
    return ' '.join(s_.split())

# ---------- câmera 16 bits (até a virada pro isométrico) ----------
WIDE=(135,240,270)
CAM=[(0,(131,300,150)),(4.6,(131,300,150)),(6.1,WIDE),(8.2,WIDE),(9.0,(105,346,150)),(T['cresce1'][1],(105,346,150)),
     (T['marco'][0]+0.8,WIDE),(T['lotado'][1],WIDE),(T['cresce'][0]+0.6,(130,380,200)),(99,(130,380,200))]
def cam_at(t):
    for (a,va),(b,vb) in zip(CAM,CAM[1:]):
        if a<=t<b:
            f=smooth((t-a)/(b-a)); return tuple(va[i]+(vb[i]-va[i])*f for i in range(3))
    return CAM[-1][1]
def hour_at(t): return None
