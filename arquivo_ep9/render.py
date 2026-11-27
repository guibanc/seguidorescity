import numpy as np, math, random, sys, json, os
from PIL import Image, ImageDraw, ImageFilter
from world import *
from scene import *
from font import draw_text, text_width
import vila16 as V
import iso, vox

# =====================================================================
#  EP. 9 — FOGO NO MERCADINHO, CORPO DE BOMBEIROS, PETSHOP, CAMPEONATO, VOTAÇÃO ABERTA (32 bits)
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
      'bombeiro':dict(camisa=0,camisa2=2,estampa='listrada',baixo='calca',cor_baixo=2,chapeu='capacete',cor_chapeu=0),
      'azul':dict(camisa=1,camisa2=4,estampa='time',baixo='bermuda',cor_baixo=2,chapeu=None),
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

_BG={}
def blur_bg(key,t,cam,dim=0.55):
    if key not in _BG:
        old=iso.VOX; iso.VOX=False; iso.K=2
        bg=iso.render_view(t,cam,[]).filter(ImageFilter.GaussianBlur(10))
        _BG[key]=Image.fromarray((np.array(bg)*dim).astype(np.uint8)); iso.VOX=old
    return _BG[key].copy()
_HEADS={}
def head_img(pid):
    if pid not in _HEADS:
        s=npc_k(pid,'down',0,2); s=s.crop(s.getbbox()); _HEADS[pid]=s.crop((0,0,s.width,int(s.height*0.5)))
    return _HEADS[pid]
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

# =====================================================================
#  EP. 9 — cenas
# =====================================================================
K_=KW
def CI(x,y,z): px,py=iso.PW(x,y); return (px,py,z)
MX,MY=lot(*MERCADO); MX0,MX1,MY0,MY1=MX+1,MX+20,MY+5,MY+20          # mercadinho do centro
BX,BY=lot(*BOMBEIROS); PX_,PY_=lot(*PETSHOP); QX,QY=lot(*PADARIA)
FX0,FY0,FX1,FY1=vox.campo_rect(); FXM,FYM=(FX0+FX1)/2,(FY0+FY1)/2
RB=ROADB+5                                                          # meio da rua B (frente do mercadinho)
TRUCK_PARK=(MX+10,RB)

# ---------- caminho do caminhão: garagem -> rua F -> avenida -> rua B -> mercadinho ----------
_route=[(BX+10,BY+24),(BX+10,ROADF+5),(131.5,ROADF+5),(131.5,RB),(TRUCK_PARK[0],RB)]
_seg=[math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(_route,_route[1:])]; _tot=sum(_seg)
TR0,TR1=K_['caminhao']-0.2,K_['banho']-0.3
def truck_at(t):
    if t<TR0: return (_route[0][0],_route[0][1],'y',False)
    f=smooth(clamp((t-TR0)/(TR1-TR0)))*_tot
    for (a,b),L_ in zip(zip(_route,_route[1:]),_seg):
        if f<=L_:
            u=f/L_ if L_ else 0; x=a[0]+(b[0]-a[0])*u; y=a[1]+(b[1]-a[1])*u
            return (x,y,'x' if abs(b[0]-a[0])>abs(b[1]-a[1]) else 'y',True)
        f-=L_
    return (_route[-1][0],_route[-1][1],'x',True)
def truck_extra(t):
    if not (K_['fundado']+1.4<=t<T['bombeiros'][1]): return []
    x,y,ax,mov=truck_at(t)
    def fn(vd,vx0,vy0,k,x=x,y=y,ax=ax):
        X,Y=iso.PW(x,y); iso.caminhao(vd,X*k-vx0,Y*k-vy0,k,ax,t,True)
    return [(x+y+3,('fn',fn))]

