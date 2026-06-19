import {
  LOGIN_STORAGE_KEYS,
  MSME_LOGIN_SEGMENTS,
  type MsmeLoginSegmentId,
} from "@/lib/constants";
import type { AppLanguage } from "@/lib/i18n";

const DEFAULT_SEGMENT: MsmeLoginSegmentId = MSME_LOGIN_SEGMENTS[0].id;

export function isMsmeSegmentId(value: string | null | undefined): value is MsmeLoginSegmentId {
  return Boolean(value && MSME_LOGIN_SEGMENTS.some((segment) => segment.id === value));
}

export function getStoredMsmeSegment(): MsmeLoginSegmentId {
  if (typeof window === "undefined") return DEFAULT_SEGMENT;
  const saved = window.localStorage.getItem(LOGIN_STORAGE_KEYS.MSME_SEGMENT);
  return isMsmeSegmentId(saved) ? saved : DEFAULT_SEGMENT;
}

export function resolveMsmeSegment(
  apiSegment?: string | null,
  localSegment?: MsmeLoginSegmentId,
): MsmeLoginSegmentId {
  if (isMsmeSegmentId(apiSegment)) return apiSegment;
  return localSegment ?? getStoredMsmeSegment();
}

export async function persistMsmeSegment(segmentId: MsmeLoginSegmentId): Promise<void> {
  setStoredMsmeSegment(segmentId);
  const { apiClient } = await import("@/lib/api-client");
  const { API_PATHS } = await import("@/lib/constants");
  await apiClient(API_PATHS.COMPANY_ME, {
    method: "PATCH",
    body: { msme_segment: segmentId },
  });
}

export function setStoredMsmeSegment(id: MsmeLoginSegmentId): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(LOGIN_STORAGE_KEYS.MSME_SEGMENT, id);
}

export function getMsmeSegmentLabel(id: MsmeLoginSegmentId, lang: AppLanguage): string {
  const segment = MSME_LOGIN_SEGMENTS.find((item) => item.id === id);
  return segment?.label[lang] ?? MSME_LOGIN_SEGMENTS[0].label[lang];
}

export function isQuickStartDismissed(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(LOGIN_STORAGE_KEYS.QUICK_START_DISMISSED) === "1";
}

export function dismissQuickStart(): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(LOGIN_STORAGE_KEYS.QUICK_START_DISMISSED, "1");
}

export function isStarterProductsImported(segmentId: MsmeLoginSegmentId): boolean {
  if (typeof window === "undefined") return false;
  const raw = window.localStorage.getItem(LOGIN_STORAGE_KEYS.STARTER_PRODUCTS_IMPORTED);
  if (!raw) return false;
  try {
    const imported = JSON.parse(raw) as string[];
    return imported.includes(segmentId);
  } catch {
    return false;
  }
}

export function markStarterProductsImported(segmentId: MsmeLoginSegmentId): void {
  if (typeof window === "undefined") return;
  const raw = window.localStorage.getItem(LOGIN_STORAGE_KEYS.STARTER_PRODUCTS_IMPORTED);
  let imported: string[] = [];
  if (raw) {
    try {
      imported = JSON.parse(raw) as string[];
    } catch {
      imported = [];
    }
  }
  if (!imported.includes(segmentId)) {
    imported.push(segmentId);
  }
  window.localStorage.setItem(LOGIN_STORAGE_KEYS.STARTER_PRODUCTS_IMPORTED, JSON.stringify(imported));
}
