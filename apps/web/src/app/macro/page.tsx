import {
  Box,
  Grid,
  Heading,
  HStack,
  SimpleGrid,
  Stack,
  Text
} from "@chakra-ui/react";

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
    // Keep the page renderable before the API is live.
  }

  return {
    asOf: "2026-05-01",
    metrics: [
      { label: "GDP growth", value: "2.1%" },
      { label: "CPI", value: "2.9%" },
      { label: "Policy rate", value: "5.50%" },
      { label: "Labor anchor", value: "4.2%" }
    ]
  };
}

const regions = ["World", "USA", "Euro Area", "China", "Asia ex-China"];

const drivers = [
  {
    title: "Liquidity and Money Impulse",
    summary: "Money and credit conditions still matter before the headline economy catches up.",
    cue: "Liquidity pulse stabilizing"
  },
  {
    title: "Credit Conditions and Financing Stress",
    summary: "The financing channel is often where policy becomes real economic pressure.",
    cue: "Credit stress elevated"
  },
  {
    title: "Price Pressure Pipeline",
    summary: "Inflation should be read upstream, not only at the CPI print.",
    cue: "Pipeline cooling unevenly"
  },
  {
    title: "Consumer Behavior and Demand Resilience",
    summary: "Demand resilience helps reveal whether the cycle is broadening or tiring.",
    cue: "Consumer resilience narrowing"
  },
  {
    title: "Industrial and Trade Pulse",
    summary: "Goods demand and export sensitivity still anchor the global cycle.",
    cue: "Trade pulse mixed"
  },
  {
    title: "Housing and Construction Transmission",
    summary: "Housing remains one of the clearest rate-sensitive transmission paths.",
    cue: "Construction drag persistent"
  }
];

const drilldownBlocks = [
  {
    title: "Full chart sets",
    detail: "Each driver will expand into deeper time-series work rather than staying a thumbnail-only box."
  },
  {
    title: "Causal rationale",
    detail: "Every major signal should say why it matters in the transmission chain, not just that it moved."
  },
  {
    title: "Source and update notes",
    detail: "The drilldown layer will expose source quality, update rhythm, and regional comparability limits."
  },
  {
    title: "Caveats and revision risk",
    detail: "MVD should surface weaknesses plainly so summary signals never masquerade as certainty."
  }
];

export default async function MacroPage() {
  const overview = await getMacroOverview();

  return (
    <Stack gap={{ base: "10", md: "14" }}>
      <Grid gap="8" templateColumns={{ base: "1fr", xl: "1.15fr 0.85fr" }}>
        <Stack gap="5">
          <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
            Macro Workspace
          </Text>
          <Heading as="h1" fontSize={{ base: "4xl", md: "5xl" }} lineHeight="0.98">
            Macro
          </Heading>
          <Text color="muted" fontSize={{ base: "lg", md: "xl" }} maxW="3xl">
            A Pareto-first macro page organized around the small set of drivers that matter most
            for cycle direction, inflation path, financing conditions, and real-economy sensitivity.
          </Text>
        </Stack>

        <Stack
          bg="surface"
          borderColor="edge"
          borderWidth="1px"
          gap="4"
          p={{ base: "5", md: "6" }}
          rounded="panel"
        >
          <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
            Page posture
          </Text>
          <Text>Headline layer</Text>
          <Text>Driver analysis</Text>
          <Text>Drilldown-oriented methodology</Text>
          <Text color="muted" fontSize="sm">
            As of {overview.asOf}
          </Text>
        </Stack>
      </Grid>

      <Stack gap="5">
        <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Headline layer
        </Text>
        <HStack flexWrap="wrap" gap="3" align="stretch">
          {regions.map((region) => (
            <Box
              key={region}
              borderColor="edge"
              borderWidth="1px"
              color={region === "World" ? "accent" : "muted"}
              px="3"
              py="2"
              rounded="control"
            >
              <Text fontSize="sm">{region}</Text>
            </Box>
          ))}
        </HStack>
        <SimpleGrid columns={{ base: 1, md: 2, xl: 4 }} gap="4">
          {overview.metrics.map((metric) => (
            <Stack
              key={metric.label}
              bg="surface"
              borderColor="edge"
              borderWidth="1px"
              gap="2"
              minH="9rem"
              p={{ base: "5", md: "6" }}
              rounded="panel"
            >
              <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                {metric.label}
              </Text>
              <Heading as="h2" fontSize={{ base: "2xl", md: "3xl" }} lineHeight="1">
                {metric.value}
              </Heading>
              <Text color="muted" fontSize="sm">
                Placeholder context for directionality, change, and regional framing.
              </Text>
            </Stack>
          ))}
        </SimpleGrid>
      </Stack>

      <Stack gap="5">
        <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Driver analysis
        </Text>
        <SimpleGrid columns={{ base: 1, xl: 2 }} gap="5">
          {drivers.map((driver, index) => (
            <Stack
              key={driver.title}
              bg="surface"
              borderColor="edge"
              borderWidth="1px"
              gap="4"
              p={{ base: "5", md: "6" }}
              rounded="panel"
            >
              <HStack justify="space-between" align="start">
                <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                  Driver {index + 1}
                </Text>
                <Text color="muted" fontSize="sm">
                  {driver.cue}
                </Text>
              </HStack>
              <Heading as="h2" fontSize={{ base: "2xl", md: "3xl" }} lineHeight="1.05">
                {driver.title}
              </Heading>
              <Text color="muted">{driver.summary}</Text>
              <Box
                bg="surfaceRaised"
                borderColor="edge"
                borderWidth="1px"
                h="5.5rem"
                position="relative"
                rounded="control"
              >
                <Box
                  bg="linear-gradient(90deg, rgba(138,223,229,0.05), rgba(138,223,229,0.35), rgba(138,223,229,0.08))"
                  bottom="1rem"
                  height="2px"
                  left="1rem"
                  position="absolute"
                  right="1rem"
                />
                <Box
                  bg="accent"
                  bottom="1rem"
                  clipPath="polygon(0 80%, 12% 62%, 24% 68%, 38% 36%, 52% 44%, 66% 18%, 78% 30%, 100% 0, 100% 100%, 0 100%)"
                  left="1rem"
                  opacity="0.28"
                  position="absolute"
                  right="1rem"
                  top="1rem"
                />
              </Box>
              <Text color="muted" fontSize="sm">
                Methodology placeholder: show strongest candidate metrics, signal summary, and later
                drilldown entry points without pretending the model is finished.
              </Text>
            </Stack>
          ))}
        </SimpleGrid>
      </Stack>

      <Stack gap="5">
        <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Drilldown-oriented layer
        </Text>
        <SimpleGrid columns={{ base: 1, md: 2, xl: 4 }} gap="4">
          {drilldownBlocks.map((block) => (
            <Stack
              key={block.title}
              bg="surface"
              borderColor="edge"
              borderWidth="1px"
              gap="3"
              p={{ base: "5", md: "6" }}
              rounded="panel"
            >
              <Heading as="h3" fontSize="xl">
                {block.title}
              </Heading>
              <Text color="muted">{block.detail}</Text>
            </Stack>
          ))}
        </SimpleGrid>
      </Stack>
    </Stack>
  );
}
