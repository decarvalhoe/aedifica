// Debug screenshot — viewport only, no fullPage.
import { chromium } from "@playwright/test";

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
const page = await ctx.newPage();

await page.goto("https://aedifica-demo.fly.dev/workspace");
await page.waitForTimeout(800);
await page.locator('input[type="email"]').fill("etienne@carre-neuf.ch");
await page.locator('input[type="password"]').fill("carre-neuf-2026");
await page.locator('button.ds-btn.full').filter({ hasText: /Se connecter/i }).click();
await page.waitForLoadState("networkidle");
await page.waitForTimeout(1800);
// Resize to mobile.
await page.setViewportSize({ width: 390, height: 844 });
await page.waitForTimeout(500);

// Viewport screenshot
await page.screenshot({ path: "/tmp/mobile-viewport.png", fullPage: false });
console.log("viewport saved");
// Get computed style of .ws
const r = await page.evaluate(() => {
  const ws = document.querySelector(".ws");
  const aside = document.querySelector(".ws__side");
  const main = document.querySelector(".ws__main");
  const bodyRect = document.body.getBoundingClientRect();
  const mainRect = main?.getBoundingClientRect();
  return {
    ws_display: ws ? getComputedStyle(ws).display : "N/A",
    ws_minHeight: ws ? getComputedStyle(ws).minHeight : "N/A",
    aside_position: aside ? getComputedStyle(aside).position : "N/A",
    aside_transform: aside ? getComputedStyle(aside).transform : "N/A",
    bodyRect: { top: bodyRect.top, height: bodyRect.height },
    mainRect: mainRect ? { top: mainRect.top, height: mainRect.height } : null,
    docHeight: document.documentElement.scrollHeight,
    viewport: { w: window.innerWidth, h: window.innerHeight },
  };
});
console.log(JSON.stringify(r, null, 2));

await browser.close();
