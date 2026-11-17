// The learning loop (17 November 2026, when Talha asked that the content strategy improve itself from research and
// results, with one out-of-the-box test a week). The Weekly report run writes research/results/{week}.json from
// Buffer, Metricool and HubSpot; this script turns every week's results into:
//   research/scores.json       how each hook pattern, format, scene, pillar and platform does at each stage,
//                              against the goal of that stage, recent weeks counting most
//   research/experiments.json  the verdict on each weekly wild card, and which ones have earned a place
// The Research desk reads both on Mondays to rank the next week's ideas, and the Plan run follows its brief.
//
//   node tools/learn.mjs                 update both files from every research/results/*.json
//   node tools/learn.mjs --dry           print what would change, write nothing
//
// Goals by stage (what "better" means): top of funnel pieces are for reach and new followers, so views, shares and
// holding attention count most; middle of funnel pieces are for saves and keyword comments; bottom of funnel pieces
// are for DMs, leads and booked calls. Every number is compared with the median of the same platform and kind of post
// over the last eight weeks, so a score of 1.0 is our usual and 1.5 is half again better.
import { readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const RES = join(root, "research", "results");
const SCORES = join(root, "research", "scores.json");
const EXPS = join(root, "research", "experiments.json");
const dry = process.argv.includes("--dry");

export const GOALS = {
  top: { views: 0.4, shares: 0.25, saves: 0.1, hold: 0.25 },
  middle: { views: 0.25, saves: 0.3, comments: 0.15, actions: 0.3 },
  bottom: { views: 0.15, actions: 0.35, leads: 0.3, calls: 0.2 },
};
const HALF_LIFE_WEEKS = 4;
const PRIOR = 3; // how many usual pieces a new pattern's score is pulled towards 1.0 by
const WIN = 1.25, STRONG_WIN = 1.5, LOSS = 0.8;

const median = (xs) => {
  const v = xs.filter((x) => typeof x === "number" && Number.isFinite(x)).sort((a, b) => a - b);
  if (!v.length) return null;
  const m = Math.floor(v.length / 2);
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
};
const weekNum = (w) => { const m = /^(\d{4})-W(\d{2})$/.exec(w || ""); return m ? Number(m[1]) * 53 + Number(m[2]) : 0; };
const kindOf = (fmt) => (["carousel", "story", "linkedin_image"].includes(fmt) ? "image" : fmt === "text" ? "text" : "video");
const stageOf = (s) => String(s || "").toLowerCase().replace(/ of funnel$/, "");
const num = (x) => (typeof x === "number" && Number.isFinite(x) ? x : null);

// Each post's numbers as rates the goals use. hold is 100 minus the skip rate (Instagram reels), or the average watch
// time where the skip rate is missing.
function rates(post) {
  const v = num(post.views) ?? num(post.reach);
  const r = { views: v };
  if (v && v > 0) {
    for (const k of ["shares", "saves", "comments"]) if (num(post[k]) !== null) r[k] = post[k] / v;
  }
  if (num(post.skip_rate) !== null) r.hold = 100 - post.skip_rate;
  else if (num(post.avg_watch_s) !== null) r.hold = post.avg_watch_s;
  return r;
}

export function learn(weeks) {
  weeks = [...weeks].sort((a, b) => weekNum(a.week) - weekNum(b.week));
  const last = weeks.length ? weeks[weeks.length - 1].week : null;
  // every post with its week, piece and rates
  const posts = [];
  for (const w of weeks) for (const p of w.pieces || []) for (const post of p.posts || []) posts.push({ week: w.week, piece: p, post, r: rates(post) });
  // baselines: median of the same platform and kind of post over the eight weeks up to each week
  const base = (week, platform, kind, key) => median(posts.filter((x) => x.post.platform === platform && kindOf(x.piece.format) === kind
    && weekNum(x.week) <= weekNum(week) && weekNum(x.week) > weekNum(week) - 8).map((x) => x.r[key]));
  const pieceBase = (week, key) => median(weeks.filter((w) => weekNum(w.week) <= weekNum(week) && weekNum(w.week) > weekNum(week) - 8)
    .flatMap((w) => (w.pieces || []).map((p) => num(p[key]))));
  // each piece's score against its stage's goal
  const scored = [];
  for (const w of weeks) for (const p of w.pieces || []) {
    const stage = stageOf(p.stage);
    const goal = GOALS[stage];
    if (!goal || !(p.posts || []).length) continue;
    const parts = {};
    for (const post of p.posts) {
      const r = rates(post);
      for (const key of ["views", "shares", "saves", "comments", "hold"]) {
        if (!(key in goal) || r[key] == null) continue;
        const b = base(w.week, post.platform, kindOf(p.format), key);
        if (b && b > 0) (parts[key] = parts[key] || []).push(Math.min(4, r[key] / b));
      }
    }
    for (const key of ["actions", "leads", "calls"]) {
      if (!(key in goal) || num(p[key === "actions" ? "keyword_actions" : key]) === null) continue;
      const v = p[key === "actions" ? "keyword_actions" : key];
      const b = pieceBase(w.week, key === "actions" ? "keyword_actions" : key);
      parts[key] = [Math.min(4, (v + 0.5) / ((b || 0) + 0.5))];
    }
    let total = 0, wsum = 0;
    for (const [key, wt] of Object.entries(goal)) if (parts[key] && parts[key].length) { total += wt * (parts[key].reduce((a, b) => a + b, 0) / parts[key].length); wsum += wt; }
    if (!wsum) continue;
    scored.push({ week: w.week, id: p.id, stage, score: total / wsum, parts: Object.fromEntries(Object.entries(parts).map(([k, v]) => [k, +(v.reduce((a, b) => a + b, 0) / v.length).toFixed(2)])),
      tags: p.tags || {}, format: p.format, pillar: p.pillar, platforms: p.posts.map((x) => x.platform), experiment: p.experiment || null,
      views: p.posts.reduce((a, x) => a + (num(x.views) ?? num(x.reach) ?? 0), 0) });
  }
  // tag scores by stage, recent weeks counting most, pulled towards 1.0 until there is evidence
  const byStage = {};
  for (const s of scored) {
    const age = last ? (weekNum(last) - weekNum(s.week)) : 0;
    const wt = Math.pow(0.5, age / HALF_LIFE_WEEKS);
    const keys = [];
    for (const [k, v] of Object.entries(s.tags)) for (const x of [].concat(v)) if (x) keys.push(`${k}:${x}`);
    keys.push(`kind:${s.format}`, `pillar:${s.pillar}`, ...s.platforms.map((x) => `platform:${x}`));
    if (s.experiment) keys.push(`experiment:${s.experiment}`);
    for (const key of keys) {
      const t = ((byStage[s.stage] = byStage[s.stage] || {})[key] = byStage[s.stage][key] || { sum: 0, w: 0, n: 0, last: null });
      t.sum += wt * s.score; t.w += wt; t.n += 1;
      if (!t.last || weekNum(s.week) > weekNum(t.last)) t.last = s.week;
    }
  }
  const out = {};
  for (const [stage, tags] of Object.entries(byStage)) {
    out[stage] = {};
    for (const [key, t] of Object.entries(tags)) out[stage][key] = { score: +(t.sum / t.w).toFixed(3), adj: +((t.sum + PRIOR) / (t.w + PRIOR)).toFixed(3), n: t.n, last: t.last };
  }
  // ranked picks per stage for each kind of tag
  const picks = {};
  for (const [stage, tags] of Object.entries(out)) {
    picks[stage] = {};
    for (const [key, t] of Object.entries(tags)) {
      const [kind, val] = [key.slice(0, key.indexOf(":")), key.slice(key.indexOf(":") + 1)];
      if (kind === "experiment") continue;
      (picks[stage][kind] = picks[stage][kind] || []).push({ id: val, adj: t.adj, n: t.n });
    }
    for (const k of Object.keys(picks[stage])) picks[stage][k].sort((a, b) => b.adj - a.adj || b.n - a.n);
  }
  return { last, scored, byStage: out, picks };
}

// The wild card's verdict: its score against the median score of the same stage's other pieces that week and the
// three weeks before. Fewer than 100 views, or no numbers, is "not readable" rather than a loss.
export function judge(exp, scored) {
  const me = scored.find((s) => s.id === exp.piece);
  if (!me) return { verdict: "not readable", why: "no results for its piece yet" };
  if (me.views < 100) return { verdict: "not readable", why: `${me.views} views is too few to judge`, score: +me.score.toFixed(2) };
  const peers = scored.filter((s) => s.stage === me.stage && s.id !== me.id && !s.experiment && weekNum(s.week) <= weekNum(me.week) && weekNum(s.week) > weekNum(me.week) - 4);
  const b = median(peers.map((s) => s.score));
  if (!b) return { verdict: "not readable", why: "no other pieces at its stage to compare with", score: +me.score.toFixed(2) };
  const ratio = me.score / b;
  const verdict = ratio >= WIN ? "win" : ratio <= LOSS ? "loss" : "inconclusive";
  return { verdict, strong: ratio >= STRONG_WIN, score: +me.score.toFixed(2), baseline: +b.toFixed(2), ratio: +ratio.toFixed(2), parts: me.parts, compared_with: peers.length };
}

function main() {
  const weeks = existsSync(RES) ? readdirSync(RES).filter((f) => /^\d{4}-W\d{2}\.json$/.test(f)).map((f) => JSON.parse(readFileSync(join(RES, f), "utf8"))) : [];
  const L = learn(weeks);
  const scores = { about: "Written by node tools/learn.mjs from research/results/*.json after each Weekly report. adj is the score pulled towards 1.0 (our usual) until a pattern has evidence; rank by adj. Goals: " + JSON.stringify(GOALS), updated: L.last, half_life_weeks: HALF_LIFE_WEEKS, by_stage: L.byStage, picks: L.picks, pieces: L.scored.slice(-120) };
  const exps = existsSync(EXPS) ? JSON.parse(readFileSync(EXPS, "utf8")) : { experiments: [] };
  const changed = [];
  for (const e of exps.experiments || []) {
    if (!e.piece || (e.result && ["win", "loss"].includes(e.result.verdict))) continue;
    const r = judge(e, L.scored);
    if (JSON.stringify(r) !== JSON.stringify(e.result || null)) { e.result = { ...r, judged: L.last }; changed.push(`${e.id}: ${r.verdict}${r.ratio ? ` (${r.ratio} times our usual)` : ""}`); }
    const wins = (exps.experiments || []).filter((x) => x.idea === e.idea && x.result && x.result.verdict === "win");
    e.promote = wins.some((x) => x.result.strong) || wins.length >= 2;
  }
  if (!dry) {
    writeFileSync(SCORES, JSON.stringify(scores, null, 2) + "\n");
    writeFileSync(EXPS, JSON.stringify(exps, null, 2) + "\n");
  }
  const top = Object.fromEntries(Object.entries(L.picks).map(([st, k]) => [st, Object.fromEntries(Object.entries(k).filter(([kind]) => ["hook", "format", "scene"].includes(kind)).map(([kind, list]) => [kind, list.slice(0, 3)]))]));
  console.log(JSON.stringify({ weeks: weeks.map((w) => w.week), pieces_scored: L.scored.length, experiments_judged: changed, best: top, wrote: dry ? [] : ["research/scores.json", "research/experiments.json"] }, null, 2));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main();
