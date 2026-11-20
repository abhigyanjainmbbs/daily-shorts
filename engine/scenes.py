"""Scene library. Each scene draws onto an RGBA frame for local time t in [0, dur]."""
import math, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from gfx import (W, H, CREAM, GOLD, PALETTES, font, text_sprite, emoji, pill, paste, paste_c, ease, window,
                 clamp, sphere, molecule, MOLS, glow, rrect, with_alpha, drop_shadow)
from shapes import organ, cell, glass_body, ORGAN_POS, BODY_W, BODY_H


# ---------------------------------------------------------------- backgrounds
@lru_cache(maxsize=8)
def background(pal_name, seed=1):
    p = PALETTES[pal_name]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    t = yy / H
    c0, c1 = np.array(p['bg0'], np.float32), np.array(p['bg1'], np.float32)
    rgb = c0[None, None, :] * (1 - t[..., None]) + c1[None, None, :] * t[..., None]
    # radial light
    d = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .42) / H) ** 2)
    rgb *= (1.15 - 0.9 * d)[..., None]
    rnd = np.random.RandomState(seed)
    rgb += rnd.normal(0, 4, rgb.shape[:2])[..., None]  # paper grain
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    # paper-cut layers (wavy hills) at the bottom and top, with shadows
    paper = np.array(p['paper'])
    for li, (base, amp, shade) in enumerate([(H * .88, 60, 0.55), (H * .93, 45, 0.8), (H * .08, 50, 0.5)]):
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        ph = rnd.rand() * 6
        pts = []
        for x in range(0, W + 41, 40):
            y = base + amp * math.sin(x / 170 + ph) + amp * .4 * math.sin(x / 63 + ph * 2)
            pts.append((x, y))
        if base > H / 2:
            poly = pts + [(W, H), (0, H)]
        else:
            poly = pts + [(W, 0), (0, 0)]
        col = tuple(int(c * shade) for c in paper) + (255,)
        dd.polygon(poly, fill=col)
        sh = lay.filter(ImageFilter.GaussianBlur(14))
        shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        shadow.paste((0, 0, 0, 255), (0, 0), sh.getchannel('A'))
        paste(im, with_alpha(shadow, 0.55), 0, -12 if base > H / 2 else 12)
        im.alpha_composite(lay)
    # vignette
    v = np.clip(d * 1.25, 0, 1) ** 2 * 170
    vig = Image.fromarray(np.dstack([np.zeros_like(v), np.zeros_like(v), np.zeros_like(v), v]).astype(np.uint8), 'RGBA')
    im.alpha_composite(vig)
    return im


_BOKEH = None


def bokeh(fr, t, col):
    global _BOKEH
    if _BOKEH is None:
        r = random.Random(7)
        _BOKEH = [(r.uniform(0, W), r.uniform(0, H), r.uniform(6, 22), r.uniform(10, 40), r.uniform(0, 6)) for _ in range(26)]
    for x, y, rad, sp, ph in _BOKEH:
        yy = (y - t * sp) % H
        xx = x + math.sin(t * 0.5 + ph) * 20
        paste_c(fr, glow(int(rad), col, 150), xx, yy, 0.35)


def label_top(fr, t, dur, text, icon=None, y=300, pal=None):
    if not text:
        return
    k = window(t, 0.1, dur - 0.05, 0.2, 0.15)
    sp = pill(text, size=40, icon=icon)
    s = 0.85 + 0.15 * ease(t, 0.1, 0.25)
    paste_c(fr, sp, W / 2, y, k, s)


def big_text(fr, t, txt, y, size=110, col=CREAM, glow_col=None, t0=0.0, slam=True, fnt='pop_b', k=1.0, spacing=0):
    if t < t0:
        return
    spr, ox, oy, tw, th = text_sprite(txt, font(fnt, size), col + (255,), shadow=0.85, blur=12,
                                      glow=(glow_col, 14) if glow_col else None, spacing=spacing, stroke=2)
    s = 1 + 0.35 * (1 - ease(t, t0, 0.18)) if slam else 1.0
    kk = k * ease(t, t0, 0.12)
    paste_c(fr, spr, W / 2, y, kk, s)


