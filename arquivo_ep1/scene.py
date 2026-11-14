import numpy as np, random, math
from PIL import Image, ImageDraw
from world import *
from font import draw_text, text_width

# ---------- contador ----------
CK=[(0,0),(19.4,0),(23.6,3),(29.6,5),(30.3,5),(37.8,42),(40.4,45),(41.4,50),(42.75,100),(47.5,200),(50.0,200),(51.8,267)]
def count_at(t):
    if t>=CK[-1][0]: return 267
    for (a,va),(b,vb) in zip(CK,CK[1:]):
        if a<=t<b:
            f=(t-a)/(b-a)
            if b==51.8: f=1-(1-f)**2
            return int(va+(vb-va)*f)
    return 0
def time_reach(n):
    lo,hi=0,60.0
    if count_at(hi)<n: return None
    for _ in range(40):
        m=(lo+hi)/2
        if count_at(m)>=n: hi=m
        else: lo=m
    return hi

# ---------- lotes ----------
LX_L=[104,82,60,38,16]; LX_R=[140,162,184,206]
def lot(x,road,side):  # retorna canto sup-esq do sprite (21x25) ; parede embaixo
    if side=='a': y=road-24
    else: y=road+12
    return (x-1,y)
lots=[]
for road in (ROADA,ROADB):
    cand=[]
    for i in range(5):
        for xs in (LX_L,LX_R):
            if i<len(xs):
                for side in ('a','b'):
                    x=xs[i]
                    if road==ROADB and x in (104,140): continue
                    cand.append((x,road,side))
    lots+=cand
VENDA=(82,ROADB,'a'); MERCADO=(162,ROADB,'a')
house_lots=[l for l in lots if l not in (VENDA,MERCADO)][:27]
FUTURE=[l for l in lots if l not in (VENDA,MERCADO) and l not in house_lots]
house_var=[(i*5+2)%6 for i in range(27)]
def house_p(i,C): return clamp((C-(10*i+5))/5)
def house_done_time(i): return time_reach(10*(i+1))

# ---------- árvores ----------
trees=[]  # dict x,y(base),r,kind,chop0,mode
tr=random.Random(7)
def far_from_village(x,y):
    return True
for _ in range(400):
    x=tr.randint(2,W-3); y=tr.randint(2,H-3)
    border = x<14 or y<62 or y>466 or (x>254) or (219<x<229)
    if y>466 and 112<x<152: continue
    if 228<=x<=254: continue
    if border: trees.append(dict(x=x,y=y,r=tr.choice([5,6,6,7]),k=tr.randint(0,1),chop=None))
# árvores no meio (serão cortadas)
interiorA=[(40,316),(70,352),(96,300),(150,318),(178,350),(200,306),(120,372),(146,400),(116,430),(58,300)]
interiorBC=[(52,228),(86,180),(170,224),(196,170),(30,140),(150,130),(110,196),(60,262),(186,262),(120,140)]
for i,(x,y) in enumerate(interiorA):
    trees.append(dict(x=x,y=y,r=6,k=i%2,chop=24.2+i*0.52,mode='axe'))
for i,(x,y) in enumerate(interiorBC):
    trees.append(dict(x=x,y=y,r=6,k=i%2,chop=43.0+i*0.09,mode='poof'))
trees.sort(key=lambda d:d['y'])
TREE_SPR={}
def tree_img(r,k):
    key=(r,k)
    if key not in TREE_SPR: TREE_SPR[key]=tree_sprite(r,k,r*10+k)
    return TREE_SPR[key]

# ---------- moradores ----------
ROADSEG={'A':((16,ROADA+5),(217,ROADA+5),29.6),'B':((16,ROADB+5),(217,ROADB+5),44.8),
         'C':((16,ROADC+5),(217,ROADC+5),45.0),'M1':((131.5,330),(131.5,470),27.2),'M2':((131.5,112),(131.5,330),44.7)}
