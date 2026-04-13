"use client";

import {
  Button,
  Group,
  Paper,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { IconRefresh, IconServerBolt } from "@tabler/icons-react";

import { PageHero, SectionCard } from "./ui-kit";

type PageLoadingStateProps = {
  title: string;
  detail: string;
};

export function PageLoadingState({ title, detail }: PageLoadingStateProps) {
  return (
    <Stack gap="xl">
      <PageHero
        eyebrow="Loading"
        title={title}
        description={detail}
        aside={
          <Paper withBorder radius="xl" p="lg" bg="rgba(255,255,255,0.72)">
            <Stack gap="sm">
              <Skeleton height={18} radius="xl" />
              <Skeleton height={42} radius="xl" />
              <Skeleton height={14} radius="xl" width="78%" />
            </Stack>
          </Paper>
        }
      />

      <SimpleGrid cols={{ base: 1, md: 3 }} spacing="lg">
        {Array.from({ length: 3 }).map((_, index) => (
          <Paper key={index} withBorder radius="xl" p="lg">
            <Stack gap="md">
              <Skeleton height={16} radius="xl" width="32%" />
              <Skeleton height={36} radius="xl" />
              <Skeleton height={14} radius="xl" width="65%" />
            </Stack>
          </Paper>
        ))}
      </SimpleGrid>

      <SimpleGrid cols={{ base: 1, xl: 2 }} spacing="lg">
        {Array.from({ length: 2 }).map((_, index) => (
          <SectionCard
            key={index}
            eyebrow="Loading"
            title="Подтягиваем витрину"
          >
            <Stack gap="sm">
              {Array.from({ length: 4 }).map((__, innerIndex) => (
                <Skeleton key={innerIndex} height={68} radius="lg" />
              ))}
            </Stack>
          </SectionCard>
        ))}
      </SimpleGrid>
    </Stack>
  );
}

type PageErrorStateProps = {
  title: string;
  detail: string;
  actionLabel?: string;
  onRetry?: () => void;
};

export function PageErrorState({
  title,
  detail,
  actionLabel = "Повторить запрос",
  onRetry,
}: PageErrorStateProps) {
  return (
    <Paper withBorder radius="xl" p="xl" shadow="sm">
      <Stack gap="md">
        <Group gap="sm">
          <IconServerBolt size={20} color="#9f2d2d" />
          <Text fw={700} c="red.8">
            Product API вернул ошибку
          </Text>
        </Group>
        <Title order={2}>{title}</Title>
        <Text c="dimmed">{detail}</Text>
        {onRetry ? (
          <Group>
            <Button leftSection={<IconRefresh size={16} />} onClick={onRetry}>
              {actionLabel}
            </Button>
          </Group>
        ) : null}
      </Stack>
    </Paper>
  );
}
