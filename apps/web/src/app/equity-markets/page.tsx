import {
  Box,
  Grid,
  Heading,
  HStack,
  SimpleGrid,
  Stack,
  Text
} from "@chakra-ui/react";

const valuationStates = [
  "Historically compressed",
  "Moderately compressed",
  "Historically neutral",
  "Moderately elevated",
  "Historically elevated"
];

const valuationLenses = [
  {
    title: "Earnings-based",
    detail: "Use earnings multiples carefully and keep cycle distortion explicit."
  },
  {
    title: "Balance-sheet based",
    detail: "Asset-heavy markets need a different valuation framing than capital-light ones."
  },
  {
    title: "Sales and cash flow",
    detail: "Sales and cash flow metrics help when margins distort the picture."
  },
  {
    title: "Macro-relative",
    detail: "Market valuation should also be read against discount rates and equity risk premium logic."
  }
];

const shortlistMarkets = [
  { region: "North America", market: "S&P 500", ticker: "SPX", posture: "Moderately elevated" },
  { region: "Europe", market: "STOXX Europe 600", ticker: "SXXP", posture: "Historically neutral" },
  { region: "Nordics", market: "OMX Helsinki 25", ticker: "OMXH25", posture: "Moderately compressed" },
  { region: "Asia", market: "Nikkei 225", ticker: "N225", posture: "Moderately elevated" },
  { region: "Asia", market: "Hang Seng Index", ticker: "HSI", posture: "Moderately compressed" },
  { region: "Oceania", market: "S&P/ASX 200", ticker: "ASX 200", posture: "Historically neutral" }
];

const workflowBlocks = [
  {
    title: "Map layer",
    detail: "Fast geographic entry into broad market posture, built for navigation rather than fake precision."
  },
  {
    title: "Summary table",
    detail: "A compact market snapshot that frames what to open next without turning into a ranking gimmick."
  },
  {
    title: "Valuation drilldown",
    detail: "History, lens separation, and macro-relative context belong deeper in the research flow."
  },
  {
    title: "Method notes",
    detail: "Every market should disclose the measured object, update rhythm, substitutions, and caveats."
  }
];

