"""Render a daily short from a script JSON + per-scene voice files.

usage: python engine/render.py SCRIPT.json AUDIO_DIR OUT.mp4
AUDIO_DIR must contain scene_00.mp3 (or .wav), scene_01..., one per scene.
"""
import json, os, subprocess, sys, math, glob
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import W, H, font, text_sprite, paste, CREAM, ease, rrect, film_overlay, grain, keywords, source_card, KW_COLS
import scenes as S
import scenes2 as S2
S.TYPES.update(S2.EXTRA)
from captions import SceneCaptions

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, 'config.json')))
FPS = CFG.get('fps', 30)
SR = 44100
GAP = 0.16


def probe_dur(path):
    out = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path])
    return float(out.strip())


def load_audio(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'])
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def scene_audio(audio_dir, i):
    for ext in ('mp3', 'wav'):
        p = os.path.join(audio_dir, f'scene_{i:02d}.{ext}')
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f'missing audio for scene {i}')


def pick_cta(script):
    sc = script.get('cta_dm') if CFG.get('dm_enabled') else script.get('cta_plain')
    return sc


def build_timeline(script, audio_dir):
    specs = list(script['scenes'])
    cta = pick_cta(script)
    if cta:
        specs.append(cta)
    tl, t = [], 0.35
    for i, sp in enumerate(specs):
        d = probe_dur(scene_audio(audio_dir, i))
        hold = float(sp.get('hold', 0.0))
        tl.append(dict(spec=sp, t0=t, vo0=t + 0.05, vo1=t + 0.05 + d, t1=t + 0.05 + d + GAP + hold, audio=scene_audio(audio_dir, i)))
        t = tl[-1]['t1']
    return tl, t


def mix_audio(tl, total, outro_path, out_wav, sfx_dir):
    n = int((total + 6) * SR)
    vo = np.zeros((n, 2), np.float32)
    for s in tl:
        a = load_audio(s['audio'])
        a = a / max(1e-4, np.abs(a).max()) * 0.8
        i0 = int(s['vo0'] * SR)
        vo[i0:i0 + len(a)] += a[:max(0, n - i0)]
    mus = np.zeros_like(vo)
    bed = load_audio(os.path.join(sfx_dir, 'score.mp3'))
    pos = 0
    while pos < int(total * SR):
        seg = bed[:min(len(bed), int(total * SR) - pos)]
        mus[pos:pos + len(seg)] += seg
        pos += len(seg)
    k = int(1.5 * SR)
    end = int(total * SR)
    mus[max(0, end - k):end] *= np.linspace(1, 0, min(k, end))[:, None]
    mus[end:] = 0
    env = np.convolve(np.abs(vo[:, 0]), np.ones(int(0.25 * SR)) / int(0.25 * SR), 'same')
    duck = 1 - 0.6 * np.clip(env / 0.05, 0, 1)
    mix = vo + mus * (0.28 * duck)[:, None]
    sfx_map = {'title': 'stinger', 'counter': 'tick', 'organ': 'heartbeat', 'body': 'heartbeat', 'taxi': 'riser', 'versus': 'boom',
               'nail': 'boom', 'toxin': 'riser', 'nerve': 'riser', 'spasm': 'heartbeat', 'soil': 'wind'}
    for s in tl:
        typ = s['spec'].get('visual', {}).get('type')
        name = s['spec'].get('sfx') or sfx_map.get(typ)
        if not name:
            continue
        p = os.path.join(sfx_dir, f'{name}.mp3')
        if os.path.exists(p):
            a = load_audio(p)[: int(2.5 * SR)] * 0.32
            f = int(0.3 * SR)
            a[-f:] *= np.linspace(1, 0, f)[:, None]
            i0 = int(s['t0'] * SR)
            mix[i0:i0 + len(a)] += a[:max(0, n - i0)]
    # outro audio (his voice line) after total
    if outro_path and os.path.exists(outro_path):
        o = load_audio(outro_path)
        i0 = int(total * SR)
        mix[i0:i0 + len(o)] += o[:max(0, n - i0)]
        n_end = i0 + len(o)
    else:
        n_end = end
    mix = np.clip(mix[:n_end], -1, 1)
    import soundfile as sf
    sf.write(out_wav, mix, SR, subtype='FLOAT')


