"""Extra 3D scene types (infection / toxin stories): nail, soil, drumstick, spore, wound, toxin, nerve, antibody, spasm."""
import math, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from gfx import (W, H, CREAM, font, text_sprite, paste, paste_c, ease, window, clamp, sphere, molecule, MOLS, glow,
                 rrect, inflate, drop_shadow, emoji)
from shapes import glass_body, BODY_W, BODY_H, cell, _tube, SS
from scenes import Scene, big_text, label_top

PURPLE = (150, 70, 230)       # Gram-positive (crystal violet) stain colour
SPORE = (245, 236, 210)
TOXIN = (140, 240, 60)


def _mask(w, h):
    m = Image.new('L', (w * SS, h * SS), 0)
    return m, ImageDraw.Draw(m)


def _done(m, w, h):
    return m.resize((w, h), Image.LANCZOS)


@lru_cache(maxsize=8)
def drumstick(length=520, col=PURPLE):
    """C. tetani: slender rod with a round terminal spore (the 'drumstick' appearance)."""
    w, h = length + 40, int(length * 0.32)
    m, d = _mask(w, h)
    r = h * 0.17
    d.rounded_rectangle((20 * SS, (h / 2 - r) * SS, (w - h * 0.55) * SS, (h / 2 + r) * SS), int(r * SS), fill=255)
    rod = inflate(_done(m, w, h), col, spec=0.55, gloss=26)
    sp = sphere(h * 0.3, SPORE, spec=0.6)
    rod.alpha_composite(sp, (int(w - h * 0.62 - sp.width / 2 + h * 0.18), int(h / 2 - sp.height / 2)))
    return rod


@lru_cache(maxsize=4)
def nail_sprite(length=900, rust=True):
    w, h = length, 150
    m, d = _mask(w, h)
    S = lambda v: int(v * SS)
    d.rounded_rectangle((S(60), S(h / 2 - 20), S(w - 120), S(h / 2 + 20)), S(18), fill=255)       # shaft
    d.polygon([(S(w - 122), S(h / 2 - 20)), (S(w - 10), S(h / 2)), (S(w - 122), S(h / 2 + 20))], fill=255)  # tip
    d.rounded_rectangle((S(20), S(10), S(80), S(h - 10)), S(14), fill=255)                         # head
    mask = _done(m, w, h)
    spr = inflate(mask, (150, 150, 158), spec=0.8, gloss=40)
    if rust:
        rnd = np.random.RandomState(3)
        rl = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        dd = ImageDraw.Draw(rl)
        for _ in range(70):
            x = rnd.uniform(40, w - 160); y = rnd.uniform(h / 2 - 24, h / 2 + 24); r = rnd.uniform(5, 18)
            dd.ellipse((x - r, y - r * .7, x + r, y + r * .7), fill=(150 + int(rnd.rand() * 60), 60 + int(rnd.rand() * 30), 20, 210))
        rl = rl.filter(ImageFilter.GaussianBlur(1.5))
        a = np.asarray(rl.getchannel('A'), np.float32) * (np.asarray(mask, np.float32) / 255)
        rl.putalpha(Image.fromarray(a.astype(np.uint8)))
        spr.alpha_composite(rl)
    return drop_shadow(spr, (0, 26), 16, 170)


@lru_cache(maxsize=2)
def plank():
    w, h = 1400, 560
    rnd = np.random.RandomState(5)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    grain = np.sin(yy / 9 + np.sin(xx / 140) * 3) * 0.5 + 0.5
    base = np.array([150, 96, 52], np.float32)
    rgb = base[None, None, :] * (0.7 + 0.35 * grain[..., None]) + rnd.normal(0, 6, (h, w))[..., None]
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    dd = ImageDraw.Draw(im)
    for y in (180, 370):
        dd.line((0, y, w, y), fill=(60, 34, 16, 255), width=6)
    return im


