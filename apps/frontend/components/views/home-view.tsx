"use client";

import Link from "next/link";

import { Badge, Group, Paper, SimpleGrid, Stack, Text } from "@mantine/core";
import {
  IconAlertTriangle,
  IconBolt,
  IconChartBar,
  IconSparkles,
  IconShieldX,
  IconUsers,
} from "@tabler/icons-react";

import type {
  DashboardOverviewResponse,
  HighRiskCustomersResponse,
} from "../../lib/api";
import {
  formatCompactNumber,
  formatCurrency,
  formatPercent,
} from "../../lib/format";
import {
  FeatureLinkCard,
  InlineActionLink,
  MetricTile,
  PageHero,
  SectionCard,
} from "../ui-kit";

function riskColor(bucket: string): string {
  if (bucket === "high") return "red";
  if (bucket === "medium") return "orange";
  return "teal";
}

type HomeViewProps = {
  overview: DashboardOverviewResponse;
  highRisk: HighRiskCustomersResponse;
};

export function HomeView({ overview, highRisk }: HomeViewProps) {
  return (
    <Stack gap="xl">
      <PageHero
        eyebrow="Product MVP"
        title="Единый экран удержания: сигнал, риск, действие."
        description={
          <>
            Этот фронт не заменяет Superset. Он собирает в один сценарий
            витрины, churn-сигнал и retention-рекомендации, чтобы показать, как
            бизнес работает с клиентом, а не как аналитик строит ad hoc графики.
          </>
        }
        aside={
          <SimpleGrid cols={1} spacing="md">
            <MetricTile
              label="Клиентов"
              value={formatCompactNumber(
                overview.customer_health.customers_total,
              )}
              help="активная база после clean и mart"
              icon={<IconUsers size={18} />}
            />
            <MetricTile
              label="High-risk"
              value={formatCompactNumber(
                overview.churn_monitor.high_risk_customers,
              )}
              help={`${formatPercent(overview.churn_monitor.high_risk_share)} базы`}
              icon={<IconAlertTriangle size={18} />}
              tone="danger"
            />
            <MetricTile
              label="Revenue 30d"
              value={formatCurrency(overview.sales_kpis.revenue_last_30d)}
              help="операционный ориентир для retention"
              icon={<IconBolt size={18} />}
              tone="accent"
            />
          </SimpleGrid>
        }
      />

      <SimpleGrid cols={{ base: 1, md: 3 }} spacing="lg">
        <FeatureLinkCard
          href="/dashboard"
          eyebrow="Диагностика"
          title="KPI и customer health"
          description="Выручка, сегменты, логистика и категории с риском недовольства."
          icon={<IconChartBar size={22} />}
        />
        <FeatureLinkCard
          href="/churn"
          eyebrow="Прогноз"
          title="Отток и приоритет клиентов"
          description="Список high-risk клиентов с вероятностью оттока и факторами риска."
          icon={<IconAlertTriangle size={22} />}
        />
        <FeatureLinkCard
          href="/recommendations"
          eyebrow="Воздействие"
          title="Retention-рекомендации"
          description="Персональные офферы для high-risk сегмента без небезопасных категорий."
          icon={<IconSparkles size={22} />}
        />
      </SimpleGrid>

      <SimpleGrid cols={{ base: 1, xl: 2 }} spacing="lg">
        <SectionCard
          eyebrow="Сейчас в фокусе"
          title="Приоритетные клиенты"
          action={
            <InlineActionLink href="/churn" label="Открыть churn board" />
          }
        >
          <Stack gap="sm">
            {highRisk.items.map((customer) => (
              <Link
                key={customer.user_id}
                href={`/customer/${customer.user_id}`}
                prefetch={false}
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <Paper
                  withBorder
                  radius="lg"
                  p="md"
                  bg="rgba(255,255,255,0.72)"
                >
                  <Group justify="space-between" align="center" wrap="nowrap">
                    <Stack gap={2}>
                      <Text fw={700}>{customer.full_name}</Text>
                      <Text size="sm" c="dimmed">
                        {customer.city ?? "Неизвестный город"} ·{" "}
                        {customer.rfm_segment ?? "unclassified"}
                      </Text>
                    </Stack>
                    <Group gap="sm">
                      <Badge
                        color={riskColor(customer.churn_bucket)}
                        variant="light"
                      >
                        {customer.churn_bucket}
                      </Badge>
                      <Text fw={700}>
                        {formatPercent(customer.churn_probability)}
                      </Text>
                    </Group>
                  </Group>
                </Paper>
              </Link>
            ))}
          </Stack>
        </SectionCard>

        <SectionCard
          eyebrow="Гигиена оффера"
          title="Что не отправлять в реактивацию"
          action={
            <InlineActionLink href="/dashboard" label="Все quality-сигналы" />
          }
        >
          <Stack gap="md">
            {overview.category_watchlist.map((item) => (
              <Paper
                key={item.category}
                withBorder
                radius="lg"
                p="md"
                bg="rgba(255,255,255,0.72)"
              >
                <Stack gap="sm">
                  <Group
                    justify="space-between"
                    align="flex-start"
                    wrap="nowrap"
                  >
                    <Stack gap={2}>
                      <Text fw={700}>{item.category}</Text>
                      <Text size="sm" c="dimmed">
                        dissatisfaction{" "}
                        {formatPercent(item.dissatisfaction_score)} · returns{" "}
                        {formatPercent(item.return_rate)}
                      </Text>
                    </Stack>
                    <IconShieldX size={18} color="#9f2d2d" />
                  </Group>
                  <Text size="sm" c="dimmed">
                    {formatCompactNumber(item.order_items_count)} позиций с
                    заметной долей возвратов или негативных отзывов. Эти
                    категории лучше исключать из retention-подборок.
                  </Text>
                </Stack>
              </Paper>
            ))}
          </Stack>
        </SectionCard>
      </SimpleGrid>
    </Stack>
  );
}
