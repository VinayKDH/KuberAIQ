"use client";

import { ThemeProvider } from "next-themes";
import { QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { CanonicalOriginGuard } from "@/components/canonical-origin-guard";
import { createQueryClient } from "@/lib/query-client";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => createQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
        <CanonicalOriginGuard>{children}</CanonicalOriginGuard>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
