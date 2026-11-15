import numpy as np, random, math, json, os
from PIL import Image, ImageDraw
from world import *
from font import draw_text, text_width

# =====================================================================
#  EPISÓDIO 4  (370 -> 460 seguidores)
#  Escola (marco 400), casas 38-46, o mapa lota e a vila abre a rua D,
#  visão em primeira pessoa passando pela escola, sábado de mercadinho.
#  Tempos sincronizados com a narração (narracao_ep4.wav, 78,5 s).
# =====================================================================
EP=4; C0=370; C1=460
T=dict(
    titulo=(0.0,3.4), recap=(3.4,9.0),
    cresce1=(9.0,14.8),        # casa 38 11.2 / casa 39 12.3 / casa 40 13.6
    quase=(14.8,18.2),         # "bateu quatrocentos" 16.7-17.9
    escola=(18.2,25.5),        # ESCOLA 19.3 / fundação 20.3 / parede 21.3 / telhado 22.1 / sino 23.4 / bandeira 24.6
    fp=(25.5,28.9),            # primeira pessoa: "o sino toca" 27.1
    cresce2=(28.9,35.1),       # 400 -> 460
    lotado=(35.1,39.7),        # casa 46 36.3 / nenhum lote 38.3
    ruanova=(39.7,45.6),       # pilha 41.6 / episódio 1 43.0 / rua nova 44.3
    casa47=(45.6,47.9),
    sabado=(47.9,51.0),        # sábado 48.2 / dia de quê 52.3
    mercado=(51.0,58.8),       # mercadinho 51.2 / fila 56.3 / vendinha 56.8
    resumo=(58.8,65.1),        # 460 60.1 / 46 casas 61.9 / escola 63.1 / rua 63.8
    proximo=(65.1,70.2),       # 500 66.2 / prefeitura 68.5 / calçadas 69.2
    nome=(70.2,74.5),          # placa 70.4 / nome 72.4 / comenta 73.7
    cta=(74.5,79.6),
)
DUR=79.6

# ---------- contador ----------
CK=[(0,C0),(9.3,C0),(11.7,380),(12.8,390),(14.0,395),(16.6,399),(17.45,400),(29.4,400),(34.4,C1)]
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
NH=C1//10                                   # 46 casas
house_var=[(i*5+2)%6 for i in range(len(house_lots))]
def house_p(i,C): return clamp((C-(10*i+5))/5)
def house_done_time(i): return time_reach(10*(i+1))

# ---------- obras do episódio ----------
ESC_KEYS=[(19.0,0.0),(20.3,0.2),(21.2,0.3),(21.9,0.62),(22.9,0.85),(23.6,0.9),(24.5,0.93),(25.0,1.0)]
def escola_p(t): return 0.0 if t<19.0 else interp(t,ESC_KEYS)
def pile_n(t): return int(round(interp(t,[(41.5,10),(44.0,0)])))       # toras na pilha
def roadd_f(t): return interp(t,[(44.0,0.0),(45.2,1.0)])               # rua D sendo aberta (0..1)
def stakes_f(t): return interp(t,[(44.8,0.0),(45.8,1.0)])
def bell_swing(t):
    for a in (23.6,27.0,27.6):
        if a<=t<a+0.9: return [1,0,-1,0][int((t-a)*12)%4]
    return 0

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

