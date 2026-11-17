// The LinkedIn engine's editor and learning loop (17 November 2026, when Talha asked for LinkedIn to get the same
// research, planning, writing, editing, design and self-improving system as the social media content, with one
// out-of-the-box test a week). Everything about a post lives in linkedin/posts.json; the posts doc is its readable copy.
//
//   node tools/linkedin.mjs check [--week 2026-11-30] [--id LI-2026-11-30] [--file other.json] [--media]
//        checks posts against the house rules and the research (research/linkedin/patterns.json); exit 1 on errors
//   node tools/linkedin.mjs doc --week 2026-11-30 [--file other.json] [--drafted 2026-11-19]
//        prints that week's markdown for the posts doc, built from the JSON so the two always match
//   node tools/linkedin.mjs results --week 2026-W49 --rows rows.json
//        turns the Growth Loop sheet's "LinkedIn posts" rows into research/linkedin/results/{week}.json
//   node tools/linkedin.mjs learn [--dry]
//        scores every tag from research/linkedin/results/*.json, judges each experiment, checks the pace
import { readFileSync, writeFileSync, readdirSync, existsSync, mkdirSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const POSTS = join(root, "linkedin", "posts.json");
const MEDIA = join(root, "linkedin", "media");
const RL = join(root, "research", "linkedin");
const RES = join(RL, "results");
const SCORES = join(RL, "scores.json");
const EXPS = join(RL, "experiments.json");
const RAW = "https://raw.githubusercontent.com/talhakhaan2550-pixel/fd-media/main/linkedin/media/";
const VIEW = "https://talhakhaan2550-pixel.github.io/fd-media/linkedin/media/";

const arg = (k) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : null; };
const has = (k) => process.argv.includes(k);

// ---------------------------------------------------------------- the vocabulary a post is tagged with
export const FORMATS = ["linkedin_image", "linkedin_document", "linkedin_text", "linkedin_video", "linkedin_poll"];
export const KINDS = ["deadline explainer", "rule explainer", "rule change explainer", "tax law change explainer", "worked example",
  "reference calendar", "checklist", "comparison", "myth versus fact", "data story", "lighter", "case breakdown", "question post"];
export const PATTERNS = ["question", "number", "deadline", "mistake", "myth", "contrast", "who_it_affects", "news",
  "expectation_reality", "nobody_founders", "investor_speak", "red_green_flag", "receipt_day", "story"];
export const STAGES = ["top", "middle"]; // posts never pitch (connect first, give value, then invite), so no bottom
const LIGHTER_PATTERNS = ["expectation_reality", "nobody_founders", "investor_speak", "red_green_flag", "receipt_day"];
const RESOURCES = ["/scorecard", "/do-i-need-to-file-a-1099", "/us-entry", "/sba-loan-package", "/funded-startups", "/books-cleanup",
  "/startup-tax-returns", "/rd-tax-credit", "/delaware-franchise-tax", "/1099-filing"];
const PRIMARY = ["irs.gov", "sec.gov", "investor.gov", "sba.gov", "fincen.gov", "federalregister.gov", "govinfo.gov", "uscode.house.gov",
  "ecfr.gov", "treasury.gov", "ssa.gov", "dol.gov", "bls.gov", "census.gov", "federalreserve.gov", "corp.delaware.gov", "legis.delaware.gov",
  "sos.wyo.gov", "wyobiz.wyo.gov", "ycombinator.com", "carta.com", "pitchbook.com", "fasb.org", "nvca.org", "congress.gov", "law.cornell.edu"];

