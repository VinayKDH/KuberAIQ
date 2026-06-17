import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { PUBLIC_WEB_URL } from "@/lib/constants";
import { Providers } from "@/components/providers";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-geist-sans" });

export const metadata: Metadata = {
  metadataBase: new URL(PUBLIC_WEB_URL),
  manifest: "/manifest.json",
  title: "KuberAIQ — GST Billing, Collections & Compliance for MSMEs",
  description:
    "Sign up free. GST invoices, payment reminders, MSME compliance calendar, and AI assistant for Indian small businesses.",
  openGraph: {
    siteName: "KuberAIQ",
    url: PUBLIC_WEB_URL,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
