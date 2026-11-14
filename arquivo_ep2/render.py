import numpy as np, math, random, sys, json, os
from PIL import Image, ImageDraw
from world import *
from scene import *
from font import draw_text, text_width

FPS=30
OUTW,OUTH=1080,1920
_est=json.load(open(os.path.join(os.path.dirname(__file__),'..','estado_vila.json')))
NOME_VILA=_est.get('nome_vila')   # None = ainda sem nome

# chão fixo (ruas e praça já prontas desde o ep. 1)
BASE,RIVER=make_base()
for lay,order,_,_ in build_layers():
    m=lay[:,:,3]>0; BASE[m]=lay[:,:,:3][m]
ry,rx=np.nonzero(RIVER)
LAMPS=[(x,y) for y in range(124,460,34) for x in (123,140) if not (205<y<285) and not (ROADA-8<y<ROADA+16) and not (ROADC-8<y<ROADC+16)]
PILE=(86,412); SIGN=(142,442); CHURCH=(115,61)
def lot_xy(l): return lot(*l)
MER=lot_xy(MERCADO)

def compose_world(t):
    a=BASE.astype(np.int16).copy()
    m=((ry*3 - int(t*40) + (rx*7)%13) % 23)==0; a[ry[m],rx[m]]=[150,200,250]
    m2=((ry*5 - int(t*25) + (rx*11)%17) % 31)==0; a[ry[m2],rx[m2]]=[96,156,226]
    img=Image.fromarray(a.clip(0,255).astype(np.uint8)); d=ImageDraw.Draw(img)
    C=count_at(t); objs=[]
    for tr_ in trees:
        x,y,r=tr_['x'],tr_['y'],tr_['r']
        im,(ax,ay)=tree_img(r,tr_['k'])
        sh=1 if (int((t*0.8+x*0.37))%7==0 and int(t*3+x)%2) else 0
        objs.append((y,lambda im=im,x=x,y=y,ax=ax,ay=ay,sh=sh: img.paste(im,(x-ax+sh,y-ay),im)))
    # pilha de madeira (cheia, do ep. 1)
    def pile():
        px,py=PILE
        for row,cnt in enumerate([4,3,2,1]):
            for j in range(cnt):
                x=px+j*6+row*3; y=py-row*2
                d.rectangle([x,y,x+5,y+1],fill=(140,92,52)); d.point((x,y),fill=(210,170,120)); d.point((x,y+1),fill=(180,140,96))
    objs.append((PILE[1]+2,pile))
    # casas
    active=None
    for i,l in enumerate(house_lots[:NH]):
        p=house_p(i,C)
        if p<=0: continue
        if p<1 and active is None: active=(i,l)
        x,y=lot_xy(l)
        hi=house_sprite(house_var[i],round(p*40)/40)
        objs.append((y+21,lambda hi=hi,x=x,y=y: img.paste(hi,(x,y),hi)))
        if p<1:
            for k,wx in enumerate((x-3,x+18)):
                wk=WORKERS[(i+k)%6]; fr=int(t*6+k)%2
                pim=person_sprite(wk['skin'],wk['hair'],wk['shirt'],wk['pants'],0,'up' if fr else 'down')
                objs.append((y+22,lambda pim=pim,wx=wx,y=y: img.paste(pim,(wx,y+15),pim)))
            if int(t*8)%2: objs.append((y+30,lambda x=x,y=y,t=t:[d.point((x+3+((t*37+k*29)%14),y+12+((t*23+k*5)%8)),fill=(220,200,160)) for k in range(3)]))
        else:
            tdn=house_done_time(i)
            if tdn and 0<=t-tdn<0.6:
                f=(t-tdn)/0.6
                objs.append((999,lambda x=x,y=y,f=f:[d.point((x+10+math.cos(k*0.785)*(4+f*12),y+10+math.sin(k*0.785)*(4+f*12)),fill=(255,240,120)) for k in range(8)]))
            for k in range(3):
                ph=((t+k*0.9+i*0.37)%2.7)/2.7
                sx=x+14+ph*4; sy=y-1-ph*12; c=int(235-ph*60)
                if ph<0.9: objs.append((998,lambda sx=sx,sy=sy,c=c,ph=ph: d.rectangle([sx,sy,sx+(1 if ph>0.4 else 0),sy+(1 if ph>0.4 else 0)],fill=(c,c,c))))
            if i%3==1 and (tdn is None or t>tdn+1.5):
                def fence(x=x,y=y):
                    for fx in range(x,x+21,2):
                        if x+7<=fx<=x+12: continue
                        d.point((fx,y+22),fill=(250,246,236)); d.point((fx,y+21),fill=(250,246,236))
                    d.line([x,y+22,x+6,y+22],fill=(214,206,190)); d.line([x+13,y+22,x+20,y+22],fill=(214,206,190))
                objs.append((y+23,fence))
    # vendinha
    x,y=lot_xy(VENDA); vi=house_sprite(5,1,venda=True)
    objs.append((y+21,lambda vi=vi,x=x,y=y: img.paste(vi,(x,y),vi)))
    # mercadinho
    mp=mercado_p(t); x,y=MER
    if t<T['obra'][0]:
        mi=house_sprite(0,0.01)   # só as estacas do lote reservado
    else:
        mi=mercado_sprite(round(mp*40)/40)
    objs.append((y+21,lambda mi=mi,x=x,y=y: img.paste(mi,(x,y),mi)))
    if 0<mp<1:
        for k,wx in enumerate((x-3,x+18)):
            wk=WORKERS[k+2]; fr=int(t*7+k)%2
            pim=person_sprite(wk['skin'],wk['hair'],wk['shirt'],wk['pants'],0,'up' if fr else 'down')
            objs.append((y+22,lambda pim=pim,wx=wx,y=y: img.paste(pim,(wx,y+15),pim)))
        if int(t*8)%2: objs.append((y+30,lambda x=x,y=y,t=t:[d.point((x+3+((t*37+k*29)%14),y+12+((t*23+k*5)%8)),fill=(220,200,160)) for k in range(4)]))
    tm=T['obra'][1]-1.2
    if 0<=t-tm<0.9:
        f=(t-tm)/0.9
        objs.append((999,lambda f=f:[d.point((x+10+math.cos(k*0.524)*(5+f*18),y+10+math.sin(k*0.524)*(5+f*18)),fill=[(255,240,120),(120,230,110),(250,250,250)][k%3]) for k in range(12)]))
    # escola: estacas no lote reservado a partir do "próximo marco"
    if t>=57.3:
        def stakes():
            ex,ey=lot_xy(ESCOLA[0])
            for (sx_,sy_) in [(ex+1,ey+3),(ex+42,ey+3),(ex+1,ey+20),(ex+42,ey+20)]:
                d.line([sx_,sy_-2,sx_,sy_],fill=(120,80,40))
            for fx in range(ex+1,ex+43,3): d.point((fx,ey+3),fill=(250,250,250)); d.point((fx,ey+20),fill=(250,250,250))
        objs.append((lot_xy(ESCOLA[0])[1]+21,stakes))
    # igreja
    ci=church_sprite(1)
    objs.append((CHURCH[1]+43,lambda ci=ci: img.paste(ci,CHURCH,ci)))
    # praça
    im,(ax,ay)=tree_img(6,0)
    objs.append((231,lambda im=im,ax=ax,ay=ay: img.paste(im,(153-ax,231-ay),im)))
    def benches():
        for bx,by in ((108,266),(148,266),(108,222)):
            d.rectangle([bx,by,bx+6,by+1],fill=(150,100,56)); d.point((bx,by+2),fill=(70,50,30)); d.point((bx+6,by+2),fill=(70,50,30))
        for fx,fy in ((102,215),(158,215),(102,271),(158,271)):
            for k,c in enumerate([(240,80,90),(250,220,70),(240,140,200),(80,170,80)]): d.point((fx+k%2,fy+k//2),fill=c)
    objs.append((268,benches))
    def well():
        cx,cy=117,226
        d.ellipse([cx-5,cy-4,cx+5,cy+4],fill=(130,130,138)); d.ellipse([cx-3,cy-2,cx+3,cy+2],fill=(40,70,140))
        d.line([cx-5,cy-6,cx+5,cy-6],fill=(110,70,36)); d.line([cx-5,cy-6,cx-5,cy],fill=(110,70,36)); d.line([cx+5,cy-6,cx+5,cy],fill=(110,70,36))
        d.point((cx,cy-4),fill=(120,120,130)); d.point((cx,cy-5),fill=(90,90,96))
    objs.append((231,well))
    for (lx,ly) in LAMPS:
        objs.append((ly,lambda lx=lx,ly=ly:(d.line([lx,ly-4,lx,ly],fill=(60,60,70)),d.point((lx,ly-5),fill=(220,220,200)),d.point((lx,ly+1),fill=(0,0,0)))))
    def sign():
        x,y=SIGN
        d.line([x+1,y,x+1,y+9],fill=(100,64,34)); d.line([x+12,y,x+12,y+9],fill=(100,64,34))
        d.rectangle([x,y,x+13,y+6],fill=(214,178,120)); d.rectangle([x,y,x+13,y+6],outline=(120,80,40))
        if NOME_VILA:
            for k in range(3): d.line([x+3,y+2+k*2-1,x+10,y+2+k*2-1],fill=(90,60,30)) if k==1 else None
    objs.append((SIGN[1]+9,sign))
    for k in range(6):
        bx=40+k*31; by=ROADA+18 if k%2 else ROADA-6
        cx=bx+math.sin(t*0.9+k)*6; cy=by+math.sin(t*1.3+k*2)*2; hop=int(t*4+k)%5==0
        objs.append((cy,lambda cx=cx,cy=cy-(1 if hop else 0):(d.rectangle([cx,cy,cx+1,cy+1],fill=(250,250,250)),d.point((cx,cy-1),fill=(220,40,40)),d.point((cx+2,cy),fill=(240,160,40)))))
    ph=((t+5)/14.0)%2; up=ph<1; f=smooth(ph if up else 2-ph); cy=468-f*350; cx=133
    def cart(cx=cx,cy=cy,up=up):
        hy=cy-7 if up else cy+8
        d.rectangle([cx-2,cy,cx+2,cy+6],fill=(150,100,56)); d.line([cx-2,cy,cx+2,cy],fill=(110,70,36))
        for px_,py_ in ((cx-3,cy+1),(cx+3,cy+1),(cx-3,cy+5),(cx+3,cy+5)): d.point((px_,py_),fill=(40,30,24))
        d.rectangle([cx-1,hy,cx+1,hy+4],fill=(120,74,40)); d.point((cx,hy if up else hy+4),fill=(70,40,24))
        d.rectangle([cx-1,cy+1,cx+1,cy+3],fill=(220,190,80))
    objs.append((cy+6,cart))
    for pp in people:
        st=person_state(pp,t)
        if st is None: continue
        x,y,mv,tool=st; fr=(int(t*6+pp['ph']*3)%2) if mv else 0
        im=pimg(pp,fr,tool)
        objs.append((y+5,lambda im=im,x=x,y=y: img.paste(im,(int(round(x))-2,int(round(y))-5),im)))
    # clientes do mercadinho
    door=(MER[0]+9.5,ROADB+3)
    for s in SHOPPERS:
        if t<s['t0']: continue
        pts=[(s['x0'],ROADB+6),(door[0],ROADB+6),door]
        L=plen(pts); per=7.0; ph_=((t-s['t0'])%per)/per
        if ph_<0.4: (x,y),_=path_pos(pts,L*ph_/0.4); bag=False; vis=True
        elif ph_<0.55: vis=False; bag=False; x,y=door
        else: (x,y),_=path_pos(pts,L*(1-(ph_-0.55)/0.45)); bag=True; vis=True
        if not vis: continue
        im=pimg(s,int(t*6+s['ph'])%2)
        def drw(im=im,x=x,y=y,bag=bag):
            img.paste(im,(int(x)-2,int(y)-5),im)
            if bag: d.point((int(x)+2,int(y)-1),fill=(250,240,200)); d.point((int(x)+2,int(y)),fill=(230,60,50))
        objs.append((y+5,drw))
    # carregadores de madeira p/ obra ativa
    if active and T['cresce'][0]<t<T['ruac'][1]:
        i,l=active; hx,hy=lot_xy(l); roady=l[1]+5
        pts=[(PILE[0]+12,PILE[1]+4),(131.5,PILE[1]+4),(131.5,roady),(hx+10,roady)]
        L=plen(pts)
        for k in range(2):
            per=(t+k*1.5)%3.0; go=per<1.5; f=per/1.5 if go else (3.0-per)/1.5
            (x,y),_=path_pos(pts,L*f)
            wk=WORKERS[4+k]; im=person_sprite(wk['skin'],wk['hair'],wk['shirt'],wk['pants'],int(t*6)%2,None,go)
            objs.append((y+5,lambda im=im,x=x,y=y: img.paste(im,(int(x)-2,int(y)-5),im)))
    objs.sort(key=lambda o:o[0])
    for _,fn in objs: fn()
    return np.asarray(img)

# ---------------- UI ----------------
NAVY=(24,22,52,235); WHITE=(255,255,255,255); YEL=(255,214,70,255); GREEN=(120,230,110,255); LBLUE=(180,200,255,255)
def box(d,x0,y0,x1,y1,fill=NAVY):
    d.rectangle([x0,y0,x1,y1],fill=fill); d.rectangle([x0,y0,x1,y1],outline=(255,255,255,255))
    d.rectangle([x0+2,y0+2,x1-2,y1-2],outline=(120,120,180,255))
def pop(t,t0,t1,fade=0.25):
    if t<t0 or t>t1: return 0
    return min(clamp((t-t0)/0.18),clamp((t1-t)/fade))
def w2s(x,y,cam):
    cx,cy,vw=cam; vh=vw*H/W; s=W/vw
    return (x-(cx-vw/2))*s,(y-(cy-vh/2))*s
def banner(d,lines,y,t,t0,t1,colors=None,scale=2):
    v=pop(t,t0,t1)
    if v<=0: return
    wmax=max(text_width(s,scale) for s in lines)+16; hh=len(lines)*(9*scale+4)+10
    yy=y+int((1-v)*12)
    box(d,135-wmax//2,yy,135+wmax//2,yy+hh)
    for k,s in enumerate(lines):
        draw_text(d,s,135,yy+7+k*(9*scale+4)+(2*scale),scale,colors[k] if colors else WHITE)
def nhouses(C): return sum(1 for i in range(NH) if house_p(i,C)>=1)
def draw_ui(t,cam):
    ui=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ui)
    C=count_at(t); hs=nhouses(C)
    y0=36+int((1-smooth(t/0.6))*-60)
    box(d,32,y0,238,y0+42)
    draw_text(d,"SEGUIDORES",86,y0+7,1,LBLUE); draw_text(d,"CASAS",192,y0+7,1,LBLUE)
    d.line([150,y0+6,150,y0+36],fill=(120,120,180,255))
    draw_text(d,str(C),86,y0+20,2,YEL if C!=count_at(t-0.12) else WHITE)
    draw_text(d,str(hs),192,y0+20,2,YEL if hs!=nhouses(count_at(t-0.4)) else WHITE)
    a,b=T['titulo']
    if pop(t,a,b)>0:
        draw_text(d,"A CIDADE DOS",135,130,2,WHITE); draw_text(d,"SEGUIDORES",135,152,3,YEL)
        draw_text(d,"EPISÓDIO 2",135,186,1,LBLUE)
    a,b=T['recap']
    banner(d,["ATÉ AGORA:"],120,t,a,b,[LBLUE],2)
    banner(d,["267 MORADORES","26 CASAS"],156,t,a+0.6,b,[YEL,WHITE],2)
    a,b=T['h27']
    if a+0.3<t<b:
        x,y=lot_xy(house_lots[26]); sx,sy=w2s(x+10,y,cam); bob=int(math.sin(t*5)*2)
        lab="7/10" if C<268 else ("8/10" if C<269 else ("9/10" if C<270 else "PRONTA!"))
        draw_text(d,lab,int(sx),int(sy)-30+bob,2,GREEN if C>=270 else YEL)
    a,b=T['cresce']
    banner(d,["NOVOS MORADORES","CHEGANDO..."],128,t,a+0.6,b-0.3,[WHITE,YEL])
    a,b=T['quase']
    if a<t<b:
        v=pop(t,a,b); draw_text(d,"QUASE...",135,200-int(v*6),2,WHITE)
    a,b=T['desbloq']
    v=pop(t,a,b)
    if v>0:
        sc=4 if int(t*4)%2 else 3
        draw_text(d,"300!",135,120,sc,GREEN)
        banner(d,["NOVO MARCO","DESBLOQUEADO"],170,t,a+0.5,b,[WHITE,YEL])
    a,b=T['obra']
    banner(d,["MERCADINHO"],118,t,a,a+2.2,[GREEN],3)
    if a+0.3<t<b-1.2:
        mp=mercado_p(t)
        lab="FUNDAÇÃO" if mp<0.2 else ("PAREDES" if mp<0.5 else ("TELHADO" if mp<0.85 else "TOLDO"))
        sx,sy=w2s(MER[0]+10,MER[1]-2,cam); draw_text(d,lab,int(sx),int(sy)-14,1,YEL)
    if b-1.2<t<b+0.2:
        sx,sy=w2s(MER[0]+10,MER[1]-2,cam); draw_text(d,"ABERTO!",int(sx),int(sy)-18,2,GREEN)
    a,b=T['clientes']
    banner(d,["+ MERCADINHO"],320,t,a+0.3,b,[WHITE])
    a,b=T['ruac']
    banner(d,["A VILA CHEGOU","NA RUA DE CIMA!"],330,t,43.3,b,[WHITE,YEL])
    a,b=T['resumo']
    banner(d,[str(C1)+" MORADORES"],120,t,47.7,b,[YEL])
    banner(d,[str(NH)+" CASAS"],156,t,49.6,b,[WHITE])
    banner(d,["1 MERCADINHO"],192,t,51.1,b,[GREEN])
    a,b=T['proximo']
    if a+0.8<t<b:
        ex,ey=lot_xy(ESCOLA[0]); sx,sy=w2s(ex+21,ey,cam)
        draw_text(d,"400",int(sx),int(sy)-24+int(math.sin(t*5)*2),3,YEL)
    banner(d,["PRÓXIMO MARCO:","400 SEGUIDORES"],116,t,a+0.2,57.2,[WHITE,YEL])
    banner(d,["UMA ESCOLA!"],116,t,57.3,b,[GREEN],3)
    a,b=T['nome']
    if a+0.8<t<b:
        sx,sy=w2s(SIGN[0]+7,SIGN[1],cam)
        draw_text(d,NOME_VILA.upper() if NOME_VILA else "???",int(sx),int(sy)-34+int(math.sin(t*6)*3),2 if NOME_VILA else 3,YEL)
    if NOME_VILA:
        banner(d,["BEM-VINDOS A",NOME_VILA.upper()+"!"],112,t,a+0.4,b,[WHITE,YEL])
    else:
        banner(d,["NOME DA VILA:","EM VOTAÇÃO!"],112,t,a+0.2,b,[WHITE,YEL])
        banner(d,["COMENTA E CURTE","NO VÍDEO 1!"],190,t,63.7,b,[GREEN,WHITE])
    a,b=T['cta']
    v=pop(t,a,b,0.01)
    if v>0:
        yy=150+int((1-v)*14)
        box(d,30,yy,240,yy+62,(200,40,50,240))
        draw_text(d,"SEGUE E VIRA",135,yy+10,2,WHITE); draw_text(d,"MORADOR!",135,yy+34,3,YEL)
    return ui

def render_frame(t):
    cx,cy,vw=cam_at(t); vh=vw*H/W
    cx=clamp(cx,vw/2,W-vw/2); cy=clamp(cy,vh/2,H-vh/2); cam=(cx,cy,vw)
    img=Image.fromarray(compose_world(t))
    fr=img.resize((OUTW,OUTH),Image.NEAREST,box=(cx-vw/2,cy-vh/2,cx+vw/2,cy+vh/2))
    ui=draw_ui(t,cam).resize((OUTW,OUTH),Image.NEAREST)
    fr=fr.convert('RGBA'); fr.alpha_composite(ui)
    return fr.convert('RGB')

if __name__=='__main__':
    out=sys.argv[1]
    for t in map(float,sys.argv[2:]):
        render_frame(t).save(f'{out}/frame_{t:05.1f}.png')
