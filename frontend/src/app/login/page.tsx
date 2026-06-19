"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { MsmeLoginShowcase } from "@/components/auth/msme-login-showcase";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  API_PATHS,
  DEMO_CA_LOGIN_EMAIL,
  DEMO_LOGIN_EMAIL,
  LANDING_COPY,
  LEGAL_COPY,
  LOGIN_COPY,
  LOGIN_STORAGE_KEYS,
  MSME_LOGIN_SEGMENTS,
  ROUTES,
  type MsmeLoginSegmentId,
} from "@/lib/constants";
import { apiClient } from "@/lib/api-client";
import { clearSession, isAuthenticated, storeSession, type AuthTokens } from "@/lib/auth";
import { isEntraAuthConfigured, isMockAuthEnabled, startEntraLogin } from "@/lib/entra";
import { postLoginRoute, type MeGate } from "@/lib/session-routing";
import { isGoogleAuthConfigured, startGoogleLogin } from "@/lib/google";
import { getPreferredLanguage, I18N_MESSAGES, type AppLanguage } from "@/lib/i18n";

function readStoredSegment(): MsmeLoginSegmentId {
  if (typeof window === "undefined") return MSME_LOGIN_SEGMENTS[0].id;
  const saved = window.localStorage.getItem(LOGIN_STORAGE_KEYS.MSME_SEGMENT);
  return MSME_LOGIN_SEGMENTS.some((s) => s.id === saved)
    ? (saved as MsmeLoginSegmentId)
    : MSME_LOGIN_SEGMENTS[0].id;
}

