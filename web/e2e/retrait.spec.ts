import { test, expect, type Page } from "@playwright/test";

// W23-5b — retrait d'un squelette de projet AU NAVIGATEUR : un projet créé
// par erreur (le cas « Neuchâtel (VD) » historique) se retire depuis Réglages
// tant qu'il est vide ; dès qu'il porte du travail, le refus NOMME ce qui a
// été trouvé. Miroir produit du retrait des demandes communales (W22-2b).

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

test("retrait: un squelette se retire depuis Réglages, l'atelier retombe sur l'état vide", async ({ page }) => {
  const run = Date.now();
  await register(page, "Atelier Retrait", `retrait-${run}@test.ch`);
  await createProject(page, "Erreur Canton", "Lausanne");

  await page.locator(".ws__side").getByRole("button", { name: /Réglages/ }).click();
  await expect(page.getByRole("heading", { name: "Retirer ce projet" })).toBeVisible();
  await page.getByRole("button", { name: /Retirer « Erreur Canton »…/ }).click();
  // Étape de confirmation explicite — rien ne part sur un seul clic.
  await expect(page.getByText(/Confirmer le retrait de « Erreur Canton »/)).toBeVisible();
  await page.getByRole("button", { name: "Retirer définitivement" }).click();

  // Le projet a disparu : le sélecteur retombe sur « Aucun projet ».
  await expect(page.locator(".psw-cur .nm")).toHaveText("Aucun projet");
});

test("retrait: un projet qui porte du travail est refusé, le refus nomme ce qu'il a trouvé", async ({ page }) => {
  const run = Date.now();
  await register(page, "Atelier Immortel", `immortel-${run}@test.ch`);
  await createProject(page, "Projet Travaillé", "Lausanne");

  // Une seule pièce fournie au dossier de permis = du travail réel.
  await page.locator(".ws__side").getByRole("button", { name: /Dossier de permis/ }).click();
  await page.getByRole("button", { name: "Fournir" }).first().click();
  await expect(page.getByRole("button", { name: "Retirer", exact: true }).first()).toBeVisible();

  await page.locator(".ws__side").getByRole("button", { name: /Réglages/ }).click();
  await page.getByRole("button", { name: /Retirer « Projet Travaillé »…/ }).click();
  await page.getByRole("button", { name: "Retirer définitivement" }).click();
  // Refus 409 : le travail trouvé est NOMMÉ, le projet survit.
  await expect(page.getByText(/porte du travail/)).toBeVisible();
  await expect(page.getByText(/dossier permis/)).toBeVisible();
  await expect(page.locator(".psw-cur .nm")).toHaveText("Projet Travaillé");
});
