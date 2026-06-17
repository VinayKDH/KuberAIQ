import { LEGAL_COPY } from "@/lib/constants";
import { LegalDocument } from "@/components/marketing/legal-document";

export default function PrivacyPage() {
  return (
    <LegalDocument title={LEGAL_COPY.PRIVACY_TITLE}>
      <section className="space-y-4 text-sm leading-relaxed text-muted-foreground">
        <p>
          This Privacy Policy explains how KuberAIQ (&quot;we&quot;, &quot;us&quot;) collects, uses, and
          protects information when you use our platform. We are committed to handling data
          responsibly in line with applicable Indian law, including the Digital Personal Data
          Protection Act, 2023 (DPDP).
        </p>

        <h2 className="text-lg font-semibold text-foreground">1. Information we collect</h2>
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong className="text-foreground">Account data:</strong> name, email, OAuth
            identifiers (Google/Microsoft), and role.
          </li>
          <li>
            <strong className="text-foreground">Business data:</strong> company name, GSTIN,
            address, invoice and customer records, payment history, compliance profile fields.
          </li>
          <li>
            <strong className="text-foreground">Usage data:</strong> app logs, audit trail of
            changes, AI chat messages you send, and technical diagnostics.
          </li>
        </ul>

        <h2 className="text-lg font-semibold text-foreground">2. How we use information</h2>
        <p>
          We use your data to provide and improve the Service: generate invoices and PDFs, send
          payment reminders (when enabled), personalize compliance calendars, operate the AI
          assistant, and secure your account. We do not sell your business data to third parties.
        </p>

        <h2 className="text-lg font-semibold text-foreground">3. Storage &amp; processors</h2>
        <p>
          Data is stored on Microsoft Azure infrastructure in India regions where available.
          Sub-processors may include cloud hosting, email/WhatsApp delivery, and AI inference
          providers bound by contractual data protection obligations.
        </p>

        <h2 className="text-lg font-semibold text-foreground">4. Retention</h2>
        <p>
          We retain account and business records while your account is active. After closure, we
          delete or anonymize data within a reasonable period unless retention is required by law
          (e.g., tax records).
        </p>

        <h2 className="text-lg font-semibold text-foreground">5. Your rights</h2>
        <p>
          You may request access, correction, or deletion of personal data by contacting us.
          Business owners control tenant data; staff access is limited by role. You may export
          invoices and reports from within the app.
        </p>

        <h2 className="text-lg font-semibold text-foreground">6. Security</h2>
        <p>{LEGAL_COPY.SECURITY_CONTACT}</p>

        <h2 className="text-lg font-semibold text-foreground">7. Contact &amp; grievance</h2>
        <p>{LEGAL_COPY.PRIVACY_CONTACT}</p>
      </section>
    </LegalDocument>
  );
}
