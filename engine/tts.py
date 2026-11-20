"""ElevenLabs voice for each scene of a script (runs in GitHub Actions with ELEVENLABS_API_KEY secret).

usage: python engine/tts.py SCRIPT.json OUT_DIR
"""
import json, os, re, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, 'config.json')))
API = 'https://api.elevenlabs.io/v1'


def _req(method, url, key, body=None, accept='application/json'):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={'xi-api-key': key, 'Content-Type': 'application/json', 'Accept': accept})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def voice_id(key):
    vid = os.environ.get('ELEVENLABS_VOICE_ID') or CFG.get('voice_id')
    if vid:
        return vid
    data = json.loads(_req('GET', f'{API}/voices', key))
    want = CFG.get('voice_name', 'Abhigyan').lower()
    for v in data.get('voices', []):
        if v.get('name', '').strip().lower() == want:
            return v['voice_id']
    for v in data.get('voices', []):
        if want in v.get('name', '').lower():
            return v['voice_id']
    raise SystemExit(f'voice "{want}" not found in ElevenLabs account')


def strip_tags(t):
    return re.sub(r'\[[^\]]+\]', '', t).replace('  ', ' ').strip()


def speak(key, vid, text, out):
    last = None
    for model in CFG.get('tts_models', ['eleven_v3', 'eleven_multilingual_v2']):
        body = {'text': text if model == 'eleven_v3' else strip_tags(text), 'model_id': model}
        if model == 'eleven_v3':
            body['voice_settings'] = {'stability': 0.5, 'similarity_boost': 0.8}
        else:
            body['voice_settings'] = {'stability': 0.45, 'similarity_boost': 0.85, 'style': 0.35, 'use_speaker_boost': True}
        for attempt in range(3):
            try:
                audio = _req('POST', f'{API}/text-to-speech/{vid}?output_format=mp3_44100_128', key, body, accept='audio/mpeg')
                open(out, 'wb').write(audio)
                return model
            except urllib.error.HTTPError as e:
                last = f'{model}: HTTP {e.code} {e.read()[:300]!r}'
                if e.code in (400, 404, 422):
                    break  # try next model
                time.sleep(5 * (attempt + 1))
            except Exception as e:  # network
                last = f'{model}: {e}'
                time.sleep(5 * (attempt + 1))
    raise SystemExit(f'TTS failed: {last}')


def scene_list(script):
    specs = list(script['scenes'])
    cta = script.get('cta_dm') if CFG.get('dm_enabled') else script.get('cta_plain')
    if cta:
        specs.append(cta)
    return specs


def main(script_path, out_dir):
    key = os.environ.get('ELEVENLABS_API_KEY')
    if not key:
        raise SystemExit('ELEVENLABS_API_KEY not set')
    script = json.load(open(script_path))
    os.makedirs(out_dir, exist_ok=True)
    vid = voice_id(key)
    for i, sp in enumerate(scene_list(script)):
        out = os.path.join(out_dir, f'scene_{i:02d}.mp3')
        if os.path.exists(out) and os.path.getsize(out) > 1000:
            continue
        m = speak(key, vid, sp['vo'], out)
        print(f'scene {i}: {m} -> {out}', flush=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
