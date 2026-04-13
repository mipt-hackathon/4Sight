import { Center, Loader, Paper, Stack, Text, Title } from "@mantine/core";

export default function Loading() {
  return (
    <Center mih="70vh">
      <Paper withBorder radius="xl" p="xl" shadow="sm">
        <Stack align="center" gap="md">
          <Loader color="teal" size="lg" />
          <Title order={3}>Загружаем продуктовый контур</Title>
          <Text c="dimmed">
            Подтягиваем агрегаты, churn-сигналы и рекомендации.
          </Text>
        </Stack>
      </Paper>
    </Center>
  );
}
