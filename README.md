# fd-media

Finished media for Finance Department's social posts, served by GitHub Pages at
https://talhakhaan2550-pixel.github.io/fd-media/. Scheduled Claude runs make the files here, and Buffer (Instagram,
Facebook and, from 17 November 2026, YouTube) fetches them by link when a post is placed; Metricool takes any post Buffer
has no room for. Everything in this repository is public.

## Layout

- `weeks/{week}/pieces.json`: the week's pieces, written by the Monday plan run and updated by every run after it.
- `weeks/{week}/media/`: the finished files, served at `{pagesBase}/weeks/{week}/media/{file}`.
- `instagram/highlights/`: the six Instagram highlights put up on 15 November 2026. `media/` holds each highlight's cover
  (`-01`) and its frames as 1080 x 1920 JPEGs, drawn by `tools/studio/instagram_highlights.py` and approved by Talha;
  `stories.json` lists them in posting order with their alt text and the Buffer post that published each highlight's set.
- `tools/studio/`: the studio, in Python, that makes every piece since 15 November 2026: carousel slides
  (1080 x 1350), story frames (1080 x 1920), narrated story videos for explainers and ads, each carousel's music reel
  (1080 x 1920) and LinkedIn post images (1080 x 1350). Since the afternoon of 15 November 2026 everything is in the
  light look Talha chose that day, a mix of his two favourite options: warm paper with grain, Fraunces headlines with
  one part on a yellow marker, ink outlined cards with offset shadows, drawn objects (cheques, bills, forms, stamps,
  calendars), and his real photo cut out on a yellow circle; videos move from scene to scene on colour wipes, with big
  words and big figures.
  - `render.py` makes one piece; `make.mjs` calls it.
  - `slides.py` draws COVER, POINT, CLOSE and STORY with their visuals; `video.py` builds a video's scenes and captions;
    `linkedin_profile.py` draws Talha's LinkedIn background photo (1584 x 396; the record banner has been on his profile since
    15 November 2026) and previews of it on his profile; `linkedin.py` draws a LinkedIn post image (a cheque, a bill, a timeline or any carousel visual, up to three points,
    Talha's photo); `profiles.py` draws the Facebook cover, the YouTube banner and the LinkedIn company banner put up
    on 15 November 2026;
    `brand.py` holds the fonts, colours, icons, US map and page shell; `capture.py` drives Chromium and ffmpeg.
  - `audio.py` is the sound: the AI narrator (Kokoro 82M through kokoro-onnx, voice af_heart, never Talha's voice), word
    timings for the captions, music beds and sound effects made in code (original, so free of any licence), and the
    mix, ducked under the voice and set to -14 LUFS.
  - `doctor.py` checks the workspace and, with `--setup`, installs the narrator (pip package and model files, about
    350 MB, checked by SHA-256 and kept in `~/.cache/fd-studio`).
- `site/offer-videos.json`: the website's page videos, one for each offer page and one for the home page, written by
  `site/make_offer_videos.py` from the pages' words and the Claim Library (15 November 2026). Each runs the same way in under a
  minute: the visitor's situation, what is at stake, the offer and its price, the written guarantee (the `promise` scene; the home page's video
  opens on FD-30, Talha's line, in its place since 15 November 2026), what you get, the record, and "Book a 30 minute call", the words of the button under the video on the page. Render one with
  `python3 tools/studio/render.py site/offer-videos.json offer-1099 --media /tmp/out --preview /tmp/prev`; the finished files
  live in the website's `public/media` at 720 by 1280, not here.
- `tools/make.mjs`: makes the media for a week's pieces and a contact sheet of each in `.previews/` (not committed).
- `tools/check.mjs`: the automatic half of the quality check.
- `tools/explainer.mjs`, `tools/ad.mjs`, `tools/stills.mjs`: the first engine (HyperFrames and Chromium), kept for any
  piece marked `"style": "classic"`; it needs `npm install`.
- `tools/config.json`: the Pages address, the platforms switched on, posting hours and spacing.
- `tools/assets/`: the fonts (Source Serif 4 and IBM Plex Sans, and for the light look Fraunces, Plus Jakarta Sans,
  Caveat and IBM Plex Mono, all SIL Open Font License), the FD mark, GSAP, `us-map.json` (US states from us-atlas, ISC
  licence), `textures/` (paper grain and a stamp mask, drawn in code) and `photos/` with Talha's real portrait, the
  same photo cut out (`talha_cut.png`, and `talha_sticker.png` with a white edge) and the photo of him receiving the
  Best Freelancer of Swabi award (never AI made).
- `linkedin/posts.json` and `linkedin/media/`: one image per LinkedIn post, made from the post's own words in the
  LinkedIn posts doc and named under the post there in a paragraph starting "Image:"; the LinkedIn daily run attaches
  it when it schedules the post. Make one with
  `python3 tools/studio/render.py linkedin/posts.json LI-2026-11-24 --preview /tmp/prev`.

The words on screen are always exactly the words in the piece file: the tools add nothing, reword nothing and
invent nothing. A visual or scene shows the piece's own words and figures again, never a new fact, and the narrator
speaks the piece's `say` words, which are its lines written out as spoken. Piece IDs are `{week}-{letter}{NN}`:
Y reel and cuts, E explainers, C carousels, M carousel music reels, S stories, T text posts, D ads, A avatar videos.
TEST pieces have `"test": true`, a title starting `TEST ` and files starting `TEST-`.

## Commands

```bash
python3 tools/studio/doctor.py --setup        # once per session: checks Python, ffmpeg, Chromium, installs the narrator
node tools/make.mjs weeks/2026-W47/pieces.json --only 2026-W47-E01,2026-W47-C01
node tools/check.mjs weeks/2026-W47/pieces.json claims.json --only 2026-W47-E01
python3 tools/studio/render.py weeks/2026-W47/pieces.json 2026-W47-E01 --media /tmp/out --preview /tmp/prev  # one piece, for a look
```

A narrated video takes two to four minutes and a music reel about three, so run `make.mjs` for a whole week in the
background (`nohup node tools/make.mjs ... > make.log 2>&1 &`) and read its report from the log. If the narrator
cannot be installed, explainers and ads are made with captions and music but no voice, and `check_notes` says so.

`claims.json` holds the month's approved claim IDs, copied from the Claim Library:
`{"tab": "November 2026", "approved": ["1099-01"], "firm": ["FD-01"]}`.

## A piece

```json
{
  "id": "2026-W45-E01", "format": "explainer", "title": "Your 2026 contractors: the 1099 threshold is now $2,000",
  "pillar": "Deadlines", "stage": "Middle", "claims": ["1099-01", "1099-02"],
  "publish_at": "2026-11-03T12:30:00-05:00", "platforms": ["youtube", "instagram", "facebook", "tiktok", "threads"],
  "content": { "kicker": "1099 season", "hook": "...", "lines": ["...", "..."], "cta": "...",
               "say": { "hook": "...", "lines": ["...", "..."], "cta": "..." }, "scenes": [null, {"type": "stat", "value": "$2,000"}, null, null] },
  "captions": { "instagram": "...", "facebook": "...", "tiktok": "...", "threads": "...", "youtube": { "title": "...", "description": "..." } },
  "media": [], "status": "Planned", "check_notes": "", "buffer": {}, "metricool": {}
}
```

`content` by format:

- explainer `{kicker?, hook, lines[2..7], cta, offer?, end_hold?, say?, scenes?}` (`end_hold`: seconds the end card stays, 3 by
  default); ad `{hook_visual?, hook_clip?, kicker?, hook, lines[1..4], offer?, cta, say?, scenes?}`.
  `say` has the spoken words for the hook, each line and the call to action: numbers, dates, form numbers and initials
  written as they are said ("ten ninety-nine N E C"), keeping the line's commas for the pauses. Without it the studio
  writes them out itself. `scenes` has one scene per beat in order (hook, each line, call to action); `null` is the
  default, the line as a large headline, and the call to action's default is the end card. Scene types: headline,
  stat, doc, route, date, ladder, alert, compare, checklist, map, icons, steps, quote, gauge, promise (a written
  guarantee drawn as a certificate with a stamp: `stamp`, `note`, `title`, `text`, `at`), end. A scene's `at`
  names the spoken word it reacts to: its picture is on screen within about 1.4 seconds of the line starting and
  pulses or lights up on that word; consecutive `ladder` scenes with the same `id` grow one chart.
- carousel and story `{slides: [{layout, ...}]}` (each slide published as a JPEG, quality 93), with layouts COVER, POINT,
  CLOSE (carousels) and STORY, where a STORY may
  carry `photo` set to `talha` or `award`. Optional slide fields: `emph` (the part of the title in emerald), `bold`
  (more phrases of the body to bold; figures and dates are bold anyway), `tag` (a point's small line above its
  title), `state` (a postal code for the small map), and `visual` and `visual2`, each one of: map, stats, date, bars,
  hero, chips, quote, threshold, split, tiles, list, steps, compare, checklist, cast. `cast` (approved by Talha on
  16 November 2026, tools/studio/cast.py) draws the cartoon cast: `who` (sam, penny or rex, or a list of up to three),
  `expr` (one per character: sam and penny happy, surprised or thinking; rex sly, surprised, happy or wink), `says` (a
  speech bubble holding only the piece's own words) and `size` (m, or l for a single big character).
- carousel_reel `{from}`: the ID of a carousel in the same week, whose slides it plays at 1080 x 1920 with music; it
  posts as a reel on Instagram and Facebook one to three days after the carousel, with the carousel's claims and captions.
- text `{text}`, and on Threads (since 16 November 2026) also `thread` (up to 4 follow up posts, each under 500 characters), `poll` (2 to 4 options of up to 25 characters), `first_reply` (our first reply under the post, the only place a Threads piece carries its tracked link) and `video_from` (an explainer in the same week whose video the post carries); a Threads caption is the post itself, under 500 characters, with exactly one hashtag, which Threads makes the topic tag; reel and cuts `{brief, opus_project, clip}`.

A piece with `"style": "classic"` is made by the first engine. `make.mjs` sets `ai_voice` to true on every explainer or
ad it narrates, and the platforms' AI labels go on when it is placed (Meta requires one on a reel narrated with a
realistic AI voice). Since the afternoon of 15 November 2026, at Talha's request, the videos carry no AI wording on
screen.

An ad's `hook_visual` describes the opening shot to make (in Higgsfield). Its `hook_clip` is the finished shot:
`{file}` for a clip inside this repository, which the first engine stitches in front of the ad, or `{url}` for a clip
this workspace cannot download, which the Production run stitches elsewhere. An ad with a hook_clip sets `ai_generated`
(true for footage made by AI), and the AI label goes on when it is placed. The clip shows scenes and objects, never a
person presented as a client, a reviewer or Talha.

Platforms are switched on in `tools/config.json`. LinkedIn (Talha's profile) takes explainers, ads, carousels and text
posts, with the tracked link on middle and bottom of funnel pieces, once it is connected in Metricool and added there.
Status runs Planned, Rendering, Made, Passed check, Held, Draft in Metricool, Scheduled, Vetoed, Published, Taken down.

## Threads (since 16 November 2026)

Threads is not placed through Buffer or Metricool. The Social desk, a scheduled run in Talha's business Chrome (Run instructions tab of the Content Engine Kit, block "Social desk"), schedules each Threads piece in Threads' own composer up to three days ahead and keeps its records here:

- `weeks/{week}/threads.json`: one line per scheduled Threads piece, `{"id", "scheduled_et", "scheduled_pkt", "first_reply"}`, plus `"pulled"` when a vetoed post was taken down.
- `threads/replies.json`: the Social desk's replies on other US accounts' Threads posts, `{"date", "url", "account", "words"}` (at most 10 a day, never the same account twice in seven days).
- `threads/insights.json`: Threads' own insights saved on Thursday nights, keyed by ISO week, for the Friday report.

