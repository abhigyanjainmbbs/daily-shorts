"""Cut-out animation scenes ("comp"): AI image plates + cut-out sprites animated with keyframes,
image swaps and layered effects - the 2.5D editor style used by big science-explainer reels.

visual spec:
{"type": "comp",
 "bg": {"img": "courtyard", "blur": 8, "zoom": [1.0, 1.08], "pan": [0, -40], "dark": 0.15,
        "seq": [["soil_day", 0], ["soil_dusk", 0.4], ["soil_storm", 0.7]]},     # optional crossfades (fractions)
 "layers": [
   {"img": "nail_cut", "w": 520, "x": 540, "y": 1180, "rot": -8,              # base pose (px, deg)
    "keys": [{"t": 0, "y": 2300}, {"t": 0.12, "y": 1180, "e": "back"}],        # keyframes (t = fraction of scene)
    "swap": [[0.55, "hand_fist_cut"]],                                         # image swaps at fractions
    "shadow": true, "wiggle": 0, "bob": 0, "drift": [0, 0], "spin": 0, "flip": false, "glow": [140,240,60]},
   {"text": "0.000000 g", "font": "osw", "size": 90, "col": [120,255,140], "x": 540, "y": 1290,
    "swap": [[0.5, "0.000000175 g"]]}],
 "fx": [{"type": "steam", "x": 540, "y": 900, "w": 380},
        {"type": "bubbles", "n": 10}, {"type": "boil", "x": 540, "y": 1000, "w": 420, "h": 90},
        {"type": "flakes", "x": 560, "y": 900, "t": 0.4}, {"type": "blood", "x": 600, "y": 980, "t": 0.5},
        {"type": "glow", "x": 540, "y": 900, "r": 220, "col": [140,240,60]},
        {"type": "particles", "col": [140,240,60], "n": 24, "t": 0.5},
        {"type": "shake", "t": 0.5, "d": 0.4, "amp": 14}, {"type": "flash", "t": 0.5},
        {"type": "path", "pts": [[x,y],...], "t": 0.1, "d": 0.7, "col": [140,240,60]},
        {"type": "people", "n": 10, "red": 1, "y": 1250, "t": 0.4},
        {"type": "crack", "x": 540, "y": 900, "t": 0.5}]}
Images live in <img_dir>/<name>.png ('_cut' names are transparent cut-outs).
"""
import math, os, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from gfx import W, H, font, text_sprite, paste, paste_c, ease, clamp, sphere, glow, drop_shadow, emoji


# ---------- loading ----------
@lru_cache(maxsize=128)
def load(path):
    im = Image.open(path).convert('RGBA')
    if path.endswith('_cut.png'):
        bb = im.getchannel('A').getbbox()
        if bb:
            im = im.crop(bb)
    return im


@lru_cache(maxsize=256)
def sized(path, w, flip=False):
    im = load(path)
    if w and abs(im.width - w) > 1:
        im = im.resize((int(w), max(1, int(im.height * w / im.width))), Image.LANCZOS)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im


@lru_cache(maxsize=64)
def shadowed(path, w, flip=False, blur=18, alpha=150, off=(0, 22)):
    return drop_shadow(sized(path, w, flip), off, blur, alpha)


@lru_cache(maxsize=32)
def plate(path, blur=0, dark=0.0, sat=1.0, oversize=1.12):
    """cover-fit an image to a slightly oversized frame so we can zoom/pan."""
    im = load(path).convert('RGB')
    tw, th = int(W * oversize), int(H * oversize)
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s + 1), int(im.height * s + 1)), Image.LANCZOS)
    x0, y0 = (im.width - tw) // 2, (im.height - th) // 2
    im = im.crop((x0, y0, x0 + tw, y0 + th))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    if sat != 1.0:
        im = ImageEnhance.Color(im).enhance(sat)
    if dark:
        im = ImageEnhance.Brightness(im).enhance(1 - dark)
    return im.convert('RGBA')


