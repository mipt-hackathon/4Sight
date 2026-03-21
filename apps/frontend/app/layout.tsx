import "./globals.css";

import type { Metadata } from "next";
import { ReactNode } from "react";

import { AppShell } from "../components/app-shell";

export const metadata: Metadata = {
  title: "Retail Analytics Hackathon",
  description: "Frontend scaffold for dashboard, churn, recommendations, and forecast flows.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
