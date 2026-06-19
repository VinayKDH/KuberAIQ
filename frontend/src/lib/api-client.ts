import { clearSession } from "@/lib/auth";
import { API_NETWORK_ERROR, STORAGE_KEYS } from "@/lib/constants";
import { resolveApiBase } from "@/lib/api-url";

const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class NetworkError extends Error {
  constructor(message: string = API_NETWORK_ERROR) {
    super(message);
    this.name = "NetworkError";
  }
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

function isFetchNetworkError(err: unknown): boolean {
  if (!(err instanceof TypeError)) return false;
  const msg = err.message.toLowerCase();
  return (
    msg === "failed to fetch" ||
    msg.includes("networkerror") ||
    msg.includes("load failed") ||
    msg.includes("network request failed")
  );
}

function formatValidationDetails(details: unknown): string | null {
  if (!Array.isArray(details) || details.length === 0) return null;
  const parts = details
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const field = "field" in item && typeof item.field === "string" ? item.field : "";
      const issue = "issue" in item && typeof item.issue === "string" ? item.issue : "";
      if (!issue) return null;
      return field ? `${field}: ${issue}` : issue;
    })
    .filter((part): part is string => Boolean(part));
  return parts.length > 0 ? parts.join("; ") : null;
}

export function formatApiError(err: unknown, fallback = "Request failed"): string {
  if (err instanceof ApiError) {
    const detailText = formatValidationDetails(err.details);
    if (detailText && err.message === "Request validation failed") {
      return detailText;
    }
    return err.message;
  }
  if (err instanceof NetworkError) {
    return err.message;
  }
  if (err instanceof Error) {
    return err.message;
  }
  return fallback;
}

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
}

export function setTokens(accessToken: string, refreshToken?: string) {
  localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, accessToken);
  if (refreshToken) {
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
  }
}

export function clearTokens() {
  localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.USER);
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined | null> | object;
};

function buildUrl(path: string, params?: RequestOptions["params"]): string {
  const base = resolveApiBase();
  const pathWithPrefix = `${API_PREFIX}${path}`;
  const url = base
    ? new URL(pathWithPrefix, `${base}/`)
    : new URL(
        pathWithPrefix,
        typeof window !== "undefined" ? window.location.origin : "http://localhost:3000",
      );
  if (params) {
    Object.entries(params as Record<string, unknown>).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  }
  return url.toString();
}

async function fetchWithNetworkGuard(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  try {
    return await fetch(input, init);
  } catch (err) {
    if (isFetchNetworkError(err)) {
      throw new NetworkError();
    }
    throw err;
  }
}

export async function apiClient<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, params, headers: customHeaders, ...rest } = options;
  const token = getAccessToken();

  const headers: HeadersInit = {
    Accept: "application/json",
    ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...customHeaders,
  };

  const response = await fetchWithNetworkGuard(buildUrl(path, params), {
    ...rest,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401 && token) {
      clearSession();
    }
    const error = data?.error;
    throw new ApiError(
      error?.message ?? response.statusText ?? "Request failed",
      response.status,
      error?.code,
      error?.details,
    );
  }

  return data as T;
}

export async function downloadBlob(
  path: string,
  fallbackFilename: string,
  params?: Record<string, string | number | boolean | undefined | null>,
): Promise<void> {
  const token = getAccessToken();
  const response = await fetchWithNetworkGuard(buildUrl(path, params), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    if (response.status === 401 && token) {
      clearSession();
    }
    const data = await response.json().catch(() => null);
    const error = data?.error;
    throw new ApiError(
      error?.message ?? response.statusText ?? "Download failed",
      response.status,
      error?.code,
      error?.details,
    );
  }

  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition");
  const filenameMatch = disposition?.match(/filename="([^"]+)"/);
  const filename = filenameMatch?.[1] ?? fallbackFilename;
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}
