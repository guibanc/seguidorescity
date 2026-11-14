import numpy as np, random, math, json, os
from PIL import Image, ImageDraw
from world import *
from font import draw_text, text_width

# =====================================================================
#  EPISÓDIO 3  (320 -> 370 seguidores)
#  A vila evolui de 8 bits para 16 bits + site na bio (cada inscrito
#  registra o nome dele num morador).
#  Linha do tempo PROVISÓRIA: quando a narração chegar, só ajustar T{}
# =====================================================================
EP=3; C0=320; C1=370; C8=340      # até 340 ainda é 8 bits
T=dict(
    titulo=(0.2,4.4), recap=(4.4,9.4),
    cresce8=(9.4,13.8),         # "mais duas casas prontas na rua de cima" 11.25-13.3
    aviso=(13.8,17.3),          # "Mas hoje..." 14.08 / "a vila vai mudar" 15.14
    evolucao=(17.3,24.2),       # "A vila EVOLUIU" 17.5 / "16 bits!" 22.66
    compara=(24.2,32.3),        # telha 25.47 / floreira 26.74 / chaminé 28.47 / mercadinho 30.16
    detalhe=(32.3,40.6),        # único 33.46 / cabelo 35.71 / roupa 36.62 / chapéu 37.24 / óculos 38.42 / iguais 39.41
    cresce16=(40.6,46.2),       # "chegamos a 370" 42.11 / "três casas novas" 43.48
    site=(46.2,55.6),           # site 47.42 / link 49.12 / escolhe 50.4 / nome 52.23 / acompanha 53.6
    npc=(55.6,63.4),            # rotina 55.86 / manhã 57.31 / mercadinho 58.86 / praça 60.09 / noite 61.2
    resumo=(63.4,70.0),         # 370 64.87 / 37 casas 66.98 / 16 bits 68.3
    proximo=(70.0,73.9),        # escola 72.4
    cta=(74.0,78.4),
)
DUR=78.4
T_SWEEP=(17.45,18.6)   # a "varredura" que troca 8->16

# ---------- contador ----------
CK=[(0,C0),(9.8,C0),(13.0,C8),(41.4,C8),(45.4,C1)]
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
def is16(t): return t>=T_SWEEP[1]

# ---------- lotes (iguais aos eps. anteriores) ----------
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
NH=C1//10                                   # 37 casas
house_var=[(i*5+2)%6 for i in range(len(house_lots))]
def house_p(i,C): return clamp((C-(10*i+5))/5)
def house_done_time(i): return time_reach(10*(i+1))
def mercado_p(t): return 1.0

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
TREE_SPR={}
def tree_img(r,k):
    if (r,k) not in TREE_SPR: TREE_SPR[(r,k)]=tree_sprite(r,k,r*10+k)
    return TREE_SPR[(r,k)]

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

PSPR={}
def pimg(d,frame,tool=None,log=False):
    key=(d['skin'],d['hair'],d['shirt'],d['pants'],frame,tool,log)
    if key not in PSPR: PSPR[key]=person_sprite(d['skin'],d['hair'],d['shirt'],d['pants'],frame,tool,log)
    return PSPR[key]
WORKERS=[dict(skin=SKINS[i%5]+(255,),hair=HAIRS[i%6]+(255,),shirt=[(240,130,40),(60,110,220),(220,60,60),(70,170,90)][i%4]+(255,),pants=(60,60,80,255),seed=8000+i) for i in range(6)]