# ---------- fogo, fumaça e água ----------
def fire_extra(t):
    out=[]
    st=merc_estado(t)
    sm_until=K_['reforma']
    if st=='fogo' or (st=='queimado' and t<sm_until):
        inten=clamp((t-K_['fogo0'])/0.6) if st=='fogo' else 0.0
        if st=='fogo' and t>K_['apagou']-1.2: inten*=clamp((K_['apagou']-t)/1.2)
        def fn(vd,vx0,vy0,k,inten=inten,st=st):
            rr=random.Random(7)
            def S(x,y,z): X,Y=iso.PW(x,y,z); return (X*k-vx0,Y*k-vy0)
            nfl=int(110*inten)
            for i in range(nfl):                                    # chamas
                px=rr.uniform(MX0,MX1); py=rr.uniform(MY0,MY1); base=16 if rr.random()<0.6 else rr.uniform(4,14)
                if base<16: py=MY1
                ph=rr.uniform(0,1); life=0.7; a=((t*1.6+ph)%life)/life
                z=base+a*14*rr.uniform(0.6,1.3); X,Y=S(px+math.sin(t*9+i)*0.6,py,z)
                c=[(255,240,120),(255,180,40),(240,90,30),(200,40,20)][min(3,int(a*4))]
                s_=max(1,int((1-a)*6*k))
                vd.rectangle([X-s_,Y-s_*2,X+s_,Y],fill=c+(230,))
            ns=int(30*inten)+(14 if st=='queimado' else 0)
            for i in range(ns):                                     # fumaça
                ph=rr.uniform(0,1); life=2.4; a=((t*0.7+ph)%life)/life
                px=rr.uniform(MX0+2,MX1-2)+a*16; py=rr.uniform(MY0+2,MY1-2)-a*8; z=18+a*60
                X,Y=S(px,py,z); r_=int((3+a*9)*k)
                g=int(70+a*60) if st=='fogo' else int(110+a*60)
                vd.ellipse([X-r_,Y-r_,X+r_,Y+r_],fill=(g,g,g,int(170*(1-a))))
        out.append((MX+MY+42,('fn',fn)))
    # baldes de água (correria) e jato do caminhão
    if K_['baldes']<=t<K_['apagou']:
        def fn2(vd,vx0,vy0,k):
            rr=random.Random(3)
            for i in range(14):
                ph=rr.uniform(0,1); a=((t*1.4+ph)%1.0)
                sx_=rr.uniform(MX0+2,MX1-2); x=sx_; y=MY1+3-a*2; z=4+math.sin(a*math.pi)*8
                X,Y=iso.PW(x,y,z); X=X*k-vx0; Y=Y*k-vy0
                if a<0.8: vd.rectangle([X-k,Y-k,X+k,Y+k],fill=(90,160,240,220))
        out.append((MX+MY+44,('fn',fn2)))
    if K_['banho']<=t<K_['reforma']+0.4:
        def fn3(vd,vx0,vy0,k):
            nx,ny,nz=TRUCK_PARK[0]-3,RB,9
            for j,(tx,tz) in enumerate(((MX+6,10),(MX+12,13),(MX+16,8))):
                for i in range(18):
                    u=((i/18)+t*1.8+j*0.3)%1.0
                    x=nx+(tx-nx)*u; y=ny+(MY1-ny)*u; z=nz+(tz-nz)*u+math.sin(u*math.pi)*6
                    X,Y=iso.PW(x,y,z); X=X*k-vx0; Y=Y*k-vy0
                    vd.rectangle([X-k,Y-k,X+k,Y+k],fill=(120,190,255,230))
                X,Y=iso.PW(tx,MY1,tz); X=X*k-vx0; Y=Y*k-vy0
                vd.ellipse([X-4*k,Y-3*k,X+4*k,Y+3*k],fill=(220,240,255,150))
        out.append((MX+MY+46,('fn',fn3)))
    return out

# ---------- bichos ----------
_CAT={}
def cat32(dr,fr,k):
    key=(dr,fr,k)
    if key in _CAT: return _CAT[key]
    im=Image.new('RGBA',(24,18),(0,0,0,0)); d=ImageDraw.Draw(im)
    c=(120,120,128); c2=(90,90,98); o=(40,40,46)
    sw=[0,1,0,-1][fr%4]
    for lx,o_ in ((5,sw),(8,-sw),(14,-sw),(17,sw)): d.rectangle([lx+o_,12,lx+o_,16],fill=c2)
    d.rectangle([4,8,18,13],fill=c,outline=o)
    d.rectangle([15,3,21,9],fill=c,outline=o); d.polygon([(15,3),(16,0),(17,3)],fill=c); d.polygon([(19,3),(20,0),(21,3)],fill=c)
    d.point((19,5),fill=(120,220,90)); d.point((17,5),fill=(120,220,90))
    d.line([(4,9),(1,4+abs(sw))],fill=c,width=2)
    if dr=='left': im=im.transpose(Image.FLIP_LEFT_RIGHT)
    if k==1: im=im.resize((12,9),Image.NEAREST)
    _CAT[key]=im; return im
_HEN={}
def hen32(fr,dr,k):
    key=(fr,dr,k)
    if key not in _HEN:
        h=V.HENS[fr%2]; h=h.resize((h.width*2,h.height*2),Image.NEAREST) if k==2 else h
        if dr=='left': h=h.transpose(Image.FLIP_LEFT_RIGHT)
        _HEN[key]=h
    return _HEN[key]
_ar=random.Random(91)
ANIMAIS=[]
for i in range(16):
    kind=['dog','cat','hen','hen','dog','cat'][i%6]
    if i<8: cx,cy=PX_+10+_ar.uniform(-6,40),ROADF+5+_ar.uniform(-3,3)      # perto do petshop
    else: cx,cy=_ar.uniform(30,200),_ar.choice([ROADE+5,ROADF+5,ROADD+5,RB])
    ANIMAIS.append(dict(kind=kind,cx=cx,cy=cy,amp=_ar.uniform(8,26),spd=_ar.uniform(0.6,1.6),ph=_ar.uniform(0,6.28),t0=K_['petshop']+0.6+i*0.12))
