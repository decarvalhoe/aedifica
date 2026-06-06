import { test, expect, type Page } from "@playwright/test";

// Register a fresh atelier with email + password (the real auth front door).
// Registration seeds the reference project and lands on the smart home.
async function register(page: Page, org: string, email: string) {
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Créer un atelier" }).click(); // switch to register tab
  await page.getByPlaceholder("Atelier Martin").fill(org);
  await page.getByPlaceholder("vous@atelier.ch").fill(email);
  await page.getByPlaceholder("6 caractères minimum").fill("motdepasse1");
  await page.getByRole("button", { name: "Créer l'atelier" }).click();
  await expect(page.getByRole("heading", { name: /Vos projets/ })).toBeVisible();
}

// End-to-end smoke: register, open the seeded reference project, and run the
// agent→Archicad action loop (preview → approval → apply) with the safety gate.
test("auth → project → action loop", async ({ page }) => {
  await register(page, "E2E Atelier", "e2e@test.ch");

  // Smart home shows the seeded reference project; open it.
  await page.getByRole("button", { name: /Place de la Palud/ }).click();
  // Dual-nav workspace: the SIA phase rail is always present.
  await expect(page.getByText("Parcours SIA du projet")).toBeVisible();

  // Open the Copilote IA surface (task nav) and run the action loop.
  await page.locator(".ws__side").getByRole("button", { name: /Copilote/ }).click();
  await page.getByRole("button", { name: "Demander un aperçu" }).click();
  await expect(page.getByText(/Aperçu prêt/)).toBeVisible();

  await page.getByRole("button", { name: "Valider l'exécution" }).click();
  await expect(page.getByText(/Exécution validée/).first()).toBeVisible();

  await page.getByRole("button", { name: "Appliquer à la maquette" }).click();
  await expect(page.getByText(/Modification appliquée et inscrite/)).toBeVisible();
});
