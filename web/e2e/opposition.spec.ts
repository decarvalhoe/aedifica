import { test, expect, type Page } from "@playwright/test";

// W21-4 — the opposition surface leads with TARGETED points (each anchored to
// a verifiable dossier fact) instead of the generic score Etienne dismissed.
// The view payload is mocked: the renderer contract is the unit under test;
// the mechanical derivation is covered by tests/product/test_opposition_points.

const WITH_POINTS = {
  opposition: {
    overall: "eleve", score: 62, claims_prediction: false, data_basis: "project",
    disclaimer: "Radar générique sur signaux de contexte.",
    signals: [{ ground: "neighbor", category: "context", level: "medium", basis: "Mitoyenneté dense au sud." }],
    points: [
      {
        kind: "conflit_avere", focus: "Friction avérée · Indice d'utilisation du sol",
        why: "Deux bases se contredisent sur ce point — un opposant l'exploitera tel quel à l'enquête.",
        action: "Arbitrer le conflit et tracer la décision (Mémoire).",
        basis: [{ kind: "claim", ref: "c-conf", title: "Indice d'utilisation du sol", state: "conflict", sources: ["rdppf"] }],
      },
      {
        kind: "base_non_sourcee", focus: "Point sensible voisinage non sourcé · Hauteur maximale au faîte",
        why: "Valeur non adossée à une source officielle sur un motif d'opposition classique — attaquable à l'enquête.",
        action: "Vérifier l'art. 12 RPGA",
        basis: [{ kind: "claim", ref: "c-haut", title: "Hauteur maximale au faîte", state: "unknown", sources: [] }],
      },
    ],
    doc_basis: { canonical: 1, indicative: 0, refused: 1, pending: 2 },
  },
};

const EMPTY = {
  opposition: {
    overall: null, score: null, claims_prediction: false, data_basis: "empty",
    disclaimer: "Aucune analyse de parcelle pour ce projet.", signals: [],
    points: [], doc_basis: { canonical: 0, indicative: 0, refused: 0, pending: 0 },
  },
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

test("opposition: les points ciblés mènent, le radar générique est en annexe", async ({ page }) => {
  const run = Date.now();
  await page.route("**/api/projects/*/opposition", (route) => route.fulfill({ json: WITH_POINTS }));
  await register(page, "Opp Atelier", `opp-${run}@test.ch`);
  await createProject(page, "Points Cibles", "Lausanne");
  await page.locator(".ws__side").getByRole("button", { name: /Risque d'opposition/ }).click();

  const points = page.getByTestId("opposition-points");
  await expect(points).toBeVisible();
  await expect(points).toContainText("À désamorcer · 2 point(s) ciblé(s)");
  await expect(points).toContainText("Friction avérée · Indice d'utilisation du sol");
  await expect(points).toContainText("Point sensible voisinage non sourcé · Hauteur maximale au faîte");
  await expect(points).toContainText("Vérifier l'art. 12 RPGA");
  await expect(points).toContainText("base : claim · c-conf");
  // Base documentaire chips + the demoted generic radar.
  await expect(page.getByText("Canonique · 1")).toBeVisible();
  await expect(page.getByText("Refusé · 1")).toBeVisible();
  await expect(page.getByText(/Annexe — radar générique/)).toBeVisible();
  await expect(page.getByText(/niveau eleve/)).toBeVisible();
});

test("opposition: dossier vide → état vide explicite, rien d'inventé", async ({ page }) => {
  const run = Date.now();
  await page.route("**/api/projects/*/opposition", (route) => route.fulfill({ json: EMPTY }));
  await register(page, "Opp Vide", `opp-vide-${run}@test.ch`);
  await createProject(page, "Dossier Vide", "Lausanne");
  await page.locator(".ws__side").getByRole("button", { name: /Risque d'opposition/ }).click();
  await expect(page.getByText("Pas encore de point d'attention")).toBeVisible();
  await expect(page.getByText("Aucune analyse n'est inventée", { exact: false })).toBeVisible();
});
