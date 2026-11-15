import numpy as np, math, random, sys, json, os
from PIL import Image, ImageDraw
from world import *
from scene import *
from font import draw_text, text_width
from vila16 import compose16, L2, SIGN, TREE16
from world16 import S, make_ground16_h
import vila16 as V
import iso

# =====================================================================
#  EP. 6 — começa em 16 bits, o mapa cresce, e vira ISOMÉTRICO (iso.py)
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

# ---------- câmera 16 bits (mapa de 480, e na hora do crescimento, 680) ----------
CAM16=[(0,(131,300,150)),(4.6,(131,300,150)),(6.1,WIDE),(8.2,WIDE),(9.0,(105,346,150)),(T['cresce1'][1],(105,346,150)),
       (T['marco'][0]+0.8,WIDE),(T['lotado'][1],WIDE),(T['cresce'][0]+0.8,(132,360,220)),(GROW[1],(132,500,250)),(99,(132,500,250))]
def cam16(t):
    for (a,va),(b,vb) in zip(CAM16,CAM16[1:]):
        if a<=t<b:
            f=smooth((t-a)/(b-a)); c=tuple(va[i]+(vb[i]-va[i])*f for i in range(3)); break
    else: c=CAM16[-1][1]
    cx,cy,vw=c; vh=vw*H/W
    hh=MH6 if t>=T['cresce'][0] else H
    return (clamp(cx,vw/2,W-vw/2),clamp(cy,vh/2,hh-vh/2),vw)
def w2s16(x,y,cam):
    cx,cy,vw=cam; vh=vw*H/W; s=W/vw
    return (x-(cx-vw/2))*s,(y-(cy-vh/2))*s

# ---------- mapa 16 bits "grande" (o de sempre + a parte nova de baixo) ----------
_EXT=None
def ext16():
    global _EXT
    if _EXT is None:
        G=make_ground16_h(MH6,(ROADD,ROADE,ROADF),True)[0]
        im=Image.fromarray(G[H*S:]).convert('RGBA')
        for tr in TREES6:
            if tr['y']<=H: continue
            ti,(ax,ay)=TREE16(tr['r'],tr['k'],0)
            im.paste(ti,(int(tr['x']*S)-ax,int((tr['y']-H)*S)-ay),ti)
        _EXT=np.array(im.convert('RGB'))
    return _EXT
_FORA=None
def fora16():
    """campo de fora (visto de cima) na faixa nova do mapa, pra mostrar antes de 'desenrolar'"""
    global _FORA
    if _FORA is None:
        hh,ww=(MH6-H)*S,W*S
        ly,lx=np.mgrid[0:hh,0:ww].astype(np.float32)/S
        ly+=MH6+40                              # usa um pedaço de campo de fora (sem rua)
        a=iso.terreno_l(lx,ly).astype(np.float32)
        _FORA=(a*np.array([0.62,0.68,0.62])).astype(np.uint8)
    return _FORA
def big16(t):
    top=compose16(t,0.0,None)
    g=grow_f(t)
    if g<=0 and t<T['cresce'][0]: return top
    ext=ext16().copy()
    rev=H+g*(MH6-H)                                  # até onde o mapa já "desenrolou"
    ys=np.arange(ext.shape[0])/S+H
    xs=np.arange(ext.shape[1])/S
    edge=rev+np.sin(xs*0.4+t*6)*2.2
    m=ys[:,None]>edge[None,:]
    ext[m]=fora16()[m]
    # borda que desenrola (terra)
    band=(ys[:,None]>edge[None,:]-3)&~m
    ext[band]=(ext[band]*0.5+np.array([150,104,64])*0.5).astype(np.uint8)
    return np.vstack([top,ext])

def crop_arr(a,cam):
    cx,cy,vw=cam; vh=vw*H/W
    img=Image.fromarray(a)
    return img.resize((OUTW,OUTH),Image.NEAREST,box=((cx-vw/2)*S,(cy-vh/2)*S,(cx+vw/2)*S,(cy+vh/2)*S))

