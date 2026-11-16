import numpy as np, wave, math
import sys
from scene import count_at, house_done_time, T, DUR, NH, SITE_CUTS
from world import clamp
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
for i in range(60,NH):
    td=house_done_time(i)
    if td and td>0: chime(td,0.06)
for tt in (11.45,11.7,11.95,12.2,19.8,21.2,22.9,35.5,36.5,37.5,38.8,39.7,40.5,41.4,45.7,47.1,48.1,48.5,52.2,53.6,55.1,56.1,57.3,
           74.4,77.6,80.4,81.4,85.0,87.1,90.9,91.6,93.7,95.2,96.1,100.0,101.2):
    blip(tt)
for a_,b_,nm in SITE_CUTS: whoosh(a_,0.25); blip(a_+0.05)
# abertura: vento + nota grave
for k in range(int(7.2/0.1)):
    add(k*0.1,noise(0.12,0.02*clamp(k/20),20,k))
add(0.3,tri(55,6.5,0.10,0.35)); add(5.5,tri(82,2.0,0.08,1.2))
fanfare(7.4)
# rufar de tambor (14.75 -> 16.5) e explosão no nome
for k in range(int((16.5-14.75)/0.035)):
    tt=14.75+k*0.035; add(tt,noise(0.03,0.03+0.05*k/50,70,k))
add(16.5,noise(0.6,0.16,6,1)); fanfare(16.55)
for j_,fq in enumerate((523,659,784,1047,1319,1568,2093)): add(16.6+j_*0.06,sq(fq,0.2,0.25,0.06,8))
# mutirão: serrote, pincel, corda
for k in range(int((21.1-19.8)/0.18)): add(19.8+k*0.18,noise(0.14,0.05,25,k))
for k in range(15): add(21.2+k*0.1,sq(700+(k%5)*80,0.04,0.5,0.03,30))
for k in range(int((25.0-22.9)/0.3)): add(22.9+k*0.3,sq(110,0.18,0.5,0.05,6)); add(22.9+k*0.3,noise(0.08,0.03,30,k))
fanfare(25.1)
# fogos
for k in range(9):
    t0=25.4+k*0.42; add(t0,noise(0.3,0.02,40,k)); add(t0+0.3,noise(0.5,0.11,8,k+50))
# nuvens / evolução
whoosh(30.8,1.6); whoosh(32.6,1.2)
for k in range(48): add(31.0+k*0.04,sq(196*2**(k/16),0.05,0.25,0.03,16))
for j_,fq in enumerate((392,523,659,784,1047,1319,1568,2093)): add(33.75+j_*0.07,sq(fq,0.22,0.25,0.07,7))
fanfare(33.8)
# provador: um "clic" por troca de roupa
for k in range(int((51.2-45.6)/0.42)): add(45.6+k*0.42,sq(1200,0.03,0.5,0.03,40))
# prefeito / economia / campo
fanfare(74.4)
for k in range(30): add(80.3+k*0.13,sq(1568+(k%3)*200,0.05,0.5,0.025,30))
for k in range(9): add(85.0+k*0.6,sq(120,0.05,0.5,0.03,30))
for j,fq in enumerate((523,659,784,1047,1319)): add(T['cta'][0]+j*0.09,sq(fq,0.25 if j==4 else 0.12,0.25,0.08,6))
fanfare(101.2)
out=np.clip(out,-0.95,0.95)
dst=sys.argv[1] if len(sys.argv)>1 else 'bg.wav'
with wave.open(dst,'wb') as w_:
    w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR)
    w_.writeframes((out*32767).astype(np.int16).tobytes())
print('ok',np.abs(out).max())
