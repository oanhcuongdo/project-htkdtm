import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  reporter: "line",
  outputDir: "../../.runtime/playwright-results",
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://127.0.0.1:5173",
    channel: process.env.E2E_BROWSER_CHANNEL,
    headless: true,
    screenshot: "only-on-failure",
  },
});
