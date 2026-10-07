import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  timeout: 90000,
  workers: 1,
  use: {
    baseURL: "http://localhost:5173",
    channel: "chrome",
    headless: true,
    viewport: { width: 1440, height: 1000 },
    screenshot: "only-on-failure",
  },
  reporter: [["list"], ["html", { open: "never" }]],
});
