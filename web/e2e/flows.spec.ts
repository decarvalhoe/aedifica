import { test, expect, type Page } from "@playwright/test";

async function register(page: Page, org: string, email: string) {
  await page.goto("/workspace");
  await page.getByPlaceholder("Nom de l'atelier").fill(org);
  await page.getByPlaceholder("Votre e-mail").fill(email);
  await page.getByRole("button", { name: "Créer l'atelier" }).click();
  await expect(page.getByRole("heading", { name: "Vos projets" })).toBeVisible();
}

async function createProject(page: Page, name: string, commune: string) {
  await page.getByRole("button", { name: /Nouveau projet/ }).click();
  await page.getByPlaceholder("Nom du projet").fill(name);
  await page.getByPlaceholder(/Commune/).fill(commune);
  await page.getByRole("button", { name: "Créer & ouvrir" }).click();
  await expect(page.getByRole("heading", { name: "Vue d'ensemble" })).toBeVisible();
}

test("create project → empty Terrain (honest, not a fixture)", async ({ page }) => {
  await register(page, "Crea Atelier", "crea@test.ch");
  await createProject(page, "Villa Test", "Genève");
  await page.getByRole("button", { name: /Terrain & zonage/ }).click();
  await expect(page.getByText(/Aucune parcelle analysée/)).toBeVisible();
});

test("permit: submitting a piece flips it to present", async ({ page }) => {
  await register(page, "Permit Atelier", "permit@test.ch");
  await createProject(page, "Permit Proj", "Lausanne");
  await page.locator(".side").getByRole("button", { name: /Dossier de permis/ }).click();
  // empty project: nothing provided yet
  await expect(page.getByRole("button", { name: "Retirer" })).toHaveCount(0);
  await page.getByRole("button", { name: "Fournir" }).first().click();
  await expect(page.getByRole("button", { name: "Retirer" })).toHaveCount(1);
});

test("team: an owner can invite a member", async ({ page }) => {
  await register(page, "Team Atelier", "team@test.ch");
  await expect(page.getByRole("heading", { name: /Équipe/ })).toBeVisible();
  await page.getByRole("button", { name: /Inviter un collaborateur/ }).click();
  await page.getByPlaceholder("E-mail du collaborateur").fill("member@test.ch");
  await page.getByRole("button", { name: "Inviter" }).click();
  await expect(page.getByText("member@test.ch").first()).toBeVisible();
  await expect(page.getByText(/Membre ajouté/)).toBeVisible();
});
