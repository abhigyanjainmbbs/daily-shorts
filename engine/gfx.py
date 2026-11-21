"""Drawing primitives: fonts, text sprites, pseudo-3D shading (spheres, inflated shapes), glows."""
import math, os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, 'assets', 'fonts')
W, H = 1080, 1920

CREAM = (255, 246, 230)
GOLD = (242, 193, 78)

PALETTES = {
    # bg top, bg bottom, paper layer, accent, accent2, text
    'ember': dict(bg0=(26, 12, 10), bg1=(70, 22, 16), paper=(120, 44, 30), acc=(255, 110, 70), acc2=(242, 193, 78)),
    'ocean': dict(bg0=(6, 16, 30), bg1=(14, 48, 78), paper=(28, 82, 120), acc=(90, 200, 255), acc2=(242, 193, 78)),
    'mint':  dict(bg0=(6, 24, 20), bg1=(14, 62, 52), paper=(30, 104, 86), acc=(110, 240, 190), acc2=(255, 214, 120)),
    'plum':  dict(bg0=(20, 8, 28), bg1=(58, 20, 72), paper=(98, 40, 118), acc=(230, 130, 255), acc2=(255, 200, 110)),
    'sand':  dict(bg0=(34, 26, 16), bg1=(92, 66, 38), paper=(150, 112, 70), acc=(255, 170, 90), acc2=(255, 236, 170)),
    # warm 'story' palettes (alternate per scene)
    'amber': dict(bg0=(120, 70, 10), bg1=(214, 150, 40), paper=(170, 104, 24), acc=(255, 120, 60), acc2=(255, 240, 200)),
    'teal':  dict(bg0=(6, 40, 40), bg1=(24, 110, 100), paper=(16, 80, 72), acc=(120, 255, 220), acc2=(255, 230, 150)),
    'violet': dict(bg0=(26, 10, 52), bg1=(76, 36, 130), paper=(54, 24, 96), acc=(200, 120, 255), acc2=(255, 220, 140)),
    'navy':  dict(bg0=(8, 14, 40), bg1=(30, 52, 120), paper=(20, 36, 86), acc=(110, 180, 255), acc2=(255, 220, 140)),
    'crimson': dict(bg0=(40, 4, 12), bg1=(120, 20, 40), paper=(90, 14, 30), acc=(255, 90, 90), acc2=(255, 220, 160)),
    'soil':  dict(bg0=(30, 18, 8), bg1=(92, 60, 30), paper=(70, 44, 20), acc=(200, 120, 255), acc2=(255, 220, 150)),
}

KW_COLS = {'red': (255, 72, 60), 'purple': (196, 120, 255), 'green': (150, 255, 90), 'yellow': (255, 214, 70),
           'blue': (110, 190, 255), 'orange': (255, 140, 50), 'white': (255, 250, 240)}


@lru_cache(maxsize=64)
def font(name, size):
    files = {
        'lora': 'Lora-Variable.ttf', 'lora_i': 'Lora-Italic-Variable.ttf',
        'pop_b': 'Poppins-Bold.ttf', 'pop_m': 'Poppins-Medium.ttf', 'emoji': 'NotoColorEmoji.ttf',
        'osw': 'Oswald-Bold.woff', 'osw_s': 'Oswald-SemiBold.woff',
    }
    f = ImageFont.truetype(os.path.join(FONTS, files[name]), size)
    if name.startswith('lora'):
        try:
            f.set_variation_by_name('SemiBold')
        except Exception:
            pass
    return f


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t, t0, d):
    if d <= 0:
        return 1.0 if t >= t0 else 0.0
    x = clamp((t - t0) / d)
    return 1 - (1 - x) ** 3


def window(t, a, b, fi=0.15, fo=0.15):
    if t < a or t > b:
        return 0.0
    k = 1.0
    if fi > 0:
        k = min(k, (t - a) / fi)
    if fo > 0:
        k = min(k, (b - t) / fo)
    return clamp(k)


def with_alpha(im, k):
    if k >= 0.999:
        return im
    a = im.getchannel('A').point(lambda v: int(v * k))
    out = im.copy()
    out.putalpha(a)
    return out


def paste(dst, src, x, y, k=1.0):
    if k <= 0.003:
        return
    if k < 0.999:
        src = with_alpha(src, k)
    x, y = int(round(x)), int(round(y))
    sw, sh = src.size
    dw, dh = dst.size
    if x >= dw or y >= dh or x + sw <= 0 or y + sh <= 0:
        return
    cx0, cy0 = max(0, -x), max(0, -y)
    cx1, cy1 = min(sw, dw - x), min(sh, dh - y)
    if cx0 or cy0 or cx1 < sw or cy1 < sh:
        src = src.crop((cx0, cy0, cx1, cy1))
    dst.alpha_composite(src, (x + cx0, y + cy0))


