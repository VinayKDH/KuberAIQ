import { ADMIN_SESSION_HEADER, ADMIN_PROXY_PREFIX, STORAGE_KEYS } from "@/lib/constants";

export function getAdminSessionKey(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(STORAGE_KEYS.ADMIN_SESSION_KEY);
}

export function setAdminSessionKey(key: string): void {
  sessionStorage.setItem(STORAGE_KEYS.ADMIN_SESSION_KEY, key.trim());
}

export function clearAdminSession(): void {
  sessionStorage.removeItem(STORAGE_KEYS.ADMIN_SESSION_KEY);
}

export function isAdminAuthenticated(): boolean {
  return Boolean(getAdminSessionKey());
}

type AdminRequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined | null>;
};

function buildAdminUrl(path: string, params?: AdminRequestOptions["params"]): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${ADMIN_PROXY_PREFIX}${normalized}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  }
  return url.toString();
}

export async function adminClient<T>(path: string, options: AdminRequestOptions = {}): Promise<T> {
  const sessionKey = getAdminSessionKey();
  if (!sessionKey) {
    throw new Error("Admin session expired");
  }

  const { body, params, headers: customHeaders, ...rest } = options;
  const response = await fetch(buildAdminUrl(path, params), {
    ...rest,
    headers: {
      Accept: "application/json",
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      [ADMIN_SESSION_HEADER]: sessionKey,
      ...customHeaders,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.error?.message ?? data?.detail ?? response.statusText ?? "Request failed";
    throw new Error(message);
  }
  return data as T;
}

export async function verifyAdminKey(key: string): Promise<boolean> {
  setAdminSessionKey(key);
  try {
    await adminClient("/admin/auth/verify", { method: "POST" });
    return true;
  } catch {
    clearAdminSession();
    return false;
  }
}
