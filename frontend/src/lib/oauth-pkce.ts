import {
  OAUTH_COOKIE_DOMAIN,
  OAUTH_PKCE_TTL_SECONDS,
  OAUTH_PROVIDER_GOOGLE,
  OAUTH_PROVIDER_MICROSOFT,
  PUBLIC_WEB_URL,
  ROUTES,
} from "@/lib/constants";

export const PKCE_VERIFIER_KEY = "kuberaiq_pkce_verifier";
export const OAUTH_PROVIDER_KEY = "kuberaiq_oauth_provider";

export function randomString(length: number): string {
  const bytes = new Uint8Array(length);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("").slice(0, length);
}

export async function sha256Base64Url(value: string): Promise<string> {
  const data = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", data);
  const bytes = new Uint8Array(digest);
  let binary = "";
  bytes.forEach((b) => {
    binary += String.fromCharCode(b);
  });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function writeOAuthCookie(key: string, value: string): void {
  if (typeof document === "undefined") return;
  const domain = OAUTH_COOKIE_DOMAIN ? `; domain=${OAUTH_COOKIE_DOMAIN}` : "";
  document.cookie = `${key}=${encodeURIComponent(value)}; path=/; max-age=${OAUTH_PKCE_TTL_SECONDS}; SameSite=Lax; Secure${domain}`;
}

function readOAuthCookie(key: string): string | null {
  if (typeof document === "undefined") return null;
  const prefix = `${key}=`;
  for (const part of document.cookie.split(";")) {
    const trimmed = part.trim();
    if (trimmed.startsWith(prefix)) {
      return decodeURIComponent(trimmed.slice(prefix.length));
    }
  }
  return null;
}

function deleteOAuthCookie(key: string): void {
  if (typeof document === "undefined") return;
  const domain = OAUTH_COOKIE_DOMAIN ? `; domain=${OAUTH_COOKIE_DOMAIN}` : "";
  document.cookie = `${key}=; path=/; max-age=0; Secure${domain}`;
}

function storeOAuthValue(key: string, value: string): void {
  sessionStorage.setItem(key, value);
  writeOAuthCookie(key, value);
}

function readOAuthValue(key: string): string | null {
  return sessionStorage.getItem(key) ?? readOAuthCookie(key);
}

function removeOAuthValue(key: string): void {
  sessionStorage.removeItem(key);
  deleteOAuthCookie(key);
}

export async function createPkceChallenge(): Promise<{ verifier: string; challenge: string }> {
  const verifier = randomString(64);
  const challenge = await sha256Base64Url(verifier);
  storeOAuthValue(PKCE_VERIFIER_KEY, verifier);
  return { verifier, challenge };
}

export function getPkceVerifier(): string {
  const codeVerifier = readOAuthValue(PKCE_VERIFIER_KEY);
  if (!codeVerifier) {
    throw new Error("Missing PKCE verifier — restart sign-in");
  }
  return codeVerifier;
}

export function clearOAuthSession(): void {
  removeOAuthValue(PKCE_VERIFIER_KEY);
  removeOAuthValue(OAUTH_PROVIDER_KEY);
}

export function setOAuthProvider(
  provider: typeof OAUTH_PROVIDER_GOOGLE | typeof OAUTH_PROVIDER_MICROSOFT,
): void {
  storeOAuthValue(OAUTH_PROVIDER_KEY, provider);
}

export function getOAuthProvider(): typeof OAUTH_PROVIDER_GOOGLE | typeof OAUTH_PROVIDER_MICROSOFT | null {
  const provider = readOAuthValue(OAUTH_PROVIDER_KEY);
  if (provider === OAUTH_PROVIDER_GOOGLE || provider === OAUTH_PROVIDER_MICROSOFT) {
    return provider;
  }
  return null;
}

export function getOAuthRedirectUri(): string {
  if (process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI) {
    return process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI;
  }
  if (process.env.NEXT_PUBLIC_ENTRA_REDIRECT_URI) {
    return process.env.NEXT_PUBLIC_ENTRA_REDIRECT_URI;
  }
  if (typeof window !== "undefined") {
    return `${window.location.origin}${ROUTES.AUTH_CALLBACK}`;
  }
  return `${PUBLIC_WEB_URL}${ROUTES.AUTH_CALLBACK}`;
}
