import numpy as np, wave, math
import sys
from scene import count_at, house_done_time, T, DUR, NH, SITE_CUTS, C0, old2new, DUR_VIDEO
from world import clamp
SR=44100; N=int(SR*DUR_VIDEO)
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
    i=int(old2new(t)*SR); j=min(N,i+len(w))   # tempos do roteiro -> tempo da narração final
    if i<N: out[i:j]+=w[:j-i]
# ---- música chiptune ----
bpm=104; beat=60/bpm
prog=[(48,[60,64,67]),(45,[57,60,64]),(41,[53,57,60]),(43,[55,59,62])]
mid=lambda m:440*2**((m-69)/12)
music=np.zeros(N,np.float32)
t=0.0;bar=0
while t<DUR_VIDEO:
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
for i in range(C0//10,NH):
    td=house_done_time(i)
    if td and td>0: chime(td,0.06)
for tt in (4.3,4.6,5.4,10.4,13.7,14.4,17.8,18.9,19.4,21.06,22.24,23.24,28.3,29.5,30.5,31.9,38.38,39.32,40.63,41.70,
           44.3,45.86,47.06,48.56,57.6,59.2,61.97,67.78,69.57,71.06,72.06,73.64,75.8,88.28,90.1,91.09,92.99,94.53,95.48,99.3):
    blip(tt)
for tt in (4.6,10.2,21.0,25.9,57.0,64.8,75.4,80.5,84.5,89.7,96.7): whoosh(tt,0.3)
fanfare(0.2)
# a cidade vira blocos: cubos caindo
for k in range(40): add(15.35+k*0.025,sq(180+(k%7)*60,0.04,0.5,0.04,30)); add(15.4+k*0.025,noise(0.03,0.03,60,k))
for j_,fq in enumerate((392,523,659,784,1047,1319,1568,2093)): add(15.75+j_*0.07,sq(fq,0.22,0.25,0.07,7))
# quase... 700!
for k in range(int((35.6-33.4)/0.06)): add(33.4+k*0.06,noise(0.04,0.02+0.04*k/36,70,k))
add(35.65,noise(0.6,0.16,6,1)); fanfare(35.7)
for j_,fq in enumerate((523,659,784,1047,1319,1568,2093)): add(35.75+j_*0.06,sq(fq,0.2,0.25,0.06,8))
for k in range(8):
    t0=35.7+k*0.18; add(t0+0.25,noise(0.5,0.09,8,k+50))
# obra do campo: pá e martelo
for k in range(int((42.5-36.6)/0.25)): add(36.6+k*0.25,noise(0.06,0.04,40,k+200))
fanfare(42.6)
# apito + passes
for tt in (43.6,49.8):
    add(tt,sq(2400,0.35,0.5,0.05,3)); add(tt+0.38,sq(2400,0.2,0.5,0.05,5))
for tt in (50.0,50.7,51.25,52.2,52.95): add(tt,noise(0.05,0.12,50,int(tt*10))); add(tt,tri(90,0.08,0.15,30))
add(53.4,noise(0.08,0.2,40,9)); add(53.4,tri(70,0.1,0.25,25))
# GOOOL: torcida e fogos
add(53.72,noise(2.2,0.10,1.4,77)); fanfare(53.75)
for k in range(10): add(53.9+k*0.18,noise(0.5,0.07,8,k+300))
# vira-lata: latidos
for tt in (54.9,55.3,56.1,56.5):
    add(tt,sq(420,0.07,0.5,0.08,25)); add(tt+0.02,noise(0.06,0.05,40,int(tt*7)))
# fazenda: galo e trator
for k in range(14): add(57.4+k*0.05,sq(600+ (k%5)*90,0.06,0.5,0.025,20))
for k in range(int(6.5/0.09)): add(58.0+k*0.09,sq(55,0.06,0.5,0.02,20))
# eleição: carimbo por cartaz
for k in range(11): add(65.45+k*0.22,noise(0.05,0.08,50,k+400))
# entregaram: carimbo
add(78.79,noise(0.15,0.2,20,5)); add(78.79,tri(80,0.2,0.25,10)); fanfare(78.9)
# chat: notificações
for k in range(12): add(80.7+k*0.3,sq(1568,0.04,0.5,0.03,30))
add(82.4,sq(330,0.12,0.5,0.06,10))
# 800
fanfare(84.8)
for j,fq in enumerate((523,659,784,1047,1319)): add(T['cta'][0]+j*0.09,sq(fq,0.25 if j==4 else 0.12,0.25,0.08,6))
for k in range(int((103-97)/0.42)): add(97.0+k*0.42,tri(110,0.08,0.12,30))
out=np.clip(out,-0.95,0.95)
dst=sys.argv[1] if len(sys.argv)>1 else 'bg.wav'
with wave.open(dst,'wb') as w_:
    w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR)
    w_.writeframes((out*32767).astype(np.int16).tobytes())
print('ok',np.abs(out).max())
