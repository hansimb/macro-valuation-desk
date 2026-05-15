import React from "react";
import {
  Badge,
  Box,
  Grid,
  Heading,
  HStack,
  SimpleGrid,
  Stack,
  Text
} from "@chakra-ui/react";

const valuationStates = [
  "Historically Compressed",
  "Moderately Compressed",
  "Historically Neutral",
  "Moderately Elevated",
  "Historically Elevated"
];

const metricFamilies = [
  {
    title: "Earnings-based",
    detail: "P/E, forward P/E, and cycle-aware earnings framing anchor the broad market read."
  },
  {
    title: "Balance-sheet based",
    detail: "P/B helps separate asset-heavy markets from profit-rich but capital-light ones."
  },
  {
    title: "Sales and cash flow",
    detail: "Price-to-sales and free cash flow yield preserve structure when margins are distorted."
  },
  {
    title: "Macro-relative",
    detail: "Equity yields versus bond yields and Buffett-style context frame discount-rate pressure."
  }
];

const shortlistMarkets = [
  { region: "North America", market: "S&P 500", ticker: "SPX", posture: "Moderately Elevated" },
  { region: "Europe", market: "STOXX Europe 600", ticker: "SXXP", posture: "Historically Neutral" },
  { region: "Nordics", market: "OMX Helsinki 25", ticker: "OMXH25", posture: "Moderately Compressed" },
  { region: "Asia", market: "Nikkei 225", ticker: "N225", posture: "Moderately Elevated" },
  { region: "Asia", market: "Hang Seng Index", ticker: "HSI", posture: "Moderately Compressed" },
  { region: "Oceania", market: "S&P/ASX 200", ticker: "ASX 200", posture: "Historically Neutral" }
];

const overviewPoints = [
  "Multidimensional valuation instead of a single headline multiple",
  "History-first framing with percentile and range context",
  "Methodological honesty about index-native versus ETF-proxy inputs"
];

