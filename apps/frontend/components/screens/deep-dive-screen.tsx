"use client";

import { useEffect, useRef, useState } from "react";

import {
  Anchor,
  Box,
  Group,
  Paper,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import { IconExternalLink, IconLayoutDashboard } from "@tabler/icons-react";

import {
  ApiRequestError,
  apiClient,
  SupersetDeepDiveEmbedResponse,
} from "../../lib/api";
import { useApiResource } from "../../lib/use-api-resource";
import { PageErrorState, PageLoadingState } from "../request-state";
import { PageHero } from "../ui-kit";

export function DeepDiveScreen() {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const [embedError, setEmbedError] = useState<string | null>(null);
  const { data, error, loading, reload } = useApiResource(
    () => apiClient.getSupersetDeepDiveEmbed(),
    [],
  );

  useEffect(() => {
    if (!data || !mountRef.current) {
      return;
    }

    let active = true;
    const mountPoint = mountRef.current;
    mountPoint.innerHTML = "";
    setEmbedError(null);

    async function mountDashboard(embedConfig: SupersetDeepDiveEmbedResponse) {
      try {
        const { embedDashboard } = await import("@superset-ui/embedded-sdk");
        if (!active || !mountPoint) {
          return;
        }
        await embedDashboard({
          id: embedConfig.embedded_id,
          supersetDomain: embedConfig.superset_domain,
          mountPoint,
          fetchGuestToken: async () => embedConfig.guest_token,
          dashboardUiConfig: {
            hideTitle: true,
            hideTab: true,
            hideChartControls: true,
            filters: {
              visible: true,
              expanded: false,
            },
          },
        });
      } catch (nextError) {
        if (!active) {
          return;
        }
        const detail =
          nextError instanceof Error
            ? nextError.message
            : "Не удалось инициализировать Embedded SDK.";
        setEmbedError(detail);
      }
    }

    void mountDashboard(data);

    return () => {
      active = false;
      mountPoint.innerHTML = "";
    };
  }, [data]);

  if (loading && !data) {
    return (
      <PageLoadingState
        title="Подключаем Superset deep dive"
        detail="Готовим embedded dashboard, guest token и BI-контур внутри product MVP."
      />
    );
  }

  if (error) {
    return (
      <PageErrorState
        title="Не удалось подключить Superset"
        detail={
          error instanceof ApiRequestError
            ? error.message
            : "Неожиданная ошибка инициализации embedded dashboard."
        }
        onRetry={reload}
      />
    );
  }

  if (!data) {
    return null;
  }

  return (
    <Stack gap="lg">
      <PageHero
        eyebrow="BI Deep Dive"
        title="Встроенный Superset прямо во фронте"
        description={
          <>
            Полный `retail-notebook-bi-deep-dive` внутри MVP: можно фильтровать
            и drill-down'ить, не уходя в отдельный BI-контур.
          </>
        }
        aside={
          <Paper withBorder radius="xl" p="lg" bg="rgba(255,255,255,0.72)">
            <Stack gap="xs">
              <Group gap="sm">
                <ThemeIcon color="teal" variant="light" radius="xl" size="lg">
                  <IconLayoutDashboard size={18} />
                </ThemeIcon>
                <Text fw={700}>{data.dashboard_title}</Text>
              </Group>
              <Text size="sm" c="dimmed">
                Источник: Superset Embedded SDK + guest token через backend.
              </Text>
              <Anchor
                href={data.dashboard_url}
                target="_blank"
                rel="noreferrer"
                size="sm"
              >
                Открыть dashboard отдельно <IconExternalLink size={14} />
              </Anchor>
            </Stack>
          </Paper>
        }
      />

      <Paper
        withBorder
        radius="xl"
        p={{ base: "sm", md: "md" }}
        shadow="sm"
        style={{
          minHeight: "calc(100vh - 17rem)",
          background: "rgba(255, 255, 255, 0.82)",
        }}
      >
        <Stack gap="md">
          <Group justify="space-between" align="flex-start">
            <Stack gap={4}>
              <Text
                tt="uppercase"
                fw={800}
                size="xs"
                c="teal.7"
                style={{ letterSpacing: "0.12em" }}
              >
                Embedded
              </Text>
              <Title order={3}>Интерактивный BI внутри product frontend</Title>
            </Stack>
          </Group>
          {embedError ? (
            <PageErrorState
              title="Superset dashboard не смонтировался"
              detail={embedError}
              onRetry={reload}
            />
          ) : null}
          <Box
            style={{
              minHeight: "calc(100vh - 24rem)",
              borderRadius: "1.5rem",
              overflow: "hidden",
              border: "1px solid rgba(63, 52, 41, 0.10)",
              background: "#fff",
            }}
          >
            <div
              ref={mountRef}
              style={{
                width: "100%",
                height: "calc(100vh - 24rem)",
                minHeight: "72vh",
              }}
            />
          </Box>
        </Stack>
      </Paper>
    </Stack>
  );
}