def paste_c(dst, src, cx, cy, k=1.0, scale=1.0):
    if scale != 1.0:
        w, h = max(1, int(src.width * scale)), max(1, int(src.height * scale))
        src = src.resize((w, h), Image.BILINEAR)
    paste(dst, src, cx - src.width / 2, cy - src.height / 2, k)


# ---------------------------------------------------------------- text
_TS = {}


def text_sprite(txt, fnt, fill=(255, 255, 255, 255), stroke=0, stroke_fill=(0, 0, 0, 255),
                shadow=0.85, blur=10, glow=None, spacing=0):
    """Returns RGBA sprite with padding; (img, ox, oy, tw, th) where ox,oy = offset of text box in img."""
    key = (txt, id(fnt), fill, stroke, stroke_fill, shadow, blur, glow, spacing)
    if key in _TS:
        return _TS[key]
    d0 = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
    if spacing:
        widths = [d0.textlength(c, font=fnt) for c in txt]
        tw = int(sum(widths) + spacing * (len(txt) - 1))
    else:
        tw = int(d0.textlength(txt, font=fnt))
    asc, desc = fnt.getmetrics()
    th = asc + desc
    pad = int(blur * 3 + 10 + stroke + (glow[1] * 3 if glow else 0))
    W_, H_ = tw + 2 * pad, th + 2 * pad
    layer = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    def draw_text(dd, fill_, sw=0, sf=None):
        if spacing:
            x = pad
            for c in txt:
                dd.text((x, pad), c, font=fnt, fill=fill_, stroke_width=sw, stroke_fill=sf)
                x += dd.textlength(c, font=fnt) + spacing
        else:
            dd.text((pad, pad), txt, font=fnt, fill=fill_, stroke_width=sw, stroke_fill=sf)

    out = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
        draw_text(ImageDraw.Draw(sh), (0, 0, 0, int(255 * shadow)), stroke + 2, (0, 0, 0, int(255 * shadow)))
        sh = sh.filter(ImageFilter.GaussianBlur(blur))
        out.alpha_composite(sh, (0, 4))
    if glow:
        col, r = glow
        g = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
        draw_text(ImageDraw.Draw(g), col + (230,), stroke + 3, col + (230,))
        g = g.filter(ImageFilter.GaussianBlur(r))
        out.alpha_composite(g)
        out.alpha_composite(g)
    draw_text(d, fill, stroke, stroke_fill)
    out.alpha_composite(layer)
    res = (out, pad, pad, tw, th)
    _TS[key] = res
    return res


def emoji(ch, size):
    key = ('emo', ch, size)
    if key in _TS:
        return _TS[key]
    f = font('emoji', 109)
    im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((8, 8), ch, font=f, embedded_color=True)
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    s = size / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    _TS[key] = im
    return im


def rrect(size, r, fill, outline=None, width=0, pad=6):
    w, h = size
    im = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + w, pad + h), r, fill=fill, outline=outline, width=width)
    return im, pad


def pill(text, size=40, bg=(12, 10, 8, 215), fg=CREAM + (255,), outline=GOLD + (190,), icon=None, padx=34):
    key = ('pill', text, size, bg, fg, outline, icon)
    if key in _TS:
        return _TS[key]
    spr, ox, oy, tw, th = text_sprite(text, font('pop_b', size), fg, shadow=0)
    icw = 0
    ic = None
    if icon:
        ic = emoji(icon, int(size * 1.05))
        icw = ic.width + 14
    h = int(size * 1.9)
    w = tw + 2 * padx + icw
    im, pad = rrect((w, h), h // 2, bg, outline=outline, width=3)
    # soft drop shadow
    sh = Image.new('RGBA', (im.width + 40, im.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 28, 20 + w + 2 * pad - 12, 28 + h + 2 * pad - 12), h // 2, fill=(0, 0, 0, 140))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    sh.alpha_composite(im, (20, 20))
    im = sh
    x = 20 + pad + padx
    if ic is not None:
        paste(im, ic, x, 20 + pad + (h - ic.height) / 2)
        x += icw
    paste(im, spr, x - ox, 20 + pad + (h - th) / 2 - oy)
    _TS[key] = im
    return im


# ---------------------------------------------------------------- 3D-ish shading
_SPH = {}


def sphere(r, col, spec=0.7):
    key = (int(r), tuple(col), spec)
    if key in _SPH:
        return _SPH[key]
    r = max(2, int(r))
    s = 2 * r + 4
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32) - (r + 2)
    d = np.sqrt(xx ** 2 + yy ** 2) / r
    z = np.sqrt(np.clip(1 - d ** 2, 0, 1))
    L = np.array([-0.45, -0.6, 0.66]); L /= np.linalg.norm(L)
    lam = np.clip((xx / r) * L[0] + (yy / r) * L[1] + z * L[2], 0, 1)
    hv = np.array([L[0], L[1], L[2] + 1]); hv /= np.linalg.norm(hv)
    sp = np.clip((xx / r) * hv[0] + (yy / r) * hv[1] + z * hv[2], 0, 1) ** 40
    rim = np.clip(1 - z, 0, 1) ** 3
    shade = 0.18 + 0.82 * lam
    c = np.array(col, np.float32)
    rgb = c[None, None, :] * shade[..., None] + 255 * sp[..., None] * spec + np.array([40, 60, 90])[None, None, :] * rim[..., None]
    a = np.clip((1 - d) * r, 0, 1)
    im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8), 'RGBA')
    _SPH[key] = im
    return im