export default function StockMarketsPage() {
  return (
    <Box
      minH="100vh"
      bgGradient="linear(to-b, white, #f4f1ea 45%, #e7edf5)"
      _dark={{ bgGradient: "linear(to-b, #111827, #172033 45%, #1f2937)" }}
    >
      <Stack gap={{ base: "10", md: "14" }} px={{ base: "6", md: "10" }} py={{ base: "10", md: "14" }}>
        <Grid gap="8" templateColumns={{ base: "1fr", xl: "1.35fr 0.95fr" }} alignItems="start">
          <Stack gap="5">
            <Badge
              alignSelf="flex-start"
              rounded="full"
              px="3"
              py="1"
              colorPalette="orange"
              letterSpacing="0.12em"
              textTransform="uppercase"
            >
              Global Equity Valuation Desk
            </Badge>
            <Stack gap="3">
              <Heading as="h1" size={{ base: "2xl", md: "3xl" }} lineHeight="1.02" maxW="4xl">
                Stock Markets
              </Heading>
              <Text
                fontFamily="heading"
                fontSize={{ base: "xl", md: "2xl" }}
                lineHeight="1.15"
                maxW="4xl"
              >
                Stock-market valuation research built for broad market risk, not single-stock noise.
              </Text>
            </Stack>
            <Text fontSize={{ base: "md", md: "lg" }} color="fg.muted" maxW="3xl">
              This draft turns the stock-markets section into an overview workspace for serious
              valuation framing: multiple lenses, long history, and explicit methodology before
              any market drilldown becomes chart-deep.
            </Text>
            <SimpleGrid columns={{ base: 1, md: 3 }} gap="4">
              {overviewPoints.map((point) => (
                <Box
                  key={point}
                  rounded="panel"
                  borderWidth="1px"
                  borderColor="blackAlpha.200"
                  bg="whiteAlpha.900"
                  p="5"
                  _dark={{ borderColor: "whiteAlpha.200", bg: "whiteAlpha.70" }}
                >
                  <Text fontSize="sm" color="fg.muted">
                    {point}
                  </Text>
                </Box>
              ))}
            </SimpleGrid>
          </Stack>

          <Stack
            gap="5"
            rounded="panel"
            borderWidth="1px"
            borderColor="blackAlpha.200"
            bg="blackAlpha.900"
            color="white"
            p={{ base: "6", md: "7" }}
            _dark={{ borderColor: "whiteAlpha.200", bg: "whiteAlpha.120" }}
          >
            <Text fontSize="xs" letterSpacing="0.16em" textTransform="uppercase" color="whiteAlpha.700">
              Historical Valuation Position
            </Text>
            <Heading size="lg" lineHeight="1.1">
              A navigation aid that summarizes historical positioning without pretending to be fair value.
            </Heading>
            <Text color="whiteAlpha.800">
              The overview layer stays narrow on purpose: it compares current market valuation against
              that market&apos;s own history across the core raw metrics, then expresses the posture
              qualitatively.
            </Text>
            <SimpleGrid columns={{ base: 1, sm: 2 }} gap="3">
              {valuationStates.map((state) => (
                <Box
                  key={state}
                  rounded="xl"
                  borderWidth="1px"
                  borderColor="whiteAlpha.300"
                  bg="whiteAlpha.100"
                  px="4"
                  py="3"
                >
                  <Text fontSize="sm">{state}</Text>
                </Box>
              ))}
            </SimpleGrid>
          </Stack>
        </Grid>

        <SimpleGrid columns={{ base: 1, lg: 2 }} gap="6">
          <Stack
            gap="5"
            rounded="panel"
            borderWidth="1px"
            borderColor="blackAlpha.200"
            bg="bg.panel"
            p={{ base: "6", md: "7" }}
          >
            <Stack gap="2">
              <Text fontSize="xs" letterSpacing="0.16em" textTransform="uppercase" color="fg.muted">
                Core metric families
              </Text>
              <Heading size="lg">Keep the valuation lenses separate before drawing conclusions.</Heading>
            </Stack>
            <Stack gap="4">
              {metricFamilies.map((family) => (
                <Box key={family.title} rounded="xl" bg="bg.subtle" p="4">
                  <Text fontWeight="semibold">{family.title}</Text>
                  <Text mt="2" color="fg.muted">
                    {family.detail}
                  </Text>
                </Box>
              ))}
            </Stack>
          </Stack>

          <Stack
            gap="5"
            rounded="panel"
            borderWidth="1px"
            borderColor="blackAlpha.200"
            bg="bg.panel"
            p={{ base: "6", md: "7" }}
          >
            <Stack gap="2">
              <Text fontSize="xs" letterSpacing="0.16em" textTransform="uppercase" color="fg.muted">
                Coverage shortlist
              </Text>
              <Heading size="lg">Start with serious reference markets, then expand the map later.</Heading>
            </Stack>
            <Stack gap="3">
              {shortlistMarkets.map((market) => (
                <HStack
                  key={`${market.market}-${market.ticker}`}
                  align="start"
                  justify="space-between"
                  rounded="xl"
                  bg="bg.subtle"
                  px="4"
                  py="3"
                  gap="4"
                >
                  <Stack gap="1">
                    <Text fontWeight="semibold">{market.market}</Text>
                    <Text fontSize="sm" color="fg.muted">
                      {market.region} · {market.ticker}
                    </Text>
                  </Stack>
                  <Badge colorPalette="blue" rounded="full" px="3">
                    {market.posture}
                  </Badge>
                </HStack>
              ))}
            </Stack>
          </Stack>
        </SimpleGrid>

        <Grid gap="6" templateColumns={{ base: "1fr", xl: "1.1fr 0.9fr" }}>
          <Stack
            gap="5"
            rounded="panel"
            borderWidth="1px"
            borderColor="blackAlpha.200"
            bg="bg.panel"
            p={{ base: "6", md: "7" }}
          >
            <Stack gap="2">
              <Text fontSize="xs" letterSpacing="0.16em" textTransform="uppercase" color="fg.muted">
                Page structure
              </Text>
              <Heading size="lg">Overview first, drilldown later.</Heading>
            </Stack>
            <SimpleGrid columns={{ base: 1, md: 2 }} gap="4">
              <Box rounded="xl" borderWidth="1px" borderColor="blackAlpha.200" p="4">
                <Text fontWeight="semibold">Map layer</Text>
                <Text mt="2" color="fg.muted">
                  Fast geographic navigation, color-coded by historical posture, with tooltip-level context.
                </Text>
              </Box>
              <Box rounded="xl" borderWidth="1px" borderColor="blackAlpha.200" p="4">
                <Text fontWeight="semibold">Summary table</Text>
                <Text mt="2" color="fg.muted">
                  A compact snapshot layer for index identity, headline valuation posture, and drilldown entry.
                </Text>
              </Box>
              <Box rounded="xl" borderWidth="1px" borderColor="blackAlpha.200" p="4">
                <Text fontWeight="semibold">Valuation drilldown</Text>
                <Text mt="2" color="fg.muted">
                  Raw valuation history, CAPE, and macro-relative analysis live deeper in the research flow.
                </Text>
              </Box>
              <Box rounded="xl" borderWidth="1px" borderColor="blackAlpha.200" p="4">
                <Text fontWeight="semibold">Method notes</Text>
                <Text mt="2" color="fg.muted">
                  Every market should disclose the measured object, source shape, update rhythm, and caveats.
                </Text>
              </Box>
            </SimpleGrid>
          </Stack>

          <Stack
            gap="5"
            rounded="panel"
            borderWidth="1px"
            borderColor="blackAlpha.200"
            bg="#f7efe2"
            p={{ base: "6", md: "7" }}
            _dark={{ bg: "#352919", borderColor: "whiteAlpha.200" }}
          >
            <Stack gap="2">
              <Text fontSize="xs" letterSpacing="0.16em" textTransform="uppercase" color="fg.muted">
                Methodology posture
              </Text>
              <Heading size="lg">No fake precision, no black-box country score.</Heading>
            </Stack>
            <Text color="fg.muted">
              The page should support judgment, not replace it. Historical Valuation Position is allowed as
              an overview helper, but the research experience stays explicit about what it measures and what
              it does not.
            </Text>
            <Stack gap="3">
              <Box rounded="xl" bg="whiteAlpha.700" p="4" _dark={{ bg: "blackAlpha.300" }}>
                <Text fontWeight="semibold">Measured object</Text>
                <Text mt="2" color="fg.muted">
                  Prefer the actual broad market index and clearly disclose any ETF-proxy substitutions.
                </Text>
              </Box>
              <Box rounded="xl" bg="whiteAlpha.700" p="4" _dark={{ bg: "blackAlpha.300" }}>
                <Text fontWeight="semibold">Interpretation discipline</Text>
                <Text mt="2" color="fg.muted">
                  Elevated valuations frame thinner asymmetry and compressed valuations frame better asymmetry,
                  but neither becomes a simplistic buy or sell signal.
                </Text>
              </Box>
            </Stack>
          </Stack>
        </Grid>
      </Stack>
    </Box>
  );
}
