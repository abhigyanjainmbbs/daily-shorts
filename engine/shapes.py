"""Code-drawn 3D-looking organs, cells and a glass body. All original shapes (no copyrighted art)."""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from gfx import inflate, sphere, drop_shadow

SS = 2  # supersample for masks


def _mask(w, h):
    m = Image.new('L', (w * SS, h * SS), 0)
    return m, ImageDraw.Draw(m)


def _done(m, w, h):
    return m.resize((w, h), Image.LANCZOS)


def _tube(d, pts, r):
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / (r * 0.4)))
        for k in range(n + 1):
            t = k / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            d.ellipse((x - r, y - r, x + r, y + r), fill=255)


def _bez(p0, p1, p2, p3, n=40):
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 3; b = 3 * (1 - t) ** 2 * t; c = 3 * (1 - t) * t ** 2; e = t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + e * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + e * p3[1]))
    return out


def _S(v):
    return v * SS


ORGAN_COL = {
    'heart': (205, 38, 52), 'brain': (238, 150, 168), 'lungs': (236, 118, 138), 'kidney': (168, 58, 66),
    'liver': (150, 48, 38), 'stomach': (238, 140, 118), 'intestine': (236, 158, 136), 'bone': (238, 230, 208),
    'pancreas': (240, 190, 120), 'thyroid': (200, 88, 100), 'eye': (245, 245, 250), 'bladder': (230, 200, 120),
    'skin': (232, 170, 140), 'blood': (190, 20, 34), 'tooth': (245, 245, 240), 'uterus': (230, 120, 140),
}


