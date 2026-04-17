import "@mantine/core/styles.css";
import "./globals.css";

import type { Metadata } from "next";
import {
  ColorSchemeScript,
  MantineProvider,
  mantineHtmlProps,
} from "@mantine/core";
import { ReactNode } from "react";

import { AppShell } from "../components/app-shell";
import { theme } from "../theme";

export const metadata: Metadata = {
  title: "Retention Control Room",
  description:
    "Кастомное аналитическое приложение для churn, рекомендаций и мониторинга продаж.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru" {...mantineHtmlProps}>
      <head>
        <ColorSchemeScript defaultColorScheme="light" />
      </head>
      <body>
        <MantineProvider theme={theme} defaultColorScheme="light">
          <AppShell>{children}</AppShell>
        </MantineProvider>
      </body>
    </html>
  );
}