def wrap(txt, fnt, maxw):
    d = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
    words, lines, cur = txt.split(), [], ''
    for w_ in words:
        cand = (cur + ' ' + w_).strip()
        if d.textlength(cand, font=fnt) <= maxw or not cur:
            cur = cand
        else:
            lines.append(cur); cur = w_
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- scene types
class Scene:
    def __init__(self, spec, dur, pal, seed):
        self.v = spec.get('visual', {})
        self.dur = dur
        self.pal = PALETTES[pal]
        self.acc = tuple(self.pal['acc'])
        self.acc2 = tuple(self.pal['acc2'])
        self.rnd = random.Random(seed)
        self.setup()

    def setup(self):
        pass

    def draw(self, fr, t):
        pass


class Title(Scene):
    def setup(self):
        v = self.v
        self.lines = wrap(v.get('title', '').upper(), font('pop_b', 118), 980)[:3]
        self.conf = [(self.rnd.uniform(0, W), self.rnd.uniform(-200, H * .5), self.rnd.uniform(-1, 1), self.rnd.uniform(30, 90),
                      self.rnd.choice([self.acc, self.acc2, CREAM])) for _ in range(16)]

    def draw(self, fr, t):
        v = self.v
        # paper confetti falling
        for i, (x, y0, rot, sz, col) in enumerate(self.conf):
            y = y0 + t * 240 + i * 7
            k = clamp(1 - t / max(self.dur, 0.1)) * 0.8
            im = Image.new('RGBA', (int(sz), int(sz * .6)), col + (255,))
            im = im.rotate(rot * 140 * t + i * 30, expand=True, resample=Image.BICUBIC)
            paste(fr, im, x, y % (H + 200) - 100, k)
        if v.get('kicker'):
            sp = pill(v['kicker'].upper(), size=38)
            paste_c(fr, sp, W / 2, 600, ease(t, 0.05, 0.25))
        n = len(self.lines)
        y0 = 860 - (n - 1) * 70
        for i, ln in enumerate(self.lines):
            big_text(fr, t, ln, y0 + i * 140, size=118, col=CREAM if i else self.acc2, glow_col=self.acc, t0=0.12 + i * 0.12)
        if v.get('sub'):
            spr, ox, oy, tw, th = text_sprite(v['sub'], font('lora_i', 56), CREAM + (240,), shadow=0.8, blur=8)
            paste_c(fr, spr, W / 2, y0 + n * 140 + 20, ease(t, 0.45, 0.3))
        if v.get('emoji'):
            e = emoji(v['emoji'], 150)
            bob = math.sin(t * 3) * 10
            paste_c(fr, e, W / 2, 400 + bob, ease(t, 0.3, 0.3))


class Counter(Scene):
    def setup(self):
        self.val = str(self.v.get('value', '0'))
        self.prefix = self.v.get('prefix', '')
        self.suffix = self.v.get('suffix', '')

    def draw(self, fr, t):
        txt = self.val
        n = len(txt)
        cw, ch = min(170, int(900 / max(n, 1))), 250
        total = n * cw + (n - 1) * 16
        x0 = W / 2 - total / 2
        fnt = font('pop_b', int(ch * 0.62))
        for i, c in enumerate(txt):
            settle = 0.25 + i * 0.18 + 0.6
            if c.isdigit() and t < settle:
                shown = str(int((t * 23 + i * 3)) % 10)
                flip = (t * 23) % 1
            else:
                shown, flip = c, 0
            card, pad = rrect((cw, ch), 22, (18, 16, 20, 240), outline=self.acc + (200,), width=3)
            dd = ImageDraw.Draw(card)
            dd.line((pad + 6, pad + ch / 2, pad + cw - 6, pad + ch / 2), fill=(0, 0, 0, 255), width=4)
            spr, ox, oy, tw, th = text_sprite(shown, fnt, CREAM + (255,), shadow=0, blur=2)
            paste(card, spr, pad + cw / 2 - tw / 2 - ox, pad + ch / 2 - th / 2 - oy - 8)
            sy = 1 - 0.25 * math.sin(flip * math.pi) if flip else 1
            if sy != 1:
                card = card.resize((card.width, max(1, int(card.height * sy))))
            paste(fr, drop_shadow(card, (0, 14), 14, 160), x0 + i * (cw + 16) - 34, 760 - card.height / 2 - 34, ease(t, 0.05 + i * 0.06, 0.2))
        if self.prefix:
            big_text(fr, t, self.prefix, 560, size=64, col=self.acc2, slam=False, t0=0.1)
        if self.suffix:
            big_text(fr, t, self.suffix, 990, size=70, col=self.acc2, glow_col=self.acc, t0=0.25 + n * 0.18 + 0.5)
        if self.v.get('label'):
            big_text(fr, t, self.v['label'].upper(), 1100, size=50, col=CREAM, slam=False, t0=0.6, spacing=3)


