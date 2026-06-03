import { defineConfig } from "@playwright/test";

// E2E smoke for the product app. Servers (API on :8090, web on :3100) are started
// by CI / the developer before `npm run e2e`; this config only drives the browser.
export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  retries: process.env.CI ? 1 : 0,
  reporter: "list",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3100",
    trace: "on-first-retry",
  },
});
