// The automatic half of the quality check. It reads a week's pieces file and the month's approved claim IDs
// and lists every rule a piece breaks. The other half (does each sentence match its claim, does the piece
// read well, do the frames look right) is the run's own judgment, set out in the kit's Quality check tab.
//
//   node tools/check.mjs weeks/2026-W45/pieces.json claims.json [--only 2026-W45-E01,2026-W45-C01]
//   claims.json: { "tab": "November 2026", "approved": ["1099-01", ...], "firm": ["FD-01", ...] }
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const config = JSON.parse(readFileSync(join(here, "config.json"), "utf8"));

export const FORMAT_PLATFORMS = {
  explainer: ["youtube", "instagram", "facebook", "tiktok", "linkedin", "x", "threads"],
  ad: ["youtube", "instagram", "facebook", "tiktok", "linkedin", "x", "threads"],
  reel: ["youtube", "instagram", "facebook", "tiktok", "x", "threads"],
  cut: ["youtube", "instagram", "facebook", "tiktok", "x", "threads"],
  avatar: ["youtube", "instagram", "facebook", "tiktok", "x", "threads"],
  carousel: ["instagram", "facebook", "tiktok", "linkedin", "x", "threads"],
  carousel_reel: ["youtube", "instagram", "facebook", "tiktok"],
  story: ["instagram", "facebook"],
  text: ["facebook", "linkedin", "x", "threads"],
};
const LETTER = { reel: "Y", cut: "Y", explainer: "E", ad: "D", avatar: "A", carousel: "C", carousel_reel: "M", story: "S", text: "T" };
const CAPTION_MAX = { x: 280, threads: 500, instagram: 2200, tiktok: 2200, facebook: 5000, linkedin: 3000 };
const HASHTAGS = { instagram: [3, 5], tiktok: [3, 5], threads: [1, 1], x: [0, 2], facebook: [0, 0], youtube: [0, 3], linkedin: [0, 3] };
const DISCLAIMER = "General information, not tax or legal advice for your situation.";
// [words, why, and the approved firm claims whose own wording carries those words: a piece that cites one of them
// may use them]. Talha, 15 November 2026: posts may use the approved wording of the written guarantees and of the
// tax return and Form 5472 offers; return work starts once the firm's PTIN is active.
// Claims Talha has struck: never used, whatever claims.json says.
const STRUCK = new Set(["FD-29"]);

