import { test, expect, type Page } from "@playwright/test";

// W22-2 — la chaîne complète d'un référentiel communal AU NAVIGATEUR :
// demande (seed + job tracé) → ingestion manuelle du règlement officiel
// (provenance complète exigée) → promotion après revue → pack « Actif ».
// Commune fictive unique par run (le cache des packs est global/partagé).

async function register(page: Page, org: string, email: string) {
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Créer un atelier" }).click();
  await page.getByPlaceholder("Atelier Martin").fill(org);
  await page.getByPlaceholder("vous@atelier.ch").fill(email);
  await page.getByPlaceholder("6 caractères minimum").fill("motdepasse1");
  await page.getByRole("button", { name: "Créer l'atelier" }).click();
  await expect(page.getByText("Créer votre premier projet")).toBeVisible();
}

test("communes: demande → ingestion tracée → promotion, sans toucher la DB", async ({ page }) => {
  const run = Date.now();
  const COMMUNE = `E2E-Ref-${run}`;
  await register(page, "Atelier Referentiels", `communes-${run}@test.ch`);

  await page.locator(".ws__side").getByRole("button", { name: /Communes · référentiels/ }).click();
  await expect(page.getByRole("heading", { name: /Communes · référentiels officiels/ })).toBeVisible();
  // La provenance du registre OFS est affichée (fraîcheur W18).
  await expect(page.getByTestId("ofs-freshness")).toContainText("OFS");

  // 1. Demande d'ingestion.
  await page.getByPlaceholder("Commune (ex. Vevey)").fill(COMMUNE);
  await page.locator("select.fld").first().selectOption("VD");
  await page.getByRole("button", { name: "Demander l'ingestion" }).click();
  await expect(page.getByTestId("communes-ok")).toContainText("Demande enregistrée");
  const seedRow = page.locator('[data-testid^="pack-"]', { hasText: COMMUNE });
  await expect(seedRow).toContainText("Demandé");
  await expect(seedRow).toContainText("job #");
  await expect(seedRow).toContainText("demandé");

  // 2. Ingestion manuelle — provenance complète exigée, zones JSON.
  await seedRow.getByRole("button", { name: /Ingestion manuelle/ }).click();
  const form = page.locator('[data-testid^="ingest-"]');
  await expect(form).toBeVisible();
  await form.getByPlaceholder(/Version \(ex\./).fill(`ref-${run}-2026-06`);
  await form.getByPlaceholder(/Autorité source \(ex\./).fill("Commune E2E / géoportail VD");
  await form.getByPlaceholder(/Valide au/).fill("2026-06-01");
  await form.getByPlaceholder(/Révision due/).fill("2026-12-01");
  await form.locator("textarea").fill('{"Zone village": {"ius": 0.4, "hauteur_max_m": 9}}');
  await form.getByRole("button", { name: "Ingérer cette version" }).click();
  await expect(page.getByTestId("communes-ok")).toContainText("ingérée");
  const ingRow = page.locator('[data-testid^="pack-"]', { hasText: `ref-${run}-2026-06` });
  await expect(ingRow).toContainText("Ingéré · à promouvoir");
  await expect(ingRow).toContainText("valide au 2026-06-01");
  await expect(ingRow).toContainText("1 zone(s)");

  // 3. Promotion après revue humaine.
  await ingRow.getByRole("button", { name: "Promouvoir" }).click();
  await expect(page.getByTestId("communes-ok")).toContainText("promu");
  await expect(page.locator('[data-testid^="pack-"]', { hasText: `ref-${run}-2026-06` })).toContainText("Actif");
});
