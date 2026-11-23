import sys, subprocess, numpy as np
sys.path.insert(0,'/home/claude/daily-shorts/engine')
from PIL import Image
import gfx as G
W,H,FPS=1080,1920,30
def grab(src, ss, dur, zoom=1.0):
    n=int(round(dur*FPS))
    vf=f"fps={FPS},scale=-2:{int(H*zoom)},crop={W}:{H}"
    p=subprocess.run(['ffmpeg','-v','error','-ss',str(ss),'-i',src,'-frames:v',str(n),
                      '-vf',vf,'-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True)
    a=np.frombuffer(p.stdout,np.uint8)
    a=a[:n*H*W*3].reshape(-1,H,W,3)
    return [Image.fromarray(x).convert('RGBA') for x in a]

A='clips/clip_man_gym.mp4'; B='clips/clip_lift.mp4'
plan=[(A,1.2,1.55,1.00),(None,0,0.20,1.0),(A,6.2,1.25,1.35),(B,1.6,1.00,1.05),(A,3.4,0.95,1.18)]
frames=[]
for src,ss,dur,z in plan:
    if src is None:
        frames += [Image.new('RGBA',(W,H),(0,0,0,255))]*int(round(dur*FPS))
    else:
        frames += grab(src,ss,dur,z)
need=int(round(4.949*FPS))
while len(frames)<need: frames.append(frames[-1].copy())
frames=frames[:need]

wm,wox,woy,wtw,wth=G.text_sprite('@abhigyanjainmbbs',G.font('pop_b',38),(255,255,255,80),shadow=0.35,blur=4)
out=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),
                      '-i','-','-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','hook.mp4'],stdin=subprocess.PIPE)
for i,fr in enumerate(frames):
    t=i/FPS
    fr=fr.copy()
    # punchy grade: contrast + slight desat
    arr=np.asarray(fr.convert('RGB')).astype(np.float32)
    g=arr.mean(axis=2,keepdims=True)
    arr=arr*0.88+g*0.12
    arr=(arr-128.0)*1.18+128.0+6.0
    # red flash on the black-cut impact
    if 1.55<=t<1.78:
        arr[:,:,0]+= 38*(1-(t-1.55)/0.23)
    fr=Image.fromarray(np.clip(arr,0,255).astype(np.uint8)).convert('RGBA')
    fr.alpha_composite(G.film_overlay())
    fr.alpha_composite(G.grain(i))
    if t<2.78: G.keywords(fr,t,'GYM MEIN JAWAN LOG','ACHANAK GIR RAHE HAIN',G.KW_COLS['red'],0.15,0.40)
    if t>=2.80:
        ov=Image.new('RGBA',(W,H),(0,0,0,0))
        G.keywords(ov,t,'AUR REPORT?','AKSAR NORMAL',G.KW_COLS['yellow'],2.80,3.75)
        fr=Image.alpha_composite(fr,ov)
    G.paste(fr,wm,W/2-wtw/2+wox,1530+woy,1.0)
    out.stdin.write(np.asarray(fr.convert('RGB')).tobytes())
out.stdin.close(); out.wait()
print('hook frames',len(frames))
