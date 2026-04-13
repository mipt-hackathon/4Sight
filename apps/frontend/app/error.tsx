"use client";

import { useEffect } from "react";

import { Button, Group, Paper, Stack, Text, Title } from "@mantine/core";
import { IconRefresh, IconPlugConnectedX } from "@tabler/icons-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <Paper withBorder radius="xl" p="xl" shadow="sm">
      <Stack gap="md">
        <Group gap="sm">
          <IconPlugConnectedX size={22} color="#9f2d2d" />
          <Text fw={700} c="red.8">
            Frontend не смог собрать страницу
          </Text>
        </Group>
        <Title order={2}>Ошибка загрузки данных</Title>
        <Text c="dimmed">
          Backend или ML-контур вернул неожиданный ответ. Если это не старт
          после <code>down -v</code>, проверь логи сервисов и повтори запрос.
        </Text>
        <Text size="sm" c="dimmed">
          {error.message}
        </Text>
        <Group>
          <Button leftSection={<IconRefresh size={16} />} onClick={reset}>
            Повторить
          </Button>
        </Group>
      </Stack>
    </Paper>
  );
}
