import { expect, test } from "@playwright/test";
import { DEMO_LOGIN_EMAIL } from "../src/lib/constants";
import { agreeToTerms } from "./helpers";

test("login page loads", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByText("KuberAIQ").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
});

test("mock login reaches dashboard", async ({ page }) => {
  await page.goto("/login");
  await agreeToTerms(page);
  await page.getByLabel("Email").fill(DEMO_LOGIN_EMAIL);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});

test("settings company tab loads", async ({ page }) => {
  await page.goto("/login");
  await agreeToTerms(page);
  await page.getByLabel("Email").fill(DEMO_LOGIN_EMAIL);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.goto("/settings");
  await expect(page.getByRole("tab", { name: "Company" })).toBeVisible();
});
