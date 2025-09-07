import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AuthProvider } from '@/contexts/AuthContext';
import { FrameworkProvider } from '@/contexts/FrameworkContext';
import { AIProvider } from '@/contexts/AIContext';
import { AccessibilityProvider } from '@/components/accessibility/AccessibilityProvider';
import "./globals.css";
import "../styles/accessibility.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Biz Design - AI-powered Business Framework Learning",
  description: "Transform your business thinking with AI-guided framework learning",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <AuthProvider>
          <FrameworkProvider>
            <AIProvider>
              <AccessibilityProvider>
                {children}
              </AccessibilityProvider>
            </AIProvider>
          </FrameworkProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