def disclaimer_sprite(text):
    f = font('pop_m', 30)
    spr, ox, oy, tw, th = text_sprite(text, f, (255, 250, 240, 255), shadow=0)
    card, pad = rrect((tw + 56, th + 30), 30, (0, 0, 0, 150), outline=(255, 255, 255, 60), width=2)
    paste(card, spr, pad + 28 - ox, pad + 15 - oy)
    return card


def composer(script_path, audio_dir):
    script = json.load(open(script_path))
    pal = script.get('palette', 'ocean')
    speed = float(script.get('vo_speed', CFG.get('vo_speed', 1.0)))
    if abs(speed - 1.0) > 1e-3:  # speed the voice up/down without changing pitch
        import tempfile
        fast = tempfile.mkdtemp(prefix='vo_')
        for f in sorted(glob.glob(os.path.join(audio_dir, 'scene_*.*'))):
            name = os.path.splitext(os.path.basename(f))[0] + '.wav'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f, '-filter:a', f'atempo={speed}', '-ar', str(SR), os.path.join(fast, name)], check=True)
        audio_dir = fast
    tl, total = build_timeline(script, audio_dir)
    seed = sum(map(ord, script.get('id', ''))) % 1000
    bgs = {}

    def bg_for(p):
        if p not in bgs:
            bgs[p] = S.background(p, seed=seed)
        return bgs[p]

    show_caps = script.get('captions', True)
    film = script.get('film', False)
    objs = []
    for i, s in enumerate(tl):
        sp = s['spec']
        sp_pal = sp.get('bg') or pal
        objs.append((s, S.make(sp, s['t1'] - s['t0'], sp_pal, i), SceneCaptions(sp.get('cap', '') if show_caps else '', s['vo0'], s['vo1'] + GAP * 0.5), sp_pal))
    wm, wox, woy, wtw, wth = text_sprite(CFG['watermark'], font('pop_m', 34), (255, 255, 255, 72), shadow=0, blur=2)
    disc = disclaimer_sprite(CFG['disclaimer']) if CFG.get('disclaimer') else None
    def frame(fi):
        t = fi / FPS
        si = 0
        while si < len(objs) - 1 and t >= objs[si][0]['t1']:
            si += 1
        s, sc, cap, sp_pal = objs[si]
        P = S.PALETTES[sp_pal]
        fr = bg_for(sp_pal).copy()
        lt = t - s['t0']
        S.bokeh(fr, t, tuple(P['acc']))
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        sc.draw(layer, lt)
        z = 1.0 + 0.035 * min(1.0, lt / max(s['t1'] - s['t0'], 0.5))
        if z > 1.001:
            nw, nh = int(W * z), int(H * z)
            layer = layer.resize((nw, nh), Image.BILINEAR).crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
        fr.alpha_composite(layer)
        if film:
            fr.alpha_composite(film_overlay())
        sp = s['spec']
        kw = sp.get('kw')
        if kw:
            vo_len = s['vo1'] - s['vo0']
            v0 = s['vo0'] - s['t0']
            if isinstance(kw[0], list):  # several keyword pairs timed across the VO
                act = None
                for e in kw:
                    tk = v0 + vo_len * float(e[3] if len(e) > 3 else 0)
                    if lt >= tk - 0.05 or act is None:
                        act = (e, max(tk, 0.0))
                e, tk = act
                col = KW_COLS.get(e[2], KW_COLS['yellow']) if len(e) > 2 else KW_COLS['yellow']
                keywords(fr, lt, e[0], e[1], col, tk, tk + 0.22)
            else:
                t_p = v0 + vo_len * float(sp.get('kw_at', 0.4))
                col = KW_COLS.get(kw[2], KW_COLS['yellow']) if len(kw) > 2 else KW_COLS['yellow']
                keywords(fr, lt, kw[0], kw[1], col, v0, t_p)
        if sp.get('source'):
            t_s = (s['vo0'] - s['t0']) + (s['vo1'] - s['vo0']) * 0.3
            if lt >= t_s:
                source_card(fr, sp['source'], ease(lt, t_s, 0.25))
        # paper swipe transition at scene start
        if si > 0 and lt < 0.22:
            p = lt / 0.22
            x = -W + p * W * 2.2
            band = Image.new('RGBA', (int(W * 0.9), H), tuple(P['paper']) + (255,))
            paste(fr, band, x, 0, 1 - p * 0.3)
        cap.draw(fr, t)
        if disc is not None and (t < 4.0 or si == len(objs) - 1):
            k = min(1.0, t / 0.3) * (1 - ease(t, 3.6, 0.4)) if t < 4.0 else ease(lt, 0.0, 0.3)
            paste(fr, disc, W / 2 - disc.width / 2, 1450 - disc.height / 2, k)
        paste(fr, wm, W / 2 - wtw / 2 - wox, 1530 - wth / 2 - woy)
        if film:
            fr.alpha_composite(grain(fi))
        return fr.convert('RGB')

    return script, tl, total, frame


