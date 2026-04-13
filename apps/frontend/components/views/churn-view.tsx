"use client";

import Link from "next/link";

import { Badge, Group, Paper, SimpleGrid, Stack, Text } from "@mantine/core";
import {
  IconAlertTriangle,
  IconFlame,
  IconTargetArrow,
} from "@tabler/icons-react";

import type {
  DashboardOverviewResponse,
  HighRiskCustomersResponse,
} from "../../lib/api";
import {
  formatCompactNumber,
  formatCurrency,
  formatDays,
  formatPercent,
} from "../../lib/format";
import { MetricTile, PageHero, SectionCard } from "../ui-kit";

function riskColor(bucket: string): string {
  if (bucket === "high") return "red";
  if (bucket === "medium") return "orange";
  return "teal";
}

type ChurnViewProps = {
  overview: DashboardOverviewResponse;
  highRisk: HighRiskCustomersResponse;
};

export function ChurnView({ overview, highRisk }: ChurnViewProps) {
  return (
    <Stack gap="xl">
      <PageHero
        eyebrow="Churn board"
        title="Кого удерживать прямо сейчас"
        description={
          <>
            Это не мониторинг модели ради модели. Экран отвечает на вопрос, у
            каких клиентов риск уже высокий и с кем надо работать в первую
            очередь.
          </>
        }
        aside={
          <SimpleGrid cols={1} spacing="md">
            <MetricTile
              label="High-risk"
              value={formatCompactNumber(
                overview.churn_monitor.high_risk_customers,
              )}
              icon={<IconAlertTriangle size={18} />}
              tone="danger"
            />
            <MetricTile
              label="Medium-risk"
              value={formatCompactNumber(
                overview.churn_monitor.medium_risk_customers,
              )}
              icon={<IconTargetArrow size={18} />}
              tone="accent"
            />
            <MetricTile
              label="High-risk share"
              value={formatPercent(overview.churn_monitor.high_risk_share)}
              icon={<IconFlame size={18} />}
              tone="brand"
            />
          </SimpleGrid>
        }
      />

      <SimpleGrid cols={{ base: 1, xl: 2 }} spacing="lg">
        <SectionCard eyebrow="Priority queue" title="High-risk клиенты">
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
                  <Group
                    justify="space-between"
                    align="flex-start"
                    wrap="nowrap"
                  >
                    <Stack gap={4}>
                      <Text fw={700}>{customer.full_name}</Text>
                      <Text size="sm" c="dimmed">
                        {customer.city ?? "Неизвестный город"} ·{" "}
                        {customer.country ?? "—"}
                      </Text>
                      <Text size="sm" c="dimmed">
                        {customer.rfm_segment ?? "unclassified"} ·{" "}
                        {formatCurrency(customer.total_revenue)} ·{" "}
                        {formatDays(customer.days_since_last_order)}
                      </Text>
                      <Text size="sm" c="dimmed">
                        {customer.top_factors
                          .map((factor) => factor.label)
                          .join(" · ")}
                      </Text>
                    </Stack>
                    <Stack gap="xs" align="flex-end">
                      <Badge
                        color={riskColor(customer.churn_bucket)}
                        variant="light"
                      >
                        {customer.churn_bucket}
                      </Badge>
                      <Text fw={800}>
                        {formatPercent(customer.churn_probability)}
                      </Text>
                    </Stack>
                  </Group>
                </Paper>
              </Link>
            ))}
          </Stack>
        </SectionCard>

        <SectionCard
          eyebrow="Risk segments"
          title="Где high-risk особенно плотный"
        >
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
                      avg revenue {formatCurrency(segment.avg_revenue)}
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
      </SimpleGrid>
    </Stack>
  );
}