def animal_people(t):
    out=[]
    if t<K_['petshop']+0.6: return out
    for i,a in enumerate(ANIMAIS):
        if t<a['t0']: continue
        u=(t-a['t0'])*a['spd']+a['ph']
        e=clamp((t-a['t0'])/1.2)
        x=a['cx']+math.sin(u)*a['amp']*e; y=a['cy']+math.sin(u*1.7)*1.5
        if i<8: x=PX_+10+(x-PX_-10)*e; y=PY_+22+(y-PY_-22)*e
        dx=math.cos(u); dr='right' if dx>0 else 'left'; fr=int(t*10+i)%4
        if a['kind']=='dog': f=(lambda k,dr=dr,fr=fr: dog32(dr,fr,False,k))
        elif a['kind']=='cat': f=(lambda k,dr=dr,fr=fr: cat32(dr,fr,k))
        else: f=(lambda k,dr=dr,fr=fr: hen32(fr,dr,k))
        out.append((x,y,f))
    if K_['cachorro']-0.6<=t<T['petshop'][1]:                         # morador correndo atrás
        u=(t-K_['cachorro']+0.6)
        a=ANIMAIS[0]; x=PX_+10+math.sin((t-a['t0'])*a['spd']+a['ph'])*a['amp']-6; y=PY_+24
        out.append((x,y,sf(735,'right' if math.cos((t-a['t0'])*a['spd']+a['ph'])>0 else 'left',int(t*10)%4)))
    return out

# ---------- campeonato ----------
TEAM=[(12,(200,628)),(555,(199,643)),(168,(182,627)),(348,(182,644)),(236,(169,636)),(473,(158,629)),(441,(FX0+3,FYM))]
RIVAL=[(9301,(207,637)),(9302,(203,624)),(9303,(212,648)),(9304,(192,636)),(9305,(FX1-3,FYM))]
def ball_at(t):
    u=t*0.9; return (FXM+math.sin(u)*24+math.sin(u*2.3)*6,FYM+math.sin(u*1.6)*10,abs(math.sin(t*3.1))*3)
def game_people(t):
    out=[]
    a,b=T['campeonato']
    if not (a<=t<b or T['cta'][0]<=t): return out
    bx,by,_=ball_at(t)
    for k,(pid,(hx,hy)) in enumerate(TEAM):
        gk=k==6
        x=hx+(0 if gk else clamp((bx-hx)*0.35,-10,10))+math.sin(t*1.3+k)*2; y=(FYM+clamp(by-FYM,-4,4)) if gk else hy+clamp((by-hy)*0.3,-5,5)
        out.append((x,y,sf(pid,'right',int(t*8+k)%4,'goleiro' if gk else 'jogador')))
    for k,(pid,(hx,hy)) in enumerate(RIVAL):
        gk=k==4
        x=hx+(0 if gk else clamp((bx-hx)*0.35,-10,10))+math.sin(t*1.1+k*3)*2; y=(FYM+clamp(by-FYM,-4,4)) if gk else hy+clamp((by-hy)*0.3,-5,5)
        out.append((x,y,sf(pid,'left',int(t*8+k)%4,'goleiro' if gk else 'azul')))
    rr=random.Random(5)                                         # torcida
    for k in range(26):
        dj=1+k%4; pid=_regids[(k*3)%len(_regids)] if k%2==0 else rr.randint(1,C1)
        x=FX0+6+rr.uniform(0,FX1-FX0-12); y=FY1+2+dj*1.5-0.6
        hop=dj*1.5+(abs(math.sin((t*2.6+k*0.37)*math.pi))*3 if K_['torcida']<=t<b else 0)
        out.append((x,y,sf(pid,'up',0,hop=hop)))
    return out
def ball_extra(t):
    a,b=T['campeonato']
    if not (a<=t<b or T['cta'][0]<=t): return []
    x,y,h=ball_at(t)
    def ball(vd,vx0,vy0,k,x=x,y=y,h=h):
        X,Y=iso.PW(x,y,h); X=X*k-vx0; Y=Y*k-vy0; r=2*k
        Xs,Ys=iso.PW(x,y,0); Xs=Xs*k-vx0; Ys=Ys*k-vy0
        vd.ellipse([Xs-r,Ys-r/2,Xs+r,Ys+r/2],fill=(0,30,0,80))
        vd.ellipse([X-r,Y-2*r,X+r,Y],fill=(250,250,250),outline=(40,40,50))
    return [(x+y+0.6,('fn',ball))]
_regids=sorted(i for i in REG if i<=C1)

# ---------- moradores ----------
BRIGADA=[740,744,752,760,733,766,771,778]
def fire_people(t):
    out=[]
    if K_['fumaca']<=t<K_['apagou']+2.0:                       # correria com balde
        for k,pid in enumerate(BRIGADA):
            run=K_['baldes']-0.4<=t<K_['apagou']
            ph=k/len(BRIGADA)
            if run:
                u=((t*0.55+ph)%1.0); go=u<0.5; f=u*2 if go else (1-u)*2
                x0,y0=128+k*1.5,RB+6; x1,y1=MX0+2+k*2.2,MY1+3
                x=x0+(x1-x0)*f; y=y0+(y1-y0)*f
                dr='right' if go else 'left'
                out.append((x,y,sf(pid,dr,int(t*10+k)%4,carry='balde')))
            else:
                x=120+k*7; y=RB+8+(k%2)*3
                out.append((x,y,sf(pid,'up',0)))
    if K_['banho']-0.3<=t<T['bombeiros'][1]:                   # bombeiros com a mangueira
        for k in range(3):
            out.append((TRUCK_PARK[0]-6+k*5,RB-1.5,sf(8040+k,'up',0,'bombeiro')))
    if K_['fundado']+0.8<=t<K_['caminhao']:                     # equipe na frente do quartel
        for k in range(4): out.append((BX+4+k*4,BY+25,sf(8040+k,'down',0,'bombeiro')))
    return out
