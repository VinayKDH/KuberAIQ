import Link from "next/link";
import { APP_NAME, LEGAL_COPY, ROUTES } from "@/lib/constants";
import { SiteFooter } from "@/components/marketing/site-footer";

interface LegalDocumentProps {
  title: string;
  children: React.ReactNode;
}

export function LegalDocument({ title, children }: LegalDocumentProps) {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
          <Link href={ROUTES.HOME} className="font-semibold text-primary">
            {APP_NAME}
          </Link>
          <Link href={ROUTES.LOGIN} className="text-sm text-muted-foreground hover:text-foreground">
            Sign in
          </Link>
        </div>
      </header>
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10">
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{LEGAL_COPY.LAST_UPDATED}</p>
        <div className="prose prose-neutral mt-8 max-w-none dark:prose-invert">{children}</div>
      </main>
      <SiteFooter />
    </div>
  );
}
