"use client";

import Link from "next/link";
import { ReactNode } from "react";

import {
  Box,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import { IconArrowUpRight, IconChevronRight } from "@tabler/icons-react";

type MetricTileProps = {
  label: string;
  value: ReactNode;
  help?: ReactNode;
  icon?: ReactNode;
  tone?: "neutral" | "brand" | "accent" | "danger";
};

const toneStyles: Record<
  NonNullable<MetricTileProps["tone"]>,
  { bg: string; border: string }
> = {
  neutral: { bg: "rgba(255,255,255,0.78)", border: "rgba(63, 52, 41, 0.10)" },
  brand: { bg: "rgba(15, 118, 110, 0.10)", border: "rgba(15, 118, 110, 0.18)" },
  accent: {
    bg: "rgba(197, 107, 34, 0.10)",
    border: "rgba(197, 107, 34, 0.18)",
  },
  danger: { bg: "rgba(159, 45, 45, 0.10)", border: "rgba(159, 45, 45, 0.18)" },
};

export function MetricTile({
  label,
  value,
  help,
  icon,
  tone = "neutral",
}: MetricTileProps) {
  const style = toneStyles[tone];

  return (
    <Paper
      withBorder
      radius="xl"
      p="lg"
      h="100%"
      style={{ background: style.bg, borderColor: style.border }}
    >
      <Stack gap="sm">
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <Text size="sm" c="dimmed" fw={600}>
            {label}
          </Text>
          {icon ? (
            <ThemeIcon
              size={38}
              radius="md"
              variant="light"
              color={
                tone === "accent"
                  ? "orange"
                  : tone === "danger"
                    ? "red"
                    : "teal"
              }
            >
              {icon}
            </ThemeIcon>
          ) : null}
        </Group>
        <Title order={3} style={{ lineHeight: 1.02 }}>
          {value}
        </Title>
        {help ? (
          <Text size="sm" c="dimmed">
            {help}
          </Text>
        ) : null}
      </Stack>
    </Paper>
  );
}

type PageHeroProps = {
  eyebrow: string;
  title: string;
  description: ReactNode;
  aside?: ReactNode;
};

export function PageHero({
  eyebrow,
  title,
  description,
  aside,
}: PageHeroProps) {
  return (
    <Paper
      withBorder
      radius={28}
      p={{ base: "lg", md: "xl" }}
      shadow="sm"
      style={{
        background:
          "radial-gradient(circle at top right, rgba(15, 118, 110, 0.12), transparent 28%), linear-gradient(180deg, rgba(255, 250, 243, 0.95), rgba(255, 244, 230, 0.92))",
      }}
    >
      <SimpleGrid cols={{ base: 1, md: 2 }} spacing="xl" verticalSpacing="xl">
        <Stack gap="md">
          <Text
            tt="uppercase"
            fw={800}
            size="xs"
            c="teal.7"
            style={{ letterSpacing: "0.12em" }}
          >
            {eyebrow}
          </Text>
          <Title
            order={1}
            size="clamp(2.2rem, 4vw, 4.3rem)"
            style={{ lineHeight: 0.95, letterSpacing: "-0.04em" }}
          >
            {title}
          </Title>
          <Text size="lg" c="dimmed" maw={760}>
            {description}
          </Text>
        </Stack>
        {aside ? <Box>{aside}</Box> : <div />}
      </SimpleGrid>
    </Paper>
  );
}

type SectionCardProps = {
  eyebrow: string;
  title: string;
  action?: ReactNode;
  children: ReactNode;
};

export function SectionCard({
  eyebrow,
  title,
  action,
  children,
}: SectionCardProps) {
  return (
    <Paper withBorder radius="xl" p="lg" shadow="sm" h="100%">
      <Stack gap="lg">
        <Group justify="space-between" align="flex-start">
          <Stack gap={4}>
            <Text
              tt="uppercase"
              fw={800}
              size="xs"
              c="teal.7"
              style={{ letterSpacing: "0.12em" }}
            >
              {eyebrow}
            </Text>
            <Title order={3}>{title}</Title>
          </Stack>
          {action}
        </Group>
        {children}
      </Stack>
    </Paper>
  );
}

type FeatureLinkCardProps = {
  href: string;
  eyebrow: string;
  title: string;
  description: string;
  icon: ReactNode;
};

export function FeatureLinkCard({
  href,
  eyebrow,
  title,
  description,
  icon,
}: FeatureLinkCardProps) {
  return (
    <Link
      href={href}
      prefetch={false}
      style={{ textDecoration: "none", color: "inherit" }}
    >
      <Paper
        withBorder
        radius="xl"
        p="lg"
        shadow="sm"
        h="100%"
        style={{
          background: "rgba(255, 252, 247, 0.86)",
          transition:
            "transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease",
        }}
      >
        <Stack gap="md" h="100%">
          <Group justify="space-between" align="flex-start">
            <ThemeIcon size={44} radius="lg" variant="light" color="teal">
              {icon}
            </ThemeIcon>
            <ThemeIcon size={34} radius="lg" variant="subtle" color="gray">
              <IconArrowUpRight size={18} />
            </ThemeIcon>
          </Group>
          <Stack gap={6} style={{ flex: 1 }}>
            <Text
              tt="uppercase"
              fw={800}
              size="xs"
              c="teal.7"
              style={{ letterSpacing: "0.12em" }}
            >
              {eyebrow}
            </Text>
            <Title order={3}>{title}</Title>
            <Text c="dimmed">{description}</Text>
          </Stack>
        </Stack>
      </Paper>
    </Link>
  );
}

type InlineActionLinkProps = {
  href: string;
  label: string;
};

export function InlineActionLink({ href, label }: InlineActionLinkProps) {
  return (
    <Link
      href={href}
      prefetch={false}
      style={{ textDecoration: "none", color: "inherit" }}
    >
      <Group gap={6} wrap="nowrap">
        <Text fw={600} c="teal.7">
          {label}
        </Text>
        <IconChevronRight size={16} color="#0f766e" />
      </Group>
    </Link>
  );
}
