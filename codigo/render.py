import numpy as np, math, random, sys, json, os
from PIL import Image, ImageDraw
from world import *
from scene import *
from font import draw_text, text_width
from vila16 import compose16, L2, SIGN, night_tint, show_overlay
from world16 import S

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
    w=text_width(txt,1)+12
    x=int(clamp(x,w/2+4,W-w/2-4)); y=int(y); yy=y+int((1-v)*6)
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
        draw_text(d,"EPISÓDIO 5",135,186,1,LBLUE)
    a,b=T['recap']
    banner(d,["ATÉ AGORA:"],120,t,3.5,b,[LBLUE],2)
    banner(d,[f"{C0} MORADORES",f"{C0//10} CASAS"],156,t,4.3,7.6,[YEL,WHITE],2)
    banner(d,["RUA NOVA ESPERANDO GENTE"],156,t,7.8,b,[GREEN],1)
    for n,t0 in ((47,12.2),(48,13.2),(49,14.0)):
        x,y=lot_center(house_lots[n-1],4); tag(d,f"CASA {n}",x,y,cam,t,t0,T['quase'][0]+1.2,GREEN)
    banner(d,["QUASE..."],140,t,16.1,17.6,[WHITE],3)
    if 17.6<=t<19.4:
        draw_text(d,"500!",135,150,6 if int(t*5)%2 else 5,YEL)
        banner(d,["NOVO MARCO","DESBLOQUEADO!"],200,t,17.7,19.4,[WHITE,GREEN])
    a,b=T['pref']
    banner(d,["PREFEITURA!"],120,t,19.4,b-0.1,[YEL],3)
    for k,(w_,t0) in enumerate((("FUNDAÇÃO",21.0),("COLUNAS",21.8),("RELÓGIO",22.6),("BANDEIRAS",24.1))):
        chip(d,w_,135,160+k*20,t,t0,b-0.1,GREEN if k==3 else YEL)
    if 25.0<=t<b-0.1: draw_text(d,"PRONTA!",135,250,4 if int(t*6)%2 else 3,GREEN)
    a,b=T['calc']
    banner(d,["RUAS","CALÇADAS!"],120,t,27.1,b,[WHITE,YEL],3)
    banner(d,["TERRA  >  PARALELEPÍPEDO"],200,t,27.6,b,[WHITE],1)
    a,b=T['cidadezinha']
    v=pop(t,31.4,b)
    if v>0:
        yy=150+int((1-v)*12)
        box(d,30,yy,240,yy+58,(40,120,70,240))
        draw_text(d,"AGORA É UMA",135,yy+9,1,WHITE); draw_text(d,"CIDADEZINHA!",135,yy+26,3,YEL)
        for k in range(26):
            q=((t-31.4)*0.9+k*0.13)%1.0
            cx_=(k*37)%270; cy_=int(q*480)
            d.rectangle([cx_,cy_,cx_+2,cy_+3],fill=[(255,214,70),(120,230,110),(230,60,60),(180,200,255)][k%4]+(255,))
    a,b=T['cresce2']
    banner(d,["+ 7 CASAS NA RUA D"],120,t,34.7,b,[GREEN])
    x,y=lot_center(house_lots[57],4); tag(d,"CASA 58: EM OBRA",x,y,cam,t,36.4,b,YEL)
    a,b=T['prefeito']
    banner(d,["EM BREVE:","PREFEITO!"],120,t,40.6,b,[LBLUE,YEL],3)
    ex,ey=lot(*PREFEITURA[0])
    if 40.6<t<b:
        sx,sy=w2s(ex+22,ey+2,cam); draw_text(d,"?",int(sx),int(sy)-26+int(math.sin(t*5)*2),4,YEL)
    chip(d,"E O NOME DA CIDADE...",135,206,t,42.96,b,WHITE)
    if 42.96<t<b:
        sx,sy=w2s(SIGN[0]+7,SIGN[1]+3,cam)
        if int(t*3)%2: draw_text(d,"???",int(sx),int(sy)-4,2,(120,70,30,255),outline=None)
    banner(d,["FICA ATENTO!"],300,t,45.0,b,[GREEN],3)
    if 46.3<=t<55.7:
        h=interp(t,[(46.3,18.5),(47.9,19.5),(55.7,22.0)])
        box(d,80,90,190,112); d.ellipse([86,95,98,107],fill=(255,214,70,255) if h<19 else (220,226,255,255))
        draw_text(d,f"DOMINGO {int(h):02d}:{int((h%1)*60)//10*10:02d}",144,98,1,WHITE)
    banner(d,["DOMINGO!"],320,t,46.4,47.4,[YEL],3)
    banner(d,["DIA DE SHOW","NA PRAÇA!"],310,t,47.45,49.6,[WHITE,YEL],3)
    for k,(w_,t0) in enumerate((("PALCO MONTADO",49.7),("BANDA TOCANDO",50.5),("LUZ COLORIDA",51.6))):
        chip(d,w_,135,380+k*20,t,t0,52.6,[YEL,GREEN,LBLUE][k])
    banner(d,["A CIDADE INTEIRA","DANÇANDO!"],370,t,52.7,55.5,[WHITE,YEL],2)
    a,b=T['resumo']
    banner(d,["RESULTADO:"],84,t,55.9,b,[LBLUE],1)
    banner(d,[f"{C1} MORADORES"],120,t,56.7,b,[YEL])
    banner(d,[f"{NH} CASAS"],156,t,58.75,b,[WHITE])
    banner(d,["PREFEITURA"],192,t,60.15,b,[GREEN])
    banner(d,["RUAS CALÇADAS"],228,t,60.85,b,[GREEN])
    a,b=T['proximo']
    banner(d,[f"FALTAM SÓ {600-C1}"],130,t,62.3,b,[WHITE],3)
    banner(d,["SEGUNDO MERCADINHO"],180,t,64.5,b,[YEL])
    banner(d,["+ POSTO DE SAÚDE"],216,t,65.55,b,[GREEN])
    banner(d,["600"],270,t,62.9,b,[YEL],4)
    a,b=T['mapa']
    if 67.0<=t<b:
        free=[l for i,l in enumerate(house_lots) if house_p(i,C1)<=0]
        on=int(t*4)%2==0
        for l in free:
            r=lot_rect(l,cam)
            d.rectangle(r,outline=YEL if on else WHITE)
        chip(d,f"SÓ {len(free)} LOTES LIVRES",135,330,t,67.0,b,YEL)
    v=pop(t,68.9,b)
    if v>0:
        yy=150+int((1-v)*12)
        box(d,30,yy,240,yy+48,(200,40,50,240))
        draw_text(d,"FIM DO MAPA!",135,yy+8,2,WHITE); draw_text(d,"A CIDADE VAI TER QUE CRESCER",135,yy+31,1,YEL)
        if int(t*3)%2: d.polygon([(125,448),(145,448),(135,462)],fill=(255,214,70,255))
    a,b=T['cta']
    v=pop(t,a,b,0.01)
    if v>0:
        yy=150+int((1-v)*14)
        box(d,24,yy,246,yy+62,(200,40,50,240))
        draw_text(d,"LINK NA BIO!",135,yy+10,2,WHITE); draw_text(d,"ESCOLHE O TEU MORADOR",135,yy+38,1,YEL)
    banner(d,["O PRIMEIRO PREFEITO","PODE SER VOCÊ?"],250,t,73.9,b,[WHITE,YEL],2)
    return ui

