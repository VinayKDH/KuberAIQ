"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  CalendarCheck,
  FileText,
  MessageSquare,
  Sparkles,
  Wallet,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { SiteFooter } from "@/components/marketing/site-footer";
import { apiClient } from "@/lib/api-client";
import { isAuthenticated } from "@/lib/auth";
import { API_PATHS, APP_NAME, LANDING_COPY, ROUTES } from "@/lib/constants";
import { postLoginRoute, type MeGate } from "@/lib/session-routing";

const FEATURES = [
  {
    icon: FileText,
    title: LANDING_COPY.FEATURE_INVOICES,
    description: LANDING_COPY.FEATURE_INVOICES_DESC,
  },
  {
    icon: Wallet,
    title: LANDING_COPY.FEATURE_COLLECTIONS,
    description: LANDING_COPY.FEATURE_COLLECTIONS_DESC,
  },
  {
    icon: CalendarCheck,
    title: LANDING_COPY.FEATURE_COMPLIANCE,
    description: LANDING_COPY.FEATURE_COMPLIANCE_DESC,
  },
  {
    icon: Sparkles,
    title: LANDING_COPY.FEATURE_AI,
    description: LANDING_COPY.FEATURE_AI_DESC,
  },
] as const;

export default function HomePage() {
  const router = useRouter();
  const [checkingSession, setCheckingSession] = useState(() => isAuthenticated());

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
        setCheckingSession(false);
      });
  }, [router]);

  if (checkingSession) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
              K
            </div>
            <span className="font-semibold">{APP_NAME}</span>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" onClick={() => router.push(ROUTES.LOGIN)}>
              {LANDING_COPY.CTA_SECONDARY}
            </Button>
            <Button onClick={() => router.push(ROUTES.LOGIN)}>
              {LANDING_COPY.CTA_PRIMARY}
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <section className="mx-auto max-w-5xl px-4 py-16 text-center sm:py-24">
          <p className="mb-4 text-sm font-medium text-primary">{LANDING_COPY.TAGLINE}</p>
          <h1 className="mx-auto max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
            {LANDING_COPY.HERO_TITLE}
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
            {LANDING_COPY.HERO_SUBTITLE}
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button size="lg" onClick={() => router.push(ROUTES.LOGIN)}>
              {LANDING_COPY.CTA_PRIMARY}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <p className="text-sm text-muted-foreground">{LANDING_COPY.TRUST_LINE}</p>
          </div>
        </section>

        <section className="border-t bg-muted/30 py-16">
          <div className="mx-auto max-w-5xl px-4">
            <h2 className="text-center text-2xl font-semibold">{LANDING_COPY.FEATURES_TITLE}</h2>
            <div className="mt-10 grid gap-6 sm:grid-cols-2">
              {FEATURES.map(({ icon: Icon, title, description }) => (
                <div
                  key={title}
                  className="rounded-xl border bg-background p-6 shadow-sm"
                >
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold">{title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-16">
          <div className="mx-auto max-w-5xl px-4 text-center">
            <MessageSquare className="mx-auto h-10 w-10 text-primary" />
            <h2 className="mt-4 text-2xl font-semibold">Ready for your first invoice?</h2>
            <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
              Sign up in under two minutes. Add your GSTIN, invite your team later, and start
              billing today.
            </p>
            <Button size="lg" className="mt-8" onClick={() => router.push(ROUTES.LOGIN)}>
              {LANDING_COPY.CTA_PRIMARY}
            </Button>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