class Nail(Scene):
    def draw(self, fr, t):
        v = self.v
        ground = v.get('on', 'wood')
        if ground == 'soil':
            mound = Image.new('RGBA', (W + 200, 600), (0, 0, 0, 0))
            dd = ImageDraw.Draw(mound)
            dd.ellipse((-100, 120, W + 300, 900), fill=(74, 46, 22, 255))
            rnd = random.Random(2)
            for _ in range(160):
                x, y, r = rnd.uniform(0, W + 200), rnd.uniform(160, 600), rnd.uniform(4, 14)
                c = rnd.choice([(96, 62, 30), (58, 36, 16), (120, 90, 60)])
                dd.ellipse((x - r, y - r, x + r, y + r), fill=c + (255,))
            paste(fr, mound, -100, 1020)
        else:
            pl = plank()
            paste(fr, pl.rotate(0), (W - pl.width) / 2, 1020)
        ang = -24 + 4 * math.sin(t * 0.8)
        sp = nail_sprite(rust=v.get('rust', True)).rotate(ang, expand=True, resample=Image.BICUBIC)
        s = 0.9 + 0.08 * ease(t, 0, self.dur)
        paste_c(fr, sp, W / 2, 900, ease(t, 0, 0.2), s)
        if v.get('flakes'):
            rnd = random.Random(9)
            for i in range(26):
                x0 = W / 2 + rnd.uniform(-330, 330); y0 = 880 + rnd.uniform(-90, 90)
                tt = (t * 0.9 + rnd.random()) % 1.6
                x, y = x0 + math.sin(tt * 4 + i) * 20, y0 + tt * 360
                sz = rnd.uniform(8, 18)
                fl = Image.new('RGBA', (int(sz * 2), int(sz)), (170, 74, 26, 255)).rotate(tt * 300 + i * 20, expand=True)
                paste_c(fr, fl, x, y, clamp(1.4 - tt) * ease(t, 0.3, 0.3))
        st = v.get('stamp')
        if st:
            t0 = v.get('stamp_at', 0.5) * self.dur
            if t >= t0:
                f = font('osw', 120)
                spr, ox, oy, tw, th = text_sprite(st.upper(), f, (235, 50, 40, 255), shadow=0)
                card, pad = rrect((tw + 80, th + 50), 16, (0, 0, 0, 0), outline=(235, 50, 40, 255), width=10)
                paste(card, spr, pad + 40 - ox, pad + 25 - oy)
                card = card.rotate(12, expand=True, resample=Image.BICUBIC)
                s2 = 1 + 0.6 * (1 - ease(t, t0, 0.15))
                paste_c(fr, card, W / 2 + 60, 760, ease(t, t0, 0.08), s2)


class Soil(Scene):
    def setup(self):
        self.peb = [(self.rnd.uniform(0, W), self.rnd.uniform(560, 1500), self.rnd.uniform(8, 30),
                     self.rnd.choice([(110, 80, 50), (80, 56, 30), (140, 112, 80), (60, 40, 20)])) for _ in range(140)]
        self.bugs = [(self.rnd.uniform(100, W - 100), self.rnd.uniform(650, 1350), self.rnd.uniform(0, 6), self.rnd.uniform(0.5, 1))
                     for _ in range(int(self.v.get('count', 7)))]

    def draw(self, fr, t):
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        dd.rectangle((0, 520, W, H), fill=(70, 44, 20, 255))
        dd.rectangle((0, 520, W, 600), fill=(46, 92, 34, 255))  # grass strip
        for i in range(60):
            x = i * 19 + (i % 3) * 5
            dd.line((x, 600, x + 6, 520 - (i % 5) * 12), fill=(70, 140, 50, 255), width=5)
        for x, y, r, c in self.peb:
            dd.ellipse((x - r, y - r * .7, x + r, y + r * .7), fill=c + (255,))
        paste(fr, lay, 0, -40 * ease(t, 0, self.dur))
        ds = drumstick(260)
        for i, (x, y, ph, z) in enumerate(self.bugs):
            g = 0.5 + 0.5 * math.sin(t * 3 + ph)
            paste_c(fr, glow(70, (190, 110, 255)), x, y - 40 * ease(t, 0, self.dur), 0.5 * g)
            paste_c(fr, ds.rotate(ph * 50 + t * 10, expand=True, resample=Image.BICUBIC), x, y - 40 * ease(t, 0, self.dur), ease(t, 0.2 + i * 0.08, 0.3), z)
        if self.v.get('label'):
            label_top(fr, t, self.dur, self.v['label'].upper(), y=470)


