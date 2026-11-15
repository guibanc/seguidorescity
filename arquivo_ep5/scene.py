import numpy as np, random, math, json, os
from PIL import Image, ImageDraw
from world import *
from font import draw_text, text_width

# =====================================================================
#  EPISÓDIO 5  (460 -> 577 seguidores)
#  Casas 47-58 na rua D, PREFEITURA (marco 500), ruas calçadas (vira
#  cidadezinha), teaser do prefeito/nome, domingo à noite: show na praça.
#  Tempos sincronizados com a narração (narracao_ep5.wav, 75,9 s).
# =====================================================================
EP=5; C0=460; C1=577
T=dict(
    titulo=(0.0,3.2), recap=(3.2,9.7),       # "rua nova esperando gente" 7.8
    cresce1=(9.7,15.9),        # casa 47 12.2 / 48 13.2 / 49 14.0
    quase=(15.9,18.3),         # "chegou em quinhentos" 16.1-17.8
    pref=(18.3,25.5),          # PREFEITURA 19.4 / fundação 21.0 / colunas 21.8 / relógio 22.6 / bandeiras 24.1
    calc=(25.5,30.6),          # "ruas de terra viraram paralelepípedo" 27.1-29.0 / calçada 29.1
    cidadezinha=(30.6,33.8),   # cidadezinha 32.3
    cresce2=(33.8,38.6),       # sete casas 34.7 / casa 58 em obra 36.4
    prefeito=(38.6,46.1),      # prefeito 40.8 / nome da cidade 43.0 / fica atento 45.1
    domingo=(46.1,49.4),       # domingo 46.3 / show na praça 47.4
    show=(49.4,55.6),          # palco 49.7 / banda 50.5 / luz 51.6 / dançando 52.7
    resumo=(55.6,62.1),        # 577 56.7 / 57 casas 58.8 / prefeitura 60.2 / calçadas 60.9
    proximo=(62.1,66.7),       # faltam 23 62.3 / mercadinho 64.5 / posto 65.6
    mapa=(66.7,71.1),          # quase cheia 67.0 / fora do mapa 68.9
    cta=(71.1,78.0),           # prefeito: você? 73.9
)
DUR=78.0

# ---------- contador ----------
CK=[(0,C0),(10.0,C0),(12.6,470),(13.5,480),(14.4,490),(15.4,495),(17.0,499),(17.6,500),(34.3,500),(36.3,575),(37.5,C1)]
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
VENDA=(82,ROADB,'a'); MERCADO=(162,ROADB,'a')
ESCOLA=[(162,ROADC,'a'),(184,ROADC,'a')]    # marco 400 (construída no ep. 4)
PREFEITURA=[(140,ROADD,'a'),(162,ROADD,'a')]  # reservado p/ marco 500
RESERV=[VENDA,MERCADO]+ESCOLA+PREFEITURA
house_lots=[l for l in lots if l not in RESERV]
NH=C1//10                                   # 57 casas
house_var=[(i*5+2)%6 for i in range(len(house_lots))]
def house_p(i,C): return clamp((C-(10*i+5))/5)
def house_done_time(i): return time_reach(10*(i+1))

# ---------- obras do episódio ----------
def escola_p(t): return 1.0                 # pronta desde o ep. 4
def bell_swing(t): return 0
def pile_n(t): return 0                     # a pilha virou a rua D
def roadd_f(t): return 1.0
def stakes_f(t): return 1.0
PREF_KEYS=[(18.6,0.0),(21.0,0.2),(21.7,0.6),(22.3,0.85),(24.1,0.93),(25.0,1.0)]
def pref_p(t): return 0.0 if t<18.6 else interp(t,PREF_KEYS)
PAVE=(27.1,29.9)                            # calçamento se espalhando a partir da prefeitura
def pave_f(t): return interp(t,[(PAVE[0],0.0),(PAVE[1],1.0)])
def night_f(t): return interp(t,[(46.3,0.0),(47.9,1.0)])
SHOW0=49.7                                  # palco aparece

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

# ---------- moradores (mesmo sorteio dos eps. anteriores: ninguém muda de lugar) ----------
ROADSEG={'A':((16,ROADA+5),(217,ROADA+5)),'B':((16,ROADB+5),(217,ROADB+5)),
         'C':((16,ROADC+5),(217,ROADC+5)),'M1':((131.5,330),(131.5,470)),'M2':((131.5,112),(131.5,330))}
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
        else: lst=list('ABCCCC')+['M1','M2']
        s=pr.choice(lst)
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

