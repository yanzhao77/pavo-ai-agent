import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pavo AI Agent - Video Generation",
  description: "AI-powered video storyboard and generation platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-gray-50">{children}</body>
    </html>
  );
}
