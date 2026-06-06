import { test, expect, type Page } from "@playwright/test";

// Register a fresh atelier with email + password (the real auth front door).
// W13: registration now lands DIRECTLY in the unified workspace — the
// reference project ("Place de la Palud") is auto-selected, the SIA phase
// rail is visible immediately, no intermediate Home page to click through.
async function register(page: Page, org: string, email: string) {
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Créer un atelier" }).click(); // switch to register tab
  await page.getByPlaceholder("Atelier Martin").fill(org);
  await page.getByPlaceholder("vous@atelier.ch").fill(email);
  await page.getByPlaceholder("6 caractères minimum").fill("motdepasse1");
  await page.getByRole("button", { name: "Créer l'atelier" }).click();
  // The seeded project is auto-selected, the workspace shell renders directly.
  await expect(page.getByText("Parcours SIA du projet")).toBeVisible();
}

// End-to-end smoke: register, ride the action loop on the seeded reference
// project (auto-selected by W13), preview → approval → apply with the safety gate.
test("auth → project → action loop", async ({ page }) => {
  await register(page, "E2E Atelier", "e2e@test.ch");

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
