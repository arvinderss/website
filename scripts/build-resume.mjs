#!/usr/bin/env node
// Builds an ATS-friendly A4 resume PDF from the CV content on index.html.
// Usage: node scripts/build-resume.mjs [in=index.html] [out=resume-arvinder-singh.pdf]
// Needs: node-html-parser (npm) and Chrome/Chromium (set CHROME to override the binary).
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { parse } from "node-html-parser";

const [inFile = "index.html", outFile = "resume-arvinder-singh.pdf"] = process.argv.slice(2);
const doc = parse(readFileSync(inFile, "utf8"));

const clean = (s = "") => s.replace(/\s+/g, " ").trim();
const txt = (el) => clean(el?.textContent ?? "");
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const $ = (sel, root = doc) => root.querySelector(sel);
const $$ = (sel, root = doc) => root.querySelectorAll(sel);
function must(el, what) { if (!el) throw new Error(`build-resume: could not find ${what} in ${inFile}`); return el; }

// ---------- Extract ----------
const hero = must($("main > section"), "hero section");
const cv = {
  name: txt(must($("h1", hero), "name (h1)")),
  title: txt($("h1 + p", hero)),
  location: txt([...$$(".badge", hero)].pop()),
  summary: txt($("p.max-w-xl", hero)),
  linkedin: $('a[href*="linkedin.com/in/"]')?.getAttribute("href") ?? "",
  email: ($('a[href^="mailto:"]')?.getAttribute("href") ?? "").replace(/^mailto:/, "").split("?")[0],
  site: $('link[rel="canonical"]')?.getAttribute("href") ?? "",
  highlights: $$('[aria-label="Highlights"] .card').map((c) => {
    const [num, label] = $$("p", c).map(txt);
    return `${num} ${/^[A-Z][a-z]/.test(label) && !/^LinkedIn/.test(label) ? label[0].toLowerCase() + label.slice(1) : label}`;
  }),
  skills: $$("#expertise .card").map((c) => ({ group: txt($("h3", c)), items: $$(".chip", c).map(txt) })),
  jobs: [],
  earlier: [],
  education: txt([...$$("#career > p")].pop()),
  certs: $$("#credentials a.cred").map((a) => {
    const [meta, name] = [txt($("p", a)), txt($("h3", a))];
    const [issuer, year] = meta.split("·").map(clean);
    return { name, issuer, year };
  }),
  certsMore: txt($("#credentials > p")).replace(/^Also:\s*/, ""),
};

for (const art of $$("#career ol > li > article")) {
  const dl = $("dl", art);
  if (dl) {
    cv.earlier = $$("dl > div", art).map((d) => ({ org: txt($("dt", d)), text: txt($("dd", d)) }));
    continue;
  }
  const [heading, when] = [txt($("h3", art)), txt($("h3 + span", art))];
  const [role, org] = heading.includes("·") ? heading.split("·").map(clean) : [null, heading];
  const bulletsOf = (root) => {
    const lis = $$("li", root).map(txt);
    return lis.length ? lis : $$("p.mt-3, p.mt-1\\.5", root).map(txt);
  };
  const roleBlocks = $$(".space-y-4 > div", art);
  const roles = roleBlocks.length
    ? roleBlocks.map((r) => {
        const ps = $$("p", r);
        return { title: txt(ps[0]).replace(/\s*Current$/, ""), when: txt(ps[1]), bullets: bulletsOf(r).filter((b) => b !== txt(ps[0]) && b !== txt(ps[1])) };
      })
    : [{ title: role, when: "", bullets: bulletsOf(art) }];
  cv.jobs.push({ org, when, roles });
}
if (!cv.jobs.length) throw new Error("build-resume: no career entries found");

// ---------- Render ----------
const li = (a) => a.map((b) => `<li>${esc(b)}</li>`).join("");
const contact = [
  cv.location,
  cv.email && `<a href="mailto:${esc(cv.email)}">${esc(cv.email)}</a>`,
  cv.linkedin && `<a href="${esc(cv.linkedin)}">${esc(cv.linkedin.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, ""))}</a>`,
  cv.site && `<a href="${esc(cv.site)}">${esc(cv.site.replace(/^https?:\/\//, "").replace(/\/$/, ""))}</a>`,
].filter(Boolean).join(" &nbsp;|&nbsp; ");

