"use client";

import { useEffect, useState } from "react";
import {
  Building2,
  Factory,
  Hammer,
  ShoppingBag,
  Store,
  UtensilsCrossed,
  type LucideIcon,
} from "lucide-react";
import {
  APP_NAME,
  LOGIN_COPY,
  LOGIN_STORAGE_KEYS,
  MSME_LOGIN_SEGMENTS,
  type MsmeLoginSegmentId,
} from "@/lib/constants";
import type { AppLanguage } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const SEGMENT_ICONS: Record<MsmeLoginSegmentId, LucideIcon> = {
  kirana: Store,
  trader: ShoppingBag,
  manufacturing: Factory,
  services: Building2,
  construction: Hammer,
  food: UtensilsCrossed,
};

const ROTATE_MS = 6000;

type MsmeLoginShowcaseProps = {
  lang: AppLanguage;
  activeId: MsmeLoginSegmentId;
  onSelect: (id: MsmeLoginSegmentId) => void;
};

export function MsmeLoginShowcase({ lang, activeId, onSelect }: MsmeLoginShowcaseProps) {
  const [paused, setPaused] = useState(false);
  const segment = MSME_LOGIN_SEGMENTS.find((s) => s.id === activeId) ?? MSME_LOGIN_SEGMENTS[0];
  const Icon = SEGMENT_ICONS[segment.id];

  useEffect(() => {
    if (paused) return;
    const timer = window.setInterval(() => {
      const idx = MSME_LOGIN_SEGMENTS.findIndex((s) => s.id === activeId);
      const next = MSME_LOGIN_SEGMENTS[(idx + 1) % MSME_LOGIN_SEGMENTS.length];
      onSelect(next.id);
    }, ROTATE_MS);
    return () => window.clearInterval(timer);
  }, [activeId, onSelect, paused]);

  useEffect(() => {
    window.localStorage.setItem(LOGIN_STORAGE_KEYS.MSME_SEGMENT, activeId);
  }, [activeId]);

  return (
    <div className="relative flex min-h-[38vh] flex-1 flex-col overflow-hidden bg-[#0a1f3d] lg:min-h-screen lg:max-w-[54%]">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,_rgba(251,146,60,0.18),_transparent_50%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,_rgba(37,99,235,0.22),_transparent_55%)]" />
      <div
        className="absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage:
            "repeating-linear-gradient(45deg, #fff 0, #fff 1px, transparent 0, transparent 50%)",
          backgroundSize: "12px 12px",
        }}
      />
      <div className="absolute left-0 top-0 h-1 w-full bg-gradient-to-r from-[#ff9933] via-white to-[#138808]" />

      <div className="relative z-10 flex h-full flex-col p-6 sm:p-8 lg:p-10">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10 text-lg font-bold text-white ring-1 ring-white/20">
            K
          </div>
          <div>
            <p className="text-lg font-bold text-white">{APP_NAME}</p>
            <p className="text-[10px] font-medium tracking-[0.18em] text-white/65">
              {LOGIN_COPY.SUITE_TAGLINE[lang]}
            </p>
          </div>
        </div>

        <div className="mt-8 max-w-xl lg:mt-10">
          <h1 className="text-3xl font-bold leading-tight text-white sm:text-4xl lg:text-[2.4rem]">
            {LOGIN_COPY.HERO_PRIMARY[lang]}{" "}
            <span className="text-[#fb923c]">{LOGIN_COPY.HERO_ACCENT[lang]}</span>
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-white/75 sm:text-base">
            {LOGIN_COPY.HERO_SUB[lang]}
          </p>
        </div>

        <p className="mt-6 text-xs font-semibold uppercase tracking-wider text-white/55">
          {LOGIN_COPY.YOUR_BUSINESS[lang]}
        </p>
        <div
          className="mt-3 flex flex-wrap gap-2"
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => setPaused(false)}
        >
          {MSME_LOGIN_SEGMENTS.map((item) => {
            const ItemIcon = SEGMENT_ICONS[item.id];
            const active = item.id === activeId;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelect(item.id)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                  active
                    ? "border-[#fb923c] bg-[#fb923c]/20 text-white"
                    : "border-white/20 bg-white/5 text-white/75 hover:border-white/40 hover:bg-white/10",
                )}
              >
                <ItemIcon className="h-3.5 w-3.5" />
                {item.label[lang]}
              </button>
            );
          })}
        </div>

        <div
          className="mt-8 hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm lg:block"
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => setPaused(false)}
        >
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[#fb923c] text-white">
              <Icon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-lg font-semibold text-white">{segment.label[lang]}</p>
              <p className="mt-1 text-base text-[#fdba74]">{segment.headline[lang]}</p>
              <ul className="mt-4 space-y-2">
                {segment.highlights[lang].map((line) => (
                  <li key={line} className="flex items-center gap-2 text-sm text-white/75">
                    <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                    {line}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <p className="mt-auto hidden pt-8 text-xs leading-relaxed text-white/55 lg:block">
          {LOGIN_COPY.BUILT_FOR[lang]}
        </p>
      </div>
    </div>
  );
}
