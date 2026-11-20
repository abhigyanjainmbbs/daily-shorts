"""Generate images for a shot list (runs on GitHub Actions, which has open internet).
Reads triggers/images.json: {"id": "...", "shots": [{"name": "hand_open", "prompt": "...", "w": 1024, "h": 1024, "cutout": true, "seed": 1}]}
Writes assets/gen/<id>/<name>.png (+ <name>_cut.png when cutout is requested).
"""
import json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
job = json.load(open(os.path.join(ROOT, 'triggers', 'images.json')))
out = os.path.join(ROOT, 'assets', 'gen', job['id'])
os.makedirs(out, exist_ok=True)
STYLE = job.get('style', '')
MODEL = job.get('model', 'flux')
log = []


def fetch(prompt, w, h, seed):
    q = urllib.parse.quote(prompt)
    url = f'https://image.pollinations.ai/prompt/{q}?width={w}&height={h}&seed={seed}&model={MODEL}&nologo=true&enhance=false'
    req = urllib.request.Request(url, headers={'User-Agent': 'daily-shorts/1.0'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read(), r.headers.get('Content-Type', '')


cut_list = []
for s in job['shots']:
    p = os.path.join(out, s['name'] + '.png')
    if os.path.exists(p) and not s.get('force'):
        continue
    prompt = (s['prompt'] + ', ' + STYLE).strip(', ') if not s.get('raw') else s['prompt']
    for attempt in range(4):
        try:
            data, ct = fetch(prompt, s.get('w', 1024), s.get('h', 1024), s.get('seed', 7))
            if len(data) < 5000 or 'image' not in ct:
                raise RuntimeError(f'bad response {ct} {len(data)}')
            from PIL import Image
            import io
            Image.open(io.BytesIO(data)).convert('RGB').save(p)
            log.append(f"ok {s['name']} {len(data)}")
            break
        except Exception as e:
            log.append(f"retry {s['name']} {attempt}: {e}")
            time.sleep(8 + attempt * 10)
    if s.get('cutout') and os.path.exists(p):
        cut_list.append(p)
    time.sleep(job.get('pause', 3))

if cut_list:
    from rembg import remove, new_session
    from PIL import Image
    sess = new_session(job.get('rembg_model', 'isnet-general-use'))
    for p in cut_list:
        im = Image.open(p)
        o = remove(im, session=sess, post_process_mask=True)
        o.save(p.replace('.png', '_cut.png'))
        log.append(f'cut {os.path.basename(p)}')

print('\n'.join(log))
open(os.path.join(out, '_log.txt'), 'w').write('\n'.join(log))