def render(script_path, audio_dir, out_path):
    script, tl, total, frame = composer(script_path, audio_dir)
    tmpdir = os.path.dirname(os.path.abspath(out_path))
    body_mp4 = os.path.join(tmpdir, '_body.mp4')
    nframes = int(math.ceil(total * FPS))
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', body_mp4], stdin=subprocess.PIPE)
    for fi in range(nframes):
        ff.stdin.write(frame(fi).tobytes())
    ff.stdin.close()
    ff.wait()
    outro = os.path.join(ROOT, 'assets', 'outro.mp4')
    wav = os.path.join(tmpdir, '_mix.wav')
    mix_audio(tl, total, outro, wav, os.path.join(ROOT, 'assets', 'sfx'))
    # concat body + outro video
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', body_mp4, '-i', outro, '-i', wav, '-filter_complex',
           f'[0:v]fps={FPS},format=yuv420p[a];[1:v]scale={W}:{H},fps={FPS},format=yuv420p[b];[a][b]concat=n=2:v=1:a=0[v];'
           f'[2:a]loudnorm=I=-14:TP=-1.5:LRA=11[au]',
           '-map', '[v]', '-map', '[au]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-c:a', 'aac', '-b:a', '160k',
           '-ar', '44100', '-movflags', '+faststart', '-shortest', out_path]
    subprocess.run(cmd, check=True)
    for p in (body_mp4, wav):
        try:
            os.remove(p)
        except OSError:
            pass
    return total


def thumbnail(script_path, out_jpg):
    script = json.load(open(script_path))
    pal = script.get('palette', 'ocean')
    first = script['scenes'][0]
    sp_pal = first.get('bg') or pal
    fr = S.background(sp_pal).copy()
    sc = S.make(first, 3.0, sp_pal, 0)
    sc.draw(fr, 1.2)
    if script.get('film'):
        fr.alpha_composite(film_overlay())
    th = script.get('thumb_kw') or first.get('kw')
    if th and isinstance(th[0], list):
        th = th[-1]
    if th:
        col = KW_COLS.get(th[2], KW_COLS['yellow']) if len(th) > 2 else KW_COLS['yellow']
        keywords(fr, 5.0, th[0], th[1], col, 0, 0)
    fr.convert('RGB').save(out_jpg, quality=92)


if __name__ == '__main__':
    sp, ad, out = sys.argv[1], sys.argv[2], sys.argv[3]
    d = render(sp, ad, out)
    thumbnail(sp, os.path.splitext(out)[0] + '.jpg')
    print(f'rendered {out} ({d:.1f}s + outro)')
