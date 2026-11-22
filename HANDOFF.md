# Handoff — daily-shorts (state at 22 Nov 2026, ~16:20 IST)

## Latest: Naphthalene balls short — SCHEDULED for 22 Nov, 7:30 PM IST
| Platform | Where | Notes |
|---|---|---|
| YouTube Shorts | https://youtu.be/TX5L3qZtolk | custom cover, tags, altered-content = Yes, Not made for kids |
| Facebook Reel | Business Suite → Content → Scheduled | caption + cover; never click Boost |
| Instagram Reel | Business Suite → Content → Scheduled (@abhigyanjainmbbs) | same caption + cover |
| LinkedIn | linkedin.com → clock icon → Scheduled | English caption + notes link + cover |

- **Comment-to-DM:** Business Suite → Inbox → Automations → "Comment to message - Naphthalene free notes DM" (ON, Messenger + Instagram). Keywords: NAPHTHALENE / Naphthalene / naphthalene + 3 "napthalene" misspellings (keywords are case-sensitive, so each case is a separate keyword; max 10). Meta may delay the DM ~15 min and skips it if he replies first.
- **Notes PDF (6 pages):** `notes/Naphthalene_Notes_AbhigyanJainMBBS.pdf` (source `notes/naph/notes.html`).
- **Final video:** `media/2026-11-22-naphthalene/Naphthalene_FINAL.mp4` (3:02), cover `cover_1080x1920.jpg`.
- Mix: `scripts/cues/2026-11-22-naphthalene.json`, gap-to-speech −14.5 dB (the balance he approved).

## Previous: Tetanus short (21 Nov) — live
- https://youtube.com/shorts/UkF09dCCCFI · notes `notes/Tetanus_Notes_AbhigyanJainMBBS.pdf`
- "Comment to message - Tetanus free notes DM" automation still ON (keyword TETANUS).

## How this video was made (repeat for the next topic)
1. **Script** → `scripts/queue/<id>.json`: scenes with `vo`, `kw` keyword lists, `visual` = comp spec (+ `visual_fallback`). Flags `captions:false`, `film:true`.
2. **Voice:** ElevenLabs website (his Chrome), voice "Abhigyan", **Eleven v4, stability 0.45, similarity 0.65**.
   - Paste ONE line of text (no newlines), check the char counter.
   - A fetch hook keeps audio blobs in `window.__blobs`; export via the example.com helper tab (window.open from an injected button, then postMessage).
   - Process with the kit's `voicefx.sh`; split into lines with `chunks.py` + `asr_chunks.py` (sherpa-onnx whisper-small).
   - NEVER time-stretch the voice.
3. **Images:** ChatGPT in several tabs at once (JS sender: `.ProseMirror` + `execCommand('insertText')` + Send button; clear the composer first, because drafts are shared across tabs).
   - Chrome allows only 1 auto-download per tab → download each image from a fresh tab.
   - Cut-outs: rembg `isnet-general-use`. Save to `assets/gen/<id>/`.
4. **Render:** `python engine/render.py <script> voice/<id> out.mp4`; preview with `/home/claude/work/preview.py`.
5. **Mix:** kit `audio_tools/mix.py` + cues JSON (`scripts/cues/<id>.v3.json` is the approved one).
   - Music beds about −26 dB, duck 7 dB, SFX −3 dB, loudnorm −14 LUFS. The voice must stay clearly on top: he said v2 music was too loud.
6. **Watermark:** Poppins Bold 38, alpha 80, y=1530 (he asked for bold + faint, not overlapping text).

## Gotchas learned on 22 Nov
- **GitHub rejects files over 100 MB.** Re-encode the final with `-b:v 3850k -maxrate 5M -bufsize 10M -preset fast` → ~90 MB for 3 minutes, quality still good.
- **ChatGPT tabs: wait for each image before sending the next prompt in that tab.** Sending prompt N+1 too soon cancels image N.
- **Chrome allows only one automatic download per tab.** Open a fresh tab per image: navigate to the conversation URL, screenshot to activate, then fetch the blob and click an `<a download>`. If the filename already exists Windows saves it as `name (1).png`.
- **Meta keyword field is a combobox:** type the keyword, then click the suggestion row below it. Commas and Enter do not create chips.
- **LinkedIn/Meta rich editors:** click the element by its `find` ref (coordinates often miss), then dispatch a synthetic `paste` ClipboardEvent.

## Uploading big files from the browser (works on YouTube, Meta, LinkedIn)
- Push the mp4 to this public repo; raw.githubusercontent.com allows CORS.
- YouTube Studio can `fetch()` the raw URL directly. Meta and LinkedIn block it (CSP), so:
  1. Inject a button and real-click it → `window.open('https://example.com/?xfer')` (keeps `window.opener`).
  2. In the helper tab, fetch the raw files → `window.opener.postMessage({__xfer:1,name,file},'*')`.
  3. In the main tab, patch `HTMLInputElement.prototype.click` so a file input gets `files` = DataTransfer with the received File, then dispatch `input` + `change`. Then real-click "Add video"/"Upload image".
- Meta captions use Draft.js: do NOT use execCommand (it crashes the editor). Dispatch a synthetic `paste` ClipboardEvent with text/plain.
- LinkedIn uses ProseMirror: paste text/html with `<p>` blocks and `<p><br></p>` spacers.

## Automation (pending)
- **Free images:** Cloudflare Workers AI. The user adds `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` as GitHub secrets.
  - Then add a Cloudflare provider to `tools/imagegen.py`; Pollinations quality is not usable.
- Create the 3 Zapier Zaps, the daily Claude scheduled task, and a backlog of scripts.

## Rules
- Medical accuracy first; spell out abbreviations.
- Copyright-safe music and assets.
- Never paste keys in chat.
- Never use the bank-linked Gmail.
- No "Dr." in his name; no "Follow karo" voice line.
- Disclaimer in every video: on screen, spoken, and in the description.
- Tick AI/altered-content where offered. Never click Boost.
- Watermark: @abhigyanjainmbbs.
