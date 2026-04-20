"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  AppShell as MantineAppShell,
  Badge,
  Box,
  Burger,
  Divider,
  Group,
  NavLink,
  Paper,
  ScrollArea,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import {
  IconAlertTriangle,
  IconChartLine,
  IconDashboard,
  IconHome2,
  IconLayoutDashboard,
  IconPresentationAnalytics,
  IconSparkles,
  IconUserCircle,
} from "@tabler/icons-react";
import { ReactNode } from "react";

const navigation = [
  {
    href: "/",
    label: "Обзор",
    hint: "Сигнал, риск, действие",
    icon: IconHome2,
  },
  {
    href: "/dashboard",
    label: "KPI",
    hint: "Продажи и здоровье базы",
    icon: IconDashboard,
  },
  {
    href: "/deep-dive",
    label: "BI Deep Dive",
    hint: "Встроенный Superset",
    icon: IconLayoutDashboard,
  },
  {
    href: "/churn",
    label: "Отток",
    hint: "High-risk клиенты",
    icon: IconAlertTriangle,
  },
  {
    href: "/customer/1",
    label: "Customer 360",
    hint: "Профиль одного клиента",
    icon: IconUserCircle,
  },
  {
    href: "/recommendations",
    label: "Рекомендации",
    hint: "Retention actions",
    icon: IconSparkles,
  },
  {
    href: "/forecast",
    label: "Прогноз",
    hint: "Планирование продаж",
    icon: IconChartLine,
  },
];

function isItemActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/";
  }
  if (href.startsWith("/customer/")) {
    return pathname.startsWith("/customer/");
  }
  return pathname === href;
}

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const [opened, { toggle, close }] = useDisclosure(false);
  const isDeepDivePage = pathname === "/deep-dive";

  return (
    <MantineAppShell
      header={{ height: 72 }}
      navbar={{ width: 320, breakpoint: "md", collapsed: { mobile: !opened } }}
      padding="lg"
    >
      <MantineAppShell.Header>
        <Group h="100%" px="lg" justify="space-between">
          <Group gap="md">
            <Burger
              opened={opened}
              onClick={toggle}
              hiddenFrom="md"
              size="sm"
            />
            <Link
              href="/"
              prefetch={false}
              style={{ textDecoration: "none", color: "inherit" }}
            >
              <Group gap="sm" wrap="nowrap">
                <Paper radius="lg" px="sm" py={6} bg="teal.1">
                  <Text
                    size="xs"
                    fw={800}
                    c="teal.8"
                    tt="uppercase"
                    style={{ letterSpacing: "0.12em" }}
                  >
                    Retail
                  </Text>
                </Paper>
                <Box>
                  <Title order={4}>Retention Control Room</Title>
                  <Text size="sm" c="dimmed">
                    Product MVP поверх backend API
                  </Text>
                </Box>
              </Group>
            </Link>
          </Group>
        </Group>
      </MantineAppShell.Header>

      <MantineAppShell.Navbar p="md">
        <ScrollArea type="never" style={{ height: "100%" }}>
          <Stack gap="md" h="100%">
            <Paper withBorder radius="xl" p="md" bg="rgba(255, 250, 243, 0.94)">
              <Stack gap="xs">
                <Group gap="sm">
                  <IconPresentationAnalytics size={18} color="#0f766e" />
                  <Text fw={700}>Один сценарий вместо BI-конструктора</Text>
                </Group>
                <Text size="sm" c="dimmed">
                  Фронт показывает клиентский цикл: аналитика, churn-сигнал,
                  рекомендация и действие.
                </Text>
              </Stack>
            </Paper>
            <Divider />
            <Stack gap={6} style={{ flex: 1 }}>
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.href}
                    component={Link}
                    href={item.href}
                    active={isItemActive(pathname, item.href)}
                    label={item.label}
                    description={item.hint}
                    leftSection={<Icon size={18} />}
                    variant="filled"
                    color="teal"
                    prefetch={false}
                    onClick={() => close()}
                    styles={{
                      root: {
                        borderRadius: 18,
                      },
                    }}
                  />
                );
              })}
            </Stack>
            <Paper withBorder radius="xl" p="md" bg="rgba(15, 118, 110, 0.07)">
              <Stack gap={6}>
                <Text fw={700}>Что здесь важно</Text>
                <Text size="sm" c="dimmed">
                  Никаких ad hoc дашбордов. Только product-facing экраны для
                  демонстрации бизнес-сценария.
                </Text>
              </Stack>
            </Paper>
          </Stack>
        </ScrollArea>
      </MantineAppShell.Navbar>

      <MantineAppShell.Main>
        <Box
          maw={isDeepDivePage ? "none" : 1440}
          mx={isDeepDivePage ? 0 : "auto"}
        >
          {children}
        </Box>
      </MantineAppShell.Main>
    </MantineAppShell>
  );
}