class Drumstick(Scene):
    """Microscope field with a big C. tetani (drumstick appearance)."""
    def draw(self, fr, t):
        # microscope circle
        R = 470
        circ = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(circ)
        dd.ellipse((W / 2 - R, 820 - R, W / 2 + R, 820 + R), fill=(250, 244, 226, 255))
        circ = circ.filter(ImageFilter.GaussianBlur(4))
        paste(fr, circ, 0, 0, ease(t, 0, 0.25))
        rnd = random.Random(4)
        small = drumstick(150)
        for i in range(9):
            a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(160, 400)
            x, y = W / 2 + math.cos(a) * rr, 820 + math.sin(a) * rr
            paste_c(fr, small.rotate(rnd.uniform(0, 360) + t * 8, expand=True, resample=Image.BICUBIC), x, y, 0.85 * ease(t, 0.1, 0.3))
        big = drumstick(560)
        paste_c(fr, glow(200, (190, 110, 255)), W / 2, 820, 0.35)
        paste_c(fr, big.rotate(-15 + 6 * math.sin(t * 0.9), expand=True, resample=Image.BICUBIC), W / 2, 820, ease(t, 0.15, 0.3),
                0.9 + 0.1 * ease(t, 0, self.dur))
        ring = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse((W / 2 - R, 820 - R, W / 2 + R, 820 + R), outline=(20, 20, 24, 255), width=26)
        paste(fr, ring, 0, 0, ease(t, 0, 0.25))
        if self.v.get('label'):
            big_text(fr, t, self.v['label'].upper(), 1380, size=60, col=(255, 230, 150), t0=0.4, slam=False)


class Spore(Scene):
    def draw(self, fr, t):
        mode = self.v.get('mode', 'armour')
        cx, cy = W / 2, 820
        if mode == 'boil':
            hot = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(hot).rectangle((0, 1100, W, H), fill=(255, 120, 30, 90))
            paste(fr, hot.filter(ImageFilter.GaussianBlur(60)), 0, 0)
            for i in range(26):
                ph = (t * 0.55 + i / 26) % 1
                x = 120 + (i * 137) % 840 + math.sin(ph * 6 + i) * 30
                y = 1350 - ph * 1000
                r = 10 + (i % 5) * 7 + ph * 12
                b = Image.new('RGBA', (int(r * 2 + 6), int(r * 2 + 6)), (0, 0, 0, 0))
                ImageDraw.Draw(b).ellipse((3, 3, r * 2 + 3, r * 2 + 3), outline=(220, 240, 255, 200), width=3)
                paste_c(fr, b, x, y, 0.9 * math.sin(ph * math.pi))
        if mode == 'oxygen':
            for i in range(16):
                a = i / 16 * 2 * math.pi + t * 0.5
                rr = 420 - 120 * ease(t, 0.3, self.dur * 0.6) + 20 * math.sin(t * 3 + i)
                molecule(fr, MOLS['O2'], cx + math.cos(a) * rr, cy + math.sin(a) * rr, 30, t * 2 + i)
        dim = 1.0
        if mode == 'oxygen':
            dim = 1 - 0.55 * ease(t, 0.5, self.dur * 0.6)
        col = tuple(int(c * dim + 120 * (1 - dim)) for c in SPORE)
        paste_c(fr, glow(210, (255, 230, 160)), cx, cy, 0.4 * dim)
        core = sphere(190, col, spec=0.6)
        paste_c(fr, core, cx, cy, ease(t, 0, 0.25), 1 + 0.02 * math.sin(t * 2))
        if mode in ('armour', 'boil'):
            # armour plates closing around the spore
            p = ease(t, 0.1, 0.9) if mode == 'armour' else 1.0
            for i in range(8):
                a = i / 8 * 2 * math.pi + 0.3
                rr = 215 + 260 * (1 - p)
                plate = Image.new('RGBA', (170, 120), (0, 0, 0, 0))
                ImageDraw.Draw(plate).rounded_rectangle((0, 0, 170, 120), 40, fill=(140, 150, 170, 255))
                plate = inflate(plate.getchannel('A'), (150, 160, 180), spec=0.7, gloss=30)
                plate = plate.rotate(-math.degrees(a) - 90, expand=True, resample=Image.BICUBIC)
                paste_c(fr, plate, cx + math.cos(a) * rr, cy + math.sin(a) * rr, 0.85 * p)
        if mode == 'oxygen' and t > self.dur * 0.55:
            k = ease(t, self.dur * 0.55, 0.2)
            dd = ImageDraw.Draw(fr)
            dd.line((cx - 150, cy - 150, cx + 150, cy + 150), fill=(255, 60, 50, int(255 * k)), width=22)
            dd.line((cx - 150, cy + 150, cx + 150, cy - 150), fill=(255, 60, 50, int(255 * k)), width=22)
        if self.v.get('label'):
            big_text(fr, t, self.v['label'].upper(), 1340, size=60, col=(255, 236, 190), t0=0.4, slam=False)


