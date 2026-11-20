# Handoff — daily-shorts (state at 21 Nov 2026, 04:10 IST)

## Goal today
Tetanus/rusty-nail short, live on YouTube, Instagram and Facebook at **7:30 PM IST, 21 Nov**.
- Make it in the reference reel's style: realistic AI images, cut out and animated like an editor would, not drawn shapes.
- Keep the keyword text style, film look, his ElevenLabs voice, the disclaimer and the comment CTA.

## Done
- **Script:** `scripts/queue/2026-11-21-tetanus.json`
  - 23 scenes plus the CTA, fact-checked against CDC Pink Book Ch. 21, CDC clinical overview, MoHFW (TT→Td) and WHO (MNTE 2015).
  - Share hook near the end; CTA: comment "TETANUS" for free 1-page notes in DM.
- **Voice:** generated in `voice/2026-11-21-tetanus/`; `vo_speed` 1.1 keeps it under 3 min (≈2:50 with the outro).
- **Disclaimer** appears in every video:
  - on screen in the first 4 s and on the CTA scene (`config.json` → `disclaimer`)
  - spoken in the CTA
  - auto-appended to the description (`engine/pipeline.py`)
- **1-page notes (the DM freebie):** `notes/2026-11-21-tetanus.png` / `.pdf`, made by `engine/notes_card.py`.
- **Cut-out animation engine** `engine/comp.py` (scene type `comp`):
  - image plates with zoom, pan and crossfades
  - cut-out sprites with keyframes and image swaps
  - FX: steam, bubbles, boil, flakes, blood, glow, particles, path, people, crack, rings, shake, flash, emoji
  - info cards
  - Any scene with missing images automatically falls back to `visual_fallback`.
- **Shot list:** `scripts/shots/2026-11-21-tetanus.json` has 28 ChatGPT prompts (25 priority A).
  - Cut-out images end in `_cut`. Generate them on a white background, then remove the background with rembg (`isnet-general-use`).

## Next (needs the user's laptop with Chrome + ChatGPT)
1. Generate the shot-list images in ChatGPT.
   - Save them to `assets/gen/2026-11-21-tetanus/<name>.png`.
   - For `_cut` names, run rembg and save the transparent PNG under the `_cut` name.
2. Tune the coordinates in the scene specs to the real images:
   - nerve path points
   - display text position on `scale`
   - spore position on `wound_section`
3. Preview: `python /home/claude/work/preview.py <script> voice/<id> sheet.jpg 0.15,0.5,0.85` (or write a similar contact-sheet script).
4. Render: `python engine/render.py <script> voice/<id> out.mp4`.
   - Check it, then send it to the user for approval.
5. Upload at 7:30 PM to YouTube, Instagram and Facebook:
   - Tick the AI-content disclosure.
   - Never click Boost.
   - Confirm with the user first.
   - The comment-to-DM promise needs a DM tool (ManyChat or Inrō free) connected by the user, or the user replies manually.

## Automation (pending)
- **Free images:** Cloudflare Workers AI. The user adds `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` as GitHub secrets.
  - Then add a Cloudflare provider to `tools/imagegen.py`; it currently uses Pollinations, whose quality is not usable.
- Create the 3 Zapier Zaps, the daily Claude scheduled task, and a backlog of scripts.

## Rules
- Medical accuracy first.
- Copyright-safe music and assets.
- Never paste keys in chat.
- Never use the bank-linked Gmail.
- No "Dr." in his name.
- Watermark: @abhigyanjainmbbs.