pr=random.Random(42)
people=[]
for k in range(267):
    ts=time_reach(k+1)
    d=dict(ts=ts,skin=pr.choice(SKINS)+(255,),hair=pr.choice(HAIRS)+(255,),shirt=pr.choice(SHIRTS)+(255,),pants=pr.choice(PANTS)+(255,),
           sx=131.5+pr.uniform(-3,3),spd=pr.uniform(26,36),amp=pr.uniform(8,40),wspd=pr.uniform(5,12),ph=pr.uniform(0,6.28),off=pr.uniform(-3,3))
    if ts<29:
        d['seg']=None; d['gx']=pr.uniform(112,150); d['gy']=pr.uniform(372,395)
        d['seg2']='A'; d['tx']=pr.uniform(60,200)
    else:
        avail=[s for s,v in ROADSEG.items() if v[2]<=ts+1.0]
        if ts>45.0 and pr.random()<0.25: d['seg']='P'; d['tx']=pr.uniform(104,160); d['ty']=pr.uniform(216,272)
        else:
            s=pr.choice([a for a in avail if a in 'ABC']*3+avail); d['seg']=s
            (x0,y0),(x1,y1),_=ROADSEG[s]; f=pr.uniform(0.05,0.95)
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
    """retorna (x,y,moving,carrying_tool) ou None"""
    if d['ts'] is None or t<d['ts']: return None
    el=t-d['ts']
    if d['seg'] is None:
        # chegada dos pioneiros
        pts=[(d['sx'],484),(d['sx'],440),(d['gx'],d['gy'])]
        if t<30.2:
            (x,y),done=path_pos(pts,el*16)
            if done: return (x,y+math.sin(t*3+d['ph'])*0.5,False,'up')
            return (x,y,True,'up')
        # vão para a rua A
        tx,ty=d['tx'],ROADA+5+d['off']
        pts2=[(d['gx'],d['gy']),(131.5,d['gy']),(131.5,ty),(tx,ty)]
        L=plen(pts2); dd=(t-30.2)*20
        if dd<L:
            (x,y),_=path_pos(pts2,dd); return (x,y,True,None)
        x=tx+d['amp']*math.sin((t-30.2-L/20)*d['wspd']/d['amp']+0)
        return (x,ty,True,None)
    tx,ty=d['tx'],d['ty']
    if d['seg'] in ('A','B','C'):
        ty=ty+d['off']; pts=[(d['sx'],484),(131.5+d['off'],ty),(tx,ty)]
    elif d['seg']=='P':
        pts=[(d['sx'],484),(131.5+d['off'],ty),(tx,ty)]
    else:
        tx=tx+d['off']; pts=[(d['sx'],484),(tx,ty)]
    L=plen(pts)
    dd=el*d['spd']
    if dd<L:
        (x,y),_=path_pos(pts,dd); return (x,y,True,None)
    tt=el-L/d['spd']
    if d['seg']=='P':
        # parado conversando, mexe um pouquinho
        return (tx+math.sin(tt*0.7+d['ph'])*2,ty,(int(tt*1.3+d['ph'])%4==0),None)
    s=d['amp']*math.sin(tt*d['wspd']/d['amp']*1.0)
    if d['seg'] in('A','B','C'): x,y=tx+s,ty
    else: x,y=tx,ty+s
    lo=(16,112); hi=(217,470)
    return (clamp(x,16,217),clamp(y,112,470),True,None)

PSPR={}
def pimg(d,frame,tool=None,log=False):
    key=(d['skin'],d['hair'],d['shirt'],d['pants'],frame,tool,log)
    if key not in PSPR: PSPR[key]=person_sprite(d['skin'],d['hair'],d['shirt'],d['pants'],frame,tool,log)
    return PSPR[key]
WORKERS=[dict(skin=SKINS[i%5]+(255,),hair=HAIRS[i%6]+(255,),shirt=[(240,130,40),(60,110,220),(220,60,60),(70,170,90)][i%4]+(255,),pants=(60,60,80,255)) for i in range(6)]

# ---------- câmera ----------
CAM=[(0,(131,300,112)),(5.4,(131,300,124)),(9.0,(135,240,270)),(19.0,(135,240,270)),(20.2,(131,405,140)),(23.9,(131,400,150)),
     (24.8,(120,340,190)),(29.9,(120,340,190)),(30.7,(118,326,118)),(37.9,(118,326,118)),(39.2,(135,240,270)),(55.0,(135,240,270)),
     (56.3,None),(61.0,None),(62.0,(135,240,270)),(64.3,(135,240,270)),(65.3,'M'),(67.6,'M'),(69.0,(139,420,104)),(74.8,(139,420,104)),(76.2,(135,240,270)),(99,(135,240,270))]
def cam_at(t,targets):
    keys=[]
    for tk,v in CAM:
        if v is None: v=targets['h27']
        elif v=='M': v=targets['merc']
        keys.append((tk,v))
    for (a,va),(b,vb) in zip(keys,keys[1:]):
        if a<=t<b:
            f=smooth((t-a)/(b-a)); return tuple(va[i]+(vb[i]-va[i])*f for i in range(3))
    return keys[-1][1]
