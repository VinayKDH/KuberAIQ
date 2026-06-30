export const I18N_MESSAGES = {
  en: {
    loginTitle: "Sign in to KuberAIQ",
    dashboardOverview: "Overview",
    dashboardSubtitle: "Your business at a glance",
    sidebarFooterMsme: "GST Billing & Collections",
    sidebarFooterCa: "CA Compliance Portal",
  },
  hi: {
    loginTitle: "KuberAIQ में साइन इन करें",
    dashboardOverview: "ओवरव्यू",
    dashboardSubtitle: "आपके व्यवसाय की झलक",
    sidebarFooterMsme: "GST बिलिंग और कलेक्शन्स",
    sidebarFooterCa: "CA कंप्लायंस पोर्टल",
  },
} as const;

export type AppLanguage = keyof typeof I18N_MESSAGES;

export function screenCopy<T extends { en: string; hi: string }>(
  block: T,
  lang: AppLanguage = "en",
): string {
  return block[lang] ?? block.en;
}

export function getPreferredLanguage(): AppLanguage {
  if (typeof window === "undefined") return "en";
  const saved = window.localStorage.getItem("kuberaiq_lang");
  if (saved === "hi" || saved === "en") return saved;
  const nav = window.navigator.language.toLowerCase();
  return nav.startsWith("hi") ? "hi" : "en";
}
