import type { Metadata } from "next";

import "highlight.js/styles/github-dark.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "NL2SQL — Ask your database in plain English",
  description:
    "A natural-language-to-SQL agent built on Google ADK. Ask questions, get answers, charts, and the SQL behind them.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
