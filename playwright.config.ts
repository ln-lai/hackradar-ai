import { defineConfig, devices } from "@playwright/test";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

// Every run gets its own database and ports; never reuse a personal demo API.
const database = join(mkdtempSync(join(tmpdir(), "hackradar-e2e-")), "events.sqlite3");
const python = process.platform === "win32" ? ".venv/Scripts/python.exe" : ".venv/bin/python";

export default defineConfig({
  testDir: "./tests", fullyParallel: false, workers: 1,
  reporter: "list", timeout: 30_000,
  use: { baseURL: "http://127.0.0.1:3001", trace: "retain-on-failure", screenshot: "only-on-failure", ...devices["Desktop Chrome"],
    launchOptions: process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {} },
  webServer: [
    { command: `${python} -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001`, url: "http://127.0.0.1:8001/health", reuseExistingServer: false, env: { DATABASE_PATH: database, XAI_API_KEY: "", HACKRADAR_API_TOKEN: "" } },
    { command: "node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3001", url: "http://127.0.0.1:3001", reuseExistingServer: false, env: { BACKEND_URL: "http://127.0.0.1:8001", HACKRADAR_API_TOKEN: "" } },
  ],
});
