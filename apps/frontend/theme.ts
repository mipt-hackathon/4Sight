import { createTheme } from "@mantine/core";

export const theme = createTheme({
  primaryColor: "teal",
  defaultRadius: "xl",
  fontFamily: '"Avenir Next", "Segoe UI Variable", "Trebuchet MS", sans-serif',
  headings: {
    fontFamily:
      '"Avenir Next", "Segoe UI Variable", "Trebuchet MS", sans-serif',
    fontWeight: "800",
  },
  colors: {
    sand: [
      "#fffaf3",
      "#f7ede0",
      "#efdcc5",
      "#e7ccb0",
      "#dfbb98",
      "#d8ab81",
      "#d19b69",
      "#b67f4b",
      "#8d6136",
      "#644321",
    ],
    teal: [
      "#e3faf7",
      "#c3ece7",
      "#93d8d1",
      "#62c4bc",
      "#39b3aa",
      "#1f998f",
      "#0f766e",
      "#0a605b",
      "#074a46",
      "#043431",
    ],
  },
});
