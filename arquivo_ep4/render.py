import numpy as np, math, random, sys, json, os
from PIL import Image, ImageDraw
from world import *
from scene import *
from font import draw_text, text_width
from vila16 import compose16, L2, PILE, SIGN, VENDEDOR
from world16 import S
from fp import render_fp

FPS=30
OUTW,OUTH=1080,1920

# ---------------- UI (mesma identidade dos eps. anteriores) ----------------
NAVY=(24,22,52,235); WHITE=(255,255,255,255); YEL=(255,214,70,255); GREEN=(120,230,110,255); LBLUE=(180,200,255,255); RED=(230,60,60,255)
def box(d,x0,y0,x1,y1,fill=NAVY):
    d.rectangle([x0,y0,x1,y1],fill=fill); d.rectangle([x0,y0,x1,y1],outline=(255,255,255,255))
    d.rectangle([x0+2,y0+2,x1-2,y1-2],outline=(120,120,180,255))
def pop(t,t0,t1,fade=0.25):
    if t<t0 or t>t1: return 0
    return min(clamp((t-t0)/0.18),clamp((t1-t)/fade))
def w2s(x,y,cam):
    cx,cy,vw=cam; vh=vw*H/W; s=W/vw
    return (x-(cx-vw/2))*s,(y-(cy-vh/2))*s