def inflate(mask, col, depth=1.0, spec=0.45, gloss=30, blur=None, rim_col=(255, 255, 255)):
    """Turn a 2D mask (L image) into a glossy puffy 3D-looking RGBA sprite."""
    m = np.asarray(mask, np.float32) / 255.0
    h, w = m.shape
    r = blur or max(6, int(min(h, w) * 0.09))
    hb = np.asarray(mask.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255.0
    height = np.sqrt(np.clip(hb, 0, 1)) * m * depth * r * 1.6
    gy, gx = np.gradient(height)
    nz = 1.0 / np.sqrt(gx ** 2 + gy ** 2 + 1)
    nx, ny = -gx * nz, -gy * nz
    L = np.array([-0.45, -0.62, 0.64]); L /= np.linalg.norm(L)
    lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    hv = np.array([L[0], L[1], L[2] + 1]); hv /= np.linalg.norm(hv)
    sp = np.clip(nx * hv[0] + ny * hv[1] + nz * hv[2], 0, 1) ** gloss
    edge = np.clip(1 - nz, 0, 1) ** 2
    c = np.array(col, np.float32)
    rgb = c[None, None, :] * (0.22 + 0.9 * lam[..., None]) + 255 * spec * sp[..., None] \
        + np.array(rim_col, np.float32)[None, None, :] * 0.12 * edge[..., None]
    rgb = np.clip(rgb, 0, 255)
    a = np.clip(m, 0, 1) * 255
    return Image.fromarray(np.dstack([rgb, a]).astype(np.uint8), 'RGBA')


def drop_shadow(sprite, off=(0, 18), blur=18, alpha=150):
    pad = blur * 2 + max(abs(off[0]), abs(off[1]))
    out = Image.new('RGBA', (sprite.width + 2 * pad, sprite.height + 2 * pad), (0, 0, 0, 0))
    a = sprite.getchannel('A').point(lambda v: int(v * alpha / 255))
    sh = Image.new('RGBA', sprite.size, (0, 0, 0, 0))
    sh.putalpha(a)
    tmp = Image.new('RGBA', out.size, (0, 0, 0, 0))
    tmp.alpha_composite(sh, (pad + off[0], pad + off[1]))
    tmp = tmp.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(tmp)
    out.alpha_composite(sprite, (pad, pad))
    return out


_GLOW = {}


def glow(r, col, a=255):
    key = (int(r), tuple(col), a)
    if key not in _GLOW:
        r = int(r)
        s = r * 4
        im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        ImageDraw.Draw(im).ellipse((r, r, 3 * r, 3 * r), fill=tuple(col) + (a,))
        _GLOW[key] = im.filter(ImageFilter.GaussianBlur(r * 0.6))
    return _GLOW[key]


def molecule(fr, atoms, cx, cy, r, ang, k=1.0):
    """atoms: list of (rgb, radius_factor). Linear molecule rotating about vertical axis."""
    if k <= 0.01:
        return
    n = len(atoms)
    bond = r * 1.55
    pts = []
    for j, (col, rf) in enumerate(atoms):
        off = (j - (n - 1) / 2) * bond
        x = cx + off * math.cos(ang)
        z = off / max(bond, 1) * math.sin(ang)
        s = 1 + 0.12 * z
        pts.append((z, x, cy - z * r * 0.1, r * rf * s, col))
    pts.sort(key=lambda p: p[0])
    for z, x, y, rr, col in pts:
        spr = sphere(max(3, rr), col)
        paste(fr, spr, x - spr.width / 2, y - spr.height / 2, k)


MOLS = {
    'O2': [((70, 170, 255), 1.0), ((70, 170, 255), 1.0)],
    'CO': [((52, 52, 58), 0.95), ((150, 150, 160), 1.0)],
    'CO2': [((150, 150, 160), 0.9), ((52, 52, 58), 0.95), ((150, 150, 160), 0.9)],
    'H2O': [((240, 240, 250), 0.7), ((230, 60, 60), 1.0), ((240, 240, 250), 0.7)],
    'GLU': [((255, 200, 90), 0.9), ((255, 230, 140), 0.8), ((255, 200, 90), 0.9), ((255, 230, 140), 0.8)],
    'NA': [((170, 120, 255), 1.0)],
    'K': [((255, 140, 200), 1.0)],
    'DRUG': [((120, 230, 160), 0.9), ((240, 240, 250), 0.7), ((120, 230, 160), 0.9)],
    'TOXIN': [((120, 200, 40), 1.0), ((60, 90, 20), 0.85), ((120, 200, 40), 1.0)],
    'FAT': [((255, 214, 90), 1.0), ((255, 190, 60), 0.9)],
}


# ---------------------------------------------------------------- film look overlays
_OV = {}


def film_overlay():
    """Vignette + paper crease (static)."""
    if 'v' in _OV:
        return _OV['v']
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W * .5) / (W * .62)) ** 2 + ((yy - H * .45) / (H * .62)) ** 2)
    a = np.clip(d - 0.35, 0, 1) ** 1.6 * 235
    im = Image.fromarray(np.dstack([np.zeros_like(a), np.zeros_like(a), np.zeros_like(a), a]).astype(np.uint8), 'RGBA')
    # crease: soft dark line + light highlight next to it, slightly right of centre
    cx = int(W * 0.6)
    cr = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(cr)
    dd.rectangle((cx - 2, 0, cx + 1, H), fill=(0, 0, 0, 70))
    dd.rectangle((cx + 2, 0, cx + 5, H), fill=(255, 255, 255, 26))
    cr = cr.filter(ImageFilter.GaussianBlur(2.2))
    im.alpha_composite(cr)
    _OV['v'] = im
    return im


