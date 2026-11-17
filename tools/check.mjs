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
// What each offer covers (word for word from its page, FD-31) and the approved comment and DM keywords.
const OFFERS = JSON.parse(readFileSync(join(here, "coverage.json"), "utf8")).offers;
// The pattern library the learning loop scores pieces by (research/patterns.json).
const PATTERNS = (() => { try { return JSON.parse(readFileSync(join(here, "..", "research", "patterns.json"), "utf8")); } catch { return { hooks: [], formats: [], scenes: [] }; } })();
const weekNo = (w) => { const m = /^(\d{4})-W(\d{2})$/.exec(w || ""); return m ? Number(m[1]) * 53 + Number(m[2]) : 0; };
const KEYWORDS = JSON.parse(readFileSync(join(here, "keywords.json"), "utf8"));

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
// The cast visual's characters and their expressions (tools/studio/cast.py POSES; the 3D cast since 16 November 2026)
const PEOPLE = ["happy", "surprised", "thinking"];
const CAST = { sam: PEOPLE, penny: PEOPLE, zara: PEOPLE, grace: PEOPLE, dev: PEOPLE, maya: PEOPLE, rex: ["sly", "surprised", "happy", "wink"], dot: ["happy", "surprised", "wink"] };
// Figures that matter: money, percentages, numbers of two digits or more and years.
const FIGS = /\$[\d,.]+(?:\s?(?:million|billion|M|K))?|\d[\d,.]*%|\b\d{1,3}(?:,\d{3})+\b|\b\d{2,}(?:\.\d+)?(?=s?\b)/g;
// Money keeps its $ and percentages their %, so $65 never passes for a 65 elsewhere; plain one and two digit
// numbers (days on a calendar) are not checked.
const figureSet = (s) => new Set((s.match(FIGS) || []).map((f) => f.replace(/[.,]+$/, "").replace(/[,\s]|million|billion/g, "").replace(/\.0+$/, "")));
// Motion v2 pieces (content.motion): their words, with every {"cover": id} read as the offer's own items and recap.
const motionShots = (m) => (m.shots || []).flatMap((sh) => {
  if (!sh || !sh.cover) return [sh];
  const o = OFFERS[sh.cover];
  if (!o) return [];
  return [...o.items.map((it) => ({ shot: { type: "work", ...it.scene, title: it.title }, lines: [{ text: it.text, say: it.say }] })),
    ...(sh.recap === false ? [] : [{ shot: { type: "recap", title: o.recap.title }, lines: [{ text: o.recap.text, say: o.recap.say }] }])];
});
const motionWords = (m) => [m.hook && m.hook.text, ...motionShots(m).flatMap((sh) => (sh && sh.lines || []).map((l) => l && l.text)), m.cta && m.cta.text, m.offer]
  .filter((x) => typeof x === "string").join("\n");