class Wound(Scene):
    """Skin cross-section with a deep puncture: air can't reach the bottom; spores wake there."""
    def draw(self, fr, t):
        top = 560
        layers = [(top, 50, (236, 190, 160)), (top + 50, 180, (230, 140, 140)), (top + 230, 230, (250, 214, 120)), (top + 460, 360, (170, 40, 50))]
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        for y, hgt, c in layers:
            dd.rectangle((0, y, W, y + hgt), fill=c + (255,))
            for k in range(0, W, 26):
                dd.line((k, y + 6, k + 12, y + hgt - 6), fill=tuple(int(v * 0.9) for v in c) + (120,), width=3)
        p = ease(t, 0.15, 0.9)
        depth = 620 * p
        # puncture channel
        dd.polygon([(W / 2 - 34, top), (W / 2 + 34, top), (W / 2 + 10, top + depth), (W / 2 - 10, top + depth)], fill=(40, 6, 10, 255))
        dd.ellipse((W / 2 - 70, top + depth - 50, W / 2 + 70, top + depth + 40), fill=(36, 4, 8, 255))
        paste(fr, lay, 0, 0)
        # O2 at surface bouncing off
        for i in range(9):
            x = 140 + i * 100
            y = top - 70 - 24 * abs(math.sin(t * 3 + i))
            molecule(fr, MOLS['O2'], x, y, 22, t * 2 + i)
        if p > 0.6:
            for j in range(3):
                g = 0.6 + 0.4 * math.sin(t * 5 + j)
                x = W / 2 - 40 + j * 40
                y = top + depth - 5
                paste_c(fr, glow(50, (190, 110, 255)), x, y, 0.8 * g)
                paste_c(fr, sphere(16, SPORE), x, y, ease(t, 0.9 + j * 0.1, 0.2))
        if self.v.get('label'):
            label_top(fr, t, self.dur, self.v['label'].upper(), y=470)


class Toxin(Scene):
    """Spore cracks -> rod grows -> green toxin clusters spread."""
    def setup(self):
        self.parts = [(self.rnd.uniform(0, 2 * math.pi), self.rnd.uniform(160, 480), self.rnd.uniform(0, 6)) for _ in range(18)]

    def draw(self, fr, t):
        cx, cy = W / 2, 820
        crack = ease(t, 0.3, 0.4)
        if crack < 1:
            paste_c(fr, sphere(150, SPORE), cx, cy, 1 - crack)
        for i in range(6):
            a = i / 6 * 2 * math.pi
            r = 150 * crack * 3
            sh = Image.new('RGBA', (90, 60), (0, 0, 0, 0))
            ImageDraw.Draw(sh).polygon([(0, 0), (90, 10), (40, 60)], fill=SPORE + (255,))
            paste_c(fr, sh.rotate(i * 60 + t * 200, expand=True), cx + math.cos(a) * r, cy + math.sin(a) * r, (1 - crack) if crack > 0.9 else crack)
        grow = ease(t, 0.5, 0.6)
        if grow > 0:
            rod = drumstick(int(200 + 360 * grow))
            paste_c(fr, rod.rotate(10 * math.sin(t), expand=True, resample=Image.BICUBIC), cx, cy, grow)
        spread = ease(t, 0.9, max(self.dur - 1.0, 0.5))
        for a, rr, ph in self.parts:
            if spread <= 0:
                break
            r = rr * spread
            x, y = cx + math.cos(a + t * 0.3) * r * 1.3, cy + math.sin(a + t * 0.3) * r
            paste_c(fr, glow(40, TOXIN), x, y, 0.7)
            paste_c(fr, sphere(22, TOXIN, spec=0.5), x, y, spread)
        if self.v.get('label'):
            big_text(fr, t, self.v['label'].upper(), 1340, size=64, col=TOXIN, t0=1.0, slam=True)


class Nerve(Scene):
    """Glass body; glowing poison path from the hand up the arm nerve to the spinal cord."""
    PATH = [(650, 900), (630, 640), (545, 330), (420, 300), (380, 330), (380, 620), (380, 900)]

    def draw(self, fr, t):
        body = glass_body()
        scale = 1180 / BODY_H
        cx, cy = W / 2, 840
        bx, by = cx - BODY_W * scale / 2, cy - BODY_H * scale / 2
        paste_c(fr, body, cx, cy, 1, scale)
        pts = [(bx + x * scale, by + y * scale) for x, y in self.PATH]
        dd = ImageDraw.Draw(fr)
        dd.line([(bx + 380 * scale, by + 300 * scale), (bx + 380 * scale, by + 950 * scale)], fill=(255, 240, 200, 150), width=10)  # spine
        p = ease(t, 0.2, max(self.dur * 0.8, 0.6))
        # cumulative lengths
        segs = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
        tot = sum(segs)
        dist = tot * p
        drawn = [pts[0]]
        acc = 0
        for i, L in enumerate(segs):
            if acc + L <= dist:
                drawn.append(pts[i + 1]); acc += L
            else:
                f = (dist - acc) / L
                drawn.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f))
                break
        if len(drawn) > 1:
            gl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(gl).line(drawn, fill=TOXIN + (255,), width=26, joint='curve')
            fr.alpha_composite(gl.filter(ImageFilter.GaussianBlur(12)))
            ImageDraw.Draw(fr).line(drawn, fill=(220, 255, 170, 255), width=8, joint='curve')
            hx, hy = drawn[-1]
            paste_c(fr, glow(40, TOXIN), hx, hy, 1)
        if self.v.get('label'):
            label_top(fr, t, self.dur, self.v['label'].upper(), y=470)


