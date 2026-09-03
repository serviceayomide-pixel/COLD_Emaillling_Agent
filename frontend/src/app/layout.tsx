import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "Acquisition Engine | Dashboard",
  description: "Autonomous B2B client acquisition engine for UK healthcare recruitment",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased dark`}>
      <body className="min-h-screen font-sans bg-[#07090f] text-slate-50 selection:bg-indigo-500/30 selection:text-white">
        {children}
      </body>
    </html>
  );
}
