import numpy as np, math, random, sys, json
from PIL import Image, ImageDraw
from world import *
from scene import *
from font import draw_text, text_width

FPS=30; DUR=78.6
OUTW,OUTH=1080,1920
BASE,RIVER=make_base()
LAY=build_layers()
ry,rx=np.nonzero(RIVER)
CHOPPED_LOGS=[d['chop'] for d in trees if d['chop'] and d.get('mode')=='axe']
LAMPS=[(x,y) for y in range(124,460,34) for x in (123,140) if not (205<y<285) and not (ROADA-8<y<ROADA+16) and not (ROADC-8<y<ROADC+16)]
lamp_t={p:45.2+i*0.04 for i,p in enumerate(LAMPS)}
hr=random.Random(3); LIT_TH=[hr.uniform(0.15,0.85) for _ in range(30)]
PILE=(86,412)
def lot_xy(l): return lot(*l)
T250=time_reach(250)
H27=lot_xy(house_lots[26]); MER=lot_xy(MERCADO)
TARGETS={'h27':(H27[0]+10,H27[1]+20,96),'merc':(MER[0]+10,MER[1]+16,118)}
SIGN=(142,442)
CHURCH=(115,61)

def night(t): return smooth((t-56.5)/5.0)
def sunset(t): return smooth((t-51.5)/5.0)

def glow_sprite(r,col,a):
    g=np.zeros((2*r+1,2*r+1,3),np.float32)
    for y in range(2*r+1):
        for x in range(2*r+1):
            d=math.hypot(x-r,y-r)/r
            if d<1: g[y,x]=np.array(col)*a*(1-d)**1.6
    return g
GLOW_L=glow_sprite(12,(255,200,110),0.75); GLOW_S=glow_sprite(7,(255,190,100),0.6)