# nomes dos moradores do site na plateia (alguns por vez, revezando)
def draw_names(t,cam):
    if not (50.6<=t<SHOWWIN[1]): return None
    lay=Image.new('RGBA',(W*2,H*2),(0,0,0,0)); d=ImageDraw.Draw(lay)
    k=0
    for c in PLATEIA:
        if c['id'] not in REG: continue
        k+=1
        if ((t-49.0+k*0.53)%4.2)>1.8: continue
        st=plateia_state(c,t)
        if st is None or st[2]: continue
        sx,sy=w2s(st[0],st[1]-st[3],cam)
        if not (-20<sx<W+20 and -20<sy<H+20): continue
        nm=nome_tela(REG[c['id']]['nome'])
        if not nm: continue
        X=int(sx*2); Y=int(sy*2-2*8*W/cam[2])-12
        tw=text_width(nm,1)+6
        d.rectangle([X-tw//2,Y-2,X+tw//2,Y+8],fill=(24,22,52,200))
        draw_text(d,nm,X,Y,1,YEL)
    return lay.resize((OUTW,OUTH),Image.NEAREST)

def crop16(t,cam):
    cx,cy,vw=cam; vh=vw*H/W
    k=night_f(t)
    a=compose16(t,k,(cx-vw/2,cy-vh/2,cx+vw/2,cy+vh/2))
    a=night_tint(a,k); a=show_overlay(a,t)
    img=Image.fromarray(a)
    return img.resize((OUTW,OUTH),Image.NEAREST,box=((cx-vw/2)*S,(cy-vh/2)*S,(cx+vw/2)*S,(cy+vh/2)*S))

def flash(fr,k):
    a=np.array(fr).astype(np.float32); a=a+(255-a)*k
    return Image.fromarray(a.astype(np.uint8))

def render_frame(t):
    cx,cy,vw=cam_at(t); vh=vw*H/W
    cx=clamp(cx,vw/2,W-vw/2); cy=clamp(cy,vh/2,H-vh/2)
    if 68.9<=t<69.6: cy=clamp(cy+math.sin(t*60)*2.5*(1-(t-68.9)/0.7),vh/2,H-vh/2)    # "esbarra" no fim do mapa
    cam=(cx,cy,vw)
    fr=crop16(t,cam)
    if 17.6<=t<17.9: fr=flash(fr,(1-(t-17.6)/0.3)*0.5)
    if 25.0<=t<25.3: fr=flash(fr,(1-(t-25.0)/0.3)*0.4)
    ui=draw_ui(t,cam).resize((OUTW,OUTH),Image.NEAREST)
    fr=fr.convert('RGBA'); fr.alpha_composite(ui)
    nm=draw_names(t,cam)
    if nm is not None: fr.alpha_composite(nm)
    return fr.convert('RGB')

if __name__=='__main__':
    out=sys.argv[1]
    for t in map(float,sys.argv[2:]):
        render_frame(t).save(f'{out}/frame_{t:05.1f}.png')
