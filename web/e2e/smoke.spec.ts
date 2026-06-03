import { test, expect } from "@playwright/test";

// End-to-end smoke: a real user path through the product — create an account,
// open the seeded reference project, and run the agent→Archicad action loop
// (preview → approval → apply) with the safety gate intact.
test("auth → project → action loop", async ({ page }) => {
  await page.goto("/workspace");

  // Register a fresh atelier (token-based auth).
  await page.getByPlaceholder("Nom de l'atelier").fill("E2E Atelier");
  await page.getByPlaceholder("Votre e-mail").fill("e2e@test.ch");
  await page.getByRole("button", { name: "Créer l'atelier" }).click();

  // Projects hub shows the seeded reference project; open it.
  await expect(page.getByRole("heading", { name: "Vos projets" })).toBeVisible();
  await page.getByRole("button", { name: /Place de la Palud/ }).click();

  // Land on the dashboard.
  await expect(page.getByRole("heading", { name: "Vue d'ensemble" })).toBeVisible();

  // Open the Copilote IA surface and run the action loop.
  await page.getByRole("button", { name: /Copilote IA/ }).click();
  await page.getByRole("button", { name: "Demander un aperçu" }).click();
  await expect(page.getByText(/Aperçu prêt/)).toBeVisible();

  await page.getByRole("button", { name: "Valider l'exécution" }).click();
  await expect(page.getByText(/Exécution validée/).first()).toBeVisible();

  await page.getByRole("button", { name: "Appliquer à la maquette" }).click();
  await expect(page.getByText(/Modification appliquée à la maquette et inscrite/)).toBeVisible();
});
