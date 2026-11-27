import numpy as np, math, random, sys, json, os
from PIL import Image, ImageDraw, ImageFilter
from world import *
from scene import *
from font import draw_text, text_width
import vila16 as V
import iso, vox

# =====================================================================
#  EP. 10 — PADARIA (800), RUA G, TORRE (900) RESERVADA, VACAS, ELEIÇÃO EMPATADA (32 bits)
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
        grade.v=(1-0.16*np.clip(v-0.6,0,1))[:,:,None]
    a=a*grade.v
    return Image.fromarray(np.clip(a,0,255).astype(np.uint8))

# =====================================================================
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
def draw_text_big(img,txt,cx,y,sc,col,ol=True):
    tw=text_width(txt,1); im=Image.new('RGBA',(tw+4,12),(0,0,0,0))
    if ol: draw_text(ImageDraw.Draw(im),txt,(tw+4)//2,2,1,col)
    else: draw_text(ImageDraw.Draw(im),txt,(tw+4)//2,2,1,col,outline=None)
    im=im.resize(((tw+4)*sc,12*sc),Image.NEAREST); img.alpha_composite(im,(int(cx-im.width/2),int(y)))

# =====================================================================
#  EP. 10 — cenas
# =====================================================================
K_=KW
def CI(x,y,z): px,py=iso.PW(x,y); return (px,py,z)
QX,QY=lot(*PADARIA); PX_,PY_=lot(*PETSHOP); TX,TY=lot(*TORRE); BX,BY=lot(*BOMBEIROS)
FX0,FY0,FX1,FY1=vox.campo_rect(); FXM,FYM=(FX0+FX1)/2,(FY0+FY1)/2
CX0,CY0,CX1,CY1=iso.CURRAL
FARMER=(-100,348)
RF=ROADF+5; RG=ROADG+5

# ---------- cachorros coloridos (os 3 do GLEYDSON) ----------
_DC={}
def dogc(dr,fr,k,col,peludo=False,pequeno=False):
    key=(dr,fr,k,col,peludo,pequeno)
    if key in _DC: return _DC[key]
    im=Image.new('RGBA',(30,22),(0,0,0,0)); d=ImageDraw.Draw(im)
    c=col; c2=tuple(int(v*0.78) for v in col); o=tuple(int(v*0.4) for v in col)
    sw=[0,1,0,-1][fr%4]
    for lx,o_ in ((7,sw),(10,-sw),(17,-sw),(20,sw)): d.rectangle([lx+o_,15,lx+1+o_,20],fill=c2)
    d.rectangle([5,9,22,16],fill=c,outline=o)
    if peludo:
        for xx in range(5,23,2): d.line([(xx,9),(xx+1,7)],fill=c); d.line([(xx,16),(xx+1,18)],fill=c)
    d.rectangle([19,4,27,11],fill=c,outline=o); d.rectangle([25,8,28,11],fill=tuple(min(255,int(v*1.15)+20) for v in col),outline=o)
    d.point((27,8),fill=(20,20,20)); d.point((23,6),fill=(20,20,20)); d.rectangle([19,3,21,7],fill=c2)
    d.line([(5,10),(1,6-abs(sw))],fill=c,width=2)
    d.rectangle([18,9,20,11],fill=(220,40,40))                         # coleira
    if dr=='left': im=im.transpose(Image.FLIP_LEFT_RIGHT)
    if pequeno: im=im.resize((22,16),Image.NEAREST)
    if k==1: im=im.resize((im.width//2,im.height//2),Image.NEAREST)
    else: im=im.resize((int(im.width*1.4),int(im.height*1.4)),Image.NEAREST)
    im.info['foot']=0
    _DC[key]=im; return im
DOGS3=[((40,36,40),False,True,"PRETO PEQUENO"),((226,184,90),True,False,"AMARELO PELUDO"),((214,170,80),False,False,"AMARELO PELO CURTO")]

# ---------- vacas ----------
_COW={}
def cow32(dr,fr,k,var=0):
    key=(dr,fr,k,var)
    if key in _COW: return _COW[key]
    im=Image.new('RGBA',(36,26),(0,0,0,0)); d=ImageDraw.Draw(im)
    w=(246,244,238); b=(40,36,40) if var%2==0 else (150,90,50); o=(60,56,60)
    sw=[0,1,0,-1][fr%4]
    for lx,o_ in ((7,sw),(11,-sw),(22,-sw),(26,sw)): d.rectangle([lx+o_,17,lx+2+o_,24],fill=w); d.rectangle([lx+o_,23,lx+2+o_,24],fill=o)
    d.rectangle([5,8,28,18],fill=w,outline=o)
    rr=random.Random(var)
    for _ in range(3):
        x=rr.randint(7,22); y=rr.randint(9,14); d.ellipse([x,y,x+rr.randint(3,6),y+rr.randint(2,4)],fill=b)
    d.rectangle([26,4,34,13],fill=w,outline=o); d.rectangle([29,10,35,14],fill=(240,170,170),outline=o)
    d.point((31,7),fill=(20,20,20)); d.line([(26,4),(24,2)],fill=(220,210,180)); d.line([(33,4),(35,2)],fill=(220,210,180))
    d.ellipse([14,17,18,20],fill=(240,170,170))
    d.line([(5,9),(2,15)],fill=w,width=2)
    if dr=='left': im=im.transpose(Image.FLIP_LEFT_RIGHT)
    if k==1: im=im.resize((18,13),Image.NEAREST)
    im.info['foot']=0
    _COW[key]=im; return im

# ---------- obras: rua G (máquina) ----------
def roller_extra(t):
    rg=rua_g(t)
    if not (0<rg<1): return []
    out=[]
    for sgn in (-1,1):
        x=131.5+sgn*(6+rg*120)
        def fn(vd,vx0,vy0,k,x=x,sgn=sgn):
            def Q(dx,dy,dz): X,Y=iso.PW(x+dx,RG+dy,dz); return (X*k-vx0,Y*k-vy0)
            vd.polygon([Q(-3,-3,0),Q(3,-3,0),Q(3,3,0),Q(-3,3,0)],fill=(0,30,0,80))
            for (a0,a1,b0,b1,z0,z1,c) in ((-3,3,-3,3,1.5,5,(250,200,40)),(-1,2,-2,2,5,9,(250,200,40))):
                vd.polygon([Q(a0,b1,z0),Q(a1,b1,z0),Q(a1,b1,z1),Q(a0,b1,z1)],fill=iso.sh(c,0.85))
                vd.polygon([Q(a1,b0,z0),Q(a1,b1,z0),Q(a1,b1,z1),Q(a1,b0,z1)],fill=iso.sh(c,0.7))
                vd.polygon([Q(a0,b0,z1),Q(a1,b0,z1),Q(a1,b1,z1),Q(a0,b1,z1)],fill=c)
            cx_,cy_=Q(sgn*3.5,0,1.5); vd.ellipse([cx_-3*k,cy_-3*k,cx_+3*k,cy_+3*k],fill=(70,70,76))
            p_=Q(0,0,9.5); on=int(t*6)%2; vd.rectangle([p_[0]-k,p_[1]-k,p_[0]+k,p_[1]+k],fill=(255,150,40) if on else (150,90,30))
        out.append((x+RG+2,('fn',fn)))
    return out

# ---------- fumaça do forno ----------
def smoke_extra(t):
    if padaria_p(t)<1: return []
    sx,sy=QX+17.5,QY+5.5
    def fn(vd,vx0,vy0,k):
        rr=random.Random(4)
        for i in range(14):
            ph=rr.uniform(0,1); a=((t*0.5+ph)%1.0)
            X,Y=iso.PW(sx+a*6,sy-a*3,23+a*26); X=X*k-vx0; Y=Y*k-vy0; r_=int((2+a*6)*k)
            g=int(220+a*25); vd.ellipse([X-r_,Y-r_,X+r_,Y+r_],fill=(g,g,g,int(170*(1-a))))
    return [(sx+sy+30,('fn',fn))]

# ---------- ponte fantasma (1000) ----------
def ponte_extra(t):
    a,b=T['ponte']
    if not (a<=t<b or t>=T['resumo'][0]+99): return []
    f=clamp((t-K_['ponte'])/0.8)
    if f<=0: return []
    y=ROADD+5
    def fn(vd,vx0,vy0,k):
        def S(x,yy,z): X,Y=iso.PW(x,yy,z); return (X*k-vx0,Y*k-vy0)
        x0,x1=220,262
        on=int(t*4)%2
        col=(255,255,255,int(230*f)) if on else (255,214,70,int(230*f))
        for side in (-4,4):
            for xx in np.arange(x0,x1,2.0):
                if int(xx/2)%2: continue
                a_=S(xx,y+side,0); b_=S(xx+1.4,y+side,0)
                vd.line([a_,b_],fill=col,width=2*k)
                a_=S(xx,y+side,4); b_=S(xx+1.4,y+side,4)
                vd.line([a_,b_],fill=col,width=2*k)
        for xx in np.arange(x0,x1+0.1,6):
            vd.line([S(xx,y-4,0),S(xx,y-4,4)],fill=col,width=2*k); vd.line([S(xx,y+4,0),S(xx,y+4,4)],fill=col,width=2*k)
        X,Y=S(241,y,9); draw_text(vd,'1000',int(X),int(Y)-4*k,k,(255,214,70,int(255*f)),outline=(24,22,52,255))
    return [(240+y+10,('fn',fn))]

# ---------- moradores ----------
FILA=[781,786,790,794,798,802,806,810]
def special_people(t):
    out=[]
    # fila na padaria
    if T['padaria'][0]+0.8<=t<T['padaria'][1]+0.3:
        for k,pid in enumerate(FILA):
            out.append((QX+18+k*3.2,QY+21,sf(pid,'left',0,hop=abs(math.sin(t*3+k))*1.0 if t>=K_['fila'] else 0)))
    # Venefrides com o pão de queijo
    if K_['paoqueijo']-0.4<=t<T['padaria'][1]+0.3:
        f=clamp((t-K_['paoqueijo']+0.4)/1.6)
        x=QX+14+f*10; y=QY+21+f*5
        out.append((x,y,sf(136,'right' if f<1 else 'down',int(t*8)%4 if f<1 else 0,hop=abs(math.sin(t*6))*2 if t>=K_['ganhou'] else 0)))
    # obras na rua G
    if 0<rua_g(t)<1:
        for j in range(3): out.append((131.5-14+j*14,RG+9,sf(8020+j,'up',int(t*6+j)%2*2,'pedreiro')))
    # GLEYDSON sai do petshop com os 3 cachorros
    a,b=T['destaque']
    if K_['saiu']-0.3<=t<b:
        f=clamp((t-K_['saiu']+0.3)/2.4)
        x=PX_+10+f*22; y=PY_+25
        out.append((x,y,sf(75,'right',int(t*8)%4,hop=abs(math.sin(t*5))*1.5 if t>=K_['tres'] else 0)))
        for j,(col,pel,peq,_) in enumerate(DOGS3):
            out.append((x+3.5+j*3.0,y+2.2+(j%2)*1.6,(lambda k,col=col,pel=pel,peq=peq,j=j: dogc('right',int(t*10+j)%4,k,col,pel,peq))))
    # fazenda: fazendeiro e as vacas
    a,b=T['vacas']
    if a-0.2<=t<b+0.2:
        out.append((FARMER[0],FARMER[1],sf(9500,'left',int(t*3)%2*2 if t>=K_['vacas'] else 0,'fazendeiro',carry='balde')))
        if t>=K_['vacas']-0.3:
            cf=clamp((t-K_['vacas']+0.3)/1.2)
            out.append((CX1+12-cf*26,CY0+24,(lambda k,fr=int(t*6)%4,cf=cf: cow32('left',fr if cf<1 else 0,k,0))))
    return out
def iso_people(t,cam):
    cx,cy,z=cam; vw,vh=1080/z,1920/z
    out=[]; names=[]
    for pp in people:
        st=person_state(pp,t)
        if st is None: continue
        x,y=st[0],st[1]
        if FX0-4<x<FX1+4 and FY0-4<y<FY1+10: continue
        if QX-2<x<QX+50 and QY+16<y<QY+28 and T['padaria'][0]<=t<T['padaria'][1]+0.3: continue
        if PX_-14<x<PX_+70 and PY_+14<y<PY_+40 and T['destaque'][0]<=t<T['destaque'][1]+0.3: continue
        px,py=iso.PW(x,y)
        if not (cx-vw/2-20<px<cx+vw/2+20 and cy-vh/2-30<py<cy+vh/2+30): continue
        st0=person_state(pp,t-0.08)
        dx,dy=(x-st0[0],y-st0[1]) if st0 else (0,1)
        moving=abs(dx)+abs(dy)>0.05
        sxd,syd=(dx-dy)*2,(dx+dy)
        dr=('right' if sxd>0 else 'left') if abs(sxd)>abs(syd)*1.2 else ('down' if syd>0 else 'up')
        if not moving: dr='down'
        out.append((x,y,sf(pp['id'],dr,(int(t*8+pp['ph']*3)%4) if moving else 0)))
        if pp['id'] in REG and z>=2.4 and pp['id'] not in (75,136): names.append((abs(px-cx)+abs(py-cy),x,y,pp['id']))
        if len(out)>80: break
    names=[n[1:] for n in sorted(names)[:3]]
    C=count_at(t)
    for i,l in enumerate(house_lots):
        p=house_p(i,C)
        if 0<p<1:
            lx_,ly_=lot(*l)
            for j in range(2): out.append((lx_+4+j*12,ly_+22,sf(8000+(i+j)%6,'down',int(t*6+j)%2*2,'pedreiro')))
    pq=padaria_p(t)
    if 0<pq<1:
        for j in range(3): out.append((QX+3+j*7,QY+21,sf(8010+j,'down',int(t*6+j)%2*2,'pedreiro')))
    out+=special_people(t)
    return out,names

# ---------- câmera ----------
CAMS=[(0.0,CI(132,452,4.0)),(T['titulo'][1]-0.4,CI(132,452,4.5)),
      (T['recap'][0]+0.4,CI(BX+10,BY+18,3.6)),(T['recap'][1]-0.2,CI(130,560,1.5)),
      (T['oito'][0]+0.3,CI(60,600,1.8)),(T['oito'][1],CI(QX+12,QY+12,3.4)),
      (T['padaria'][0]+0.6,CI(QX+14,QY+12,4.6)),(K_['paoqueijo']-0.5,CI(QX+18,QY+16,5.0)),(T['padaria'][1],CI(QX+22,QY+20,5.4)),
      (T['casas'][0]+0.3,CI(110,610,2.6)),(T['casas'][1],CI(115,610,2.8)),
      (T['ruag'][0]+0.3,CI(131,RG,2.0)),(K_['terreno']-0.2,CI(131,RG,2.2)),(K_['torre'],CI(TX+12,TY+6,4.2)),(T['ruag'][1],CI(TX+12,TY+6,4.6)),
      (K_['saiu']-0.3,CI(PX_+18,PY_+24,7.0)),(T['destaque'][1],CI(PX_+30,PY_+25,7.6)),
      (T['vacas'][0]+0.3,CI(-110,330,4.0)),(K_['curral'],CI(-122,322,4.4)),(T['vacas'][1],CI(-124,322,4.8)),
      (T['ponte'][0]+0.2,CI(200,420,2.4)),(K_['ponte'],CI(238,424,3.4)),(T['ponte'][1],CI(238,424,3.8)),
      (T['resumo'][0]+0.3,CI(130,560,1.3)),(T['resumo'][1],CI(130,450,0.8)),
      (T['cta'][0]+0.3,CI(QX+14,QY+14,3.6)),(DUR+1,CI(QX+14,QY+14,4.2))]
def _interp_cam(t,L):
    for (a,va),(b,vb) in zip(L,L[1:]):
        if a<=t<b:
            f=smooth((t-a)/(b-a)); return tuple(va[i]+(vb[i]-va[i])*f for i in range(3))
    return L[-1][1] if t>=L[-1][0] else L[0][1]
def camiso(t): return _interp_cam(t,CAMS)
def w2si(x,y,cam,z_=0):
    cx,cy,zz=cam; px,py=iso.PW(x,y,z_)
    return ((px-(cx-540/zz))*zz/4,(py-(cy-960/zz))*zz/4)

# ---------- telas cheias ----------
def destaque_card(t):
    """fala 10: card do morador em destaque + os 3 cachorros aparecendo"""
    fr=blur_bg('dest',T['destaque'][0],CI(PX_+20,PY_+22,3.0),0.8).convert('RGBA')
    lay=Image.new('RGBA',(OUTW,OUTH),(0,0,0,0)); d=ImageDraw.Draw(lay)
    for kk in range(5): d.polygon([(540,300),(360-kk*30,1300),(720+kk*30,1300)],fill=(255,240,200,9))
    d.polygon([(330,1290),(540,1200),(750,1290),(540,1380)],fill=(80,70,120,255))
    fr.alpha_composite(lay)
    s=npc_k(75,'down',0,2).resize((32*13,48*13),Image.NEAREST); fr.alpha_composite(s,(540-s.width//2,1290-s.height))
    for j,((col,pel,peq,nm),tk) in enumerate(zip(DOGS3,('preto','peludo','curto'))):
        t0=K_[tk]; v=clamp((t-t0)/0.25)
        if v<=0: continue
        x=180+j*360; y=1480
        dg=dogc('right' if j<2 else 'left',0,2,col,pel,peq); sc=7 if not peq else 7
        dg=dg.resize((dg.width*sc,dg.height*sc),Image.NEAREST)
        yy=y+int((1-v)*120)
        fr.alpha_composite(dg,(x-dg.width//2,yy))
        draw_text_big(fr,nm,x,yy+dg.height+10,3 if len(nm)<15 else 2,(255,214,70,255))
    return fr.convert('RGB')
CHAT=[("CABO JAIR","QUERO COLOCAR PANFLETE, SANTINHO","OU FAZER COMÍCIO, ALGUÉM SABE COMO FAZ?"),
      ("ENZO MILDANA","VCS VIRAM O EPISÓDIO 9?",""),
      ("GLEYDSON","QUERO MEUS CACHORROS, OS 3...","DESDE O EPISÓDIO 1 KSKSKS"),
      ("VENEFRIDES","ALGUÉM ARRUMA UM PÃO DE QUEIJO?",""),
      ("ISABELY67","VOTA EM MIM!","")]
def chat_phone(t):
    fr=blur_bg('chat',T['chat'][0],CI(132,250,3.0),0.8).convert('RGBA')
    lay=Image.new('RGBA',(OUTW,OUTH),(0,0,0,0)); d=ImageDraw.Draw(lay)
    a,b=T['chat']; v=clamp((t-a)/0.3)
    ox=int((1-v)*600)
    X0,Y0,X1,Y1=170+ox,330,910+ox,1700
    d.rounded_rectangle([X0,Y0,X1,Y1],radius=70,fill=(20,20,26,255))
    d.rounded_rectangle([X0+24,Y0+70,X1-24,Y1-70],radius=20,fill=(236,229,221,255))
    d.rounded_rectangle([(X0+X1)//2-70,Y0+28,(X0+X1)//2+70,Y0+46],radius=9,fill=(50,50,58,255))
    d.rectangle([X0+24,Y0+70,X1-24,Y0+180],fill=(40,120,90,255))
    draw_text_big(lay,"CHAT DA CIDADE",(X0+X1)//2,Y0+92,3,(255,255,255,255))
    draw_text_big(lay,"PINDAMONHANGABA",(X0+X1)//2,Y0+142,2,(200,240,220,255))
    n=int((t-a-0.3)/0.55)+1
    y=Y0+210
    for k,(nm,l1,l2) in enumerate(CHAT[:max(0,n)]):
        h=160 if l2 else 120
        mine=k%2==1
        bx0=X0+40 if not mine else X0+80; bx1=X1-80 if not mine else X1-40
        d.rounded_rectangle([bx0,y,bx1,y+h],radius=18,fill=(255,255,255,255) if not mine else (220,248,198,255))
        draw_text_big(lay,nm,(bx0+bx1)//2,y+12,2,[(200,60,60,255),(40,90,190,255),(150,80,180,255),(40,140,80,255),(230,120,40,255)][k])
        f=min(3,int((bx1-bx0-30)/(text_width(l1,1)+4))) or 1
        draw_text_big(lay,l1,(bx0+bx1)//2,y+50,f,(30,30,30,255),False)
        if l2: draw_text_big(lay,l2,(bx0+bx1)//2,y+92,min(3,int((bx1-bx0-30)/(text_width(l2,1)+4))) or 1,(30,30,30,255),False)
        y+=h+22
    fr.alpha_composite(lay); return fr.convert('RGB')
CANDS=[(12,"CRISTIANO RONALDO"),(347,"JOÃO GUILHERME"),(154,"WESLEY"),(67,"KIRA"),(614,"ENZO MILDANA"),(11,"ISABELY67"),
       (2,"DIDI"),(189,"CABELUDO"),(621,"BACHIRAPRO"),(647,"SALES"),(426,"MT"),(335,"APENAS UM JOGADOR"),(191,"JESSICA"),(257,"ALBERT AISTEN"),
       (96,"CABO JAIR"),(434,"SAITU")]
def mural16(t):
    fr=blur_bg('mural',T['mural'][0],CI(160,424,3.0),0.8).convert('RGBA')
    lay=Image.new('RGBA',(OUTW,OUTH),(0,0,0,0)); d=ImageDraw.Draw(lay)
    a=T['mural'][0]
    for k,(pid,nm) in enumerate(CANDS):
        t0=a+0.2+k*0.11; v=clamp((t-t0)/0.18)
        if v<=0: continue
        r,c=divmod(k,4)
        x=int(70+c*240); y=420+r*250+int((1-v)*40)
        poster(lay,d,x,y,215,pid,nm,COLS[k%6],k>=14)
        if k>=14 and t>=t0+0.3:
            d.rectangle([x+110,y-14,x+215,y+22],fill=(250,214,60,255)); draw_text_big(lay,"NOVO!",x+162,y-6,3,(160,30,30,255))
    fr.alpha_composite(lay); return fr.convert('RGB')
PLACAR=[(614,"ENZO MILDANA",3),(96,"CABO JAIR",3),(11,"ISABELY67",2),(335,"APENAS UM JOGADOR",1)]
def placar(t):
    fr=blur_bg('placar',T['placar'][0],CI(160,424,3.0),0.8).convert('RGBA')
    lay=Image.new('RGBA',(OUTW,OUTH),(0,0,0,0)); d=ImageDraw.Draw(lay)
    a,b=T['placar']
    if t<K_['sexta']:
        for side,(pid,nm,v_) in enumerate(PLACAR[:2]):
            x=70+side*500; y=460
            col=[(40,90,190),(214,50,50)][side]
            d.rectangle([x,y,x+440,y+760],fill=col+(255,),outline=(255,255,255,255),width=6)
            s=npc_k(pid,'down',0,2).resize((32*9,48*9),Image.NEAREST); lay.paste(s,(x+220-s.width//2,y+20),s)
            d.rectangle([x+14,y+470,x+426,y+746],fill=(24,22,52,255))
            draw_text_big(lay,nm,x+220,y+490,3,WHITE)
            vv=min(v_,int(clamp((t-K_['empate'])/max(0.5,K_['tres3']-K_['empate']))*v_+0.999)) if t>=K_['empate'] else 0
            draw_text_big(lay,str(vv),x+220,y+550,11,(255,214,70,255))
            draw_text_big(lay,"VOTOS",x+220,y+690,3,WHITE)
        if t>=K_['empate']:
            vv=clamp((t-K_['empate'])/0.2); draw_text_big(lay,"X",540,760,int(6+4*(1-vv)),(255,214,70,255))
        y=1280
        for k,(pid,nm,v_) in enumerate(PLACAR[2:]):
            d.rectangle([110,y+k*90,970,y+k*90+70],fill=(24,22,52,230),outline=(255,255,255,255),width=3)
            draw_text_big(lay,f"{nm}: {v_} VOTO{'S' if v_>1 else ''}",540,y+k*90+18,3,WHITE)
    else:
        d.ellipse([290,560,790,1060],fill=(250,250,244,255),outline=(24,22,52,255),width=14)
        ang=(t*1.6)%(2*math.pi)
        d.line([540,810,540+int(math.sin(ang)*190),810-int(math.cos(ang)*190)],fill=(200,40,50,255),width=14)
        d.line([540,810,540+int(math.sin(ang/12)*120),810-int(math.cos(ang/12)*120)],fill=(24,22,52,255),width=18)
        d.ellipse([520,790,560,830],fill=(24,22,52,255))
        draw_text_big(lay,"SEXTA 11:25",540,1110,6,(255,214,70,255))
        draw_text_big(lay,"A VOTAÇÃO FECHA",540,1210,3,WHITE)
        if t>=K_['quem']:
            pz=int(4*math.sin(t*8))
            draw_text_big(lay,"QUEM VAI SER",540,1320+pz,5,WHITE); draw_text_big(lay,"O PREFEITO?",540,1410+pz,5,(255,214,70,255))
        if t>=K_['ep11']:
            d.rectangle([200,1540,880,1640],fill=(200,40,50,255)); draw_text_big(lay,"DESCOBRE NO EP. 11!",540,1566,4,WHITE)
    fr.alpha_composite(lay); return fr.convert('RGB')

# ---------- UI ----------
def draw_ui(t,cam,mode):
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
        draw_text(d,"A CIDADE DOS",135,130,2,WHITE); draw_text(d,"SEGUIDORES",135,152,3,YEL); draw_text(d,"EPISÓDIO 10",135,188,1,LBLUE)
    a,b=T['recap']
    banner(d,["DA ÚLTIMA VEZ:"],110,t,a+0.3,b,[LBLUE],1)
    banner(d,["CORPO DE BOMBEIROS"],134,t,a+1.0,b,[RED],2)
    banner(d,["780 MORADORES"],166,t,a+3.4,b,[YEL],2)
    # 800
    if K_['oitocentos']<=t<T['oito'][1]+0.4:
        box(d,30,110,240,200,(200,40,50,240)); draw_text(d,"800!",135,124,6,YEL); draw_text(d,"MARCO BATIDO!",135,182,1,WHITE)
        fireworks(d,t,K_['oitocentos'],8)
    # padaria
    a,b=T['padaria']
    if K_['padaria']<=t<K_['forno']:
        box(d,24,108,246,170,(180,100,50,240)); draw_text(d,"ABRIU A",135,116,1,WHITE); draw_text(d,"PADARIA!",135,132,3,(255,240,200,255))
        fireworks(d,t,K_['padaria']+0.2,5,(180,300))
    chip(d,"PÃO QUENTINHO!",135,110,t,K_['forno'],K_['paoqueijo']-0.1,YEL)
    chip(d,"FILA NA PORTA!",135,130,t,K_['fila'],K_['paoqueijo']-0.1,WHITE)
    if mode=='city' and K_['paoqueijo']<=t<b:
        sx,sy=w2si(QX+20,QY+24,cam,16); tag_s(d,"VENEFRIDES",sx,sy,t,K_['paoqueijo'],b,YEL,dy=-44)
    banner(d,["PEDIU PÃO DE QUEIJO NA BIO..."],110,t,K_['paoqueijo'],b,[WHITE],1)
    banner(d,["...E GANHOU!"],130,t,K_['ganhou'],b,[GREEN],2)
    # casas
    a,b=T['casas']
    if mode=='city':
        for n,t0 in ((79,K_['c79']),(80,K_['c80']),(81,K_['c81'])):
            x,y=lot(*house_lots[n-1]); sx,sy=w2si(x+10,y+12,cam,22)
            tag_s(d,f"CASA {n}",sx,sy,t,t0,b,GREEN if n<81 else YEL)
    banner(d,["A RUA F TÁ ENCHENDO!"],110,t,a+0.3,b,[GREEN],2)
    # rua G + torre
    a,b=T['ruag']
    chip(d,"O ESPAÇO TÁ ACABANDO...",135,110,t,K_['espaco'],K_['ruanova']-0.05,WHITE)
    banner(d,["RUA NOVA!"],108,t,K_['ruanova'],K_['torre'],[YEL],3)
    if K_['ruanova']<=t<K_['torre']: chip(d,"RUA G",135,410,t,K_['ruanova']+0.3,K_['torre'],LBLUE)
    if K_['torre']<=t<b:
        box(d,30,100,240,170,(24,22,52,235)); draw_text(d,"TERRENO RESERVADO:",135,108,1,LBLUE)
        draw_text(d,"TORRE DE INTERNET",135,124,1,WHITE); draw_text(d,"900",135,140,3,YEL)
    # destaque
    a,b=T['destaque']
    if mode=='card':
        banner(d,["MORADOR EM DESTAQUE"],40,t,a+0.1,b,[YEL],2)
        banner(d,["GLEYDSON"],74,t,a+0.3,b,[WHITE],3)
        chip(d,"DESDE O EPISÓDIO 1...",135,120,t,a+1.0,b,LBLUE)
    if mode=='city' and t>=K_['saiu']-0.3 and a<=t<b:
        banner(d,["SAIU DO PETSHOP","COM OS TRÊS!"],100,t,K_['saiu'],b,[WHITE,GREEN],2)
        f=clamp((t-K_['saiu']+0.3)/2.4); sx,sy=w2si(PX_+10+f*22,PY_+25,cam,20)
        tag_s(d,"GLEYDSON",sx,sy,t,K_['saiu'],b,YEL,dy=-42)
        if t>=K_['tres']:
            for k in range(6):
                hx=40+k*38+int(math.sin(t*3+k)*5); hy=380-int(((t*40+k*23)%60))
                d.polygon([(hx,hy),(hx+4,hy-4),(hx+8,hy),(hx+4,hy+5)],fill=(240,80,120,255)); d.ellipse([hx-1,hy-6,hx+4,hy-1],fill=(240,80,120,255)); d.ellipse([hx+4,hy-6,hx+9,hy-1],fill=(240,80,120,255))
    # vacas
    a,b=T['vacas']
    banner(d,["O FAZENDEIRO AGORA","CUIDA DAS VACAS!"],100,t,K_['vacas']-0.4,K_['desafio']-0.05,[WHITE,YEL],1)
    if K_['desafio']<=t<b:
        v=clamp((t-K_['comentario'])/0.25)
        box(d,18,96,252,176,(40,120,70,240))
        draw_text(d,"DESAFIO!",135,104,1,YEL)
        if t>=K_['comentario']:
            sc=2+int((1-v)*2)
            draw_text(d,"1 COMENTÁRIO",135,122,2,WHITE); draw_text(d,"= 1 VACA!",135,146,2,YEL)
    if mode=='city' and K_['curral']<=t<b:
        sx,sy=w2si((CX0+CX1)/2,CY1,cam,8); tag_s(d,"CURRAL: VAGAS ABERTAS!",sx,sy,t,K_['curral'],b,YEL,dy=10)
        banner(d,["VAMOS VER, HEIN!"],400,t,K_['vamosver'],b,[YEL],2)
    if mode=='city' and K_['vacas']<=t<b:
        sx,sy=w2si(FARMER[0],FARMER[1],cam,20); tag_s(d,"O FAZENDEIRO",sx,sy,t,K_['vacas'],K_['curral'],WHITE,dy=-36)
    # eleição
    if mode=='chat':
        banner(d,["A VOTAÇÃO TÁ ABERTA!"],50,t,K_['aberta'],T['chat'][1],[GREEN],2)
        banner(d,["E O CHAT NÃO PARA!"],440,t,K_['chat'],T['chat'][1],[YEL],2)
    if mode=='mural':
        box(d,14,40,256,88,(200,40,50,240)); draw_text(d,"ELEIÇÃO PRA PREFEITO",135,48,1,WHITE)
        draw_text(d,"16 CANDIDATOS!" if t>=K_['c16'] else "...",135,62,2,YEL)
        chip(d,"CHEGOU ONTEM E JÁ TÁ LÁ EM CIMA!",135,395,t,K_['ontem'],T['mural'][1],YEL)
    if mode=='placar':
        if t<K_['sexta']:
            banner(d,["PLACAR AO VIVO"],40,t,T['placar'][0]+0.1,K_['sexta'],[YEL],2)
            banner(d,["EMPATE NO TOPO!"],78,t,K_['empate'],K_['sexta'],[WHITE],2)
    # ponte
    a,b=T['ponte']
    chip(d,"O RIO TÁ LOGO ALI...",135,110,t,a+0.2,K_['ponte']-0.05,LBLUE)
    if K_['ponte']<=t<b:
        box(d,24,100,246,170,(24,22,52,235)); draw_text(d,"EM BREVE:",135,108,1,LBLUE); draw_text(d,"A PONTE!",135,122,3,YEL)
        draw_text(d,"1000 = VIRA CIDADE",135,154,1,WHITE) if t>=K_['mil'] else None
    # resumo
    a,b=T['resumo']
    banner(d,["RESULTADO:"],84,t,a+0.2,b,[LBLUE],1)
    banner(d,["814 MORADORES"],110,t,K_['r814'],b,[YEL])
    banner(d,["81 CASAS"],146,t,K_['r81'],b,[WHITE])
    banner(d,["1 PADARIA"],330,t,K_['rpad'],b,[(255,220,160,255)])
    banner(d,["1 RUA NOVA"],366,t,K_['rrua'],b,[GREEN])
    a,b=T['cta']; v=pop(t,a,b+1,0.01)
    if v>0:
        yy=100+int((1-v)*14)
        box(d,24,yy,246,yy+62,(200,40,50,240))
        draw_text(d,"LINK NA BIO!",135,yy+10,2,WHITE); draw_text(d,"ESCOLHE O TEU MORADOR",135,yy+38,1,YEL)
        chip(d,"VOTA NO TEU PREFEITO!",135,360,t,K_['vota'],b+1,GREEN)
        if t>=K_['comenta']-0.2: banner(d,["COMENTA =","1 VACA PRO FAZENDEIRO!"],385,t,K_['comenta']-0.2,b+1,[WHITE,YEL],1)
    return ui

def view_frame(t):
    iso.VOX=False; iso.K=2
    cam=camiso(t)
    ppl,names=iso_people(t,cam)
    ex=roller_extra(t)+smoke_extra(t)+ponte_extra(t)
    fr=iso.render_view(t,cam,ppl,ex,None)
    fr=placa_texto(fr,cam)
    return fr,cam,names
def render_frame(t):
    names=None; cam=camiso(t)
    c_end=K_['saiu']-0.3
    if T['destaque'][0]<=t<c_end: mode='card'; fr=destaque_card(t)
    elif T['chat'][0]<=t<T['chat'][1]: mode='chat'; fr=chat_phone(t)
    elif T['mural'][0]<=t<T['mural'][1]: mode='mural'; fr=mural16(t)
    elif T['placar'][0]<=t<T['placar'][1]: mode='placar'; fr=placar(t)
    else:
        fr,cam,names=view_frame(t); fr=grade(fr); mode='city'
    for t0,dur,k in ((KW['oitocentos'],0.3,0.6),(KW['padaria'],0.25,0.5),(KW['ruanova'],0.2,0.3),(KW['empate'],0.2,0.4)):
        if t0<=t<t0+dur: fr=flash(fr,(1-(t-t0)/dur)*k)
    for cut in [T[k][0] for k in T]+[c_end,KW['sexta']]:
        if cut>0.1 and cut<=t<cut+0.1: fr=flash(fr,(1-(t-cut)/0.1)*0.35)
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
