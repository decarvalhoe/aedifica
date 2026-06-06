// W11 P1 audit — drive a real browser through every workspace surface and
// capture a screenshot of each, so we can verify visually that the new identity
// (official wordmark SVG, monogram, sprite icons) and the wirings (phase rail,
// checklist filter dropdown + .on feedback, document validation buttons,
// ingestion banner) actually render.
//
// Usage:
//   AEDIFICA_URL=https://aedifica-demo.fly.dev \
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

function shot(name) {
  return page.screenshot({ path: resolve(OUT, `${name}.png`), fullPage: true });
}

async function step(name, fn) {
  console.log(`▸ ${name}`);
  await fn();
  await page.waitForTimeout(500);
  await shot(name);
}

// 1) Login screen
await page.goto(`${URL}/workspace`, { waitUntil: "networkidle" });
await page.waitForTimeout(800);
await step("01-login", async () => {});

// 2) Log in as the architect
await page.locator('input[type="email"]').fill(EMAIL);
await page.locator('input[type="password"]').fill(PWD);
await page.getByRole("button", { name: /Se connecter/i }).click();
await page.waitForLoadState("networkidle");
await page.waitForTimeout(1500);
await step("02-home", async () => {});

// 3) Open the project (click the first project card)
const card = page.locator(".home__card, .card").first();
await card.click({ trial: false }).catch(() => {});
await page.waitForTimeout(1500);
await step("03-dashboard", async () => {});

// 4) Coordination
await page.getByRole("button", { name: /Coordination/i }).first().click();
await page.waitForTimeout(800);
await step("04-coordination", async () => {});

// 5) Checklist
await page.getByRole("button", { name: /Checklist SIA/i }).click();
await page.waitForTimeout(800);
await step("05-checklist", async () => {});

// 6) Documents
await page.getByRole("button", { name: /Documents & sources/i }).click();
await page.waitForTimeout(800);
await step("06-documents", async () => {});

// 7) BRS
await page.getByRole("button", { name: /Exigences \(BRS\)/i }).click();
await page.waitForTimeout(800);
await step("07-brs", async () => {});

// 8) Intervenants
await page.getByRole("button", { name: /^Intervenants$/i }).click();
await page.waitForTimeout(800);
await step("08-intervenants", async () => {});

// 9) Terrain & zonage
await page.getByRole("button", { name: /Terrain & zonage/i }).click();
await page.waitForTimeout(800);
await step("09-terrain", async () => {});

// 10) Tâches
await page.getByRole("button", { name: /Tâches & priorités/i }).click();
await page.waitForTimeout(800);
await step("10-taches", async () => {});

// 11) Permis
await page.getByRole("button", { name: /Dossier de permis/i }).click();
await page.waitForTimeout(800);
await step("11-permis", async () => {});

// 12) Opposition
await page.getByRole("button", { name: /Risque d'opposition/i }).click();
await page.waitForTimeout(800);
await step("12-opposition", async () => {});

// 13) Conformité
await page.getByRole("button", { name: /^Conformité$/i }).click();
await page.waitForTimeout(800);
await step("13-conformite", async () => {});

// 14) Couts
await page.getByRole("button", { name: /Coûts & soumissions/i }).click();
await page.waitForTimeout(800);
await step("14-couts", async () => {});

// 15) Chantier
await page.getByRole("button", { name: /Chantier & remise/i }).click();
await page.waitForTimeout(800);
await step("15-chantier", async () => {});

// 16) Mémoire
await page.getByRole("button", { name: /^Mémoire$/i }).click();
await page.waitForTimeout(800);
await step("16-memoire", async () => {});

// 17) Copilote
await page.getByRole("button", { name: /Copilote/i }).click();
await page.waitForTimeout(800);
await step("17-copilote", async () => {});

// 18) Équipe
await page.getByRole("button", { name: /^Équipe$/i }).click();
await page.waitForTimeout(800);
await step("18-equipe", async () => {});

await browser.close();
console.log(`\n✓ Wrote ${18} screenshots to ${OUT}`);