def view(pl, zoom, dx, dy):
    """crop a W x H view out of an oversized plate (1.12x frame) at zoom (>=1) and pan offset (px)."""
    pw, ph = pl.size
    vw, vh = W / zoom, H / zoom
    x0 = clamp(pw / 2 + dx - vw / 2, 0, pw - vw)
    y0 = clamp(ph / 2 + dy - vh / 2, 0, ph - vh)
    return pl.crop((int(x0), int(y0), int(x0 + vw), int(y0 + vh))).resize((W, H), Image.BILINEAR)


# ---------- easing / keyframes ----------
def _ease(p, kind):
    p = clamp(p)
    if kind == 'lin':
        return p
    if kind == 'in':
        return p * p * p
    if kind == 'inout':
        return 3 * p * p - 2 * p * p * p
    if kind == 'back':
        c1, c3 = 1.70158, 2.70158
        return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2
    if kind == 'bounce':
        n1, d1 = 7.5625, 2.75
        if p < 1 / d1:
            return n1 * p * p
        if p < 2 / d1:
            p -= 1.5 / d1
            return n1 * p * p + .75
        if p < 2.5 / d1:
            p -= 2.25 / d1
            return n1 * p * p + .9375
        p -= 2.625 / d1
        return n1 * p * p + .984375
    return 1 - (1 - p) ** 3  # out


PROPS = ('x', 'y', 'scale', 'rot', 'alpha')


def pose_at(base, keys, f):
    """base pose dict + keyframes [{t, x?, y?, scale?, rot?, alpha?, e?}] -> pose at fraction f.
    Each property animates from its previous keyframe value (or the base) to the next one."""
    pose = {k: base.get(k, {'scale': 1.0, 'alpha': 1.0, 'rot': 0.0}.get(k, 0.0)) for k in PROPS}
    if not keys:
        return pose
    ks = sorted(keys, key=lambda k: k['t'])
    for p in PROPS:
        track = [(k['t'], k[p], k.get('e', 'out')) for k in ks if p in k]
        if not track:
            continue
        # implicit end value = base value after the last key if the first key is before base? keep simple:
        # before first key -> first key value; between keys -> interpolate; after last -> base if marked, else last
        if f <= track[0][0]:
            pose[p] = track[0][1]
            continue
        val = None
        for (t0, v0, _), (t1, v1, e1) in zip(track, track[1:]):
            if t0 <= f <= t1:
                val = v0 + (v1 - v0) * _ease((f - t0) / max(t1 - t0, 1e-6), e1)
                break
        if val is None:
            val = track[-1][1]
        pose[p] = val
    return pose


# ---------- effects ----------
@lru_cache(maxsize=8)
def wisp(size=260):
    im = Image.new('RGBA', (size, size * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((size * .25, size * .2, size * .75, size * 1.8), fill=(255, 255, 255, 120))
    return im.filter(ImageFilter.GaussianBlur(size * .14))


@lru_cache(maxsize=16)
def glass_bubble(r):
    r = int(r)
    s = r * 2 + 8
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    d = np.sqrt((xx - s / 2) ** 2 + (yy - s / 2) ** 2) / r
    a = np.clip((d - 0.55) / 0.45, 0, 1) ** 2.2 * 150 * (d <= 1.0)
    rim = np.clip(1 - np.abs(d - 0.97) / 0.05, 0, 1) * 200
    alpha = np.clip(a + rim, 0, 230)
    rgb = np.dstack([np.full_like(d, 225), np.full_like(d, 240), np.full_like(d, 255)])
    im = Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), 'RGBA')
    dd = ImageDraw.Draw(im)
    hx, hy, hr = s * .36, s * .32, r * .22
    dd.ellipse((hx - hr, hy - hr * .7, hx + hr, hy + hr * .7), fill=(255, 255, 255, 230))
    return im.filter(ImageFilter.GaussianBlur(0.8))