def iso_people(t,cam):
    cx,cy,z=cam; vw,vh=1080/z,1920/z
    out=[]; names=[]
    for pp in people:
        st=person_state(pp,t)
        if st is None: continue
        x,y=st[0],st[1]
        if FX0-4<x<FX1+4 and FY0-4<y<FY1+10: continue
        if MX0-4<x<MX1+6 and MY1-2<y<RB+6 and K_['fumaca']<=t<T['bombeiros'][1]: continue
        px,py=iso.PW(x,y)
        if not (cx-vw/2-20<px<cx+vw/2+20 and cy-vh/2-30<py<cy+vh/2+30): continue
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
            for j in range(2): out.append((lx_+4+j*12,ly_+22,sf(8000+(i+j)%6,'down',int(t*6+j)%2*2,'pedreiro')))
    for (pb,lb) in ((bomb_p(t),BOMBEIROS),(pet_p(t),PETSHOP)):
        if 0<pb<1:
            lx_,ly_=lot(*lb)
            for j in range(3): out.append((lx_+3+j*7,ly_+23,sf(8010+j,'down',int(t*6+j)%2*2,'pedreiro')))
    if T['petshop'][0]<=t<K_['cachorro']:                          # inauguração
        for j in range(6): out.append((PX_+2+j*3.5,PY_+26+(j%2)*2,sf(722+j*7,'up',0)))
    out+=fire_people(t)+game_people(t)+animal_people(t)
    if T['eleicao'][0]<=t<T['promessa'][1] and False: pass
    return out,names

# ---------- câmera ----------
CAMS=[(0.0,CI(132,452,4.0)),(T['titulo'][1]-0.4,CI(132,452,4.5)),
      (T['recap'][0]+0.6,CI(FXM,FYM,2.6)),(T['recap'][1]-0.2,CI(150,520,1.2)),
      (T['fogo'][0]+0.4,CI(MX+10,MY+14,2.6)),(K_['fogo0'],CI(MX+10,MY+16,4.6)),(K_['baldes'],CI(MX+6,MY+20,5.2)),
      (K_['apagou'],CI(MX+8,MY+20,5.4)),(T['fogo'][1],CI(MX+8,MY+18,5.6)),
      (T['bombeiros'][0]+0.3,CI(BX+10,BY+18,4.0)),(K_['caminhao']-0.3,CI(BX+10,BY+18,4.4))]
CAMS_B=[(K_['banho']-0.3,CI(MX+8,MY+22,4.6)),(T['bombeiros'][1],CI(MX+8,MY+20,5.2)),
      (T['casas'][0]+0.3,CI(110,505,1.9)),(K_['ruaE'],CI(110,505,2.0)),(K_['ruaF']-0.2,CI(110,505,2.0)),(K_['ruaF']+0.4,CI(104,600,3.4)),(T['casas'][1],CI(104,600,3.6)),
      (T['petshop'][0]+0.3,CI(PX_+14,PY_+22,4.2)),(K_['cachorro']-0.4,CI(PX_+16,PY_+24,4.4)),(T['petshop'][1],CI(PX_+40,PY_+26,3.4)),
      (T['campeonato'][0]+0.3,CI(FXM,FYM-3,4.4)),(T['campeonato'][1],CI(FXM,FYM-3,5.2)),
      (T['proximo'][0]+0.3,CI(QX+12,QY+4,4.2)),(T['proximo'][1],CI(QX+12,QY+4,5.0)),
      (T['resumo'][0]+0.3,CI(140,500,1.5)),(T['resumo'][1],CI(140,420,0.82)),
      (T['cta'][0]+0.3,CI(160,424,3.4)),(DUR+1,CI(160,424,4.0))]
def _interp_cam(t,L):
    for (a,va),(b,vb) in zip(L,L[1:]):
        if a<=t<b:
            f=smooth((t-a)/(b-a)); return tuple(va[i]+(vb[i]-va[i])*f for i in range(3))
    return L[-1][1] if t>=L[-1][0] else L[0][1]
def camiso(t):
    if t<K_['caminhao']-0.3: c=_interp_cam(t,CAMS)
    elif t<K_['banho']-0.3:
        x,y,_,_=truck_at(t); c=CI(x,y,4.0)
        f=smooth(clamp((t-K_['caminhao']+0.3)/0.5)); c0=CAMS[-1][1]; c=tuple(c0[i]+(c[i]-c0[i])*f for i in range(3))
    else: c=_interp_cam(t,CAMS_B)
    if K_['FOGO']<=t<K_['FOGO']+0.8:
        k=(1-(t-K_['FOGO'])/0.8)*5; c=(c[0]+math.sin(t*70)*k,c[1]+math.cos(t*63)*k,c[2])
    return c
def w2si(x,y,cam,z_=0):
    cx,cy,zz=cam; px,py=iso.PW(x,y,z_)
    return ((px-(cx-540/zz))*zz/4,(py-(cy-960/zz))*zz/4)

# ---------- telas de UI cheia ----------
CANDS=[(12,"CRISTIANO RONALDO"),(347,"JOÃO GUILHERME"),(154,"WESLEY"),(67,"KIRA"),(614,"ENZO MILDANA"),(11,"ISABELY67"),
       (2,"DIDI"),(189,"CABELUDO"),(621,"BACHIRAPRO"),(647,"SALES"),(426,"MT"),(335,"APENAS UM JOGADOR"),(191,"JESSICA"),(257,"ALBERT AISTEN")]