# ---------- morador em destaque (cena do site) ----------
DESTAQUE_ID=205                         # morador #205, casa 21 (índice 20)
DEST_CASA=house_lots[(DESTAQUE_ID-1)//10]
def lot_center(l,dy=16):
    x,y=lot(*l); return (x+10,y+dy)
_hx,_hy=lot(*DEST_CASA)
_door=(_hx+10,_hy+22) if DEST_CASA[2]=='b' else (_hx+10,_hy+22)
_road=DEST_CASA[1]+5
_mx,_my=lot(*MERCADO); _mdoor=(_mx+10,ROADB+3)
# horário da vila durante a cena (07h -> 21h30)
HOURS=[(55.6,6.5),(57.3,7.0),(58.9,9.5),(60.1,14.0),(61.2,18.5),(62.8,21.0),(63.4,21.5)]
def hour_at(t):
    if not (T['npc'][0]<=t<T['npc'][1]+0.6): return None
    if t>=T['npc'][1]: return 21.5-(t-T['npc'][1])/0.6*7.5     # volta pro dia rapidinho
    for (a,va),(b,vb) in zip(HOURS,HOURS[1:]):
        if a<=t<b: return va+(vb-va)*(t-a)/(b-a)
    return 21.5
# roteiro do morador: casa -> mercadinho -> praça -> casa
_t=T['npc'][0]
DEST_PATH=[ (55.6,  _door, 'casa'),
            (57.3,  _door, 'anda'),
            (57.8,  (_door[0],_road), 'anda'),
            (58.8,  (_mdoor[0],ROADB+6), 'anda'),
            (59.0,  _mdoor, 'entra'),
            (59.6,  _mdoor, 'sai'),
            (59.9,  (131.5,ROADB+6), 'anda'),
            (60.3,  (118,262), 'senta'),
            (61.3,  (118,262), 'anda'),
            (61.9,  (131.5,_road), 'anda'),
            (62.5,  (_door[0],_road), 'anda'),
            (62.8,  _door, 'casa'),
            (99,    _door, 'casa')]
def destaque_state(t):
    """(x,y,acao,sacola) lógico, ou None fora da cena"""
    if not (T['npc'][0]<=t<T['npc'][1]): return None
    for (a,pa,acao),(b,pb,_) in zip(DEST_PATH,DEST_PATH[1:]):
        if a<=t<b:
            f=(t-a)/(b-a)
            x=pa[0]+(pb[0]-pa[0])*f; y=pa[1]+(pb[1]-pa[1])*f
            sac = t>_t+4.2
            return (x,y,acao,sac)
    return None

# ---------- câmera (x, y, largura visível em pixels lógicos) ----------
WIDE=(135,240,270)
_c=(122,168); _e=lot_center(ESCOLA[0]); _m=lot_center(MERCADO)
_hs=lot_center(house_lots[29]); _ppl=(108,246)
CAM=[(0,(131,300,150)),(T['recap'][0],(131,300,150)),(T['recap'][1]-0.6,WIDE),
     (T['cresce8'][0]+0.4,(_c[0]+8,_c[1],150)),(T['cresce8'][1],(_c[0]+8,_c[1],150)),
     (T['aviso'][0]+0.8,WIDE),(T['evolucao'][1],WIDE),
     (T['compara'][0]+0.8,(_m[0]-14,_m[1]+6,120)),(T['compara'][1],(_m[0]-14,_m[1]+6,120)),
     (T['detalhe'][0]+0.8,(_ppl[0],_ppl[1],70)),(T['detalhe'][1],(_ppl[0]+14,_ppl[1]-6,70)),
     (T['cresce16'][0]+0.8,(_c[0]-14,_c[1],150)),(T['cresce16'][1],(_c[0]-14,_c[1],150)),
     (T['site'][0]+0.8,WIDE),(T['site'][1]-0.4,WIDE),
     (T['resumo'][0]+0.8,WIDE),(T['resumo'][1],WIDE),
     (T['proximo'][0]+0.8,(_e[0]+10,_e[1],130)),(T['proximo'][1],(_e[0]+10,_e[1],130)),
     (T['cta'][0]+0.6,WIDE),(99,WIDE)]
def cam_at(t):
    if T['site'][1]-0.4<=t<T['resumo'][0]+0.8:
        # segue o morador em destaque
        st=destaque_state(min(max(t,T['npc'][0]),T['npc'][1]-0.01))
        fx,fy=(st[0],st[1]) if st else _door
        tgt=(fx,fy-8,82)
        if t<T['npc'][0]+0.5:
            a=(T['site'][1]-0.4); f=smooth((t-a)/(T['npc'][0]+0.5-a)); va=WIDE
            return tuple(va[i]+(tgt[i]-va[i])*f for i in range(3))
        if t>=T['npc'][1]:
            f=smooth((t-T['npc'][1])/(T['resumo'][0]+0.8-T['npc'][1])); vb=WIDE
            return tuple(tgt[i]+(vb[i]-tgt[i])*f for i in range(3))
        return tgt
    for (a,va),(b,vb) in zip(CAM,CAM[1:]):
        if a<=t<b:
            f=smooth((t-a)/(b-a)); return tuple(va[i]+(vb[i]-va[i])*f for i in range(3))
    return CAM[-1][1]
