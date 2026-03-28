import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CascadeIQ",
  description: "Vessel Delay Cascade Predictor",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <div className="sticky top-0 z-50 border-b border-white/10 bg-[#050912]/80 backdrop-blur">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
            <Link href="/" className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-xl border border-white/10 bg-[rgba(216,176,76,0.12)] flex items-center justify-center">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
    <path d="M2 12h4M18 12h4M12 2v4M12 18v4" stroke="#D8B04C" strokeWidth="2" strokeLinecap="round"/>
    <circle cx="12" cy="12" r="4" stroke="#D8B04C" strokeWidth="2"/>
    <path d="M5 5l2.5 2.5M16.5 16.5L19 19M19 5l-2.5 2.5M7.5 16.5L5 19" stroke="#D8B04C" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
</div>
<div className="leading-tight">
  <div className="text-sm font-semibold tracking-wide text-white">
    CascadeIQ
  </div>
  <div className="text-xs text-[color:var(--dp-muted)]">
    Vessel Delay Intelligence
  </div>
</div>
            </Link>
            <nav className="flex items-center gap-2 text-sm">
              <Link
                className="rounded-lg px-3 py-2 text-white/80 hover:text-white hover:bg-white/5"
                href="/"
              >
                Dashboard
              </Link>
              <Link
                className="rounded-lg px-3 py-2 text-white/80 hover:text-white hover:bg-white/5"
                href="/vessels"
              >
                Vessels
              </Link>
              <Link
                className="rounded-lg px-3 py-2 text-white/80 hover:text-white hover:bg-white/5"
                href="/cascade"
              >
                Cascade
              </Link>
            </nav>
          </div>
        </div>
        {children}
      </body>
    </html>
  );
}
