import numpy as np, math, random, sys, json, os
from PIL import Image, ImageDraw, ImageFilter
from world import *
from scene import *
from font import draw_text, text_width
import vila16 as V
import iso, vox

# =====================================================================
#  EP. 8 — TUDO EM BLOCOS (iso.VOX a partir de EVOL_T) + CAMPO DE FUTEBOL (700)
# =====================================================================
FPS=30
OUTW,OUTH=1080,1920
NAVY=(24,22,52,235); WHITE=(255,255,255,255); YEL=(255,214,70,255); GREEN=(120,230,110,255); LBLUE=(180,200,255,255); RED=(230,60,60,255)
def box(d,x0,y0,x1,y1,fill=NAVY):
    d.rectangle([x0,y0,x1,y1],fill=fill); d.rectangle([x0,y0,x1,y1],outline=(255,255,255,255))
    d.rectangle([x0+2,y0+2,x1-2,y1-2],outline=(120,120,180,255))
def pop(t,t0,t1,fade=0.25):
    if t<t0 or t>t1: return 0
    return min(clamp((t-t0)/0.18),clamp((t1-t)/fade))
def banner(d,lines,y,t,t0,t1,colors=None,scale=2,fill=NAVY):
    v=pop(t,t0,t1)
    if v<=0: return
    wmax=max(text_width(s,scale) for s in lines)+16; hh=len(lines)*(9*scale+4)+10
    yy=y+int((1-v)*12)
    box(d,135-wmax//2,yy,135+wmax//2,yy+hh,fill)
    for k,s in enumerate(lines):
        draw_text(d,s,135,yy+7+k*(9*scale+4)+(2*scale),scale,colors[k] if colors else WHITE)
def nhouses(C): return sum(1 for i in range(len(house_lots)) if house_p(i,C)>=1)
def chip(d,txt,x,y,t,t0,t1,col=YEL,fill=(24,22,52,225)):
    v=pop(t,t0,t1)
    if v<=0: return
    w=text_width(txt,1)+12
    x=int(clamp(x,w/2+4,W-w/2-4)); y=int(y)
    yy=y+int((1-v)*6)
    box(d,x-w//2,yy,x+w//2,yy+15,fill); draw_text(d,txt,x,yy+4,1,col)
def tag_s(d,txt,sx,sy,t,t0,t1,col=YEL,dy=-30,fill=(24,22,52,225)):
    bob=int(math.sin(t*5)*2)
    chip(d,txt,sx,sy+dy+bob,t,t0,t1,col,fill)
    if pop(t,t0,t1)>0: d.polygon([(int(sx)-3,int(sy)+dy+bob+16),(int(sx)+3,int(sy)+dy+bob+16),(int(sx),int(sy)+dy+bob+20)],fill=(255,255,255,255))

# ---------- moradores: 32 bits (antes) e em bloco (depois) ----------
_N2={}
UNIF={'jogador':dict(camisa=3,camisa2=2,estampa='time',baixo='bermuda',cor_baixo=2,chapeu=None),
      'rival':dict(camisa=0,camisa2=4,estampa='time',baixo='bermuda',cor_baixo=2,chapeu=None),
      'goleiro':dict(camisa=6,camisa2=6,estampa='lisa',baixo='bermuda',cor_baixo=2,chapeu=None),
      'fazendeiro':dict(camisa=0,camisa2=4,estampa='xadrez',baixo='calca',cor_baixo=0,chapeu='palha',cor_chapeu=2,barba=True)}
def look_u(pid,uniform):
    lk=dict(V.look_of(pid))
    if uniform in UNIF: lk.update(UNIF[uniform])
    return lk
def npc_k(pid,dr,fr,k,uniform=None,carry=None,tool=None):
    from char32 import npc32
    u2=None if uniform in UNIF else uniform
    if k==1:
        key=(pid,dr,fr,uniform,carry,tool,1)
        if key not in _N2: _N2[key]=npc32(look_u(pid,uniform),dr,fr,u2,tool,carry).resize((16,24),Image.NEAREST)
        return _N2[key]
    key=(pid,dr,fr,uniform,carry,tool)
    if key not in _N2: _N2[key]=npc32(look_u(pid,uniform),dr,fr,u2,tool,carry)
    return _N2[key]
_DOG={}
def dog32(dr,fr,bola,k):
    key=(dr,fr,bola,k)
    if key in _DOG: return _DOG[key]
    im=Image.new('RGBA',(30,22),(0,0,0,0)); d=ImageDraw.Draw(im)
    c=(196,150,96); c2=(160,116,70); o=(70,46,30)
    if dr in ('up','down'):
        d.rectangle([11,8,18,17],fill=c,outline=o); d.rectangle([10,3,19,10] if dr=='down' else [10,1,19,8],fill=c,outline=o)
        if dr=='down': d.point([(12,6),(17,6)],fill=(20,20,20)); d.rectangle([14,8,15,9],fill=(30,30,30))
        d.rectangle([9,2,10,6],fill=c2); d.rectangle([19,2,20,6],fill=c2)
        sw=fr%2; d.rectangle([11,17,12,20-sw],fill=c2); d.rectangle([17,17,18,19+sw],fill=c2)
    else:
        sw=[0,1,0,-1][fr%4]
        for lx,o_ in ((7,sw),(10,-sw),(17,-sw),(20,sw)): d.rectangle([lx+o_,15,lx+1+o_,20],fill=c2)
        d.rectangle([5,9,22,16],fill=c,outline=o)
        d.rectangle([19,4,27,11],fill=c,outline=o); d.rectangle([25,8,28,11],fill=(214,180,130),outline=o)
        d.point((27,8),fill=(20,20,20)); d.point((23,6),fill=(20,20,20)); d.rectangle([19,3,21,7],fill=c2)
        d.line([(5,10),(1,6-abs(sw))],fill=c,width=2)
        if bola: d.ellipse([25,11,30,16],fill=(250,250,250),outline=(40,40,50))
        if dr=='left': im=im.transpose(Image.FLIP_LEFT_RIGHT)
    if k==1: im=im.resize((15,11),Image.NEAREST)
    im.info['foot']=0
    _DOG[key]=im; return im
def sf(pid,dr,fr,uniform=None,carry=None,hop=0,tool=None):
    def f(k):
        s=npc_k(pid,dr,fr,k,uniform,carry,tool)
        if hop<=0: return s
        im=Image.new('RGBA',(s.width,s.height+int(hop*k)),(0,0,0,0)); im.paste(s,(0,0)); im.info['foot']=s.info.get('foot',0); return im
    return f
def dogf(dr,fr,bola=False):
    return lambda k: dog32(dr,fr,bola,k)

# ---------- câmera ----------
def CI(x,y,z): px,py=iso.PW(x,y); return (px,py,z)
FX0,FY0,FX1,FY1=vox.campo_rect(); FXM,FYM=(FX0+FX1)/2,(FY0+FY1)/2
CAMS=[(0.0,CI(132,452,4.0)),(3.6,CI(132,452,4.5)),(4.6,CI(135,420,0.95)),(8.6,CI(140,440,0.95)),(10.2,CI(FXM,FYM,2.6)),
      (13.5,CI(FXM,FYM,2.6)),(14.6,CI(135,480,1.3)),(16.9,CI(135,480,1.45)),
      (18.0,CI(96,512,5.2)),(20.9,CI(70,512,5.6)),
      (21.0,CI(132,248,1.0)),(25.85,CI(132,248,1.0)),
      (25.9,CI(118,515,4.0)),(29.4,CI(112,515,4.0)),(31.5,CI(54,508,4.2)),(33.0,CI(50,508,4.2)),
      (33.9,CI(FXM,FYM-3,5.2)),(36.2,CI(FXM,FYM-3,5.3)),(42.8,CI(FXM,FYM-3,5.8)),
      (43.3,CI(FXM,FYM,6.0)),(49.3,CI(FXM+4,FYM-2,6.6))]
CAMS2=[(57.0,CI(FXM+20,FYM,6.2)),(58.6,CI(-74,358,5.6)),(64.8,CI(-78,362,6.4)),
       (64.8,CI(160,424,3.0)),(75.3,CI(160,424,3.0)),
       (75.4,CI(FXM,FYM-3,5.6)),(80.4,CI(FXM,FYM-3,6.4)),
       (80.5,CI(132,250,4.0)),(84.4,CI(132,250,4.6)),
       (84.5,CI(135,520,1.5)),(89.6,CI(135,520,1.6)),
       (89.7,CI(140,500,1.5)),(96.6,CI(140,420,0.82)),
       (96.7,CI(FXM,FYM-3,5.8)),(103.5,CI(FXM,FYM-3,6.6))]
def _interp_cam(t,L):
    for (a,va),(b,vb) in zip(L,L[1:]):
        if a<=t<b:
            f=smooth((t-a)/(b-a)); return tuple(va[i]+(vb[i]-va[i])*f for i in range(3))
    return L[-1][1] if t>=L[-1][0] else L[0][1]
def camiso(t):
    if t<49.5: c=_interp_cam(t,CAMS)
    elif t<57.0:
        bx,by,bz=ball_at(t)
        if t>=54.5:
            dx,dy,_=dog_at(t); bx,by=(bx+dx)/2,(by+dy)/2
        tx,ty=clamp(bx,FX0+14,FX1-10),clamp(by,FY0+6,FY1-6)
        c0=_interp_cam(49.3,CAMS); c1=CI(tx,ty-2,7.2)
        f=smooth(clamp((t-49.5)/0.8)); c=tuple(c0[i]+(c1[i]-c0[i])*f for i in range(3))
    else: c=_interp_cam(t,CAMS2)
    if 53.7<=t<54.6:
        k=(1-(t-53.7)/0.9)*5; c=(c[0]+math.sin(t*70)*k,c[1]+math.cos(t*63)*k,c[2])
    if 35.6<=t<36.2:
        k=(1-(t-35.6)/0.6)*4; c=(c[0]+math.sin(t*70)*k,c[1]+math.cos(t*63)*k,c[2])
    return c
def w2si(x,y,cam,z_=0):
    cx,cy,zz=cam; px,py=iso.PW(x,y,z_)
    return ((px-(cx-540/zz))*zz/4,(py-(cy-960/zz))*zz/4)

# ---------- o jogo ----------
_regids=sorted(i for i in REG if i<=C1)
TEAM=[(12,'ATACANTE',(200,628)),(555,'ATACANTE',(199,643)),(168,'MEIA',(182,627)),(348,'MEIA',(182,644)),
      (236,None,(169,636)),(473,None,(158,629)),(441,'GOLEIRO',(FX0+3,FYM))]
RIVAL=[(9301,(207,637)),(9302,(203,624)),(9303,(212,648)),(9304,(192,636)),(9305,(FX1-3,FYM))]
BALLK=[(43.0,(FXM,FYM)),(49.84,(FXM,FYM)),(50.0,(169,636)),(50.7,(182,627)),(51.25,(182,644)),(52.2,(199,643)),(52.95,(200,628)),
       (53.72,(FX1+1.5,FYM-2)),(54.3,(FX1+1.5,FYM-2)),(54.5,(FXM,FYM))]
def _lerp(K_,t):
    if t<=K_[0][0]: return K_[0][1]
    for (a,pa),(b,pb) in zip(K_,K_[1:]):
        if a<=t<b:
            f=(t-a)/(b-a); return (pa[0]+(pb[0]-pa[0])*f,pa[1]+(pb[1]-pa[1])*f),f,a,b
    return K_[-1][1]
DOGK=[(54.7,(FX0-4,FY1+2)),(55.6,(FXM-1,FYM+1)),(56.0,(FXM-1,FYM+1)),(57.0,(FX0+4,FY0-6)),(60,(FX0-30,FY0-30))]
def dog_at(t):
    r=_lerp(DOGK,t); p=r[0] if isinstance(r[0],tuple) else r
    return (p[0],p[1],0)
def ball_at(t):
    if 75.4<=t<80.5 or t>=96.7:          # bola rolando à toa / quicando
        u=t*0.6; return (FXM+math.sin(u)*22,FYM+math.sin(u*1.7)*9,abs(math.sin(t*4))*6 if t>=96.7 else 0)
    if t>=55.8:
        x,y,_=dog_at(t); return (x+2.5,y,2.6)
    r=_lerp(BALLK,t)
    if isinstance(r[0],tuple):
        (x,y),f,a,b=r; h=math.sin(f*math.pi)*(3 if b-a<1.0 else 6)
        if b==53.72: h=math.sin(f*math.pi)*4+f*3
        return (x,y,h)
    return (r[0],r[1],0)
def team_people(t):
    out=[]; names=[]
    if not (43.3<=t<57.2 or 75.4<=t<80.5 or t>=96.7): return out,names
    bx,by,_=ball_at(t)
    gol=53.72<=t<55.2
    for k,(pid,pos,(hx,hy)) in enumerate(TEAM):
        ent=clamp((t-43.6-k*0.25)/1.6)
        if 75.4<=t or t>=96.7: ent=1
        sx,sy=hx,FY1+8
        x=sx+(hx-sx)*smooth(ent); y=sy+(hy-sy)*smooth(ent)
        if ent>=1:
            if t>=49.5 and pos!='GOLEIRO':
                x+=clamp((bx-x)*0.25,-4,4); y+=clamp((by-y)*0.25,-3,3)
            if 75.4<=t: x+=math.sin(t*1.3+k)*5; y+=math.sin(t*0.9+k*2)*3
            if pos=='GOLEIRO': y=FYM+clamp(by-FYM,-4,4)
        if 54.6<t<57.2 and pos!='GOLEIRO':                 # correndo atrás do vira-lata
            dx,dy,_=dog_at(t); f=clamp((t-55.4)/1.4)*0.6; x+=(dx-x)*f; y+=(dy-y)*f
        moving=ent<1 or (54.6<t<57.2) or 75.4<=t
        dr='up' if ent<1 else ('right' if pos!='GOLEIRO' else 'right')
        if 54.6<t<57.2: dr='left'
        hop=abs(math.sin((t*3+k)*math.pi))*3 if gol else 0
        out.append((x,y,sf(pid,dr,int(t*8+k)%4 if moving else 0,'goleiro' if pos=='GOLEIRO' else 'jogador',hop=hop)))
        names.append((pid,pos,x,y))
    for k,(pid,(hx,hy)) in enumerate(RIVAL):
        ent=clamp((t-44.2-k*0.25)/1.6)
        if 75.4<=t or t>=96.7: ent=1
        x=hx+(1-smooth(ent))*0; y=FY0-8+(hy-FY0+8)*smooth(ent)
        if ent>=1 and t>=49.5 and k<4: x+=clamp((bx-x)*0.2,-3,3); y+=clamp((by-y)*0.2,-3,3)
        if k==4:
            y=FYM+clamp(by-FYM,-4,4)
            if 53.4<=t<54.2: y=FYM+6*smooth(clamp((t-53.4)/0.3));
        if 75.4<=t: x+=math.sin(t*1.1+k*3)*4
        uni='goleiro' if k==4 else 'rival'
        out.append((x,y,sf(pid,'left' if ent>=1 else 'down',int(t*8+k)%4 if ent<1 or 75.4<=t else 0,uni)))
    return out,names
def torcida(t):
    out=[]
    if campo_p(t)<0.85 or not (41.7<=t<57.2 or 75.4<=t<80.5 or t>=96.7): return out
    rr=random.Random(5)
    for k in range(22):
        dj=1+k%4; pid=_regids[(k*3)%len(_regids)] if k%2==0 else rr.randint(1,C1)
        x=FX0+6+rr.uniform(0,FX1-FX0-12); y=FY1+2+dj*1.5-0.6
        hop=dj*1.5
        if 53.72<=t<55.2 or (41.7<=t<43.3 and k<8): hop+=abs(math.sin((t*2.6+k*0.37)*math.pi))*3
        out.append((x,y,sf(pid,'up',0,hop=hop)))
    return out
def ball_extra(t):
    if not (43.0<=t<57.2 or 75.4<=t<80.5 or t>=96.7): return []
    if t>=55.8 and t<57.2: return []
    x,y,h=ball_at(t)
    def ball(vd,vx0,vy0,k,x=x,y=y,h=h):
        X,Y=iso.PW(x,y,h); X=X*k-vx0; Y=Y*k-vy0; r=2*k
        Xs,Ys=iso.PW(x,y,0); Xs=Xs*k-vx0; Ys=Ys*k-vy0
        vd.ellipse([Xs-r,Ys-r/2,Xs+r,Ys+r/2],fill=(0,30,0,80))
        vd.ellipse([X-r,Y-2*r,X+r,Y],fill=(250,250,250),outline=(40,40,50))
        vd.rectangle([X-r//2,Y-r-r//2,X,Y-r],fill=(40,40,50))
    return [(x+y+0.6,('fn',ball))]
def dog_people(t):
    if not (54.6<=t<57.2): return []
    x,y,_=dog_at(t); dr='right' if t<55.6 else ('down' if t<56.0 else 'left')
    if t>=56.0: dr='up' if False else 'left'
    return [(x,y,dogf(dr,int(t*12)%4,bola=t>=55.8))]

# ---------- fazenda ----------
FARMER=(-76,340)
HIRED=[(652,(-128,372)),(663,(-110,384)),(676,(-92,396)),(689,(-120,408)),(704,(-80,416))]
def farm_people(t):
    out=[]
    if not (56.9<=t<65.0): return out
    wave=int(t*4)%2
    out.append((FARMER[0],FARMER[1],sf(9500,'down',wave*2 if t<62 else 0,'fazendeiro')))
    for k,(pid,(hx,hy)) in enumerate(HIRED):
        t0=60.8+k*0.25
        if t<t0: continue
        f=clamp((t-t0)/1.6); sx,sy=-30,395
        x=sx+(hx-sx)*f; y=sy+(hy-sy)*f
        if f<1: out.append((x,y,sf(pid,'left',int(t*8+k)%4)))
        else: out.append((x+math.sin(t*2+k)*0.6,y,sf(pid,'left',0,tool='up' if int(t*3+k)%2 else 'down')))
    return out

# ---------- moradores da cidade ----------
def iso_people(t,cam):
    cx,cy,z=cam; vw,vh=1080/z,1920/z
    out=[]; names=[]
    for pp in people:
        st=person_state(pp,t)
        if st is None: continue
        x,y=st[0],st[1]
        if FX0-4<x<FX1+4 and FY0-4<y<FY1+10: continue
        px,py=iso.PW(x,y)
        if not (cx-vw/2-20<px<cx+vw/2+20 and cy-vh/2-30<py<cy+vh/2+30): continue
        st0=person_state(pp,t-0.08)
        dx,dy=(x-st0[0],y-st0[1]) if st0 else (0,1)
        moving=abs(dx)+abs(dy)>0.05
        sxd,syd=(dx-dy)*2,(dx+dy)
        dr=('right' if sxd>0 else 'left') if abs(sxd)>abs(syd)*1.2 else ('down' if syd>0 else 'up')
        if not moving: dr='down'
        out.append((x,y,sf(pp['id'],dr,(int(t*8+pp['ph']*3)%4) if moving else 0)))
        if pp['id'] in REG and z>=2.4 and not (43.3<=t<57.2): names.append((abs(px-cx)+abs(py-cy),x,y,pp['id']))
        if len(out)>80: break
    names=[n[1:] for n in sorted(names)[:3]]
    C=count_at(t)
    for i,l in enumerate(house_lots):
        p=house_p(i,C)
        if 0<p<1:
            lx_,ly_=lot(*l)
            for j in range(2): out.append((lx_+4+j*12,ly_+22,sf(8000+(i+j)%6,'down',int(t*6+j)%2*2,'pedreiro')))
    if 36.2<=t<42.8:                               # pedreiros no campo
        p=campo_p(t)
        for k in range(4):
            x=FX0+(FX1-FX0)*clamp(min(p/0.3,1)*0.9+0.03*k) if p<0.3 else FX0+8+k*20+math.sin(t*2+k)*6
            out.append((x,FY0+6+k*10,sf(8030+k,'right' if p<0.3 else 'down',int(t*8+k)%4,'pedreiro')))
    tp,tn=team_people(t); out+=tp+torcida(t)+dog_people(t)+farm_people(t)
    return out,names,tn

# ---------- telas especiais ----------
_BG={}
def blur_bg(key,t,cam,dim=0.55):
    if key not in _BG:
        old=iso.VOX; iso.VOX=False; iso.K=2
        bg=iso.render_view(t,cam,[]).filter(ImageFilter.GaussianBlur(10))
        _BG[key]=Image.fromarray((np.array(bg)*dim).astype(np.uint8)); iso.VOX=old
    return _BG[key].copy()
SHOWIDS=None
def vitrine(t):
    """21.0-25.9: um morador de bloco grandão, girando, com o visual escolhido no site"""
    global SHOWIDS
    if SHOWIDS is None: SHOWIDS=[12,26,11,83,621,2,154,67,614,189,555,473]
    fr=blur_bg('vit',45.0,CI(132,248,1.0)); d=ImageDraw.Draw(fr,'RGBA')
    for k in range(5): d.polygon([(540,260),(380-k*30,1450),(700+k*30,1450)],fill=(255,240,200,8))
    d.polygon([(340,1440),(540,1340),(740,1440),(540,1540)],fill=(80,70,120,255)); d.polygon([(340,1440),(540,1540),(540,1580),(340,1480)],fill=(60,50,96,255))
    d.polygon([(540,1540),(740,1440),(740,1480),(540,1580)],fill=(44,38,76,255))
    if t<23.2:
        pid=12; seq=['down','right','up','left']; dr=seq[int((t-21.0)/0.55)%4]
    else:
        idx=int((t-23.2)/0.45)%len(SHOWIDS); pid=SHOWIDS[idx]; dr=['down','right'][idx%2]
    s=npc_k(pid,dr,0,2).resize((32*15,48*15),Image.NEAREST)
    fr.paste(s,(540-s.width//2,1440-s.height),s)
    nm=nome_tela(REG[pid]['nome']) if pid in REG else ''
    return fr,nm
CANDS=[(12,"CRISTIANO RONALDO"),(347,"JOÃO GUILHERME"),(154,"WESLEY"),(67,"KIRA"),(614,"ENZO MILDANA"),(11,"ISABELY67"),
       (2,"DIDI"),(189,"CABELUDO"),(621,"BACHIRAPRO"),(647,"SALES"),(426,"MT")]
PROM={0:("CAMPO GRÁTIS!",69.57),2:("LANCHONETE!",71.06),5:("LANCHONETE!",71.06),8:("PASTEL COM CALDO DE CANA!",72.06),1:("REFRI GELADINHO!",73.64)}
_HEADS={}
def head_img(pid):
    if pid not in _HEADS:
        s=npc_k(pid,'down',0,2); s=s.crop(s.getbbox()); _HEADS[pid]=s.crop((0,0,s.width,int(s.height*0.5)))
    return _HEADS[pid]
def mural(t):
    fr=blur_bg('mural',70.0,CI(160,424,3.0),0.5)
    a,b=T['eleicao']
    lay=Image.new('RGBA',(OUTW,OUTH),(0,0,0,0)); d=ImageDraw.Draw(lay)
    cols=[(214,50,50),(40,90,190),(40,150,80),(240,180,40),(150,80,180),(230,120,40)]
    for k,(pid,nm) in enumerate(CANDS):
        t0=a+0.35+k*0.22; v=clamp((t-t0)/0.2)
        if v<=0: continue
        r,c=divmod(k,3) if k<9 else (3,k-9+0.5)
        x=int(100+c*300); y=470+r*300+int((1-v)*40)
        hl=k in PROM and t>=PROM[k][1]
        d.rectangle([x,y,x+270,y+270],fill=cols[k%6]+(255,),outline=(255,255,255,255),width=6 if hl else 3)
        d.rectangle([x+12,y+12,x+258,y+190],fill=(250,246,232,255))
        h=head_img(pid); sc=int(min(220/h.width,170/h.height)); h2=h.resize((int(h.width*sc),int(h.height*sc)),Image.NEAREST)
        lay.paste(h2,(x+135-h2.width//2,y+196-h2.height),h2)
        d.rectangle([x+12,y+198,x+258,y+258],fill=(24,22,52,255))
        sc_=2 if text_width(nm,2)*4<=240 else 1
        tw=text_width(nm,1)
        im=Image.new('RGBA',(tw+4,12),(0,0,0,0)); draw_text(ImageDraw.Draw(im),nm,(tw+4)//2,2,1,WHITE)
        f=min(4,236/(tw+4)); im=im.resize((int((tw+4)*f),int(12*f)),Image.NEAREST)
        lay.paste(im,(x+135-im.width//2,y+228-im.height//2),im)
    fr=fr.convert('RGBA'); fr.alpha_composite(lay)
    return fr.convert('RGB')
def mural_ui(d,t):
    a,b=T['eleicao']
    box(d,14,58,256,98,(200,40,50,240)); draw_text(d,"ELEIÇÃO PRA PREFEITO",135,66,1,WHITE)
    draw_text(d,"PEGOU FOGO!" if t<67.78 else "11 CANDIDATOS!",135,80,1 if t<67.78 else 1,YEL)
    for k,(txt,t0) in PROM.items():
        if t<t0: continue
        r,c=divmod(k,3) if k<9 else (3,k-9+0.5)
        x=(100+c*300+135)/4; y=(470+r*300)/4-8
        if k==5: continue
        bob=int(math.sin(t*5+k)*1.5)
        w=text_width(txt,1)+10; x=clamp(x,w/2+4,W-w/2-4)
        d.rectangle([x-w/2,y-6+bob,x+w/2,y+8+bob],fill=(255,255,255,255),outline=(24,22,52,255))
        d.polygon([(x-3,y+8+bob),(x+3,y+8+bob),(x,y+12+bob)],fill=(255,255,255,255))
        draw_text(d,txt,x,y-2+bob,1,(200,40,50,255))

# ---------- UI ----------
def fireworks(d,t,t_ini,n=9,ys=(90,230)):
    rr=random.Random(int(t_ini*10))
    for k in range(n):
        t0=t_ini+k*0.18; age=t-t0
        cx=rr.uniform(30,240); cy=rr.uniform(*ys); col=[(255,90,90),(255,214,70),(120,230,110),(120,180,255),(240,120,240)][k%5]
        if age<0 or age>1.4: continue
        if age<0.25:
            y=cy+50*(1-age/0.25); d.rectangle([cx-1,y,cx+1,y+3],fill=(255,240,200,255)); continue
        a=age-0.25; R=a*50; fade=int(255*clamp(1-a/1.1))
        for j in range(12):
            ang=j/12*2*math.pi
            x=cx+math.cos(ang)*R; y=cy+math.sin(ang)*R+a*a*24
            s=3 if a<0.5 else 2
            d.rectangle([x,y,x+s,y+s],fill=col+(fade,))
def chat(d,t,a):
    msgs=[("MINHA PROPOSTA É MELHOR!",WHITE),("A MINHA QUE É!",LBLUE),("E O CAMPO?? JÁ TEM!",GREEN),("VOTA EM MIM!",YEL),("NÃO, EM MIM!",WHITE),("KKKKKKK",GREEN)]
    box(d,20,140,250,290,(10,10,24,215))
    d.rectangle([28,146,60,156],fill=(220,40,40,255)); draw_text(d,"AO VIVO",44,148,1,WHITE); draw_text(d,"CHAT",160,148,1,LBLUE)
    n=int((t-a-0.2)/0.3)+1
    for k,(m,c) in enumerate(msgs[:max(0,n)][-6:]):
        draw_text(d,m,135,166+k*19,1,c)
def blocos_icone(d,cx,cy,s,top,left,right):
    d.polygon([(cx,cy-s),(cx+s*1.7,cy-s*0.15),(cx,cy+s*0.7),(cx-s*1.7,cy-s*0.15)],fill=top)
    d.polygon([(cx-s*1.7,cy-s*0.15),(cx,cy+s*0.7),(cx,cy+s*2.1),(cx-s*1.7,cy+s*1.25)],fill=left)
    d.polygon([(cx,cy+s*0.7),(cx+s*1.7,cy-s*0.15),(cx+s*1.7,cy+s*1.25),(cx,cy+s*2.1)],fill=right)
def draw_ui(t,cam,mode,tnames):
    ui=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ui)
    C=count_at(t); hs=nhouses(C)
    if t>=3.9 and mode not in ('vit','mural'):
        y0=36
        box(d,32,y0,238,y0+42)
        draw_text(d,"SEGUIDORES",86,y0+7,1,LBLUE); draw_text(d,"CASAS",192,y0+7,1,LBLUE)
        d.line([150,y0+6,150,y0+36],fill=(120,120,180,255))
        draw_text(d,str(C),86,y0+20,2,YEL if C!=count_at(t-0.12) else WHITE)
        draw_text(d,str(hs),192,y0+20,2,YEL if hs!=nhouses(count_at(t-0.4)) else WHITE)
    a,b=T['titulo']
    if pop(t,a,b)>0:
        v=pop(t,a,b)
        box(d,20,118,250,208,(24,22,52,int(225*v)))
        draw_text(d,"A CIDADE DOS",135,130,2,WHITE); draw_text(d,"SEGUIDORES",135,152,3,YEL)
        draw_text(d,"EPISÓDIO 8",135,188,1,LBLUE)
    # recap
    banner(d,["DA ÚLTIMA VEZ:"],110,t,4.3,10.3,[LBLUE],1)
    banner(d,["647 MORADORES"],134,t,4.6,10.3,[YEL],2)
    banner(d,["64 CASAS"],166,t,5.4,10.3,[WHITE],2)
    if 10.4<=t<13.5:
        sx,sy=w2si(FXM,FYM,cam,4); tag_s(d,"TERRENO VAZIO... ESPERANDO O 700",sx,sy,t,10.4,13.4,YEL,dy=-40)
    banner(d,["MAS ANTES..."],120,t,13.7,15.3,[WHITE],2)
    banner(d,["OLHA COMO A CIDADE","TÁ CRESCENDO!"],120,t,14.4,16.95,[WHITE,YEL],2)
    for k,(w_,t0,t1) in enumerate((("CASA NOVA",17.1,20.9),("ÁRVORE",18.7,20.9),("RUA CHEIA DE GENTE!",19.9,20.9))):
        chip(d,w_,135,330+k*20,t,t0,t1,[YEL,GREEN,LBLUE][k])
    if mode=='vit':
        banner(d,["CADA MORADOR"],70,t,21.0,25.85,[YEL],2)
        banner(d,["COM O VISUAL","QUE VOCÊS ESCOLHERAM"],392,t,21.5,25.85,[WHITE,GREEN],1)
    # casas
    banner(d,["A RUA E ENCHEU!"],110,t,26.2,33.0,[GREEN],2)
    if mode=='vox' and 25.9<=t<33.1:
        for n,t0 in ((65,28.3),(66,29.5),(67,30.5),(72,31.9)):
            x,y=lot(*house_lots[n-1]); sx,sy=w2si(x+10,y+12,cam,22)
            tag_s(d,f"CASA {n}" if n<72 else "ATÉ A CASA 72!",sx,sy,t,t0,33.0,GREEN if n<72 else YEL)
    # 700
    banner(d,["QUASE..."],120,t,33.4,35.6,[WHITE],3)
    if 35.65<=t<37.0:
        v=pop(t,35.65,37.0); s=int(4+2*clamp((t-35.65)/0.25))
        box(d,30,130,240,230,(200,40,50,240)); draw_text(d,"700!",135,150,6,YEL)
        draw_text(d,"NOVO MARCO DESBLOQUEADO",135,208,1,WHITE)
        fireworks(d,t,35.7,8)
    banner(d,["CAMPO DE FUTEBOL!"],110,t,36.9,43.2,[YEL],2)
    for k,(w_,t0) in enumerate((("GRAMA NOVA",38.38),("LINHAS PINTADAS",39.32),("TRAVES",40.63),("ARQUIBANCADA",41.70))):
        chip(d,w_,135,330+k*20,t,t0,43.2,[GREEN,WHITE,YEL,LBLUE][k])
    banner(d,["PRONTO!"],420,t,42.5,43.25,[GREEN],3)
    # o time
    banner(d,["O TIME DA CIDADE"],108,t,43.6,49.4,[YEL],2)
    if 43.3<=t<49.5 and tnames:
        for (pid,pos,x,y) in tnames:
            sx,sy=w2si(x,y,cam,20)
            if pid not in REG: continue
            nm=nome_tela(REG[pid]['nome'])
            if pos in ('ATACANTE','MEIA','GOLEIRO'):
                t0={'ATACANTE':45.86,'MEIA':47.06,'GOLEIRO':48.56}[pos]
                if t>=t0: nm=nm+" - "+pos
            t0,t1={12:(45.86,47.0),555:(45.86,47.0),168:(47.06,48.5),348:(47.06,48.5),441:(48.56,49.45),236:(44.3,45.8),473:(44.3,45.8)}[pid]
            tag_s(d,nm,sx,sy,t,t0,t1,YEL if pos else WHITE,dy=-34)
    chip(d,"TOCA PRA LÁ...",80,330,t,51.0,52.0,WHITE)
    chip(d,"...TOCA PRA CÁ!",190,350,t,52.0,53.6,WHITE)
    if 53.72<=t<55.4:
        v=clamp((t-53.72)/0.15); sc=int(3+3*v)
        y=150+int(math.sin(t*20)*3)
        draw_text(d,"GOOOL!",135,y,sc,YEL)
        fireworks(d,t,53.75,10,(80,260))
    banner(d,["VIRA-LATA EM CAMPO!"],120,t,55.0,57.0,[YEL],2)
    # fazenda
    if mode=='vox' and 58.5<=t<64.8:
        sx,sy=w2si(FARMER[0],FARMER[1],cam,20); tag_s(d,"O FAZENDEIRO",sx,sy,t,59.2,61.6,YEL,dy=-34)
    banner(d,["VIZINHO NOVO!"],110,t,57.6,64.7,[GREEN],2)
    banner(d,["CONTRATOU","MORADORES!"],380,t,61.97,64.7,[WHITE,YEL],2)
    if mode=='mural': mural_ui(d,t)
    # entregaram
    banner(d,["4 DE 11 CANDIDATOS","PROMETERAM CAMPO..."],110,t,75.8,80.4,[WHITE,YEL],1)
    if 78.79<=t<80.45:
        v=clamp((t-78.79)/0.2)
        lay=Image.new('RGBA',(220,64),(0,0,0,0)); dl=ImageDraw.Draw(lay)
        dl.rectangle([2,2,217,61],outline=(60,220,90,255),width=4); dl.rectangle([7,7,212,56],outline=(60,220,90,255),width=1)
        draw_text(dl,"OS SEGUIDORES",110,14,1,(60,220,90,255)); draw_text(dl,"ENTREGARAM!",110,32,2,(60,220,90,255))
        sc=1+(1-v)*1.2; lay=lay.resize((int(220*sc),int(64*sc)),Image.NEAREST).rotate(8,expand=True)
        ui.alpha_composite(lay,(135-lay.width//2,330-lay.height//2))
    # chat
    a,b=T['chat']
    if a<=t<b:
        chat(d,t,a)
        v=pop(t,82.4,b)
        if v>0:
            bx_,by_=135,350+int(math.sin(t*6)*2)
            d.rounded_rectangle([bx_-110,by_-26,bx_+110,by_+26],radius=10,fill=(255,255,255,255),outline=(24,22,52,255),width=2)
            d.polygon([(bx_-20,by_+25),(bx_,by_+25),(bx_-30,by_+40)],fill=(255,255,255,255))
            draw_text(d,"VAMO ACALMA!",135,by_-18,2,(200,40,50,255)); draw_text(d,"TÁ PARECENDO ELEIÇÃO DE VERDADE",135,by_+8,1,(24,22,52,255))
    # próximo marco
    a,b=T['proximo']
    if a<=t<b:
        v=pop(t,a,b)
        box(d,30,110,240,250,(24,22,52,235)); draw_text(d,"PRÓXIMO MARCO",135,120,1,LBLUE)
        draw_text(d,"800",135,138,5,YEL)
        if t>=85.6:
            blocos_icone(d,92,196,9,(232,190,120,255),(196,150,90,255),(170,124,72,255))
            d.rectangle([84,190,100,193],fill=(250,240,220,255))
            blocos_icone(d,178,196,9,(240,180,60,255),(200,90,50,255),(120,180,60,255))
        draw_text(d,"PADARIA E LANCHONETE",135,230,1,WHITE) if t>=86.2 else None
        banner(d,["FALTAM 79!"],380,t,88.28,b,[YEL],3)
    # resumo
    a,b=T['resumo']
    banner(d,["RESULTADO:"],84,t,90.1,b,[LBLUE],1)
    banner(d,[f"{C1} MORADORES"],110,t,91.09,b,[YEL])
    banner(d,[f"{NH} CASAS"],146,t,92.99,b,[WHITE])
    banner(d,["E UM CAMPO","DE FUTEBOL!"],330,t,94.53,b,[WHITE,GREEN])
    a,b=T['cta']
    v=pop(t,a,b+1,0.01)
    if v>0:
        yy=110+int((1-v)*14)
        box(d,24,yy,246,yy+62,(200,40,50,240))
        draw_text(d,"LINK NA BIO!",135,yy+10,2,WHITE); draw_text(d,"ESCOLHE O TEU MORADOR",135,yy+38,1,YEL)
        if t>=99.3: banner(d,["E VEM JOGAR NO CAMPO","DE PINDAMONHANGABA!"],370,t,99.3,b+1,[WHITE,GREEN],1)
    return ui

def names_layer(t,cam,names):
    if not names: return None
    lay=Image.new('RGBA',(W*2,H*2),(0,0,0,0)); d=ImageDraw.Draw(lay)
    for (x,y,pid) in names:
        sx,sy=w2si(x,y,cam,22)
        nm=nome_tela(REG[pid]['nome'])
        if not nm: continue
        X=int(sx*2); Y=int(sy*2)-8
        tw=text_width(nm,1)+6
        d.rectangle([X-tw//2,Y-2,X+tw//2,Y+8],fill=(24,22,52,200)); draw_text(d,nm,X,Y,1,YEL)
    return lay.resize((OUTW,OUTH),Image.NEAREST)

def placa_texto(fr,cam):
    """PINDAMONHANGABA pintado em alta no pórtico (32 bits: placa inclinada do ep. 7; blocos: face do letreiro)"""
    cx,cy,Z=cam
    def O(x,y,z): px,py=iso.PW(x,y,z); return ((px-(cx-540/Z))*Z,(py-(cy-960/Z))*Z)
    if iso.VOX:
        y=vox.PORTAL_Y; I0,I1=vox.gi(PLACA_X0),vox.gi(PLACA_X1)
        xa,xb=I0*vox.B+1.6,(I1+1)*vox.B-1.6; za,zc=25*vox.B-0.6,18*vox.B+0.6
        q=[O(xa,y,za),O(xb,y,za),O(xb,y,zc),O(xa,y,zc)]
    else:
        zb,ztop,ytop=26.0,38.0,PLACA_Y; m=0.06
        xa,xb=PLACA_X0+(PLACA_X1-PLACA_X0)*m,PLACA_X1-(PLACA_X1-PLACA_X0)*m
        za,zc=ztop-(ztop-zb)*0.18,zb+(ztop-zb)*0.18
        q=[O(xa,ytop,za),O(xb,ytop,za),O(xb,ytop,zc),O(xa,ytop,zc)]
    if max(p[0] for p in q)<-50 or min(p[0] for p in q)>OUTW+50 or max(p[1] for p in q)<-50 or min(p[1] for p in q)>OUTH+50: return fr
    if not hasattr(placa_texto,'tex'):
        nome=NOME_CIDADE; tw=text_width(nome,4)+8
        im=Image.new('RGBA',(tw,44),(0,0,0,0)); dd=ImageDraw.Draw(im)
        draw_text(dd,nome,tw//2,6,4,(255,236,140,255),outline=(70,40,20,255)); placa_texto.tex=im
    tex=placa_texto.tex; w,h=tex.size
    A=[];B_=[]
    for (X,Y),(u,v) in zip(q,[(0,0),(w,0),(w,h),(0,h)]):
        A.append([X,Y,1,0,0,0,-u*X,-u*Y]); B_.append(u); A.append([0,0,0,X,Y,1,-v*X,-v*Y]); B_.append(v)
    try: co=np.linalg.solve(np.array(A,float),np.array(B_,float))
    except np.linalg.LinAlgError: return fr
    lay=tex.transform((OUTW,OUTH),Image.PERSPECTIVE,tuple(co),Image.BILINEAR)
    f2=fr.convert('RGBA'); f2.alpha_composite(lay); return f2.convert('RGB')

def flash(fr,k):
    a=np.array(fr).astype(np.float32); a=a+(255-a)*k
    return Image.fromarray(a.astype(np.uint8))
def grade(fr):
    a=np.array(fr).astype(np.float32)
    a*=np.array([1.04,1.0,0.95]); lum=a.mean(axis=2,keepdims=True); a=lum+(a-lum)*1.1
    if not hasattr(grade,'v'):
        yy,xx=np.mgrid[0:OUTH,0:OUTW]; v=np.hypot((xx-OUTW/2)/(OUTW/2),(yy-OUTH/2)/(OUTH/2))
        grade.v=(1-0.28*np.clip(v-0.6,0,1))[:,:,None]
    a=a*grade.v
    return Image.fromarray(np.clip(a,0,255).astype(np.uint8))

TILE=60
_tr=random.Random(88)
_TT={(i,j):15.35+(j/32)*0.55+_tr.uniform(0,0.45) for i in range(OUTW//TILE) for j in range(OUTH//TILE)}
def view_frame(t,vox_on):
    iso.VOX=vox_on; iso.K=2
    cam=camiso(t)
    ppl,names,tn=iso_people(t,cam)
    ex=ball_extra(t)
    fr=iso.render_view(t,cam,ppl,ex,None)
    fr=placa_texto(fr,cam)
    return fr,cam,names,tn
def render_frame(tv):
    return _frame(new2old(tv))
def _frame(t):
    names=None; tn=[]; cam=camiso(t)
    if 21.0<=t<25.9:
        mode='vit'; fr,nm=vitrine(t)
    elif T['eleicao'][0]<=t<T['eleicao'][1]:
        mode='mural'; fr=mural(t)
    elif False:
        a,cam,_,_=view_frame(t,False); b,cam,names,tn=view_frame(t,True)
        a=grade(a); b=grade(b)
        A=np.array(a); Bm=np.array(b); out=A.copy()
        for (i,j),ts in _TT.items():
            f=clamp((t-ts)/0.28)
            if f<=0: continue
            x0,y0=i*TILE,j*TILE
            if f>=1: out[y0:y0+TILE,x0:x0+TILE]=Bm[y0:y0+TILE,x0:x0+TILE]; continue
            dy=int((1-f)**2*-220)
            ys=max(0,y0+dy); ye=y0+TILE+dy
            if ye>0:
                out[ys:ye,x0:x0+TILE]=Bm[y0+(ys-(y0+dy)):y0+TILE,x0:x0+TILE]
                out[ys:min(ye,ys+4),x0:x0+TILE]=(out[ys:min(ye,ys+4),x0:x0+TILE]*0.7+255*0.3).astype(np.uint8)
        fr=Image.fromarray(out); mode='vox'
    else:
        fr,cam,names,tn=view_frame(t,False)
        fr=grade(fr); mode='vox'
    if mode in ('vit','mural'): pass
    for t0,dur,k in ((35.65,0.3,0.7),(53.72,0.25,0.5)):
        if t0<=t<t0+dur: fr=flash(fr,(1-(t-t0)/dur)*k)
    for cut in (21.0,25.9,57.0,64.8,75.4,80.5,84.5,89.7,96.7,4.6,10.2):
        if cut<=t<cut+0.1: fr=flash(fr,(1-(t-cut)/0.1)*0.35)
    fr=fr.convert('RGBA')
    if names:
        nl=names_layer(t,cam,names)
        if nl is not None: fr.alpha_composite(nl)
    ui=draw_ui(t,cam,mode,tn).resize((OUTW,OUTH),Image.NEAREST)
    fr.alpha_composite(ui)
    if mode=='vit':
        nm=vitrine(t)[1] if False else None
    return fr.convert('RGB')

if __name__=='__main__':
    out=sys.argv[1]
    for t in map(float,sys.argv[2:]):
        render_frame(t).save(f'{out}/frame_{t:05.1f}.png')

DUR=DUR_VIDEO
