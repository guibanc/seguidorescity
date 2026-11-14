# vila em 8 bits (como nos eps. 1 e 2) — usada no começo do ep. 3, antes da evolução
import numpy as np, math, random, json, os
from PIL import Image, ImageDraw
from world import *
from scene import *
_est=json.load(open(os.path.join(os.path.dirname(__file__),'..','estado_vila.json')))
NOME_VILA=_est.get('nome_vila')
# chão fixo (ruas e praça já prontas desde o ep. 1)
BASE,RIVER=make_base()
for lay,order,_,_ in build_layers():
    m=lay[:,:,3]>0; BASE[m]=lay[:,:,:3][m]
ry,rx=np.nonzero(RIVER)
LAMPS=[(x,y) for y in range(124,460,34) for x in (123,140) if not (205<y<285) and not (ROADA-8<y<ROADA+16) and not (ROADC-8<y<ROADC+16)]
PILE=(86,412); SIGN=(142,442); CHURCH=(115,61)
def lot_xy(l): return lot(*l)
MER=lot_xy(MERCADO)

def compose8(t):
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
    mi=mercado_sprite(1)
    objs.append((y+21,lambda mi=mi,x=x,y=y: img.paste(mi,(x,y),mi)))
    if 0<mp<1:
        for k,wx in enumerate((x-3,x+18)):
            wk=WORKERS[k+2]; fr=int(t*7+k)%2
            pim=person_sprite(wk['skin'],wk['hair'],wk['shirt'],wk['pants'],0,'up' if fr else 'down')
            objs.append((y+22,lambda pim=pim,wx=wx,y=y: img.paste(pim,(wx,y+15),pim)))
        if int(t*8)%2: objs.append((y+30,lambda x=x,y=y,t=t:[d.point((x+3+((t*37+k*29)%14),y+12+((t*23+k*5)%8)),fill=(220,200,160)) for k in range(4)]))
    tm=-99
    if False:
        f=(t-tm)/0.9
        objs.append((999,lambda f=f:[d.point((x+10+math.cos(k*0.524)*(5+f*18),y+10+math.sin(k*0.524)*(5+f*18)),fill=[(255,240,120),(120,230,110),(250,250,250)][k%3]) for k in range(12)]))
    # escola: estacas no lote reservado a partir do "próximo marco"
    if True:
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
    if active:
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

