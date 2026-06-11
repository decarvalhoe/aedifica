import { test, expect, type Page } from "@playwright/test";

// W21-3 — Terrain filter chips over the TrustMeta axes (trust tier ×
// provenance): Etienne's « trier · retrouver » applied to the parcel claims.
// Claims are mocked (the renderer + filter logic is the unit under test);
// real claim production stays covered by tests/product + the intake e2e.

const CLAIMS = {
  claims: [
    { claim_id: "c1", state: "sourced", title: "Hauteur max au faîte", value: "9 m", trust_tier: "certified", provenance: "official" },
    { claim_id: "c2", state: "computed", title: "IUS pratiqué dans le quartier", value: "0.6", trust_tier: "indicative", provenance: "metier_bible" },
    { claim_id: "c3", state: "assumption", title: "Servitude de passage présumée", value: "à confirmer", trust_tier: "unverified", provenance: "user_promoted" },
  ],
};

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

test("terrain: les chips tier/provenance trient les claims, état vide honnête", async ({ page }) => {
  const run = Date.now();
  await page.route("**/api/projects/*/claims", (route) => route.fulfill({ json: CLAIMS }));
  await register(page, "Atelier Filtres", `terrain-${run}@test.ch`);
  await createProject(page, "Filtres Claims", "Lausanne");
  await page.locator(".ws__side").getByRole("button", { name: /Terrain & zonage/ }).click();

  // All three claims + the filter strip with per-axis counters.
  const strip = page.getByTestId("terrain-filtres");
  await expect(strip).toBeVisible();
  await expect(strip.getByRole("button", { name: "Tout · 3" })).toBeVisible();
  await expect(page.getByText("Hauteur max au faîte")).toBeVisible();
  await expect(page.getByText("IUS pratiqué dans le quartier")).toBeVisible();
  await expect(page.getByText("Servitude de passage présumée")).toBeVisible();

  // Tier filter: only the certified claim survives.
  await strip.getByRole("button", { name: "Certifié · 1" }).click();
  await expect(page.getByText("Hauteur max au faîte")).toBeVisible();
  await expect(page.getByText("IUS pratiqué dans le quartier")).toHaveCount(0);
  await expect(page.getByText("Servitude de passage présumée")).toHaveCount(0);

  // Impossible combination (certified × promu atelier) → honest empty state.
  await strip.getByRole("button", { name: "Promu atelier · 1" }).click();
  await expect(page.getByTestId("terrain-filtre-vide")).toBeVisible();
  await expect(page.getByText("Rien sous ce filtre")).toBeVisible();

  // Reset: everything comes back.
  await strip.getByRole("button", { name: "Tout · 3" }).click();
  await expect(page.getByText("Servitude de passage présumée")).toBeVisible();
});