class Molecules(Scene):
    def setup(self):
        kinds = self.v.get('kinds') or ['O2']
        self.items = []
        for i in range(int(self.v.get('count', 16))):
            k = kinds[i % len(kinds)]
            self.items.append(dict(k=k, x=self.rnd.uniform(80, W - 80), y=self.rnd.uniform(380, 1250), r=self.rnd.uniform(24, 46),
                                   vx=self.rnd.uniform(-40, 40), vy=self.rnd.uniform(-30, 30), ph=self.rnd.uniform(0, 6)))
        self.items.sort(key=lambda d: d['r'])

    def draw(self, fr, t):
        mode = self.v.get('mode', 'float')
        for i, m in enumerate(self.items):
            x = m['x'] + m['vx'] * t + math.sin(t * 1.3 + m['ph']) * 30
            y = m['y'] + m['vy'] * t + math.cos(t * 1.1 + m['ph']) * 24
            if mode == 'rise':
                y = 1350 - ((t * 160 + m['ph'] * 180) % 1100)
            elif mode == 'swarm':
                cx, cy = W / 2, 820
                a = t * 0.9 + m['ph']
                rr = 120 + m['r'] * 6
                x, y = cx + math.cos(a) * rr * 1.4, cy + math.sin(a) * rr
            k = ease(t, i * 0.04, 0.3)
            molecule(fr, MOLS.get(m['k'], MOLS['O2']), x, y, m['r'], t * 1.6 + m['ph'], k)
        lab = self.v.get('label')
        if lab:
            big_text(fr, t, lab.upper(), 330, size=80, col=self.acc2, glow_col=self.acc, t0=0.2)


class Cells(Scene):
    def setup(self):
        kind = self.v.get('kind', 'rbc')
        self.items = []
        for i in range(int(self.v.get('count', 18))):
            z = self.rnd.uniform(0.4, 1.0)
            self.items.append(dict(x=self.rnd.uniform(-200, W + 200), y=self.rnd.uniform(360, 1300), z=z,
                                   sp=self.rnd.uniform(120, 260) * z, ph=self.rnd.uniform(0, 6), rot=self.rnd.uniform(-30, 30)))
        self.items.sort(key=lambda d: d['z'])
        self.kind = kind

    def draw(self, fr, t):
        base = cell(self.kind, 200)
        flow = self.v.get('flow', True)
        for m in self.items:
            x = (m['x'] + (m['sp'] * t if flow else 0) + 200) % (W + 400) - 200
            y = m['y'] + math.sin(t * 1.4 + m['ph']) * 22
            s = 0.45 + 0.75 * m['z']
            im = base.rotate(m['rot'] + t * 20 * (1 if m['ph'] > 3 else -1), resample=Image.BICUBIC, expand=True)
            if m['z'] < 0.6:
                im = im.filter(ImageFilter.GaussianBlur(3))
            paste_c(fr, im, x, y, 0.55 + 0.45 * m['z'], s)
        hl = self.v.get('highlight')
        if hl:
            e = cell(hl, 320)
            pul = 1 + 0.05 * math.sin(t * 6)
            paste_c(fr, glow(150, self.acc), W / 2, 820, 0.6)
            paste_c(fr, e, W / 2, 820, ease(t, 0.2, 0.3), pul)
        if self.v.get('label'):
            label_top(fr, t, self.dur, self.v['label'].upper())


