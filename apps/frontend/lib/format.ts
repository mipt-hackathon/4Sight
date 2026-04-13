const currencyFormatter = new Intl.NumberFormat("ru-RU", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat("ru-RU");
const compactFormatter = new Intl.NumberFormat("ru-RU", {
  notation: "compact",
  maximumFractionDigits: 1,
});
const percentFormatter = new Intl.NumberFormat("ru-RU", {
  style: "percent",
  maximumFractionDigits: 1,
});
const dateFormatter = new Intl.DateTimeFormat("ru-RU", {
  year: "numeric",
  month: "short",
  day: "numeric",
});
const dateTimeFormatter = new Intl.DateTimeFormat("ru-RU", {
  year: "numeric",
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatCurrency(value: number | null | undefined): string {
  return currencyFormatter.format(value ?? 0);
}

export function formatNumber(value: number | null | undefined): string {
  return numberFormatter.format(value ?? 0);
}

export function formatCompactNumber(value: number | null | undefined): string {
  return compactFormatter.format(value ?? 0);
}

export function formatPercent(value: number | null | undefined): string {
  return percentFormatter.format(value ?? 0);
}

export function formatDate(value: string | Date | null | undefined): string {
  if (!value) {
    return "—";
  }
  return dateFormatter.format(new Date(value));
}

export function formatDateTime(
  value: string | Date | null | undefined,
): string {
  if (!value) {
    return "—";
  }
  return dateTimeFormatter.format(new Date(value));
}

export function formatDays(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "—";
  }
  return `${formatNumber(value)} дн.`;
}
