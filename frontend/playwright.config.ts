/**
 * E2E tests — run with backend + frontend up and mock auth/billing enabled:
 *   Backend: USE_MOCK_AUTH=true USE_MOCK_BILLING=true uvicorn app.main:app --port 8000
 *   Frontend: NEXT_PUBLIC_USE_MOCK_AUTH=true NEXT_PUBLIC_USE_MOCK_BILLING=true npm run dev
 *   Tests:    cd frontend && npm run test:e2e
 */
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: "list",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