class Body(Scene):
    def draw(self, fr, t):
        org = self.v.get('organ', 'heart')
        state = self.v.get('state', 'pulse')
        body = glass_body()
        p = ease(t, 0.2, max(self.dur - 0.4, 0.5))
        scale = (1180 / BODY_H) * (1 + 0.35 * p)
        ox, oy, osz = ORGAN_POS.get(org, (380, 500, 200))
        # organ screen position moves from its natural place toward (W/2, 760)
        nat_x = W / 2 + (ox - BODY_W / 2) * (1180 / BODY_H)
        nat_y = 840 + (oy - BODY_H / 2) * (1180 / BODY_H)
        px_t = nat_x + (W / 2 - nat_x) * p
        py_t = nat_y + (760 - nat_y) * p
        cx = px_t - (ox - BODY_W / 2) * scale
        cy = py_t - (oy - BODY_H / 2) * scale
        bx, by = cx - BODY_W * scale / 2, cy - BODY_H * scale / 2
        paste_c(fr, body, cx, cy, ease(t, 0, 0.25), scale)
        px, py = bx + ox * scale, by + oy * scale
        col = {'alarm': (255, 60, 50), 'dim': (120, 140, 170), 'heal': (90, 240, 150)}.get(state, self.acc)
        pul = 0.75 + 0.25 * math.sin(t * (9 if state == 'alarm' else 5))
        k_glow = 1.0
        if state == 'dim':
            k_glow = 1 - 0.8 * ease(t, 0.4, max(self.dur - 0.6, 0.5))
        g = glow(int(osz * scale * 0.9), col)
        paste_c(fr, g, px, py, 0.9 * pul * k_glow)
        osprite = organ(org, 300)
        paste_c(fr, osprite, px, py, ease(t, 0.15, 0.25), osz * scale / 300 * (1 + 0.04 * math.sin(t * 6)))
        if self.v.get('label'):
            label_top(fr, t, self.dur, self.v['label'].upper(), icon=self.v.get('icon'))


class Organ(Scene):
    def draw(self, fr, t):
        org = self.v.get('organ', 'heart')
        eff = self.v.get('effect', 'pulse')
        sp = organ(org, 600)
        s = 1.0
        if eff == 'pulse' or org == 'heart':
            beat = (t * 1.3) % 1
            s = 1 + 0.06 * math.exp(-beat * 9)
        if eff == 'shrink':
            s *= 1 - 0.25 * ease(t, 0.4, max(self.dur - 0.8, 0.5))
        rot = math.sin(t * 1.4) * 4
        im = sp.rotate(rot, resample=Image.BICUBIC, expand=False)
        col = {'alarm': (255, 60, 50), 'heal': (90, 240, 150)}.get(eff, self.acc)
        paste_c(fr, glow(260, col), W / 2, 800, 0.45 + 0.2 * math.sin(t * 4))
        paste_c(fr, im, W / 2, 800, ease(t, 0, 0.25), s)
        if eff == 'crack':
            p = ease(t, 0.4, max(self.dur * 0.6, 0.4))
            dd = ImageDraw.Draw(fr)
            pts = [(W / 2 - 40, 560), (W / 2 + 10, 660), (W / 2 - 30, 760), (W / 2 + 30, 860), (W / 2 - 10, 980)]
            n = max(2, int(len(pts) * p))
            dd.line(pts[:n], fill=(20, 10, 10, 255), width=12, joint='curve')
        if eff in ('attack', 'alarm') or self.v.get('particles'):
            kind = self.v.get('particles', 'TOXIN')
            for i in range(10):
                a = i / 10 * 2 * math.pi + t * 0.6
                rr = 520 - ((t * 180 + i * 50) % 300)
                if kind in MOLS:
                    molecule(fr, MOLS[kind], W / 2 + math.cos(a) * rr, 800 + math.sin(a) * rr * 1.1, 26, t * 3 + i, 0.9)
                else:
                    paste_c(fr, cell(kind, 110), W / 2 + math.cos(a) * rr, 800 + math.sin(a) * rr * 1.1, 0.95)
        if self.v.get('label'):
            big_text(fr, t, self.v['label'].upper(), 1140, size=76, col=self.acc2, glow_col=self.acc, t0=0.25)


