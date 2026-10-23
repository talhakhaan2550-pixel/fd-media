// Makes the media for a week's pieces: explainers through HyperFrames, carousels and stories through Chromium.
// Files land in weeks/{week}/media/, which GitHub Pages serves at {pagesBase}/weeks/{week}/media/{file}.
// For each piece it also writes one contact sheet to .previews/ for the run to look at before the piece passes.
//
//   node tools/make.mjs weeks/2026-W45/pieces.json [--only 2026-W45-E01,2026-W45-C01] [--force]
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import { renderExplainer } from "./explainer.mjs";
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
  if (!["explainer", "carousel", "story"].includes(p.format)) continue;
  if (only && !only.includes(p.id)) continue;
  if (!force && !["Planned", "Rendering"].includes(p.status)) continue;
  try {
    let files, frames;
    if (p.format === "explainer") {
      const r = renderExplainer(p, mediaDir, join(previewDir, p.id));
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
