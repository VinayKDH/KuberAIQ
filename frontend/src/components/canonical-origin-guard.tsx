"use client";

import { useCanonicalOriginRedirect } from "@/hooks/use-canonical-origin";

/** Redirect apex (kuberaiq.com) → www on every page when DNS still points at Hostinger CDN. */
export function CanonicalOriginGuard({ children }: { children: React.ReactNode }) {
  const redirecting = useCanonicalOriginRedirect();
  if (redirecting) {
    return null;
  }
  return <>{children}</>;
}
