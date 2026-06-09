"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { OAUTH_PROVIDER_GOOGLE, OAUTH_PROVIDER_MICROSOFT } from "@/lib/constants";
import { useCanonicalOriginRedirect } from "@/hooks/use-canonical-origin";
import { postLoginRoute } from "@/lib/session-routing";
import { completeEntraLogin, isEntraAuthConfigured } from "@/lib/entra";
import { completeGoogleLogin, isGoogleAuthConfigured } from "@/lib/google";
import { getOAuthProvider } from "@/lib/oauth-pkce";

function resolveOAuthProvider(): typeof OAUTH_PROVIDER_GOOGLE | typeof OAUTH_PROVIDER_MICROSOFT {
  const stored = getOAuthProvider();
  if (stored) return stored;
  if (isGoogleAuthConfigured()) return OAUTH_PROVIDER_GOOGLE;
  return OAUTH_PROVIDER_MICROSOFT;
}

function AuthCallbackContent() {
  const router = useRouter();
  const params = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const redirecting = useCanonicalOriginRedirect();

  useEffect(() => {
    if (redirecting) return;
    const code = params.get("code");
    const oauthError = params.get("error_description") ?? params.get("error");
    if (oauthError) {
      setError(oauthError);
      return;
    }
    if (!code) {
      setError("Authorization code missing");
      return;
    }

    const provider = resolveOAuthProvider();
    if (provider === OAUTH_PROVIDER_MICROSOFT && !isEntraAuthConfigured()) {
      setError("Microsoft sign-in is not configured");
      return;
    }
    const completeLogin =
      provider === OAUTH_PROVIDER_GOOGLE ? completeGoogleLogin : completeEntraLogin;

    completeLogin(code)
      .then((tokens) => {
        router.replace(postLoginRoute(tokens));
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Sign-in failed");
      });
  }, [params, redirecting, router]);

  return (
    <CardContent>
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : (
        <div className="flex justify-center py-6">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      )}
    </CardContent>
  );
}

export default function AuthCallbackPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Signing you in…</CardTitle>
          <CardDescription>Completing secure authentication</CardDescription>
        </CardHeader>
        <Suspense
          fallback={
            <CardContent>
              <div className="flex justify-center py-6">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
              </div>
            </CardContent>
          }
        >
          <AuthCallbackContent />
        </Suspense>
      </Card>
    </div>
  );
}