export default function EquityMarketsPage() {
  return (
    <Stack gap={{ base: "10", md: "14" }}>
      <Grid gap="8" templateColumns={{ base: "1fr", xl: "1.2fr 0.8fr" }} alignItems="start">
        <Stack gap="5">
          <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
            Global Equity Valuation Desk
          </Text>
          <Heading as="h1" fontSize={{ base: "4xl", md: "5xl" }} lineHeight="0.98">
            Equity Markets
          </Heading>
          <Text color="muted" fontSize={{ base: "lg", md: "xl" }} maxW="4xl">
            Broad-market valuation research built for asset allocators and serious value investors,
            not for single-stock noise or simplistic country ranking.
          </Text>
          <SimpleGrid columns={{ base: 1, md: 3 }} gap="4">
            <Stack bg="surface" borderColor="edge" borderWidth="1px" gap="2" p="5" rounded="panel">
              <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                Structure
              </Text>
              <Text>Separate the lenses before drawing conclusions.</Text>
            </Stack>
            <Stack bg="surface" borderColor="edge" borderWidth="1px" gap="2" p="5" rounded="panel">
              <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                History
              </Text>
              <Text>Position markets against their own valuation history first.</Text>
            </Stack>
            <Stack bg="surface" borderColor="edge" borderWidth="1px" gap="2" p="5" rounded="panel">
              <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                Method
              </Text>
              <Text>Keep the measured object and substitution logic explicit.</Text>
            </Stack>
          </SimpleGrid>
        </Stack>

        <Stack
          bg="surface"
          borderColor="edge"
          borderWidth="1px"
          gap="5"
          p={{ base: "6", md: "7" }}
          rounded="panel"
        >
          <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
            Historical valuation position
          </Text>
          <Heading as="h2" fontSize={{ base: "2xl", md: "3xl" }} lineHeight="1.05">
            A navigation aid for historical positioning, not a fake fair-value engine.
          </Heading>
          <Text color="muted">
            The overview layer stays narrow on purpose: compare broad-market valuation against
            that market&apos;s own history and keep the posture qualitative.
          </Text>
          <SimpleGrid columns={{ base: 1, sm: 2 }} gap="3">
            {valuationStates.map((state) => (
              <Box
                key={state}
                bg="surfaceRaised"
                borderColor="edge"
                borderWidth="1px"
                px="4"
                py="3"
                rounded="control"
              >
                <Text fontSize="sm">{state}</Text>
              </Box>
            ))}
          </SimpleGrid>
        </Stack>
      </Grid>

      <SimpleGrid columns={{ base: 1, lg: 2 }} gap="6">
        <Stack
          bg="surface"
          borderColor="edge"
          borderWidth="1px"
          gap="5"
          p={{ base: "6", md: "7" }}
          rounded="panel"
        >
          <Stack gap="2">
            <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
              Valuation lens families
            </Text>
            <Heading as="h2" fontSize="3xl">
              Keep the valuation lenses separate before drawing conclusions.
            </Heading>
          </Stack>
          <Stack gap="4">
            {valuationLenses.map((family) => (
              <Box
                key={family.title}
                bg="surfaceRaised"
                borderColor="edge"
                borderWidth="1px"
                p="4"
                rounded="control"
              >
                <Text fontWeight="semibold">{family.title}</Text>
                <Text color="muted" mt="2">
                  {family.detail}
                </Text>
              </Box>
            ))}
          </Stack>
        </Stack>

        <Stack
          bg="surface"
          borderColor="edge"
          borderWidth="1px"
          gap="5"
          p={{ base: "6", md: "7" }}
          rounded="panel"
        >
          <Stack gap="2">
            <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
              Coverage shortlist
            </Text>
            <Heading as="h2" fontSize="3xl">
              Start with serious reference markets before expanding the map.
            </Heading>
          </Stack>
          <Stack gap="3">
            {shortlistMarkets.map((market) => (
              <HStack
                key={`${market.market}-${market.ticker}`}
                align="start"
                bg="surfaceRaised"
                borderColor="edge"
                borderWidth="1px"
                gap="4"
                justify="space-between"
                px="4"
                py="3"
                rounded="control"
              >
                <Stack gap="1">
                  <Text fontWeight="semibold">{market.market}</Text>
                  <Text color="muted" fontSize="sm">
                    {market.region} · {market.ticker}
                  </Text>
                </Stack>
                <Text color="accent" fontSize="sm">
                  {market.posture}
                </Text>
              </HStack>
            ))}
          </Stack>
        </Stack>
      </SimpleGrid>

      <Grid gap="6" templateColumns={{ base: "1fr", xl: "1.1fr 0.9fr" }}>
        <Stack
          bg="surface"
          borderColor="edge"
          borderWidth="1px"
          gap="5"
          p={{ base: "6", md: "7" }}
          rounded="panel"
        >
          <Stack gap="2">
            <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
              Page structure
            </Text>
            <Heading as="h2" fontSize="3xl">
              Overview first, drilldown later.
            </Heading>
          </Stack>
          <SimpleGrid columns={{ base: 1, md: 2 }} gap="4">
            {workflowBlocks.map((block) => (
              <Box
                key={block.title}
                bg="surfaceRaised"
                borderColor="edge"
                borderWidth="1px"
                p="4"
                rounded="control"
              >
                <Text fontWeight="semibold">{block.title}</Text>
                <Text color="muted" mt="2">
                  {block.detail}
                </Text>
              </Box>
            ))}
          </SimpleGrid>
        </Stack>

        <Stack
          bg="surface"
          borderColor="edge"
          borderWidth="1px"
          gap="5"
          p={{ base: "6", md: "7" }}
          rounded="panel"
        >
          <Stack gap="2">
            <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
              Methodology posture
            </Text>
            <Heading as="h2" fontSize="3xl">
              No fake precision, no black-box market score.
            </Heading>
          </Stack>
          <Text color="muted">
            The page should support judgment, not replace it. Historical valuation position can
            help navigation, but the research experience stays explicit about what it measures and
            what it does not.
          </Text>
          <Stack gap="3">
            <Box
              bg="surfaceRaised"
              borderColor="edge"
              borderWidth="1px"
              p="4"
              rounded="control"
            >
              <Text fontWeight="semibold">Measured object</Text>
              <Text color="muted" mt="2">
                Prefer the actual broad market index and clearly disclose any ETF-proxy substitutions.
              </Text>
            </Box>
            <Box
              bg="surfaceRaised"
              borderColor="edge"
              borderWidth="1px"
              p="4"
              rounded="control"
            >
              <Text fontWeight="semibold">Interpretation discipline</Text>
              <Text color="muted" mt="2">
                Elevated valuations frame thinner asymmetry and compressed valuations frame better
                asymmetry, but neither becomes a simplistic buy or sell signal.
              </Text>
            </Box>
          </Stack>
        </Stack>
      </Grid>
    </Stack>
  );
}
