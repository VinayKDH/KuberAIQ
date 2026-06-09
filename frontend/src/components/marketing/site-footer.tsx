import Link from "next/link";
import { APP_NAME, LEGAL_COPY, ROUTES } from "@/lib/constants";

export function SiteFooter() {
  return (
    <footer className="border-t bg-muted/30 py-8">
      <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 px-4 text-sm text-muted-foreground sm:flex-row">
        <p>© {new Date().getFullYear()} {APP_NAME}. Built for Indian MSMEs.</p>
        <nav className="flex gap-6">
          <Link href={ROUTES.TERMS} className="hover:text-foreground">
            {LEGAL_COPY.FOOTER_TERMS}
          </Link>
          <Link href={ROUTES.PRIVACY} className="hover:text-foreground">
            {LEGAL_COPY.FOOTER_PRIVACY}
          </Link>
          <Link href={ROUTES.LOGIN} className="hover:text-foreground">
            Sign in
          </Link>
        </nav>
      </div>
    </footer>
  );
}
