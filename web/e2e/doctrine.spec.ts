import { test, expect, type Page } from "@playwright/test";

// W21-1 — the doctrine Q&A surface over the NOMOS knowledge layer (the first
// dedicated UI of the W19/W20 work). CI starts the API with
// AEDIFICA_NOMOS_ENABLED=1, so /api/health reports features.nomos=true and the
// panel is live. The flag-OFF case is exercised by mocking /api/health (the
// server-wide flag can't be flipped per test); the flag-OFF API contract (403
// NOMOS_DISABLED) stays covered by tests/product.

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

async function openCopilote(page: Page) {
  await page.locator(".ws__side").getByRole("button", { name: /Copilote/ }).click();
  await expect(page.getByRole("heading", { name: "Copilote IA" })).toBeVisible();
}

test("doctrine: empty corpus → explicit abstention (cite-or-abstain)", async ({ page }) => {
  await register(page, "Doctrine Atelier", "doctrine@test.ch");
  await createProject(page, "Doctrine Proj", "Lausanne");
  await openCopilote(page);
  const panel = page.getByTestId("doctrine-qa");
  await expect(panel).toBeVisible();
  await panel.getByPlaceholder(/hauteur maximale/).fill("Quelle hauteur maximale en zone village ?");
  await panel.getByRole("button", { name: /Interroger/ }).click();
  // No corpus imported in this atelier → the honest answer is the abstention.
  await expect(page.getByTestId("doctrine-abstention")).toBeVisible();
  await expect(page.getByTestId("doctrine-abstention")).toContainText("décision humaine requise");
});

test("doctrine: cited answer renders sources, spans and trust tiers", async ({ page }) => {
  // Deterministic citations without seeding a whole corpus: mock the endpoint.
  // The renderer is the unit under test here; the real retrieval round-trip is
  // covered by the abstention test above + tests/product (seam e2e).
  await page.route("**/api/projects/*/copilote/nomos", (route) =>
    route.fulfill({
      json: {
        answer: "La hauteur maximale est de 9 m au faîte.",
        structured_facts: [
          { chunk_id: "c1", scope: "jurisdiction", text: "La hauteur maximale est de 9 m au faîte.", trust_tier: "unverified", provenance: "official", facets: {} },
        ],
        citations: [
          { chunk_id: "c1", scope: "jurisdiction", source_path: "reglements/lausanne/pga.md", source_hash: "sha256:abc", span: { start_line: 12, end_line: 18 }, trust_tier: "unverified", provenance: "official" },
        ],
        requires_human_decision: true,
      },
    })
  );
  await register(page, "Doctrine Cite", "doctrine-cite@test.ch");
  await createProject(page, "Doctrine Cite", "Lausanne");
  await openCopilote(page);
  const panel = page.getByTestId("doctrine-qa");
  await panel.getByPlaceholder(/hauteur maximale/).fill("Hauteur max au faîte ?");
  await panel.getByRole("button", { name: /Interroger/ }).click();
  const answer = page.getByTestId("doctrine-answer");
  await expect(answer).toContainText("La hauteur maximale est de 9 m au faîte.");
  await expect(answer).toContainText("reglements/lausanne/pga.md");
  await expect(answer).toContainText("l. 12–18");
  // Honest trust display: unverified tier + official provenance + human gate.
  await expect(answer).toContainText("Non vérifié");
  await expect(answer).toContainText("Officiel");
  await expect(answer).toContainText("la décision reste humaine");
});

test("doctrine: flag OFF → the surface does not exist", async ({ page }) => {
  await page.route("**/api/health", (route) =>
    route.fulfill({ json: { status: "ok", version: "0.1.0", env: "test", features: { nomos: false } } })
  );
  await register(page, "Doctrine Off", "doctrine-off@test.ch");
  await createProject(page, "Doctrine Off", "Lausanne");
  await openCopilote(page);
  // The Archicad action loop is still there; the doctrine panel is not.
  await expect(page.getByRole("button", { name: "Demander un aperçu" })).toBeVisible();
  await expect(page.getByTestId("doctrine-qa")).toHaveCount(0);
});
