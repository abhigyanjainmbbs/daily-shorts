"""Pick the next queued script, make the voice, render, and prepare release files.

usage: python engine/pipeline.py [SCRIPT.json] [--voice-only]
Outputs (in out/): <id>.mp4, <id>.jpg, release.md, release_title.txt, id.txt
"""
import glob, json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'engine'))
CFG = json.load(open(os.path.join(ROOT, 'config.json')))


def released_ids():
    try:
        out = subprocess.check_output(['gh', 'release', 'list', '--limit', '100', '--json', 'tagName'], cwd=ROOT)
        return {r['tagName'] for r in json.loads(out)}
    except Exception:
        return set()


def pick(arg=None):
    if arg:
        return os.path.join(ROOT, arg) if not os.path.isabs(arg) else arg
    done = released_ids()
    for p in sorted(glob.glob(os.path.join(ROOT, 'scripts', 'queue', '*.json'))):
        sid = json.load(open(p))['id']
        if sid not in done:
            return p
    return None


def release_text(script):
    desc = script.get('description', '').strip()
    if CFG.get('dm_enabled'):
        desc += f"\n\n💬 Comment \"{CFG['dm_keyword']}\" — free 1-page notes DM mein!"
    tags = ' '.join('#' + t.replace(' ', '') for t in script.get('hashtags', []))
    return f"{desc}\n\n{tags}".strip()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    voice_only = '--voice-only' in sys.argv
    sp = pick(args[0] if args else None)
    if not sp:
        print('nothing queued')
        open(os.path.join(ROOT, 'out_none'), 'w').write('1')
        return
    script = json.load(open(sp))
    sid = script['id']
    out = os.path.join(ROOT, 'out')
    os.makedirs(out, exist_ok=True)
    vdir = os.path.join(ROOT, 'voice', sid)
    import tts
    tts.main(sp, vdir)
    if voice_only:
        print('voice done', sid)
        return
    import render
    mp4 = os.path.join(out, f'{sid}.mp4')
    render.render(sp, vdir, mp4)
    render.thumbnail(sp, os.path.join(out, f'{sid}.jpg'))
    open(os.path.join(out, 'release.md'), 'w').write(release_text(script))
    open(os.path.join(out, 'release_title.txt'), 'w').write(script.get('title', sid)[:100])
    open(os.path.join(out, 'id.txt'), 'w').write(sid)
    # free notes page
    if script.get('notes_md'):
        os.makedirs(os.path.join(ROOT, 'notes'), exist_ok=True)
        open(os.path.join(ROOT, 'notes', f'{sid}.md'), 'w').write(script['notes_md'])
    print('rendered', mp4)


if __name__ == '__main__':
    main()