# ---------- câmera ISO ----------
def CI(x,y,z): px,py=iso.PW(x,y); return (px,py,z)
CAMISO=[(33.0,CI(135,365,0.75)),(34.9,CI(135,365,0.75)),
        (35.6,CI(60,168,3.0)),(37.9,CI(105,168,3.0)),
        (38.6,CI(158,414,2.6)),(40.2,CI(172,410,2.6)),
        (41.0,CI(138,505,2.3)),(44.0,CI(146,505,2.3)),
        (44.7,CI(112,532,3.0)),(47.9,CI(116,532,3.0)),
        (48.7,CI(178,606,2.2)),(54.3,CI(178,606,2.2)),
        (55.0,CI(160,414,2.6)),(56.5,CI(160,414,2.6)),(57.3,CI(150,446,3.2)),(59.2,CI(150,446,3.2)),
        (59.9,CI(132,248,2.4)),(64.8,CI(132,248,2.4)),
        (65.6,CI(135,190,0.9)),(70.9,CI(135,560,0.9)),
        (71.7,CI(135,365,0.75)),(99,CI(135,365,0.75))]
def camiso(t):
    for (a,va),(b,vb) in zip(CAMISO,CAMISO[1:]):
        if a<=t<b:
            f=smooth((t-a)/(b-a)); return tuple(va[i]+(vb[i]-va[i])*f for i in range(3))
    return CAMISO[-1][1] if t>=CAMISO[-1][0] else CAMISO[0][1]
def w2si(x,y,cam,z_=0):
    cx,cy,zz=cam; px,py=iso.PW(x,y,z_)
    return ((px-(cx-540/zz))*zz/4,(py-(cy-960/zz))*zz/4)

# ---------- virada 16 bits -> isométrico ----------
MORPH=(32.0,33.3)
PADL=620                                     # campo em volta do mapa 16 bits durante a virada
_PADBG=None
def padded16(t):
    """mapa 16 bits + campo infinito em volta (mesmo terreno do isométrico, visto de cima)"""
    global _PADBG
    if _PADBG is None:
        hh,ww=(MH6+2*PADL)*S,(W+2*PADL)*S
        ly,lx=np.mgrid[0:hh,0:ww].astype(np.float32)/S-PADL
        _PADBG=iso.terreno_l(lx,ly)
    a=_PADBG.copy()
    b=big16(t)
    a[PADL*S:PADL*S+b.shape[0],PADL*S:PADL*S+b.shape[1]]=b
    return a
def morph_frame(t):
    f=smooth(clamp((t-MORPH[0])/(MORPH[1]-MORPH[0])))
    src=Image.fromarray(padded16(t))
    c16=cam16(t); cx,cy,vw=c16; vh=vw*H/W; s=OUTW/vw
    A0=np.array([[s,0,-(cx-vw/2)*s],[0,s,-(cy-vh/2)*s]])
    icx,icy,z=camiso(MORPH[1])
    A1=np.array([[2*z,-2*z,(iso.OX-(icx-540/z))*z],[z,z,(iso.OY-(icy-960/z))*z]])
    A=A0*(1-f)+A1*f
    M=np.vstack([A,[0,0,1]]); Mi=np.linalg.inv(M)
    # saída -> lógico -> pixel da fonte (2x)
    a,b,c=Mi[0]*S; d_,e,f_=Mi[1]*S
    c+=PADL*S; f_+=PADL*S
    out=Image.new('RGB',(OUTW,OUTH),(150,206,242))
    w=src.transform((OUTW,OUTH),Image.AFFINE,(a,b,c,d_,e,f_),resample=Image.NEAREST,fillcolor=(84,150,66))
    return w

