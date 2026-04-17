"use client";

import { Code, Group, Paper, Stack, Text } from "@mantine/core";
import { IconDatabaseImport } from "@tabler/icons-react";

import { InlineActionLink, PageHero, SectionCard } from "./ui-kit";

type SetupStateProps = {
  title: string;
  detail?: string;
};

export function SetupState({ title, detail }: SetupStateProps) {
  return (
    <Stack gap="xl">
      <PageHero
        eyebrow="Data not ready"
        title={title}
        description={
          <>
            После <Code>docker compose down -v</Code> поднимаются только сервисы
            и миграции. Product API требует, чтобы в PostgreSQL уже были собраны{" "}
            <Code>clean.*</Code> и <Code>mart.*</Code>.
          </>
        }
        aside={
          <Paper withBorder radius="xl" p="lg" bg="rgba(255,255,255,0.68)">
            <Group gap="sm" mb="xs">
              <IconDatabaseImport size={18} color="#0f766e" />
              <Text fw={700}>Сервис жив, данные ещё нет</Text>
            </Group>
            <Text size="sm" c="dimmed">
              Это уже не runtime crash, а управляемое состояние старта после
              очистки volume’ов.
            </Text>
          </Paper>
        }
      />

      <SectionCard eyebrow="Bootstrap" title="Что выполнить">
        <Stack gap="md">
          <Paper withBorder radius="lg" p="md" bg="dark.9">
            <Text ff="monospace" c="gray.0">
              docker compose run --rm etl
            </Text>
          </Paper>
          <Paper withBorder radius="lg" p="md" bg="dark.9">
            <Text ff="monospace" c="gray.0">
              docker compose run --rm marts-builder
            </Text>
          </Paper>
          {detail ? (
            <Text size="sm" c="dimmed">
              {detail}
            </Text>
          ) : null}
          <Text size="sm" c="dimmed">
            После этого просто обнови страницу. Superset к этому экрану не
            относится: frontend питается от product backend, а тот читает clean
            и mart.
          </Text>
          <InlineActionLink href="/" label="Вернуться на главную" />
        </Stack>
      </SectionCard>
    </Stack>
  );
}
