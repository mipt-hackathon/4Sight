"use client";

import { Badge, Group, Paper, SimpleGrid, Stack, Text } from "@mantine/core";
import {
  IconAlertTriangle,
  IconReceipt2,
  IconUserCircle,
} from "@tabler/icons-react";

import type {
  CustomerChurnResponse,
  CustomerProfileResponse,
  CustomerRecommendationsResponse,
} from "../../lib/api";
import {
  formatCurrency,
  formatDateTime,
  formatDays,
  formatPercent,
} from "../../lib/format";
import { InlineActionLink, MetricTile, PageHero, SectionCard } from "../ui-kit";

function riskColor(bucket: string): string {
  if (bucket === "high") return "red";
  if (bucket === "medium") return "orange";
  return "teal";
}

type CustomerViewProps = {
  userId: number;
  profile: CustomerProfileResponse;
  churn: CustomerChurnResponse;
  recommendations: CustomerRecommendationsResponse;
};

export function CustomerView({
  userId,
  profile,
  churn,
  recommendations,
}: CustomerViewProps) {
  const fullName = [profile.identity.first_name, profile.identity.last_name]
    .filter(Boolean)
    .join(" ");

  return (
    <Stack gap="xl">
      <PageHero
        eyebrow="Customer 360"
        title={fullName || `Клиент #${profile.identity.user_id}`}
        description={
          <>
            Единая карточка клиента: идентичность, коммерческая история,
            поведение, churn-риск и следующее удерживающее действие.
          </>
        }
        aside={
          <SimpleGrid cols={1} spacing="md">
            <MetricTile
              label="Churn"
              value={formatPercent(churn.churn_probability)}
              help={churn.source}
              icon={<IconAlertTriangle size={18} />}
              tone={
                churn.churn_bucket === "high"
                  ? "danger"
                  : churn.churn_bucket === "medium"
                    ? "accent"
                    : "brand"
              }
            />
            <MetricTile
              label="RFM"
              value={profile.segment.rfm_segment ?? "unclassified"}
              help={profile.segment.rfm_score ?? "без score"}
              icon={<IconUserCircle size={18} />}
            />
            <MetricTile
              label="LTV"
              value={formatCurrency(profile.commerce.total_revenue)}
              help={`${profile.commerce.orders_count} заказов`}
              icon={<IconReceipt2 size={18} />}
              tone="accent"
            />
          </SimpleGrid>
        }
      />

      <SimpleGrid cols={{ base: 1, xl: 2 }} spacing="lg">
        <SectionCard eyebrow="Identity" title="Профиль">
          <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
            <MetricTile label="Email" value={profile.identity.email ?? "—"} />
            <MetricTile label="Город" value={profile.identity.city ?? "—"} />
            <MetricTile
              label="Страна"
              value={profile.identity.country ?? "—"}
            />
            <MetricTile
              label="Трафик"
              value={profile.identity.traffic_source ?? "—"}
            />
            <MetricTile label="Возраст" value={profile.identity.age ?? "—"} />
            <MetricTile
              label="Loyal"
              value={profile.identity.is_loyal ? "да" : "нет"}
              tone={profile.identity.is_loyal ? "brand" : "neutral"}
            />
          </SimpleGrid>
        </SectionCard>

        <SectionCard eyebrow="Commerce" title="Покупки">
          <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
            <MetricTile
              label="Первый заказ"
              value={formatDateTime(profile.commerce.first_order_at)}
            />
            <MetricTile
              label="Последний заказ"
              value={formatDateTime(profile.commerce.last_order_at)}
            />
            <MetricTile
              label="Всего заказов"
              value={profile.commerce.orders_count}
            />
            <MetricTile
              label="Средний чек"
              value={formatCurrency(profile.commerce.avg_order_value)}
            />
            <MetricTile
              label="Возвраты"
              value={profile.commerce.returned_orders_count}
              tone="danger"
            />
            <MetricTile
              label="Пауза с заказа"
              value={formatDays(profile.commerce.days_since_last_order)}
            />
          </SimpleGrid>
        </SectionCard>
      </SimpleGrid>

      <SimpleGrid cols={{ base: 1, xl: 2 }} spacing="lg">
        <SectionCard eyebrow="Behavior" title="События и сессии">
          <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
            <MetricTile label="Сессии" value={profile.behavior.session_count} />
            <MetricTile label="События" value={profile.behavior.event_count} />
            <MetricTile
              label="Последняя активность"
              value={formatDateTime(profile.behavior.last_event_at)}
            />
            <MetricTile
              label="Пауза в активности"
              value={formatDays(profile.behavior.days_since_last_event)}
            />
            <MetricTile
              label="Product views"
              value={profile.behavior.product_events_count}
            />
            <MetricTile
              label="Cart actions"
              value={profile.behavior.cart_events_count}
            />
          </SimpleGrid>
        </SectionCard>

        <SectionCard eyebrow="Segment" title="RFM и ML сигнал">
          <Stack gap="md">
            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
              <MetricTile
                label="RFM score"
                value={profile.segment.rfm_score ?? "—"}
              />
              <MetricTile
                label="RFM segment"
                value={profile.segment.rfm_segment ?? "—"}
              />
              <MetricTile
                label="Predicted segment"
                value={profile.segment.predicted_segment ?? "—"}
              />
              <MetricTile
                value={`${profile.segment.recency_score ?? "—"} / ${profile.segment.frequency_score ?? "—"} / ${profile.segment.monetary_score ?? "—"}`}
                label="R / F / M"
              />
              <MetricTile label="Churn source" value={churn.source} />
              <MetricTile label="Orders" value={churn.orders_count} />
            </SimpleGrid>
            <Group gap="xs">
              {profile.favorite_categories.map((category) => (
                <Badge key={category} variant="light" color="teal">
                  {category}
                </Badge>
              ))}
            </Group>
          </Stack>
        </SectionCard>
      </SimpleGrid>

      <SimpleGrid cols={{ base: 1, xl: 2 }} spacing="lg">
        <SectionCard
          eyebrow="Why churn"
          title="Факторы риска"
          action={<InlineActionLink href="/churn" label="Весь churn board" />}
        >
          <Stack gap="sm">
            {churn.top_factors.map((factor) => (
              <Paper
                key={factor.feature}
                withBorder
                radius="lg"
                p="md"
                bg="rgba(255,255,255,0.72)"
              >
                <Group justify="space-between" align="center">
                  <Stack gap={2}>
                    <Text fw={700}>{factor.label}</Text>
                    <Text size="sm" c="dimmed">
                      {factor.feature}
                    </Text>
                  </Stack>
                  <Badge color={riskColor(churn.churn_bucket)} variant="light">
                    {churn.churn_bucket}
                  </Badge>
                </Group>
              </Paper>
            ))}
          </Stack>
        </SectionCard>

        <SectionCard
          eyebrow="Next best actions"
          title="Рекомендации для удержания"
        >
          <Stack gap="sm">
            {recommendations.items.map((item) => (
              <Paper
                key={item.product_id}
                withBorder
                radius="lg"
                p="md"
                bg="rgba(255,255,255,0.72)"
              >
                <Group justify="space-between" align="flex-start" wrap="nowrap">
                  <Stack gap={2}>
                    <Text fw={700}>{item.product_name}</Text>
                    <Text size="sm" c="dimmed">
                      {item.category ?? "Без категории"} ·{" "}
                      {item.brand ?? "Без бренда"} · {item.reason}
                    </Text>
                  </Stack>
                  <Stack gap="xs" align="flex-end">
                    <Badge color="teal" variant="light">
                      {item.source}
                    </Badge>
                    <Text fw={700}>{formatCurrency(item.price)}</Text>
                  </Stack>
                </Group>
              </Paper>
            ))}
            {recommendations.excluded_categories.length > 0 ? (
              <Text size="sm" c="dimmed">
                Исключены категории:{" "}
                {recommendations.excluded_categories.join(", ")}.
              </Text>
            ) : null}
          </Stack>
        </SectionCard>
      </SimpleGrid>
    </Stack>
  );
}
