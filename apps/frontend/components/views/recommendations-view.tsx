"use client";

import { Badge, Group, Paper, SimpleGrid, Stack, Text } from "@mantine/core";
import { IconShoppingBag, IconSparkles } from "@tabler/icons-react";

import type { RetentionTargetsResponse } from "../../lib/api";
import { formatCurrency, formatDays, formatPercent } from "../../lib/format";
import { InlineActionLink, MetricTile, PageHero, SectionCard } from "../ui-kit";

function riskColor(bucket: string | null): string {
  if (bucket === "high") return "red";
  if (bucket === "medium") return "orange";
  return "teal";
}

type RecommendationsViewProps = {
  targets: RetentionTargetsResponse;
};

export function RecommendationsView({ targets }: RecommendationsViewProps) {
  return (
    <Stack gap="xl">
      <PageHero
        eyebrow="Recommendations"
        title="Что предложить, чтобы клиент вернулся"
        description={
          <>
            Экран для retention-оператора. Здесь уже не сырые модели, а готовый
            список клиентов и продуктов, которые можно использовать в
            реактивации.
          </>
        }
        aside={
          <SimpleGrid cols={1} spacing="md">
            <MetricTile
              label="Кейсов на экране"
              value={targets.items.length}
              help="подборки high-risk клиентов"
              icon={<IconSparkles size={18} />}
              tone="brand"
            />
          </SimpleGrid>
        }
      />

      <Stack gap="lg">
        {targets.items.map((target) => (
          <SectionCard
            key={target.customer.user_id}
            eyebrow={`Customer #${target.customer.user_id}`}
            title={target.customer.full_name}
            action={
              <InlineActionLink
                href={`/customer/${target.customer.user_id}`}
                label="Открыть профиль"
              />
            }
          >
            <Stack gap="lg">
              <Group justify="space-between" align="center" wrap="wrap">
                <Group gap="sm">
                  <Badge
                    color={riskColor(target.customer.churn_bucket)}
                    variant="light"
                  >
                    {formatPercent(target.customer.churn_probability)}
                  </Badge>
                  <Badge variant="light" color="gray">
                    {target.customer.rfm_segment ?? "unclassified"}
                  </Badge>
                </Group>
                <Text size="sm" c="dimmed">
                  {formatDays(target.customer.days_since_last_order)} без заказа
                  · revenue {formatCurrency(target.customer.total_revenue)}
                </Text>
              </Group>

              <SimpleGrid cols={{ base: 1, md: 3 }} spacing="md">
                {target.recommendations.map((item) => (
                  <Paper
                    key={`${target.customer.user_id}-${item.product_id}`}
                    withBorder
                    radius="lg"
                    p="md"
                    bg="rgba(255,255,255,0.72)"
                  >
                    <Stack gap="sm">
                      <Group justify="space-between" align="flex-start">
                        <Badge variant="light" color="teal">
                          {item.source}
                        </Badge>
                        <IconShoppingBag size={18} color="#0f766e" />
                      </Group>
                      <Stack gap={2}>
                        <Text fw={700}>{item.product_name}</Text>
                        <Text size="sm" c="dimmed">
                          {item.category ?? "Без категории"} ·{" "}
                          {item.brand ?? "Без бренда"}
                        </Text>
                      </Stack>
                      <Text size="sm" c="dimmed">
                        {item.reason}
                      </Text>
                      <Group justify="space-between" align="center">
                        <Text fw={800}>{formatCurrency(item.price)}</Text>
                        {item.score !== null ? (
                          <Badge variant="dot" color="gray">
                            score {item.score.toFixed(2)}
                          </Badge>
                        ) : null}
                      </Group>
                    </Stack>
                  </Paper>
                ))}
              </SimpleGrid>
            </Stack>
          </SectionCard>
        ))}
      </Stack>
    </Stack>
  );
}
