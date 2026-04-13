"use client";

import {
  Badge,
  Group,
  Paper,
  Progress,
  SimpleGrid,
  Stack,
  Text,
} from "@mantine/core";
import {
  IconAlertTriangle,
  IconCash,
  IconPackage,
  IconTruckDelivery,
  IconUsers,
} from "@tabler/icons-react";

import type { DashboardOverviewResponse } from "../../lib/api";
import {
  formatCompactNumber,
  formatCurrency,
  formatDate,
  formatDateTime,
  formatDays,
  formatPercent,
} from "../../lib/format";
import { MetricTile, PageHero, SectionCard } from "../ui-kit";

function barValue(value: number, maxValue: number): number {
  if (maxValue <= 0) return 0;
  return Math.max(8, Math.round((value / maxValue) * 100));
}

type DashboardViewProps = {
  overview: DashboardOverviewResponse;
};

export function DashboardView({ overview }: DashboardViewProps) {
  const maxTrend = Math.max(
    ...overview.sales_trend.map((point) => point.value),
    1,
  );

  return (
    <Stack gap="xl">
      <PageHero
        eyebrow="Dashboard"
        title="Операционный контур бизнеса"
        description={
          <>
            Срез для продуктовой команды: продажи, churn pressure, логистика и
            категории, которые лучше не отправлять в рекомендации.
          </>
        }
        aside={
          <Paper withBorder radius="xl" p="lg" bg="rgba(255,255,255,0.72)">
            <Stack gap={4}>
              <Text size="sm" c="dimmed">
                Обновлено
              </Text>
              <Text fw={800} size="lg">
                {formatDateTime(overview.generated_at)}
              </Text>
              <Text size="sm" c="dimmed">
                Источник: product backend поверх mart-слоя
              </Text>
            </Stack>
          </Paper>
        }
      />

      <SimpleGrid cols={{ base: 1, sm: 2, xl: 4 }} spacing="lg">
        <MetricTile
          label="Выручка"
          value={formatCurrency(overview.sales_kpis.total_revenue)}
          help={`${formatCurrency(overview.sales_kpis.revenue_last_30d)} за 30 дней`}
          icon={<IconCash size={18} />}
          tone="accent"
        />
        <MetricTile
          label="Заказы"
          value={formatCompactNumber(overview.sales_kpis.total_orders)}
          help={`${formatCompactNumber(overview.sales_kpis.orders_last_30d)} за 30 дней`}
          icon={<IconPackage size={18} />}
        />
        <MetricTile
          label="Клиенты"
          value={formatCompactNumber(overview.sales_kpis.total_customers)}
          help={`последняя дата продаж ${formatDate(overview.sales_kpis.last_sales_date)}`}
          icon={<IconUsers size={18} />}
        />
        <MetricTile
          label="High-risk share"
          value={formatPercent(overview.churn_monitor.high_risk_share)}
          help={`${formatCompactNumber(overview.churn_monitor.high_risk_customers)} клиентов`}
          icon={<IconAlertTriangle size={18} />}
          tone="danger"
        />
      </SimpleGrid>

      <SimpleGrid cols={{ base: 1, xl: 2 }} spacing="lg">
        <SectionCard eyebrow="Sales" title="Динамика продаж">
          <Stack gap="sm">
            {overview.sales_trend.slice(-14).map((point) => (
              <Paper
                key={point.date}
                withBorder
                radius="lg"
                p="sm"
                bg="rgba(255,255,255,0.72)"
              >
                <Stack gap={8}>
                  <Group justify="space-between">
                    <Text fw={600}>{formatDate(point.date)}</Text>
                    <Text fw={700}>{formatCurrency(point.value)}</Text>
                  </Group>
                  <Progress
                    value={barValue(point.value, maxTrend)}
                    color="teal"
                    radius="xl"
                    size="lg"
                  />
                </Stack>
              </Paper>
            ))}
          </Stack>
        </SectionCard>

        <SectionCard eyebrow="Customer health" title="База и лояльность">
          <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
            <MetricTile
              label="Активные 30d"
              value={formatCompactNumber(
                overview.customer_health.active_customers_30d,
              )}
            />
            <MetricTile
              label="Loyal"
              value={formatCompactNumber(
                overview.customer_health.loyal_customers,
              )}
              tone="brand"
            />
            <MetricTile
              label="Repeat rate"
              value={formatPercent(
                overview.customer_health.repeat_customer_rate,
              )}
            />
            <MetricTile
              label="AVG LTV"
              value={formatCurrency(overview.customer_health.avg_ltv)}
            />
          </SimpleGrid>
        </SectionCard>
      </SimpleGrid>

      <SimpleGrid cols={{ base: 1, xl: 2 }} spacing="lg">
        <SectionCard eyebrow="Risk map" title="Где концентрируется churn">
          <Stack gap="sm">
            {overview.churn_monitor.top_risk_segments.map((segment) => (
              <Paper
                key={segment.segment}
                withBorder
                radius="lg"
                p="md"
                bg="rgba(255,255,255,0.72)"
              >
                <Group justify="space-between" align="center">
                  <Stack gap={2}>
                    <Text fw={700}>{segment.segment}</Text>
                    <Text size="sm" c="dimmed">
                      {formatCompactNumber(segment.customers_count)} клиентов ·
                      средний revenue {formatCurrency(segment.avg_revenue)}
                    </Text>
                  </Stack>
                  <Badge color="red" variant="light">
                    {formatPercent(segment.high_risk_share)}
                  </Badge>
                </Group>
              </Paper>
            ))}
          </Stack>
        </SectionCard>

        <SectionCard eyebrow="Logistics" title="Доставка и возвраты">
          <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
            <MetricTile
              label="Ship lead time"
              value={formatDays(overview.logistics_snapshot.avg_ship_days)}
              icon={<IconTruckDelivery size={18} />}
            />
            <MetricTile
              label="Delivery lead time"
              value={formatDays(overview.logistics_snapshot.avg_delivery_days)}
              icon={<IconTruckDelivery size={18} />}
            />
            <MetricTile
              label="Delayed deliveries"
              value={formatPercent(
                overview.logistics_snapshot.delayed_delivery_rate,
              )}
              tone="accent"
            />
            <MetricTile
              label="Returned orders"
              value={formatPercent(
                overview.logistics_snapshot.returned_orders_rate,
              )}
              tone="danger"
            />
          </SimpleGrid>
        </SectionCard>
      </SimpleGrid>

      <SimpleGrid cols={{ base: 1, xl: 2 }} spacing="lg">
        <SectionCard
          eyebrow="Product quality"
          title="Категории, которые лучше исключать из офферов"
        >
          <Stack gap="sm">
            {overview.category_watchlist.map((item) => (
              <Paper
                key={item.category}
                withBorder
                radius="lg"
                p="md"
                bg="rgba(255,255,255,0.72)"
              >
                <Stack gap="xs">
                  <Group justify="space-between" align="center">
                    <Text fw={700}>{item.category}</Text>
                    <Badge color="red" variant="light">
                      {formatPercent(item.dissatisfaction_score)}
                    </Badge>
                  </Group>
                  <Text size="sm" c="dimmed">
                    {formatCompactNumber(item.order_items_count)} позиций ·
                    возвраты {formatPercent(item.return_rate)} · негатив{" "}
                    {formatPercent(item.negative_review_rate)}
                  </Text>
                </Stack>
              </Paper>
            ))}
          </Stack>
        </SectionCard>

        <SectionCard eyebrow="Segment mix" title="Клиентская база">
          <Stack gap="sm">
            {overview.segment_mix.map((item) => (
              <Paper
                key={item.segment}
                withBorder
                radius="lg"
                p="md"
                bg="rgba(255,255,255,0.72)"
              >
                <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="xs">
                  <Text fw={700}>{item.segment}</Text>
                  <Text size="sm" c="dimmed">
                    {formatCompactNumber(item.customers_count)} клиентов
                  </Text>
                  <Text size="sm" c="dimmed">
                    avg revenue {formatCurrency(item.avg_revenue)}
                  </Text>
                  <Text size="sm" c="dimmed">
                    avg orders {item.avg_orders.toFixed(1)}
                  </Text>
                  <Text size="sm" c="dimmed">
                    {formatDays(item.avg_days_since_last_order)}
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