const html = `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>${esc(cv.name)} – Resume</title>
<style>
  @page { size: A4; margin: 14mm 15mm; }
  * { box-sizing: border-box; }
  body { font: 10pt/1.42 "Inter", "Helvetica Neue", Arial, sans-serif; color: #111827; margin: 0; }
  a { color: inherit; text-decoration: none; }
  h1 { font-size: 21pt; margin: 0; letter-spacing: -0.01em; }
  .title { font-size: 11.5pt; font-weight: 600; color: #3730a3; margin: 2px 0 4px; }
  .contact { font-size: 9pt; color: #374151; }
  h2 { font-size: 10pt; text-transform: uppercase; letter-spacing: 0.08em; color: #3730a3;
       border-bottom: 1.2px solid #c7d2fe; padding-bottom: 2px; margin: 13px 0 6px; break-after: avoid; }
  p { margin: 0 0 4px; }
  ul { margin: 2px 0 0; padding-left: 15px; } li { margin: 1px 0; }
  .hl { columns: 2; column-gap: 18px; }
  .job { break-inside: avoid; margin-bottom: 7px; }
  .row { display: flex; justify-content: space-between; gap: 12px; }
  .org { font-weight: 700; } .when { color: #4b5563; white-space: nowrap; font-size: 9.2pt; }
  .role { font-weight: 600; margin-top: 3px; }
  .skills p { margin-bottom: 3px; } .skills b { font-weight: 600; }
  .muted { color: #4b5563; font-size: 9.2pt; }
</style></head><body>
<header>
  <h1>${esc(cv.name)}</h1>
  <div class="title">${esc(cv.title)}</div>
  <div class="contact">${contact}</div>
</header>

<h2>Summary</h2>
<p>${esc(cv.summary)}</p>
${cv.highlights.length ? `<ul class="hl">${li(cv.highlights)}</ul>` : ""}

<h2>Experience</h2>
${cv.jobs.map((j) => `<div class="job">
  <div class="row"><span class="org">${esc(j.roles.length === 1 && j.roles[0].title ? `${j.roles[0].title}, ${j.org}` : j.org)}</span><span class="when">${esc(j.when)}</span></div>
  ${j.roles.map((r) => `${j.roles.length > 1 ? `<div class="row role"><span>${esc(r.title)}</span><span class="when">${esc(r.when)}</span></div>` : ""}<ul>${li(r.bullets)}</ul>`).join("")}
</div>`).join("")}
${cv.earlier.length ? `<div class="job"><div class="org">Earlier career</div><ul>${li(cv.earlier.map((e) => `${e.org}: ${e.text}`))}</ul></div>` : ""}

<h2>Skills</h2>
<div class="skills">${cv.skills.map((s) => `<p><b>${esc(s.group)}:</b> ${esc(s.items.join(", "))}</p>`).join("")}</div>

<h2>Certifications</h2>
<ul>${li(cv.certs.map((c) => `${c.name}, ${c.issuer} (${c.year})`))}</ul>
${cv.certsMore ? `<p class="muted" style="margin-top:4px">Also: ${esc(cv.certsMore)}</p>` : ""}

<h2>Education &amp; Languages</h2>
<p>${esc(cv.education)}</p>
</body></html>`;

// ---------- Print to PDF ----------
const work = mkdtempSync(join(tmpdir(), "resume-"));
const htmlPath = join(work, "resume.html");
writeFileSync(htmlPath, html);
const chrome = process.env.CHROME || ["google-chrome", "chromium", "chromium-browser"].find((b) => {
  try { execFileSync("which", [b], { stdio: "ignore" }); return true; } catch { return false; }
});
if (!chrome) throw new Error("build-resume: Chrome not found; set CHROME=/path/to/chrome");
execFileSync(chrome, [
  "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
  `--user-data-dir=${join(work, "profile")}`,
  `--print-to-pdf=${resolve(outFile)}`, pathToFileURL(htmlPath).href,
], { stdio: "inherit" });
if (process.env.KEEP_HTML) writeFileSync(outFile.replace(/\.pdf$/, ".html"), html);
rmSync(work, { recursive: true, force: true });
console.log(`build-resume: wrote ${outFile} (${cv.jobs.length} roles, ${cv.certs.length} certs)`);
