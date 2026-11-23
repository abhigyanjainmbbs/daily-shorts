import sys, os, math, subprocess
sys.path.insert(0, '/home/claude/daily-shorts/engine')
import render as R

SP = '/home/claude/daily-shorts/scripts/queue/2026-11-23-scd.json'
AD = '/home/claude/daily-shorts/voice/2026-11-23-scd'
OUT = '/home/claude/work/scd/body.mp4'

script, tl, total, frame = R.composer(SP, AD)
n = int(math.ceil(total * R.FPS))
print('total', total, 'frames', n, flush=True)
ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                       '-s', f'{R.W}x{R.H}', '-r', str(R.FPS), '-i', '-',
                       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17',
                       '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
for fi in range(n):
    ff.stdin.write(frame(fi).tobytes())
    if fi % 120 == 0:
        print('f', fi, flush=True)
ff.stdin.close(); ff.wait()
print('done')
