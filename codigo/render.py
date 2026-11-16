import numpy as np, math, random, sys, json, os
from PIL import Image, ImageDraw, ImageFilter
from world import *
from scene import *
from font import draw_text, text_width
from world16 import S
import vila16 as V
import iso

# =====================================================================
#  EP. 7 — PINDAMONHANGABA + EVOLUÇÃO 32 BITS (iso.K = 2 a partir de EVOL_T)
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

# ---------- moradores: 1x (16 bits) e 2x (32 bits: EPX + sombreado) ----------
def _epx(a):
    h,w,_=a.shape
    P_=np.pad(a,((1,1),(1,1),(0,0)),mode='edge')
    A_=P_[:-2,1:-1];B_=P_[1:-1,2:];C_=P_[1:-1,:-2];D_=P_[2:,1:-1]
    eq=lambda x,y:np.all(x==y,axis=2)
    o=np.repeat(np.repeat(a,2,0),2,1)
    c=~eq(A_,D_)&~eq(B_,C_)
    m1=c&eq(C_,A_);m2=c&eq(A_,B_);m3=c&eq(D_,C_);m4=c&eq(B_,D_)
    o[0::2,0::2][m1]=C_[m1];o[0::2,1::2][m2]=B_[m2];o[1::2,0::2][m3]=C_[m3];o[1::2,1::2][m4]=D_[m4]
    return o
_N2={}
def npc_k(pid,dr,fr,k,uniform=None,carry=None):
    s=V.NPC(pid,dr,fr,uniform,carry=carry) if carry else V.NPC(pid,dr,fr,uniform)
    if k==1: return s
    key=(pid,dr,fr,uniform,carry)
    if key not in _N2:
        from char32 import npc32
        _N2[key]=npc32(V.look_of(pid),dr,fr,uniform,carry=carry)
    return _N2[key]
    if key not in _N2:
        a=np.array(s.convert('RGBA'))
        o=_epx(a).astype(np.float32)
        al=o[:,:,3]>0
        # luz de cima/esquerda: borda direita/baixo mais escura, esquerda/cima com brilho
        r_=np.zeros_like(al); r_[:,:-1]=al[:,:-1]&~al[:,1:]
        b_=np.zeros_like(al); b_[:-1,:]=al[:-1,:]&~al[1:,:]
        l_=np.zeros_like(al); l_[:,1:]=al[:,1:]&~al[:,:-1]
        t_=np.zeros_like(al); t_[1:,:]=al[1:,:]&~al[:-1,:]
        lum=o[:,:,:3].mean(axis=2)
        thin=(r_|b_|l_|t_)&(lum<70)
        o[thin,3]=0                                   # contorno com metade da grossura
        al=o[:,:,3]>0
        r_=np.zeros_like(al); r_[:,:-1]=al[:,:-1]&~al[:,1:]
        b_=np.zeros_like(al); b_[:-1,:]=al[:-1,:]&~al[1:,:]
        l_=np.zeros_like(al); l_[:,1:]=al[:,1:]&~al[:,:-1]
        t_=np.zeros_like(al); t_[1:,:]=al[1:,:]&~al[:-1,:]
        o[r_|b_,:3]*=0.72; o[l_|t_,:3]=o[l_|t_,:3]*0.8+255*0.2
        # contorno escuro fino (1 px em 2x)
        out_=np.zeros_like(al)
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            out_|=np.roll(np.roll(al,dy,0),dx,1)
        out_&=~al
        o[out_]=[34,28,40,255]
        yy=np.arange(o.shape[0])[:,None]/o.shape[0]
        o[:,:,:3]*=(1.06-0.12*yy)[:,:,None]
        _N2[key]=Image.fromarray(np.clip(o,0,255).astype(np.uint8),'RGBA')
    return _N2[key]
def sf(pid,dr,fr,uniform=None,carry=None,hop=0):
    def f(k):
        s=npc_k(pid,dr,fr,k,uniform,carry)
        if hop<=0: return s
        im=Image.new('RGBA',(s.width,s.height+int(hop*k)),(0,0,0,0)); im.paste(s,(0,0)); return im
    return f

# ---------- câmera ----------
def CI(x,y,z): px,py=iso.PW(x,y); return (px,py,z)
_vr=[(i,l) for i,l in enumerate(house_lots[:NH]) if l[1]==ROADC and house_var[i]%3==2 and 40<l[0]<120]
_VARAL=lot(*_vr[0][1]) if _vr else (60,126)
CAMS=[(0.0,CI(146,446,7.0)),(7.2,CI(146,446,8.0)),(9.0,CI(135,365,0.78)),(11.2,CI(135,330,0.8)),(14.6,CI(135,400,0.8)),
      (15.9,CI(130,452,5.0)),(18.1,CI(130,452,5.4)),(18.8,CI(130,450,7.5)),(25.4,CI(128,448,7.5)),(29.0,CI(128,448,4.0)),
      (30.4,CI(128,448,4.0)),(32.6,CI(135,365,0.62)),(34.6,CI(135,365,0.62)),(35.5,CI(135,330,0.95)),(36.5,CI(120,300,1.05)),
      (37.6,CI(60,170,3.4)),(42.6,CI(_VARAL[0]+18,_VARAL[1]+12,3.8)),
      (42.7,CI(132,248,1.0)),(51.3,CI(132,248,1.0)),
      (51.9,CI(100,525,3.0)),(59.2,CI(112,525,3.0))]