def grain(i):
    k = i % 4
    if ('g', k) not in _OV:
        rnd = np.random.RandomState(100 + k)
        n = rnd.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
        a = np.clip(np.abs(n) * 7, 0, 16)
        g = np.where(n > 0, 255, 0).astype(np.uint8)
        im = Image.fromarray(np.dstack([g, g, g, a.astype(np.uint8)]), 'RGBA').resize((W, H), Image.NEAREST)
        _OV[('g', k)] = im
    return _OV[('g', k)]


def keywords(fr, t, kicker, punch, col, t_k, t_p):
    """Two-tier top-left keyword text: small white kicker + big coloured punch line."""
    x0, y0 = 70, 210
    if kicker and t >= t_k:
        f = font('osw_s', 62)
        spr, ox, oy, tw, th = text_sprite(kicker.upper(), f, (255, 250, 240, 255), stroke=2, stroke_fill=(0, 0, 0, 200),
                                          shadow=0.9, blur=7)
        k = ease(t, t_k, 0.12)
        paste(fr, spr, x0 - ox + (1 - k) * -30, y0 - oy, k)
    if punch and t >= t_p:
        size = 118
        f = font('osw', size)
        d0 = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
        while d0.textlength(punch, font=f) > 940 and size > 60:
            size -= 6
            f = font('osw', size)
        spr, ox, oy, tw, th = text_sprite(punch, f, tuple(col) + (255,), stroke=3, stroke_fill=(0, 0, 0, 220),
                                          shadow=0.95, blur=10)
        k = ease(t, t_p, 0.1)
        s = 1 + 0.22 * (1 - ease(t, t_p, 0.16))
        if s > 1.001:
            spr = spr.resize((int(spr.width * s), int(spr.height * s)), Image.BILINEAR)
            ox, oy = ox * s, oy * s
        paste(fr, spr, x0 - ox, y0 + 78 - oy, k)


def source_card(fr, text, k=1.0):
    f = font('pop_m', 30)
    spr, ox, oy, tw, th = text_sprite(text, f, (40, 30, 20, 255), shadow=0)
    card, pad = rrect((tw + 60, th + 34), 10, (250, 240, 214, 235), outline=(120, 90, 50, 200), width=2)
    paste(card, spr, pad + 30 - ox, pad + 17 - oy)
    card = card.rotate(-2, expand=True, resample=Image.BICUBIC)
    paste(fr, card, 70, 1180, k)