@lru_cache(maxsize=32)
def organ(name, size=560):
    """Returns RGBA sprite (with shadow) of a stylised 3D organ, roughly size x size."""
    w = h = size
    m, d = _mask(w, h)
    S = lambda *v: [x * SS for x in v]
    col = ORGAN_COL.get(name, (220, 120, 120))
    detail = None
    if name == 'heart':
        body = Image.new('L', (w * SS, h * SS), 0)
        bd = ImageDraw.Draw(body)
        bd.ellipse(S(w * .16, h * .3, w * .8, h * .82), fill=255)
        bd.polygon([(_S(w * .2), _S(h * .62)), (_S(w * .42), _S(h * .96)), (_S(w * .62), _S(h * .76))], fill=255)
        body = body.rotate(-18, resample=Image.BICUBIC, center=(_S(w * .48), _S(h * .56)))
        m.paste(255, (0, 0), body)
        d = ImageDraw.Draw(m)
        _tube(d, _bez((_S(w * .5), _S(h * .38)), (_S(w * .48), _S(h * .08)), (_S(w * .82), _S(h * .04)), (_S(w * .8), _S(h * .3))), _S(w * .058))
        _tube(d, _bez((_S(w * .38), _S(h * .4)), (_S(w * .34), _S(h * .24)), (_S(w * .22), _S(h * .2)), (_S(w * .16), _S(h * .26))), _S(w * .05))
        detail = 'heart'
    elif name == 'brain':
        d.ellipse(S(w * .08, h * .18, w * .92, h * .78), fill=255)
        d.ellipse(S(w * .52, h * .58, w * .84, h * .84), fill=255)
        _tube(d, [(_S(w * .55), _S(h * .7)), (_S(w * .5), _S(h * .95))], _S(w * .05))
        detail = 'brain'
    elif name == 'lungs':
        d.rounded_rectangle(S(w * .06, h * .22, w * .44, h * .92), _S(w * .17), fill=255)
        d.rounded_rectangle(S(w * .56, h * .22, w * .94, h * .92), _S(w * .17), fill=255)
        _tube(d, [(_S(w * .5), _S(h * .02)), (_S(w * .5), _S(h * .3))], _S(w * .045))
        detail = 'lungs'
    elif name == 'kidney':
        d.ellipse(S(w * .22, h * .08, w * .78, h * .92), fill=255)
        d.ellipse(S(w * .6, h * .38, w * .9, h * .62), fill=0)
        detail = 'kidney'
    elif name == 'liver':
        d.polygon([(_S(x * w), _S(y * h)) for x, y in [(.05, .4), (.2, .2), (.6, .18), (.95, .3), (.85, .5), (.5, .78), (.25, .8), (.08, .62)]], fill=255)
    elif name == 'stomach':
        pts = _bez((_S(w * .3), _S(h * .08)), (_S(w * .3), _S(h * .55)), (_S(w * .5), _S(h * .95)), (_S(w * .88), _S(h * .62)))
        rads = [w * (0.07 + 0.13 * math.sin(math.pi * i / len(pts))) for i in range(len(pts))]
        for (x, y), r in zip(pts, rads):
            r = _S(r)
            d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    elif name == 'intestine':
        r = w * .07
        pts = []
        for row in range(4):
            y = h * (.2 + row * .2)
            xs = [w * .15, w * .85] if row % 2 == 0 else [w * .85, w * .15]
            pts += [(_S(xs[0]), _S(y)), (_S(xs[1]), _S(y))]
        _tube(d, pts, _S(r))
    elif name == 'bone':
        _tube(d, [(_S(w * .22), _S(h * .78)), (_S(w * .78), _S(h * .22))], _S(w * .07))
        for cx, cy in [(.15, .74), (.26, .86), (.74, .14), (.86, .26)]:
            r = _S(w * .1)
            d.ellipse((_S(w * cx) - r, _S(h * cy) - r, _S(w * cx) + r, _S(h * cy) + r), fill=255)
    elif name == 'pancreas':
        pts = _bez((_S(w * .1), _S(h * .55)), (_S(w * .35), _S(h * .3)), (_S(w * .65), _S(h * .65)), (_S(w * .92), _S(h * .42)))
        for i, (x, y) in enumerate(pts):
            r = _S(w * (0.12 - 0.07 * i / len(pts)))
            d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    elif name == 'thyroid':
        d.ellipse(S(w * .1, h * .25, w * .45, h * .85), fill=255)
        d.ellipse(S(w * .55, h * .25, w * .9, h * .85), fill=255)
        d.rectangle(S(w * .35, h * .55, w * .65, h * .7), fill=255)
    elif name == 'bladder':
        d.ellipse(S(w * .15, h * .15, w * .85, h * .85), fill=255)
    elif name == 'uterus':
        d.polygon([(_S(x * w), _S(y * h)) for x, y in [(.2, .2), (.8, .2), (.62, .7), (.56, .92), (.44, .92), (.38, .7)]], fill=255)
        _tube(d, [(_S(w * .22), _S(h * .22)), (_S(w * .05), _S(h * .12))], _S(w * .035))
        _tube(d, [(_S(w * .78), _S(h * .22)), (_S(w * .95), _S(h * .12))], _S(w * .035))
    elif name == 'tooth':
        d.rounded_rectangle(S(w * .2, h * .1, w * .8, h * .55), _S(w * .15), fill=255)
        d.polygon([(_S(w * .22), _S(h * .45)), (_S(w * .35), _S(h * .92)), (_S(w * .48), _S(h * .5))], fill=255)
        d.polygon([(_S(w * .52), _S(h * .5)), (_S(w * .65), _S(h * .92)), (_S(w * .78), _S(h * .45))], fill=255)
    elif name in ('eye', 'blood', 'skin'):
        d.ellipse(S(w * .12, h * .12, w * .88, h * .88), fill=255)
    else:
        d.ellipse(S(w * .15, h * .15, w * .85, h * .85), fill=255)
    mask = _done(m, w, h)
    spr = inflate(mask, col, spec=0.5, gloss=28)
    det = Image.new('RGBA', spr.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(det)
    if detail == 'brain':
        rnd = np.random.RandomState(4)
        for i in range(14):
            x0 = w * (.15 + .65 * rnd.rand()); y0 = h * (.25 + .4 * rnd.rand())
            pts = [(x0 + j * w * .035, y0 + math.sin(j * 1.3 + i) * h * .025) for j in range(6)]
            dd.line(pts, fill=(150, 70, 95, 170), width=max(3, w // 110), joint='curve')
        dd.line([(w * .5, h * .2), (w * .48, h * .45)], fill=(150, 70, 95, 140), width=max(3, w // 100))
    elif detail == 'heart':
        dd.line([(w * .48, h * .42), (w * .44, h * .6), (w * .52, h * .8)], fill=(140, 20, 30, 170), width=max(3, w // 90), joint='curve')
        dd.line([(w * .6, h * .4), (w * .66, h * .62)], fill=(240, 200, 60, 120), width=max(2, w // 140))
    elif detail == 'lungs':
        for sx in (1, -1):
            cx = w * .5
            pts = [(cx, h * .3), (cx - sx * w * .1, h * .42), (cx - sx * w * .2, h * .6)]
            dd.line(pts, fill=(160, 60, 80, 160), width=max(3, w // 100), joint='curve')
    elif detail == 'kidney':
        dd.line([(w * .62, h * .5), (w * .82, h * .55), (w * .9, h * .8)], fill=(120, 30, 40, 190), width=max(4, w // 70))
    da = np.asarray(det.getchannel('A'), np.float32) * (np.asarray(mask.filter(ImageFilter.MinFilter(9)), np.float32) / 255.0)
    det.putalpha(Image.fromarray(da.astype(np.uint8)))
    spr.alpha_composite(det)
    if name == 'eye':
        ir = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(ir).ellipse((w * .34, h * .34, w * .66, h * .66), fill=(60, 120, 200, 255))
        ImageDraw.Draw(ir).ellipse((w * .43, h * .43, w * .57, h * .57), fill=(10, 10, 14, 255))
        ImageDraw.Draw(ir).ellipse((w * .46, h * .42, w * .52, h * .48), fill=(255, 255, 255, 230))
        spr.alpha_composite(ir)
    return drop_shadow(spr, off=(0, int(size * .04)), blur=int(size * .035), alpha=150)


@lru_cache(maxsize=32)
def cell(kind, size=160):
    w = h = size
    if kind == 'rbc':
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        u = (xx - w / 2) / (w / 2); v = (yy - h / 2) / (h * 0.36); rr = np.sqrt(u * u + v * v)
        m = rr < 1
        hgt = np.where(m, 0.55 + 0.45 * np.sin(np.clip(rr, 0, 1) * math.pi * 0.92) ** 1.2 - 0.25 * np.exp(-(rr / 0.38) ** 2), 0)
        gy, gx = np.gradient(hgt * 30)
        nz = 1 / np.sqrt(gx ** 2 + gy ** 2 + 1); nx = -gx * nz; ny = -gy * nz
        L = np.array([-0.4, -0.65, 0.65]); L /= np.linalg.norm(L)
        lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
        base = np.array([196, 28, 40], np.float32)
        rgb = base[None, None, :] * (0.25 + 0.85 * lam[..., None]) + 255 * 0.35 * (lam ** 25)[..., None]
        a = np.clip((1 - rr) * min(w, h) * 0.25, 0, 1) * m * 255
        return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a]).astype(np.uint8), 'RGBA')
    m, d = _mask(w, h)
    if kind == 'rod':
        d.rounded_rectangle((_S(w * .08), _S(h * .32), _S(w * .92), _S(h * .68)), _S(h * .18), fill=255)
        return inflate(_done(m, w, h), (120, 200, 90), spec=0.55)
    if kind == 'cocci':
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        for cx, cy in [(.3, .4), (.55, .35), (.45, .62), (.7, .6)]:
            s = sphere(w * .16, (150, 110, 230))
            out.alpha_composite(s, (int(w * cx - s.width / 2), int(h * cy - s.height / 2)))
        return out
    if kind == 'virus':
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        dd = ImageDraw.Draw(out)
        for i in range(14):
            a = i / 14 * 2 * math.pi
            x0, y0 = w / 2 + math.cos(a) * w * .3, h / 2 + math.sin(a) * h * .3
            x1, y1 = w / 2 + math.cos(a) * w * .45, h / 2 + math.sin(a) * h * .45
            dd.line([(x0, y0), (x1, y1)], fill=(200, 80, 90, 255), width=max(2, w // 40))
            dd.ellipse((x1 - w * .04, y1 - w * .04, x1 + w * .04, y1 + w * .04), fill=(240, 120, 120, 255))
        s = sphere(w * .32, (220, 70, 80))
        out.alpha_composite(s, (int(w / 2 - s.width / 2), int(h / 2 - s.height / 2)))
        return out
    if kind == 'wbc':
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        s = sphere(w * .42, (235, 235, 245), spec=0.5)
        out.alpha_composite(s, (int(w / 2 - s.width / 2), int(h / 2 - s.height / 2)))
        for cx, cy in [(.42, .45), (.58, .5), (.48, .6)]:
            n = sphere(w * .1, (130, 80, 190), spec=0.3)
            out.alpha_composite(n, (int(w * cx - n.width / 2), int(h * cy - n.height / 2)))
        return out
    if kind == 'platelet':
        d.polygon([(_S(x * w), _S(y * h)) for x, y in [(.2, .4), (.45, .25), (.75, .35), (.8, .6), (.5, .75), (.25, .65)]], fill=255)
        return inflate(_done(m, w, h), (230, 180, 200), spec=0.4)
    if kind == 'fat':
        return sphere(w * .45, (255, 214, 90), spec=0.6)
    if kind == 'neuron':
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        dd = ImageDraw.Draw(out)
        rnd = np.random.RandomState(2)
        for i in range(7):
            a = rnd.rand() * 2 * math.pi
            dd.line([(w / 2, h / 2), (w / 2 + math.cos(a) * w * .45, h / 2 + math.sin(a) * h * .45)], fill=(255, 210, 120, 220), width=max(2, w // 45))
        s = sphere(w * .18, (255, 190, 90))
        out.alpha_composite(s, (int(w / 2 - s.width / 2), int(h / 2 - s.height / 2)))
        return out
    return sphere(w * .4, (200, 200, 220))


# Body: glass figure, front view. Coordinates relative to a 760x1500 box.
BODY_W, BODY_H = 760, 1500
ORGAN_POS = {  # (x, y, size) inside body box
    'brain': (380, 130, 190), 'eye': (380, 150, 80), 'thyroid': (380, 300, 90), 'lungs': (380, 470, 330),
    'heart': (410, 500, 170), 'liver': (320, 640, 220), 'stomach': (460, 650, 170), 'pancreas': (400, 720, 170),
    'kidney': (380, 760, 120), 'intestine': (380, 870, 260), 'bladder': (380, 1000, 110), 'uterus': (380, 990, 140),
    'bone': (300, 1200, 220), 'blood': (380, 600, 500), 'skin': (380, 700, 650), 'tooth': (380, 190, 70),
}


@lru_cache(maxsize=4)
def glass_body(tint=(120, 170, 230)):
    w, h = BODY_W, BODY_H
    m, d = _mask(w, h)
    S = lambda v: v * SS
    d.ellipse((S(290), S(20), S(470), S(230)), fill=255)                 # head
    d.rounded_rectangle((S(340), S(200), S(420), S(300)), S(30), fill=255)  # neck
    d.rounded_rectangle((S(200), S(270), S(560), S(980)), S(150), fill=255)  # torso
    _tube(d, [(S(215), S(330)), (S(130), S(640)), (S(110), S(900))], S(52))  # arms
    _tube(d, [(S(545), S(330)), (S(630), S(640)), (S(650), S(900))], S(52))
    _tube(d, [(S(300), S(930)), (S(285), S(1220)), (S(280), S(1460))], S(70))  # legs
    _tube(d, [(S(460), S(930)), (S(475), S(1220)), (S(480), S(1460))], S(70))
    mask = _done(m, w, h)
    spr = inflate(mask, tint, spec=0.35, gloss=18, blur=40)
    a = np.asarray(spr.getchannel('A'), np.float32)
    # glass: semi transparent centre, brighter edges
    edge = np.asarray(mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(6)), np.float32)
    a = np.clip(a * 0.42 + edge * 2.2, 0, 255)
    spr.putalpha(Image.fromarray(a.astype(np.uint8)))
    return spr
