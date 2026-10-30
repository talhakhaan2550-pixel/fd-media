# fd-media

Finished media for Finance Department's social posts, served by GitHub Pages at
https://talhakhaan2550-pixel.github.io/fd-media/. Scheduled Claude runs make the files here, and Metricool
fetches them by link when a post is placed. Everything in this repository is public.

## Layout

- `weeks/{week}/pieces.json`: the week's pieces, written by the Monday plan run and updated by every run after it.
- `weeks/{week}/media/`: the finished files, served at `{pagesBase}/weeks/{week}/media/{file}`.
- `tools/explainer.mjs`: builds an explainer as a HyperFrames composition and renders it to MP4 (1080 x 1920).
- `tools/ad.mjs`: builds an ad on the explainer engine, with the offer on the end card and an optional opening shot in front.
- `tools/stills.mjs`: draws carousel slides (1080 x 1350) and story frames (1080 x 1920) to PNG in Chromium.
- `tools/make.mjs`: makes the media for a week's pieces and a contact sheet of each in `.previews/` (not committed).
- `tools/check.mjs`: the automatic half of the quality check.
- `tools/config.json`: the Pages address, the platforms switched on, posting hours and spacing.
- `tools/assets/`: the brand fonts (Source Serif 4 and IBM Plex Sans, SIL Open Font License), the FD mark, GSAP, and
  `photos/` with Talha's real portrait and the photo of him receiving the Best Freelancer of Swabi award (never AI made).

The words on screen are always exactly the words in the piece file: the tools add nothing, reword nothing and
invent nothing. Piece IDs are `{week}-{letter}{NN}`: Y reel and cuts, E explainers, C carousels, S stories,
T text posts, D ads, A avatar videos. TEST pieces have `"test": true`, a title starting `TEST ` and files starting `TEST-`.

## Commands

```bash
npm install                                   # once per session (Node 22, ffmpeg and Chromium are already there)
node tools/make.mjs weeks/2026-W45/pieces.json --only 2026-W45-E01,2026-W45-C01
node tools/check.mjs weeks/2026-W45/pieces.json claims.json --only 2026-W45-E01
```

`claims.json` holds the month's approved claim IDs, copied from the Claim Library:
`{"tab": "November 2026", "approved": ["1099-01"], "firm": ["FD-01"]}`.

## A piece

```json
{
  "id": "2026-W45-E01", "format": "explainer", "title": "Your 2026 contractors: the 1099 threshold is now $2,000",
  "pillar": "Deadlines", "stage": "Middle", "claims": ["1099-01", "1099-02"],
  "publish_at": "2026-11-03T12:30:00-05:00", "platforms": ["youtube", "instagram", "facebook", "tiktok", "threads"],
  "content": { "kicker": "1099 season", "hook": "...", "lines": ["...", "..."], "cta": "..." },
  "captions": { "instagram": "...", "facebook": "...", "tiktok": "...", "threads": "...", "youtube": { "title": "...", "description": "..." } },
  "media": [], "status": "Planned", "check_notes": "", "metricool": {}
}
```

`content` by format: explainer `{kicker?, hook, lines[2..7], cta}`; ad `{hook_visual?, hook_clip?, kicker?, hook, lines[1..4], offer?, cta}`;
carousel and story `{slides: [{layout, ...}]}` with layouts COVER, POINT, CLOSE (carousels) and STORY, where a STORY may
carry `photo` set to `talha` or `award`; text `{text}`; reel and cuts `{brief, opus_project, clip}`.

An ad's `hook_visual` describes the opening shot to make (in Higgsfield). Its `hook_clip` is the finished shot:
`{file}` for a clip inside this repository, which `make.mjs` stitches in front of the ad, or `{url}` for a clip this
workspace cannot download, which the Production run stitches elsewhere. An ad with a hook_clip sets `ai_generated`
(true for footage made by AI), and the AI label goes on when it is placed. The clip shows scenes and objects, never a
person presented as a client, a reviewer or Talha.

Platforms are switched on in `tools/config.json`. LinkedIn (Talha's profile) takes explainers, ads, carousels and text
posts, with the tracked link on middle and bottom of funnel pieces, once it is connected in Metricool and added there.
Status runs Planned, Rendering, Made, Passed check, Held, Draft in Metricool, Scheduled, Vetoed, Published, Taken down.
