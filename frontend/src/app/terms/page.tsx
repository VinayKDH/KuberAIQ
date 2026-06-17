import { LEGAL_COPY } from "@/lib/constants";
import { LegalDocument } from "@/components/marketing/legal-document";

export default function TermsPage() {
  return (
    <LegalDocument title={LEGAL_COPY.TERMS_TITLE}>
      <section className="space-y-4 text-sm leading-relaxed text-muted-foreground">
        <p>
          These Terms of Service (&quot;Terms&quot;) govern your use of KuberAIQ (&quot;Service&quot;),
          operated as a cloud software platform for Indian micro, small, and medium enterprises.
          By creating an account or using the Service, you agree to these Terms.
        </p>

        <h2 className="text-lg font-semibold text-foreground">1. The Service</h2>
        <p>
          KuberAIQ provides invoicing, customer management, payment collection tools, compliance
          reminders, and AI-assisted business guidance. Compliance dates and checklists are
          indicative only — you remain responsible for verifying filings on official government
          portals. KuberAIQ is not a GST Suvidha Provider (GSP), chartered accountant, or legal
          advisor.
        </p>

        <h2 className="text-lg font-semibold text-foreground">2. Accounts</h2>
        <p>
          You must provide accurate business information during registration. You are responsible
          for safeguarding your account credentials and for all activity under your account. You
          must be authorized to act on behalf of the business you register.
        </p>

        <h2 className="text-lg font-semibold text-foreground">3. Acceptable use</h2>
        <p>
          You may not use the Service for unlawful purposes, to submit false tax or invoice data,
          to abuse messaging features (spam), or to attempt unauthorized access to other tenants&apos;
          data. We may suspend accounts that violate these Terms.
        </p>

        <h2 className="text-lg font-semibold text-foreground">4. Data &amp; availability</h2>
        <p>
          We implement reasonable security and backup practices but do not guarantee uninterrupted
          availability. You should maintain your own records of critical business documents. See
          our Privacy Policy for how we handle personal and business data.
        </p>

        <h2 className="text-lg font-semibold text-foreground">5. Beta &amp; changes</h2>
        <p>
          During public beta, features may change without notice. We may introduce paid plans in
          the future with advance notice. Continued use after changes constitutes acceptance of
          updated Terms.
        </p>

        <h2 className="text-lg font-semibold text-foreground">6. Limitation of liability</h2>
        <p>
          To the maximum extent permitted by law, KuberAIQ is not liable for indirect, incidental,
          or consequential damages, including lost profits or penalties arising from missed
          statutory deadlines. Our total liability is limited to fees paid in the twelve months
          preceding the claim (or ₹5,000 during free beta, whichever is greater).
        </p>

        <h2 className="text-lg font-semibold text-foreground">7. Contact</h2>
        <p>{LEGAL_COPY.TERMS_CONTACT}</p>
      </section>
    </LegalDocument>
  );
}
