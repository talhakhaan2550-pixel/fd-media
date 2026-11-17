# fd-media

Finished media for Finance Department's social posts, served by GitHub Pages at
https://talhakhaan2550-pixel.github.io/fd-media/. Scheduled Claude runs make the files here, and Buffer (Instagram,
Facebook and, from 17 November 2026, YouTube) fetches them by link when a post is placed; Metricool takes any post Buffer
has no room for, and the hook tests' Instagram Trial Reels. Everything in this repository is public.

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
- `tools/config.json`: the Pages address, the platforms switched on, posting hours and spacing, and `trial_reels`, whether
  Instagram takes our Trial Reels (see Hook tests below).
- `research/`: the Research desk (since 17 November 2026): `patterns.json` (hook types, formats and scenes with our
  results and peer sightings), `peers.json` (the peer accounts tracked in Metricool) and each week's
  `research/{week}/brief.json`, which the Monday plan reads. See `research/README.md`.
- `tools/keywords.json`: the comment and DM keyword map Talha approved on 17 November 2026, with each keyword's page,
  tracked link, Meta automation and status (live once Talha's test passes).
- `tools/studio/motion.py`, `tools/studio/work.py` and `tools/studio/render_motion.py`: the motion v2 engine (one
  camera moving over a paper desk, the hook on screen from the first frame, step counters for middle of funnel videos,
  and since 17 November 2026 the work scenes that show what an offer covers being done). Talha approved the style on
  17 November 2026 ("the designing and video editing looks fine to me for now"): every explainer and ad with
  `content.motion` is made by it through `render.py`; `video.py` stays for pieces written the old way. The samples are
  in `samples/motion-v2/`.
- `tools/coverage.json`: what each of the twelve offers covers, word for word from the What you get list on its page
  (claim FD-31), with the on-screen title and the work scene for each item. See "What an offer covers" below.
- `tools/learn.mjs`, `research/results/`, `research/scores.json` and `research/experiments.json`: the learning loop and
  the weekly wild card. See "The learning loop" below.
- `hooks.json`: every hook test with both versions' numbers, the winner and its lesson, written by the Friday report and
  read by the Monday plan.
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
  hero, chips, quote, threshold, split, tiles, list, steps, compare, checklist, cast. `cast` (tools/studio/cast.py) shows the cartoon cast
  in 3D (Talha approved the 3D cast on the evening of 16 November 2026; it replaced the 2D drawings approved that
  morning): `who` (one of sam the founder, penny the bookkeeper, rex the runaway receipt, zara the founder abroad,
  grace the angel investor, dev the co-founder, maya the freelancer and dot the deadline, or a list of up to three),
  `expr` (one per character: the six people happy, surprised or thinking; rex sly, surprised, happy or wink; dot happy,
  surprised or wink), `says` (a speech bubble holding only the piece's own words) and `size` (m, or l for a single big
  character). The characters are sprites rendered in Blender (tools/cast3d) and pop in; in a reel they then sway
  gently, and a closing slide in a reel shows them small.
- carousel_reel `{from}`: the ID of a carousel in the same week, whose slides it plays at 1080 x 1920 with music; it
  posts as a reel on Instagram and Facebook one to three days after the carousel, with the carousel's claims and captions.
- text `{text}`, and on Threads (since 16 November 2026) also `thread` (up to 4 follow up posts, each under 500 characters), `poll` (2 to 4 options of up to 25 characters), `first_reply` (our first reply under the post, the only place a Threads piece carries its tracked link) and `video_from` (an explainer in the same week whose video the post carries); a Threads caption is the post itself, under 500 characters, with exactly one hashtag, which Threads makes the topic tag; reel and cuts `{brief, opus_project, clip}`.

An explainer in a hook test also carries `trial` `{test, variant, pattern, of?}`, as set out under Hook tests below.

Every piece planned from 2026-W49 carries `tags`: `{"hook": a hook id from research/patterns.json, "format": a format
id from it, "scenes": [the shot or scene types it leans on]}`, so the learning loop can tell what worked. The week's
wild card also carries `experiment`: its id in research/experiments.json, such as "2026-W49-X1".

### Motion v2: content.motion (explainers and ads, since 17 November 2026)

```json
"content": {"motion": {
  "stage": "top | middle | bottom",
  "pills": {"0": "Before you raise", "2": "Before you raise"},
  "hook": {"text": "...", "say": "...", "shot": {"type": "report", "title": "..."}},
  "shots": [
    {"cover": "investor_ready_scan", "pill": "What you get"},
    {"shot": {"type": "price", "first": "$750", "...": "..."}, "lines": [{"text": "...", "say": "..."}]}
  ],
  "cta": {"kind": "follow | comment | dm", "keyword": "SCAN", "text": "...", "say": "...", "pill": "DM <b>SCAN</b>",
          "shot": {"type": "phone", "keyword": "SCAN", "reply": "...", "link": "financedepartmentllc.com/investor-ready-scan"}},
  "offer": "words under Talha's name on the end card"
}}
```

The hook's words are its title and are on screen from the first frame. Each shot is one picture at its own place on the
desk; several lines in one shot keep the camera still. `pills` label the top pill by shot index (0 is the hook; a
missing index keeps the last label). The call to action matches the stage: top follow, middle comment (a comment
keyword from tools/keywords.json), bottom dm (a DM keyword); an ad may ask for its offer's DM keyword at any stage.
Shot types and their fields are documented in `tools/studio/motion.py` and `tools/studio/work.py`: versus, form,
castpay, bars, calendar, follow, person, checklist, docpair, fax, deadline, penalty, comment, report, days, price,
proof, nofee, phone, work and recap. Every word on screen restates the piece's own approved words, and a shot shows no
figure that its lines do not say. Preview a piece's frames without making the video with
`python3 tools/studio/render_motion.py weeks/{week}/pieces.json {ID} --out /tmp/peek --peek 1,4.5,9`.

### What an offer covers (since 17 November 2026)

Talha, 17 November 2026: whenever a piece introduces a service or quotes a price, it first explains in detail what the
service covers, in a visual form that practically shows the work, instead of just saying the name and the price.

- A motion piece puts `{"cover": "<offer id>"}` among its shots before the offer is named or priced. It becomes one
  numbered station per item of the offer's What you get list, each item's words spoken and captioned word for word and
  its work shown being done (books matched line by line, revenue spread over the months it is earned, a cap table
  checked against its papers, a contract read with its terms highlighted, runway drawn month by month, the findings
  report's gaps with their cost and time to fix, forms filled in and stamped, papers sent and confirmed), then a recap
  that ticks every item and names the offer. The price comes after. `"recap": false` leaves the recap out and
  `"steps": false` the step numbers.
- A story or carousel slide puts `"cover": "<offer id>"` on the slide: a story shows the list with each item's words
  after its kicker and title and before its body, so the kicker and title must not name or price the offer; a
  carousel shows the list as the slide's visual, and names and prices the offer only on a later slide.
- A text post lists every item (its title or its words) before it names or prices the offer, and so does any caption
  that quotes a price.
- A classic video may not name or price an offer at all.
- A piece about an offer lists FD-31, and one that quotes its price also lists the offer's own claim. The offer ids
  are investor_ready_scan, investor_ready_sprint, books_catch_up, funded_plan, international_founder_plan,
  startup_tax_returns (held until Talha's PTIN is active), filing_1099, payroll, rd_credit, us_entry,
  delaware_franchise_tax and form_5472. A price counts only for an offer the piece names or covers, so $600 in a post
  about the old 1099 threshold is not a price.
- `tools/check.mjs` enforces all of this. When an offer page's What you get list changes, change `tools/coverage.json`
  in the same chat and run `node tools/coverage.mjs --check ../financedepartment` with the website repository beside
  this one.

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

## Hook tests (since 16 November 2026)

Talha asked for the "test reels" on 16 November 2026: each week one explainer that goes to Instagram is tried with two
hooks on people who do not follow us yet, using Instagram's Trial Reels.

- Version A is the planned explainer with `"trial": {"test": "{week}-H1", "variant": "A", "pattern": "question"}`. Its
  other platforms post as usual; on Instagram it goes out as a Trial Reel.
- Version B is its own explainer piece, numbered after the week's other explainers, with `"platforms": ["instagram"]`,
  `"trial": {"test": "{week}-H1", "variant": "B", "of": "{A's ID}", "pattern": "contrast"}`, the same claims, kicker,
  lines, offer, call to action, spoken lines and scenes after the hook, and a hook of its own (with its `say.hook` and
  the first line of its Instagram caption). It goes out the next day at A's Eastern time. `check.mjs` holds B to this.
- Patterns: question, number, contrast (old against new), mistake, myth, deadline, call out ("If you pay
  contractors..."). B's pattern differs from A's.
- Trial Reels are placed through Metricool (Instagram type `TRIAL_REEL`), never Buffer, whose connector has no trial
  option. They show first only to people who do not follow us, and Metricool's Trial Reels share one with our
  followers automatically when it does well within 72 hours. They count toward Metricool's 20 free posts a month and
  stay out of the daily feed post count.
- `tools/config.json` `trial_reels`: `status` is `untested` until the first Trial Reel publishes, then `working`; when
  Instagram or Metricool refuses one it becomes `refused`, with `checked` (the date) and `error` (word for word). While
  it is `refused` and under 28 days old, no hook test is planned, version A posts as a normal reel through Buffer and
  version B is held. Instagram's help asks for a public professional account eligible for recommendations; guides
  disagree on the follower minimum (200 or 1,000), so the first test settles it.
- The Friday report reads both versions' numbers from Metricool's Instagram reels analytics (views, reach, average watch
  time, skip rate, shares, saves) and adds the test to `hooks.json`:
  `{"test", "week", "topic", "A": {"id", "hook", "pattern", "views", "reach", "skip_rate", "avg_watch_seconds", "shares", "saves"}, "B": {...}, "winner", "lesson"}`.
  The winner has the lower skip rate (the share of viewers who swiped away in the first three seconds) or, within two
  points, more views; "not readable" when Metricool gives no numbers for a Trial Reel.

## Threads (since 16 November 2026)

Threads is not placed through Buffer or Metricool. The Social desk, a scheduled run in Talha's business Chrome (Run instructions tab of the Content Engine Kit, block "Social desk"), schedules each Threads piece in Threads' own composer up to three days ahead and keeps its records here:

- `weeks/{week}/threads.json`: one line per scheduled Threads piece, `{"id", "scheduled_et", "scheduled_pkt", "first_reply"}`, plus `"pulled"` when a vetoed post was taken down.
- `threads/replies.json`: the Social desk's replies on other US accounts' Threads posts, `{"date", "url", "account", "words"}` (at most 10 a day, never the same account twice in seven days).
- `threads/insights.json`: no longer written. Talha connected Threads in Metricool on 15 November 2026, so from 16 November 2026 the Weekly report, the Growth loop and the Client Acquisition Dashboard read Threads' numbers from Metricool (brand 7464082: the threads evolution, posts and country fields). The file stays for history.

The Social desk also answers what people send us on Threads: replies, mentions and quotes of our posts, replies to our own replies on other accounts' posts (its step 2b) and direct messages (its step 6), from the answer bank on the kit's Replies tab. Anything it should not answer waits in Slack #content for Talha's ✅. Threads conversations and social media leads are logged in the Conversations sheet, not here.

## The learning loop and the weekly wild card (since 17 November 2026)

Talha, 17 November 2026: the system improves itself, its content strategy built on research for virality and on the
goals each piece is for, and once a week it tries something really out of the box; what works joins the strategy.

1. Every piece carries `tags` (hook pattern, format, scenes) and the wild card its `experiment` id.
2. The Friday Weekly report writes `research/results/{week}.json` with every published piece's numbers:

   ```json
   {"week": "2026-W49", "made": "2026-12-11 10:12 PKT", "pieces": [
     {"id": "2026-W49-E01", "format": "explainer", "stage": "Top", "pillar": "Deadlines", "tags": {"hook": "question", "format": "steps_video"},
      "experiment": null, "keyword_actions": 3, "leads": 1, "calls": 0,
      "posts": [{"platform": "instagram", "views": 1234, "reach": 1100, "likes": 50, "comments": 5, "saves": 12, "shares": 9,
                 "avg_watch_s": 6.2, "skip_rate": 41.0}]}]}
   ```

   `keyword_actions` counts comments and DMs with the piece's keyword (Buffer Community, the Conversations sheet),
   `leads` the HubSpot contacts credited to it by utm_campaign, `calls` those that reached Call booked. A number no
   tool gives is left out, never estimated.
3. It then runs `node tools/learn.mjs`, which scores every piece against its stage's goal (top: views, shares, saves and
   holding attention; middle: views, saves, comments and keyword actions; bottom: views, keyword actions, leads and
   calls), each number compared with the median of the same platform and kind of post over the last eight weeks, and
   writes `research/scores.json`: each hook, format, scene, pillar and platform by stage, recent weeks counting most
   (a four week half life) and pulled towards our usual until it has evidence. It also judges the wild card in
   `research/experiments.json`: a win at 1.25 times the same stage's other pieces, a loss at 0.8 or less, otherwise
   inconclusive, and not readable under 100 views. One strong win (1.5 times) or two wins mark it `promote`.
4. The Monday Research desk reads both: it ranks the week's ideas by what scores best at each stage, keeps about 80% of
   the plan on proven patterns and 20% on tests, proposes three wild cards from `research/patterns.json` wild_cards or
   new ones, picks one, moves a promoted wild card into formats as in rotation, and retires an idea after two losses.
5. The Monday Plan run follows the brief: the week's hooks and formats from the top of the scores for each stage, the
   tests, and the wild card as one extra piece, `{week}-X1` in its brief and the piece's `experiment`. Changes to the
   format mix, pace or platforms still go through the Direction tab and Talha's ✅.
