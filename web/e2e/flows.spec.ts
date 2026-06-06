import { test, expect, type Page } from "@playwright/test";

async function register(page: Page, org: string, email: string) {
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Créer un atelier" }).click();
  await page.getByPlaceholder("Atelier Martin").fill(org);
  await page.getByPlaceholder("vous@atelier.ch").fill(email);
  await page.getByPlaceholder("6 caractères minimum").fill("motdepasse1");
  await page.getByRole("button", { name: "Créer l'atelier" }).click();
  await expect(page.getByRole("heading", { name: /Vos projets/ })).toBeVisible();
}

async function createProject(page: Page, name: string, commune: string) {
  await page.getByRole("button", { name: /Nouveau projet/ }).click();
  await page.getByPlaceholder("Nom du projet").fill(name);
  await page.getByPlaceholder("Commune").fill(commune);
  await page.getByRole("button", { name: "Créer", exact: true }).click();
  // Lands in the dual-nav workspace.
  await expect(page.getByText("Parcours SIA du projet")).toBeVisible();
}

test("create project → empty Terrain (honest, not a fixture)", async ({ page }) => {
  await register(page, "Crea Atelier", "crea@test.ch");
  await createProject(page, "Villa Test", "Genève");
  await page.locator(".ws__side").getByRole("button", { name: /Terrain/ }).click();
  await expect(page.getByText(/Aucune parcelle analysée/)).toBeVisible();
});

test("permit: submitting a piece flips it to present", async ({ page }) => {
  await register(page, "Permit Atelier", "permit@test.ch");
  await createProject(page, "Permit Proj", "Lausanne");
  await page.locator(".ws__side").getByRole("button", { name: /Dossier de permis/ }).click();
  // empty project: nothing provided yet
  await expect(page.getByRole("button", { name: "Retirer" })).toHaveCount(0);
  await page.getByRole("button", { name: "Fournir" }).first().click();
  await expect(page.getByRole("button", { name: "Retirer" })).toHaveCount(1);
});

test("team: an owner can invite a member", async ({ page }) => {
  await register(page, "Team Atelier", "team@test.ch");
  // Team management lives on the project workspace (Équipe task nav).
  await page.getByRole("button", { name: /Place de la Palud/ }).click();
  await page.locator(".ws__side").getByRole("button", { name: /Équipe/ }).click();
  await expect(page.getByRole("heading", { name: /Équipe/ })).toBeVisible();
  await page.getByRole("button", { name: /Inviter un collaborateur/ }).click();
  await page.getByPlaceholder("e-mail du collaborateur").fill("member@test.ch");
  await page.getByRole("button", { name: "Inviter" }).click();
  await expect(page.getByText("member@test.ch").first()).toBeVisible();
  await expect(page.getByText(/Membre ajouté/)).toBeVisible();
});

test("home search: unsupported commune → honest dossier, no fabricated data", async ({ page }) => {
  await register(page, "Search Atelier", "search@test.ch");
  await page.getByPlaceholder(/Analyser une parcelle/).fill("Fontainemelon, bien-fonds 904");
  await page.getByRole("button", { name: "Analyser" }).click();
  // a real dossier is created for the searched parcel (not the Lausanne demo)
  await expect(page.locator(".psw .nm")).toHaveText("Fontainemelon, bien-fonds 904");
  // honest: commune not covered + no fabricated constraints
  await expect(page.getByText(/pas encore prise en charge/).first()).toBeVisible();
  await expect(page.getByText(/Aucune parcelle analysée/)).toBeVisible();
});