SITE_CAM={'virou':(CI(132,248,1.8),CI(132,248,2.3)),'chat':(CI(132,250,2.5),CI(132,250,2.6)),'online':(CI(132,252,2.9),CI(140,252,3.0)),
          'casa':(CI(160,415,3.0),CI(160,415,3.0)),'geladeira':(CI(160,415,3.0),CI(160,415,3.0)),
          'mercadinho':(CI(172,234,3.4),CI(172,234,3.6)),'banco':(CI(111,262,4.2),CI(111,262,4.4)),
          'fonte':(CI(132,245,4.2),CI(132,245,4.6)),'mudanca':(CI(70,428,3.0),CI(90,428,3.0))}
CAMS2=[(73.0,CI(160,414,3.0)),(79.1,CI(160,414,3.2)),(79.6,CI(150,500,2.2)),(84.6,CI(150,520,2.2)),
       (85.2,CI(178,606,2.7)),(90.6,CI(178,606,2.7)),(91.3,CI(135,250,0.9)),(97.4,CI(135,520,0.9)),
       (98.0,CI(128,448,5.4)),(102.6,CI(128,448,5.8)),(104.6,CI(135,365,0.8)),(110,CI(135,365,0.8))]
def _interp_cam(t,L):
    for (a,va),(b,vb) in zip(L,L[1:]):
        if a<=t<b:
            f=smooth((t-a)/(b-a)); return tuple(va[i]+(vb[i]-va[i])*f for i in range(3))
    return L[-1][1] if t>=L[-1][0] else L[0][1]
def camiso(t):
    if t<59.3: c=_interp_cam(t,CAMS)
    elif t<73.0:
        for a,b,nm in SITE_CUTS:
            if a<=t<b:
                c0,c1=SITE_CAM[nm]; f=smooth((t-a)/(b-a)); c=tuple(c0[i]+(c1[i]-c0[i])*f for i in range(3)); break
    else: c=_interp_cam(t,CAMS2)
    if T['tambor'][0]<=t<T['nome'][0]+0.3:          # tremida do tambor
        k=clamp((t-T['tambor'][0])/1.6)*3
        c=(c[0]+math.sin(t*70)*k,c[1]+math.cos(t*63)*k,c[2])
    return c
def w2si(x,y,cam,z_=0):
    cx,cy,zz=cam; px,py=iso.PW(x,y,z_)
    return ((px-(cx-540/zz))*zz/4,(py-(cy-960/zz))*zz/4)
def site_cut(t):
    for a,b,nm in SITE_CUTS:
        if a<=t<b: return nm,a,b
    return None,0,0