const BANNED = [
  [/\bthe finance department\b/i, 'the name is "Finance Department", never "The Finance Department"'],
  [/\bCPA\b/, '"CPA" is not a title anyone here holds'],
  [/\bbig (4|four)\b/i, '"Big 4" may not be used'],
  [/\b5[- ]star|\bfive[- ]star/i, 'star ratings may not be used'],
  [/\bguarantee/i, '"guarantee" only in the approved wording of FD-14, with that claim listed', ["FD-14"]],
  // Talha, 15 November 2026: the firm's old line is struck everywhere, posts included; FD-30 is the firm's line.
  [/every service has a fixed price and a written guarantee/i, 'the old line "Every service has a fixed price and a written guarantee" (FD-29) is struck; the firm\'s line is FD-30'],
  [/\b(150\+|50\+)\s*(businesses|clients|founders)?/i, 'old client figures; the only one is "300+ founders"'],
  [/\bintroduc\w* (you )?to investors\b|\binvestor introductions?\b/i, 'the firm does not introduce investors'],
  [/\byou will raise\b|\bwe('ll| will) raise\b/i, 'no promised outcomes'],
  [/\b(prepare|file|do) your (tax return|1120|form 5472|5472)\b|\btax return preparation\b/i, 'tax return and Form 5472 offers only in their approved wording (FD-16, FD-18, FD-20, FD-22, FD-23 or FD-28), with that claim listed', ["FD-16", "FD-18", "FD-20", "FD-22", "FD-23", "FD-28"]],
  [/\b(we|the firm|finance department)( now| already)? (hold|holds|have|has) (a |an |our |its )?(PTIN|EFIN)\b|\bour (PTIN|EFIN)\b|\bauthori[sz]ed (IRS )?e-?file provider\b/i, 'never say the firm holds a PTIN or IRS e-file authorization'],
  [/\b\d+% (in )?(tax )?savings?\b|\bsave \d+%/i, 'no tax savings figures'],
];
const DASH = /[‒–—―]| - /;

// Every string inside a value (visuals and scenes are nested objects).
const strings = (v) => typeof v === "string" ? [v] : Array.isArray(v) ? v.flatMap(strings) : v && typeof v === "object" ? Object.values(v).flatMap(strings) : [];
// The piece's own words: what visuals and scenes may show again.
const ownWords = (p) => {
  const c = p.content || {};
  return [c.kicker, c.hook, ...(c.lines || []), c.offer, c.cta, c.text,
    ...(c.slides || []).flatMap((s) => [s.kicker, s.title, s.body, s.cta, s.footer])].filter((x) => typeof x === "string").join("\n");
};
const SCENE_TYPES = ["headline", "stat", "doc", "route", "date", "ladder", "alert", "compare", "checklist", "map", "icons", "steps", "quote", "gauge", "promise", "end"];
const VISUAL_TYPES = ["map", "stats", "date", "bars", "quote", "hero", "chips", "threshold", "split", "tiles", "list", "steps", "compare", "checklist", "cast"];
// Figures that matter: money, percentages, numbers of two digits or more and years.
const FIGS = /\$[\d,.]+(?:\s?(?:million|billion|M|K))?|\d[\d,.]*%|\b\d{1,3}(?:,\d{3})+\b|\b\d{2,}(?:\.\d+)?(?=s?\b)/g;
// Money keeps its $ and percentages their %, so $65 never passes for a 65 elsewhere; plain one and two digit
// numbers (days on a calendar) are not checked.
const figureSet = (s) => new Set((s.match(FIGS) || []).map((f) => f.replace(/[.,]+$/, "").replace(/[,\s]|million|billion/g, "")));
const allText = (p) => {
  const c = p.content || {};
  const parts = [c.kicker, c.hook, ...(c.lines || []), c.offer, c.cta, c.text, ...(c.slides || []).flatMap((s) => Object.entries(s).filter(([k]) => k !== "layout").flatMap(([, v]) => strings(v))),
    ...strings(c.scenes || []), ...strings(c.say || {})];
  for (const [k, v] of Object.entries(p.captions || {})) parts.push(typeof v === "string" ? v : [v.title, v.description].join(" "));
  return parts.filter((x) => typeof x === "string").join("\n");
};

function eastern(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime()) || !/[+-]\d{2}:\d{2}$|Z$/.test(iso)) return null;
  const parts = Object.fromEntries(new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour12: false, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })
    .formatToParts(d).map((x) => [x.type, x.value]));
  return { day: `${parts.year}-${parts.month}-${parts.day}`, hour: Number(parts.hour) % 24 + Number(parts.minute) / 60, ms: d.getTime() };
}

