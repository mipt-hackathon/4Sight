"use client";

import { Paper, SimpleGrid, Stack, Text } from "@mantine/core";
import {
  IconCalendarStats,
  IconChartLine,
  IconTimeline,
} from "@tabler/icons-react";

import type { SalesForecastResponse } from "../../lib/api";
import { formatCurrency, formatDate } from "../../lib/format";
import { MetricTile, PageHero, SectionCard } from "../ui-kit";

type ForecastViewProps = {
  forecast: SalesForecastResponse;
};

export function ForecastView({ forecast }: ForecastViewProps) {
  return (
    <Stack gap="xl">
      <PageHero
        eyebrow="Forecast"
        title="Планирование продаж"
        description={
          <>
            Для MVP достаточно общей временной серии: история, прогноз на
            горизонт и итоговый объем, который можно использовать для закупок.
          </>
        }
        aside={
          <SimpleGrid cols={1} spacing="md">
            <MetricTile
              label="Forecast total"
              value={formatCurrency(forecast.summary.forecast_total)}
              icon={<IconChartLine size={18} />}
              tone="accent"
            />
            <MetricTile
              label="AVG / day"
              value={formatCurrency(forecast.summary.avg_daily_forecast)}
              icon={<IconTimeline size={18} />}
            />
            <MetricTile
              label="Source"
              value={forecast.summary.source}
              help={`горизонт ${forecast.summary.horizon_days} дней`}
              icon={<IconCalendarStats size={18} />}
              tone="brand"
            />
          </SimpleGrid>
        }
      />

      <SimpleGrid cols={{ base: 1, xl: 2 }} spacing="lg">
        <SectionCard eyebrow="History" title="Последние фактические продажи">
          <Stack gap="sm">
            {forecast.history.slice(-14).map((point) => (
              <Paper
                key={point.date}
                withBorder
                radius="lg"
                p="md"
                bg="rgba(255,255,255,0.72)"
              >
                <SimpleGrid cols={2} spacing="sm">
                  <Text fw={600}>{formatDate(point.date)}</Text>
                  <Text fw={700} ta="right">
                    {formatCurrency(point.value)}
                  </Text>
                </SimpleGrid>
              </Paper>
            ))}
          </Stack>
        </SectionCard>

        <SectionCard
          eyebrow="Projection"
          title={`Следующие ${forecast.summary.horizon_days} дней`}
        >
          <Stack gap="sm">
            {forecast.forecast.map((point) => (
              <Paper
                key={point.date}
                withBorder
                radius="lg"
                p="md"
                bg="rgba(255,255,255,0.72)"
              >
                <SimpleGrid cols={2} spacing="sm">
                  <Text fw={600}>{formatDate(point.date)}</Text>
                  <Text fw={700} ta="right">
                    {formatCurrency(point.value)}
                  </Text>
                </SimpleGrid>
              </Paper>
            ))}
          </Stack>
        </SectionCard>
      </SimpleGrid>
    </Stack>
  );
}
