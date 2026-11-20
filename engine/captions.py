"""Roman-Hinglish captions with *gold* hot words, timed proportionally inside each scene."""
import re
from PIL import Image
from gfx import font, text_sprite, paste, CREAM, GOLD, ease, W

CAP_Y = 1330
MAXW = 960


def chunks(cap):
    cap = cap.strip()
    if not cap:
        return []
    if ' / ' in cap:
        parts = [p.strip() for p in cap.split(' / ') if p.strip()]
    else:
        words = cap.split()
        parts, cur = [], []
        for w_ in words:
            cur.append(w_)
            if len(cur) >= 6 or w_.endswith(('.', '?', '!', ',', '—')) and len(cur) >= 3:
                parts.append(' '.join(cur)); cur = []
        if cur:
            if parts and len(cur) <= 2:
                parts[-1] += ' ' + ' '.join(cur)
            else:
                parts.append(' '.join(cur))
    return parts


def tokens(line):
    out = []
    for m in re.finditer(r'\*([^*]+)\*|(\S+)', line):
        if m.group(1):
            for w_ in m.group(1).split():
                out.append((w_, True))
        else:
            out.append((m.group(2), False))
    return out


_CACHE = {}


def line_sprites(text):
    if text in _CACHE:
        return _CACHE[text]
    f = font('lora', 66)
    toks = tokens(text)
    sprites = []
    for w_, hot in toks:
        col = GOLD + (255,) if hot else CREAM + (255,)
        spr = text_sprite(w_, f, col, stroke=3, stroke_fill=(0, 0, 0, 230), shadow=0.9, blur=8)
        sprites.append(spr)
    # layout into lines
    space = 18
    lines, cur, curw = [], [], 0
    for s in sprites:
        tw = s[3]
        if cur and curw + space + tw > MAXW:
            lines.append((cur, curw)); cur, curw = [], 0
        cur.append(s); curw += (space if len(cur) > 1 else 0) + tw
    if cur:
        lines.append((cur, curw))
    _CACHE[text] = lines
    return lines


class SceneCaptions:
    def __init__(self, cap, t0, t1):
        parts = chunks(cap)
        total = sum(max(len(p), 6) for p in parts) or 1
        self.items = []
        t = t0
        span = max(t1 - t0, 0.3)
        for p in parts:
            d = span * max(len(p), 6) / total
            self.items.append((t, t + d, p))
            t += d

    def draw(self, fr, t):
        for a, b, txt in self.items:
            if a <= t < b:
                lines = line_sprites(txt)
                nwords = sum(len(l[0]) for l in lines)
                reveal = max(1, int(nwords * min(1.0, (t - a) / max(0.35 * (b - a), 0.15))) + 1)
                y = CAP_Y - (len(lines) - 1) * 44
                k_all = ease(t, a, 0.08)
                idx = 0
                for ws, lw in lines:
                    x = W / 2 - lw / 2
                    for (spr, ox, oy, tw, th) in ws:
                        k = k_all if idx < reveal else 0.0
                        lift = 0 if idx < reveal - 1 else 6 * (1 - ease(t, a, 0.1))
                        paste(fr, spr, x - ox, y - th / 2 - oy - lift, k)
                        x += tw + 18
                        idx += 1
                    y += 88
                return
