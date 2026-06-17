"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SiteFooter } from "@/components/marketing/site-footer";
import {
  API_PATHS,
  DEMO_LOGIN_EMAIL,
  DEMO_CA_LOGIN_EMAIL,
  LANDING_COPY,
  LEGAL_COPY,
  ROUTES,
} from "@/lib/constants";
import { apiClient } from "@/lib/api-client";
import { clearSession, isAuthenticated, storeSession, type AuthTokens } from "@/lib/auth";
import { isEntraAuthConfigured, isMockAuthEnabled, startEntraLogin } from "@/lib/entra";
import { postLoginRoute, type MeGate } from "@/lib/session-routing";
import { isGoogleAuthConfigured, startGoogleLogin } from "@/lib/google";
import { getPreferredLanguage, I18N_MESSAGES } from "@/lib/i18n";

export default function LoginPage() {
  const router = useRouter();
  const mockAuth = isMockAuthEnabled();
  const showMicrosoft = !mockAuth && isEntraAuthConfigured();
  const showGoogle = !mockAuth && isGoogleAuthConfigured();
  const showOAuth = showMicrosoft || showGoogle;
  const productionAuth = !mockAuth;
  const [email, setEmail] = useState(DEMO_LOGIN_EMAIL);
  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checkingSession, setCheckingSession] = useState(() => isAuthenticated());
  const [error, setError] = useState<string | null>(null);
  const lang = getPreferredLanguage();
  const i18n = I18N_MESSAGES[lang];

  useEffect(() => {
    if (!isAuthenticated()) {
      setCheckingSession(false);
      return;
    }

    apiClient<MeGate>(API_PATHS.ME)
      .then((me) => {
        router.replace(postLoginRoute(me));
      })
      .catch(() => {
        clearSession();
        setCheckingSession(false);
      });
  }, [router]);

  const ensureAgreed = () => {
    if (!agreed) {
      setError("Please accept the Terms and Privacy Policy to continue.");
      return false;
    }
    return true;
  };

  const handleMockSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ensureAgreed()) return;
    setError(null);
    setLoading(true);

    try {
      const tokens = await apiClient<AuthTokens>(API_PATHS.MOCK_LOGIN, {
        method: "POST",
        body: { email },
      });
      storeSession(tokens);
      router.push(postLoginRoute({ ...tokens, role: tokens.user.role }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthSignIn = async (provider: "google" | "microsoft") => {
    if (!ensureAgreed()) return;
    setError(null);
    setLoading(true);
    try {
      if (provider === "google") {
        await startGoogleLogin();
      } else {
        await startEntraLogin();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
      setLoading(false);
    }
  };

  if (checkingSession) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-muted/40">
      <div className="flex flex-1 items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1 text-center">
            <Link href={ROUTES.HOME} className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-xl font-bold text-primary-foreground">
              K
            </Link>
            <CardTitle className="text-2xl">
              {showOAuth ? "Create your account" : i18n.loginTitle}
            </CardTitle>
            <CardDescription>
              {showOAuth
                ? LANDING_COPY.TRUST_LINE
                : productionAuth
                  ? "Sign in with your Google or Microsoft account to continue"
                  : "Sign in to manage invoices, customers, and collections"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <label className="flex items-start gap-3 rounded-md border p-3 text-sm">
              <input
                type="checkbox"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
                className="mt-0.5 h-4 w-4"
              />
              <span className="text-muted-foreground">
                {LEGAL_COPY.AGREE_LABEL}{" "}
                <Link href={ROUTES.TERMS} className="text-primary underline">
                  Terms
                </Link>{" "}
                and{" "}
                <Link href={ROUTES.PRIVACY} className="text-primary underline">
                  Privacy
                </Link>
              </span>
            </label>

            {showOAuth && (
              <>
                {showGoogle && (
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full"
                    disabled={loading}
                    onClick={() => handleOAuthSignIn("google")}
                  >
                    Continue with Google
                  </Button>
                )}
                {showMicrosoft && (
                  <Button
                    type="button"
                    className="w-full"
                    disabled={loading}
                    onClick={() => handleOAuthSignIn("microsoft")}
                  >
                    Continue with Microsoft
                  </Button>
                )}
                {mockAuth && (
                  <p className="text-center text-xs text-muted-foreground">or use demo login below</p>
                )}
              </>
            )}

            {mockAuth && (
              <form onSubmit={handleMockSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder={DEMO_LOGIN_EMAIL}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                  />
                </div>
                {error && (
                  <p className="text-sm text-destructive" role="alert">
                    {error}
                  </p>
                )}
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? "Signing in…" : "Sign in"}
                </Button>
                <p className="text-center text-xs text-muted-foreground">
                  Development mode — MSME demo{" "}
                  <span className="font-mono">{DEMO_LOGIN_EMAIL}</span>
                  {" · CA demo "}
                  <span className="font-mono">{DEMO_CA_LOGIN_EMAIL}</span>
                </p>
              </form>
            )}

            {productionAuth && !showOAuth && (
              <p className="text-center text-sm text-muted-foreground" role="status">
                Sign-in is not configured yet. Contact your administrator.
              </p>
            )}

            {!mockAuth && error && (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            )}

            <p className="text-center text-sm text-muted-foreground">
              <Link href={ROUTES.HOME} className="text-primary hover:underline">
                ← Back to home
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
      <SiteFooter />
    </div>
  );
}
