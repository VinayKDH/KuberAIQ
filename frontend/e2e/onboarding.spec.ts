import { expect, test } from "@playwright/test";
import {
  E2E_COMPANY_NAME_PREFIX,
  ONBOARDING_COPY,
  SUBSCRIPTION_PAGE,
} from "../src/lib/constants";
import { acceptTermsAndMockLogin, uniqueE2eEmail, uniqueGstin } from "./helpers";

test.describe("new user subscribe → onboard flow", () => {
  test("mock login → subscribe → onboarding step 1 → dashboard", async ({ page }) => {
    const email = uniqueE2eEmail();
    const gstin = uniqueGstin();

    await acceptTermsAndMockLogin(page, email);
    await expect(page).toHaveURL(/\/subscribe/);

    await page.getByRole("button", { name: SUBSCRIPTION_PAGE.MOCK_PAY_CTA }).click();
    await expect(page).toHaveURL(/\/onboarding/, { timeout: 15_000 });

    await page.getByLabel("Legal name").fill(`${E2E_COMPANY_NAME_PREFIX} ${Date.now()}`);
    await page.getByLabel("GSTIN").fill(gstin);
    await page.getByLabel("Business address").fill("42 Test Lane, Bengaluru, Karnataka");
    await page.getByRole("button", { name: ONBOARDING_COPY.CONTINUE }).click();

    await expect(page.getByText(ONBOARDING_COPY.STEP_COMPLIANCE)).toBeVisible();
    await page.getByRole("button", { name: ONBOARDING_COPY.SKIP }).first().click();

    await expect(page.getByText(ONBOARDING_COPY.STEP_PAYMENTS)).toBeVisible();
    await page.getByRole("button", { name: ONBOARDING_COPY.SKIP }).first().click();

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  });
});