# ---------- moradores no isométrico ----------
def iso_people(t,cam):
    cx,cy,z=cam; vw,vh=1080/z,1920/z
    out=[]; names=[]
    for pp in people:
        st=person_state(pp,t)
        if st is None: continue
        x,y=st[0],st[1]
        px,py=iso.PW(x,y)
        if not (cx-vw/2-20<px<cx+vw/2+20 and cy-vh/2-30<py<cy+vh/2+30): continue
        st0=person_state(pp,t-0.08)
        dx,dy=(x-st0[0],y-st0[1]) if st0 else (0,1)
        moving=abs(dx)+abs(dy)>0.05
        # direção na tela iso
        sxd,syd=(dx-dy)*2,(dx+dy)
        dr=('right' if sxd>0 else 'left') if abs(sxd)>abs(syd)*1.2 else ('down' if syd>0 else 'up')
        if not moving: dr='down'
        out.append((x,y,V.NPC(pp['id'],dr,(int(t*8+pp['ph']*3)%4) if moving else 0)))
        if pp['id'] in REG and z>=2.0: names.append((abs(px-cx)+abs(py-cy),x,y,pp['id']))
        if len(out)>80: break
    names=[n[1:] for n in sorted(names)[:3]]
    # pedreiros nas obras
    C=count_at(t)
    obras=[]
    for i,l in enumerate(house_lots):
        p=house_p(i,C)
        if 0<p<1: lx_,ly_=lot(*l); obras.append((lx_+10,ly_+22))
    for p_,l,w_ in ((merc2_p(t),MERCADO2,21),(posto_p(t),POSTO[0],44)):
        if 0<p_<1: lx_,ly_=lot(*l); obras.append((lx_+w_*0.3,ly_+23)); obras.append((lx_+w_*0.8,ly_+23))
    for k,(ox,oy) in enumerate(obras):
        for j in range(2):
            fr=int(t*6+k+j)%2
            out.append((ox-6+j*12,oy,V.NPC(8000+(k+j)%6,'down',0,'pedreiro','up' if fr else 'down')))
    # jogadores esperando o campo (marco 700)
    if T['campo'][0]-0.5<t<T['campo'][1]+0.3:
        lx_,ly_=lot(*CAMPO[0])
        for k in range(4):
            out.append((lx_+30+k*8,ly_-2,V.NPC(9100+k,'down' if k!=1 else 'up',0)))
    return out,names

def extra_iso(t):
    ex=[]
    if T['campo'][0]-0.5<t<T['campo'][1]+0.3:
        lx_,ly_=lot(*CAMPO[0]); bx,by=lx_+38,ly_-0.5
        h=abs(math.sin(t*5))*9
        def ball(vd,vx0,vy0,bx=bx,by=by,h=h):
            X,Y=iso.PW(bx,by,h); X-=vx0; Y-=vy0
            vd.ellipse([X-2,Y-2,X+2,Y+2],fill=(255,255,255),outline=(30,30,30)); vd.point((X,Y),fill=(30,30,30))
        ex.append((bx+by+0.6,('fn',ball)))
    return ex

def pop_iso(t):
    t0=33.25
    if t>=t0+1.6: return None
    dmin,dmax=200,900
    def f(dep,bx,by):
        st=t0+clamp((dep-dmin)/(dmax-dmin))*1.0
        q=clamp((t-st)/0.35)
        return q+math.sin(q*math.pi)*0.15 if q<1 else 1.0
    return f

# ---------- UI ----------
def header(d,t):
    C=count_at(t); hs=nhouses(C)
    y0=36+int((1-smooth(t/0.6))*-60)
    box(d,32,y0,238,y0+42)
    draw_text(d,"SEGUIDORES",86,y0+7,1,LBLUE); draw_text(d,"CASAS",192,y0+7,1,LBLUE)
    d.line([150,y0+6,150,y0+36],fill=(120,120,180,255))
    draw_text(d,str(C),86,y0+20,2,YEL if C!=count_at(t-0.12) else WHITE)
    draw_text(d,str(hs),192,y0+20,2,YEL if hs!=nhouses(count_at(t-0.4)) else WHITE)

def icon_cart(d,x,y,c=(255,255,255,255)):
    d.rectangle([x,y,x+8,y+5],outline=c); d.line([x-2,y-2,x,y],fill=c); d.point((x+2,y+7),fill=c); d.point((x+6,y+7),fill=c)
def icon_cross(d,x,y):
    d.rectangle([x+3,y,x+6,y+9],fill=(40,170,90,255)); d.rectangle([x,y+3,x+9,y+6],fill=(40,170,90,255))

