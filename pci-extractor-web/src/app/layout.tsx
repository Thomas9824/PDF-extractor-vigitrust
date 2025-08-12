import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  preload: true,
});

export const dynamic = "force-static";

export const viewport: Viewport = {
  maximumScale: 1, // Disable auto-zoom on mobile Safari
};

export const metadata: Metadata = {
  title: "PCI DSS Extractor - Extract requirements from PDF documents",
  description: "Extract PCI DSS requirements from PDF documents automatically. Simple, fast and secure.",
  openGraph: {
    type: "website",
    title: "PCI DSS Extractor",
    description: "Extract PCI DSS requirements from PDF documents automatically",
  },
  twitter: {
    card: "summary_large_image",
    title: "PCI DSS Extractor",
    description: "Extract PCI DSS requirements from PDF documents automatically",
  },
  generator: 'v0.dev'
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.className} antialiased max-w-screen min-h-svh bg-slate-1 text-slate-12`}
      >
        <div className="max-w-screen-sm mx-auto w-full relative z-[1] flex flex-col min-h-screen">
          <div className="px-5 gap-8 flex flex-col flex-1 py-[12vh]">
            <main className="flex justify-center">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}