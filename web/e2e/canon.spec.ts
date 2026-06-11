import { test, expect, type Page } from "@playwright/test";

// W22-1 — le canon promu, en boucle complète dans le navigateur :
// l'architecte valide une pièce en CANONIQUE avec son extrait citable →
// la doctrine cite la pièce de l'atelier (Indicatif · Promu atelier — jamais
// le certifié officiel) → il la rétrograde → la doctrine s'abstient à nouveau.
// C'est la séance Etienne §E (sourçage canonique manuel + injection d'une
// source) branchée sur la couche savoir.

const EXTRACT = "La hauteur maximale au faîte est limitée à 9 mètres en zone village (art. 12 RPGA).";

async function register(page: Page, org: string, email: string) {
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Créer un atelier" }).click();
  await page.getByPlaceholder("Atelier Martin").fill(org);
  await page.getByPlaceholder("vous@atelier.ch").fill(email);
  await page.getByPlaceholder("6 caractères minimum").fill("motdepasse1");
  await page.getByRole("button", { name: "Créer l'atelier" }).click();
  await expect(page.getByText("Créer votre premier projet")).toBeVisible();
}

async function createProject(page: Page, name: string, commune: string) {
  await page.locator(".psw-btn").click();
  await page.getByRole("button", { name: /Nouveau projet/ }).click();
  await page.getByPlaceholder("Nom du projet").fill(name);
  const communeField = page.getByPlaceholder("Commune");
  await communeField.fill("");
  await communeField.fill(commune);
  await expect(page.getByText(/Canton détecté/)).toBeVisible();
  const create = page.getByRole("button", { name: "Créer", exact: true });
  await expect(create).toBeEnabled();
  await create.click();
  await expect(page.locator(".psw-cur .nm")).toHaveText(name);
}

test("canon promu: valider → la doctrine cite la pièce de l'atelier → rétrograder → abstention", async ({ page }) => {
  const run = Date.now();
  await register(page, "Atelier Canon", `canon-${run}@test.ch`);
  await createProject(page, "Canon Promu", "Lausanne");

  // 1. Create the source piece.
  await page.locator(".ws__side").getByRole("button", { name: /Documents & sources/ }).click();
  await page.getByPlaceholder("Nom officiel du document").fill("RPGA art. 12 — hauteurs");
  await page.getByRole("button", { name: "Ajouter", exact: true }).click();
  await expect(page.getByText("RPGA art. 12 — hauteurs")).toBeVisible();

  // 2. Canonical = promotion act: the extract editor opens, the architect
  //    provides the exact passage.
  await page.getByRole("button", { name: "Canonique", exact: true }).click();
  const promo = page.locator('[data-testid^="promo-"]');
  await expect(promo).toBeVisible();
  await promo.locator("textarea").fill(EXTRACT);
  await promo.getByRole("button", { name: "Promouvoir en canonique" }).click();
  await expect(page.locator('[data-testid^="citable-"]')).toBeVisible();
  await expect(page.getByText("Citable · promu atelier")).toBeVisible();
  // The W21-2 corpus card counts the project silo.
  await expect(page.getByTestId("corpus-counts")).toContainText("Projet : 1");

  // 3. The doctrine cites the atelier's own piece — honestly tiered.
  await page.locator(".ws__side").getByRole("button", { name: /Copilote/ }).click();
  const panel = page.getByTestId("doctrine-qa");
  await panel.getByPlaceholder(/hauteur maximale/).fill("Quelle hauteur maximale au faîte ?");
  await panel.getByRole("button", { name: /Interroger/ }).click();
  const answer = page.getByTestId("doctrine-answer");
  await expect(answer).toBeVisible({ timeout: 15_000 });
  await expect(answer).toContainText("RPGA art. 12 — hauteurs");
  await expect(answer).toContainText("Promu atelier");
  await expect(answer).toContainText("Indicatif");
  await expect(answer).toContainText("la décision reste humaine");

  // 4. Demotion retracts: indicative -> the chunk is gone, the doctrine
  //    abstains again (revert-and-confirm, through the browser).
  await page.locator(".ws__side").getByRole("button", { name: /Documents & sources/ }).click();
  await page.getByRole("button", { name: "Indicatif", exact: true }).click();
  await expect(page.getByText("Citable · promu atelier")).toHaveCount(0);
  await expect(page.getByTestId("corpus-counts")).toContainText("Projet : 0");
  await page.locator(".ws__side").getByRole("button", { name: /Copilote/ }).click();
  await panel.getByPlaceholder(/hauteur maximale/).fill("Quelle hauteur maximale au faîte ?");
  await panel.getByRole("button", { name: /Interroger/ }).click();
  await expect(page.getByTestId("doctrine-abstention")).toBeVisible({ timeout: 15_000 });
});