def arcade(d,t,t0,t1):
    v=pop(t,t0,t1)
    if v<=0: return
    x0,y0,x1,y1=40,196,230,330
    yy=int((1-v)*20)
    d.rectangle([x0-6,y0-6+yy,x1+6,y1+30+yy],fill=(60,40,120,255)); d.rectangle([x0-6,y0-6+yy,x1+6,y1+30+yy],outline=(255,255,255,255))
    d.rectangle([x0,y0+yy,x1,y1+yy],fill=(14,18,40,255))
    # mini jogo: bonequinho pulando caixas e pegando moedas
    gy=y1-20+yy
    d.line([x0,gy+8,x1,gy+8],fill=(120,230,110,255)); d.line([x0,gy+9,x1,gy+9],fill=(60,140,60,255))
    sc=(t*60)%220
    for k in range(4):
        bx=x1-((sc+k*55)%(x1-x0))
        d.rectangle([bx,gy,bx+7,gy+7],fill=(214,120,60,255)); d.rectangle([bx,gy,bx+7,gy+7],outline=(255,200,120,255))
        cy_=gy-22+int(math.sin(t*6+k)*2)
        if int(t*4+k)%3: d.ellipse([bx+1,cy_,bx+6,cy_+5],fill=(255,214,70,255))
    ph=(t*1.9)%1; jy=int(-abs(math.sin(ph*math.pi))*22)
    px_=x0+40
    d.rectangle([px_,gy-9+jy,px_+6,gy+7+jy],fill=(230,60,60,255)); d.rectangle([px_+1,gy-13+jy,px_+5,gy-9+jy],fill=(250,210,170,255))
    draw_text(d,"PONTOS "+str(int((t-t0)*37)%1000).zfill(3),x0+40,y0+6+yy,1,WHITE)
    if int(t*3)%2: draw_text(d,"PRESS START",135,y0+50+yy,2,YEL)
    # controle
    cx_,cy_=135,y1+16+yy
    d.rounded_rectangle([cx_-30,cy_-9,cx_+30,cy_+9],radius=8,fill=(220,220,230,255),outline=(40,40,60,255))
    d.rectangle([cx_-22,cy_-2,cx_-12,cy_+2],fill=(40,40,60,255)); d.rectangle([cx_-19,cy_-5,cx_-15,cy_+5],fill=(40,40,60,255))
    d.ellipse([cx_+12,cy_-4,cx_+18,cy_+2],fill=(230,60,60,255)); d.ellipse([cx_+19,cy_-1,cx_+25,cy_+5],fill=(70,120,230,255))