# ---------- domingo à noite: show na praça ----------
SHOWWIN=(46.35,55.8)             # janela em que só a plateia aparece
STAGE=(112,214,152,227)          # palco no alto da praça (x0,y0,x1,y1 lógicos)
FONTE=(132,245); ARVORE=(153,231)
def nome_tela(n):
    from font import G, ACC
    s_=''.join(c for c in n.upper() if c in G or c in ACC or c==' ')
    return ' '.join(s_.split())
_sr=random.Random(505)
_spots=[]
for y in range(239,277,5):
    for x in range(104,162,5):
        jx,jy=x+_sr.uniform(-1.5,1.5),y+_sr.uniform(-1.2,1.2)
        if math.hypot(jx-FONTE[0],(jy-FONTE[1])*1.3)<9 or math.hypot(jx-ARVORE[0],jy-ARVORE[1])<6: continue
        _spots.append((jx,jy))
for y in (ROADB+3,ROADB+7):      # transborda pras ruas do lado da praça
    for x in list(range(70,100,5))+list(range(167,200,5)):
        _spots.append((x+_sr.uniform(-1,1),y))
_spots.sort(key=lambda p:math.hypot(p[0]-132,(p[1]-STAGE[3])*1.4))
_regids=sorted(REG)
_others=[i for i in _sr.sample(range(1,C1+1),160) if i not in REG]
PLATEIA=[]
for j in range(min(len(_spots),96)):
    pid=_regids.pop(0) if (j%3==1 and _regids) else _others.pop(0)
    l=house_lots[(pid-1)//10]; lx,ly=lot(*l)
    sx=lx+10+_sr.uniform(-4,4); sy=(l[1]+3) if l[2]=='a' else (l[1]+8); ry=l[1]+7
    tx,ty=_spots[j]
    if l[1]==ROADB: pts=[(sx,sy),(sx,ry),(tx,ROADB+5),(tx,ty)]
    else:
        mx=131.5+_sr.uniform(-2.5,2.5)
        pts=[(sx,sy),(sx,ry),(mx,ry),(mx,ROADB+5 if ty>ROADB else ty),(tx,ty)]
    dep=46.4+_sr.uniform(0,1.4); arr=48.6+j*0.03+_sr.uniform(0,0.6)
    spd=clamp(plen(pts)/max(0.6,arr-dep),18,70)
    PLATEIA.append(dict(id=pid,pts=pts,dep=dep,spd=spd,arr=dep+plen(pts)/spd,ph=_sr.uniform(0,6.28)))
def plateia_state(c,t):
    """(x,y,andando,pulo)"""
    if not (SHOWWIN[0]<=t<SHOWWIN[1]) or t<c['dep']: return None
    if t<c['arr']:
        (x,y),_=path_pos(c['pts'],(t-c['dep'])*c['spd']); return (x,y,True,0.0)
    x,y=c['pts'][-1]
    if t>=52.6: hop=abs(math.sin((t*2.6+c['ph']/6.28)*math.pi))*2.2      # dançando
    elif t>=50.5: hop=abs(math.sin((t*1.6+c['ph']/6.28)*math.pi))*0.8
    else: hop=0.0
    return (x,y,False,hop)
BANDA=[(121,223,'guitarra'),(132,224,'voz'),(143,221,'bateria')]

# ---------- câmera (x, y, largura visível em pixels lógicos) ----------
WIDE=(135,240,270)
_pref=(lot(*PREFEITURA[0])[0]+21,lot(*PREFEITURA[0])[1]+12)
CAM=[(0,(131,300,150)),(2.4,(131,300,150)),(3.6,WIDE),(7.4,WIDE),(8.6,(105,346,150)),(T['quase'][1],(105,346,150)),
     (T['pref'][0]+0.6,(_pref[0],398,90)),(26.0,(_pref[0],398,90)),(29.8,WIDE),(T['cidadezinha'][1],WIDE),
     (T['cresce2'][0]+0.6,(125,300,240)),(T['cresce2'][1],(125,300,240)),
     (T['prefeito'][0]+0.6,(158,394,96)),(T['prefeito'][1],(158,394,96)),
     (T['domingo'][0]+0.8,WIDE),(T['domingo'][1],WIDE),
     (T['show'][0]+0.6,(132,240,104)),(T['show'][1],(132,240,104)),
     (T['resumo'][0]+0.8,WIDE),(T['mapa'][0],WIDE),
     (T['mapa'][0]+0.8,(120,329,170)),(T['mapa'][1],(120,329,170)),
     (T['cta'][0]+0.6,WIDE),(99,WIDE)]
def cam_at(t):
    for (a,va),(b,vb) in zip(CAM,CAM[1:]):
        if a<=t<b:
            f=smooth((t-a)/(b-a)); return tuple(va[i]+(vb[i]-va[i])*f for i in range(3))
    return CAM[-1][1]
def hour_at(t): return None