# ---------- moradores ----------
_cr=random.Random(707)
_regids=sorted(i for i in REG if i<=C1)
MUTIRAO=[]                                       # plateia do mutirão (inclui gente do site)
for j in range(34):
    pid=_regids[j*len(_regids)//34] if j%2==0 else _cr.randint(1,C1)
    while True:
        x=_cr.uniform(98,174); y=_cr.uniform(460,484)
        if x<116 or x>158: break
    MUTIRAO.append(dict(id=pid,x=x,y=y,sx=131.5+_cr.uniform(-2,2),sy=_cr.uniform(380,440),arr=18.2+_cr.uniform(0,1.6),ph=_cr.uniform(0,6)))
def mutirao_people(t):
    out=[]
    if not (18.1<=t<29.2): return out
    for c in MUTIRAO:
        if t<c['arr']:
            f=clamp((t-18.1)/(c['arr']-18.1)); x=c['sx']+(c['x']-c['sx'])*f; y=c['sy']+(c['y']-c['sy'])*f
            out.append((x,y,sf(c['id'],'down',int(t*8+c['ph'])%4))); continue
        hop=0
        if 16.5<=t<18.1 or t>=25.1: hop=abs(math.sin((t*2.4+c['ph'])*math.pi))*3.5
        out.append((c['x'],c['y'],sf(c['id'],'up' if t<25.1 else 'down',(int(t*5+c['ph'])%2)*2 if hop>0.5 else 0,hop=hop)))
    # serradores, pintores, puxadores de corda
    if 19.6<=t<21.3:
        for k,(x,y) in enumerate(((152,470),(155,478))):
            out.append((x,y,sf(8000+k,'left',0,'pedreiro','up' if int(t*8+k)%2 else 'down')))
    if 21.0<=t<22.9:
        for k in range(3):
            u=PLACA_X0+3+k*7+((t-21.2)*10)%4
            out.append((u,PLACA_Y+2.2,sf(8010+k,'up',int(t*6+k)%2*2,'pedreiro')))
    if 22.7<=t<25.4:
        f=smooth(clamp((t-22.9)/2.1))
        for k in range(4):
            out.append((PLACA_X0+3+k*5.5,PLACA_Y+12+f*6,sf(8020+k,'up',int(t*6+k)%4,'pedreiro')))
    return out
def mutirao_extra(t):
    ex=[]
    if 19.4<=t<21.6:          # cavaletes com tábua + serragem
        def cav(vd,vx0,vy0,k):
            for (bx,by) in ((148,471),(151,479)):
                X,Y=iso.PW(bx,by); X=X*k-vx0; Y=Y*k-vy0
                vd.line([X-6*k,Y,X-4*k,Y-6*k],fill=(110,74,44)); vd.line([X+6*k,Y,X+4*k,Y-6*k],fill=(110,74,44))
                vd.rectangle([X-9*k,Y-8*k,X+9*k,Y-6*k],fill=(190,140,86))
                if t<21.2:
                    for j in range(5):
                        q=(t*3+j*0.2)%1
                        vd.rectangle([X+(j-2)*3*k,Y-6*k+q*8*k,X+(j-2)*3*k+k,Y-6*k+q*8*k+k],fill=(236,206,150))
        ex.append((148+475,('fn',cav)))
    if 22.7<=t<25.3:          # cordas
        n,ang=placa_estado(t)
        th=ang*math.pi/2; zb=26*ang; ztop=zb+12*math.sin(th); ytop=PLACA_Y-12*math.cos(th)
        f=smooth(clamp((t-22.9)/2.1))
        def corda(vd,vx0,vy0,k,ztop=ztop,ytop=ytop,f=f):
            for kk in range(4):
                ax,ay=iso.PW(PLACA_X0+3+kk*5.5,ytop,ztop); bx,by=iso.PW(PLACA_X0+3+kk*5.5,PLACA_Y+12+f*6,9)
                vd.line([ax*k-vx0,ay*k-vy0,bx*k-vx0,by*k-vy0],fill=(214,190,130),width=k)
        ex.append((PLACA_X1+PLACA_Y+30,('fn',corda)))
    return ex

def iso_people(t,cam):
    cx,cy,z=cam; vw,vh=1080/z,1920/z
    out=[]; names=[]
    hide=18.1<=t<29.2
    for pp in people:
        st=person_state(pp,t)
        if st is None: continue
        x,y=st[0],st[1]
        px,py=iso.PW(x,y)
        if not (cx-vw/2-20<px<cx+vw/2+20 and cy-vh/2-30<py<cy+vh/2+30): continue
        if hide and 100<x<175 and 440<y<505: continue
        st0=person_state(pp,t-0.08)
        dx,dy=(x-st0[0],y-st0[1]) if st0 else (0,1)
        moving=abs(dx)+abs(dy)>0.05
        sxd,syd=(dx-dy)*2,(dx+dy)
        dr=('right' if sxd>0 else 'left') if abs(sxd)>abs(syd)*1.2 else ('down' if syd>0 else 'up')
        if not moving: dr='down'
        out.append((x,y,sf(pp['id'],dr,(int(t*8+pp['ph']*3)%4) if moving else 0)))
        if pp['id'] in REG and z>=2.4: names.append((abs(px-cx)+abs(py-cy),x,y,pp['id']))
        if len(out)>80: break
    names=[n[1:] for n in sorted(names)[:3]]
    C=count_at(t)
    for i,l in enumerate(house_lots):
        p=house_p(i,C)
        if 0<p<1:
            lx_,ly_=lot(*l)
            for j in range(2): out.append((lx_+4+j*12,ly_+22,sf(8000+(i+j)%6,'down',0,'pedreiro','up' if int(t*6+j)%2 else 'down')))
    out+=mutirao_people(t)
    if T['campo'][0]-0.4<t<T['campo'][1]+0.3:
        lx_,ly_=lot(*CAMPO[0])
        for k in range(4): out.append((lx_+30+k*8,ly_-2,sf(9100+k,'down',0)))
        gx=lx_+44+math.sin(t*3.2)*10; hop=max(0,math.sin(t*6.4))*5
        out.append((gx,ly_+30,sf(9200,'down',1 if hop>1 else 0,hop=hop)))   # goleiro
    nm,a,b=site_cut(t)
    if nm=='mercadinho':
        dx_=lot(*MERCADO)[0]+9.5; f=clamp((t-a)/(b-a))
        out.append((dx_,ROADB+3+f*6,sf(REG and _regids[3] or 5,'down',int(t*8)%4,carry='sacola')))
    if nm=='banco': out.append((111,265.2,sf(_regids[5] if len(_regids)>5 else 7,'down',0)))
    if nm=='online':
        for k in range(6): out.append((120+k*5,248+(k%2)*6+((t-a)*8)%6,sf(_regids[k*3%len(_regids)],'right',int(t*8+k)%4)))
    return out,names

def extra_iso(t):
    ex=mutirao_extra(t)
    if T['campo'][0]-0.4<t<T['campo'][1]+0.3:
        lx_,ly_=lot(*CAMPO[0]); bx,by=lx_+38,ly_+12+math.sin(t*1.7)*8
        h=abs(math.sin(t*5))*9
        def ball(vd,vx0,vy0,k,bx=bx,by=by,h=h):
            X,Y=iso.PW(bx,by,h); X=X*k-vx0; Y=Y*k-vy0
            vd.ellipse([X-2*k,Y-2*k,X+2*k,Y+2*k],fill=(255,255,255),outline=(30,30,30))
        ex.append((bx+by+0.6,('fn',ball)))
    nm,a,b=site_cut(t)
    if nm=='mudanca':
        f=clamp((t-a)/(b-a)); tx=40+f*90; ty=ROADD+5
        def truck(vd,vx0,vy0,k,tx=tx,ty=ty):
            pass
        s_=iso.sprite(lambda tx=tx,ty=ty: caminhao(tx,ty),tx-3,ty-4,tx+14,ty+4,24)
        if s_: ex.append((tx+ty+8,('spr',s_)))
    return ex
def caminhao(x,y):
    iso.shadow(x,y-2,x+12,y+2,10)
    iso.box(x+4,y-2,x+12,y+2,11,(240,240,244),(200,200,206)); iso.top(x+4,y-2,x+12,y+2,11,(226,226,232))
    iso.box(x,y-2,x+4,y+2,7,(214,60,50),(170,44,38)); iso.top(x,y-2,x+4,y+2,7,(230,80,70))
    iso.quad([iso.P(x+0.4,y+2,4),iso.P(x+3,y+2,4),iso.P(x+3,y+2,6.5),iso.P(x+0.4,y+2,6.5)],(150,206,236))
    for (wx,wy) in ((x+2,y+2),(x+6,y+2),(x+10,y+2)):
        X,Y=iso.P(wx,wy,1); iso.d.ellipse([X-1.5,Y-1.5,X+1.5,Y+1.5],fill=(30,30,34))
    for j in range(3): iso.box(x+5+j*2.3,y-1.5,x+6.8+j*2.3,y+0.5,3,(200,150,90),(170,124,72),z0=11)
    cx,cy=iso.P(x+8,y+2,7); draw_text(iso.d,"MUDANÇA",cx,cy-3,1,(214,60,50,255),outline=None) if False else None

def pop_iso(t): return None

# ---------- efeitos de tela ----------
def dark_spot(fr,t,cam):
    a=np.array(fr).astype(np.float32)
    k=1.0 if t<6.6 else clamp(1-(t-6.6)/0.9)
    if k<=0: return fr
    sx,sy=w2si(149,446,cam,12); sx*=4; sy*=4
    yy,xx=np.ogrid[0:OUTH,0:OUTW]
    r=np.sqrt((xx-sx)**2+((yy-sy)*0.8)**2)
    spot=np.clip(1-(r-170)/240,0,1)*clamp(t/1.2)
    mul=0.12+0.88*spot
    m=(1-k)+k*mul
    a*=m[:,:,None]
    a[:,:,2]*= (1-k*0.15*(1-spot))+k*0.15*(1-spot)*1.4
    return Image.fromarray(np.clip(a,0,255).astype(np.uint8))
def night_tint(fr,k):
    a=np.array(fr).astype(np.float32)*(1-(1-np.array([0.45,0.5,0.75]))*k)
    return Image.fromarray(np.clip(a,0,255).astype(np.uint8))
def grade32(fr,t):
    """luz '32 bits': quente, contraste e vinheta"""
    a=np.array(fr).astype(np.float32)
    a*=np.array([1.05,1.0,0.92]); lum=a.mean(axis=2,keepdims=True); a=lum+(a-lum)*1.12
    a=128+(a-128)*1.05
    if not hasattr(grade32,'v'):
        yy,xx=np.mgrid[0:OUTH,0:OUTW]; v=np.hypot((xx-OUTW/2)/(OUTW/2),(yy-OUTH/2)/(OUTH/2))
        grade32.v=(1-0.3*np.clip(v-0.6,0,1))[:,:,None]
        warm=np.clip(1-np.hypot(xx/OUTW-0.15,yy/OUTH-0.0)/1.2,0,1)
        grade32.w=warm[:,:,None]*np.array([24,14,0])
    a=a*grade32.v+grade32.w
    return Image.fromarray(np.clip(a,0,255).astype(np.uint8))
def pixelate(fr,b):
    if b<=1: return fr
    w,h=fr.size; return fr.resize((max(1,w//b),max(1,h//b)),Image.BILINEAR).resize((w,h),Image.NEAREST)
_CL=[(random.Random(k).uniform(-100,1180),random.Random(k+99).uniform(0,1),random.Random(k+7).uniform(90,260)) for k in range(70)]
def clouds(fr,t):
    if not (30.6<=t<34.8): return fr
    if t<32.6: cover=smooth(clamp((t-30.6)/2.0)); drift=(t-30.6)*900
    else: cover=1-smooth(clamp((t-32.6)/2.2)); drift=(t-32.6)*-700
    im=fr.convert('RGBA'); lay=Image.new('RGBA',im.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
    for (x,yf,r) in _CL:
        y=(yf*2600+drift)%2600-340
        rr=r*(0.4+cover*1.4)
        if t>=32.6: x=540+(x-540)*(1+(t-32.6)*0.8)
        d.ellipse([x-rr,y-rr*0.6,x+rr,y+rr*0.6],fill=(255,255,255,int(150+100*cover)))
        d.ellipse([x-rr*0.6,y-rr*0.9,x+rr*0.5,y+rr*0.2],fill=(255,255,255,int(150+100*cover)))
    lay=lay.filter(ImageFilter.GaussianBlur(6))
    im.alpha_composite(lay)
    if cover>0.85:
        wv=(cover-0.85)/0.15
        im=Image.blend(im,Image.new('RGBA',im.size,(250,252,255,255)),wv)
    return im.convert('RGB')
def fireworks(d,t):
    if not (25.3<=t<29.6): return
    rr=random.Random(3)
    for k in range(9):
        t0=25.4+k*0.42; age=t-t0
        if age<0 or age>1.4: continue
        cx=rr.uniform(40,230); cy=rr.uniform(90,230); col=[(255,90,90),(255,214,70),(120,230,110),(120,180,255),(240,120,240)][k%5]
        if age<0.3:
            y=cy+60*(1-age/0.3); d.rectangle([cx,y,cx+1,y+3],fill=(255,240,200,255)); continue
        a=age-0.3; R=a*55; fade=int(255*clamp(1-a/1.1))
        for j in range(16):
            ang=j/16*2*math.pi
            x=cx+math.cos(ang)*R; y=cy+math.sin(ang)*R+a*a*20
            d.rectangle([x,y,x+1,y+1],fill=col+(fade,))
            d.point((cx+math.cos(ang)*R*0.6,cy+math.sin(ang)*R*0.6+a*a*12),fill=(255,255,255,fade))

# ---------- telas especiais ----------
_PROV_BG=None
def provador(t):
    global _PROV_BG
    if _PROV_BG is None:
        old=iso.K; iso.K=2
        bg=iso.render_view(45.0,CI(132,248,1.0),[])
        iso.K=old
        _PROV_BG=bg.filter(ImageFilter.GaussianBlur(10))
        _PROV_BG=Image.fromarray((np.array(_PROV_BG)*0.55).astype(np.uint8))
    fr=_PROV_BG.copy(); d=ImageDraw.Draw(fr,'RGBA')
    # palco/pedestal com luz
    d.ellipse([340,1380,740,1500],fill=(255,240,200,60)); d.ellipse([380,1400,700,1480],fill=(60,50,90,255),outline=(255,214,70,255),width=4)
    for k in range(5): d.polygon([(540,300),(400-k*30,1440),(680+k*30,1440)],fill=(255,240,200,8))
    a,b=T['provador']
    if t<45.6:   # antes / agora
        s1=npc_k(_regids[0],'down',0,1).resize((12*24,18*24),Image.NEAREST)
        s2=npc_k(_regids[0],'down',0,2).resize((32*9,48*9),Image.NEAREST)
        fr.paste(s1,(270-s1.width//2,1440-s1.height),s1); fr.paste(s2,(810-s2.width//2,1440-s2.height),s2)
    else:
        seq=_regids[:]+list(range(1,C1,37))
        idx=int((t-45.6)/0.42)%len(seq)
        pid=seq[idx]; dr=['down','right','down','left'][int((t-45.6)/0.42)%4]
        s2=npc_k(pid,dr,int(t*6)%4 if dr!='down' else 0,2).resize((32*15,48*15),Image.NEAREST)
        fr.paste(s2,(540-s2.width//2,1440-s2.height),s2)
    return fr
_INT={}
def interior_frame(t,nm,a,b):
    fo=clamp((t-a-0.3)/0.4) if nm=='geladeira' else 0.0
    key=round(fo,2)
    if key not in _INT:
        old=iso.K; iso.K=2
        s_=iso.sprite(lambda: iso.interior(key),0,0,30,22,40)
        iso.K=old
        _INT[key]=s_[0]
    im=_INT[key]
    base=Image.new('RGB',(OUTW,OUTH),(30,26,44))
    if nm=='casa':
        z=4.4+0.6*clamp((t-a)/(b-a)); cx,cy=im.width/2,im.height/2
    else:
        z=8.0; cx,cy=im.width*0.80,im.height*0.30
    s=im.resize((int(im.width*z),int(im.height*z)),Image.NEAREST)
    base.paste(s,(int(540-cx*z),int(980-cy*z)),s)
    return base

def coins(d,t,t0,t1):
    if not (t0<=t<t1): return
    rr=random.Random(11)
    for k in range(26):
        x=rr.uniform(10,260); sp=rr.uniform(90,180); ph=rr.uniform(0,3)
        y=((t-t0)*sp+ph*120)%560-40
        w=abs(math.sin(t*6+k))*4+1
        d.ellipse([x-w,y-5,x+w,y+5],fill=(255,214,70,255),outline=(170,120,20,255))
def icon_brief(d,x,y): d.rectangle([x,y+3,x+14,y+12],fill=(120,80,40,255)); d.rectangle([x+4,y,x+10,y+3],outline=(120,80,40,255))
def icon_helmet(d,x,y): d.pieslice([x,y,x+14,y+14],180,360,fill=(250,200,40,255)); d.rectangle([x-1,y+7,x+15,y+8],fill=(250,200,40,255))
def icon_apron(d,x,y): d.polygon([(x+3,y),(x+11,y),(x+14,y+14),(x,y+14)],fill=(250,250,250,255)); d.rectangle([x+5,y+6,x+9,y+9],outline=(200,60,60,255))

def chat(d,t,a):
    msgs=[("OI GENTE!",WHITE),("BORA PRA PRAÇA",YEL),("ALGUÉM NO MERCADINHO?",LBLUE),("KKKKKKK",GREEN),("QUE CIDADE LINDA",WHITE),("PINDA!!!",YEL)]
    box(d,20,300,250,440,(10,10,24,200))
    d.rectangle([28,306,60,316],fill=(220,40,40,255)); draw_text(d,"AO VIVO",44,308,1,WHITE)
    n=int((t-a)/0.17)+1
    for k,(m,c) in enumerate(msgs[:n][-6:]):
        draw_text(d,m,135,326+k*18,1,c)

def draw_ui(t,cam,mode):
    ui=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ui)
    C=count_at(t); hs=nhouses(C)
    if t>=7.35 and mode not in ('prov','int'):
        y0=36
        box(d,32,y0,238,y0+42)
        draw_text(d,"SEGUIDORES",86,y0+7,1,LBLUE); draw_text(d,"CASAS",192,y0+7,1,LBLUE)
        d.line([150,y0+6,150,y0+36],fill=(120,120,180,255))
        draw_text(d,str(C),86,y0+20,2,YEL if C!=count_at(t-0.12) else WHITE)
        draw_text(d,str(hs),192,y0+20,2,YEL if hs!=nhouses(count_at(t-0.4)) else WHITE)
    if 5.5<=t<7.3:
        v=pop(t,5.5,7.3); draw_text(d,"HOJE ELA GANHA UM NOME",135,380,1,(255,255,255,int(255*v)))
    a,b=T['titulo']
    if pop(t,a,b)>0:
        draw_text(d,"A CIDADE DOS",135,130,2,WHITE); draw_text(d,"SEGUIDORES",135,152,3,YEL)
        draw_text(d,"EPISÓDIO 7",135,186,1,LBLUE)
    # votação nos comentários
    a,b=T['votos']
    if a<=t<T['nome'][1]:
        opts=[("SEGUIDÓPOLIS",0.55),("PIXELÂNDIA",0.62),("VILA NOVA",0.4),("PINDAMONHANGABA",1.0)]
        for k,(nm_,mx) in enumerate(opts):
            v=pop(t,a+0.25*k,T['nome'][0]+0.2)
            if v<=0: continue
            y=110+k*30
            box(d,24,y,246,y+24,(24,22,52,220))
            draw_text(d,nm_,90,y+5,1,WHITE if k<3 else YEL)
            g=clamp((t-a-0.25*k)/2.6)*mx
            d.rectangle([150,y+8,150+int(80*g),y+15],fill=(230,60,90,255) if k==3 else (150,120,180,255))
            d.polygon([(140,y+9),(143,y+7),(146,y+9),(143,y+14)],fill=(255,90,110,255))
        if T['tambor'][0]<=t<T['nome'][0]:
            draw_text(d,"...",135,300+int(math.sin(t*30)*3),4,WHITE)
    if T['nome'][0]<=t<T['mutirao'][0]+1.2:
        nome=NOME_CIDADE; n=int(clamp((t-T['nome'][0])/0.6)*len(nome))
        sc=2
        box(d,8,250,262,300,(200,40,50,240))
        draw_text(d,nome[:n],135,266,sc,YEL)
        for k in range(30):
            q=((t-16.5)*0.9+k*0.07)%1.0; cx_=(k*37)%270; cy_=int(q*480)
            d.rectangle([cx_,cy_,cx_+2,cy_+3],fill=[(255,214,70),(120,230,110),(230,60,60),(180,200,255)][k%4]+(255,))
    a,b=T['mutirao']
    for k,(w_,t0,t1) in enumerate((("SERRARAM A MADEIRA",19.8,21.1),("PINTARAM LETRA POR LETRA",21.2,22.8),("E LEVANTARAM NA CORDA!",22.9,25.3))):
        chip(d,w_,135,120,t,t0,t1,[YEL,GREEN,WHITE][k])
    a,b=T['fogos']
    fireworks(d,t)
    if a<=t<b:
        v=pop(t,a,b)
        box(d,10,330,260,392,(40,120,70,240)); draw_text(d,"OFICIALMENTE UMA CIDADE!",135,340,1,WHITE); draw_text(d,NOME_CIDADE,135,358,2,YEL)
    banner(d,["UM VISUAL","À ALTURA..."],140,t,29.2,30.9,[WHITE,YEL],2)
    a,b=T['bits32']
    if 33.6<=t<35.4:
        box(d,22,118,248,186,(40,120,70,240))
        draw_text(d,"NOVA EVOLUÇÃO:",135,128,1,WHITE); draw_text(d,"32 BITS!",135,146,4,YEL)
    for k,(w_,t0) in enumerate((("MAIS LUZ",35.5),("SOMBRA",36.5),("DETALHE EM CADA CASA",37.5))):
        chip(d,w_,135,330+k*20,t,t0,38.6,[YEL,LBLUE,GREEN][k])
    for k,(w_,t0) in enumerate((("TELHADO",38.8),("VARANDA",39.7),("JARDIM",40.5),("ROUPA NO VARAL",41.4))):
        chip(d,w_,135,330+k*20,t,t0,b,[YEL,GREEN,GREEN,LBLUE][k])
    a,b=T['provador']
    if mode=='prov':
        banner(d,["MORADORES","32 BITS"],60,t,a+0.2,b,[WHITE,YEL],3)
        if t<45.6:
            draw_text(d,"ANTES",68,230,2,LBLUE); draw_text(d,"AGORA",202,230,2,YEL)
        for k,(w_,t0) in enumerate((("+ ROUPA",45.7),("+ CABELO",47.1),("+ CHAPÉU",48.1),("+ ACESSÓRIO",48.5))):
            chip(d,w_,[50,220,50,220][k],[400,400,425,425][k],t,t0,b,[YEL,GREEN,LBLUE,YEL][k])
        banner(d,["MONTA O TEU","DO TEU JEITO!"],380,t,50.0,b,[WHITE,GREEN],2)
    a,b=T['casas']
    banner(d,["A RUA E NÃO PAROU"],120,t,52.2,b,[GREEN],2)
    if mode=='iso32' and a<=t<b:
        for n,t0 in ((62,53.6),(63,55.1),(64,56.1),(65,57.3)):
            x,y=lot(*house_lots[n-1]); sx,sy=w2si(x+10,y+12,cam,22)
            tag_s(d,f"CASA {n}"+(": EM OBRA" if n==65 else ""),sx,sy,t,t0,b,GREEN if n<65 else YEL)
        banner(d,["COMEÇA EM 645","PRONTA EM 650"],360,t,57.3,b,[WHITE,GREEN])
    nm,ca,cb=site_cut(t)
    if nm:
        lbl={'virou':"O SITE VIROU OUTRA COISA!",'chat':"CHAT AO VIVO",'online':"TODO MUNDO JUNTO, AO VIVO",'casa':"DÁ PRA ENTRAR NAS CASAS",
             'geladeira':"LANCHE NA GELADEIRA",'mercadinho':"COMPRAS NO MERCADINHO",'banco':"SENTAR NA PRAÇA",'fonte':"MOEDA NA FONTE",'mudanca':"E ATÉ MUDAR DE CASA!"}[nm]
        box(d,14,104,256,128,(200,40,50,235)); draw_text(d,lbl,135,111,1,WHITE)
        if nm=='chat': chat(d,t,ca)
        if nm=='online':
            for k in range(6):
                sx,sy=w2si(120+k*5,248+(k%2)*6+((t-ca)*8)%6,cam,22); d.ellipse([sx-3,sy-3,sx+3,sy+3],fill=(60,230,90,255),outline=(255,255,255,255))
        if nm in ('geladeira','mercadinho'):
            f=clamp((t-ca-0.4)/0.7)
            box(d,60,400,210,420); draw_text(d,"VIDA",80,406,1,WHITE)
            d.rectangle([100,405,100+int(100*(0.35+0.65*f)),414],fill=(80,220,90,255)); d.rectangle([100,405,200,414],outline=(255,255,255,255))
            if f>0: draw_text(d,"+VIDA!",135,380-int(f*10),2,GREEN)
        if nm=='banco': draw_text(d,"Z Z Z",150,250-int(((t-ca)*8)%10),1,WHITE) if False else None
        if nm=='fonte':
            f=clamp((t-ca)/0.7); sx0,sy0=w2si(124,256,cam,14); sx1,sy1=w2si(132,245,cam,8)
            if f<1:
                x=sx0+(sx1-sx0)*f; y=sy0+(sy1-sy0)*f-math.sin(f*math.pi)*40
                d.ellipse([x-3,y-3,x+3,y+3],fill=(255,214,70,255),outline=(170,120,20,255))
            else:
                v=pop(t,ca+0.7,cb)
                box(d,40,300,230,340,(40,120,70,240)); draw_text(d,"SORTE DO DIA!",135,306,2,YEL)
                for k in range(12):
                    ang=k/12*6.28+t*2; r=30+((t-ca)*30)%20
                    d.point((sx1+math.cos(ang)*r,sy1+math.sin(ang)*r*0.6),fill=(255,240,140,255))
    a,b=T['prefeito']
    if a<=t<b:
        box(d,14,104,256,128,(40,90,190,240)); draw_text(d,"CANDIDATURAS ABERTAS!",135,111,1,WHITE)
        if t>=74.4: banner(d,["PREFEITO DE",NOME_CIDADE],300,t,74.4,b,[WHITE,YEL],2)
        if t>=77.6:
            banner(d,["QUEM VAI SER","O PRIMEIRO?"],370,t,77.6,b,[WHITE,YEL],2)
    a,b=T['economia']
    coins(d,t,a+1.2,b)
    banner(d,["EM BREVE:"],110,t,79.3,b,[LBLUE],1)
    v=pop(t,80.4,b)
    if v>0:
        box(d,30,140,240,170); icon_brief(d,42,148); icon_helmet(d,62,146); icon_apron(d,84,146); draw_text(d,"PROFISSÕES",170,150,1,YEL)
    v=pop(t,81.4,b)
    if v>0:
        box(d,30,176,240,206); d.ellipse([44,182,58,196],fill=(255,214,70,255),outline=(170,120,20,255)); draw_text(d,"$",51,186,1,(150,100,20,255)); draw_text(d,"DINHEIRO",160,186,1,GREEN)
    banner(d,["ECONOMIA","DE VERDADE!"],330,t,82.2,b,[WHITE,YEL],2)
    a,b=T['campo']
    banner(d,["JÁ TEM GOLEIRO..."],110,t,85.0,87.1,[WHITE],2)
    banner(d,["SÓ FALTA O CAMPO"],110,t,87.1,b,[YEL],2)
    banner(d,["FALTAM 53"],360,t,88.1,b,[WHITE],3)
    banner(d,["PRO 700!"],400,t,88.6,b,[GREEN],2)
    a,b=T['resumo']
    banner(d,["RESULTADO:"],84,t,90.9,b,[LBLUE],1)
    banner(d,[f"{C1} MORADORES"],110,t,91.6,b,[YEL])
    banner(d,[f"{NH} CASAS"],146,t,93.7,b,[WHITE])
    banner(d,[NOME_CIDADE],330,t,95.2,b,[YEL],1)
    banner(d,["VISUAL 32 BITS"],356,t,96.1,b,[GREEN])
    a,b=T['cta']
    v=pop(t,a,b,0.01)
    if v>0:
        yy=110+int((1-v)*14)
        box(d,24,yy,246,yy+62,(200,40,50,240))
        draw_text(d,"LINK NA BIO!",135,yy+10,2,WHITE); draw_text(d,"CRIA O TEU MORADOR",135,yy+38,1,YEL)
        if t>=100.0: banner(d,["E SE CANDIDATA!"],330,t,100.0,b,[GREEN],2)
        if t>=101.2: banner(d,[NOME_CIDADE,"TE ESPERA!"],370,t,101.2,b,[YEL,WHITE],2)
    return ui

def names_layer(t,cam,names):
    if not names: return None
    lay=Image.new('RGBA',(W*2,H*2),(0,0,0,0)); d=ImageDraw.Draw(lay)
    for (x,y,pid) in names:
        sx,sy=w2si(x,y,cam,40 if iso.K==2 else 20)
        nm=nome_tela(REG[pid]['nome'])
        if not nm: continue
        X=int(sx*2); Y=int(sy*2)-8
        tw=text_width(nm,1)+6
        d.rectangle([X-tw//2,Y-2,X+tw//2,Y+8],fill=(24,22,52,200)); draw_text(d,nm,X,Y,1,YEL)
    return lay.resize((OUTW,OUTH),Image.NEAREST)

_TXT={}
def placa_texto(fr,t,cam):
    est=placa_estado(t)
    if est is None: return fr
    n,ang=est
    if n<=0: return fr
    th=ang*math.pi/2; zb=26*ang; ztop=zb+12*math.sin(th); ytop=PLACA_Y-12*math.cos(th)
    cx,cy,Z=cam
    def O(x,y,z): px,py=iso.PW(x,y,z); return ((px-(cx-540/Z))*Z,(py-(cy-960/Z))*Z)
    m=0.06; h_=0.18
    xa,xb=PLACA_X0+(PLACA_X1-PLACA_X0)*m,PLACA_X1-(PLACA_X1-PLACA_X0)*m
    fy=lambda f: (ytop+(PLACA_Y-ytop)*f, ztop+(zb-ztop)*f)
    (y0,z0),(y1,z1)=fy(h_),fy(1-h_)
    q=[O(xa,y0,z0),O(xb,y0,z0),O(xb,y1,z1),O(xa,y1,z1)]
    if n not in _TXT:
        nome=NOME_CIDADE; vis=nome[:n]
        tw=text_width(nome,4)+8
        im=Image.new('RGBA',(tw,44),(0,0,0,0)); dd=ImageDraw.Draw(im)
        draw_text(dd,vis+' '*(len(nome)-n),tw//2,6,4,(255,236,140,255),outline=(70,40,20,255))
        _TXT[n]=im
    tex=_TXT[n]; w,h=tex.size
    A=[];B=[]
    for (X,Y),(u,v) in zip(q,[(0,0),(w,0),(w,h),(0,h)]):
        A.append([X,Y,1,0,0,0,-u*X,-u*Y]); B.append(u); A.append([0,0,0,X,Y,1,-v*X,-v*Y]); B.append(v)
    try: co=np.linalg.solve(np.array(A,float),np.array(B,float))
    except np.linalg.LinAlgError: return fr
    lay=tex.transform((OUTW,OUTH),Image.PERSPECTIVE,tuple(co),Image.BILINEAR)
    f2=fr.convert('RGBA'); f2.alpha_composite(lay); return f2.convert('RGB')

def flash(fr,k):
    a=np.array(fr).astype(np.float32); a=a+(255-a)*k
    return Image.fromarray(a.astype(np.uint8))

def render_frame(t):
    iso.K=1 if t<EVOL_T else 2
    cam=camiso(t); names=None
    nm,ca,cb=site_cut(t)
    if T['provador'][0]<=t<T['provador'][1]:
        mode='prov'; fr=provador(t)
    elif nm in ('casa','geladeira'):
        mode='int'; fr=interior_frame(t,nm,ca,cb)
    else:
        mode='iso32' if iso.K==2 else 'iso'
        ppl,names=iso_people(t,cam)
        fr=iso.render_view(t,cam,ppl,extra_iso(t),pop_iso(t))
        fr=placa_texto(fr,t,cam)
    if t<7.6: fr=dark_spot(fr,t,cam)
    if 25.3<=t<29.6: fr=night_tint(fr,0.55*min(clamp((t-25.3)/0.4),clamp((29.6-t)/0.6)))
    if iso.K==2 and mode!='prov': fr=grade32(fr,t)
    if 30.4<=t<32.7: fr=pixelate(fr,int(1+smooth(clamp((t-30.4)/2.0))*30))
    fr=clouds(fr,t)
    for t0,dur,k in ((16.5,0.35,0.8),(EVOL_T+1.2,0.3,0.3)):
        if t0<=t<t0+dur: fr=flash(fr,(1-(t-t0)/dur)*k)
    for a,b,_ in SITE_CUTS[1:]:
        if a<=t<a+0.12: fr=flash(fr,(1-(t-a)/0.12)*0.5)
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
