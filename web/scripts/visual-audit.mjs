// Drive Playwright through every workspace surface and capture screenshots.
//
// Usage (from web/):
//   AEDIFICA_URL=http://localhost:3000 \
//   AEDIFICA_EMAIL=etienne@carre-neuf.ch \
//   AEDIFICA_PWD=carre-neuf-2026 \
//   node scripts/visual-audit.mjs
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(__dirname, "..", "..", "docs", "audit", "w11-p1");

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
await page.waitForTimeout(1500);
await shot("02-home");

// 3) Open the seeded project
await page.locator('button.pcard').first().click();
await page.waitForLoadState("networkidle");
await page.waitForTimeout(1500);
await shot("03-dashboard");

// 4) Iterate over the side nav by visible label
// nav buttons contain Icon + .lb label + optional .ph phase chip — match on the label text loosely.
// Side nav lives in `<nav class="tnav">`; each button has a `.lb` span carrying its label.
const nav = (name) => page.locator('nav.tnav button').filter({ has: page.locator('.lb', { hasText: new RegExp(name, "i") }) }).first();

const surfaces = [
  ["04-coordination", "Coordination"],
  ["05-checklist", "Checklist SIA"],
  ["06-documents", "Documents & sources"],
  ["07-brs", "Exigences \\(BRS\\)"],
  ["08-intervenants", "Intervenants"],
  ["09-terrain", "Terrain & zonage"],
  ["10-taches", "Tâches & priorités"],
  ["11-permis", "Dossier de permis"],
  ["12-opposition", "Risque d'opposition"],
  ["13-conformite", "Conformité"],
  ["14-couts", "Coûts & soumissions"],
  ["15-chantier", "Chantier & remise"],
  ["16-memoire", "Mémoire"],
  ["17-copilote", "Copilote · maquette"],
  ["18-equipe", "Équipe"],
];

for (const [slug, label] of surfaces) {
  try {
    await nav(label).click({ timeout: 10000 });
    await page.waitForTimeout(700);
    await shot(slug);
  } catch (e) {
    console.log(`  ✗ failed on ${slug}: ${e.message?.split("\n")[0]}`);
  }
}

await browser.close();
console.log(`\n✓ Wrote screenshots to ${OUT}`);
