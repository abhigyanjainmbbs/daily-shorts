# Handoff — daily-shorts (state at 21 Nov 2026, ~17:15 IST)

## Status: Tetanus short is DONE and SCHEDULED for 21 Nov, 7:30 PM IST
| Platform | Where | Notes |
|---|---|---|
| YouTube Shorts | https://youtube.com/shorts/UkF09dCCCFI | custom cover, tags, altered-content = Yes, Not made for kids |
| Facebook Reel | Business Suite → Content → Scheduled | caption + cover; never click Boost |
| Instagram Reel | Business Suite → Content → Scheduled (@abhigyanjainmbbs) | same caption + cover |
| LinkedIn | linkedin.com → Start a post → clock icon → Scheduled | English caption + notes link |

- **Comment-to-DM:** Business Suite → Inbox → Automations → "Comment to message - Tetanus free notes DM" (ON, Messenger + Instagram). Keyword TETANUS → sends the 6-page notes PDF link. Meta may delay the DM ~15 min and skips it if he replies first.
- **Notes PDF (6 pages):** `notes/Tetanus_Notes_AbhigyanJainMBBS.pdf` (source in `notes/src/`).
  - Public: https://github.com/abhigyanjainmbbs/daily-shorts/blob/main/notes/Tetanus_Notes_AbhigyanJainMBBS.pdf
- **Final video:** `media/2026-11-21-tetanus/Tetanus_FINAL.mp4` (2:46.9), cover `cover_1080x1920.jpg`. Laptop copies in `Downloads/ABHIGYAN JAIN SHORTS/Tetanus/`.

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