class Vessel(Scene):
    def setup(self):
        self.items = [dict(x=self.rnd.uniform(0, W + 300), y=self.rnd.uniform(-130, 130), z=self.rnd.uniform(.6, 1), ph=self.rnd.uniform(0, 6))
                      for _ in range(22)]

    def draw(self, fr, t):
        cy = 820
        block = float(self.v.get('blockage', 0))
        p_block = ease(t, 0.3, max(self.dur * 0.6, 0.5)) * block
        # vessel walls
        wall = Image.new('RGBA', (W, 520), (0, 0, 0, 0))
        dd = ImageDraw.Draw(wall)
        dd.rounded_rectangle((-40, 10, W + 40, 510), 200, fill=(150, 30, 45, 120))
        dd.rounded_rectangle((-40, 70, W + 40, 450), 170, fill=(60, 6, 14, 200))
        paste(fr, wall, 0, cy - 260)
        # plaque
        if block > 0:
            for i, x in enumerate([380, 520, 660]):
                r = 40 + 150 * p_block * (1 - abs(i - 1) * 0.35)
                pl = sphere(r, (250, 214, 110), spec=0.4)
                paste_c(fr, pl, x, cy - 190 + r * 0.35)
                paste_c(fr, pl, x + 30, cy + 190 - r * 0.35)
        speed = 340 * (1 - 0.85 * p_block)
        kind = self.v.get('cells', 'rbc')
        base = cell(kind, 150)
        for m in self.items:
            x = (m['x'] + speed * t) % (W + 300) - 150
            y = cy + m['y'] * (1 - 0.6 * p_block if 300 < x < 760 else 1) + math.sin(t * 2 + m['ph']) * 10
            im = base.rotate(t * 40 + m['ph'] * 30, resample=Image.BICUBIC, expand=True)
            paste_c(fr, im, x, y, 0.95, 0.6 + 0.4 * m['z'])
        if self.v.get('label'):
            label_top(fr, t, self.dur, self.v['label'].upper(), y=470)


class Steps(Scene):
    def draw(self, fr, t):
        items = self.v.get('items', [])[:5]
        icons = self.v.get('icons', [])
        if self.v.get('title'):
            big_text(fr, t, self.v['title'].upper(), 380, size=84, col=self.acc2, glow_col=self.acc, t0=0.0)
        n = max(1, len(items))
        span = max(self.dur - 0.6, 0.6)
        for i, it in enumerate(items):
            t0 = 0.25 + span * i / n
            k = ease(t, t0, 0.25)
            if k <= 0:
                continue
            fnt = font('pop_b', 42)
            lines = wrap(it, fnt, 720)[:2]
            ch = 70 + 52 * len(lines)
            card, pad = rrect((900, ch), 28, (14, 12, 16, 225), outline=self.acc + (190,), width=3)
            num, ox, oy, tw, th = text_sprite(str(i + 1), font('pop_b', 58), self.acc2 + (255,), shadow=0)
            paste(card, num, pad + 36 - ox, pad + ch / 2 - th / 2 - oy)
            x = pad + 110
            if i < len(icons) and icons[i]:
                e = emoji(icons[i], 56)
                paste(card, e, x, pad + ch / 2 - e.height / 2)
                x += 76
            for j, ln in enumerate(lines):
                spr, ox2, oy2, tw2, th2 = text_sprite(ln, fnt, CREAM + (255,), shadow=0)
                paste(card, spr, x - ox2, pad + 34 + j * 52 - oy2)
            y = 520 + i * (ch + 30) if n <= 3 else 480 + i * (ch + 18)
            paste(fr, drop_shadow(card, (0, 12), 12, 150), 90 - 30 - 6 + (1 - k) * 120, y - 30, k)


class Versus(Scene):
    def draw(self, fr, t):
        v = self.v
        half = self.dur * 0.45
        for i, (title, text, col, ok) in enumerate([(v.get('left_title', 'MYTH'), v.get('left_text', ''), (235, 80, 70), False),
                                                    (v.get('right_title', 'FACT'), v.get('right_text', ''), (80, 220, 140), True)]):
            t0 = 0.1 if i == 0 else half
            k = ease(t, t0, 0.25)
            if k <= 0:
                continue
            fnt = font('pop_b', 44)
            lines = wrap(text, fnt, 760)[:3]
            ch = 150 + 56 * len(lines)
            card, pad = rrect((920, ch), 30, (14, 12, 16, 230), outline=col + (230,), width=4)
            dd = ImageDraw.Draw(card)
            # tick / cross drawn
            cx, cy = pad + 70, pad + 70
            if ok:
                dd.line([(cx - 26, cy), (cx - 6, cy + 22), (cx + 30, cy - 24)], fill=col + (255,), width=12, joint='curve')
            else:
                dd.line([(cx - 24, cy - 24), (cx + 24, cy + 24)], fill=col + (255,), width=12)
                dd.line([(cx - 24, cy + 24), (cx + 24, cy - 24)], fill=col + (255,), width=12)
            spr, ox, oy, tw, th = text_sprite(title.upper(), font('pop_b', 54), col + (255,), shadow=0)
            paste(card, spr, pad + 130 - ox, pad + 70 - th / 2 - oy)
            for j, ln in enumerate(lines):
                s2, ox2, oy2, tw2, th2 = text_sprite(ln, fnt, CREAM + (255,), shadow=0)
                paste(card, s2, pad + 50 - ox2, pad + 140 + j * 56 - oy2)
            y0 = int(v.get('y', 420))
            y = y0 if i == 0 else y0 + ch + 60
            if i == 0 and t > half:
                k *= 0.55
            paste(fr, drop_shadow(card, (0, 12), 12, 150), 80 - 30 - 6, y - 30, k)


