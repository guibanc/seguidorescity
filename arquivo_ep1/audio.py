import numpy as np, wave, math
from scene import count_at, house_done_time, trees
SR=44100; DUR=78.6; N=int(SR*DUR)
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
last=-1; prev=0; lt=-9
for k in range(int(DUR*60)):
    tt=k/60; c=count_at(tt)
    if c!=prev and tt-lt>0.05:
        add(tt,sq(1320 if c%10 else 1760,0.03,0.25,0.06,40)); lt=tt
    prev=c
def chime(tt,vol=0.08):
    add(tt,sq(988,0.08,0.25,vol,20)); add(tt+0.07,sq(1319,0.14,0.25,vol,14))
for i in range(27):
    td=house_done_time(i)
    if td: chime(td,0.06)
for tr in trees:
    if tr['chop'] and tr.get('mode')=='axe':
        for k in range(3): add(tr['chop']-0.85+k*0.28,noise(0.06,0.18,50,k)+sq(180,0.06,0.5,0.05,40))
    elif tr['chop']: add(tr['chop'],noise(0.12,0.05,25,3))
for k in range(int((37.8-30.4)/0.34)): add(30.4+k*0.34,noise(0.03,0.07,80,k)+sq(420,0.03,0.5,0.03,60))
for tt in (0.25,10.5,12.7,14.5,16.4,52.4,54.5,57.8,61.8,64.6,68.4,70.8):
    add(tt,sq(660,0.06,0.5,0.06,20)); add(tt+0.05,sq(990,0.1,0.5,0.06,16))
for tt in (40.4,41.4,42.75):
    for j,f in enumerate((784,988,1175,1568)): add(tt+j*0.06,sq(f,0.12,0.25,0.07,12))
for tt in (44.0,44.9,45.9,47.1): chime(tt,0.07)
for j,f in enumerate((523,659,784,1047,1319)): add(75.2+j*0.09,sq(f,0.25 if j==4 else 0.12,0.25,0.08,6))
out=np.clip(out,-0.95,0.95)
with wave.open('/home/claude/vila/bg.wav','wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out*32767).astype(np.int16).tobytes())
print('ok',np.abs(out).max())
