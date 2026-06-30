import { API_PATHS, getOAuthRedirectUri, OAUTH_PROVIDER_MICROSOFT } from "@/lib/constants";
import { apiClient } from "@/lib/api-client";
import { storeSession, type AuthTokens } from "@/lib/auth";
import { isGoogleAuthConfigured } from "@/lib/google";
import {
  clearOAuthSession,
  createPkceChallenge,
  getPkceVerifier,
  setOAuthProvider,
} from "@/lib/oauth-pkce";

const ENTRA_CLIENT_ID = process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID ?? "";
const ENTRA_TENANT_ID = process.env.NEXT_PUBLIC_ENTRA_TENANT_ID ?? "common";

export function isEntraAuthConfigured(): boolean {
  return Boolean(ENTRA_CLIENT_ID);
}

export function isOAuthConfigured(): boolean {
  return isEntraAuthConfigured() || isGoogleAuthConfigured();
}

export function isMockAuthEnabled(): boolean {
  return process.env.NEXT_PUBLIC_USE_MOCK_AUTH !== "false";
}

export async function startEntraLogin(): Promise<void> {
  if (!ENTRA_CLIENT_ID) {
    throw new Error("Microsoft sign-in is not configured");
  }
  const { challenge } = await createPkceChallenge();
  setOAuthProvider(OAUTH_PROVIDER_MICROSOFT);
  const params = new URLSearchParams({
    client_id: ENTRA_CLIENT_ID,
    response_type: "code",
    redirect_uri: getOAuthRedirectUri(),
    response_mode: "query",
    scope: "openid profile email offline_access",
    code_challenge: challenge,
    code_challenge_method: "S256",
  });
  window.location.href = `https://login.microsoftonline.com/${ENTRA_TENANT_ID}/oauth2/v2.0/authorize?${params}`;
}

export async function completeEntraLogin(code: string): Promise<AuthTokens> {
  const codeVerifier = getPkceVerifier();
  const tokens = await apiClient<AuthTokens>(API_PATHS.AUTH_CALLBACK, {
    method: "POST",
    body: {
      code,
      code_verifier: codeVerifier,
      redirect_uri: getOAuthRedirectUri(),
    },
  });
  clearOAuthSession();
  storeSession(tokens);
  return tokens;
}