def draw_ui(t,cam,mode):
    ui=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ui)
    header(d,t)
    a,b=T['titulo']
    if pop(t,a,b)>0:
        draw_text(d,"A CIDADE DOS",135,130,2,WHITE); draw_text(d,"SEGUIDORES",135,152,3,YEL)
        draw_text(d,"EPISÓDIO 6",135,186,1,LBLUE)
    a,b=T['recap']
    banner(d,["ATÉ AGORA:"],120,t,6.2,b,[LBLUE],2)
    banner(d,[f"{C0} MORADORES",f"{C0//10} CASAS"],156,t,6.9,9.2,[YEL,WHITE],2)
    if mode=='16':
        if 9.3<=t<12.4:
            for i,l in enumerate(house_lots):
                if l[1]==ROADD and house_p(i,count_at(t))<=0:
                    x,y=lot(*l); p0=w2s16(x,y,cam); p1=w2s16(x+21,y+25,cam)
                    d.rectangle([int(p0[0]),int(p0[1]),int(p1[0]),int(p1[1])],outline=YEL if int(t*4)%2 else WHITE)
        chip(d,"SÓ 3 LOTES LIVRES",135,330,t,9.3,b,YEL)
        for n,t0 in ((58,12.6),(59,13.1),(60,13.7),(61,14.3)):
            x,y=lot(*house_lots[n-1]); sx,sy=w2s16(x+10,y+4,cam); tag_s(d,f"CASA {n}",sx,sy,t,t0,T['marco'][0]+0.6,GREEN)
    if 16.3<=t<17.9:
        draw_text(d,"600!",135,150,6 if int(t*5)%2 else 5,YEL)
    banner(d,["NOVO MARCO","DESBLOQUEADO!"],200,t,16.4,20.6,[WHITE,GREEN])
    v=pop(t,18.6,20.6)
    if v>0:
        box(d,30,262,240,284); icon_cart(d,44,270,(255,255,255,255)); draw_text(d,"MERCADINHO 2",140,269,1,YEL)
    v=pop(t,19.6,20.6)
    if v>0:
        box(d,30,290,240,312); icon_cross(d,42,296); draw_text(d,"POSTO DE SAÚDE",140,297,1,GREEN)
    # lotado
    banner(d,["CONSTRUIR ONDE?"],140,t,21.1,T['lotado'][1],[WHITE],2)
    if mode=='16' and 22.4<=t<T['lotado'][1]:
        blink=int(t*6)%2==0
        for l in house_lots[:NH]+[VENDA,MERCADO]+ESCOLA+PREFEITURA:
            x,y=lot(*l); w_=21
            p0=w2s16(x,y,cam); p1=w2s16(x+w_,y+25,cam)
            d.rectangle([int(p0[0]),int(p0[1]),int(p1[0]),int(p1[1])],outline=RED)
            if blink: d.rectangle([int(p0[0])+1,int(p0[1])+1,int(p1[0])-1,int(p1[1])-1],outline=RED)
        if 22.4<=t:
            box(d,40,300,230,330,(200,40,50,240)); draw_text(d,"MAPA LOTADO!",135,309,2,WHITE)
        # prédios "flutuando" sem lugar
        for k,fn in enumerate((icon_cart,icon_cross)):
            bx_,by_=95+k*70,380+int(math.sin(t*4+k)*5)
            box(d,bx_-14,by_-12,bx_+14,by_+12); fn(d,bx_-5,by_-4) if k else fn(d,bx_-4,by_-3,(255,255,255,255))
            draw_text(d,"?",bx_+18,by_-14,2,YEL)
    # cresce
    a,b=T['cresce']
    banner(d,["O MAPA","CRESCEU!"],120,t,26.1,b+0.2,[WHITE,GREEN],3)
    banner(d,["+ 2 RUAS NOVAS"],196,t,29.1,b+0.2,[YEL],2)
    if mode=='16':
        for nm,ry in (("RUA E",ROADE),("RUA F",ROADF)):
            sx,sy=w2s16(60,ry+5,cam); tag_s(d,nm,sx,sy,t,29.3 if nm=="RUA E" else 29.7,b+0.6,WHITE,-22)
    # evolução
    a,b=T['evolui']
    banner(d,["NOVA EVOLUÇÃO..."],130,t,31.0,33.1,[LBLUE],2)
    if 33.2<=t<35.3:
        sc=3
        box(d,22,118,248,186,(40,120,70,240))
        draw_text(d,"NOVA EVOLUÇÃO:",135,128,1,WHITE); draw_text(d,"ISOMÉTRICO!",135,148,sc,YEL)
    for k,(w_,t0) in enumerate((("TELHADO DE VERDADE",35.5),("JANELA",36.4),("CHAMINÉ",37.2))):
        chip(d,w_,135,330+k*20,t,t0,38.0,[YEL,LBLUE,GREEN][k])
    banner(d,["DÁ PRA VER","A LATERAL!"],130,t,38.1,b,[WHITE,YEL],2)
    if mode=='iso':
        # obras do marco 600
        x,y=lot(*MERCADO2); sx,sy=w2si(x+10,y+12,cam,22); tag_s(d,"MERCADINHO 2",sx,sy,t,41.9,T['obras'][1],YEL)
        x,y=lot(*POSTO[0]); sx,sy=w2si(x+21,y+12,cam,24); tag_s(d,"POSTO DE SAÚDE",sx,sy,t,43.2,T['obras'][1]+0.3,GREEN)
        x,y=lot(*house_lots[61]); sx,sy=w2si(x+10,y+12,cam,20); tag_s(d,"CASA 62",sx,sy,t,44.5,T['casa62'][1],YEL)
        x,y=lot(*PREFEITURA[0]); sx,sy=w2si(x+21,y+10,cam,40)
        if 54.8<t<56.6: draw_text(d,"?",int(sx),int(sy)-20+int(math.sin(t*5)*2),4,YEL)
        if 56.7<t<T['prefeito'][1]:
            sx,sy=w2si(149,446,cam,14)
            if int(t*3)%2: draw_text(d,"???",int(sx),int(sy)-12,2,YEL)
    banner(d,["COMEÇA EM 615","PRONTA EM 620"],330,t,45.0,T['casa62'][1],[WHITE,GREEN])
    chip(d,"A PRIMEIRA DA RUA E",135,380,t,46.4,T['casa62'][1],LBLUE)
    a,b=T['campo']
    banner(d,["PRÓXIMO MARCO:"],120,t,48.3,b,[LBLUE],1)
    banner(d,["700"],140,t,48.3,b,[YEL],4)
    banner(d,["CAMPO DE FUTEBOL"],190,t,49.8,b,[GREEN],2)
    chip(d,"TEM JOGADOR ESPERANDO...",135,390,t,51.0,b,WHITE)
    a,b=T['prefeito']
    banner(d,["EM BREVE:","PREFEITO"],120,t,54.8,56.6,[LBLUE,YEL],3)
    banner(d,["E O NOME","DA CIDADE..."],120,t,56.7,b,[WHITE,YEL],2)
    banner(d,["FICA DE OLHO!"],330,t,58.1,b,[GREEN],3)
    a,b=T['minigame']
    banner(d,["NOVIDADE!"],120,t,59.6,60.7,[YEL],3)
    arcade(d,t,60.7,b)
    banner(d,["MINIGAMES","EM BREVE!"],100,t,60.7,b,[WHITE,YEL],2)
    chip(d,"JOGA DENTRO DA CIDADE",135,390,t,63.0,b,GREEN)
    a,b=T['resumo']
    banner(d,["RESULTADO:"],84,t,65.2,b,[LBLUE],1)
    banner(d,[f"{C1} MORADORES"],110,t,65.8,b,[YEL])
    banner(d,[f"{NH} CASAS"],146,t,67.6,b,[WHITE])
    banner(d,["MAPA MAIOR"],330,t,69.1,b,[GREEN])
    banner(d,["VISUAL NOVO"],366,t,70.0,b,[GREEN])
    a,b=T['cta']
    v=pop(t,a,b,0.01)
    if v>0:
        yy=140+int((1-v)*14)
        box(d,24,yy,246,yy+62,(200,40,50,240))
        draw_text(d,"LINK NA BIO!",135,yy+10,2,WHITE); draw_text(d,"ESCOLHE O TEU MORADOR",135,yy+38,1,YEL)
        if t>73.6:
            banner(d,["PREPARA O","CONTROLE!"],300,t,73.6,b,[WHITE,YEL],3)
    return ui

