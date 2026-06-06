// Test if scrollLeft can be set at all on the Gantt's scroller.
import { chromium } from "@playwright/test";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
const __dirname = dirname(fileURLToPath(import.meta.url));

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } });
const page = await ctx.newPage();
await page.goto("https://aedifica-demo.fly.dev/workspace");
await page.waitForTimeout(800);
await page.locator('input[type="email"]').fill("etienne@carre-neuf.ch");
await page.locator('input[type="password"]').fill("carre-neuf-2026");
await page.locator('button.ds-btn.full').filter({ hasText: /Se connecter/i }).click();
await page.waitForLoadState("networkidle");
await page.waitForTimeout(1500);
await page.locator('nav.tnav button').filter({ has: page.locator('.lb', { hasText: /Atelier · multi-projet/i }) }).first().click();
await page.waitForTimeout(800);
await page.getByRole("button", { name: /^Gantt$/i }).click();
await page.waitForTimeout(3000);

// MANUALLY set scrollLeft and check if it sticks.
const r = await page.evaluate(() => {
  const svgGantt = document.querySelector("svg.gantt");
  if (!svgGantt) return { error: "no svg" };
  let el = svgGantt.parentElement;
  let scroller = null;
  while (el) {
    const s = getComputedStyle(el);
    if (s.overflowX === "auto" || s.overflow === "auto") { scroller = el; break; }
    el = el.parentElement;
  }
  if (!scroller) return { error: "no scroller" };
  const before = scroller.scrollLeft;
  scroller.scrollLeft = 1000;
  const afterImmediate = scroller.scrollLeft;
  return {
    before, afterImmediate,
    scrollWidth: scroller.scrollWidth,
    clientWidth: scroller.clientWidth,
    tagName: scroller.tagName,
    className: scroller.className,
    parent: scroller.parentElement?.tagName,
    childCount: scroller.children.length,
    overflow: getComputedStyle(scroller).overflow,
    overflowX: getComputedStyle(scroller).overflowX,
    display: getComputedStyle(scroller).display,
    position: getComputedStyle(scroller).position,
  };
});
console.log(JSON.stringify(r, null, 2));

await page.waitForTimeout(500);
const after = await page.evaluate(() => {
  const svgGantt = document.querySelector("svg.gantt");
  let el = svgGantt.parentElement;
  let scroller = null;
  while (el) {
    const s = getComputedStyle(el);
    if (s.overflowX === "auto" || s.overflow === "auto") { scroller = el; break; }
    el = el.parentElement;
  }
  return { scrollLeft: scroller ? scroller.scrollLeft : null };
});
console.log("500ms later:", JSON.stringify(after));

const out = resolve(__dirname, "..", "..", "docs", "audit", "gantt-after-manual.png");
await page.screenshot({ path: out, fullPage: false });
console.log("screenshot:", out);

await browser.close();
