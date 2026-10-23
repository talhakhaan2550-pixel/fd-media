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
  explainer: ["youtube", "instagram", "facebook", "tiktok", "x", "threads"],
  reel: ["youtube", "instagram", "facebook", "tiktok", "x", "threads"],
  cut: ["youtube", "instagram", "facebook", "tiktok", "x", "threads"],
  avatar: ["youtube", "instagram", "facebook", "tiktok", "x", "threads"],
  carousel: ["instagram", "facebook", "tiktok", "x", "threads"],
  story: ["instagram", "facebook"],
  text: ["facebook", "x", "threads"],
};
const LETTER = { reel: "Y", cut: "Y", explainer: "E", avatar: "A", carousel: "C", story: "S", text: "T" };
const CAPTION_MAX = { x: 280, threads: 500, instagram: 2200, tiktok: 2200, facebook: 5000 };
const HASHTAGS = { instagram: [3, 5], tiktok: [3, 5], threads: [3, 5], x: [0, 2], facebook: [0, 0], youtube: [0, 3] };
const DISCLAIMER = "General information, not tax or legal advice for your situation.";
const BANNED = [
  [/\bthe finance department\b/i, 'the name is "Finance Department", never "The Finance Department"'],
  [/\bCPA\b/, '"CPA" is not a title anyone here holds'],
  [/\bbig (4|four)\b/i, '"Big 4" may not be used'],
  [/\b5[- ]star|\bfive[- ]star/i, 'star ratings may not be used'],
  [/\bguarantee/i, 'no promised outcomes'],
  [/\b(150\+|50\+)\s*(businesses|clients|founders)?/i, 'old client figures; the only one is "300+ founders"'],
  [/\bintroduc\w* (you )?to investors\b|\binvestor introductions?\b/i, 'the firm does not introduce investors'],
  [/\byou will raise\b|\bwe('ll| will) raise\b/i, 'no promised outcomes'],
  [/\b(prepare|file|do) your (tax return|1120|form 5472|5472)\b|\btax return preparation\b/i, 'tax returns are not offered until the firm has a PTIN'],
  [/\b\d+% (in )?(tax )?savings?\b|\bsave \d+%/i, 'no tax savings figures'],
];
const DASH = /[‒–—―]| - /;

const allText = (p) => {
  const c = p.content || {};
  const parts = [c.kicker, c.hook, ...(c.lines || []), c.cta, c.text, ...(c.slides || []).flatMap((s) => Object.entries(s).filter(([k]) => k !== "layout").map(([, v]) => v))];
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
  // Words
  const text = allText(p);
  for (const [re, why] of BANNED) if (re.test(text)) errors.push(why);
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
    for (const u of urls) {
      const m = u.match(/^https:\/\/www\.financedepartmentllc\.com\/[a-z0-9\-\/]*\?utm_source=([a-z]+)&utm_medium=social_media&utm_campaign=([a-z0-9\-]+)$/);
      if (!m) errors.push(`${n} link is not a tracked financedepartmentllc.com link: ${u}`);
      else if (m[1] !== n || m[2] !== p.id.toLowerCase()) errors.push(`${n} link must carry utm_source=${n} and utm_campaign=${p.id.toLowerCase()}`);
    }
    if ((p.stage === "Middle" || p.stage === "Bottom") && ["facebook", "x", "threads", "youtube"].includes(n) && !urls.length) errors.push(`${n} needs the tracked link for a ${p.stage.toLowerCase()} of funnel piece`);
    if ((p.stage === "Middle" || p.stage === "Bottom") && n === "instagram" && !/link in bio/i.test(body)) errors.push('instagram needs "link in bio"');
    if (n === "tiktok" && (p.stage === "Middle" || p.stage === "Bottom") && !/link in bio/i.test(body)) errors.push('tiktok needs "link in bio"');
  }
  // Timing
  const e = p.publish_at ? eastern(p.publish_at) : null;
  if (!e) errors.push("publish_at must be a date and time with its offset, such as 2026-11-03T12:30:00-05:00");
  else if (e.hour < config.posting_hours_eastern[0] || e.hour > config.posting_hours_eastern[1]) errors.push(`publish_at is outside ${config.posting_hours_eastern.join(":00 to ")}:00 Eastern`);
  // Media
  if (["explainer", "carousel", "story", "reel", "cut", "avatar"].includes(fmt) && ["Made", "Passed check", "Draft in Metricool", "Scheduled"].includes(p.status) && !(p.media || []).length) errors.push("no media");
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
