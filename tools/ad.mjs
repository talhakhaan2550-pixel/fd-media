// Finance Department ads: one offer at a time, posted like any other piece with no ad budget.
// The body is the explainer engine (approved words only, the offer and call to action on the end card).
// An optional opening shot (content.hook_clip) goes in front: up to 3.5 seconds of cinematic footage,
// usually made in Higgsfield from content.hook_visual. Footage made by AI sets the piece's ai_generated to true,
// so the Production run switches on each platform's AI label. No AI people: the clip shows scenes and objects,
// never a person presented as a client, a reviewer or Talha.
//
// A hook_clip with a file (a path inside this repository) is stitched here with ffmpeg. A hook_clip with only a
// url is stitched by the Production run outside this workspace, which cannot reach other websites.
import { mkdirSync, existsSync, renameSync, rmSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";
import { execFileSync } from "node:child_process";
import { checkExplainer, renderExplainer } from "./explainer.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");
export const AD_OPTS = { idRe: /^\d{4}-W\d{2}-D\d{2}$/, idHint: "id must look like 2026-W45-D01", minLines: 1, maxLines: 4, allowOffer: true };
export const HOOK_MAX_SECONDS = 3.5;

export function checkAd(piece) {
  const p = checkExplainer(piece, AD_OPTS);
  const c = piece.content || {};
  if (c.hook_visual !== undefined && (typeof c.hook_visual !== "string" || !c.hook_visual.trim() || c.hook_visual.length > 400)) p.push("hook_visual must be 1 to 400 characters");
  if (c.hook_clip !== undefined) {
    const h = c.hook_clip || {};
    if (!h.file && !h.url) p.push("hook_clip needs a file or a url");
    if (h.url && !/^https:\/\//.test(h.url)) p.push("hook_clip url must start with https://");
    if (h.file && !existsSync(resolve(root, h.file))) p.push(`hook_clip file ${h.file} is not in the repository`);
    if (typeof piece.ai_generated !== "boolean") p.push("a piece with a hook_clip says whether it is AI made: ai_generated true or false");
  }
  return p;
}

const probeSeconds = (f) => Number(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).toString().trim());

// Renders the ad into mediaDir. Returns the file name, the length and the preview frames, as renderExplainer does.
export function renderAd(piece, mediaDir, previewDir) {
  const problems = checkAd(piece);
  if (problems.length) throw new Error(problems.join("; "));
  const hook = piece.content.hook_clip && piece.content.hook_clip.file ? resolve(root, piece.content.hook_clip.file) : null;
  if (!hook) return renderExplainer(piece, mediaDir, previewDir, AD_OPTS);

  const work = join(tmpdir(), `fd-ad-${piece.id}`);
  rmSync(work, { recursive: true, force: true });
  mkdirSync(work, { recursive: true });
  const body = renderExplainer(piece, work, null, AD_OPTS);
  const bodyFile = join(work, body.file);
  const hookFile = join(work, "hook.mp4");
  const fit = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p";
  execFileSync("ffmpeg", ["-v", "error", "-y", "-i", hook, "-t", String(HOOK_MAX_SECONDS), "-vf", fit, "-an", "-c:v", "libx264", "-crf", "18", "-preset", "medium", hookFile]);
  const hookSeconds = probeSeconds(hookFile);
  mkdirSync(mediaDir, { recursive: true });
  const out = join(mediaDir, body.file);
  const tmpOut = join(work, `stitched-${body.file}`);
  execFileSync("ffmpeg", ["-v", "error", "-y", "-i", hookFile, "-i", bodyFile, "-filter_complex",
    `[0:v]${fit}[a];[1:v]${fit}[b];[a][b]concat=n=2:v=1:a=0[v]`, "-map", "[v]",
    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-movflags", "+faststart", tmpOut]);
  renameSync(tmpOut, out);
  const frames = [];
  if (previewDir) {
    mkdirSync(previewDir, { recursive: true });
    const looks = [hookSeconds / 2, ...body.looks.map((t) => t + hookSeconds)];
    looks.forEach((t, i) => {
      const f = join(previewDir, `${piece.id}_${String(i).padStart(2, "0")}.png`);
      execFileSync("ffmpeg", ["-v", "error", "-y", "-ss", String(Math.round(t * 10) / 10), "-i", out, "-frames:v", "1", "-vf", "scale=540:-1", f]);
      frames.push(f);
    });
  }
  rmSync(work, { recursive: true, force: true });
  return { file: body.file, seconds: Math.round((hookSeconds + body.seconds) * 10) / 10, frames, looks: null };
}
