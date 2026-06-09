import { test, expect, type Page } from "@playwright/test";

// W17: register lands directly in the workspace, but new ateliers are empty.
// The first stable post-registration state is the first-project placeholder.
async function register(page: Page, org: string, email: string) {
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Créer un atelier" }).click();
  await page.getByPlaceholder("Atelier Martin").fill(org);
  await page.getByPlaceholder("vous@atelier.ch").fill(email);
  await page.getByPlaceholder("6 caractères minimum").fill("motdepasse1");
  await page.getByRole("button", { name: "Créer l'atelier" }).click();
  await expect(page.getByText("Créer votre premier projet")).toBeVisible();
  await expect(page.locator(".psw-cur .nm")).toHaveText("Aucun projet");
}

// W13: project creation now lives in the sidebar ProjectSwitcher popover.
// Open the switcher (button-card at the top of the sidebar), click
// "+ Nouveau projet", fill the inline form, submit. The new project becomes
// active and the workspace re-renders for it.
async function createProject(page: Page, name: string, commune: string, canton?: string) {
  await page.locator(".psw-btn").click();
  await page.getByRole("button", { name: /Nouveau projet/ }).click();
  await page.getByPlaceholder("Nom du projet").fill(name);
  // The popover form already pre-fills "Lausanne" — override:
  const communeField = page.getByPlaceholder("Commune");
  await communeField.fill("");
  await communeField.fill(commune);
  if (canton) {
    await expect(page.getByText(/Commune inconnue|Plusieurs cantons/)).toBeVisible();
    await page.locator(".psw-canton select").selectOption(canton);
  } else {
    await expect(page.getByText(/Canton détecté/)).toBeVisible();
  }
  const create = page.getByRole("button", { name: "Créer", exact: true });
  await expect(create).toBeEnabled();
  await create.click();
  // The active project flips to the new one; the switcher shows its name.
  await expect(page.locator(".psw-cur .nm")).toHaveText(name);
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
  // W13: Équipe lives in the "Atelier · global" group; it stays accessible
  // regardless of the active project — no need to bounce through a project
  // selector card.
  await page.locator(".ws__side").getByRole("button", { name: /Équipe/ }).click();
  await expect(page.getByRole("heading", { name: /Équipe/ })).toBeVisible();
  await page.getByRole("button", { name: /Inviter un collaborateur/ }).click();
  await page.getByPlaceholder("e-mail du collaborateur").fill("member@test.ch");
  await page.getByRole("button", { name: "Inviter" }).click();
  await expect(page.getByText("member@test.ch").first()).toBeVisible();
  await expect(page.getByText(/Membre ajouté/)).toBeVisible();
});

// W13: the standalone home parcel-search was removed (it duplicated the
// Terrain & zonage flow). The equivalent honesty guarantee — "unsupported
// commune → no fabricated data" — is now exercised inside Terrain itself.
test("unsupported commune → honest dossier, no fabricated data", async ({ page }) => {
  await register(page, "Search Atelier", "search@test.ch");
  await createProject(page, "Fontaine 904", "Glubzy-sur-Mer", "NE");
  await page.locator(".ws__side").getByRole("button", { name: /Terrain/ }).click();
  // Empty Terrain on the freshly-created project: no claims, banner about
  // commune not supported, NEVER fabricated.
  await expect(page.getByText(/Aucune parcelle analysée/)).toBeVisible();
  // W14.A: the banner is now the honest IngestionPanel ("pas encore
  // exploitable" + required-inputs list + "Aedifica ne fabrique pas de zones").
  await expect(page.getByText(/pas encore exploitable/).first()).toBeVisible();
  await expect(page.getByText(/Aedifica ne fabrique pas de zones/).first()).toBeVisible();
});
