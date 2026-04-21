import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import StyledJsxRegistry from "./registry";
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
  title: "Pixra - AI E-Commerce SEO Platform",
  description: "Yapay zeka destekli e-ticaret SEO ve GEO optimizasyon platformu",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="tr"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
          <StyledJsxRegistry>{children}</StyledJsxRegistry>
        </body>
    </html>
  );
}
