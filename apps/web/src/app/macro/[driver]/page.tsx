import { notFound } from "next/navigation";
import { Box, Heading, Stack, Text } from "@chakra-ui/react";

import { BackLink } from "../../../features/site-shell/back-link";
import { macroAnalyses } from "../../../features/site-shell/mvd-data";

export function generateStaticParams() {
  return macroAnalyses.map((analysis) => ({ driver: analysis.slug }));
}

export default async function MacroDriverPage({
  params
}: {
  params: Promise<{ driver: string }>;
}) {
  const { driver } = await params;
  const current = macroAnalyses.find((item) => item.slug === driver);

  if (!current) {
    notFound();
  }

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Stack gap="4" maxW="4xl">
        <BackLink href="/macro" label="Back to Macro" />
        <Text color="accent" textStyle="eyebrow">
          {current.eyebrow}
        </Text>
        <Heading as="h1" textStyle="hero">
          {current.title}
        </Heading>
        <Text color="muted" maxW="3xl" textStyle="subtitle">
          {current.summary}
        </Text>
      </Stack>

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
        <Stack gap="3">
          <Text color="accent" textStyle="eyebrow">
            Current read
          </Text>
          <Text color="muted" textStyle="body">{current.cue}</Text>
          <Text color="muted" textStyle="body">
            This page is reserved for the deeper charts, interpretation, and methodology behind this
            macro driver.
          </Text>
        </Stack>
      </Box>
    </Stack>
  );
}