@lru_cache(maxsize=4)
def antibody(size=160, col=(80, 150, 255)):
    w = h = size
    m, d = _mask(w, h)
    S = lambda v: v * SS
    r = S(w * .07)
    _tube(d, [(S(w * .5), S(h * .95)), (S(w * .5), S(h * .5))], r)
    _tube(d, [(S(w * .5), S(h * .5)), (S(w * .18), S(h * .1))], r)
    _tube(d, [(S(w * .5), S(h * .5)), (S(w * .82), S(h * .1))], r)
    return inflate(_done(m, w, h), col, spec=0.6, gloss=30)


class Antibody(Scene):
    def setup(self):
        self.tox = [(self.rnd.uniform(160, W - 160), self.rnd.uniform(520, 1180), self.rnd.uniform(0, 6)) for _ in range(7)]

    def draw(self, fr, t):
        neut = ease(t, self.dur * 0.35, self.dur * 0.4)
        ab = antibody(150)
        for i, (x, y, ph) in enumerate(self.tox):
            col = tuple(int(TOXIN[k] * (1 - neut) + (120, 120, 120)[k] * neut) for k in range(3))
            paste_c(fr, glow(40, TOXIN), x, y, 0.6 * (1 - neut))
            paste_c(fr, sphere(30, col, spec=0.5), x, y)
            for j in range(3):
                a = j / 3 * 2 * math.pi + ph
                p = ease(t, 0.2 + i * 0.12, 0.8)
                rr = 400 * (1 - p) + 55
                ax, ay = x + math.cos(a) * rr, y + math.sin(a) * rr
                im = ab.rotate(-math.degrees(a) + 90, expand=True, resample=Image.BICUBIC)
                paste_c(fr, im, ax, ay, ease(t, 0.1 + i * 0.1, 0.2), 0.7)
        if self.v.get('syringe'):
            e = emoji('💉', 170)
            paste_c(fr, e, 200 + 60 * ease(t, 0, 0.6), 420, ease(t, 0, 0.3))
        if self.v.get('label'):
            big_text(fr, t, self.v['label'].upper(), 1340, size=60, col=(170, 210, 255), t0=0.4, slam=False)


class Spasm(Scene):
    """Glass body shaking with red tension lines (rigidity / spasms)."""
    def draw(self, fr, t):
        body = glass_body((200, 120, 120))
        scale = 1180 / BODY_H
        sh = 7 * math.sin(t * 40) * ease(t, 0.3, 0.5)
        cx, cy = W / 2 + sh, 840
        paste_c(fr, body, cx, cy, 1, scale)
        bx, by = cx - BODY_W * scale / 2, cy - BODY_H * scale / 2
        dd = ImageDraw.Draw(fr)
        rnd = random.Random(int(t * 12))
        zones = self.v.get('zones', ['jaw', 'neck', 'back', 'belly'])
        zpos = {'jaw': (380, 200), 'neck': (380, 280), 'back': (380, 520), 'belly': (380, 780), 'arms': (160, 600), 'legs': (300, 1200)}
        n = len(zones)
        for i, z in enumerate(zones):
            if t < self.dur * i / max(n, 1):
                continue
            zx, zy = zpos.get(z, (380, 500))
            x0, y0 = bx + zx * scale, by + zy * scale
            paste_c(fr, glow(70, (255, 50, 40)), x0, y0, 0.8)
            for k in range(3):
                pts = [(x0 - 80 + k * 30, y0 - 40)]
                for s in range(5):
                    pts.append((pts[-1][0] + rnd.uniform(10, 40), pts[-1][1] + rnd.uniform(-30, 30)))
                dd.line(pts, fill=(255, 80, 60, 230), width=5)
        if self.v.get('label'):
            label_top(fr, t, self.dur, self.v['label'].upper(), y=470)


EXTRA = {'nail': Nail, 'soil': Soil, 'drumstick': Drumstick, 'spore': Spore, 'wound': Wound, 'toxin': Toxin,
         'nerve': Nerve, 'antibody': Antibody, 'spasm': Spasm}