def poster(lay,d,x,y,w,pid,nm,col,hl=False):
    d.rectangle([x,y,x+w,y+w],fill=col+(255,),outline=(255,255,255,255),width=6 if hl else 3)
    d.rectangle([x+10,y+10,x+w-10,y+w*0.7],fill=(250,246,232,255))
    h=head_img(pid); sc=max(1,int(min((w-30)/h.width,(w*0.62)/h.height))); h2=h.resize((h.width*sc,h.height*sc),Image.NEAREST)
    lay.paste(h2,(int(x+w/2-h2.width/2),int(y+w*0.7-h2.height)),h2)
    d.rectangle([x+10,y+w*0.72,x+w-10,y+w-10],fill=(24,22,52,255))
    tw=text_width(nm,1); im=Image.new('RGBA',(tw+4,12),(0,0,0,0)); draw_text(ImageDraw.Draw(im),nm,(tw+4)//2,2,1,WHITE)
    f=min(4,(w-28)/(tw+4)); im=im.resize((max(1,int((tw+4)*f)),max(1,int(12*f))),Image.NEAREST)
    lay.paste(im,(int(x+w/2-im.width/2),int(y+w*0.86-im.height/2)),im)
COLS=[(214,50,50),(40,90,190),(40,150,80),(240,180,40),(150,80,180),(230,120,40)]
def mural(t):
    fr=blur_bg('mural',T['eleicao'][0],CI(160,424,3.0),0.5).convert('RGBA')
    lay=Image.new('RGBA',(OUTW,OUTH),(0,0,0,0)); d=ImageDraw.Draw(lay)
    a=T['eleicao'][0]
    for k,(pid,nm) in enumerate(CANDS):
        t0=a+0.3+k*0.14; v=clamp((t-t0)/0.18)
        if v<=0: continue
        r,c=divmod(k,3)
        if k>=12: c=k-12+0.5
        x=int(130+c*290); y=380+r*228+int((1-v)*40)
        poster(lay,d,x,y,210,pid,nm,COLS[k%6],k>=11)
        if k>=11 and t>=a+0.3+k*0.14+0.3:
            d.rectangle([x+120,y-14,x+220,y+22],fill=(250,214,60,255)); draw_text_big(lay,"NOVO!",x+170,y-6,3,(160,30,30,255))
    fr.alpha_composite(lay)
    if t>=K_['abriu']:                                                 # urna
        v=clamp((t-K_['abriu'])/0.25); u=Image.new('RGBA',(OUTW,OUTH),(0,0,0,0)); du=ImageDraw.Draw(u)
        cx,cy=540,1760+int((1-v)*200)
        du.rectangle([cx-150,cy-90,cx+150,cy+90],fill=(240,240,236,255),outline=(24,22,52,255),width=8)
        du.rectangle([cx-70,cy-100,cx+70,cy-82],fill=(24,22,52,255))
        pp_=int(((t*1.3)%1.0)*60); du.rectangle([cx-40,cy-170+pp_,cx+40,cy-110+pp_],fill=(255,255,255,255),outline=(24,22,52,255),width=4)
        draw_text_big(u,"VOTE",cx,cy-30,6,(40,90,190,255))
        fr.alpha_composite(u)
    return fr.convert('RGB')
def draw_text_big(img,txt,cx,y,sc,col):
    tw=text_width(txt,1); im=Image.new('RGBA',(tw+4,12),(0,0,0,0)); draw_text(ImageDraw.Draw(im),txt,(tw+4)//2,2,1,col)
    im=im.resize(((tw+4)*sc,12*sc),Image.NEAREST); img.alpha_composite(im,(int(cx-im.width/2),int(y)))
def campanha(t):
    """fala 15: panfleto da jessica, discurso do Enzo e a briga do 777"""
    fr=blur_bg('camp',T['eleicao'][0],CI(132,250,3.0),0.45).convert('RGBA')
    lay=Image.new('RGBA',(OUTW,OUTH),(0,0,0,0)); d=ImageDraw.Draw(lay)
    if t<K_['discurso']:
        s=npc_k(191,'down',0,2,carry='panfleto').resize((32*12,48*12),Image.NEAREST); lay.paste(s,(140,560),s)
        d.rectangle([540,520,1010,1060],fill=(250,250,244,255),outline=(40,90,190,255),width=10)
        draw_text_big(lay,"VOTE",775,560,7,(40,90,190,255)); draw_text_big(lay,"JOÃO",775,680,7,(200,40,50,255)); draw_text_big(lay,"GUILHERME",775,800,4,(200,40,50,255))
        draw_text_big(lay,"(ELA É A 32!)",775,920,3,(24,22,52,255))
    elif t<K_['briga']:
        s=npc_k(614,'down',0,2).resize((32*11,48*11),Image.NEAREST); lay.paste(s,(360,1100),s)
        d.rounded_rectangle([90,520,990,1020],radius=40,fill=(255,255,255,255),outline=(24,22,52,255),width=8)
        d.polygon([(470,1015),(560,1015),(500,1100)],fill=(255,255,255,255))
        for i,(ln,c) in enumerate((("A COMIDA ACABA...",(24,22,52,255)),("MAS A PALAVRA",(24,22,52,255)),("DE UM HOMEM",(24,22,52,255)),("MANTÉM-SE FIXA!",(200,40,50,255)))):
            draw_text_big(lay,ln,540,580+i*105,5,c)
    else:
        for side,(pid,nm,msg,col) in enumerate(((335,"APENAS UM JOGADOR","VOTEM 777!",(214,50,50)),(621,"BACHIRAPRO","TA ME COPIANDO!",(40,90,190)))):
            x=60+side*500; y=520
            d.rectangle([x,y,x+460,y+700],fill=col+(255,),outline=(255,255,255,255),width=6)
            s=npc_k(pid,'down' if side==0 else 'down',0,2).resize((32*9,48*9),Image.NEAREST); lay.paste(s,(x+230-s.width//2,y+20),s)
            d.rectangle([x+14,y+470,x+446,y+686],fill=(24,22,52,255))
            draw_text_big(lay,nm,x+230,y+490,2 if len(nm)>12 else 3,WHITE)
            draw_text_big(lay,"777",x+230,y+540,6,(255,214,70,255))
            draw_text_big(lay,msg,x+230,y+630,2,(255,255,255,255))
        v=clamp((t-K_['n777'])/0.2)
        if v>0:
            sc=int(8+4*(1-v)); draw_text_big(lay,"X",540,800,sc,(255,214,70,255))
    fr.alpha_composite(lay); return fr.convert('RGB')
def promessa(t):
    fr=blur_bg('prom',T['eleicao'][0],CI(160,424,3.0),0.45).convert('RGBA')
    lay=Image.new('RGBA',(OUTW,OUTH),(0,0,0,0)); d=ImageDraw.Draw(lay)
    poster(lay,d,240,420,600,335,"APENAS UM JOGADOR",(214,50,50))
    d.rectangle([140,1060,940,1300],fill=(250,250,244,255),outline=(24,22,52,255),width=6)
    draw_text_big(lay,"PROMESSA:",540,1080,3,(24,22,52,255))
    draw_text_big(lay,"DELEGACIA, HOSPITAL",540,1140,3,(200,40,50,255)); draw_text_big(lay,"E BOMBEIROS",540,1210,4,(200,40,50,255))
    fr.alpha_composite(lay)
    v=clamp((t-K_['antes']+0.4)/0.2)
    if v>0:
        st=Image.new('RGBA',(260,90),(0,0,0,0)); ds=ImageDraw.Draw(st)
        ds.rectangle([3,3,256,86],outline=(60,220,90,255),width=5); draw_text(ds,"JÁ TEM!",130,26,4,(60,220,90,255))
        sc=1+(1-v)*1.2; st=st.resize((int(260*2.6*sc/1.6),int(90*2.6*sc/1.6)),Image.NEAREST).rotate(10,expand=True)
        fr.alpha_composite(st,(540-st.width//2,1240-st.height//2))
    return fr.convert('RGB')
def destaque(t):
    fr=blur_bg('dest',T['eleicao'][0],CI(132,250,3.0),0.45).convert('RGBA')
    lay=Image.new('RGBA',(OUTW,OUTH),(0,0,0,0)); d=ImageDraw.Draw(lay)
    for kk in range(5): d.polygon([(540,300),(360-kk*30,1450),(720+kk*30,1450)],fill=(255,240,200,9))
    d.polygon([(340,1440),(540,1340),(740,1440),(540,1540)],fill=(80,70,120,255))
    fr.alpha_composite(lay)
    dr=['down','right','down','left'][int((t-T['destaque'][0])/0.7)%4]
    s=npc_k(614,dr,0,2).resize((32*15,48*15),Image.NEAREST)
    fr.alpha_composite(s,(540-s.width//2,1440-s.height))
    return fr.convert('RGB')

# ---------- UI por cima ----------
def draw_ui(t,cam,mode,tnames=None):
    ui=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ui)
    C=count_at(t); hs=nhouses(C)
    if t>=T['recap'][0] and mode=='city':
        y0=36
        box(d,32,y0,238,y0+42)
        draw_text(d,"SEGUIDORES",86,y0+7,1,LBLUE); draw_text(d,"CASAS",192,y0+7,1,LBLUE)
        d.line([150,y0+6,150,y0+36],fill=(120,120,180,255))
        draw_text(d,str(C),86,y0+20,2,YEL if C!=count_at(t-0.12) else WHITE)
        draw_text(d,str(hs),192,y0+20,2,YEL if hs!=nhouses(count_at(t-0.4)) else WHITE)
    a,b=T['titulo']; v=pop(t,a,b)
    if v>0:
        box(d,20,118,250,208,(24,22,52,int(225*v)))
        draw_text(d,"A CIDADE DOS",135,130,2,WHITE); draw_text(d,"SEGUIDORES",135,152,3,YEL); draw_text(d,"EPISÓDIO 9",135,188,1,LBLUE)
    a,b=T['recap']
    banner(d,["DA ÚLTIMA VEZ:"],110,t,a+0.3,b,[LBLUE],1)
    banner(d,["CAMPO DE FUTEBOL"],134,t,a+0.6,b,[GREEN],2)
    banner(d,["721 MORADORES"],166,t,a+2.6,b,[YEL],2)
    # fogo
    a,b=T['fogo']
    chip(d,"CHEIRO DE FUMAÇA...",135,120,t,K_['fumaca'],K_['FOGO']-0.1,WHITE)
    if K_['FOGO']<=t<K_['apagou']:
        sc=int(5+math.sin(t*18)*0.6); draw_text(d,"FOGO!",135,120+int(math.sin(t*25)*3),sc,(255,120,40,255),outline=(90,20,10,255))
        if mode=='city':
            sx,sy=w2si(MX+10,MY1,cam,22); tag_s(d,"MERCADINHO DO CENTRO",sx,sy,t,K_['FOGO']+0.4,K_['baldes']+0.5,RED,dy=-60)
    chip(d,"BALDE PRA CÁ...",80,390,t,K_['baldes']+0.4,K_['apagou'],LBLUE)
    chip(d,"...BALDE PRA LÁ!",190,410,t,K_['la'],K_['apagou'],LBLUE)
    banner(d,["NINGUÉM","SE MACHUCOU!"],110,t,K_['apagou'],b,[WHITE,GREEN],2)
    banner(d,["MAS PRECISAVA","DE BOMBEIROS..."],380,t,K_['precisava'],b,[WHITE,YEL],2)
    # bombeiros
    a,b=T['bombeiros']
    if K_['fundado']<=t<K_['caminhao']+0.6:
        box(d,16,104,254,186,(200,40,50,240))
        draw_text(d,"FUNDADO O",135,114,1,WHITE); draw_text(d,"CORPO DE",135,130,2,YEL); draw_text(d,"BOMBEIROS!",135,154,3,YEL)
        fireworks(d,t,K_['fundado']+0.3,6)
    chip(d,"SIRENE LIGADA!",135,400,t,K_['sirene'],K_['banho'],RED)
    banner(d,["PRIMEIRA MISSÃO:","BANHO NO MERCADINHO"],110,t,K_['banho'],K_['reforma']-0.1,[LBLUE,WHITE],1)
    banner(d,["MERCADINHO","REFORMADO!"],110,t,K_['reforma'],b,[WHITE,GREEN],2)
    if K_['reforma']<=t<K_['reforma']+1.2: fireworks(d,t,K_['reforma'],5,(160,300))
    # casas
    banner(d,["A RUA E FECHOU!"],110,t,K_['ruaE'],K_['ruaF']-0.1,[GREEN],2)
    banner(d,["A RUA F","COMEÇOU!"],110,t,K_['ruaF'],T['casas'][1],[WHITE,YEL],2)
    if mode=='city':
        for n,t0 in ((73,K_['c73']),(74,K_['c74']),(75,K_['c75']),(76,K_['c76']),(77,K_['c77']),(78,K_['c78'])):
            x,y=lot(*house_lots[n-1]); sx,sy=w2si(x+10,y+12,cam,22)
            tag_s(d,f"CASA {n}",sx,sy,t,t0,(K_['ruaF']-0.1 if n<77 else T['casas'][1]),GREEN if n<77 else YEL)
    # petshop
    a,b=T['petshop']
    if K_['petshop']<=t<K_['cachorro']-0.1:
        box(d,30,110,240,170,(220,80,140,240)); draw_text(d,"ABRIU O",135,118,1,WHITE); draw_text(d,"PETSHOP!",135,134,3,WHITE)
        fireworks(d,t,K_['petshop']+0.2,5,(170,300))
    banner(d,["BICHARADA SOLTA!"],110,t,K_['cachorro']-0.1,b,[YEL],2)
    for k,(w_,t0) in enumerate((("CACHORRO",K_['cachorro']),("GATO",K_['gato']),("GALINHA",K_['galinha']))):
        chip(d,w_,70+k*65,400,t,t0,b,[YEL,LBLUE,WHITE][k])
    # campeonato
    a,b=T['campeonato']
    if a<=t<b:
        v=pop(t,a,b)
        box(d,24,100,246,150,(24,22,52,235)); draw_text(d,"CAMPEONATO DE PINDAMONHANGABA",135,108,1,YEL)
        g1=1 if t>=K_['timecontra']+0.6 else 0; g2=1 if t>=K_['torcida']+0.4 else 0; g1+=1 if t>=b-0.8 else 0
        d.rectangle([44,122,98,142],fill=(40,150,80,255)); d.rectangle([172,122,226,142],fill=(40,90,190,255))
        draw_text(d,"VERDE",71,128,1,WHITE); draw_text(d,"AZUL",199,128,1,WHITE); draw_text(d,f"{g1}  X  {g2}",135,126,2,WHITE)
    chip(d,"TIME CONTRA TIME!",135,400,t,K_['timecontra'],b,WHITE)
    chip(d,"ARQUIBANCADA LOTADA!",135,420,t,K_['torcida'],b,GREEN)
    # eleição
    a,b=T['eleicao']
    if mode=='mural':
        box(d,14,40,256,88,(200,40,50,240)); draw_text(d,"ELEIÇÃO PRA PREFEITO",135,48,1,WHITE)
        draw_text(d,"14 CANDIDATOS!" if t>=K_['c14'] else "...",135,62,2,YEL)
        if t>=K_['abriu']:
            v=clamp((t-K_['abriu'])/0.2); y=384
            box(d,40,y,230,y+26,(40,150,80,245)); draw_text(d,"VOTAÇÃO ABERTA!",135,y+8,1 if v<1 else 1,WHITE)
    if mode=='campanha':
        if t<K_['discurso']: banner(d,["PANFLETANDO","PRO ADVERSÁRIO!"],40,t,K_['panfleto']-0.4,K_['discurso'],[WHITE,YEL],2)
        elif t<K_['briga']: banner(d,["DISCURSO NO CHAT"],40,t,K_['discurso'],K_['briga'],[YEL],2)
        else: banner(d,["QUEM É O","VERDADEIRO 777?"],40,t,K_['briga'],b,[WHITE,YEL],2)
    if mode=='promessa':
        banner(d,["PROMETEU BOMBEIROS..."],40,t,T['promessa'][0]+0.2,T['promessa'][1],[WHITE],2)
        banner(d,["O FOGO CHEGOU","ANTES DA ELEIÇÃO!"],400,t,K_['antes'],T['promessa'][1],[YEL,WHITE],1)
    if mode=='destaque':
        a,b=T['destaque']
        banner(d,["MORADOR EM DESTAQUE"],40,t,a+0.1,b,[YEL],2)
        banner(d,["ENZO MILDANA"],74,t,a+0.4,b,[WHITE],3)
        for k,(w_,t0,x,y) in enumerate((("FEZ DISCURSO",K_['discurso2'],70,150),("ACALMOU A BRIGA",K_['discurso2']+0.8,200,200),("SEMPRE ON-LINE!",K_['online'],80,260))):
            chip(d,w_,x,y,t,t0,b,[YEL,GREEN,LBLUE][k])
        if t>=K_['online']:
            d.ellipse([196,252,204,260],fill=(60,220,90,255))
    # próximo marco
    a,b=T['proximo']
    if a<=t<b:
        box(d,30,96,240,170,(24,22,52,235)); draw_text(d,"PRÓXIMO MARCO",135,104,1,LBLUE); draw_text(d,"800",135,118,4,YEL)
        if t>=K_['m800']+0.6: draw_text(d,"PADARIA E LANCHONETE",135,156,1,WHITE)
        if mode=='city' and t>=K_['reservado']:
            sx,sy=w2si(QX+10,QY+22,cam,20); tag_s(d,"TERRENO RESERVADO!",sx,sy,t,K_['reservado'],b,GREEN,dy=-28)
        banner(d,["FALTAM SÓ 20!"],390,t,K_['faltam'],b,[YEL],3)
    # resumo
    a,b=T['resumo']
    banner(d,["RESULTADO:"],84,t,a+0.2,b,[LBLUE],1)
    banner(d,["780 MORADORES"],110,t,K_['r780'],b,[YEL])
    banner(d,["78 CASAS"],146,t,K_['r78'],b,[WHITE])
    banner(d,["1 CORPO DE BOMBEIROS"],330,t,K_['rbomb'],b,[RED])
    banner(d,["1 PETSHOP"],366,t,K_['rpet'],b,[(240,140,190,255)])
    a,b=T['cta']; v=pop(t,a,b+1,0.01)
    if v>0:
        yy=110+int((1-v)*14)
        box(d,24,yy,246,yy+62,(200,40,50,240))
        draw_text(d,"LINK NA BIO!",135,yy+10,2,WHITE); draw_text(d,"ESCOLHE O TEU MORADOR",135,yy+38,1,YEL)
        if t>=K_['votar']-0.2: banner(d,["E VAI VOTAR","NO TEU PREFEITO!"],370,t,K_['votar']-0.2,b+1,[WHITE,GREEN],2)
    return ui

def view_frame(t):
    iso.VOX=False; iso.K=2
    cam=camiso(t)
    ppl,names=iso_people(t,cam)
    ex=ball_extra(t)+truck_extra(t)+fire_extra(t)
    fr=iso.render_view(t,cam,ppl,ex,None)
    fr=placa_texto(fr,cam)
    return fr,cam,names
def render_frame(t):
    names=None; cam=camiso(t)
    a15=T['eleicao'][0]; e15=KW['panfleto']-0.5
    if a15<=t<e15: mode='mural'; fr=mural(t)
    elif e15<=t<T['eleicao'][1]: mode='campanha'; fr=campanha(t)
    elif T['promessa'][0]<=t<T['promessa'][1]: mode='promessa'; fr=promessa(t)
    elif T['destaque'][0]<=t<T['destaque'][1]: mode='destaque'; fr=destaque(t)
    else:
        fr,cam,names=view_frame(t); fr=grade(fr); mode='city'
    for t0,dur,k in ((KW['FOGO'],0.3,0.6),(KW['fundado'],0.25,0.5),(KW['reforma'],0.25,0.4),(KW['petshop'],0.2,0.4)):
        if t0<=t<t0+dur: fr=flash(fr,(1-(t-t0)/dur)*k)
    for cut in [T[k][0] for k in T]+[e15,KW['discurso'],KW['briga']]:
        if cut>0.1 and cut<=t<cut+0.1: fr=flash(fr,(1-(t-cut)/0.1)*0.35)
    if mode=='city' and KW['FOGO']<=t<KW['apagou']:                    # brilho laranja do fogo
        a=np.array(fr).astype(np.float32); a[:,:,0]*=1.06; a[:,:,2]*=0.9; fr=Image.fromarray(np.clip(a,0,255).astype(np.uint8))
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