// Engagement bait LinkedIn says it shows less of (Pressroom and Tim Jurka, 12 March 2026: "Comment 'Yes' if you agree")
// and our own rule: no post asks people to comment a keyword to receive something.
const BAIT = [/\bcomment\s+["“'‘]?[A-Z]{2,}["”'’]?/, /\b(type|reply|write)\s+["“'‘]?[A-Z]{2,}["”'’]?\s+(below|in the comments)/i,
  /\blike (this|if)\b/i, /\brepost (this|if)\b/i, /\btag (a|someone|your)\b/i, /\bshare (this|it) with\b/i, /\bfollow (me|for more)\b/i,
  /\bdrop an?\b/i, /\bagree\?\s*$/i, /\bthoughts\?\s*$/i, /\bsmash\b/i, /\blink in (the )?(first )?comment/i, /\bDM me\b/i];
// Wording that reads as generic AI text. LinkedIn's classifiers cut the spread of "AI slop" beyond the first network
// (Laura Lorenzetti, 20 May 2026; Tim Jurka, 8 October 2026: 40% fewer views for content classified as slop).
const SLOP = ["in today's", "fast-paced", "fast paced", "game changer", "game-changer", "delve", "unlock", "unleash", "navigate the",
  "landscape", "leverage", "it's not about", "here's the thing", "let that sink in", "buckle up", "dive in", "deep dive", "the secret",
  "nobody talks about", "most people don't know", "hidden gem", "elevate", "harness", "supercharge", "seamless", "robust",
  "in conclusion", "at the end of the day", "the truth is", "plot twist", "a testament", "tapestry", "embark", "realm",
  "ever-evolving", "ever evolving", "not just", "it's important to note", "crucial", "pivotal", "empower"];
const SLOP_HARD = new Set(["in today's", "game changer", "game-changer", "delve", "unleash", "let that sink in", "buckle up", "tapestry", "embark", "realm", "a testament"]);
const PITCH = [/\bFinance Department\b/, /\bour (firm|team|clients|services?|packages?|plans?)\b/i, /\bwe (offer|help|can help|provide)\b/i,
  /\bbook a (call|meeting)\b/i, /\bhire us\b/i, /\bcontact us\b/i];

// US federal holidays, worked out from the rules in 5 U.S.C. 6103 (observed on the Friday or Monday next to a weekend)
function nthWeekday(y, m, wd, n) { const d = new Date(Date.UTC(y, m, 1)); let c = 0; while (true) { if (d.getUTCDay() === wd && ++c === n) return d; d.setUTCDate(d.getUTCDate() + 1); } }
function lastWeekday(y, m, wd) { const d = new Date(Date.UTC(y, m + 1, 0)); while (d.getUTCDay() !== wd) d.setUTCDate(d.getUTCDate() - 1); return d; }
function observed(y, m, day) { const d = new Date(Date.UTC(y, m, day)); if (d.getUTCDay() === 6) d.setUTCDate(day - 1); if (d.getUTCDay() === 0) d.setUTCDate(day + 1); return d; }
export function holidays(y) {
  const iso = (d) => d.toISOString().slice(0, 10);
  return new Map([
    [iso(observed(y, 0, 1)), "New Year's Day"], [iso(nthWeekday(y, 0, 1, 3)), "Martin Luther King Jr. Day"],
    [iso(nthWeekday(y, 1, 1, 3)), "Washington's Birthday"], [iso(lastWeekday(y, 4, 1)), "Memorial Day"],
    [iso(observed(y, 5, 19)), "Juneteenth"], [iso(observed(y, 6, 4)), "Independence Day"], [iso(nthWeekday(y, 8, 1, 1)), "Labor Day"],
    [iso(nthWeekday(y, 9, 1, 2)), "Columbus Day"], [iso(observed(y, 10, 11)), "Veterans Day"], [iso(nthWeekday(y, 10, 4, 4)), "Thanksgiving Day"],
    [iso(observed(y, 11, 25)), "Christmas Day"]]);
}
const holidayOf = (date) => holidays(Number(date.slice(0, 4))).get(date) || null;
const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const dayOf = (date) => DAYS[new Date(date + "T12:00:00Z").getUTCDay()];
export function mondayOf(date) { const d = new Date(date + "T12:00:00Z"); const k = (d.getUTCDay() + 6) % 7; d.setUTCDate(d.getUTCDate() - k); return d.toISOString().slice(0, 10); }
export function isoWeek(date) {
  const d = new Date(date + "T12:00:00Z"); const day = (d.getUTCDay() + 6) % 7; d.setUTCDate(d.getUTCDate() - day + 3);
  const y = d.getUTCFullYear(); const jan4 = new Date(Date.UTC(y, 0, 4)); const w = 1 + Math.round(((d - jan4) / 864e5 - 3 + ((jan4.getUTCDay() + 6) % 7)) / 7);
  return `${y}-W${String(w).padStart(2, "0")}`;
}
const human = (date) => { const d = new Date(date + "T12:00:00Z"); return `${dayOf(date)} ${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`; };

const words = (s) => (s.match(/[A-Za-z0-9$%][A-Za-z0-9$%.,'’()/&-]*/g) || []).length;
const allowedHyphen = (tok) => /^[A-Z0-9]+(?:-[A-Z0-9]+)+[a-z]?$/.test(tok) || /^\d+(?:-\d+)+$/.test(tok) || /^[0-9]+-[A-Z]{1,4}$/.test(tok)
  || /^[A-Z][a-z]+-[A-Z]{2,}$/.test(tok)
  || /^(?:[A-Z]{1,4}|[0-9]{2,4})-[0-9A-Z]{1,6}(?:-[0-9A-Z]{1,6})*$/.test(tok);

function loadPosts(file) { const d = JSON.parse(readFileSync(file || POSTS, "utf8")); return d.pieces || []; }

// ---------------------------------------------------------------- check
export function checkPost(p, opts = {}) {
  const E = [], W = [];
  const text = (p.text || []).join("\n\n");
  if (!/^LI-\d{4}-\d{2}-\d{2}$/.test(p.id || "")) E.push("id must be LI-YYYY-MM-DD");
  if (!p.date || p.id !== `LI-${p.date}`) E.push("date and id must match");
  if (!FORMATS.includes(p.format)) E.push(`format must be one of ${FORMATS.join(", ")}`);
  if (!p.text || !p.text.length) {
    if (p.legacy || p.text_in_doc) return { E, W: ["made before the engine: its words are only in the posts doc"] };
    E.push("text is missing (a list of paragraphs)"); return { E, W };
  }
  const hol = holidayOf(p.date);
  if (hol) E.push(`${p.date} is ${hol} in the US: use that week's Sunday instead`);
  if (!p.post || !p.post.startsWith(human(p.date))) E.push(`post (the doc heading) must start "${human(p.date)}:"`);
  // the hook: the first paragraph is what shows before "see more" (about 140 characters on mobile, 210 on desktop)
  const hook = p.text[0];
  if (hook.length > 150) E.push(`hook is ${hook.length} characters; keep the first paragraph under 150 so it shows before "see more" on a phone`);
  else if (hook.length > 140) W.push(`hook is ${hook.length} characters; under 140 shows whole on every phone`);
  const n = words(text);
  const [lo, hi, wlo, whi] = p.format === "linkedin_document" ? [40, 220, 60, 150] : p.format === "linkedin_poll" ? [40, 160, 40, 160] : [150, 300, 150, 260];
  if (n < lo || n > hi) E.push(`${n} words; a ${p.format.replace("linkedin_", "")} post has ${lo} to ${hi}`);
  else if (n < wlo || n > whi) W.push(`${n} words; the house range for this format is ${wlo} to ${whi}`);
  if (p.format === "linkedin_text" && text.length < 1000) W.push(`${text.length} characters; text posts of 1,000 or more reached 1.18 times the usual (AuthoredUp)`);
  if (text.length > 3000) E.push(`${text.length} characters, over LinkedIn's 3,000`);
  if (/https?:\/\/|www\./i.test(text)) E.push("a link in the post: links go in the first comment");
  if (/(^|\s)#[A-Za-z]/.test(text)) E.push("a hashtag in the post");
  if (/(^|\s)@[A-Za-z]/.test(text)) E.push("an @ mention in the post");
  if (/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u.test(text)) E.push("an emoji in the post");
  if (/[—–]/.test(text) || / - /.test(text)) E.push("a dash in the post: plain English with no dashes");
  for (const tok of text.match(/[A-Za-z0-9.()]+(?:-[A-Za-z0-9()]+)+/g) || []) if (!allowedHyphen(tok.replace(/[.()]+$/g, "").replace(/^\(|\)$/g, ""))) E.push(`hyphen in "${tok}": hyphens only inside form and rule names such as 1099-NEC`);
  const last = p.text[p.text.length - 1].trim();
  if (!last.endsWith("?")) E.push("the last paragraph must be a question founders would want to answer");
  for (const re of BAIT) if (re.test(text)) E.push(`engagement bait (${re.source}): LinkedIn shows less of it`);
  for (const re of PITCH) if (re.test(text)) E.push(`reads as a pitch or a claim about the firm (${re.source}): posts give value only`);
  const low = text.toLowerCase();
  for (const s of SLOP) if (low.includes(s)) (SLOP_HARD.has(s) ? E : W).push(`"${s}" reads as generic AI wording`);
  if (/\$\s?\d/.test(text) && /\b(price|fee for our|our fee|starting at|per month for)\b/i.test(text)) E.push("a price for a service: posts never quote our prices");
  if (!/\b(what to do|the practical step|before you|this week|this month|today)\b/i.test(text)) W.push("no practical step a founder can take (\"What to do ...\")");
  // the first comment: sources first, then one free resource with its tracked link
  const fc = p.first_comment || "";
  if (!fc) E.push("first_comment is missing");
  else {
    if (!fc.startsWith("Sources:") && !fc.startsWith("Source:")) E.push('first_comment must start "Sources:"');
    if (fc.length > 1250) E.push(`first_comment is ${fc.length} characters, over LinkedIn's 1,250 for a comment`);
    const site = fc.match(/https:\/\/www\.financedepartmentllc\.com(\/[a-z0-9-]*)?\?utm_source=linkedin&utm_medium=content_linkedin&utm_campaign=post_(\d{4})_(\d{2})_(\d{2})/);
    if (!site) E.push("first_comment needs one free resource link with ?utm_source=linkedin&utm_medium=content_linkedin&utm_campaign=post_YYYY_MM_DD");
    else {
      if (`${site[2]}-${site[3]}-${site[4]}` !== p.date) E.push(`utm_campaign date ${site[2]}_${site[3]}_${site[4]} does not match the post date`);
      if (!RESOURCES.includes(site[1] || "/")) W.push(`resource ${site[1] || "/"} is not one of the free resources the runs know`);
    }
    if ((fc.match(/financedepartmentllc\.com/g) || []).length > 1) E.push("first_comment offers more than one resource");
  }
  // sources: every page relied on, opened with WebFetch, with what it supports
  const src = p.sources || [];
  if (!src.length) E.push("sources are missing");
  for (const s of src) {
    if (!/^https:\/\//.test(s.url || "")) E.push(`source "${s.name}" has no https address`);
    else if (!PRIMARY.some((d) => new URL(s.url).hostname.endsWith(d))) W.push(`source ${new URL(s.url).hostname} is not on the primary list: check it is the publisher's own page`);
    if (!s.supports) E.push(`source "${s.name}" does not say which figures and rules it supports`);
  }
  // every figure in the post appears in what the sources support, or is worked in the note
  const support = (src.map((s) => s.supports + " " + s.name).join(" ") + " " + (p.sources_note || "")).toLowerCase();
  const figs = new Set((text.match(/\$\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s(?:million|billion))?|\$\d+(?:\.\d+)?|\d+(?:\.\d+)?%|\b\d{1,3}(?:,\d{3})+\b/g) || []));
  for (const f of figs) { const bare = f.toLowerCase().replace(/\.00\b/, ""); if (!support.includes(bare) && !support.includes(bare.replace(/,/g, ""))) W.push(`figure ${f} is not named in the sources or the note: check it is sourced or worked`); }
  // the tags the learning loop scores
  if (!KINDS.includes(p.kind)) E.push(`kind must be one of: ${KINDS.join(", ")}`);
  if (!PATTERNS.includes(p.pattern)) E.push(`pattern must be one of: ${PATTERNS.join(", ")}`);
  if (!STAGES.includes(p.stage)) E.push(`stage must be top or middle (posts never pitch)`);
  if (!p.topic) E.push("topic is missing");
  if (typeof p.lighter !== "boolean") E.push("lighter must be true or false");
  if (p.lighter && !LIGHTER_PATTERNS.includes(p.pattern)) E.push(`a lighter post uses one of the lighter formats: ${LIGHTER_PATTERNS.join(", ")}`);
  if (!p.format_hook) E.push("format_hook (the doc's Format and hook line) is missing");
  if (p.experiment && !/^LIX-\d{4}-W\d{2}-[a-z0-9_]+$/.test(p.experiment)) E.push("experiment id must be LIX-YYYY-Www-idea");
  // the design
  if (["linkedin_image", "linkedin_document"].includes(p.format)) {
    if (!p.content) E.push("content (the design spec) is missing");
    if (!p.alt) E.push("alt text is missing");
    else if (p.alt.length > 250) W.push(`alt text is ${p.alt.length} characters; keep it under 250`);
    if (p.format === "linkedin_document" && !(p.content || {}).doc_title) E.push("a document needs content.doc_title (LinkedIn asks for one)");
    const ob = (p.content || {}).object;
    if (ob && ob.type === "cast") {
      // the cartoon cast (the cast_comic wild card): it says only the post's own words, never plays a real person
      const flat = (x) => String(x).toLowerCase().replace(/[^a-z0-9$%]+/g, " ").trim();
      if (!ob.says || ob.says.length > 90) E.push("the cast's speech bubble (says) needs words from the post, up to 90 characters");
      else if (!flat(text).includes(flat(ob.says))) E.push("the cast's speech bubble must repeat words from the post exactly");
      if ([].concat(ob.who || []).length > 3) E.push("a cast image shows at most three characters");
      if ((((p.content || {}).points || {}).items || []).length > 2) E.push("a cast image takes at most two points, so the cast and the photo fit");
    }
    if (opts.media) {
      const need = p.format === "linkedin_document" ? [`${p.id}.pdf`, `${p.id}.jpg`] : [`${p.id}.jpg`];
      for (const f of need) { const fp = join(MEDIA, f); if (!existsSync(fp)) E.push(`linkedin/media/${f} is not made yet`); else if (statSync(fp).size < 50000) E.push(`linkedin/media/${f} is under 50 KB`); }
    }
  }
  if (p.format === "linkedin_poll") {
    const o = p.poll || {};
    if (!o.question || o.question.length > 140) E.push("a poll needs a question of up to 140 characters");
    if (!Array.isArray(o.options) || o.options.length < 2 || o.options.length > 4 || o.options.some((x) => x.length > 30)) E.push("a poll needs 2 to 4 options of up to 30 characters");
    W.push("polls reach far but earn little engagement (AuthoredUp: 1.78 times reach, 0.37 times engagement): only as a test");
  }
  return { E, W };
}

export function checkWeek(posts, monday) {
  const E = [], W = [];
  const wk = posts.filter((p) => mondayOf(p.date) === monday).sort((a, b) => a.date.localeCompare(b.date));
  if (!wk.length) return { E: [`no posts in the week of ${monday}`], W };
  const dates = wk.map((p) => p.date);
  if (new Set(dates).size !== dates.length) E.push("two posts on one day");
  if (wk.length > 6) E.push(`${wk.length} posts; six a week at most`);
  const sundays = wk.filter((p) => dayOf(p.date) === "Sunday");
  const holidaysIn = [0, 1, 2, 3, 4, 5].map((k) => { const d = new Date(monday + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + k); return d.toISOString().slice(0, 10); }).filter(holidayOf);
  if (sundays.length > holidaysIn.length) E.push("a Sunday post without a US holiday that week");
  if (wk.filter((p) => p.lighter).length > 2) E.push("more than two lighter posts in the week");
  if (wk.filter((p) => p.experiment).length > 1) E.push("more than one experiment in the week: one wild card a week");
  for (let i = 1; i < wk.length; i++) if (wk[i].topic === wk[i - 1].topic) W.push(`${wk[i - 1].date} and ${wk[i].date} share the topic "${wk[i].topic}"`);
  if (new Set(wk.map((p) => p.kind)).size < Math.min(3, wk.length)) W.push("fewer than three kinds of post in the week");
  if (wk.length >= 4 && !wk.some((p) => p.format === "linkedin_document")) W.push("no document post this week: documents had the highest reach and engagement multipliers (AuthoredUp)");
  return { E, W, count: wk.length };
}

function cmdCheck() {
  const posts = loadPosts(arg("--file"));
  let sel = posts;
  const week = arg("--week"), id = arg("--id");
  if (week) sel = sel.filter((p) => mondayOf(p.date) === mondayOf(week));
  if (id) sel = sel.filter((p) => p.id === id);
  // posts made before the engine (10 to 25 November) carry no tags: check those only on request
  if (!week && !id) sel = sel.filter((p) => p.text);
  let errors = 0;
  const out = [];
  for (const p of sel) {
    const r = checkPost(p, { media: has("--media") });
    errors += r.E.length;
    out.push({ id: p.id, status: r.E.length ? "Held" : "Made", errors: r.E, warnings: r.W });
  }
  const weeks = [...new Set(sel.map((p) => mondayOf(p.date)))];
  const wk = weeks.map((m) => { const r = checkWeek(posts.filter((p) => p.text || mondayOf(p.date) === m), m); errors += r.E.length; return { week_of: m, posts: r.count, errors: r.E, warnings: r.W }; });
  console.log(JSON.stringify({ checked: out.length, errors, posts: out, weeks: wk }, null, 2));
  process.exit(errors ? 1 : 0);
}

// ---------------------------------------------------------------- doc: the week's markdown for the posts doc
export function postMarkdown(p) {
  const out = [`## ${p.post}`];
  out.push(p.text.map((x, i) => (i ? ">\n> " : "> ") + x).join("\n"));
  out.push(`**First comment:** ${p.first_comment}`);
  let src = (p.sources || []).map((s) => `[${s.name}](${s.url}) (${s.supports})`).join(" · ");
  if (p.sources_note) src += `. ${p.sources_note}`;
  out.push(`**Sources:** ${src}`);
  out.push(`**Format and hook:** ${p.format_hook}${p.experiment ? ` (this week's test, ${p.experiment})` : ""}`);
  // the Image: and Document: paragraphs go in only once their files are made (the Monday plan run makes them and adds
  // the paragraphs for posts the Thursday run drafted), so the daily run never meets a link to a missing file
  const made = (f) => existsSync(join(MEDIA, f));
  if (p.format === "linkedin_document" && made(`${p.id}.pdf`)) out.push(`**Document:** ${RAW}${p.id}.pdf ([see it](${VIEW}${p.id}.pdf)). Title: ${p.content.doc_title}`);
  if (["linkedin_image", "linkedin_document"].includes(p.format) && made(`${p.id}.jpg`)) out.push(`**Image:** ${RAW}${p.id}.jpg ([see it](${VIEW}${p.id}.jpg)). Alt text: ${p.alt}`);
  if (p.format === "linkedin_poll") out.push(`**Poll:** ${p.poll.question} | ${p.poll.options.join(" | ")} | ${p.poll.duration || "1 week"}`);
  return out.join("\n\n");
}

function cmdDoc() {
  const posts = loadPosts(arg("--file"));
  const monday = mondayOf(arg("--week"));
  const only = arg("--ids") ? arg("--ids").split(",") : null;
  const wk = posts.filter((p) => mondayOf(p.date) === monday && p.text && (!only || only.includes(p.id))).sort((a, b) => a.date.localeCompare(b.date));
  const drafted = arg("--drafted");
  const head = [`## Week of ${human(monday)}`];
  if (drafted) {
    const hol = wk.find((p) => dayOf(p.date) === "Sunday");
    head.push(`Drafted on ${human(drafted).replace(/^\w+ /, "")} ${drafted.slice(0, 4)}. The LinkedIn daily run schedules these ${["no", "one", "two", "three", "four", "five", "six"][wk.length] || wk.length} posts for 6:30 pm your time once the week is six days away. Change any words before then, or add a paragraph starting Hold: under this heading to stop the week.${hol ? " A US holiday falls in this week, so one post runs on Sunday instead." : ""}`);
  }
  console.log([...(only ? [] : head), ...wk.map(postMarkdown)].join("\n\n"));
}

// ---------------------------------------------------------------- results: the sheet's rows to a results file
// Each row of the Growth Loop sheet's "LinkedIn posts" tab, written by the LinkedIn daily run on Fridays from each
// post's analytics: Post date, Post id, Impressions, Members reached, Reactions, Comments, Reposts, Saves, Sends,
// Profile viewers, Followers gained, Link visits (HubSpot, utm_campaign post_YYYY_MM_DD), Read at, Hours live, Note.
function cmdResults() {
  const week = arg("--week");
  const rows = JSON.parse(readFileSync(arg("--rows"), "utf8"));
  const posts = loadPosts();
  const num = (x) => (x === "" || x == null || Number.isNaN(Number(String(x).replace(/,/g, ""))) ? null : Number(String(x).replace(/,/g, "")));
  const pieces = [];
  for (const r of rows) {
    const id = r.post_id || r["Post id"]; const p = posts.find((x) => x.id === id);
    if (!p) continue;
    pieces.push({ id, date: p.date, format: p.format, kind: p.kind || null, pattern: p.pattern || null, stage: p.stage || "top", topic: p.topic || null,
      lighter: !!p.lighter, experiment: p.experiment || null, weekday: dayOf(p.date), words: p.text ? words(p.text.join(" ")) : null,
      impressions: num(r.impressions ?? r["Impressions"]), reached: num(r.reached ?? r["Members reached"]), reactions: num(r.reactions ?? r["Reactions"]),
      comments: num(r.comments ?? r["Comments"]), reposts: num(r.reposts ?? r["Reposts"]), saves: num(r.saves ?? r["Saves"]), sends: num(r.sends ?? r["Sends"]),
      profile_viewers: num(r.profile_viewers ?? r["Profile viewers"]), followers: num(r.followers ?? r["Followers gained"]),
      visits: num(r.visits ?? r["Link visits"]), hours_live: num(r.hours_live ?? r["Hours live"]) });
  }
  mkdirSync(RES, { recursive: true });
  const out = join(RES, `${week}.json`);
  writeFileSync(out, JSON.stringify({ week, written: new Date().toISOString(), pieces }, null, 2) + "\n");
  console.log(JSON.stringify({ wrote: out, pieces: pieces.length }));
}

// ---------------------------------------------------------------- learn: scores, experiments and the pace check
// A post's score is a weighted mix of its counts against the median of the last eight weeks' posts of the same format,
// so 1.0 is our usual and 1.5 is half again better. Weights follow what LinkedIn says it ranks on (long dwells,
// comments and shares, March 2026) and what brings founders to us (profile views, followers, visits).
export const GOAL = { impressions: 0.3, comments: 0.15, saves_sends: 0.2, reactions: 0.05, reposts: 0.05, profile: 0.15, visits: 0.1 };
const HALF_LIFE_WEEKS = 4, PRIOR = 3, WIN = 1.25, STRONG_WIN = 1.5, LOSS = 0.8, READABLE = 150;
const median = (xs) => { const v = xs.filter((x) => typeof x === "number" && Number.isFinite(x)).sort((a, b) => a - b); if (!v.length) return null; const m = Math.floor(v.length / 2); return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2; };
const wn = (w) => { const m = /^(\d{4})-W(\d{2})$/.exec(w || ""); return m ? Number(m[1]) * 53 + Number(m[2]) : 0; };
function rates(x) {
  // counts, not rates per impression: a post that travels far reaches colder readers, so its rates fall even as it
  // brings more comments, saves and profile views; the goal is the counts
  const r = { impressions: x.impressions };
  if (x.comments != null) r.comments = x.comments;
  if (x.saves != null || x.sends != null) r.saves_sends = (x.saves || 0) + (x.sends || 0);
  if (x.reactions != null) r.reactions = x.reactions;
  if (x.reposts != null) r.reposts = x.reposts;
  if (x.profile_viewers != null || x.followers != null) r.profile = (x.profile_viewers || 0) + 3 * (x.followers || 0);
  if (x.visits != null) r.visits = x.visits;
  return r;
}
const lengthBucket = (n) => (n == null ? null : n < 150 ? "under 150" : n <= 200 ? "150 to 200" : n <= 260 ? "201 to 260" : "over 260");

export function learn(weeks) {
  weeks = [...weeks].sort((a, b) => wn(a.week) - wn(b.week));
  const last = weeks.length ? weeks[weeks.length - 1].week : null;
  const all = weeks.flatMap((w) => (w.pieces || []).map((p) => ({ week: w.week, p, r: rates(p) })));
  const base = (week, format, key) => median(all.filter((x) => x.p.format === format && wn(x.week) <= wn(week) && wn(x.week) > wn(week) - 8).map((x) => x.r[key]));
  const scored = [];
  for (const x of all) {
    const parts = {}; let total = 0, wsum = 0;
    for (const [key, wt] of Object.entries(GOAL)) {
      if (x.r[key] == null) continue;
      const b = base(x.week, x.p.format, key);
      const v = key === "impressions" ? (b && b > 0 ? x.r[key] / b : null) : (x.r[key] + 0.5) / ((b || 0) + 0.5);
      if (v == null) continue;
      parts[key] = +Math.min(4, v).toFixed(2); total += wt * Math.min(4, v); wsum += wt;
    }
    if (!wsum) continue;
    scored.push({ week: x.week, id: x.p.id, score: +(total / wsum).toFixed(3), parts, impressions: x.p.impressions || 0, experiment: x.p.experiment,
      tags: { format: x.p.format, kind: x.p.kind, pattern: x.p.pattern, topic: x.p.topic, stage: x.p.stage, weekday: x.p.weekday, lighter: String(x.p.lighter), length: lengthBucket(x.p.words) } });
  }
  const acc = {};
  for (const s of scored) {
    const wt = Math.pow(0.5, (last ? wn(last) - wn(s.week) : 0) / HALF_LIFE_WEEKS);
    for (const [k, v] of Object.entries(s.tags)) {
      if (v == null || v === "null") continue;
      const t = ((acc[k] = acc[k] || {})[v] = acc[k][v] || { sum: 0, w: 0, n: 0, last: null });
      t.sum += wt * s.score; t.w += wt; t.n += 1; if (!t.last || wn(s.week) > wn(t.last)) t.last = s.week;
    }
  }
  const by_tag = {}, picks = {};
  for (const [k, vals] of Object.entries(acc)) {
    by_tag[k] = {};
    for (const [v, t] of Object.entries(vals)) by_tag[k][v] = { score: +(t.sum / t.w).toFixed(3), adj: +((t.sum + PRIOR) / (t.w + PRIOR)).toFixed(3), n: t.n, last: t.last };
    picks[k] = Object.entries(by_tag[k]).map(([id, t]) => ({ id, adj: t.adj, n: t.n })).sort((a, b) => b.adj - a.adj || b.n - a.n);
  }
  // pace: median impressions per post each week against the four weeks before; two weeks a third below steps back
  const weekly = weeks.map((w) => ({ week: w.week, posts: (w.pieces || []).length, median_impressions: median((w.pieces || []).map((p) => p.impressions)) }));
  const pace = weekly.map((w, i) => {
    const prev = weekly.slice(Math.max(0, i - 4), i).map((x) => x.median_impressions);
    const b = prev.filter((x) => x != null).length >= 2 ? median(prev) : null;
    return { ...w, baseline: b, change: b ? +((w.median_impressions - b) / b).toFixed(2) : null };
  });
  const lastTwo = pace.slice(-2);
  const step_back = lastTwo.length === 2 && lastTwo.every((w) => w.change != null && w.change <= -1 / 3 && w.posts >= 5);
  return { last, scored, by_tag, picks, pace, step_back };
}

export function judge(e, scored) {
  const me = scored.find((s) => s.id === e.post);
  if (!me) return { verdict: "not readable", why: "no results for its post yet" };
  if (me.impressions < READABLE) return { verdict: "not readable", why: `${me.impressions} impressions is too few to judge`, score: me.score };
  const peers = scored.filter((s) => s.id !== me.id && !s.experiment && wn(s.week) <= wn(me.week) && wn(s.week) > wn(me.week) - 4);
  const b = median(peers.map((s) => s.score));
  if (!b) return { verdict: "not readable", why: "no other posts to compare with", score: me.score };
  const ratio = me.score / b;
  return { verdict: ratio >= WIN ? "win" : ratio <= LOSS ? "loss" : "inconclusive", strong: ratio >= STRONG_WIN, score: me.score, baseline: +b.toFixed(3), ratio: +ratio.toFixed(2), parts: me.parts, compared_with: peers.length };
}

function cmdLearn() {
  const weeks = existsSync(RES) ? readdirSync(RES).filter((f) => /^\d{4}-W\d{2}\.json$/.test(f)).map((f) => JSON.parse(readFileSync(join(RES, f), "utf8"))) : [];
  const L = learn(weeks);
  const exps = existsSync(EXPS) ? JSON.parse(readFileSync(EXPS, "utf8")) : { experiments: [] };
  const changed = [];
  for (const e of exps.experiments || []) {
    if (!e.post || (e.result && ["win", "loss"].includes(e.result.verdict))) continue;
    const r = judge(e, L.scored);
    if (JSON.stringify(r) !== JSON.stringify(e.result || null)) { e.result = { ...r, judged: L.last }; changed.push(`${e.id}: ${r.verdict}${r.ratio ? ` (${r.ratio} times our usual)` : ""}`); }
    const wins = (exps.experiments || []).filter((x) => x.idea === e.idea && x.result && x.result.verdict === "win");
    e.promote = wins.some((x) => x.result.strong) || wins.length >= 2;
  }
  const scores = { about: "Written by node tools/linkedin.mjs learn from research/linkedin/results/*.json. adj is the score pulled towards 1.0 (our usual) until a tag has evidence; rank by adj. Goal weights: " + JSON.stringify(GOAL), updated: L.last, half_life_weeks: HALF_LIFE_WEEKS, by_tag: L.by_tag, picks: L.picks, pace: L.pace, step_back: L.step_back, posts: L.scored.slice(-90) };
  if (!has("--dry")) { mkdirSync(RL, { recursive: true }); writeFileSync(SCORES, JSON.stringify(scores, null, 2) + "\n"); writeFileSync(EXPS, JSON.stringify(exps, null, 2) + "\n"); }
  const top = Object.fromEntries(Object.entries(L.picks).filter(([k]) => ["format", "kind", "pattern", "topic", "weekday"].includes(k)).map(([k, v]) => [k, v.slice(0, 3)]));
  console.log(JSON.stringify({ weeks: weeks.map((w) => w.week), posts_scored: L.scored.length, experiments_judged: changed, best: top, pace: L.pace.slice(-3), step_back: L.step_back, wrote: has("--dry") ? [] : ["research/linkedin/scores.json", "research/linkedin/experiments.json"] }, null, 2));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const cmd = process.argv[2];
  if (cmd === "check") cmdCheck();
  else if (cmd === "doc") cmdDoc();
  else if (cmd === "results") cmdResults();
  else if (cmd === "learn") cmdLearn();
  else { console.error("usage: node tools/linkedin.mjs check|doc|results|learn (see the top of this file)"); process.exit(2); }
}