export function checkPiece(p, claims, week) {
  const errors = [], warnings = [];
  const fmt = p.format;
  if (!FORMAT_PLATFORMS[fmt]) errors.push(`unknown format ${fmt}`);
  if (!new RegExp(`^${week.week}-${LETTER[fmt] || "?"}\\d{2}$`).test(p.id || "")) errors.push(`id ${p.id} must be ${week.week}-${LETTER[fmt] || "?"}NN`);
  if (p.test && !/^TEST /.test(p.title || "")) errors.push('a TEST piece\'s title starts with "TEST "');
  const allowed = (FORMAT_PLATFORMS[fmt] || []).filter((n) => config.platforms_enabled.includes(n));
  for (const n of p.platforms || []) if (!allowed.includes(n)) errors.push(`${fmt} cannot go to ${n}${config.platforms_enabled.includes(n) ? "" : " (not switched on yet)"}`);
  if (!p.platforms || !p.platforms.length) errors.push("no platforms");
  // Claims
  const ok = new Set([...(claims.approved || []), ...(claims.firm || [])]);
  const used = p.claims || [];
  if (!used.length) warnings.push("no claims listed: the piece must state no facts at all");
  for (const id of used) if (!ok.has(id)) errors.push(`claim ${id} is not approved in ${claims.tab}`);
  for (const id of used) if (STRUCK.has(id)) errors.push(`claim ${id} is struck in the Claim Library`);
  // Words
  const text = allText(p);
  for (const [re, why, allowedBy] of BANNED) if (re.test(text) && !(allowedBy || []).some((id) => used.includes(id) && ok.has(id))) errors.push(why);
  if (DASH.test(text)) errors.push("a dash is used as punctuation; rewrite the sentence (hyphens inside names such as 1099-NEC are fine)");
  if (/\bchartered accountant\b/i.test(text) && !/working towards qualifying as a Chartered Accountant with ICAP/.test(text)) errors.push('"Chartered Accountant" only in the FD-03 wording');
  if (/success fee/i.test(text) && !/do not introduce investors or take a success fee/i.test(text)) warnings.push('"success fee" outside the FD-05 wording: check it says the firm takes none');
  // Captions
  const needsDisclaimer = used.some((id) => !id.startsWith("FD-"));
  for (const n of p.platforms || []) {
    if (fmt === "story") continue; // stories carry no caption
    const cap = (p.captions || {})[n];
    if (n === "youtube") {
      if (!cap || !cap.title || !cap.description) { errors.push("youtube needs a title and a description"); continue; }
      if (cap.title.length > 100) errors.push(`youtube title is ${cap.title.length} characters, over 100`);
    } else if (typeof cap !== "string" || !cap.trim()) { errors.push(`no ${n} caption`); continue; }
    const body = n === "youtube" ? `${cap.title}\n${cap.description}` : cap;
    if (CAPTION_MAX[n] && body.length > CAPTION_MAX[n]) errors.push(`${n} caption is ${body.length} characters, over ${CAPTION_MAX[n]}`);
    const tags = (body.match(/(^|\s)#[A-Za-z0-9_]+/g) || []).length;
    const [lo, hi] = HASHTAGS[n];
    if (tags < lo || tags > hi) errors.push(`${n} has ${tags} hashtags; ${lo === hi ? lo : `${lo} to ${hi}`} allowed`);
    if (needsDisclaimer && !body.includes(DISCLAIMER)) errors.push(`${n} caption lacks "${DISCLAIMER}"`);
    const urls = body.match(/https?:\/\/\S+/g) || [];
    if ((n === "instagram" || n === "tiktok") && (urls.length || /www\./i.test(body))) errors.push(`${n} captions cannot carry links; say "link in bio"`);
    // Every YouTube post is a Short, and YouTube makes links in Shorts descriptions unclickable,
    // so the call to action points to the links on the channel page instead.
    if (n === "youtube" && (urls.length || /www\./i.test(body))) errors.push('youtube Shorts cannot carry clickable links; say "link on our channel page"');
    for (const u of n === "youtube" ? [] : urls) {
      const m = u.match(/^https:\/\/www\.financedepartmentllc\.com\/[a-z0-9\-\/]*\?utm_source=([a-z]+)&utm_medium=social_media&utm_campaign=([a-z0-9\-]+)$/);
      if (!m) errors.push(`${n} link is not a tracked financedepartmentllc.com link: ${u}`);
      else if (m[1] !== n || m[2] !== p.id.toLowerCase()) errors.push(`${n} link must carry utm_source=${n} and utm_campaign=${p.id.toLowerCase()}`);
    }
    // Threads (since 16 November 2026): no link in the post itself; a middle or bottom of funnel piece
    // carries its tracked link in content.first_reply, which the Social desk posts as our first reply.
    if (n === "threads") {
      if (urls.length || /www\./i.test(body)) errors.push("threads posts carry no link; put the tracked link in content.first_reply");
      const fr = (p.content || {}).first_reply;
      const frUrls = typeof fr === "string" ? fr.match(/https?:\/\/\S+/g) || [] : [];
      for (const u of frUrls) {
        const m = u.match(/^https:\/\/www\.financedepartmentllc\.com\/[a-z0-9\-\/]*\?utm_source=([a-z]+)&utm_medium=social_media&utm_campaign=([a-z0-9\-]+)$/);
        if (!m) errors.push(`threads first_reply link is not a tracked financedepartmentllc.com link: ${u}`);
        else if (m[1] !== "threads" || m[2] !== p.id.toLowerCase()) errors.push(`threads first_reply link must carry utm_source=threads and utm_campaign=${p.id.toLowerCase()}`);
      }
      if (fr !== undefined && (typeof fr !== "string" || fr.length > 500)) errors.push("content.first_reply is text under 500 characters");
      if ((p.stage === "Middle" || p.stage === "Bottom") && !frUrls.length) errors.push(`threads needs the tracked link in content.first_reply for a ${p.stage.toLowerCase()} of funnel piece`);
      const th = (p.content || {}).thread;
      if (th !== undefined && (!Array.isArray(th) || th.length > 4 || th.some((t) => typeof t !== "string" || !t.trim() || t.length > 500))) errors.push("content.thread is a list of up to 4 follow up posts, each under 500 characters");
      const poll = (p.content || {}).poll;
      if (poll !== undefined && (!Array.isArray(poll) || poll.length < 2 || poll.length > 4 || poll.some((o) => typeof o !== "string" || !o.trim() || o.length > 25))) errors.push("content.poll is a list of 2 to 4 options, each up to 25 characters");
    }
    if ((p.stage === "Middle" || p.stage === "Bottom") && ["facebook", "linkedin", "x"].includes(n) && !urls.length) errors.push(`${n} needs the tracked link for a ${p.stage.toLowerCase()} of funnel piece`);
    if ((p.stage === "Middle" || p.stage === "Bottom") && n === "youtube" && !/link on our channel page/i.test(body)) errors.push('youtube needs "link on our channel page"');
    if ((p.stage === "Middle" || p.stage === "Bottom") && n === "instagram" && !/link in bio/i.test(body)) errors.push('instagram needs "link in bio"');
    if (n === "tiktok" && (p.stage === "Middle" || p.stage === "Bottom") && !/link in bio/i.test(body)) errors.push('tiktok needs "link in bio"');
  }
  // Timing
  const e = p.publish_at ? eastern(p.publish_at) : null;
  if (!e) errors.push("publish_at must be a date and time with its offset, such as 2026-11-03T12:30:00-05:00");
  else if (e.hour < config.posting_hours_eastern[0] || e.hour > config.posting_hours_eastern[1]) errors.push(`publish_at is outside ${config.posting_hours_eastern.join(":00 to ")}:00 Eastern`);
  // Ads: an opening shot made by AI must say so, so the AI label goes on when the piece is placed.
  if (fmt === "ad") {
    const c = p.content || {};
    if (c.hook_clip && typeof p.ai_generated !== "boolean") errors.push("an ad with a hook_clip needs ai_generated true or false");
    if (p.ai_generated === true) warnings.push("AI made footage: switch on each platform's AI label when placing");
    if (!c.offer) warnings.push("an ad usually names its offer on the end card");
  }
  // Studio: spoken words, scenes and visuals restate the piece's own words and add no figure
  if (p.style !== "classic") {
    const c = p.content || {};
    const say = c.say || {};
    if (say.lines !== undefined && (!Array.isArray(say.lines) || say.lines.length !== (c.lines || []).length)) errors.push("say.lines must have one entry per line");
    for (const v of [say.hook, say.cta, ...(Array.isArray(say.lines) ? say.lines : [])]) if (v !== undefined && v !== null && (typeof v !== "string" || !v.trim())) errors.push("every say entry is a non-empty string");
    const own = figureSet(ownWords(p));
    const extras = [];
    if (Array.isArray(c.scenes)) {
      const beats = 2 + (c.lines || []).length;
      if (c.scenes.length > beats) errors.push(`scenes has ${c.scenes.length} entries for ${beats} beats`);
      c.scenes.forEach((s, i) => { if (s && !SCENE_TYPES.includes(s.type)) errors.push(`scene ${i + 1} has an unknown type ${s && s.type}`); if (s) extras.push(...strings(s)); });
    }
    for (const [i, s] of (c.slides || []).entries()) for (const k of ["visual", "visual2"]) {
      if (!s[k]) continue;
      if (!VISUAL_TYPES.includes(s[k].type)) errors.push(`slide ${i + 1} ${k} has an unknown type ${s[k].type}`);
      extras.push(...strings(s[k]));
    }
    for (const t of extras) for (const f of figureSet(t)) if (!own.has(f) && !/^\d{1,2}$/.test(f)) errors.push(`a scene or visual shows ${f}, which is not in the piece's own words`);
    if (fmt === "carousel_reel") {
      const src = c.slides ? null : week.pieces.find((x) => x.id === c.from);
      if (!c.slides && (!src || src.format !== "carousel")) errors.push("a carousel_reel needs content.from naming a carousel in this week");
      if (src && !(p.claims || []).every((x) => (src.claims || []).includes(x))) warnings.push("its claims differ from its carousel's");
    }
    if ((fmt === "explainer" || fmt === "ad") && p.ai_voice === true) warnings.push("AI voice: switch on each platform's AI label when placing");
  }
  // Media
  if (fmt === "carousel_reel" && (p.media || []).length > 1) errors.push("a carousel_reel has one video");
  if (["explainer", "ad", "carousel", "carousel_reel", "story", "reel", "cut", "avatar"].includes(fmt) && ["Made", "Passed check", "Draft in Metricool", "Scheduled"].includes(p.status) && !(p.media || []).length) errors.push("no media");
  if (fmt === "carousel" && (p.media || []).length && p.content && p.content.slides && p.media.length !== p.content.slides.length) errors.push("the carousel's image count does not match its slides");
  return { errors, warnings, eastern: e };
}

export function checkWeek(week, claims, only) {
  const out = {};
  const feed = {};
  for (const p of week.pieces) {
    if (only && !only.includes(p.id)) continue;
    const r = checkPiece(p, claims, week);
    if (r.eastern && p.format !== "story" && p.status !== "Held" && p.status !== "Vetoed") {
      for (const n of p.platforms || []) {
        const k = `${n}|${r.eastern.day}`;
        (feed[k] = feed[k] || []).push({ id: p.id, ms: r.eastern.ms });
      }
    }
    out[p.id] = { errors: r.errors, warnings: r.warnings };
  }
  for (const [k, list] of Object.entries(feed)) {
    const [n, day] = k.split("|");
    if (list.length > config.max_feed_posts_per_day) for (const x of list) out[x.id] && out[x.id].warnings.push(`${list.length} feed posts on ${n} on ${day}; at most ${config.max_feed_posts_per_day}`);
    list.sort((a, b) => a.ms - b.ms);
    for (let i = 1; i < list.length; i++) if (list[i].ms - list[i - 1].ms < config.min_gap_hours * 3600e3 && out[list[i].id]) out[list[i].id].warnings.push(`under ${config.min_gap_hours} hours after ${list[i - 1].id} on ${n}`);
  }
  return out;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [file, claimsFile] = process.argv.slice(2);
  const onlyArg = process.argv.find((a) => a.startsWith("--only="));
  const only = onlyArg ? onlyArg.slice(7).split(",") : process.argv.includes("--only") ? process.argv[process.argv.indexOf("--only") + 1].split(",") : null;
  const week = JSON.parse(readFileSync(file, "utf8"));
  const claims = JSON.parse(readFileSync(claimsFile, "utf8"));
  const result = checkWeek(week, claims, only);
  const failed = Object.entries(result).filter(([, r]) => r.errors.length).map(([id]) => id);
  console.log(JSON.stringify({ ok: failed.length === 0, failed, pieces: result }, null, 2));
  process.exit(failed.length ? 1 : 0);
}
