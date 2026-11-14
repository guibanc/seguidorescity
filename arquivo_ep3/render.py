import numpy as np, math, random, sys, json, os
from PIL import Image, ImageDraw
from world import *
from scene import *
from font import draw_text, text_width
from vila8 import compose8
from vila16 import compose16, L2
from world16 import S

FPS=30
OUTW,OUTH=1080,1920

# ---------------- UI (mesma identidade dos eps. 1 e 2) ----------------
NAVY=(24,22,52,235); WHITE=(255,255,255,255); YEL=(255,214,70,255); GREEN=(120,230,110,255); LBLUE=(180,200,255,255); PINK=(255,140,190,255)
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

def clock_txt(h):
    hh=int(h)%24; mm=int((h-int(h))*60)//10*10
    return f"{hh:02d}:{mm:02d}"
def destaque_label(t):
    if t<57.3: return "ACORDANDO..."
    if t<58.9: return "SAINDO DE CASA"
    if t<59.7: return "NO MERCADINHO"
    if t<61.2: return "NA PRAÇA"
    if t<62.8: return "VOLTANDO PRA CASA"
    return "LUZ ACESA. BOA NOITE!"
def chip(d,txt,x,y,t,t0,t1,col=YEL):
    v=pop(t,t0,t1)
    if v<=0: return
    w=text_width(txt,1)+12; yy=y+int((1-v)*6)
    box(d,x-w//2,yy,x+w//2,yy+15,(24,22,52,225)); draw_text(d,txt,x,yy+4,1,col)

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
        draw_text(d,"EPISÓDIO 3",135,186,1,LBLUE)
    a,b=T['recap']
    banner(d,["ATÉ AGORA:"],120,t,a,b,[LBLUE],2)
    banner(d,[f"{C0} MORADORES",f"{C0//10} CASAS"],156,t,a+0.6,b,[YEL,WHITE],2)
    a,b=T['cresce8']
    banner(d,["NOVOS MORADORES","CHEGANDO..."],330,t,a+0.6,b-0.3,[WHITE,YEL])
    a,b=T['aviso']
    banner(d,["MAS HOJE..."],140,t,14.05,15.1,[WHITE],3)
    banner(d,["A VILA VAI","MUDAR!"],140,t,15.1,b,[WHITE,YEL],3)
    a,b=T['evolucao']
    banner(d,["A VILA","EVOLUIU!"],150,t,18.4,b,[WHITE,YEL],3)
    banner(d,["8 BITS"],230,t,20.1,22.6,[LBLUE],2)
    if 22.6<t<b:
        sc=5 if int(t*4)%2 else 4
        draw_text(d,"16 BITS!",135,236,sc,GREEN)
    a,b=T['compara']
    if a+0.6<t<b:
        sx=slider_x(t)
        sxu=int(sx*W)
        box(d,max(4,sxu-74),150,max(4,sxu-74)+64,170,(24,22,52,210)); draw_text(d,"8 BITS",max(4,sxu-74)+32,156,1,WHITE)
        box(d,min(W-68,sxu+10),150,min(W-68,sxu+10)+64,170,(24,22,52,210)); draw_text(d,"16 BITS",min(W-68,sxu+10)+32,156,1,GREEN)
    chip(d,"TELHADO DE TELHA",135,300,t,25.45,b)
    chip(d,"JANELA COM FLOREIRA",135,320,t,26.7,b)
    chip(d,"CHAMINÉ DE TIJOLO",135,340,t,28.45,b)
    chip(d,"MERCADINHO DETALHADO",135,360,t,30.1,b,GREEN)
    a,b=T['detalhe']
    banner(d,["CADA MORADOR","AGORA É ÚNICO!"],300,t,33.4,b,[WHITE,YEL])
    for k,(w,t0) in enumerate((("CABELO",35.7),("ROUPA",36.6),("CHAPÉU",37.2),("ÓCULOS",38.4))):
        chip(d,w,40+k*63,360,t,t0,b)
    banner(d,["NÃO TEM DOIS IGUAIS!"],392,t,39.4,b,[GREEN])
    a,b=T['cresce16']
    banner(d,["+ 3 CASAS NOVAS"],330,t,43.45,b,[GREEN])
    a,b=T['site']
    v=pop(t,47.3,b)
    if v>0:
        yy=112+int((1-v)*14)
        box(d,26,yy,244,yy+40,(200,40,50,240))
        draw_text(d,"A VILA TEM SITE!",135,yy+7,2,WHITE)
        if t>49.1: draw_text(d,"LINK NA BIO",135,yy+27,1,YEL)
        steps=[("1","ESCOLHA UM MORADOR"),("2","COLOQUE SEU NOME"),("3","ACOMPANHE A VIDA DELE")]
        for k,(n,s) in enumerate(steps):
            vv=pop(t,(50.4,52.2,53.6)[k],b)
            if vv<=0: continue
            by=yy+56+k*34+int((1-vv)*10)
            box(d,30,by,240,by+26)
            d.rectangle([36,by+5,52,by+21],fill=(255,214,70,255)); draw_text(d,n,44,by+8,1,(24,22,52,255),outline=None)
            draw_text(d,s,148,by+10,1,WHITE)
    # morador em destaque
    st=destaque_state(t)
    if st:
        x,y,acao,_=st
        sx,sy=w2s(x,y,cam)
        if acao!='entra' or True:
            lab="SEU NOME AQUI"
            bob=int(math.sin(t*5)*2)
            tw=text_width(lab,1)+10; tx0=int(sx)-tw//2; ty0=int(sy)-46+bob
            if acao in ('entra','casa'): ty0=int(sy)-58+bob
            box(d,tx0,ty0,tx0+tw,ty0+14,(200,40,50,235)); draw_text(d,lab,int(sx),ty0+4,1,WHITE)
            d.polygon([(int(sx)-3,ty0+15),(int(sx)+3,ty0+15),(int(sx),ty0+19)],fill=(255,255,255,255))
        h=hour_at(t)
        if h is not None:
            box(d,92,90,178,112)
            sun = 6<=h<18.6
            if sun:
                d.ellipse([98,95,110,107],fill=(255,214,70,255))
            else:
                d.ellipse([98,95,110,107],fill=(230,230,250,255)); d.ellipse([102,93,113,104],fill=(24,22,52,255))
            draw_text(d,clock_txt(h),145,97,2,WHITE)
            lb=destaque_label(t)
            box(d,135-text_width(lb,1)//2-8,118,135+text_width(lb,1)//2+8,134,(24,22,52,220)); draw_text(d,lb,135,123,1,YEL)
    a,b=T['resumo']
    banner(d,["RESULTADO:"],84,t,63.8,b,[LBLUE],1)
    banner(d,[f"{C1} MORADORES"],120,t,64.85,b,[YEL])
    banner(d,[f"{NH} CASAS"],156,t,66.95,b,[WHITE])
    banner(d,["VILA EM 16 BITS"],192,t,68.3,b,[GREEN])
    a,b=T['proximo']
    if a+0.8<t<b:
        ex,ey=lot(*ESCOLA[0]); sx,sy=w2s(ex+21,ey,cam)
        draw_text(d,"400",int(sx),int(sy)-24+int(math.sin(t*5)*2),3,YEL)
    banner(d,["FALTAM SÓ 30"],300,t,70.25,b,[WHITE])
    banner(d,["PRA ESCOLA!"],336,t,72.3,b,[GREEN])
    a,b=T['cta']
    v=pop(t,a,b,0.01)
    if v>0:
        yy=150+int((1-v)*14)
        box(d,24,yy,246,yy+62,(200,40,50,240))
        draw_text(d,"LINK NA BIO!",135,yy+10,2,WHITE); draw_text(d,"VIRA MORADOR" if t>75.6 else "ESCOLHE O TEU",135,yy+34,3 if t>75.6 else 2,YEL)
    return ui

# ---------------- transições ----------------
def slider_x(t):
    a,b=T['compara']; x=(t-a-0.6)/(b-a-0.6)
    return 0.5+0.32*math.sin(x*math.pi*2.2)

def crop8(t,cam):
    cx,cy,vw=cam; vh=vw*H/W
    img=Image.fromarray(compose8(t))
    return img.resize((OUTW,OUTH),Image.NEAREST,box=(cx-vw/2,cy-vh/2,cx+vw/2,cy+vh/2))
def crop16(t,cam):
    cx,cy,vw=cam; vh=vw*H/W
    img=Image.fromarray(compose16(t,hour_at(t),(cx-vw/2,cy-vh/2,cx+vw/2,cy+vh/2)))
    return img.resize((OUTW,OUTH),Image.NEAREST,box=((cx-vw/2)*S,(cy-vh/2)*S,(cx+vw/2)*S,(cy+vh/2)*S))

def glitch(fr,t,amt):
    a=np.array(fr); r=random.Random(int(t*30))
    for _ in range(int(3+amt*10)):
        y0=r.randrange(0,OUTH-40); hh=r.randrange(8,60); sh_=int(r.uniform(-40,40)*amt)
        a[y0:y0+hh]=np.roll(a[y0:y0+hh],sh_,axis=1)
    if amt>0.3:
        a[:,:,0]=np.roll(a[:,:,0],int(6*amt),axis=1); a[:,:,2]=np.roll(a[:,:,2],-int(6*amt),axis=1)
    return Image.fromarray(a)

def render_frame(t):
    cx,cy,vw=cam_at(t); vh=vw*H/W
    cx=clamp(cx,vw/2,W-vw/2); cy=clamp(cy,vh/2,H-vh/2); cam=(cx,cy,vw)
    s0,s1=T_SWEEP
    ca,cb=T['compara']
    if ca+0.6<t<cb:
        f8=crop8(t,cam); f16=crop16(t,cam)
        sx=int(slider_x(t)*OUTW)
        fr=f16.copy(); fr.paste(f8.crop((0,0,sx,OUTH)),(0,0))
        d=ImageDraw.Draw(fr); d.rectangle([sx-3,0,sx+3,OUTH],fill=(255,255,255))
        d.ellipse([sx-26,OUTH//2-26,sx+26,OUTH//2+26],fill=(255,255,255)); d.ellipse([sx-20,OUTH//2-20,sx+20,OUTH//2+20],fill=(24,22,52))
        d.polygon([(sx-14,OUTH//2),(sx-5,OUTH//2-8),(sx-5,OUTH//2+8)],fill=(255,255,255)); d.polygon([(sx+14,OUTH//2),(sx+5,OUTH//2-8),(sx+5,OUTH//2+8)],fill=(255,255,255))
    elif t<s0:
        fr=crop8(t,cam)
        ga=T_SWEEP[0]-1.0
        if t>ga: fr=glitch(fr,t,(t-ga)/1.0)
    elif t>=s1:
        fr=crop16(t,cam)
    else:
        f=smooth((t-s0)/(s1-s0)); ys=int(f*OUTH)
        f8=crop8(t,cam); f16=crop16(t,cam)
        fr=f8.copy(); fr.paste(f16.crop((0,0,OUTW,ys)),(0,0))
        d=ImageDraw.Draw(fr)
        for k,(c,w) in enumerate([((255,255,255),6),((160,240,255),14),((90,180,255),24)]):
            pass
        d.rectangle([0,ys-4,OUTW,ys+4],fill=(255,255,255))
        d.rectangle([0,ys-12,OUTW,ys-5],fill=(170,240,255)); d.rectangle([0,ys+5,OUTW,ys+10],fill=(120,200,255))
        r=random.Random(int(t*60))
        for _ in range(40):
            x=r.randrange(0,OUTW); y=ys+r.randrange(-60,40); q=r.choice([4,8,12])
            d.rectangle([x,y,x+q,y+q],fill=r.choice([(255,255,255),(255,240,140),(160,240,255)]))
    # flash branco no fim da varredura
    if s1<=t<s1+0.35:
        a=np.array(fr).astype(np.float32); k=1-(t-s1)/0.35
        a=a+(255-a)*k*0.7; fr=Image.fromarray(a.astype(np.uint8))
    ui=draw_ui(t,cam).resize((OUTW,OUTH),Image.NEAREST)
    fr=fr.convert('RGBA'); fr.alpha_composite(ui)
    return fr.convert('RGB')

if __name__=='__main__':
    out=sys.argv[1]
    for t in map(float,sys.argv[2:]):
        render_frame(t).save(f'{out}/frame_{t:05.1f}.png')
