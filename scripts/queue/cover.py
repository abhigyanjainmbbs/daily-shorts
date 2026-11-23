import sys, os
sys.path.insert(0, '/home/claude/daily-shorts/engine')
from PIL import Image, ImageDraw, ImageFilter
import gfx as G

W, H = 1080, 1920
src = Image.open('/home/claude/daily-shorts/assets/gen/2026-11-23-scd/gym_collapse.png').convert('RGB')
# cover-fill crop to 9:16
sw, sh = src.size
k = max(W / sw, H / sh)
src = src.resize((int(sw * k), int(sh * k)), Image.LANCZOS)
x0 = (src.width - W) // 2; y0 = int((src.height - H) * 0.35)
fr = src.crop((x0, y0, x0 + W, y0 + H))

# dark cinematic grade + vignette
from PIL import ImageEnhance
fr = ImageEnhance.Color(fr).enhance(0.80)
fr = ImageEnhance.Contrast(fr).enhance(1.22)
fr = ImageEnhance.Brightness(fr).enhance(0.88)

vig = Image.new('L', (W, H), 0)
dv = ImageDraw.Draw(vig)
dv.ellipse((-260, 180, W + 260, H - 60), fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(260))
black = Image.new('RGB', (W, H), (0, 0, 0))
fr = Image.composite(fr, black, vig)

# top + bottom scrims for text legibility
sc = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ds = ImageDraw.Draw(sc)
for i in range(560):
    ds.line([(0, i), (W, i)], fill=(0, 0, 0, int(205 * (1 - i / 560) ** 1.25)))
for i in range(420):
    y = H - 1 - i
    ds.line([(0, y), (W, y)], fill=(0, 0, 0, int(190 * (1 - i / 420) ** 1.2)))
fr = Image.alpha_composite(fr.convert('RGBA'), sc)

d = ImageDraw.Draw(fr)

def band_line(txt, y, size, fg, bg, pad=(26, 14)):
    f = G.font('osw', size)
    tw = int(d.textlength(txt, font=f))
    asc, desc = f.getmetrics()
    th = asc + desc
    x = W // 2 - tw // 2
    if bg:
        d.rectangle((x - pad[0], y - pad[1], x + tw + pad[0], y + th + pad[1]), fill=bg)
    d.text((x, y), txt, font=f, fill=fg)
    return th + 2 * pad[1]

def plain_line(txt, y, size, fg, stroke=6):
    f = G.font('osw', size)
    tw = int(d.textlength(txt, font=f))
    d.text((W // 2 - tw // 2, y), txt, font=f, fill=fg, stroke_width=stroke, stroke_fill=(0, 0, 0))
    asc, desc = f.getmetrics()
    return asc + desc

y = 150
y += plain_line('GYM MEIN JAWAN LOG', y, 92, (255, 255, 255)) + 6
y += plain_line('ACHANAK KYUN', y, 92, (255, 255, 255)) + 6
band_line('GIR RAHE HAIN?', y, 96, (255, 255, 255), (214, 36, 28))

# bottom hook
by = 1672
f2 = G.font('osw', 64)
t2 = '300 MEIN SE 1 KE DIL MEIN'
tw2 = int(d.textlength(t2, font=f2))
d.text((W // 2 - tw2 // 2, by), t2, font=f2, fill=(255, 214, 70), stroke_width=6, stroke_fill=(0, 0, 0))
f3 = G.font('osw', 64)
t3 = 'CHHUPI BIMARI'
tw3 = int(d.textlength(t3, font=f3))
d.text((W // 2 - tw3 // 2, by + 80), t3, font=f3, fill=(255, 214, 70), stroke_width=6, stroke_fill=(0, 0, 0))

# watermark, same spec as video
wm, wox, woy, wtw, wth = G.text_sprite('@abhigyanjainmbbs', G.font('pop_b', 38), (255, 255, 255, 204), shadow=0.6, blur=8)
G.paste(fr, wm, W / 2 - wtw / 2 + wox, 1530 + woy, 1.0)

fr.convert('RGB').save('/home/claude/work/scd/cover_1080x1920.jpg', quality=93)
print('ok', fr.size)
