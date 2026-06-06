// W15.C — drive Playwright through every workspace surface (W13 onwards:
// no intermediate Home page; project auto-selected; ProjectSwitcher in
// the sidebar) and capture screenshots, then a mobile pass.
//
// Usage (from web/):
//   AEDIFICA_URL=https://aedifica-demo.fly.dev \
//   AEDIFICA_EMAIL=etienne@carre-neuf.ch \
//   AEDIFICA_PWD=carre-neuf-2026 \
//   AEDIFICA_OUT_DIR=wave-15 \
//   node scripts/visual-audit.mjs
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_SUB = process.env.AEDIFICA_OUT_DIR || "wave-15";
const OUT = resolve(__dirname, "..", "..", "docs", "audit", OUT_SUB);

const URL = process.env.AEDIFICA_URL || "https://aedifica-demo.fly.dev";
const EMAIL = process.env.AEDIFICA_EMAIL || "etienne@carre-neuf.ch";
const PWD = process.env.AEDIFICA_PWD || "carre-neuf-2026";

await mkdir(OUT, { recursive: true });

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 1 });
const page = await ctx.newPage();

async function shot(name) {
  await page.screenshot({ path: resolve(OUT, `${name}.png`), fullPage: true });
  console.log(`▸ ${name}`);
}

// 1) Login
await page.goto(`${URL}/workspace`, { waitUntil: "networkidle" });
await page.waitForTimeout(800);
await shot("01-login");

// 2) Auth in
await page.locator('input[type="email"]').fill(EMAIL);
await page.locator('input[type="password"]').fill(PWD);
await page.locator('button.ds-btn.full').filter({ hasText: /Se connecter/i }).click();
await page.waitForLoadState("networkidle");
await page.waitForTimeout(1800);
// W13+: the seeded project is auto-selected, landing directly on the
// Dashboard. No "Vos projets" page to click through.
await shot("02-dashboard");

// 3) Iterate over the side nav by visible label.
const nav = (name) =>
  page.locator('nav.tnav button').filter({ has: page.locator('.lb', { hasText: new RegExp(name, "i") }) }).first();

const surfaces = [
  ["03-foresight", "Foresight"],
  ["04-taches", "Tâches & priorités"],
  ["05-checklist", "Checklist SIA"],
  ["06-terrain", "Terrain"],
  ["07-copilote", "Copilote"],
  ["08-memoire", "Mémoire"],
  ["09-coordination", "Coordination"],
  ["10-intervenants", "Intervenants"],
  ["11-documents", "Documents & sources"],
  ["12-brs", "Exigences"],
  ["13-permis", "Dossier de permis"],
  ["14-opposition", "Risque d'opposition"],
  ["15-conformite", "Conformité"],
  ["16-couts", "Coûts"],
  ["17-chantier", "Chantier"],
  ["18-atelier", "Atelier · multi-projet"],
  ["19-equipe", "Équipe"],
  ["20-settings", "Réglages"],
];

for (const [slug, label] of surfaces) {
  try {
    await nav(label).click({ timeout: 10000 });
    await page.waitForTimeout(900);
    await shot(slug);
  } catch (e) {
    console.log(`  ✗ failed on ${slug}: ${e.message?.split("\n")[0]}`);
  }
}

// 4) Mobile audit (W15.D drawer + responsive)
console.log("\n--- mobile (390x844) ---");
await page.setViewportSize({ width: 390, height: 844 });
await nav("Tableau de bord").click().catch(() => {});
await page.waitForTimeout(700);
await shot("21-mobile-dashboard");
await page.locator(".ws__nav-toggle").click().catch(() => {});
await page.waitForTimeout(500);
await shot("22-mobile-drawer");
await page.locator(".ws__backdrop").click().catch(() => {});
await page.waitForTimeout(300);
await page.locator(".ws__nav-toggle").click().catch(() => {});
await page.waitForTimeout(300);
await nav("Atelier · multi-projet").click().catch(() => {});
await page.waitForTimeout(800);
await shot("23-mobile-atelier");

await browser.close();
console.log(`\n✓ Wrote screenshots to ${OUT}`);
