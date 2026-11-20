# daily-shorts

Automatic daily medical shorts for **@abhigyanjainmbbs** (Abhigyan Jain, MBBS student).

How it works
1. A daily script (JSON) lands in `scripts/queue/` — written and fact-checked by Claude.
2. GitHub Actions (`daily.yml`, 17:11 IST) makes the voice with ElevenLabs (secret `ELEVENLABS_API_KEY`) and renders the
   3D-animated short with the code engine in `engine/`, then creates a **draft release** holding `video.mp4`.
3. `publish.yml` (19:22 IST) publishes the draft; Zapier picks up the new release and posts to YouTube, Instagram and Facebook.
4. Free 1-page notes for each video live in `notes/`.

All visuals are drawn in code (original shapes); music and sound effects are the channel's own generated tracks.
