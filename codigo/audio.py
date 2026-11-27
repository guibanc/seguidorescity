import numpy as np, wave, math
import sys
from scene import count_at, house_done_time, T, DUR, NH, SITE_CUTS, C0, old2new, DUR_VIDEO, KW
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
K=KW
for k in ('padaria','forno','fila','paoqueijo','ganhou','c79','c80','c81','terreno','torre','preto','peludo','curto','tres','vacas','comentario',
          'curral','aberta','chat','c16','ontem','placar','sexta','quem','rio','mil','r814','r81','rpad','rrua','vota','comenta'):
    blip(K[k])
for k in T:
    if T[k][0]>0.2: whoosh(T[k][0],0.3)
fanfare(0.2)
for k in range(12): add(K['oitocentos']-1.6+k*0.12,sq(400+k*50,0.04,0.4,0.03,20))
fanfare(K['oitocentos'])
for j in range(8): add(K['oitocentos']+0.2+j*0.18,noise(0.5,0.07,8,j+50))
fanfare(K['padaria'])
# rua nova: máquina
for k in range(int(1.8/0.08)): add(K['ruanova']-0.1+k*0.08,sq(60,0.06,0.5,0.02,20))
# latidos (3 cachorros)
for tt,fq in ((K['preto'],520),(K['peludo'],380),(K['curto'],440),(K['tres'],460),(K['tres']+0.25,520)):
    add(tt,sq(fq,0.07,0.5,0.08,25)); add(tt+0.02,noise(0.06,0.05,40,int(tt*7)))
fanfare(K['tres'])
# muuu
for tt in (K['vacas'],K['vaca1']):
    for j in range(16): add(tt+j*0.03,sq(150-j*3,0.04,0.5,0.06,6))
# chat: notificações
for k in range(5): add(T['chat'][0]+0.3+k*0.55,sq(1568,0.04,0.5,0.03,30))
for k in range(16): add(T['mural'][0]+0.2+k*0.11,noise(0.05,0.07,50,k+400))
add(K['empate'],noise(0.15,0.2,20,5)); add(K['empate'],tri(80,0.3,0.3,8))
for k in range(int((K['ep11']-K['sexta'])/0.5)): add(K['sexta']+k*0.5,sq(1200,0.03,0.5,0.03,40))
fanfare(K['ep11']); fanfare(K['ponte'])
for j,fq in enumerate((523,659,784,1047,1319)): add(T['cta'][0]+j*0.09,sq(fq,0.25 if j==4 else 0.12,0.25,0.08,6))
for k in range(int((DUR_VIDEO-T['cta'][0])/0.42)): add(T['cta'][0]+0.3+k*0.42,tri(110,0.08,0.12,30))
out=np.clip(out,-0.95,0.95)
dst=sys.argv[1] if len(sys.argv)>1 else 'bg.wav'
with wave.open(dst,'wb') as w_:
    w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR)
    w_.writeframes((out*32767).astype(np.int16).tobytes())
print('ok',np.abs(out).max())
