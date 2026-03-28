import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import Image from "next/image";

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
  icons: {
    icon: "/logo.png",
  },
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
              <div className="h-9 w-9 rounded-xl overflow-hidden">
  <Image src="/logo.png" alt="CascadeIQ" width={36} height={36} className="object-contain" />
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
        <footer className="border-t border-white/10 mt-auto py-6 px-5">
  <div className="mx-auto max-w-6xl flex flex-col items-center gap-2">
    <div className="text-sm font-semibold text-white/70 tracking-wide">Developed by Team APYREX</div>
    <div className="flex flex-wrap justify-center gap-x-6 gap-y-1">
      {["Anvith N", "Utkrisht Thaman", "Mitansh Gupta", "Sai Pranav", "Nihal Goud"].map((name) => (
        <span key={name} className="text-sm text-white/50">{name}</span>
      ))}
    </div>
    <div className="text-xs text-white/30 mt-1">©CascadeIQ · DP World National Hackathon · BITS Pilani Hyderabad</div>
  </div>
</footer>
      </body>
    </html>
  );
}
