# The LinkedIn engine

On 17 November 2026 Talha doubled LinkedIn to six posts a week from the week of 23 November and asked for "the same
research planning editing designing and writing system like we have for social media content ... for linkedin as
well to make sure our posts are going viral", self improving, trying one new thing a week. This folder is that
engine's research desk and memory. The posts themselves live in `linkedin/posts.json`; the LinkedIn posts doc is their
readable copy, which the LinkedIn daily run schedules from.

## The week, run by run

| When (Pakistan time) | Run | What it does for LinkedIn |
| --- | --- | --- |
| Friday 18:34 | LinkedIn daily run (First Leads Kit) | Reads each post of the week before in LinkedIn's analytics and writes it to the Growth Loop sheet's **LinkedIn posts** tab; reads the five peers' posts of the last seven days into the **LinkedIn peers** tab; updates What's working in the posts doc. |
| Monday 04:23 | Content Engine: Research desk | Turns those rows into `results/{week}.json`, runs `node tools/linkedin.mjs learn`, judges the last wild card, reads the peers, deadlines and news, and writes `briefs/{date}.json` and `.md`: ranked ideas, three wild cards with one pick, and the pace check. |
| Monday 06:47 | Content Engine: Plan, step 8a | Makes the images and documents for the LinkedIn posts of the week it plans from each post's design spec, checks them (`--media`), pushes, and adds the Image: and Document: paragraphs to the posts doc. |
| Thursday 14:17 | LinkedIn posts, next week (First Leads Kit) | Plans the next free week from the newest brief and the scores, researches every fact from primary sources, writes the six posts into `linkedin/posts.json`, edits them with `node tools/linkedin.mjs check` until they pass, pushes, and adds the week to the posts doc with `node tools/linkedin.mjs doc`. |
| Weekdays 18:34 | LinkedIn daily run | Schedules a week in LinkedIn's own scheduler once its Monday is six days away (images and documents attached), adds each weekday post's first comment. |
| Saturday and Sunday 19:15 | Content Engine: Social desk | Adds the first comment to the weekend post. |

## A post in `linkedin/posts.json`

```json
{
  "id": "LI-2026-12-04",
  "format": "linkedin_document",
  "date": "2026-12-04",
  "post": "Friday 4 December: what a Delaware corporation, a Delaware LLC and a Wyoming LLC pay every year",
  "stage": "top",
  "kind": "comparison",
  "pattern": "who_it_affects",
  "topic": "US company setup",
  "lighter": false,
  "experiment": "LIX-2026-W49-document",
  "format_hook": "comparison document, opens with who it is for",
  "text": ["the post, one paragraph per item"],
  "first_comment": "Sources: ... then one free resource with ?utm_source=linkedin&utm_medium=content_linkedin&utm_campaign=post_2026_12_04",
  "sources": [{"name": "...", "url": "https://...", "supports": "the figures, dates and rules this page supports"}],
  "sources_note": "what is worked from the sources, and the Claim Library IDs",
  "claims": ["DE-01"],
  "alt": "what the image or cover shows, under 250 characters",
  "content": {"the design spec": "see below"}
}
```

- `stage` is top or middle: posts never pitch (connect first, give value, then invite).
- `kind`, `pattern`, `topic`, `format`, `lighter` and the weekday are what the learning loop scores.
- `experiment` is set on the week's wild card only.

### Design specs (tools/studio/linkedin.py)

- `linkedin_image`: `kicker`, `lead`, `title` with `emph`, one `object` (cheque, bill, spread, or any carousel visual
  such as date, steps, checklist, compare) and up to three `points`.
- `linkedin_document`: `doc_title` (up to 58 characters, the title LinkedIn shows), `kicker`, `cover` (lead, title,
  emph, optional object), 3 to 8 `pages` (title, emph, text up to 60 words, optional object or points) and a `recap`
  (title and up to four items). It renders to `linkedin/media/{id}.pdf`, a JPEG of each page, and the cover as
  `{id}.jpg`, which the daily run attaches if the document upload fails.
- Every word and figure on an image or page comes from the post or its sources; a design never adds a fact.

## The rules the editor checks (`node tools/linkedin.mjs check`)

- The first paragraph is under 140 characters (150 at most): it is all a phone shows before "see more".
- Image posts 150 to 260 words; text posts 1,000+ characters; document posts 60 to 150 words.
- No link, hashtag, emoji, @ mention or dash in the post; hyphens only inside form and rule names such as 1099-NEC.
- A practical step, and a closing question; no comment-a-keyword, like, repost, tag or follow asks.
- No pitch, price or claim about the firm. No generic AI wording.
- The first comment starts with the sources, offers one free resource with its tracked link for the post's date, and
  stays under 1,250 characters.
- Every source is the publisher's own page, opened with WebFetch, with what it supports; every figure in the post is
  named in the sources or worked in the note.
- The week: six posts Monday to Saturday (a US federal holiday moves to Sunday), at most two lighter posts, one wild
  card, at least three kinds, and a document post while documents are being tested or in rotation.

## Learning (`node tools/linkedin.mjs learn`)

A post's score mixes impressions, comments, saves and sends, reactions, reposts, profile views and followers, and
website visits, each against the median of the last eight weeks' posts of the same format, so 1.0 is our usual.
Scores by tag (format, kind, pattern, topic, weekday, length, lighter) are weighted towards recent weeks and pulled
towards 1.0 until there is evidence (adj). The wild card is judged against the other posts of its week and the three
weeks before. The pace check compares each week's median impressions per post with the four weeks before: two weeks
running a third or more below, at six posts a week, and the Research desk asks Talha in #content whether to go back to
four a week. Nothing about the pace changes without his ✅.

## The Growth Loop sheet tabs the engine reads

- **LinkedIn posts**, A to P: Week of, Post date, Post id, Format, Impressions, Members reached, Reactions, Comments,
  Reposts, Saves, Sends, Profile viewers, Followers gained, Link visits, Read at, Note.
- **LinkedIn peers**, A to L: Week of, Peer, Profile, Post link, Posted, Format, First line (under 15 words), Topic,
  Reactions, Comments, Reposts, Read at.

## The Monday brief (`briefs/{date}.json`)

```json
{
  "made": "2026-11-23 04:40 PKT",
  "for_week": "the week the next Thursday run drafts, as its Monday",
  "inputs": {"posts_scored": 0, "peer_posts": 0, "peer_standouts": 0, "founder_questions": 0, "news": 0},
  "ideas": [{"rank": 1, "title": "", "format": "", "kind": "", "pattern": "", "topic": "", "hook": "", "claims": [], "why": "", "evidence": [{"kind": "ours | peer | founder | calendar | news | research", "detail": "", "link": ""}]}],
  "wild_cards": [{"idea": "", "what": "", "why": "", "needs": "", "pick": true}],
  "pace": {"median_impressions": null, "baseline": null, "change": null, "step_back": false},
  "scores_used": "",
  "patterns_changed": []
}
```
