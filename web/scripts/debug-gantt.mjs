// Capture a fresh Gantt screenshot.
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

// Open Atelier multi-projet
await page.locator('nav.tnav button').filter({ has: page.locator('.lb', { hasText: /Atelier · multi-projet/i }) }).first().click();
await page.waitForTimeout(800);

// Click Gantt view
await page.getByRole("button", { name: /^Gantt$/i }).click();
await page.waitForTimeout(2000);

const out = resolve(__dirname, "..", "..", "docs", "audit", "gantt-debug.png");
await page.screenshot({ path: out, fullPage: false });
console.log(`viewport saved → ${out}`);

// Also fullPage
const outFull = resolve(__dirname, "..", "..", "docs", "audit", "gantt-debug-full.png");
await page.screenshot({ path: outFull, fullPage: true });
console.log(`full saved → ${outFull}`);

// Dump info about the gantt
const r = await page.evaluate(() => {
  const containers = document.querySelectorAll("svg.gantt");
  const out = [];
  containers.forEach((c) => {
    const r = c.getBoundingClientRect();
    out.push({
      tagName: c.tagName,
      width: r.width, height: r.height,
      viewBox: c.getAttribute("viewBox"),
      childCount: c.children.length,
    });
  });
  return out;
});
console.log("Gantt SVGs found:", JSON.stringify(r, null, 2));

await browser.close();
