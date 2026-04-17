"use client";

import { MantineProvider } from "@mantine/core";
import { ReactNode } from "react";

import { theme } from "../theme";

type ProvidersProps = {
  children: ReactNode;
};

export function Providers({ children }: ProvidersProps) {
  return (
    <MantineProvider theme={theme} defaultColorScheme="light">
      {children}
    </MantineProvider>
  );
}