export default function LoginPage() {
  const router = useRouter();
  const mockAuth = isMockAuthEnabled();
  const showMicrosoft = !mockAuth && isEntraAuthConfigured();
  const showGoogle = !mockAuth && isGoogleAuthConfigured();
  const showOAuth = showMicrosoft || showGoogle;
  const productionAuth = !mockAuth;

  const [lang, setLang] = useState<AppLanguage>("en");
  const [segmentId, setSegmentId] = useState<MsmeLoginSegmentId>(MSME_LOGIN_SEGMENTS[0].id);
  const [email, setEmail] = useState(DEMO_LOGIN_EMAIL);
  const [remember, setRemember] = useState(true);
  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checkingSession, setCheckingSession] = useState(() => isAuthenticated());
  const [error, setError] = useState<string | null>(null);

  const onSelectSegment = useCallback((id: MsmeLoginSegmentId) => {
    setSegmentId(id);
  }, []);

  useEffect(() => {
    setLang(getPreferredLanguage());
    setSegmentId(readStoredSegment());
    const savedEmail = window.localStorage.getItem(LOGIN_STORAGE_KEYS.REMEMBER_EMAIL);
    if (savedEmail) {
      setEmail(savedEmail);
      setRemember(true);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated()) {
      setCheckingSession(false);
      return;
    }
    apiClient<MeGate>(API_PATHS.ME)
      .then((me) => router.replace(postLoginRoute(me)))
      .catch(() => {
        clearSession();
        setCheckingSession(false);
      });
  }, [router]);

  const setLanguage = (value: AppLanguage) => {
    setLang(value);
    window.localStorage.setItem("kuberaiq_lang", value);
  };

  const ensureAgreed = () => {
    if (!agreed) {
      setError("Please accept the Terms and Privacy Policy to continue.");
      return false;
    }
    return true;
  };

  const persistEmail = (value: string) => {
    if (remember) {
      window.localStorage.setItem(LOGIN_STORAGE_KEYS.REMEMBER_EMAIL, value);
    } else {
      window.localStorage.removeItem(LOGIN_STORAGE_KEYS.REMEMBER_EMAIL);
    }
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
      persistEmail(email);
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
      if (provider === "google") await startGoogleLogin();
      else await startEntraLogin();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
      setLoading(false);
    }
  };

  if (checkingSession) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="h-9 w-9 animate-spin rounded-full border-4 border-[#0a1f3d] border-t-transparent" />
      </div>
    );
  }

  const i18n = I18N_MESSAGES[lang];
  const activeSegment = MSME_LOGIN_SEGMENTS.find((s) => s.id === segmentId) ?? MSME_LOGIN_SEGMENTS[0];

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <MsmeLoginShowcase lang={lang} activeId={segmentId} onSelect={onSelectSegment} />

      <div className="flex flex-1 flex-col bg-slate-50">
        <div className="flex justify-end p-4 sm:p-6">
          <label className="flex items-center gap-2 rounded-lg border bg-white px-3 py-2 text-sm shadow-sm">
            <span aria-hidden>🇮🇳</span>
            <select
              value={lang}
              onChange={(e) => setLanguage(e.target.value as AppLanguage)}
              className="bg-transparent outline-none"
              aria-label="Language"
            >
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
            </select>
          </label>
        </div>

        <div className="flex flex-1 items-center justify-center px-4 pb-8 sm:px-8">
          <div className="w-full max-w-md">
            <div className="rounded-2xl border bg-white p-6 shadow-lg sm:p-8">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-[#0a1f3d]">
                  {showOAuth && !mockAuth ? "Sign in" : LOGIN_COPY.WELCOME[lang]}
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {showOAuth && !mockAuth ? i18n.loginTitle : LOGIN_COPY.SUBTITLE[lang]}
                </p>
                <p className="mt-3 rounded-lg bg-orange-50 px-3 py-2 text-xs text-orange-900 lg:hidden">
                  {activeSegment.headline[lang]}
                </p>
              </div>

              <label className="mt-5 flex items-start gap-2 rounded-lg border bg-slate-50 p-3 text-xs text-muted-foreground">
                <input
                  type="checkbox"
                  checked={agreed}
                  onChange={(e) => setAgreed(e.target.checked)}
                  className="mt-0.5 h-4 w-4"
                />
                <span>
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
                <div className="mt-4 space-y-2">
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
                    <p className="text-center text-xs text-muted-foreground">
                      {LOGIN_COPY.OR_CONTINUE[lang]}
                    </p>
                  )}
                </div>
              )}

              {mockAuth && (
                <form onSubmit={handleMockSubmit} className="mt-4 space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">{LOGIN_COPY.EMAIL_LABEL[lang]}</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder={LOGIN_COPY.EMAIL_PLACEHOLDER[lang]}
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      autoComplete="email"
                      className="h-11"
                    />
                  </div>
                  <label className="flex items-center gap-2 text-sm text-muted-foreground">
                    <input
                      type="checkbox"
                      checked={remember}
                      onChange={(e) => setRemember(e.target.checked)}
                      className="h-4 w-4"
                    />
                    {LOGIN_COPY.REMEMBER[lang]}
                  </label>
                  {error && (
                    <p className="text-sm text-destructive" role="alert">
                      {error}
                    </p>
                  )}
                  <Button type="submit" className="h-11 w-full bg-[#0a1f3d]" disabled={loading}>
                    {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    {loading ? LOGIN_COPY.SIGNING_IN[lang] : LOGIN_COPY.SIGN_IN[lang]}
                  </Button>
                  <p className="text-center text-xs text-muted-foreground">
                    Dev — MSME <span className="font-mono">{DEMO_LOGIN_EMAIL}</span>
                    {" · CA "}
                    <span className="font-mono">{DEMO_CA_LOGIN_EMAIL}</span>
                  </p>
                </form>
              )}

              {productionAuth && !showOAuth && (
                <p className="mt-4 text-center text-sm text-muted-foreground" role="status">
                  Sign-in is not configured yet. Contact your administrator.
                </p>
              )}

              {!mockAuth && error && (
                <p className="mt-4 text-sm text-destructive" role="alert">
                  {error}
                </p>
              )}

              <p className="mt-6 text-center text-sm text-muted-foreground">
                {LOGIN_COPY.NEW_HERE[lang]}{" "}
                <Link href={ROUTES.HOME} className="font-medium text-[#ea580c] hover:underline">
                  {LOGIN_COPY.START_FREE[lang]}
                </Link>
              </p>
              <p className="mt-3 text-center text-xs text-muted-foreground">{LANDING_COPY.TRUST_LINE}</p>
              <p className="mt-4 text-center text-sm">
                <Link href={ROUTES.HOME} className="text-primary hover:underline">
                  ← Back to home
                </Link>
              </p>
            </div>
          </div>
        </div>

        <footer className="border-t bg-white px-4 py-3 text-center text-[11px] text-muted-foreground sm:px-8">
          © {new Date().getFullYear()} KuberAIQ ·{" "}
          <Link href={ROUTES.PRIVACY} className="hover:underline">
            Privacy
          </Link>
          {" · "}
          <Link href={ROUTES.TERMS} className="hover:underline">
            Terms
          </Link>
        </footer>
      </div>
    </div>
  );
}
