import { Heading, SimpleGrid, Stack, Text } from "@chakra-ui/react";

interface MacroOverviewResponse {
  asOf: string;
  metrics: Array<{
    label: string;
    value: string;
  }>;
}

async function getMacroOverview(): Promise<MacroOverviewResponse> {
  const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:4000";

  try {
    const response = await fetch(`${apiBaseUrl}/macro/overview`, {
      cache: "no-store"
    });

    if (response.ok) {
      return (await response.json()) as MacroOverviewResponse;
    }
  } catch {
    // Keep the skeleton page renderable even before the API container is live.
  }

  return {
    asOf: "2026-05-01",
    metrics: [
      { label: "cpi_yoy", value: "2.9" },
      { label: "fed_funds_upper", value: "5.50" },
      { label: "valuation_context", value: "watchful" }
    ]
  };
}

export default async function MacroPage() {
  const overview = await getMacroOverview();

  return (
    <Stack gap="4" px={{ base: "6", md: "10" }} py={{ base: "10", md: "14" }}>
      <Heading size="xl">Macro</Heading>
      <Text color="fg.muted">
        The macro section will become the core view for regime context, inflation, rates, and liquidity.
      </Text>
      <Text fontSize="sm" color="fg.muted">
        As of {overview.asOf}
      </Text>
      <SimpleGrid columns={{ base: 1, md: 3 }} gap="4">
        {overview.metrics.map((metric) => (
          <Stack key={metric.label} rounded="xl" borderWidth="1px" borderColor="blackAlpha.200" p="4">
            <Text fontSize="xs" letterSpacing="0.12em" textTransform="uppercase" color="fg.muted">
              {metric.label}
            </Text>
            <Heading size="md">{metric.value}</Heading>
          </Stack>
        ))}
      </SimpleGrid>
    </Stack>
  );
}
