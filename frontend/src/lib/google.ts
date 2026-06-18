import {
  API_PATHS,
  GOOGLE_OAUTH_SCOPES,
  OAUTH_PROVIDER_GOOGLE,
  PUBLIC_WEB_URL,
  ROUTES,
  usesSameOriginApi,
} from "@/lib/constants";
import { apiClient } from "@/lib/api-client";
import { storeSession, type AuthTokens } from "@/lib/auth";
import {
  clearOAuthSession,
  createPkceChallenge,
  getPkceVerifier,
  setOAuthProvider,
} from "@/lib/oauth-pkce";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "";

function getGoogleRedirectUri(): string {
  if (typeof window !== "undefined" && usesSameOriginApi(window.location.hostname)) {
    return `${window.location.origin}${ROUTES.AUTH_CALLBACK}`;
  }
  return (
    process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI ||
    `${PUBLIC_WEB_URL}${ROUTES.AUTH_CALLBACK}`
  );
}

export function isGoogleAuthConfigured(): boolean {
  return Boolean(GOOGLE_CLIENT_ID);
}

export async function startGoogleLogin(): Promise<void> {
  if (!GOOGLE_CLIENT_ID) {
    throw new Error("Google sign-in is not configured");
  }
  const { challenge } = await createPkceChallenge();
  setOAuthProvider(OAUTH_PROVIDER_GOOGLE);
  const params = new URLSearchParams({
    client_id: GOOGLE_CLIENT_ID,
    response_type: "code",
    redirect_uri: getGoogleRedirectUri(),
    scope: GOOGLE_OAUTH_SCOPES,
    code_challenge: challenge,
    code_challenge_method: "S256",
    access_type: "online",
    prompt: "select_account",
  });
  window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
}

export async function completeGoogleLogin(code: string): Promise<AuthTokens> {
  const codeVerifier = getPkceVerifier();
  const tokens = await apiClient<AuthTokens>(API_PATHS.GOOGLE_CALLBACK, {
    method: "POST",
    body: {
      code,
      code_verifier: codeVerifier,
      redirect_uri: getGoogleRedirectUri(),
    },
  });
  clearOAuthSession();
  storeSession(tokens);
  return tokens;
}
