"use client";

import Link from "next/link";
import { ArrowRight, Bot } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export interface DashboardNudge {
  type: string;
  count: number;
  label: string;
  href: string;
}

interface DashboardNudgesCardProps {
  nudges?: DashboardNudge[];
}

export function DashboardNudgesCard({ nudges }: DashboardNudgesCardProps) {
  if (!nudges?.length) {
    return null;
  }

  return (
    <Card className="border-primary/20 bg-primary/5">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          <CardTitle className="text-base">Suggested actions</CardTitle>
        </div>
        <CardDescription>Quick links based on your business data</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        {nudges.map((nudge) => (
          <Link
            key={nudge.type}
            href={nudge.href}
            className="inline-flex h-9 items-center rounded-md border border-input bg-background px-3 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
          >
            {nudge.label}
            <ArrowRight className="ml-1 h-3 w-3" />
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}
