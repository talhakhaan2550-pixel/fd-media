// Finance Department explainers: a HyperFrames composition built from the piece's approved words, rendered to MP4.
// The words on screen are exactly the words in the piece: nothing is added, reworded or invented.
// Text stays between y 400 and 1400 and 160 px clear of the right edge, out of the way of the
// buttons and captions that Reels, TikTok and Shorts lay over a video.
import { writeFileSync, mkdirSync, cpSync, existsSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";
import { execFileSync } from "node:child_process";

const here = dirname(fileURLToPath(import.meta.url));
export const LIMITS = { kicker: 40, hook: 90, line: 150, cta: 60, minLines: 2, maxLines: 7 };
const SITE = "financedepartmentllc.com";
export const HYPERFRAMES = "hyperframes@0.8.186";

export function checkExplainer(piece) {
  const p = [];
  if (!/^\d{4}-W\d{2}-E\d{2}$/.test(piece.id || "")) p.push("id must look like 2026-W45-E01");
  const c = piece.content || {};
  const text = (v) => typeof v === "string" && v.trim().length > 0;
  if (c.kicker !== undefined && (!text(c.kicker) || c.kicker.length > LIMITS.kicker)) p.push(`kicker must be 1 to ${LIMITS.kicker} characters`);
  if (!text(c.hook) || c.hook.length > LIMITS.hook) p.push(`hook must be 1 to ${LIMITS.hook} characters`);
  if (!Array.isArray(c.lines) || c.lines.length < LIMITS.minLines || c.lines.length > LIMITS.maxLines) {
    p.push(`lines must hold ${LIMITS.minLines} to ${LIMITS.maxLines} lines`);
  } else {
    c.lines.forEach((l, i) => { if (!text(l) || l.length > LIMITS.line) p.push(`line ${i + 1} must be 1 to ${LIMITS.line} characters`); });
  }
  if (!text(c.cta) || c.cta.length > LIMITS.cta) p.push(`cta must be 1 to ${LIMITS.cta} characters`);
  const all = [c.kicker, c.hook, ...(c.lines || []), c.cta].filter(text).join(" ");
  if (/https?:\/\/|www\.|\.(com|org|gov|net|io)\b/i.test(all)) p.push("no web address may appear in the words; the end card carries the site");
  return p;
}

const words = (s) => s.trim().split(/\s+/).length;
const round = (n) => Math.round(n * 10) / 10;
// Reading time: about 3.3 words a second plus a beat, from 3.5 to 8 seconds a scene.
const sceneSeconds = (s, min = 3.5) => round(Math.min(8, Math.max(min, 1.4 + words(s) * 0.3)));
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December";
const HL = new RegExp(`(\\$[\\d,.]+(?:\\s?(?:million|billion))?|\\d[\\d,.]*%|\\b\\d{1,2} (?:${MONTHS})(?: \\d{4})?\\b)`, "g");
const marked = (s) => esc(s).replace(HL, '<span class="hl">$1</span>');

export function buildExplainer(piece, outRoot = join(tmpdir(), "fd-explainers")) {
  const problems = checkExplainer(piece);
  if (problems.length) throw new Error(problems.join("; "));
  const c = piece.content;
  const scenes = [];
  let t = 0;
  const hookDur = sceneSeconds(c.hook, 4);
  scenes.push({ id: "s0", kind: "hook", start: 0, dur: hookDur });
  t = hookDur;
  c.lines.forEach((line, i) => {
    const d = sceneSeconds(line);
    scenes.push({ id: `s${i + 1}`, kind: "line", text: line, n: i + 1, start: round(t), dur: d });
    t = round(t + d);
  });
  const endDur = 4.5, endStart = round(t), total = round(t + endDur);
  const sceneHtml = scenes.map((s) => s.kind === "hook"
    ? `      <section id="${s.id}" class="clip scene" data-start="${s.start}" data-duration="${s.dur}" data-track-index="1">
        ${c.kicker ? `<p class="kicker">${esc(c.kicker)}</p>` : ""}
        <h1 class="hook">${marked(c.hook)}</h1>
      </section>`
    : `      <section id="${s.id}" class="clip scene" data-start="${s.start}" data-duration="${s.dur}" data-track-index="1">
        <p class="num">${String(s.n).padStart(2, "0")}</p>
        <p class="line">${marked(s.text)}</p>
      </section>`).join("\n");
  const tweens = scenes.map((s) =>
    `      tl.fromTo("#${s.id}", { opacity: 0, y: 36 }, { opacity: 1, y: 0, duration: 0.6, ease: "power2.out" }, ${s.start});\n` +
    `      tl.to("#${s.id}", { opacity: 0, y: -18, duration: 0.4, ease: "power1.in" }, ${round(s.start + s.dur - 0.4)});`).join("\n");
  const html = `<!doctype html>
<html lang="en" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>${esc(piece.id)}</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      @font-face { font-family: "Source Serif 4"; font-weight: 600; src: url("assets/fonts/source-serif-4-latin-600-normal.woff2") format("woff2"); }
      @font-face { font-family: "IBM Plex Sans"; font-weight: 400; src: url("assets/fonts/ibm-plex-sans-latin-400-normal.woff2") format("woff2"); }
      @font-face { font-family: "IBM Plex Sans"; font-weight: 500; src: url("assets/fonts/ibm-plex-sans-latin-500-normal.woff2") format("woff2"); }
      :root { --navy: #06162D; --emerald: #15B781; --offwhite: #F9FBFA; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: var(--navy); }
      #root { position: relative; width: 1080px; height: 1920px; background: var(--navy); color: var(--offwhite); font-family: "IBM Plex Sans", sans-serif; }
      .clip { position: absolute; inset: 0; }
      #header { display: flex; align-items: center; gap: 26px; position: absolute; inset: 250px 120px auto 120px; height: 72px; }
      #header img { width: 72px; height: 72px; display: block; }
      #header span { font-family: "Source Serif 4", serif; font-weight: 600; font-size: 44px; color: var(--offwhite); letter-spacing: -0.005em; }
      .scene { display: flex; flex-direction: column; justify-content: center; padding: 400px 160px 520px 120px; }
      .kicker { font-weight: 500; font-size: 40px; color: var(--emerald); margin-bottom: 36px; }
      .hook { font-family: "Source Serif 4", serif; font-weight: 600; font-size: 96px; line-height: 1.08; letter-spacing: -0.015em; }
      .num { font-family: "Source Serif 4", serif; font-weight: 600; font-size: 64px; color: var(--emerald); margin-bottom: 28px; }
      .line { font-size: 62px; line-height: 1.3; }
      .hl { color: var(--emerald); font-weight: 500; }
      #bar-track { position: absolute; inset: 1450px 120px auto 120px; height: 6px; background: rgba(249, 251, 250, 0.14); border-radius: 3px; }
      #bar { width: 840px; height: 6px; background: var(--emerald); border-radius: 3px; transform-origin: left center; }
      #end { display: flex; flex-direction: column; justify-content: center; padding: 300px 160px 520px 120px; gap: 44px; }
      #end img { width: 160px; height: 160px; display: block; }
      #end .cta { font-family: "Source Serif 4", serif; font-weight: 600; font-size: 76px; line-height: 1.12; letter-spacing: -0.01em; }
      #end .site { font-weight: 500; font-size: 46px; color: var(--emerald); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="${total}" data-width="1080" data-height="1920">
      <div id="header" class="clip" data-start="0" data-duration="${endStart}" data-track-index="0">
        <img src="assets/fd-mark.svg" alt="" /><span>Finance Department</span>
      </div>
      <div id="bar-track" class="clip" data-start="0" data-duration="${endStart}" data-track-index="2"><div id="bar"></div></div>
${sceneHtml}
      <section id="end" class="clip" data-start="${endStart}" data-duration="${endDur}" data-track-index="1">
        <img src="assets/fd-mark.svg" alt="" />
        <p class="cta">${esc(c.cta)}</p>
        <p class="site">${SITE}</p>
      </section>
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      tl.fromTo("#header", { opacity: 0 }, { opacity: 1, duration: 0.6, ease: "power1.out" }, 0);
      tl.fromTo("#bar", { scaleX: 0 }, { scaleX: 1, duration: ${endStart}, ease: "none" }, 0);
${tweens}
      tl.fromTo("#end", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.7, ease: "power2.out" }, ${endStart});
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
`;
  const dir = join(outRoot, piece.id);
  mkdirSync(dir, { recursive: true });
  cpSync(join(here, "assets"), join(dir, "assets"), { recursive: true });
  writeFileSync(join(dir, "index.html"), html);
  writeFileSync(join(dir, "meta.json"), JSON.stringify({ id: piece.id, name: piece.id }, null, 2));
  // The middle of each scene and of the end card, for the frames a run looks at before it passes the piece.
  const looks = [...scenes.map((s) => round(s.start + s.dur / 2)), round(endStart + endDur / 2)];
  return { dir, total, looks };
}

function headlessShell() {
  if (process.env.PRODUCER_HEADLESS_SHELL_PATH) return process.env.PRODUCER_HEADLESS_SHELL_PATH;
  const root = "/opt/pw-browsers";
  if (!existsSync(root)) return undefined;
  for (const d of readdirSync(root).filter((d) => d.startsWith("chromium_headless_shell-")).sort().reverse()) {
    const p = join(root, d, "chrome-headless-shell-linux64", "chrome-headless-shell");
    if (existsSync(p)) return p;
  }
  return undefined;
}

// Builds and renders one explainer into mediaDir, and writes the scene frames into previewDir.
export function renderExplainer(piece, mediaDir, previewDir) {
  const { dir, total, looks } = buildExplainer(piece);
  mkdirSync(mediaDir, { recursive: true });
  const name = `${piece.test ? "TEST-" : ""}${piece.id}.mp4`;
  const out = join(mediaDir, name);
  const env = { ...process.env, HYPERFRAMES_SKIP_SKILLS: "1", DO_NOT_TRACK: "1" };
  const shell = headlessShell();
  if (shell) env.PRODUCER_HEADLESS_SHELL_PATH = shell;
  execFileSync("npx", ["--yes", HYPERFRAMES, "render", dir, "-o", out, "--quality", "delivery", "--quiet"], { env, stdio: "pipe", timeout: 15 * 60 * 1000 });
  const frames = [];
  if (previewDir) {
    mkdirSync(previewDir, { recursive: true });
    looks.forEach((t, i) => {
      const f = join(previewDir, `${piece.id}_${String(i).padStart(2, "0")}.png`);
      execFileSync("ffmpeg", ["-v", "error", "-y", "-ss", String(t), "-i", out, "-frames:v", "1", "-vf", "scale=540:-1", f]);
      frames.push(f);
    });
  }
  return { file: name, seconds: total, frames };
}
