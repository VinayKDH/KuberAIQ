import { LOCAL_API_URL, PUBLIC_APEX_DOMAIN } from "@/lib/constants";

function stripTrailingSlash(url: string): string {
  return url.replace(/\/$/, "");
}

function isKuberaiqHostname(hostname: string): boolean {
  return (
    hostname === PUBLIC_APEX_DOMAIN || hostname.endsWith(`.${PUBLIC_APEX_DOMAIN}`)
  );
}

/** Resolve API base URL — same-origin on kuberaiq.com (Next.js rewrites proxy to API). */
export function resolveApiBase(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL
    ? stripTrailingSlash(process.env.NEXT_PUBLIC_API_URL)
    : undefined;

  if (typeof window !== "undefined" && isKuberaiqHostname(window.location.hostname)) {
    return "";
  }

  if (fromEnv) return fromEnv;
  return LOCAL_API_URL;
}
