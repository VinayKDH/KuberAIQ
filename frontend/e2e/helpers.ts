const GSTIN_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";

function gstinChecksum(first14: string): string {
  const code: Record<string, number> = {};
  for (let i = 0; i < GSTIN_ALPHABET.length; i += 1) {
    code[GSTIN_ALPHABET[i]!] = i;
  }
  let factor = 2;
  let total = 0;
  const base = GSTIN_ALPHABET.length;
  for (let i = first14.length - 1; i >= 0; i -= 1) {
    let digit = code[first14[i]!]! * factor;
    digit = Math.floor(digit / base) + (digit % base);
    total += digit;
    factor = factor === 2 ? 1 : 2;
  }
  const checkVal = (base - (total % base)) % base;
  return GSTIN_ALPHABET[checkVal]!;
}

export function uniqueE2eEmail(): string {
  return `e2e+${Date.now()}@test.kuberaiq.com`;
}

export function uniqueGstin(seed = Date.now()): string {
  const digits = String(seed % 10000).padStart(4, "0");
  const first14 = `29AAAAA${digits}A1Z`;
  return first14 + gstinChecksum(first14);
}

export async function agreeToTerms(page: import("@playwright/test").Page): Promise<void> {
  await page.getByRole("checkbox").check();
}

export async function acceptTermsAndMockLogin(
  page: import("@playwright/test").Page,
  email: string,
): Promise<void> {
  await page.goto("/login");
  await agreeToTerms(page);
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Sign in" }).click();
}