const allText = (p) => {
  const c = p.content || {};
  const parts = [c.kicker, c.hook, ...(c.lines || []), c.offer, c.cta, c.text, ...(c.slides || []).flatMap((s) => Object.entries(s).filter(([k]) => k !== "layout").flatMap(([, v]) => strings(v))),
    ...strings(c.scenes || []), ...strings(c.say || {}), ...(c.motion ? strings({ ...c.motion, shots: motionShots(c.motion) }) : [])];
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

// ---------------------------------------------------------------- motion v2
const SHOT_TYPES = ["versus", "form", "castpay", "bars", "calendar", "follow", "person", "checklist", "docpair", "fax", "deadline", "penalty",
  "comment", "report", "days", "price", "proof", "nofee", "phone", "work", "recap"];
const WORK_KINDS = ["books", "revenue", "table", "review", "runway", "findings", "form", "send", "stack", "calendar", "compare", "setup"];
const CTA_FOR = { top: "follow", middle: "comment", bottom: "dm" };

function motionChecks(p, errors, warnings) {
  const m = p.content.motion;
  if (!["explainer", "ad"].includes(p.format)) errors.push("content.motion is for explainers and ads");
  const stage = String(m.stage || "");
  if (!CTA_FOR[stage]) errors.push('motion.stage is "top", "middle" or "bottom"');
  else if (p.stage && stage !== String(p.stage).toLowerCase()) errors.push(`motion.stage ${stage} does not match the piece's stage ${p.stage}`);
  const h = m.hook || {};
  if (typeof h.text !== "string" || !h.text.trim()) errors.push("motion.hook needs its text");
  if (!h.shot || !SHOT_TYPES.includes(h.shot.type)) errors.push(`motion.hook.shot has an unknown type ${h.shot && h.shot.type}`);
  (m.shots || []).forEach((sh, i) => {
    if (sh && sh.cover !== undefined) {
      if (!OFFERS[sh.cover]) errors.push(`shot ${i + 1}: cover ${sh.cover} is not an offer in tools/coverage.json`);
      return;
    }
    if (!sh || !sh.shot || !SHOT_TYPES.includes(sh.shot.type)) errors.push(`shot ${i + 1} has an unknown type ${sh && sh.shot && sh.shot.type}`);
    else if (sh.shot.type === "work" && !WORK_KINDS.includes(sh.shot.kind)) errors.push(`shot ${i + 1}: work kind ${sh.shot.kind} is not one of ${WORK_KINDS.join(", ")}`);
    if (!sh || !Array.isArray(sh.lines) || !sh.lines.length || sh.lines.some((l) => !l || typeof l.text !== "string" || !l.text.trim())) errors.push(`shot ${i + 1} needs lines, each with its text`);
    for (const l of (sh && sh.lines) || []) if (l && l.say !== undefined && (typeof l.say !== "string" || !l.say.trim())) errors.push(`shot ${i + 1}: every say is a non-empty string`);
    for (const l of (sh && sh.lines) || []) if (l && typeof l.text === "string" && l.text.split(/\s+/).length > 32) warnings.push(`shot ${i + 1}: a line of ${l.text.split(/\s+/).length} words holds one picture too long; split it`);
  });
  const cta = m.cta || {};
  if (CTA_FOR[stage] && cta.kind !== CTA_FOR[stage] && !(p.format === "ad" && cta.kind === "dm")) errors.push(`a ${stage} of funnel piece ends with the ${CTA_FOR[stage]} call to action, not ${cta.kind}`);
  if (!cta.shot || !SHOT_TYPES.includes(cta.shot.type)) errors.push("motion.cta needs a shot");
  if (cta.kind === "comment" || cta.kind === "dm") {
    const list = cta.kind === "comment" ? KEYWORDS.comment : KEYWORDS.dm;
    const k = (list || []).find((x) => x.keyword === cta.keyword);
    if (!k) errors.push(`${cta.keyword} is not an approved ${cta.kind === "dm" ? "DM" : "comment"} keyword in tools/keywords.json`);
    else if (/^waits/i.test(k.status || "")) errors.push(`the ${cta.keyword} keyword ${k.status}`);
    else if (!/^live/i.test(k.status || "")) warnings.push(`the ${cta.keyword} automation is ${k.status}: Talha tests it from his personal Instagram before it is live`);
    if (cta.shot && cta.shot.keyword !== undefined && cta.shot.keyword !== cta.keyword) errors.push("the call to action's shot shows a different keyword from the one it asks for");
    const covered = (m.shots || []).filter((x) => x && x.cover).map((x) => x.cover);
    if (cta.kind === "dm" && covered.length && cta.keyword !== "CALL" && !covered.some((o) => OFFERS[o] && OFFERS[o].keyword === cta.keyword))
      warnings.push(`DM ${cta.keyword} sends a page other than the offer this piece covers (${covered.join(", ")})`);
  }
  // figures in shots and scenes come from the piece's own words
  const own = figureSet(motionWords(m));
  const extras = [...strings(h.shot || {}), ...(m.shots || []).filter((x) => x && !x.cover).flatMap((x) => strings(x.shot || {})), ...strings(cta.shot || {})];
  for (const t of extras) for (const f of figureSet(t)) if (!own.has(f) && !/^\d{1,2}$/.test(f)) errors.push(`a shot shows ${f}, which is not in the piece's own words`);
}

// ---------------------------------------------------------------- coverage before name and price
const escRe = (x) => x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const priceAt = (text, pr) => { const r = new RegExp(`${escRe(pr)}(?![\\d.,]*\\d)`).exec(text); return r ? r.index : -1; };
const nameAt = (text, o) => Math.min(...[o.name, ...(o.names || [])].map((n) => { const i = text.toLowerCase().indexOf(n.toLowerCase()); return i < 0 ? Infinity : i; }));
// Where in a text an offer is first named or priced: {named, priced} as positions, or -1. A price counts for an offer
// only when the piece names or covers that offer ($600 in a post about the old 1099 threshold is not a price).
function mentions(text, o, prices = true) {
  const named = nameAt(text, o);
  const at = prices ? o.prices.map((pr) => priceAt(text, pr)).filter((i) => i >= 0) : [];
  return { named: named === Infinity ? -1 : named, priced: at.length ? Math.min(...at) : -1 };
}
const listsItems = (text, o, upTo) => { const t = text.slice(0, upTo < 0 ? undefined : upTo).toLowerCase(); return o.items.filter((it) => !t.includes(it.title.toLowerCase()) && !t.includes(it.text.toLowerCase())); };

function coverageChecks(p, claims, errors, warnings) {
  const c = p.content || {};
  const used = p.claims || [];
  // the piece's own words, without what a cover adds (the Sprint's items name the Scan)
  const capText = Object.values(p.captions || {}).map((v) => (typeof v === "string" ? v : [v && v.title, v && v.description].join("\n"))).join("\n");
  const own = [strings({ ...c, motion: undefined }).join("\n"), c.motion ? strings(c.motion).join("\n") : "", capText].join("\n");
  const covers = new Set([...(c.motion ? (c.motion.shots || []).filter((x) => x && x.cover).map((x) => x.cover) : []),
    ...(Array.isArray(c.slides) ? c.slides.filter((x) => x && x.cover).map((x) => x.cover) : [])]);
  const known = new Set(Object.entries(OFFERS).filter(([id, o]) => covers.has(id) || nameAt(own, o) !== Infinity).map(([id]) => id));
  const offersHere = new Set(known);
  const priced = new Set();
  const look = (text, id) => { const x = mentions(text, OFFERS[id], known.has(id)); if (x.priced >= 0) priced.add(id); return x; };
  if (c.motion) {
    const m = c.motion;
    // the order the viewer meets things in: hook, shots, call to action, end card
    const segs = [{ text: [m.hook && m.hook.text, ...strings((m.hook || {}).shot || {})].join("\n") },
      ...(m.shots || []).map((sh) => (sh && sh.cover ? { cover: sh.cover } : { text: strings(sh || {}).join("\n") })),
      { text: strings(m.cta || {}).join("\n") }, { text: m.offer || "" }];
    for (const id of known) {
      const o = OFFERS[id];
      const at = segs.findIndex((g) => g.cover === id);
      const first = segs.findIndex((g) => g.text !== undefined && (() => { const x = look(g.text, id); return x.named >= 0 || x.priced >= 0; })());
      if (first >= 0 && (at < 0 || first < at))
        errors.push(`${o.name} is ${first === 0 ? "named or priced in the hook" : "named or priced"} before what it covers is shown: put {"cover": "${id}"} first (Talha, 17 November 2026)`);
    }
  } else if (Array.isArray(c.slides) && c.slides.length) {
    // a slide with "cover": "<offer id>" shows the offer's list: in a story after the kicker and title and before the
    // body, in a carousel as the slide's visual, after its words. The offer is named or priced only after the list.
    const story = p.format === "story";
    const parts = (sl) => {
      const t = (keys) => strings(Object.fromEntries(Object.entries(sl).filter(([k]) => keys.includes(k)))).join("\n");
      const pre = sl.cover ? (story ? ["kicker", "title", "emph"] : ["kicker", "title", "emph", "body", "bold", "num"]) : Object.keys(sl).filter((k) => k !== "layout");
      return [t(pre), sl.cover ? t(Object.keys(sl).filter((k) => !pre.includes(k) && !["layout", "cover", "visual", "visual2"].includes(k))) : ""];
    };
    for (const id of known) {
      const o = OFFERS[id];
      const at = c.slides.findIndex((sl) => sl.cover === id);
      let first = Infinity;
      c.slides.forEach((sl, i) => parts(sl).forEach((t, half) => { const x = look(t, id); if ((x.named >= 0 || x.priced >= 0) && i + half * 0.75 < first) first = i + half * 0.75; }));
      if (first === Infinity) continue;
      if (at < 0) errors.push(`${o.name} is named or priced on slide ${Math.floor(first) + 1} without its coverage: add a slide with "cover": "${id}" first (Talha, 17 November 2026)`);
      else if (first < at + 0.5) errors.push(`${o.name} is named or priced on slide ${Math.floor(first) + 1} before its coverage list: name and price it ${story ? "in the body, after the list" : "on a slide after the cover slide"}`);
    }
    c.slides.forEach((sl, i) => { if (sl.cover !== undefined && !OFFERS[sl.cover]) errors.push(`slide ${i + 1}: cover ${sl.cover} is not an offer in tools/coverage.json`); });
  } else if (["explainer", "ad"].includes(p.format)) {
    const t = [c.kicker, c.hook, ...(c.lines || []), c.offer, c.cta].filter((x) => typeof x === "string").join("\n");
    for (const id of known) {
      const x = look(t, id);
      if (x.named >= 0 || x.priced >= 0) errors.push(`${OFFERS[id].name} is named or priced in a classic video: make it a motion piece that shows what it covers first ({"cover": "${id}"})`);
    }
  } else if (typeof c.text === "string") {
    for (const id of known) {
      const o = OFFERS[id];
      const x = look(c.text, id);
      if (x.named < 0 && x.priced < 0) continue;
      const upTo = Math.min(...[x.named, x.priced].filter((i) => i >= 0));
      const missing = listsItems(c.text, o, upTo);
      if (missing.length) errors.push(`${o.name} is named or priced before the post lists what it covers (missing: ${missing.map((i) => i.title).join(", ")})`);
    }
  }
  // captions that quote a price list what the offer covers before the price
  for (const [n, cap] of Object.entries(p.captions || {})) {
    const body = typeof cap === "string" ? cap : [cap && cap.title, cap && cap.description].join("\n");
    for (const id of known) {
      const o = OFFERS[id];
      const x = look(body, id);
      if (x.priced < 0) continue;
      const missing = listsItems(body, o, x.priced);
      if (missing.length) errors.push(`the ${n} caption quotes ${o.name}'s price before listing what it covers (missing: ${missing.map((i) => i.title).join(", ")})`);
    }
  }
  for (const id of offersHere) {
    const o = OFFERS[id];
    if (o.hold) errors.push(`${o.name} ${o.hold}`);
    if (!used.includes("FD-31")) errors.push(`a piece about ${o.name} lists FD-31, the approved wording of what each offer covers`);
    if (priced.has(id) && !o.claims.filter((x) => x !== "FD-31").some((x) => used.includes(x))) errors.push(`${o.name}'s price needs one of its claims listed (${o.claims.filter((x) => x !== "FD-31").join(", ")})`);
  }
  if (c.motion && String(p.stage) === "Bottom" && !offersHere.size) {
    const kw = c.motion && c.motion.cta && c.motion.cta.keyword;
    if (kw !== "CALL") warnings.push("a bottom of funnel piece usually covers one offer: add {\"cover\": \"<offer>\"} or ask for DM CALL");
  }
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
    if (!c.offer && !(c.motion && c.motion.offer)) warnings.push("an ad usually names its offer on the end card");
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
      if (s[k].type === "cast") {
        const who = s[k].who === undefined ? ["sam"] : [].concat(s[k].who), expr = s[k].expr === undefined ? [] : [].concat(s[k].expr);
        if (!who.length || who.length > 3) errors.push(`slide ${i + 1} ${k}: the cast visual shows one to three characters`);
        who.forEach((w, j) => {
          if (!CAST[w]) errors.push(`slide ${i + 1} ${k}: ${w} is not in the cast (${Object.keys(CAST).join(", ")})`);
          else if (expr[j] != null && !CAST[w].includes(expr[j])) warnings.push(`slide ${i + 1} ${k}: ${w} has no ${expr[j]} expression (${CAST[w].join(", ")}), so it wears its usual one`);
        });
      }
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
  // Motion v2 (Talha approved the style on 17 November 2026): every explainer and ad is a content.motion piece.
  if (p.content && p.content.motion) motionChecks(p, errors, warnings);
  else if ((fmt === "explainer" || fmt === "ad") && p.style !== "classic" && !["Made", "Passed check", "Draft in Metricool", "Scheduled", "Posted"].includes(p.status))
    warnings.push("explainers and ads are made as motion v2 since 17 November 2026: write content.motion (see tools/studio/motion.py)");
  // Talha, 17 November 2026: a piece that introduces a service or quotes a price shows in detail what it covers first.
  coverageChecks(p, claims, errors, warnings);
  // The learning loop (since 17 November 2026): pieces planned from 2026-W49 carry tags, and the wild card its experiment.
  if (weekNo(week.week) >= weekNo("2026-W49") && !p.test) {
    const t = p.tags;
    if (!t || typeof t !== "object") warnings.push("no tags: the learning loop cannot score this piece (tags {hook, format, scenes})");
    else {
      if (t.hook && !(PATTERNS.hooks || []).some((x) => x.id === t.hook)) warnings.push(`tags.hook ${t.hook} is not a hook in research/patterns.json`);
      const fmts = [...(PATTERNS.formats || []).map((x) => x.id), ...(PATTERNS.wild_cards || []).map((x) => x.idea)];
      if (t.format && !fmts.includes(t.format)) warnings.push(`tags.format ${t.format} is not a format or wild card in research/patterns.json`);
    }
  }
  if (p.experiment !== undefined && !new RegExp(`^${week.week}-X\\d$`).test(String(p.experiment))) errors.push(`experiment must be ${week.week}-X1`);
  // Hook tests (since 16 November 2026): an explainer whose Instagram post goes out as an Instagram Trial Reel,
  // shown first only to people who do not follow us. Version A is the planned explainer; version B is its own
  // explainer piece, Instagram only, with the same words as A except the hook, a day later at the same time.
  if (p.trial !== undefined) {
    const t = p.trial || {};
    if (fmt !== "explainer") errors.push("only an explainer can be a hook test");
    if (!(p.platforms || []).includes("instagram")) errors.push("a hook test goes to Instagram");
    if (typeof t.test !== "string" || !new RegExp(`^${week.week}-H\\d$`).test(t.test)) errors.push(`trial.test must be ${week.week}-H1`);
    if (!["A", "B"].includes(t.variant)) errors.push('trial.variant is "A" or "B"');
    if (typeof t.pattern !== "string" || !t.pattern.trim()) errors.push("trial.pattern names the hook's pattern");
    if (t.variant === "B") {
      if ((p.platforms || []).length !== 1) errors.push("a hook test's version B goes to Instagram only");
      const a = week.pieces.find((x) => x.id === t.of);
      if (!a || !a.trial || a.trial.variant !== "A" || a.trial.test !== t.test) errors.push("trial.of must name this test's version A");
      else {
        const c = p.content || {}, ac = a.content || {};
        const same = (x, y) => JSON.stringify(x ?? null) === JSON.stringify(y ?? null);
        if (c.motion || ac.motion) {
          const m = c.motion || {}, am = ac.motion || {};
          if (!same(m.shots, am.shots) || !same(m.cta, am.cta) || !same(m.offer, am.offer)) errors.push("version B keeps A's shots, call to action and offer; only the hook changes");
          if (!m.hook || !am.hook || (m.hook.text || "").trim() === (am.hook.text || "").trim()) errors.push("version B needs a hook of its own");
          if (!same([...(p.claims || [])].sort(), [...(a.claims || [])].sort())) errors.push("version B lists the same claims as A");
          if (t.pattern === a.trial.pattern) warnings.push("version B uses the same hook pattern as A");
        } else {
        if (!same(c.kicker, ac.kicker) || !same(c.lines, ac.lines) || !same(c.offer, ac.offer) || !same(c.cta, ac.cta)) errors.push("version B keeps A's kicker, lines, offer and call to action word for word; only the hook changes");
        if (!same((c.say || {}).lines, (ac.say || {}).lines) || !same((c.say || {}).cta, (ac.say || {}).cta)) errors.push("version B keeps A's spoken lines and call to action");
        if (!same((c.scenes || []).slice(1), (ac.scenes || []).slice(1))) errors.push("version B keeps A's scenes after the hook");
        if (!c.hook || c.hook.trim() === (ac.hook || "").trim()) errors.push("version B needs a hook of its own");
        if (!same([...(p.claims || [])].sort(), [...(a.claims || [])].sort())) errors.push("version B lists the same claims as A");
        if (t.pattern === a.trial.pattern) warnings.push("version B uses the same hook pattern as A");
        }
        const ea = a.publish_at ? eastern(a.publish_at) : null;
        const h = e && ea ? (e.ms - ea.ms) / 3600e3 : null;
        if (h !== null && (h < 20 || h > 28)) warnings.push("version B usually goes out a day after A, at A's Eastern time");
      }
    }
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
        if (n === "instagram" && p.trial) continue; // a Trial Reel is not in our followers' feed
        const k = `${n}|${r.eastern.day}`;
        (feed[k] = feed[k] || []).push({ id: p.id, ms: r.eastern.ms });
      }
    }
    out[p.id] = { errors: r.errors, warnings: r.warnings };
  }
  // Each hook test has exactly one version A and one version B.
  const tests = {};
  for (const p of week.pieces) if (p.trial && p.trial.test && p.status !== "Vetoed") (tests[p.trial.test] = tests[p.trial.test] || []).push(p);
  for (const [t, list] of Object.entries(tests)) {
    const vs = list.map((x) => x.trial.variant).sort().join("");
    if (vs !== "AB") for (const x of list) if (out[x.id]) out[x.id].errors.push(`hook test ${t} needs exactly one version A and one version B (has ${vs})`);
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