class Timeline(Scene):
    def draw(self, fr, t):
        pts = self.v.get('points', [])[:5]
        n = max(1, len(pts))
        dd = ImageDraw.Draw(fr)
        top, bot = 420, 1250
        p = ease(t, 0.1, max(self.dur * 0.8, 0.5))
        dd.line([(230, top), (230, top + (bot - top) * p)], fill=self.acc + (255,), width=8)
        for i, (when, what) in enumerate(pts):
            y = top + (bot - top) * (i + 0.5) / n
            t0 = 0.1 + (self.dur * 0.8) * (i + 0.5) / n
            k = ease(t, t0 - 0.15, 0.25)
            if k <= 0:
                continue
            paste_c(fr, sphere(26, self.acc2), 230, y, k)
            s1, ox, oy, tw, th = text_sprite(when.upper(), font('pop_b', 46), self.acc2 + (255,), shadow=0.8, blur=6)
            paste(fr, s1, 290 - ox, y - 62 - oy, k)
            for j, ln in enumerate(wrap(what, font('pop_m', 40), 700)[:2]):
                s2, ox2, oy2, tw2, th2 = text_sprite(ln, font('pop_m', 40), CREAM + (255,), shadow=0.8, blur=6)
                paste(fr, s2, 290 - ox2, y - 4 + j * 48 - oy2, k)
        if self.v.get('title'):
            label_top(fr, t, self.dur, self.v['title'].upper())


class Taxi(Scene):
    """Haemoglobin 'taxi' with 4 seats; start kinds -> end kinds swapped one by one."""
    def draw(self, fr, t):
        start = self.v.get('start', ['O2'] * 4)
        end = self.v.get('end', start)
        rbc = cell('rbc', 700)
        cx, cy = W / 2 - 700 * (1 - ease(t, 0, 0.8)), 830
        paste_c(fr, rbc, cx, cy)
        seats = [(-190, -62), (190, -62), (-190, 72), (190, 72)]
        span = max(self.dur - 1.2, 0.8)
        for j, (sx, sy) in enumerate(seats):
            swap_t = 0.8 + span * (j + 0.5) / 4
            kind = end[j] if (t >= swap_t and end != start) else start[j]
            wx, wy = cx + sx, cy + sy
            well, pad = rrect((96, 70), 34, (70, 6, 12, 210), outline=(255, 170, 170, 120), width=3)
            paste_c(fr, well, wx, wy + 8)
            molecule(fr, MOLS.get(kind, MOLS['O2']), wx, wy - 6 + math.sin(t * 3 + j) * 4, 30, t * 1.6 + j)
            if end != start and swap_t <= t < swap_t + 1.2:
                p = (t - swap_t) / 1.2
                molecule(fr, MOLS.get(start[j], MOLS['O2']), wx - 260 * p, wy - 380 * p, 30, t * 6, 1 - p)
            if end != start and swap_t - 0.7 <= t < swap_t:
                p = ease(t, swap_t - 0.7, 0.7)
                x0, y0 = 1250, wy - 300
                molecule(fr, MOLS.get(end[j], MOLS['CO']), x0 + (wx - x0) * p, y0 + (wy - y0) * p, 30, t * 5)
        if self.v.get('label'):
            big_text(fr, t, self.v['label'].upper(), 420, size=72, col=self.acc2, glow_col=self.acc, t0=0.1)


TYPES = {'title': Title, 'counter': Counter, 'molecules': Molecules, 'cells': Cells, 'body': Body, 'organ': Organ,
         'vessel': Vessel, 'steps': Steps, 'versus': Versus, 'timeline': Timeline, 'taxi': Taxi}


def make(spec, dur, pal, seed):
    typ = spec.get('visual', {}).get('type', 'title')
    return TYPES.get(typ, Title)(spec, dur, pal, seed)
