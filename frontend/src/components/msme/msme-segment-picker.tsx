"use client";

import {
  Building2,
  Factory,
  Hammer,
  ShoppingBag,
  Store,
  UtensilsCrossed,
  type LucideIcon,
} from "lucide-react";
import { MSME_LOGIN_SEGMENTS, type MsmeLoginSegmentId } from "@/lib/constants";
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

type MsmeSegmentPickerProps = {
  lang: AppLanguage;
  value: MsmeLoginSegmentId;
  onChange: (id: MsmeLoginSegmentId) => void;
  compact?: boolean;
};

export function MsmeSegmentPicker({ lang, value, onChange, compact }: MsmeSegmentPickerProps) {
  return (
    <div className={cn("flex flex-wrap gap-2", compact ? "gap-1.5" : "gap-2")}>
      {MSME_LOGIN_SEGMENTS.map((item) => {
        const Icon = SEGMENT_ICONS[item.id];
        const active = item.id === value;
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onChange(item.id)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full border text-xs font-medium transition-colors",
              compact ? "px-2.5 py-1" : "px-3 py-1.5",
              active
                ? "border-primary bg-primary/10 text-primary"
                : "border-border bg-background text-muted-foreground hover:border-primary/40 hover:text-foreground",
            )}
          >
            <Icon className="h-3.5 w-3.5 shrink-0" />
            {item.label[lang]}
          </button>
        );
      })}
    </div>
  );
}