# ---------- sábado: a vila inteira vai pro mercadinho ----------
SAT=(48.0,60.2)                  # janela em que só a "multidão" aparece
DOOR_M=(lot(*MERCADO)[0]+9.5,ROADB+3)
QY=ROADB+5; EXY=ROADB+9; QSP=5.0; QX0=DOOR_M[0]-4.5; SVC=0.32
def q_slot(n): return (QX0-n*QSP,QY)
_cr=random.Random(404)
_regids=sorted(REG)
_others=[i for i in _cr.sample(range(1,C1+1),80) if i not in REG]
CROWD=[]
_oi=0
for j in range(51):
    if j%3==1 and _regids: pid=_regids.pop(0)
    else: pid=_others[_oi]; _oi+=1
    l=house_lots[(pid-1)//10]; lx,ly=lot(*l)
    sx=lx+10+_cr.uniform(-4,4)
    sy=(l[1]+3) if l[2]=='a' else (l[1]+8)
    ry=l[1]+7
    if l[1]==ROADB: pts=[(sx,sy),(sx,ry)]
    else:
        mx=131.5+_cr.uniform(-2,2)
        pts=[(sx,sy),(sx,ry),(mx,ry),(mx,ROADB+7)]
    CROWD.append(dict(id=pid,pts=pts,dep=48.3+_cr.uniform(0,1.6),ph=_cr.uniform(0,6),
                      exit=('dir' if j%2 else 'desce')))
# chegada na fila em ordem (j); velocidade ajustada pra chegar na hora
for j,c in enumerate(CROWD):
    want=51.0+j*0.15
    L=plen(c['pts'])+abs(c['pts'][-1][0]-QX0)+10
    spd=clamp(L/max(0.5,want-c['dep']),18,60)
    c['arr']=c['dep']+L/spd; c['spd']=spd
CROWD.sort(key=lambda c:c['arr'])
_e=0
for c in CROWD:
    c['ent']=max(c['arr']+0.3,_e+SVC); _e=c['ent']
for j,c in enumerate(CROWD):
    c['ahead']=[k['ent'] for k in CROWD[:j]]
    c['n_arr']=sum(1 for e in c['ahead'] if e>c['arr'])
    tail=q_slot(c['n_arr'])
    c['walk']=c['pts']+[(tail[0],ROADB+7),tail]
    c['spd']=plen(c['walk'])/max(0.4,c['arr']-c['dep'])
    door=DOOR_M
    if c['exit']=='dir': c['out']=[door,(door[0]+2,EXY),(226,EXY)]
    else: c['out']=[door,(door[0],EXY),(134.5,EXY),(134.5,370)]
def crowd_state(c,t):
    """(x,y,dir_hint,sacola) ou None"""
    if t<c['dep'] or t>=SAT[1]: return None
    if t<c['arr']:
        (x,y),_=path_pos(c['walk'],(t-c['dep'])*c['spd']); return (x,y,False)
    if t<c['ent']:
        n=sum(clamp((e+0.35-t)/0.35) for e in c['ahead'])
        n=min(n,c['n_arr']) if t<c['arr']+0.4 else n
        x,y=q_slot(n); return (x,y,False)
    if t<c['ent']+0.2:
        f=(t-c['ent'])/0.2; x0,y0=q_slot(0)
        return (x0+(DOOR_M[0]-x0)*f,y0+(DOOR_M[1]-y0)*f,False)
    if t<c['ent']+1.0: return None                       # dentro do mercadinho
    (x,y),end=path_pos(c['out'],(t-c['ent']-1.0)*30)
    if end: return None
    return (x,y,True)
VENDEDOR=(lot(*VENDA)[0]+9.5,ROADB+4)

# ---------- câmera (x, y, largura visível em pixels lógicos) ----------
WIDE=(135,240,270)
_esc=(lot(*ESCOLA[0])[0]+21,lot(*ESCOLA[0])[1]+12)
_c47=lot_center(house_lots[46],12)
_pref=(lot(*PREFEITURA[0])[0]+21,lot(*PREFEITURA[0])[1]+12)
_h46=lot_center(house_lots[45])
CAM=[(0,(131,300,150)),(2.6,(131,300,150)),(4.0,WIDE),(T['recap'][1],WIDE),
     (T['cresce1'][0]+0.8,(120,170,210)),(T['quase'][1],(120,170,210)),
     (T['escola'][0]+0.8,(_esc[0],_esc[1]+14,92)),(T['escola'][1]-0.45,(_esc[0],_esc[1]+14,92)),
     (T['escola'][1],(_esc[0],_esc[1]+10,40)),
     (T['cresce2'][0],(118,168,240)),(T['cresce2'][1],(118,168,240)),
     (T['lotado'][0]+0.7,WIDE),(T['lotado'][1],WIDE),
     (T['ruanova'][0]+1.0,(125,340,170)),(T['ruanova'][1],(125,340,170)),
     (T['casa47'][0]+0.7,(_c47[0]+8,_c47[1],110)),(T['casa47'][1],(_c47[0]+8,_c47[1],110)),
     (T['sabado'][0]+0.7,WIDE),(T['sabado'][1],WIDE),
     (T['mercado'][0]+0.8,(150,236,124)),(55.9,(150,236,124)),(56.7,(108,236,124)),(T['mercado'][1],(108,236,124)),
     (T['resumo'][0]+0.8,WIDE),(T['resumo'][1],WIDE),
     (T['proximo'][0]+0.8,(_pref[0],_pref[1],130)),(T['proximo'][1],(_pref[0],_pref[1],130)),
     (T['nome'][0]+0.7,(149,440,96)),(T['nome'][1],(149,440,96)),
     (T['cta'][0]+0.6,WIDE),(99,WIDE)]
def cam_at(t):
    for (a,va),(b,vb) in zip(CAM,CAM[1:]):
        if a<=t<b:
            f=smooth((t-a)/(b-a)); return tuple(va[i]+(vb[i]-va[i])*f for i in range(3))
    return CAM[-1][1]
def hour_at(t): return None          # o ep. 4 é todo de dia
