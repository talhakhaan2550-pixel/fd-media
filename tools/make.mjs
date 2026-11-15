// Makes the media for a week's pieces. Files land in weeks/{week}/media/, which GitHub Pages serves at
// {pagesBase}/weeks/{week}/media/{file}. For each piece it also writes one contact sheet to .previews/ for the run
// to look at before the piece passes.
//
// Since 15 November 2026 every piece is made by the studio (tools/studio, Python): narrated story videos for
// explainers and ads, carousels with visuals, carousel music reels and stories in the new style. A piece with
// "style": "classic" is still made by the first engine (HyperFrames explainers and the plain slides).
//
//   node tools/make.mjs weeks/2026-W45/pieces.json [--only 2026-W45-E01,2026-W45-C01] [--force]
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import { renderExplainer } from "./explainer.mjs";
import { renderAd } from "./ad.mjs";
import { renderStill } from "./stills.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");
const config = JSON.parse(readFileSync(join(here, "config.json"), "utf8"));

function sheet(images, out) {
  const args = ["-v", "error", "-y"];
  images.forEach((f) => args.push("-i", f));
  const scaled = images.map((_, i) => `[${i}:v]scale=360:-1[a${i}]`).join(";");
  const stack = images.length > 1 ? `;${images.map((_, i) => `[a${i}]`).join("")}hstack=inputs=${images.length}[out]` : "";
  args.push("-filter_complex", scaled + stack, "-map", images.length > 1 ? "[out]" : "[a0]", "-frames:v", "1", out);
  execFileSync("ffmpeg", args);
  return out;
}

const file = process.argv[2];
if (!file) { console.error("usage: node tools/make.mjs weeks/<week>/pieces.json [--only IDS] [--force]"); process.exit(2); }
const onlyArg = process.argv.indexOf("--only");
const only = onlyArg > -1 ? process.argv[onlyArg + 1].split(",") : null;
const force = process.argv.includes("--force");
const weekFile = resolve(file);
const week = JSON.parse(readFileSync(weekFile, "utf8"));
const mediaDir = join(root, "weeks", week.week, "media");
const previewDir = join(root, ".previews", week.week);
mkdirSync(previewDir, { recursive: true });
const report = [];

for (const p of week.pieces) {
  if (!["explainer", "ad", "carousel", "story", "carousel_reel"].includes(p.format)) continue;
  if (only && !only.includes(p.id)) continue;
  if (!force && !["Planned", "Rendering"].includes(p.status)) continue;
  try {
    let files, frames;
    if (p.style !== "classic") {
      const out = execFileSync("python3", [join(here, "studio", "render.py"), weekFile, p.id, "--media", mediaDir, "--preview", previewDir],
        { encoding: "utf8", timeout: 30 * 60 * 1000, maxBuffer: 1 << 26 });
      const r = JSON.parse(out.slice(out.indexOf("{")));
      p.media = r.files.map((f) => `${config.pagesBase}/weeks/${week.week}/media/${f}`);
      const notes = [...(r.problems || []).map((x) => `layout: ${x}`), ...(r.notes || [])];
      if (p.content?.hook_clip) notes.push("the studio does not add the opening shot (hook_clip) yet; mark the piece \"style\": \"classic\" to stitch it");
      if (p.format === "explainer" || p.format === "ad") p.ai_voice = r.voiced === true;
      p.status = (r.problems || []).length ? "Held" : "Made";
      p.check_notes = notes.join("; ");
      report.push({ id: p.id, status: p.status, media: p.media, preview: r.preview, seconds: r.seconds, notes, loudness: r.loudness });
      continue;
    }
    if (p.format === "carousel_reel") throw new Error("a carousel_reel is made only by the studio");
    if (p.format === "explainer" || p.format === "ad") {
      const r = p.format === "ad" ? renderAd(p, mediaDir, join(previewDir, p.id)) : renderExplainer(p, mediaDir, join(previewDir, p.id));
      files = [r.file];
      frames = r.frames;
    } else {
      files = await renderStill(p, mediaDir);
      frames = files.map((f) => join(mediaDir, f));
    }
    p.media = files.map((f) => `${config.pagesBase}/weeks/${week.week}/media/${f}`);
    p.status = "Made";
    p.check_notes = "";
    const preview = sheet(frames, join(previewDir, `${p.id}.png`));
    report.push({ id: p.id, status: p.status, media: p.media, preview });
  } catch (e) {
    p.status = "Held";
    p.check_notes = `make: ${String(e.message || e).split("\n")[0].slice(0, 300)}`;
    report.push({ id: p.id, status: p.status, problem: p.check_notes });
  }
}
writeFileSync(weekFile, JSON.stringify(week, null, 2) + "\n");
console.log(JSON.stringify(report, null, 2));
