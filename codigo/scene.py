import numpy as np, random, math, json, os
from PIL import Image, ImageDraw
from world import *
from font import draw_text, text_width

# =====================================================================
#  EPISÓDIO 9  (721 -> 780 seguidores) — 32 bits
#  Fogo no mercadinho do centro -> CORPO DE BOMBEIROS fundado; casas 73-78 (rua E fecha,
#  rua F começa); PETSHOP e a bicharada solta; campeonato no campo; eleição com 14
#  candidatos e VOTAÇÃO ABERTA; morador em destaque; terreno da padaria (marco 800) reservado.
#  Tempos sincronizados com a narração (narracao_ep9.wav).
# =====================================================================
EP=9; C0=721; C1=780
NOME_CIDADE="PINDAMONHANGABA"
MH6=680
from tempos_ep9 import T, KW, DUR
DUR_VIDEO=DUR
EVOL_T=1e9
SITE_CUTS=[]
def old2new(t): return t
def new2old(t): return t

# ---------- contador ----------
CK=None   # definido em tempos_ep9.py (CK)
from tempos_ep9 import CK
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
CAMPO=[(140,ROADF,'b'),(162,ROADF,'b'),(184,ROADF,'b'),(206,ROADF,'b')]   # marco 700 (pronto no ep. 8)
BOMBEIROS=(206,ROADF,'a')                   # ep. 9: corpo de bombeiros (era a casa 88 prevista)
PETSHOP=(16,ROADF,'a')                      # ep. 9: petshop (era a casa 89 prevista)
PADARIA=(16,ROADF,'b')                      # ep. 9: reservado p/ marco 800 (era a casa 90 prevista)
RESERV=[VENDA,MERCADO]+ESCOLA+PREFEITURA+[MERCADO2]+POSTO+CAMPO+[BOMBEIROS,PETSHOP,PADARIA]
house_lots=[l for l in lots if l not in RESERV]
NH=C1//10                                   # 78 casas
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
def grow_f(t): return 1.0
def merc2_p(t): return 1.0
def posto_p(t): return 1.0
# ---------- a placa nova (mutirão) ----------
PLACA_X0,PLACA_X1,PLACA_Y=121.0,143.0,466.0      # pórtico novo sobre a rua principal, na entrada
def placa_velha(t): return False            # a vazia sai quando o mutirão começa
def placa_estado(t):
    """(letras pintadas, ângulo 0=deitada..1=em pé) ou None antes de existir"""
    return (len(NOME_CIDADE),1.0)
def eleicao(t): return True                   # faixas "VOTE" na prefeitura
def campo_p(t): return 1.0                   # campo pronto desde o ep. 8
def merc_estado(t):
    """mercadinho do centro: ok -> fogo -> queimado -> ok (reformado)"""
    if t<KW['fogo0']: return 'ok'
    if t<KW['apagou']: return 'fogo'
    if t<KW['reforma']: return 'queimado'
    return 'ok'
def bomb_p(t): return clamp((t-KW['fundado'])/1.4)
def pet_p(t): return clamp((t-KW['petshop']+0.6)/1.0)
T_ATUAL=[0.0]

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
         'D':((16,ROADD+5),(217,ROADD+5)),'E':((16,ROADE+5),(217,ROADE+5)),'M3':((131.5,470),(131.5,670)),'F':((16,ROADF+5),(217,ROADF+5))}
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
        elif k<617: lst=list('ABCCCC')+['M1','M2']
        elif k<647: lst=list('DDEE')+['M3']
        elif k<721: lst=list('EEEE')+['M3']
        else: lst=list('EF')+['M3']
        s=pr.choice(lst)
        d['seg']=s; (x0,y0),(x1,y1)=ROADSEG[s]; f=pr.uniform(0.05,0.95)
        d['tx']=x0+(x1-x0)*f; d['ty']=y0+(y1-y0)*f
    d['y0']=484 if k<617 else MH6+4         # quem chega no ep. 6 vem pela entrada nova
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

def cam_at(t): return (135,240,270)
def hour_at(t): return None
