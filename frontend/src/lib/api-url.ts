import { LOCAL_API_URL, usesSameOriginApi } from "@/lib/constants";

function stripTrailingSlash(url: string): string {
  return url.replace(/\/$/, "");
}

/** Resolve API base URL — same-origin on kuberaiq.com and Cloud Run (Next.js rewrites proxy to API). */
export function resolveApiBase(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL
    ? stripTrailingSlash(process.env.NEXT_PUBLIC_API_URL)
    : undefined;

  if (typeof window !== "undefined" && usesSameOriginApi(window.location.hostname)) {
    return "";
  }

  if (fromEnv) return fromEnv;
  return LOCAL_API_URL;
}
