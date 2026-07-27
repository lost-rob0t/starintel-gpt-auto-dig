import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e-auto-dig",
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://127.0.0.1:4174",
    trace: "on-first-retry"
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ],
  webServer: {
    command: "python3 -m http.server 4174 --directory ../site",
    url: "http://127.0.0.1:4174/quasar/index.html",
    reuseExistingServer: !process.env.CI
  }
});
