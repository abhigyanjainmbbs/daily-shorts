"""Render a script's notes_md as a 1-page notes image (PNG + PDF) for DMs."""
import json, os, re, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import font

W, H = 1240, 1754
INK, ACC, PAPER, MUTED = (34, 28, 24), (176, 52, 36), (250, 245, 232), (120, 104, 90)


def runs(line):
    """split '**bold** and *italic*' into (text, style) runs"""
    out = []
    for part in re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*)', line):
        if not part:
            continue
        if part.startswith('**'):
            out.append((part[2:-2], 'b'))
        elif part.startswith('*'):
            out.append((part[1:-1], 'i'))
        else:
            out.append((part, 'r'))
    return out


def draw_wrapped(d, x, y, maxw, line, size=30, lh=1.42):
    F = {'r': font('pop_m', size), 'b': font('pop_b', size), 'i': font('lora_i', size + 2)}
    words = []
    for txt, st in runs(line):
        for w in re.split(r'(\s+)', txt):
            if w:
                words.append((w, st))
    cx = x
    for w, st in words:
        f = F[st]
        wl = d.textlength(w, font=f)
        if w.isspace():
            if cx > x:
                cx += wl
            continue
        if cx + wl > x + maxw and cx > x and not re.fullmatch(r'[.,;:)\]]+', w):
            cx = x
            y += int(size * lh)
        d.text((cx, y), w, font=f, fill=ACC if st == 'b' else INK)
        cx += wl
    return y + int(size * lh)


def render(script_path, out_png):
    s = json.load(open(script_path))
    md = s['notes_md'].replace('→', '»').strip().splitlines()
    im = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(im)
    for yy in range(250, H - 120, 46):
        d.line((70, yy, W - 70, yy), fill=(232, 224, 205), width=1)
    d.line((140, 230, 140, H - 110), fill=(230, 170, 160), width=2)
    title = md[0].lstrip('# ').strip()
    d.text((70, 70), title, font=font('pop_b', 58), fill=INK)
    d.text((72, 160), '@abhigyanjainmbbs · MBBS student notes', font=font('pop_m', 28), fill=MUTED)
    y = 260
    for ln in md[1:]:
        ln = ln.strip()
        if not ln:
            continue
        if ln.startswith('- '):
            d.ellipse((160, y + 16, 172, y + 28), fill=ACC)
            y = draw_wrapped(d, 190, y, W - 260, ln[2:], 29) + 10
        else:
            y = draw_wrapped(d, 160, y + 10, W - 230, ln, 26) + 6
    d.text((70, H - 96), 'Educational content only · Not medical advice', font=font('pop_b', 22), fill=MUTED)
    d.text((70, H - 62), 'Sources: CDC Pink Book Ch. 21 · CDC Clinical Overview · Ananthanarayan & Paniker · MoHFW', font=font('pop_m', 22), fill=MUTED)
    im.save(out_png)
    im.save(os.path.splitext(out_png)[0] + '.pdf', resolution=150)
    return y


if __name__ == '__main__':
    print('content ends at y =', render(sys.argv[1], sys.argv[2]))
