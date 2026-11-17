// Compares tools/coverage.json with the offer pages in the website repository, so a piece never shows a coverage list
// the page no longer has. Each offer's items must be the page's What you get list (the gets prop of its OfferPage),
// word for word and in order.
//
//   node tools/coverage.mjs --check ../financedepartment
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const at = process.argv.indexOf("--check");
const repo = at > -1 ? process.argv[at + 1] : null;
if (!repo) { console.error("usage: node tools/coverage.mjs --check <path to the financedepartment repository>"); process.exit(2); }
const cov = JSON.parse(readFileSync(join(here, "coverage.json"), "utf8"));
const problems = [];
for (const [id, o] of Object.entries(cov.offers)) {
  const f = join(repo, "src", "pages", o.source);
  if (!existsSync(f)) { problems.push(`${id}: ${o.source} is not in the website repository`); continue; }
  const t = readFileSync(f, "utf8");
  const m = /gets=\{\[([\s\S]*?)\]\}/.exec(t);
  if (!m) { problems.push(`${id}: no What you get list found in ${o.source}`); continue; }
  const gets = [...m[1].matchAll(/"((?:[^"\\]|\\.)*)"/g)].map((x) => x[1].replace(/\\"/g, '"'));
  const items = o.items.map((x) => x.text);
  if (gets.length !== items.length) problems.push(`${id}: the page lists ${gets.length} items, coverage.json ${items.length}`);
  gets.forEach((g, i) => { if (items[i] !== g) problems.push(`${id} item ${i + 1}: the page says "${g}", coverage.json "${items[i] || ""}"`); });
  if (!t.includes(`offerSeo("${o.page}")`)) problems.push(`${id}: ${o.source} is not the page at ${o.page}`);
}
console.log(JSON.stringify({ ok: !problems.length, offers: Object.keys(cov.offers).length, problems }, null, 2));
process.exit(problems.length ? 1 : 0);
