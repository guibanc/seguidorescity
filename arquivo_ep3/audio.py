import numpy as np, wave, math
import sys
from scene import count_at, house_done_time, T, DUR, NH, T_SWEEP
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
# ---- efeitos ----
# depois da evolução a música fica "16 bits": eco + dobra uma oitava acima
s1=int(T_SWEEP[1]*SR); g0=int((T_SWEEP[0]-1.0)*SR); g1=int(T_SWEEP[0]*SR)
d=int(0.19*SR)
echo=np.zeros_like(out); echo[d:]=out[:-d]
out[s1:]+=echo[s1:]*0.35
up=np.zeros_like(out); up[:-1:2]=0   # (mantém leve)
# glitch: corta a música em pedacinhos antes da varredura
for k in range(g0,g1,int(0.09*SR)):
    if (k//int(0.09*SR))%2: out[k:k+int(0.09*SR)]*=0.15
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
for i in range(32,NH):
    td=house_done_time(i)
    if td and td>0: chime(td,0.06)
for tt in (4.6,14.05,25.45,26.7,28.45,30.1,33.4,35.7,36.6,37.2,38.4,47.3,50.4,52.2,53.6,57.3,58.9,60.1,61.2,63.8,70.25):
    blip(tt)
# varredura: sobe um "zuuum" + brilho
a,b=T_SWEEP
tt=np.arange(int(SR*(b-a)))/SR; f=300+2400*(tt/(b-a))**2
w=(np.where((np.cumsum(f)/SR)%1<0.5,1,-1)*0.06*(0.3+0.7*tt/(b-a))).astype(np.float32); add(a,w)
for j,fq in enumerate((523,659,784,1047,1319,1568,2093)): add(b+j*0.05,sq(fq,0.22,0.25,0.07,8))
fanfare(22.6)
fanfare(68.3)
for j,fq in enumerate((523,659,784,1047,1319)): add(T['cta'][0]+j*0.09,sq(fq,0.25 if j==4 else 0.12,0.25,0.08,6))
out=np.clip(out,-0.95,0.95)
dst=sys.argv[1] if len(sys.argv)>1 else 'bg.wav'
with wave.open(dst,'wb') as w_:
    w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR)
    w_.writeframes((out*32767).astype(np.int16).tobytes())
print('ok',np.abs(out).max())