def compose_world(t):
    a=BASE.astype(np.int16).copy()
    # água animada
    m=((ry*3 - int(t*40) + (rx*7)%13) % 23)==0
    a[ry[m],rx[m]]=[150,200,250]
    m2=((ry*5 - int(t*25) + (rx*11)%17) % 31)==0
    a[ry[m2],rx[m2]]=[96,156,226]
    for lay,order,t0,t1 in LAY:
        if t<t0: continue
        p=clamp((t-t0)/(t1-t0))*1.0001
        msk=(order<=p)&(lay[:,:,3]>0)
        a[msk]=lay[:,:,:3][msk]
    img=Image.fromarray(a.clip(0,255).astype(np.uint8))
    d=ImageDraw.Draw(img)
    C=count_at(t)
    n=night(t)
    objs=[]  # (ybase, fn)
    glows=[]
    # árvores
    for tr_ in trees:
        x,y,r=tr_['x'],tr_['y'],tr_['r']
        ch=tr_['chop']
        if ch is not None and t>=ch:
            if tr_['mode']=='axe' and t<ch+1.3:
                objs.append((y,lambda d=d,x=x,y=y:(d.rectangle([x-1,y-2,x+1,y],fill=(120,82,48)),d.point((x,y-1),fill=(196,160,110)))))
            if tr_['mode']=='poof' and t<ch+0.45:
                f=(t-ch)/0.45
                def poof(d=d,x=x,y=y,f=f):
                    for k in range(10):
                        ang=k*0.628; rr=2+f*8
                        d.point((x+math.cos(ang)*rr,y-5+math.sin(ang)*rr),fill=(250,250,250))
                objs.append((y+1,poof))
            continue
        im,(ax,ay)=tree_img(r,tr_['k'])
        sh=0
        if ch is not None and tr_['mode']=='axe' and ch-0.9<t<ch: sh=(1 if int(t*16)%2 else -1)
        elif int((t*0.8+x*0.37))%7==0: sh=1 if (int(t*3+x)%2) else 0
        objs.append((y,lambda im=im,x=x,y=y,ax=ax,ay=ay,sh=sh: img.paste(im,(x-ax+sh,y-ay),im)))
        if ch is not None and tr_['mode']=='axe' and ch-0.9<t<ch+0.05:
            wk=WORKERS[int(ch*7)%4]; fr=int(t*7)%2
            pim=person_sprite(wk['skin'],wk['hair'],wk['shirt'],wk['pants'],0,'up' if fr else 'down')
            objs.append((y+1,lambda pim=pim,x=x,y=y: img.paste(pim,(x-8,y-6),pim)))
            if fr:
                objs.append((y+2,lambda x=x,y=y,t=t:[d.point((x-3+((t*50+k*13)%5),y-5-((t*40+k*7)%4)),fill=(196,150,100)) for k in range(3)]))
    # pilha de madeira
    nl=sum(1 for c in CHOPPED_LOGS if t>=c+0.3)
    if nl:
        def pile(nl=nl):
            px,py=PILE; k=0
            for row,cnt in enumerate([4,3,2,1]):
                for j in range(cnt):
                    if k>=nl: return
                    x=px+j*6+row*3; y=py-row*2
                    d.rectangle([x,y,x+5,y+1],fill=(140,92,52)); d.point((x,y),fill=(210,170,120)); d.point((x,y+1),fill=(180,140,96))
                    k+=1
        objs.append((PILE[1]+2,pile))
    # casas
    active=None
    for i,l in enumerate(house_lots):
        p=house_p(i,C)
        if p<=0: continue
        if p<1 and active is None: active=(i,l,p)
        x,y=lot_xy(l)
        lit = n>LIT_TH[i]
        hi=house_sprite(house_var[i],round(p*40)/40,lit)
        objs.append((y+21,lambda hi=hi,x=x,y=y: img.paste(hi,(x,y),hi)))
        if lit: glows.append((x+10,y+22,'S')); 
        if p<1:
            for k,wx in enumerate((x-3,x+18)):
                wk=WORKERS[(i+k)%6]; fr=int(t*6+k)%2
                pim=person_sprite(wk['skin'],wk['hair'],wk['shirt'],wk['pants'],0,'up' if fr else 'down')
                objs.append((y+22,lambda pim=pim,wx=wx,y=y: img.paste(pim,(wx,y+15),pim)))
            if int(t*8)%2: objs.append((y+30,lambda x=x,y=y,t=t:[d.point((x+3+((t*37+k*29)%14),y+12+((t*23+k*5)%8)),fill=(220,200,160)) for k in range(3)]))
        else:
            tdn=house_done_time(i)
            if tdn and t-tdn<0.6:
                f=(t-tdn)/0.6
                objs.append((999,lambda x=x,y=y,f=f:[d.point((x+10+math.cos(k*0.785)*(4+f*12),y+10+math.sin(k*0.785)*(4+f*12)),fill=(255,240,120)) for k in range(8)]))
            if t>39 and tdn:
                for k in range(3):
                    ph=((t+k*0.9+i*0.37)%2.7)/2.7
                    sx=x+14+ph*4; sy=y-1-ph*12
                    c=int(235-ph*60)
                    if ph<0.9:
                        objs.append((998,lambda sx=sx,sy=sy,c=c,ph=ph: d.rectangle([sx,sy,sx+(1 if ph>0.4 else 0),sy+(1 if ph>0.4 else 0)],fill=(c,c,c))))
    # cerquinhas
    for i,l in enumerate(house_lots):
        tdn=house_done_time(i)
        if i%3==1 and tdn and t>tdn+1.5:
            x,y=lot_xy(l)
            def fence(x=x,y=y):
                for fx in range(x,x+21,2):
                    if x+7<=fx<=x+12: continue
                    d.point((fx,y+22),fill=(250,246,236)); d.point((fx,y+21),fill=(250,246,236))
                d.line([x,y+22,x+6,y+22],fill=(214,206,190)); d.line([x+13,y+22,x+20,y+22],fill=(214,206,190))
            objs.append((y+23,fence))
    # vendinha
    if T250 and t>=T250:
        x,y=lot_xy(VENDA); p=clamp((t-T250)/0.9)
        vi=house_sprite(5,round(p*20)/20,n>0.4,venda=p>=1)
        objs.append((y+21,lambda vi=vi,x=x,y=y: img.paste(vi,(x,y),vi)))
        if n>0.4: glows.append((x+10,y+22,'S'))
    # lote do mercadinho
    if t>=64.0:
        x,y=lot_xy(MERCADO); mi=house_sprite(0,0.01)
        objs.append((y+21,lambda mi=mi,x=x,y=y: img.paste(mi,(x,y),mi)))
    # igreja
    if t>=46.4:
        p=clamp((t-46.4)/1.1); ci=church_sprite(round(p*30)/30,n>0.3)
        objs.append((CHURCH[1]+43,lambda ci=ci: img.paste(ci,CHURCH,ci)))
        if n>0.3: glows.append((131,105,'L'))
    # praça: árvore, poço, bancos, flores
    if t>=45.0:
        g=clamp((t-45.0)/1.0); r=max(2,int(2+g*4))
        im,(ax,ay)=tree_img(r,0)
        objs.append((231,lambda im=im,ax=ax,ay=ay: img.paste(im,(153-ax,231-ay),im)))
    if t>=45.5:
        def benches():
            for bx,by in ((108,266),(148,266),(108,222)):
                d.rectangle([bx,by,bx+6,by+1],fill=(150,100,56)); d.point((bx,by+2),fill=(70,50,30)); d.point((bx+6,by+2),fill=(70,50,30))
            for fx,fy in ((102,215),(158,215),(102,271),(158,271)):
                for k,c in enumerate([(240,80,90),(250,220,70),(240,140,200),(80,170,80)]):
                    d.point((fx+k%2,fy+k//2),fill=c)
        objs.append((268,benches))
    if t>=45.9:
        f=clamp((t-45.9)/0.4)
        def well(f=f):
            cx,cy=117,226
            if f<1:
                d.ellipse([cx-4*f,cy-4*f,cx+4*f,cy+4*f],fill=(150,150,156)); return
            d.ellipse([cx-5,cy-4,cx+5,cy+4],fill=(130,130,138)); d.ellipse([cx-3,cy-2,cx+3,cy+2],fill=(40,70,140))
            d.line([cx-5,cy-6,cx+5,cy-6],fill=(110,70,36)); d.line([cx-5,cy-6,cx-5,cy],fill=(110,70,36)); d.line([cx+5,cy-6,cx+5,cy],fill=(110,70,36))
            d.point((cx,cy-4),fill=(120,120,130)); d.point((cx,cy-5),fill=(90,90,96))
        objs.append((231,well))
    # postes
    for (lx,ly),t0 in lamp_t.items():
        if t>=t0:
            def lamp(lx=lx,ly=ly,lit=n>0.25):
                d.line([lx,ly-4,lx,ly],fill=(60,60,70)); d.point((lx,ly-5),fill=(255,230,120) if lit else (220,220,200)); d.point((lx,ly+1),fill=(0,0,0))
            objs.append((ly,lamp))
            if n>0.25: glows.append((lx,ly-5,'L'))
    # placa da entrada
    def sign():
        x,y=SIGN
        d.line([x+1,y,x+1,y+9],fill=(100,64,34)); d.line([x+12,y,x+12,y+9],fill=(100,64,34))
        d.rectangle([x,y,x+13,y+6],fill=(214,178,120)); d.rectangle([x,y,x+13,y+6],outline=(120,80,40))
    objs.append((SIGN[1]+9,sign))
    # galinhas
    if t>=38:
        for k in range(6):
            bx=40+k*31; by=ROADA+18 if k%2 else ROADA-6
            cx=bx+math.sin(t*0.9+k)*6; cy=by+math.sin(t*1.3+k*2)*2
            hop=int(t*4+k)%5==0
            objs.append((cy,lambda cx=cx,cy=cy-(1 if hop else 0):(d.rectangle([cx,cy,cx+1,cy+1],fill=(250,250,250)),d.point((cx,cy-1),fill=(220,40,40)),d.point((cx+2,cy),fill=(240,160,40)))))
    # carroça
    if t>=46:
        ph=((t-46)/14.0)%2; up=ph<1; f=smooth(ph if up else 2-ph)
        cy=468-f*350; cx=133
        def cart(cx=cx,cy=cy,up=up,t=t):
            hy=cy-7 if up else cy+8
            d.rectangle([cx-2,cy,cx+2,cy+6],fill=(150,100,56)); d.line([cx-2,cy,cx+2,cy],fill=(110,70,36))
            d.point((cx-3,cy+1),fill=(40,30,24)); d.point((cx+3,cy+1),fill=(40,30,24)); d.point((cx-3,cy+5),fill=(40,30,24)); d.point((cx+3,cy+5),fill=(40,30,24))
            d.rectangle([cx-1,hy,cx+1,hy+4],fill=(120,74,40)); d.point((cx,hy if up else hy+4),fill=(70,40,24))
            d.rectangle([cx-1,cy+1,cx+1,cy+3],fill=(220,190,80))
        objs.append((cy+6,cart))
    # moradores
    for pp in people:
        st=person_state(pp,t)
        if st is None: continue
        x,y,mv,tool=st
        fr=(int(t*6+pp['ph']*3)%2) if mv else 0
        im=pimg(pp,fr,tool)
        objs.append((y+5,lambda im=im,x=x,y=y: img.paste(im,(int(round(x))-2,int(round(y))-5),im)))
    # carregadores
    if 30.4<t<52 and active:
        i,l,p=active; hx,hy=lot_xy(l)
        roady=l[1]+5
        pts=[(PILE[0]+12,PILE[1]+4),(131.5,PILE[1]+4),(131.5,roady),(hx+10,roady)]
        L=plen(pts)
        for k in range(2):
            per=(t*1.0+k*1.5)%3.0; go=per<1.5; f=per/1.5 if go else (3.0-per)/1.5
            (x,y),_=path_pos(pts,L*f)
            wk=WORKERS[4+k]; im=person_sprite(wk['skin'],wk['hair'],wk['shirt'],wk['pants'],int(t*6)%2,None,go)
            objs.append((y+5,lambda im=im,x=x,y=y: img.paste(im,(int(x)-2,int(y)-5),im)))
    objs.sort(key=lambda o:o[0])
    for _,fn in objs: fn()
    # luz
    arr=np.asarray(img).astype(np.float32)
    s=sunset(t)
    if s>0 or n>0:
        tint=np.array([1,1,1])*(1-s)+np.array([1.0,0.78,0.62])*s
        tint=tint*(1-n)+np.array([0.30,0.34,0.60])*n
        arr*=tint
        for gx,gy,k in glows:
            g=GLOW_L if k=='L' else GLOW_S; r=g.shape[0]//2
            x0,y0=int(gx)-r,int(gy)-r
            xa,ya=max(0,x0),max(0,y0); xb,yb=min(W,x0+2*r+1),min(H,y0+2*r+1)
            if xa<xb and ya<yb:
                arr[ya:yb,xa:xb]+=g[ya-y0:yb-y0,xa-x0:xb-x0]*n
    return arr.clip(0,255).astype(np.uint8)

# ---------------- UI ----------------
NAVY=(24,22,52,235); WHITE=(255,255,255,255); YEL=(255,214,70,255); GREEN=(120,230,110,255)
def box(d,x0,y0,x1,y1,fill=NAVY):
    d.rectangle([x0,y0,x1,y1],fill=fill)
    d.rectangle([x0,y0,x1,y1],outline=(255,255,255,255))
    d.rectangle([x0+2,y0+2,x1-2,y1-2],outline=(120,120,180,255))
def pop(t,t0,t1,fade=0.25):
    """fator de escala/visibilidade com 'pop'"""
    if t<t0 or t>t1: return 0
    a=clamp((t-t0)/0.18); b=clamp((t1-t)/fade)
    return min(a,b)
def w2s(x,y,cam):
    cx,cy,vw=cam; vh=vw*H/W; s=W/vw
    return (x-(cx-vw/2))*s,(y-(cy-vh/2))*s
def banner(d,lines,y,t,t0,t1,colors=None,scale=2):
    v=pop(t,t0,t1)
    if v<=0: return
    wmax=max(text_width(s,scale) for s in lines)+16
    hh=len(lines)*(9*scale+4)+10
    yy=y+int((1-v)*12)
    box(d,135-wmax//2,yy,135+wmax//2,yy+hh)
    for k,s in enumerate(lines):
        c=(colors[k] if colors else WHITE)
        draw_text(d,s,135,yy+7+k*(9*scale+4)+(2*scale),scale,c)
def draw_ui(t,cam):
    ui=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ui)
    C=count_at(t); houses=sum(1 for i in range(27) if house_p(i,C)>=1)
    # caixa do contador
    ys=int((1-smooth(t/0.6))*-60)
    y0=36+ys
    box(d,32,y0,238,y0+42)
    draw_text(d,"SEGUIDORES",86,y0+7,1,(180,200,255,255))
    draw_text(d,"CASAS",192,y0+7,1,(180,200,255,255))
    d.line([150,y0+6,150,y0+36],fill=(120,120,180,255))
    prev=count_at(t-0.12)
    col=YEL if (C!=prev or (2.6<t<3.9 and int(t*6)%2)) else WHITE
    draw_text(d,str(C),86,y0+20,2,col)
    hp=sum(1 for i in range(27) if house_p(i,count_at(t-0.4))>=1)
    draw_text(d,str(houses),192,y0+20,2,YEL if houses!=hp else WHITE)
    # título
    v=pop(t,0.2,4.1)
    if v>0:
        draw_text(d,"A CIDADE DOS",135,130,2,WHITE)
        draw_text(d,"SEGUIDORES",135,152,3,YEL)
        draw_text(d,"EPISÓDIO 1",135,186,1,(200,220,255,255))
    if 6.9<t<9.2: draw_text(d,"TERRENO VAZIO",135,250,1,WHITE)
    banner(d,["O DESAFIO"],150,t,10.5,12.5,[YEL],3)
    banner(d,["A VILA CRESCE","JUNTO COM O CANAL"],140,t,12.7,14.4)
    if 14.5<t<19.3:
        v=pop(t,14.5,19.3); yy=128+int((1-v)*12)
        box(d,28,yy,242,yy+34)
        draw_text(d,"1 SEGUIDOR = 1 MORADOR",145,yy+12,1,WHITE)
        pi=person_sprite(SKINS[1]+(255,),HAIRS[0]+(255,),SHIRTS[0]+(255,),PANTS[0]+(255,),0).resize((15,24),Image.NEAREST)
        ui.paste(pi,(38,yy+6),pi)
    if 16.4<t<19.3:
        v=pop(t,16.4,19.3); yy=172+int((1-v)*12)
        box(d,28,yy,242,yy+40)
        draw_text(d,"10 SEGUIDORES = 1 CASA",150,yy+15,1,YEL)
        hi=house_sprite(0,1.0)
        ui.paste(hi,(36,yy+8),hi)
    # etapa da construção
    if 30.4<t<37.9:
        for i,l in enumerate(house_lots):
            p=house_p(i,C)
            if 0<p<1:
                lab="FUNDAÇÃO" if p<0.25 else ("PAREDE" if p<0.6 else "TELHADO")
                x,y=lot_xy(l); sx,sy=w2s(x+10,y-2,cam)
                draw_text(d,lab,int(sx),int(sy)-12,1,YEL); break
    for tt,s in ((40.4,"10"),(41.4,"50"),(42.75,"100")):
        v=pop(t,tt,tt+0.95,0.2)
        if v>0:
            sc=3 if v<1 else 4
            draw_text(d,s+" SEGUIDORES!",135,200-int(v*10),2,GREEN)
    for tt,s in ((44.0,"+ RUAS"),(44.9,"+ PRAÇA"),(45.9,"+ POÇO"),(47.1,"+ IGREJA")):
        v=pop(t,tt,tt+1.0,0.2)
        if v>0: draw_text(d,s,135,330-int(v*8),2,WHITE)
    if 50.0<t<51.9 and int(t*10)%2==0:
        pass
    banner(d,["267 MORADORES"],128,t,52.4,54.4,[YEL],2)
    banner(d,["26 CASAS PRONTAS"],128,t,54.5,56.0,[WHITE],2)
    if 56.2<t<61.2:
        x,y=H27; sx,sy=w2s(x+10,y,cam)
        bob=int(math.sin(t*5)*2)
        draw_text(d,"7/10",int(sx),int(sy)-30+bob,2,YEL)
        if t>57.8: banner(d,["FALTAM SÓ 3!"],380,t,57.8,61.2,[GREEN],2)
    banner(d,["MAIS SEGUIDORES","= CIDADE MAIOR"],128,t,61.8,64.3,[WHITE,YEL])
    if 64.4<t<67.8:
        x,y=MER; sx,sy=w2s(x+10,y,cam)
        draw_text(d,"300",int(sx),int(sy)-26+int(math.sin(t*5)*2),3,YEL)
        banner(d,["PRÓXIMO MARCO:","300 > MERCADINHO"],120,t,64.6,67.8,[WHITE,GREEN])
    if 68.1<t<75.0:
        x,y=SIGN; sx,sy=w2s(x+7,y,cam)
        draw_text(d,"???",int(sx),int(sy)-34+int(math.sin(t*6)*3),3,YEL)
    banner(d,["QUAL VAI SER O","NOME DA VILA?"],112,t,68.4,75.0,[WHITE,YEL])
    banner(d,["COMENTA AÍ!"],196,t,70.8,75.0,[GREEN])
    if 72.3<t<75.0: draw_text(d,"O MAIS CURTIDO VAI PRA PLACA",135,246,1,WHITE)
    v=pop(t,75.2,78.6,0.01)
    if v>0:
        yy=150+int((1-v)*14)
        box(d,30,yy,240,yy+62,(200,40,50,240))
        draw_text(d,"SEGUE E VIRA",135,yy+10,2,WHITE)
        draw_text(d,"MORADOR!",135,yy+34,3,YEL)
    return ui

def render_frame(t):
    cam=cam_at(t,TARGETS)
    cx,cy,vw=cam; vh=vw*H/W
    cx=clamp(cx,vw/2,W-vw/2); cy=clamp(cy,vh/2,H-vh/2); cam=(cx,cy,vw)
    arr=compose_world(t)
    img=Image.fromarray(arr)
    box_=(cx-vw/2,cy-vh/2,cx+vw/2,cy+vh/2)
    fr=img.resize((OUTW,OUTH),Image.NEAREST,box=box_)
    ui=draw_ui(t,cam).resize((OUTW,OUTH),Image.NEAREST)
    fr=fr.convert('RGBA'); fr.alpha_composite(ui)
    # fade inicial/final
    return fr.convert('RGB')

if __name__=='__main__':
    for t in map(float,sys.argv[1:]):
        render_frame(t).resize((360,640)).save(f'/home/claude/vila/test_{t}.png')