@lru_cache(maxsize=4)
def flake(seed):
    rnd = random.Random(seed)
    w, h = rnd.randint(10, 22), rnd.randint(6, 14)
    im = Image.new('RGBA', (w + 4, h + 4), (0, 0, 0, 0))
    pts = [(2 + rnd.uniform(0, w * .3), 2 + rnd.uniform(0, h)), (2 + w * rnd.uniform(.5, 1), 2), (2 + w, 2 + h * rnd.uniform(.4, 1)),
           (2 + w * rnd.uniform(.2, .6), 2 + h)]
    ImageDraw.Draw(im).polygon(pts, fill=(rnd.randint(130, 190), rnd.randint(55, 85), rnd.randint(15, 35), 255))
    return im


@lru_cache(maxsize=4)
def blood_drop(r=26):
    d = sphere(r, (170, 10, 18), spec=0.9)
    return d


def person_icon(h, col):
    im = Image.new('RGBA', (int(h * .6), h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = im.width
    d.ellipse((w * .28, 0, w * .72, h * .3), fill=col)
    d.rounded_rectangle((w * .08, h * .34, w * .92, h), int(w * .3), fill=col)
    return im


class FX:
    def __init__(self, spec, dur, rnd):
        self.s, self.dur, self.rnd = spec, dur, rnd
        self.seed = rnd.randint(0, 9999)

    def f(self, t):
        return t / max(self.dur, 1e-3)

    def draw(self, fr, t):
        s = self.s
        typ = s['type']
        f = self.f(t)
        t0 = s.get('t', 0.0)
        if f < t0 and typ not in ('steam', 'bubbles', 'boil', 'glow'):
            return
        if 'until' in s and f > s['until']:
            return
        lt = (f - t0) * self.dur  # seconds since effect start
        rnd = random.Random(self.seed)
        if typ == 'steam':
            x, y, w = s.get('x', W / 2), s.get('y', 900), s.get('w', 360)
            n = s.get('n', 7)
            for i in range(n):
                ph = (t * 0.35 + i / n) % 1
                xx = x + (rnd.uniform(-.5, .5) * w) + math.sin(t * 1.3 + i * 2) * 30 * ph
                yy = y - ph * s.get('rise', 520)
                k = math.sin(ph * math.pi) * s.get('a', 0.8)
                sc = 0.6 + ph * 1.1
                paste_c(fr, wisp(int(160 * sc) + 20), xx, yy, k)
        elif typ == 'bubbles':
            n = s.get('n', 10)
            for i in range(n):
                r = rnd.uniform(s.get('rmin', 22), s.get('rmax', 70))
                bx = rnd.uniform(80, W - 80)
                speed = rnd.uniform(60, 140)
                by = (rnd.uniform(0, H) - t * speed) % (H + 300) - 150 + s.get('dy', 0)
                bx += math.sin(t * 1.5 + i) * 18
                paste_c(fr, glass_bubble(int(r)), bx, by, s.get('a', 0.9) * ease(t, i * 0.05, 0.4))
        elif typ == 'boil':
            x, y, w, h = s.get('x', W / 2), s.get('y', 1000), s.get('w', 420), s.get('h', 90)
            for i in range(s.get('n', 22)):
                ph = (t * rnd.uniform(1.2, 2.4) + rnd.random()) % 1
                bx = x + rnd.uniform(-.5, .5) * w
                by = y + rnd.uniform(-.5, .5) * h
                r = 6 + ph * rnd.uniform(10, 24)
                paste_c(fr, glass_bubble(int(r)), bx, by, math.sin(ph * math.pi) * 0.9)
        elif typ == 'flakes':
            x, y = s.get('x', W / 2), s.get('y', 900)
            for i in range(s.get('n', 26)):
                st = rnd.uniform(0, 0.6)
                if lt < st:
                    continue
                tt = lt - st
                fx = x + rnd.uniform(-s.get('spread', 160), s.get('spread', 160)) + math.sin(tt * 3 + i) * 20
                fy = y + rnd.uniform(-40, 40) + 0.5 * 1400 * tt * tt * rnd.uniform(.5, 1)
                im = flake(i % 4).rotate(tt * 360 * rnd.uniform(.5, 1.5) + i * 40, expand=True)
                if fy < H + 40:
                    paste_c(fr, im, fx, fy, 1.0, rnd.uniform(1.0, 1.8))
        elif typ == 'blood':
            x, y = s.get('x', W / 2), s.get('y', 900)
            g = ease(lt, 0, 0.25)
            r = s.get('r', 26)
            drip = s.get('drip', 0) * ease(lt, 0.3, 1.2)
            if drip:
                dd = ImageDraw.Draw(fr)
                dd.rounded_rectangle((x - r * .35, y, x + r * .35, y + drip), int(r * .35), fill=(150, 8, 16, 255))
                paste_c(fr, blood_drop(int(r * .6)), x, y + drip, 1)
            paste_c(fr, blood_drop(r), x, y, g, 0.4 + 0.6 * g)
        elif typ == 'glow':
            k = s.get('a', 0.8) * (0.75 + 0.25 * math.sin(t * s.get('pulse', 3)))
            if 't' in s:
                k *= ease(lt, 0, 0.3)
            paste_c(fr, glow(s.get('r', 200), tuple(s.get('col', (255, 220, 140)))), s.get('x', W / 2), s.get('y', 900), k)
        elif typ == 'particles':
            col = tuple(s.get('col', (140, 240, 60)))
            cx, cy, R = s.get('x', W / 2), s.get('y', 900), s.get('r', 420)
            spread = ease(lt, 0, s.get('d', 1.2))
            for i in range(s.get('n', 24)):
                a = rnd.uniform(0, 2 * math.pi) + t * rnd.uniform(-.3, .3)
                rr = rnd.uniform(.2, 1) * R * spread
                px, py = cx + math.cos(a) * rr * 1.2, cy + math.sin(a) * rr
                sz = rnd.uniform(10, 22)
                paste_c(fr, glow(int(sz * 2.2), col), px, py, 0.6)
                paste_c(fr, sphere(sz, col, spec=0.5), px, py, spread)
        elif typ == 'flash':
            k = 1 - ease(lt, 0, s.get('d', 0.35))
            if k > 0:
                fl = Image.new('RGBA', (W, H), tuple(s.get('col', (255, 255, 255))) + (int(200 * k),))
                fr.alpha_composite(fl)
        elif typ == 'path':
            pts = s['pts']
            p = ease(lt, 0, s.get('d', 1.0) * self.dur)
            segs = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
            tot, dist, acc, drawn = sum(segs), sum(segs) * p, 0, [tuple(pts[0])]
            for i, L in enumerate(segs):
                if acc + L <= dist:
                    drawn.append(tuple(pts[i + 1]))
                    acc += L
                else:
                    q = (dist - acc) / max(L, 1e-6)
                    drawn.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * q, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * q))
                    break
            if len(drawn) > 1:
                col = tuple(s.get('col', (140, 240, 60)))
                gl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(gl).line(drawn, fill=col + (255,), width=s.get('w', 26), joint='curve')
                fr.alpha_composite(gl.filter(ImageFilter.GaussianBlur(12)))
                ImageDraw.Draw(fr).line(drawn, fill=(235, 255, 200, 255), width=max(4, s.get('w', 26) // 3), joint='curve')
                paste_c(fr, glow(46, col), drawn[-1][0], drawn[-1][1], 1)
        elif typ == 'people':
            n, red = s.get('n', 10), s.get('red', 1)
            y, hh = s.get('y', 1250), s.get('h', 150)
            gap = hh * 0.66
            x0 = W / 2 - (n - 1) * gap / 2
            for i in range(n):
                k = ease(lt, i * 0.06, 0.2)
                is_red = i >= n - red and lt > s.get('red_at', 0.9)
                col = (235, 50, 45, 255) if is_red else (245, 240, 230, 235)
                paste_c(fr, person_icon(int(hh), col), x0 + i * gap, y, k)
        elif typ == 'crack':
            k = ease(lt, 0, 0.15)
            x, y = s.get('x', W / 2), s.get('y', 900)
            rr = random.Random(5)
            dd = ImageDraw.Draw(fr)
            for j in range(7):
                a = j / 7 * 2 * math.pi + rr.uniform(-.3, .3)
                pts = [(x, y)]
                L = s.get('r', 220) * k
                for q in range(4):
                    a += rr.uniform(-.5, .5)
                    pts.append((pts[-1][0] + math.cos(a) * L / 4, pts[-1][1] + math.sin(a) * L / 4))
                dd.line(pts, fill=(255, 255, 255, 230), width=5)
        elif typ == 'rings':  # sound / alarm rings
            x, y = s.get('x', W / 2), s.get('y', 900)
            for i in range(3):
                ph = (lt * 1.2 + i / 3) % 1
                r = 60 + ph * s.get('r', 320)
                im = Image.new('RGBA', (int(r * 2 + 10),) * 2, (0, 0, 0, 0))
                ImageDraw.Draw(im).ellipse((5, 5, r * 2 + 5, r * 2 + 5), outline=tuple(s.get('col', (255, 255, 255))) + (220,), width=6)
                paste_c(fr, im, x, y, 1 - ph)
        elif typ == 'emoji':
            k = ease(lt, 0, 0.2)
            paste_c(fr, emoji(s['ch'], s.get('size', 140)), s.get('x', W / 2), s.get('y', 900), k, 0.6 + 0.4 * _ease(min(lt / 0.3, 1), 'back'))


class Comp:
    def __init__(self, spec, dur, pal, seed):
        self.v = spec.get('visual', {})
        self.dur = dur
        self.rnd = random.Random(seed)
        self.dir = self.v.get('_dir', '.')
        b = self.v.get('bg') or {}
        self.bg = b
        self.plates = []
        if b.get('seq'):
            for e in b['seq']:
                name, at = e[0], e[1]
                bb = dict(b)
                if len(e) > 2:
                    bb['blur'] = e[2]
                if len(e) > 3:
                    bb['dark'] = e[3]
                self.plates.append((self._plate(name, bb), at))
        elif b.get('img'):
            self.plates.append((self._plate(b['img'], b), 0.0))
        self.fx = [FX(s, dur, self.rnd) for s in self.v.get('fx', [])]
        self.shake = [s for s in self.v.get('fx', []) if s['type'] == 'shake']

    def path(self, name):
        p = os.path.join(self.dir, name if name.endswith('.png') else name + '.png')
        return p

    def _plate(self, name, b):
        return plate(self.path(name), b.get('blur', 0), b.get('dark', 0.0), b.get('sat', 1.0))

    def draw(self, fr, t):
        f = t / max(self.dur, 1e-3)
        b = self.bg
        if self.plates:
            z0, z1 = (b.get('zoom') or [1.0, 1.06])
            z = z0 + (z1 - z0) * _ease(f, 'inout')
            px, py = (b.get('pan') or [0, 0])
            dx, dy = px * _ease(f, 'inout'), py * _ease(f, 'inout')
            cur = view(self.plates[0][0], z, dx, dy)
            for pl, at in self.plates[1:]:
                k = ease(t, at * self.dur, b.get('xfade', 0.6))
                if k > 0:
                    nxt = view(pl, z, dx, dy)
                    cur = Image.blend(cur, nxt, k) if k < 1 else nxt
            fr.alpha_composite(cur)
        under = [s for s in self.fx if s.s.get('under')]
        over = [s for s in self.fx if not s.s.get('under') and s.s['type'] != 'shake']
        for e in under:
            e.draw(fr, t)
        for L in self.v.get('layers', []):
            self._layer(fr, L, t, f)
        for e in over:
            e.draw(fr, t)

    def _layer(self, fr, L, t, f):
        base = dict(L)
        pose = pose_at(base, L.get('keys'), f)
        if pose['alpha'] <= 0.01:
            return
        if 'card' in L:
            fnt = font('pop_b', L.get('size', 44))
            spr, ox, oy, tw, th = text_sprite(L['card'], fnt, (255, 250, 240, 255), shadow=0)
            ic = emoji(L['icon'], 64) if L.get('icon') else None
            iw = (ic.width + 24) if ic else 0
            cw, ch = max(L.get('cw', 0), tw + iw + 80), max(th + 56, 110)
            from gfx import rrect
            card, pad = rrect((int(cw), int(ch)), 30, (12, 10, 14, 225), outline=tuple(L.get('col', (255, 214, 70))) + (220,), width=4)
            if ic:
                paste(card, ic, pad + 30, pad + ch / 2 - ic.height / 2)
            paste(card, spr, pad + 40 + iw - ox, pad + ch / 2 - th / 2 - oy)
            card = drop_shadow(card, (0, 14), 14, 150)
            paste_c(fr, card, pose['x'], pose['y'], pose['alpha'], pose['scale'])
            return
        if 'text' in L:
            txt = L['text']
            for at, val in L.get('swap', []):
                if f >= at:
                    txt = val
            fnt = font(L.get('font', 'osw'), int(L.get('size', 90) * pose['scale']))
            spr, ox, oy, tw, th = text_sprite(txt, fnt, tuple(L.get('col', (255, 255, 255))) + (255,), shadow=L.get('shadow', 0.6),
                                              blur=8, stroke=L.get('stroke', 0))
            if L.get('glow'):
                paste_c(fr, glow(int(max(tw, th) * .6), tuple(L['glow'])), pose['x'], pose['y'], 0.5 * pose['alpha'])
            paste(fr, spr, pose['x'] - tw / 2 - ox, pose['y'] - th / 2 - oy, pose['alpha'])
            return
        name = L['img']
        for at, val in L.get('swap', []):
            if f >= at:
                name = val
        w = int(L.get('w', 600) * pose['scale'])
        p = self.path(name)
        if L.get('shadow', True):
            im = shadowed(p, w, bool(L.get('flip')))
        else:
            im = sized(p, w, bool(L.get('flip')))
        rot = pose['rot'] + L.get('wiggle', 0) * math.sin(t * L.get('wspeed', 3.0)) + L.get('spin', 0) * t
        if abs(rot) > 0.05:
            im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
        x = pose['x'] + L.get('drift', [0, 0])[0] * t
        y = pose['y'] + L.get('drift', [0, 0])[1] * t + L.get('bob', 0) * math.sin(t * 2.2)
        if L.get('glow'):
            paste_c(fr, glow(int(w * .45), tuple(L['glow'])), x, y, 0.55 * pose['alpha'])
        paste_c(fr, im, x, y, pose['alpha'])

    def offset(self, t):
        """camera shake offset (applied by the renderer)."""
        for s in self.shake:
            t0 = s.get('t', 0) * self.dur
            d = s.get('d', 0.4)
            if t0 <= t <= t0 + d:
                k = 1 - (t - t0) / d
                a = s.get('amp', 14) * k
                return a * math.sin(t * 90), a * math.cos(t * 70)
        return 0, 0


def needed_images(v):
    names = set()
    b = v.get('bg') or {}
    if b.get('img'):
        names.add(b['img'])
    for e in b.get('seq') or []:
        names.add(e[0])
    for L in v.get('layers') or []:
        if 'img' in L:
            names.add(L['img'])
            for _, n in L.get('swap', []):
                names.add(n)
    return sorted(names)
