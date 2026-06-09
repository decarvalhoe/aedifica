import { test, expect, type Page } from "@playwright/test";

// Register a fresh atelier with email + password (the real auth front door).
// W17: fresh ateliers are intentionally empty. The project is created
// explicitly below before exercising project-bound flows.
async function register(page: Page, org: string, email: string) {
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Créer un atelier" }).click(); // switch to register tab
  await page.getByPlaceholder("Atelier Martin").fill(org);
  await page.getByPlaceholder("vous@atelier.ch").fill(email);
  await page.getByPlaceholder("6 caractères minimum").fill("motdepasse1");
  await page.getByRole("button", { name: "Créer l'atelier" }).click();
  await expect(page.getByText("Créer votre premier projet")).toBeVisible();
  await expect(page.locator(".psw-cur .nm")).toHaveText("Aucun projet");
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
  await expect(page.getByText("Parcours SIA du projet")).toBeVisible();
}

// End-to-end smoke: register, create a project, ride the action loop,
// preview → approval → apply with the safety gate.
test("auth → project → action loop", async ({ page }) => {
  await register(page, "E2E Atelier", "e2e@test.ch");
  await createProject(page, "E2E Projet", "Lausanne");

  // Open the Copilote IA surface (task nav) and run the action loop.
  await page.locator(".ws__side").getByRole("button", { name: /Copilote/ }).click();
  // W11.D: the demand is now parametric — fill the target element + the desired
  // value before asking for a preview. Type defaults to set_property.
  await page.getByPlaceholder("ex. AC-SPACE-101").fill("AC-SPACE-101");
  await page.getByPlaceholder("ex. bureau").fill("bureau");
  await page.getByRole("button", { name: "Demander un aperçu" }).click();
  await expect(page.getByText(/Aperçu prêt/)).toBeVisible();

  await page.getByRole("button", { name: "Valider l'exécution" }).click();
  await expect(page.getByText(/Exécution validée/).first()).toBeVisible();

  await page.getByRole("button", { name: "Appliquer à la maquette" }).click();
  await expect(page.getByText(/Modification appliquée et inscrite/)).toBeVisible();
});
