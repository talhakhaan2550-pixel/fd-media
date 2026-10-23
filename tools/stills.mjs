// Finance Department carousels and stories: one PNG per slide, drawn from HTML with the website's fonts.
// The words on each slide are exactly the words in the piece: nothing is added or reworded.
// Carousel slides are 1080 x 1350 (4:5); a story is one 1080 x 1920 frame.
import { mkdirSync, writeFileSync, existsSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { tmpdir } from "node:os";

const here = dirname(fileURLToPath(import.meta.url));
const ASSETS = pathToFileURL(join(here, "assets")).href;
export const LIMITS = {
  COVER: { kicker: 40, title: 90, footer: 60 },
  POINT: { num: 3, title: 80, body: 260, footer: 60 },
  CLOSE: { title: 80, body: 180, cta: 48 },
  STORY: { kicker: 40, title: 110, body: 200, cta: 48 },
};
const SITE = "financedepartmentllc.com";

export function checkStill(piece) {
  const p = [];
  if (!/^\d{4}-W\d{2}-[CS]\d{2}$/.test(piece.id || "")) p.push("id must look like 2026-W45-C01 or 2026-W45-S01");
  const kind = piece.format;
  if (kind !== "carousel" && kind !== "story") p.push("format must be carousel or story");
  const slides = piece.content && piece.content.slides;
  if (!Array.isArray(slides) || slides.length === 0) return p.concat(["content.slides is empty"]);
  if (kind === "story" && slides.length !== 1) p.push("a story has exactly one slide");
  if (kind === "carousel" && (slides.length < 3 || slides.length > 10)) p.push("a carousel has 3 to 10 slides");
  slides.forEach((s, i) => {
    const lim = LIMITS[s.layout];
    if (!lim) { p.push(`slide ${i + 1} has an unknown layout ${s.layout}`); return; }
    if (kind === "story" && s.layout !== "STORY") p.push(`slide ${i + 1} must use STORY`);
    if (kind === "carousel" && s.layout === "STORY") p.push(`slide ${i + 1} cannot use STORY`);
    if (kind === "carousel" && i === 0 && s.layout !== "COVER") p.push("a carousel starts with COVER");
    if (kind === "carousel" && i === slides.length - 1 && s.layout !== "CLOSE") p.push("a carousel ends with CLOSE");
    for (const k of Object.keys(s)) {
      if (k === "layout") continue;
      if (!(k in lim)) { p.push(`slide ${i + 1} has a field ${k} its layout does not use`); continue; }
      if (String(s[k]).length > lim[k]) p.push(`slide ${i + 1} ${k} is ${String(s[k]).length} characters, over ${lim[k]}`);
    }
    const needs = { COVER: ["title"], POINT: ["num", "title"], CLOSE: ["title", "cta"], STORY: ["title"] }[s.layout];
    for (const k of needs) if (!s[k] || !String(s[k]).trim()) p.push(`slide ${i + 1} needs ${k}`);
  });
  return p;
}

const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December";
const HL = new RegExp(`(\\$[\\d,.]+(?:\\s?(?:million|billion))?|\\d[\\d,.]*%|\\b\\d{1,2} (?:${MONTHS})(?: \\d{4})?\\b)`, "g");
const marked = (s) => esc(s).replace(HL, '<span class="hl">$1</span>');
// Long text gets a smaller size so it stays inside its box.
const size = (text, base, steps) => {
  const n = String(text || "").length;
  for (const [max, factor] of steps) if (n <= max) return Math.round(base * factor);
  return Math.round(base * steps[steps.length - 1][1]);
};
const TITLE_STEPS = [[40, 1], [60, 0.88], [80, 0.78], [110, 0.7]];
const BODY_STEPS = [[140, 1], [200, 0.9], [260, 0.82]];

const css = `
@font-face { font-family: "Source Serif 4"; font-weight: 600; src: url("${ASSETS}/fonts/source-serif-4-latin-600-normal.woff2") format("woff2"); }
@font-face { font-family: "IBM Plex Sans"; font-weight: 400; src: url("${ASSETS}/fonts/ibm-plex-sans-latin-400-normal.woff2") format("woff2"); }
@font-face { font-family: "IBM Plex Sans"; font-weight: 500; src: url("${ASSETS}/fonts/ibm-plex-sans-latin-500-normal.woff2") format("woff2"); }
:root { --navy: #06162D; --deep: #0B7955; --emerald: #15B781; --offwhite: #F9FBFA; --soft: #C9D1DB; --muted: #4E596A; --rule: #D1DBD6; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: var(--w); height: var(--h); overflow: hidden; font-family: "IBM Plex Sans", sans-serif; }
.slide { position: relative; width: var(--w); height: var(--h); display: flex; flex-direction: column; }
.navy { background: var(--navy); color: var(--offwhite); }
.light { background: var(--offwhite); color: var(--navy); }
.brand { display: flex; align-items: center; gap: 20px; }
.brand img { display: block; }
.brand span { font-family: "Source Serif 4", serif; font-weight: 600; letter-spacing: -0.005em; }
.serif { font-family: "Source Serif 4", serif; font-weight: 600; letter-spacing: -0.015em; }
.hl { color: var(--emerald); }
.light .hl { color: var(--deep); }
.foot { display: flex; justify-content: space-between; font-size: 26px; }
.navy .foot { color: var(--soft); }
.light .foot { color: var(--muted); }
`;

function slideHtml(s, i, total, kind) {
  const W = 1080, H = kind === "story" ? 1920 : 1350;
  const page = `${i + 1}/${total}`;
  const brand = (px, color) => `<div class="brand"><img src="${ASSETS}/fd-mark.svg" style="width:${px}px;height:${px}px"><span style="font-size:${Math.round(px * 0.62)}px;color:${color}">Finance Department</span></div>`;
  let inner = "";
  if (s.layout === "COVER") {
    inner = `<div class="slide navy" style="padding:80px">
      ${brand(64, "#F9FBFA")}
      <div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:34px;padding-bottom:40px">
        ${s.kicker ? `<p style="font-weight:500;font-size:36px;color:var(--emerald)">${esc(s.kicker)}</p>` : ""}
        <h1 class="serif" style="font-size:${size(s.title, 88, TITLE_STEPS)}px;line-height:1.08">${marked(s.title)}</h1>
      </div>
      <div class="foot"><span>${esc(s.footer || SITE)}</span><span>${page}</span></div>
    </div>`;
  } else if (s.layout === "POINT") {
    inner = `<div class="slide light" style="padding:80px">
      ${brand(48, "#06162D")}
      <div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding-bottom:30px">
        <p class="serif" style="font-size:128px;line-height:1;color:var(--deep)">${esc(s.num)}</p>
        <div style="width:140px;height:5px;background:var(--deep);margin:34px 0 40px"></div>
        <h2 class="serif" style="font-size:${size(s.title, 62, TITLE_STEPS)}px;line-height:1.12;color:var(--navy)">${marked(s.title)}</h2>
        ${s.body ? `<p style="margin-top:34px;font-size:${size(s.body, 38, BODY_STEPS)}px;line-height:1.42;color:var(--muted)">${marked(s.body)}</p>` : ""}
      </div>
      <div class="foot"><span>${esc(s.footer || SITE)}</span><span>${page}</span></div>
    </div>`;
  } else if (s.layout === "CLOSE") {
    inner = `<div class="slide navy" style="padding:80px">
      ${brand(64, "#F9FBFA")}
      <div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:36px">
        <h2 class="serif" style="font-size:${size(s.title, 80, TITLE_STEPS)}px;line-height:1.1">${marked(s.title)}</h2>
        ${s.body ? `<p style="font-size:${size(s.body, 40, BODY_STEPS)}px;line-height:1.4;color:var(--soft)">${marked(s.body)}</p>` : ""}
      </div>
      <div style="background:var(--deep);border-radius:22px;height:112px;display:flex;align-items:center;justify-content:center;font-weight:500;font-size:36px;color:#fff">${esc(s.cta)}</div>
    </div>`;
  } else if (s.layout === "STORY") {
    // Instagram and Facebook cover about the top 250 and bottom 340 pixels of a story with their own bars.
    inner = `<div class="slide navy" style="padding:280px 96px 360px 96px">
      ${brand(72, "#F9FBFA")}
      <div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:40px">
        ${s.kicker ? `<p style="font-weight:500;font-size:42px;color:var(--emerald)">${esc(s.kicker)}</p>` : ""}
        <h1 class="serif" style="font-size:${size(s.title, 100, TITLE_STEPS)}px;line-height:1.07">${marked(s.title)}</h1>
        ${s.body ? `<p style="font-size:${size(s.body, 46, BODY_STEPS)}px;line-height:1.38;color:var(--soft)">${marked(s.body)}</p>` : ""}
      </div>
      ${s.cta ? `<p style="font-weight:500;font-size:46px;color:var(--emerald)">${esc(s.cta)}</p>` : ""}
    </div>`;
  }
  return { W, H, html: `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head><body style="--w:${W}px;--h:${H}px">${inner}</body></html>` };
}

export function chromiumPath() {
  if (process.env.CHROMIUM_PATH && existsSync(process.env.CHROMIUM_PATH)) return process.env.CHROMIUM_PATH;
  const root = "/opt/pw-browsers";
  if (existsSync(root)) {
    for (const d of readdirSync(root).filter((d) => /^chromium-\d+$/.test(d)).sort().reverse()) {
      const p = join(root, d, "chrome-linux64", "chrome");
      if (existsSync(p)) return p;
    }
  }
  return undefined;
}

// Renders a still piece's slides into outDir and returns the file names in slide order.
export async function renderStill(piece, outDir) {
  const problems = checkStill(piece);
  if (problems.length) throw new Error(problems.join("; "));
  const { chromium } = await import("playwright-core");
  mkdirSync(outDir, { recursive: true });
  const work = join(tmpdir(), `fd-still-${piece.id}`);
  mkdirSync(work, { recursive: true });
  const browser = await chromium.launch({ executablePath: chromiumPath() });
  const files = [];
  try {
    const slides = piece.content.slides;
    for (let i = 0; i < slides.length; i++) {
      const { W, H, html } = slideHtml(slides[i], i, slides.length, piece.format);
      const file = join(work, `slide${i + 1}.html`);
      writeFileSync(file, html);
      const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
      await page.goto(pathToFileURL(file).href);
      await page.evaluate(() => document.fonts.ready);
      const fontsOk = await page.evaluate(() => document.fonts.check('600 40px "Source Serif 4"') && document.fonts.check('400 40px "IBM Plex Sans"'));
      if (!fontsOk) throw new Error("the brand fonts did not load");
      const overflow = await page.evaluate(() => document.body.scrollHeight > window.innerHeight + 1 || document.body.scrollWidth > window.innerWidth + 1);
      if (overflow) throw new Error(`slide ${i + 1} text overflows the frame`);
      const name = `${piece.test ? "TEST-" : ""}${piece.id}_${String(i + 1).padStart(2, "0")}.png`;
      await page.screenshot({ path: join(outDir, name) });
      await page.close();
      files.push(name);
    }
  } finally {
    await browser.close();
  }
  return files;
}