def banner(d,lines,y,t,t0,t1,colors=None,scale=2,fill=NAVY):
    v=pop(t,t0,t1)
    if v<=0: return
    wmax=max(text_width(s,scale) for s in lines)+16; hh=len(lines)*(9*scale+4)+10
    yy=y+int((1-v)*12)
    box(d,135-wmax//2,yy,135+wmax//2,yy+hh,fill)
    for k,s in enumerate(lines):
        draw_text(d,s,135,yy+7+k*(9*scale+4)+(2*scale),scale,colors[k] if colors else WHITE)
def nhouses(C): return sum(1 for i in range(NH) if house_p(i,C)>=1)
def chip(d,txt,x,y,t,t0,t1,col=YEL,fill=(24,22,52,225)):
    v=pop(t,t0,t1)
    if v<=0: return
    x=int(x); y=int(y)
    w=text_width(txt,1)+12; yy=y+int((1-v)*6)
    box(d,x-w//2,yy,x+w//2,yy+15,fill); draw_text(d,txt,x,yy+4,1,col)
def tag(d,txt,wx,wy,cam,t,t0,t1,col=YEL,dy=-30,fill=(24,22,52,225)):
    sx,sy=w2s(wx,wy,cam)
    bob=int(math.sin(t*5)*2)
    chip(d,txt,sx,sy+dy+bob,t,t0,t1,col,fill)
    v=pop(t,t0,t1)
    if v>0: d.polygon([(int(sx)-3,int(sy)+dy+bob+16),(int(sx)+3,int(sy)+dy+bob+16),(int(sx),int(sy)+dy+bob+20)],fill=(255,255,255,255))
def lot_rect(l,cam,w=21,h=25):
    x,y=lot(*l); a=w2s(x,y,cam); b=w2s(x+w,y+h,cam); return [int(a[0]),int(a[1]),int(b[0]),int(b[1])]
def clock(d,dia,txt,lbl=None):
    box(d,80,90,190,112)
    d.ellipse([86,95,98,107],fill=(255,214,70,255))
    draw_text(d,(dia+" " if dia else "")+txt,144,97,2 if not dia else 1,WHITE)
    if lbl:
        box(d,135-text_width(lbl,1)//2-8,118,135+text_width(lbl,1)//2+8,134,(24,22,52,220)); draw_text(d,lbl,135,123,1,YEL)

def draw_ui(t,cam,fpmode=False):
    ui=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ui)
    C=count_at(t); hs=nhouses(C)
    y0=36+int((1-smooth(t/0.6))*-60)
    box(d,32,y0,238,y0+42)
    draw_text(d,"SEGUIDORES",86,y0+7,1,LBLUE); draw_text(d,"CASAS",192,y0+7,1,LBLUE)
    d.line([150,y0+6,150,y0+36],fill=(120,120,180,255))
    draw_text(d,str(C),86,y0+20,2,YEL if C!=count_at(t-0.12) else WHITE)
    draw_text(d,str(hs),192,y0+20,2,YEL if hs!=nhouses(count_at(t-0.4)) else WHITE)
    # título
    a,b=T['titulo']
    if pop(t,a,b)>0:
        draw_text(d,"A CIDADE DOS",135,130,2,WHITE); draw_text(d,"SEGUIDORES",135,152,3,YEL)
        draw_text(d,"EPISÓDIO 4",135,186,1,LBLUE)
    a,b=T['recap']
    banner(d,["ATÉ AGORA:"],120,t,3.7,b,[LBLUE],2)
    banner(d,[f"{C0} MORADORES",f"{C0//10} CASAS"],156,t,4.9,b,[YEL,WHITE],2)
    # casas 38-40
    for n,t0 in ((38,11.2),(39,12.3),(40,13.6)):
        x,y=lot_center(house_lots[n-1],4); tag(d,f"CASA {n}",x,y,cam,t,t0,T['quase'][0]+1.6,GREEN if n<40 else YEL)
    banner(d,["QUASE..."],300,t,15.0,17.4,[WHITE],3)
    if 17.45<=t<19.3:
        sc=6 if int(t*5)%2 else 5
        draw_text(d,"400!",135,250,sc,YEL)
        banner(d,["NOVO MARCO","DESBLOQUEADO!"],320,t,17.6,19.3,[WHITE,GREEN])
    # escola
    a,b=T['escola']
    banner(d,["A ESCOLA!"],130,t,19.3,b-0.1,[YEL],3)
    for k,(w_,t0) in enumerate((("FUNDAÇÃO",20.3),("PAREDE",21.25),("TELHADO",22.1),("SINO",23.4),("BANDEIRA",24.4))):
        chip(d,w_,135,330+k*20,t,t0,b-0.1,GREEN if k==4 else YEL)
    if 24.9<=t<b-0.1:
        draw_text(d,"ABERTA!",135,240,4 if int(t*6)%2 else 3,GREEN)
    # primeira pessoa
    if fpmode:
        clock(d,"SEG","07:30","INDO PRA ESCOLA")
        for t0 in (27.0,27.6):
            if t0<=t<t0+0.5:
                f=(t-t0)/0.5
                draw_text(d,"DING!",190-int(f*6),170-int(f*14),3,YEL)
    # casas 41-46
    banner(d,["+ 6 CASAS NOVAS"],330,t,32.3,T['cresce2'][1],[GREEN])
    # mapa lotado
    a,b=T['lotado']
    x,y=lot_center(house_lots[45],4); tag(d,"CASA 46",x,y,cam,t,36.25,37.6,GREEN)
    if 37.5<=t<b:
        allL=house_lots[:NH]+[VENDA,MERCADO]+ESCOLA
        n=int(clamp((t-37.5)/0.75)*len(allL))
        blink=t>=38.3 and int(t*6)%2==0
        for k,l in enumerate(allL[:n]):
            r=lot_rect(l,cam)
            d.rectangle(r,outline=RED if t>=38.3 else GREEN)
            if blink: d.rectangle([r[0]+1,r[1]+1,r[2]-1,r[3]-1],outline=RED)
    v=pop(t,38.3,b)
    if v>0:
        yy=300+int((1-v)*12)
        box(d,40,yy,230,yy+48,(200,40,50,240))
        draw_text(d,"MAPA LOTADO!",135,yy+8,2,WHITE); draw_text(d,"LOTES LIVRES: 0",135,yy+31,1,YEL)
    # rua nova
    a,b=T['ruanova']
    tag(d,"A PILHA DO EP. 1",PILE[0]+12,PILE[1]-6,cam,t,41.6,44.1,YEL)
    banner(d,["RUA NOVA!"],140,t,44.3,b,[GREEN],3)
    tag(d,"RUA D",60,ROADD+5,cam,t,44.9,b,WHITE,-22)
    # casa 47
    x,y=lot_center(house_lots[46],4); tag(d,"CASA 47",x,y,cam,t,T['casa47'][0]+0.4,T['casa47'][1],YEL)
    banner(d,["COMEÇA EM 465","PRONTA EM 470"],320,t,46.1,T['casa47'][1],[WHITE,GREEN])
    # sábado
    if 48.1<=t<58.9:
        h=interp(t,[(48.1,9.0),(58.9,10.5)])
        clock(d,"SÁBADO",f"{int(h):02d}:{int((h%1)*60)//10*10:02d}")
    banner(d,["SÁBADO!"],320,t,48.2,49.3,[YEL],3)
    banner(d,["DIA DE QUÊ?"],320,t,49.4,51.1,[WHITE],3)
    banner(d,["DIA DE","MERCADINHO!"],310,t,51.15,53.6,[WHITE,GREEN],3)
    chip(d,"FILA NO CAIXA",135,390,t,54.1,58.7,YEL)
    chip(d,"SACOLA CHEIA",135,410,t,55.0,58.7,GREEN)
    tag(d,"PSIU! PROMOÇÃO!",VENDEDOR[0],VENDEDOR[1]-8,cam,t,56.4,58.7,WHITE,-30,(200,40,50,235))
    # resumo
    a,b=T['resumo']
    banner(d,["RESULTADO:"],84,t,59.1,b,[LBLUE],1)
    banner(d,[f"{C1} MORADORES"],120,t,60.1,b,[YEL])
    banner(d,[f"{NH} CASAS"],156,t,61.9,b,[WHITE])
    banner(d,["1 ESCOLA"],192,t,63.1,b,[GREEN])
    banner(d,["1 RUA NOVA"],228,t,63.8,b,[GREEN])
    # próximo
    a,b=T['proximo']
    if a+0.8<t<b:
        ex,ey=lot(*PREFEITURA[0]); sx,sy=w2s(ex+22,ey+4,cam)
        draw_text(d,"500",int(sx),int(sy)-20+int(math.sin(t*5)*2),3,YEL)
    banner(d,["FALTAM SÓ 40"],120,t,65.4,b,[WHITE])
    banner(d,["PREFEITURA"],156,t,68.4,b,[YEL])
    banner(d,["+ RUAS CALÇADAS"],188,t,69.1,b,[GREEN])
    # nome
    a,b=T['nome']
    if a+0.5<t<b:
        sx,sy=w2s(SIGN[0]+7,SIGN[1]+3,cam)
        if int(t*3)%2: draw_text(d,"???",int(sx),int(sy)-4,2,(120,70,30,255),outline=None)
    banner(d,["QUAL O NOME","DA VILA?"],130,t,72.4,b,[WHITE,YEL])
    banner(d,["COMENTA AÍ!"],300,t,73.7,b,[GREEN],3)
    # cta
    a,b=T['cta']
    v=pop(t,a,b,0.01)
    if v>0:
        yy=150+int((1-v)*14)
        box(d,24,yy,246,yy+62,(200,40,50,240))
        draw_text(d,"LINK NA BIO!",135,yy+10,2,WHITE); draw_text(d,"VIRA MORADOR" if t>77.5 else "ESCOLHE O TEU",135,yy+34,3 if t>77.5 else 2,YEL)
    return ui

# nomes dos moradores registrados (letra menor: camada 540x960)
def draw_names(t,cam):
    if not (SAT[0]<=t<SAT[1]): return None
    lay=Image.new('RGBA',(W*2,H*2),(0,0,0,0)); d=ImageDraw.Draw(lay)
    k=0
    for c in CROWD:
        if c['id'] not in REG: continue
        st=crowd_state(c,t)
        if st is None: continue
        sx,sy=w2s(st[0],st[1],cam)
        if not (-20<sx<W+20 and -20<sy<H+20): continue
        nm=REG[c['id']]['nome'].upper()
        k+=1
        X=int(sx*2); Y=int(sy*2-2*8*W/cam[2])-12-(k%2)*12
        tw=text_width(nm,1)+6
        d.rectangle([X-tw//2,Y-2,X+tw//2,Y+8],fill=(24,22,52,200))
        draw_text(d,nm,X,Y,1,YEL)
    return lay.resize((OUTW,OUTH),Image.NEAREST)

def crop16(t,cam):
    cx,cy,vw=cam; vh=vw*H/W
    img=Image.fromarray(compose16(t,None,(cx-vw/2,cy-vh/2,cx+vw/2,cy+vh/2)))
    return img.resize((OUTW,OUTH),Image.NEAREST,box=((cx-vw/2)*S,(cy-vh/2)*S,(cx+vw/2)*S,(cy+vh/2)*S))

def flash(fr,k):
    a=np.array(fr).astype(np.float32); a=a+(255-a)*k
    return Image.fromarray(a.astype(np.uint8))

def render_frame(t):
    cx,cy,vw=cam_at(t); vh=vw*H/W
    cx=clamp(cx,vw/2,W-vw/2); cy=clamp(cy,vh/2,H-vh/2); cam=(cx,cy,vw)
    fa,fb=T['fp']
    fpm=fa<=t<fb
    fr=render_fp(t) if fpm else crop16(t,cam)
    # flashes nas entradas/saídas da primeira pessoa
    for t0 in (fa,fb):
        if t0-0.15<=t<t0+0.3:
            k=1-abs(t-t0)/(0.15 if t<t0 else 0.3); fr=flash(fr,clamp(k)*0.9)
    if 17.45<=t<17.75: fr=flash(fr,(1-(t-17.45)/0.3)*0.5)
    ui=draw_ui(t,cam,fpm).resize((OUTW,OUTH),Image.NEAREST)
    fr=fr.convert('RGBA'); fr.alpha_composite(ui)
    nm=draw_names(t,cam)
    if nm is not None: fr.alpha_composite(nm)
    return fr.convert('RGB')

if __name__=='__main__':
    out=sys.argv[1]
    for t in map(float,sys.argv[2:]):
        render_frame(t).save(f'{out}/frame_{t:05.1f}.png')
