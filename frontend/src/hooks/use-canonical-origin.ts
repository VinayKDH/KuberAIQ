import { useEffect, useState } from "react";
import { PUBLIC_APEX_DOMAIN, PUBLIC_WEB_URL } from "@/lib/constants";

/** Redirect apex (kuberaiq.com) → www so auth tokens and API calls share one origin. */
export function useCanonicalOriginRedirect(): boolean {
  const [redirecting, setRedirecting] = useState(
    () =>
      typeof window !== "undefined" &&
      window.location.hostname === PUBLIC_APEX_DOMAIN,
  );

  useEffect(() => {
    if (window.location.hostname !== PUBLIC_APEX_DOMAIN) {
      setRedirecting(false);
      return;
    }

    setRedirecting(true);
    const canonical = new URL(PUBLIC_WEB_URL);
    const target = new URL(window.location.href);
    target.protocol = canonical.protocol;
    target.host = canonical.host;
    window.location.replace(target.toString());
  }, []);

  return redirecting;
}
