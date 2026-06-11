import { test, expect, type Page } from "@playwright/test";

// W21-5 — séance Etienne, les compléments :
// (§C/§D) un projet se crée À une phase d'entrée → la checklist SIA est seedée
//         avec les phases antérieures en rétroactif, et le dashboard affiche
//         les intervenants attendus de la phase (feuille SIA Vaud).
// (§A)    groupes ⊃ sous-groupes ⊃ personnes dans le registre d'intervenants.

async function register(page: Page, org: string, email: string) {
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Créer un atelier" }).click();
  await page.getByPlaceholder("Atelier Martin").fill(org);
  await page.getByPlaceholder("vous@atelier.ch").fill(email);
  await page.getByPlaceholder("6 caractères minimum").fill("motdepasse1");
  await page.getByRole("button", { name: "Créer l'atelier" }).click();
  await expect(page.getByText("Créer votre premier projet")).toBeVisible();
}

test("création à la phase 33 → checklist rétroactive + intervenants par phase au dashboard", async ({ page }) => {
  const run = Date.now();
  await register(page, "Atelier Entree", `entree-${run}@test.ch`);
  await page.locator(".psw-btn").click();
  await page.getByRole("button", { name: /Nouveau projet/ }).click();
  await page.getByPlaceholder("Nom du projet").fill("Reprise Permis");
  const communeField = page.getByPlaceholder("Commune");
  await communeField.fill("");
  await communeField.fill("Lausanne");
  await expect(page.getByText(/Canton détecté/)).toBeVisible();
  // W21-5 — the entry-phase select: the project is JOINED at phase 33.
  await page.locator(".psw-phase").selectOption("33");
  await expect(page.getByText(/marqués rétroactifs/)).toBeVisible();
  await page.getByRole("button", { name: "Créer", exact: true }).click();
  await expect(page.locator(".psw-cur .nm")).toHaveText("Reprise Permis");

  // The project landed IN phase 33 (not « à cadrer »).
  await expect(page.getByRole("heading", { name: /Phase 33/ })).toBeVisible();
  // Dashboard: SIA-expected actors of the current phase (feuille SIA Vaud).
  const card = page.getByTestId("intervenants-par-phase");
  await expect(card).toBeVisible();
  await expect(card).toContainText("Intervenants de la phase 33");
  await expect(card).toContainText("Atelier");
  // Checklist seeded with the earlier phases flagged retroactive.
  await page.locator(".ws__side").getByRole("button", { name: /Checklist SIA/ }).click();
  await expect(page.getByText(/step\(s\) rétroactif\(s\)/)).toBeVisible();
});

test("intervenants: groupe racine ⊃ sous-groupe, rendu en arborescence", async ({ page }) => {
  const run = Date.now();
  await register(page, "Atelier Arbo", `arbo-${run}@test.ch`);
  await page.locator(".psw-btn").click();
  await page.getByRole("button", { name: /Nouveau projet/ }).click();
  await page.getByPlaceholder("Nom du projet").fill("Arborescence");
  const communeField = page.getByPlaceholder("Commune");
  await communeField.fill("");
  await communeField.fill("Lausanne");
  await expect(page.getByText(/Canton détecté/)).toBeVisible();
  await page.getByRole("button", { name: "Créer", exact: true }).click();
  await expect(page.locator(".psw-cur .nm")).toHaveText("Arborescence");

  await page.locator(".ws__side").getByRole("button", { name: /Intervenants/ }).click();
  // Root group.
  await page.getByRole("button", { name: /Nouveau groupe/ }).click();
  await page.getByPlaceholder("Nom du groupe (ex. Ingénieurs)").fill("Ingénieurs");
  await page.getByRole("button", { name: "Créer", exact: true }).click();
  await expect(page.getByRole("heading", { name: /^Ingénieurs/ })).toBeVisible();
  // Sub-group under it (séance §A: « groupe ingénieur » → civil).
  await page.getByRole("button", { name: /Nouveau groupe/ }).click();
  await page.getByPlaceholder("Nom du groupe (ex. Ingénieurs)").fill("Civil");
  await page.locator("select", { hasText: "groupe racine" }).selectOption({ label: "Sous-groupe de · Ingénieurs" });
  await page.getByRole("button", { name: "Créer", exact: true }).click();
  // Indented under the parent, not a sibling card.
  await expect(page.getByText("↳ Civil")).toBeVisible();
  // The person form offers the qualified path.
  await expect(page.locator("option", { hasText: "Ingénieurs · Civil" })).toHaveCount(1);
});