def names_layer(t,cam,names):
    if not names: return None
    lay=Image.new('RGBA',(W*2,H*2),(0,0,0,0)); d=ImageDraw.Draw(lay)
    for (x,y,pid) in names:
        sx,sy=w2si(x,y,cam,20)
        nm=nome_tela(REG[pid]['nome'])
        if not nm: continue
        X=int(sx*2); Y=int(sy*2)-8
        tw=text_width(nm,1)+6
        d.rectangle([X-tw//2,Y-2,X+tw//2,Y+8],fill=(24,22,52,200)); draw_text(d,nm,X,Y,1,YEL)
    return lay.resize((OUTW,OUTH),Image.NEAREST)

def flash(fr,k):
    a=np.array(fr).astype(np.float32); a=a+(255-a)*k
    return Image.fromarray(a.astype(np.uint8))

def render_frame(t):
    names=None
    if t<MORPH[0]:
        cam=cam16(t); mode='16'
        fr=crop_arr(big16(t),cam)
    elif t<MORPH[1]:
        cam=cam16(t); mode='morph'
        fr=morph_frame(t)
    else:
        cam=camiso(t); mode='iso'
        ppl,nm=iso_people(t,cam)
        fr=iso.render_view(t,cam,ppl,extra_iso(t),pop_iso(t))
        names=nm
    if 16.3<=t<16.6: fr=flash(fr,(1-(t-16.3)/0.3)*0.5)
    if MORPH[1]-0.05<=t<MORPH[1]+0.35: fr=flash(fr,clamp(1-(t-MORPH[1]+0.05)/0.4)*0.85)
    fr=fr.convert('RGBA')
    if names:
        nl=names_layer(t,cam,names)
        if nl is not None: fr.alpha_composite(nl)
    ui=draw_ui(t,cam,mode).resize((OUTW,OUTH),Image.NEAREST)
    fr.alpha_composite(ui)
    return fr.convert('RGB')

if __name__=='__main__':
    out=sys.argv[1]
    for t in map(float,sys.argv[2:]):
        render_frame(t).save(f'{out}/frame_{t:05.1f}.png')
