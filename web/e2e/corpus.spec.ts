import { test, expect, type Page } from "@playwright/test";
import * as path from "path";

// W21-2 — the jurisdictional corpus card + NOMOS bundle import UI.
// The crown test replays the whole W20 seam THROUGH THE BROWSER: import the
// UNMODIFIED golden emitted bundle (74 nodes / 10 sources) via the file input,
// watch the corpus counters move 0 -> 74, then get a cited doctrine answer in
// Copilote from that very corpus. Unique commune per run (the importer scopes
// feeds on the project jurisdiction and feed versions are immutable), so the
// spec is repeatable against a persistent local DB too.

const GOLDEN = path.resolve(__dirname, "..", "..", "tests", "fixtures", "nomos", "canonical-knowledge-bundle.emitted.json");

async function register(page: Page, org: string, email: string) {
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Créer un atelier" }).click();
  await page.getByPlaceholder("Atelier Martin").fill(org);
  await page.getByPlaceholder("vous@atelier.ch").fill(email);
  await page.getByPlaceholder("6 caractères minimum").fill("motdepasse1");
  await page.getByRole("button", { name: "Créer l'atelier" }).click();
  await expect(page.getByText("Créer votre premier projet")).toBeVisible();
}

// Unknown commune + explicit canton (the resolver's honest "Commune inconnue"
// branch) — gives us a unique jurisdiction per run.
async function createProject(page: Page, name: string, commune: string, canton: string) {
  await page.locator(".psw-btn").click();
  await page.getByRole("button", { name: /Nouveau projet/ }).click();
  await page.getByPlaceholder("Nom du projet").fill(name);
  const communeField = page.getByPlaceholder("Commune");
  await communeField.fill("");
  await communeField.fill(commune);
  await expect(page.getByText(/Commune inconnue|Plusieurs cantons/)).toBeVisible();
  await page.locator(".psw-canton select").selectOption(canton);
  const create = page.getByRole("button", { name: "Créer", exact: true });
  await expect(create).toBeEnabled();
  await create.click();
  await expect(page.locator(".psw-cur .nm")).toHaveText(name);
}

test("corpus: golden bundle imported through the UI → counters move → doctrine cites it", async ({ page }) => {
  const run = Date.now();
  await register(page, "Corpus Atelier", `corpus-${run}@test.ch`);
  await createProject(page, "Corpus Golden", `E2E-Corpus-${run}`, "VD");

  await page.locator(".ws__side").getByRole("button", { name: /Documents & sources/ }).click();
  const card = page.getByTestId("corpus-nomos");
  await expect(card).toBeVisible();
  // Honest empty state: zero everywhere + the abstention warning.
  await expect(card.getByTestId("corpus-counts")).toContainText("Juridiction : 0");
  await expect(card.getByText(/Corpus vide/)).toBeVisible();

  // Import the UNMODIFIED emitter output through the real file input.
  await card.locator('input[type="file"]').setInputFiles(GOLDEN);
  await card.getByRole("button", { name: "Importer le bundle" }).click();
  await expect(card.getByTestId("corpus-import-ok")).toContainText("74 chunks", { timeout: 30_000 });
  await expect(card.getByTestId("corpus-counts")).toContainText("Juridiction : 74");
  await expect(card.getByText(/Actif/).first()).toBeVisible();

  // The seam, through the browser: the freshly imported corpus is citable.
  await page.locator(".ws__side").getByRole("button", { name: /Copilote/ }).click();
  const panel = page.getByTestId("doctrine-qa");
  await expect(panel).toBeVisible();
  await panel.getByPlaceholder(/hauteur maximale/).fill("Which auditable fields does the evaluation record store?");
  await panel.getByRole("button", { name: /Interroger/ }).click();
  const answer = page.getByTestId("doctrine-answer");
  await expect(answer).toBeVisible({ timeout: 15_000 });
  // Golden corpus is all-unverified: cited but the decision stays human.
  await expect(answer.getByText("Non vérifié").first()).toBeVisible();
  await expect(answer).toContainText("la décision reste humaine");
});

test("corpus: corrupted bundle → readable 422, zero rows leaked", async ({ page }) => {
  const run = Date.now();
  await register(page, "Corpus Bad", `corpus-bad-${run}@test.ch`);
  await createProject(page, "Corpus Bad", `E2E-Bad-${run}`, "VD");

  await page.locator(".ws__side").getByRole("button", { name: /Documents & sources/ }).click();
  const card = page.getByTestId("corpus-nomos");
  await expect(card).toBeVisible();

  // schema_version stripped — the schema gate must answer in clear text.
  await card.locator('input[type="file"]').setInputFiles({
    name: "forged.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify({ bundle_id: "forged", feeds: [] })),
  });
  await card.getByRole("button", { name: "Importer le bundle" }).click();
  await expect(card.getByTestId("corpus-import-err")).toContainText(/schema_version/i);
  // Nothing leaked: the corpus stays empty.
  await expect(card.getByTestId("corpus-counts")).toContainText("Juridiction : 0");
});
