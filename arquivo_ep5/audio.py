import numpy as np, wave, math
import sys
from scene import count_at, house_done_time, T, DUR, NH
SR=44100; N=int(SR*DUR)
out=np.zeros(N,np.float32)
def sq(f,dur,duty=0.5,vol=0.2,decay=8.0):
    t=np.arange(int(SR*dur))/SR
    w=np.where((t*f)%1<duty,1.0,-1.0)*vol*np.exp(-t*decay)
    return w.astype(np.float32)
def tri(f,dur,vol=0.2,decay=2.0):
    t=np.arange(int(SR*dur))/SR
    w=(2*np.abs(2*((t*f)%1)-1)-1)*vol*np.exp(-t*decay)
    return w.astype(np.float32)
def noise(dur,vol=0.2,decay=30.0,seed=0):
    t=np.arange(int(SR*dur))/SR
    r=np.random.RandomState(seed).uniform(-1,1,len(t))
    return (r*vol*np.exp(-t*decay)).astype(np.float32)
def add(t,w):
    i=int(t*SR); j=min(N,i+len(w))
    if i<N: out[i:j]+=w[:j-i]
# ---- música chiptune ----
bpm=104; beat=60/bpm
prog=[(48,[60,64,67]),(45,[57,60,64]),(41,[53,57,60]),(43,[55,59,62])]
mid=lambda m:440*2**((m-69)/12)
music=np.zeros(N,np.float32)
t=0.0;bar=0
while t<DUR:
    root,ch=prog[bar%4]
    for b in range(4):
        tb=t+b*beat
        w=tri(mid(root-12 if b%2 else root),beat*0.95,0.16,1.5); i=int(tb*SR); j=min(N,i+len(w))
        if i<N: music[i:j]+=w[:j-i]
        for k in range(4):
            ta=tb+k*beat/4; note=ch[(b*4+k)%3]+12*(k==3)
            w=sq(mid(note),beat/4*0.9,0.125,0.045,6.0); i=int(ta*SR); j=min(N,i+len(w))
            if i<N: music[i:j]+=w[:j-i]
        if b%2==1:
            w=noise(0.05,0.03,60,b); i=int(tb*SR); j=min(N,i+len(w))
            if i<N: music[i:j]+=w[:j-i]
    t+=4*beat; bar+=1
env=np.ones(N,np.float32)
fi=int(1.5*SR); env[:fi]=np.linspace(0,1,fi); fo=int(2.0*SR); env[-fo:]=np.linspace(1,0,fo)
out+=music*env*0.9
# ---- ef# ---- efeitos ----
# som "16 bits": eco leve na música inteira
d=int(0.19*SR)
echo=np.zeros_like(out); echo[d:]=out[:-d]
out+=echo*0.35
prev=count_at(0); lt=-9
for k in range(int(DUR*60)):
    tt=k/60; c=count_at(tt)
    if c!=prev and tt-lt>0.05:
        add(tt,sq(1320 if c%10 else 1760,0.03,0.25,0.06,40)); lt=tt
    prev=c
def chime(tt,vol=0.08):
    add(tt,sq(988,0.08,0.25,vol,20)); add(tt+0.07,sq(1319,0.14,0.25,vol,14))
def blip(tt): add(tt,sq(660,0.06,0.5,0.06,20)); add(tt+0.05,sq(990,0.1,0.5,0.06,16))
def fanfare(tt):
    for j,f in enumerate((784,988,1175,1568)): add(tt+j*0.06,sq(f,0.12,0.25,0.07,12))
def bell(tt):
    for f,v in ((1047,0.10),(1568,0.05),(2093,0.03)): add(tt,tri(f,1.4,v,2.6))
def whoosh(tt,dur=0.35):
    n=int(SR*dur); x=np.random.RandomState(int(tt*10)).uniform(-1,1,n).astype(np.float32)
    env=np.sin(np.linspace(0,np.pi,n))**2
    lp=np.convolve(x,np.ones(12)/12,'same'); add(tt-dur/2,(lp*env*0.12).astype(np.float32))
for i in range(45,NH):
    td=house_done_time(i)
    if td and td>0: chime(td,0.06)
for tt in (3.5,4.3,7.8,12.2,13.2,14.0,21.0,21.8,22.6,24.1,27.6,34.7,36.4,42.96,46.4,49.7,50.5,51.6,
           55.9,56.7,58.75,60.15,60.85,62.3,64.5,65.55,67.0,73.9):
    blip(tt)
for tt in (17.6,19.4,25.0,31.4,47.45,52.7): fanfare(tt)
for k in range(int((24.9-19.5)/0.27)):            # marteladas da obra
    add(19.5+k*0.27,noise(0.04,0.05,90,k)); add(19.5+k*0.27,sq(180,0.03,0.5,0.03,60))
for k in range(int((29.9-27.1)/0.09)):            # calçamento: "toc-toc" de pedra
    add(27.1+k*0.09,sq(520+(k%3)*90,0.025,0.5,0.025,80))
whoosh(27.1,0.8); whoosh(45.0,0.5)
# show na praça: bumbo + caixa + baixo animado
for k in range(int((55.7-50.5)/0.25)):
    tt=50.5+k*0.25; vol=0.10 if tt>52.6 else 0.06
    if k%2==0: add(tt,sq(60,0.12,0.5,vol,18))
    else: add(tt,noise(0.07,vol*0.7,40,k))
    add(tt,sq([110,110,147,165][(k//2)%4],0.2,0.5,vol*0.5,9))
for j_,fq in enumerate((659,784,880,784,659,587,523,587)*2):
    add(52.7+j_*0.18,sq(fq,0.15,0.25,0.035,10))
for j in range(3):                                 # fim do mapa
    add(68.9+j*0.3,sq(330,0.14,0.5,0.06,6)); add(69.05+j*0.3,sq(247,0.14,0.5,0.06,6))
for j,fq in enumerate((523,659,784,1047,1319)): add(T['cta'][0]+j*0.09,sq(fq,0.25 if j==4 else 0.12,0.25,0.08,6))
out=np.clip(out,-0.95,0.95)
dst=sys.argv[1] if len(sys.argv)>1 else 'bg.wav'
with wave.open(dst,'wb') as w_:
    w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR)
    w_.writeframes((out*32767).astype(np.int16).tobytes())
print('ok',np.abs(out).max())
