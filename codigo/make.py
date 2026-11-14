import subprocess, sys, time
from render import render_frame, FPS, DUR
a=int(sys.argv[1]); b=int(sys.argv[2]); out=sys.argv[3]
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r',str(FPS),'-i','-',
    '-c:v','libx264','-preset','ultrafast','-tune','animation','-crf','17','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
t0=time.time()
for k in range(a,b):
    p.stdin.write(render_frame(k/FPS).tobytes())
    if k%150==0: print(k,round(time.time()-t0),flush=True)
p.stdin.close(); p.wait(); print('done',round(time.time()-t0),flush=True)
