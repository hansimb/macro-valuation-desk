import NextLink from "next/link";
import {
  Box,
  Grid,
  Heading,
  HStack,
  Link,
  SimpleGrid,
  Stack,
  Text
} from "@chakra-ui/react";

const insightStrip = [
  {
    eyebrow: "Macro",
    title: "Credit is tight before damage is obvious",
    detail: "Financing stress usually matters before lagging growth data admits it."
  },
  {
    eyebrow: "Equity",
    title: "Valuation breadth matters more than one multiple",
    detail: "Broad-market pricing needs history, composition, and discount-rate context."
  },
  {
    eyebrow: "Method",
    title: "Signal density over dashboard sprawl",
    detail: "The product stays narrow on purpose and goes deeper where the causal chain is strongest."
  }
];

const sectionEntries = [
  {
    href: "/macro",
    label: "Macro",
    title: "Track the six macro driver families that matter most.",
    description:
      "Follow liquidity, credit, inflation transmission, demand resilience, trade, and housing in a tighter analytic frame."
  },
  {
    href: "/equity-markets",
    label: "Equity Markets",
    title: "Read broad market valuation before you read narratives.",
    description:
      "Use earnings, balance-sheet, cash-flow, and macro-relative lenses to judge broad equity-market risk more seriously."
  }
];

export default function HomePage() {
  return (
    <Stack gap={{ base: "12", md: "16" }}>
      <Grid gap="8" templateColumns={{ base: "1fr", xl: "1.2fr 0.8fr" }} alignItems="end">
        <Stack gap="5" maxW="4xl">
          <Text
            alignSelf="flex-start"
            borderWidth="1px"
            borderColor="accent"
            color="accent"
            fontSize="xs"
            letterSpacing="0.16em"
            px="3"
            py="1"
            textTransform="uppercase"
          >
            Research Product Skeleton
          </Text>
          <Heading as="h1" fontSize={{ base: "4xl", md: "6xl" }} lineHeight="0.98" maxW="5xl">
            Macro and valuation context that makes serious browsing immediately worth it.
          </Heading>
          <Text color="muted" fontSize={{ base: "lg", md: "xl" }} lineHeight="1.5" maxW="3xl">
            Macro Valuation Desk is being built as a tighter research shell for macro regime
            reading and broad equity valuation framing, with less dashboard sprawl and more
            signal discipline.
          </Text>
        </Stack>

        <Stack
          bg="surface"
          borderColor="edge"
          borderWidth="1px"
          gap="4"
          justifySelf="stretch"
          p={{ base: "5", md: "6" }}
          rounded="panel"
        >
          <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
            Fast orientation
          </Text>
          <Stack gap="3">
            <HStack align="start" justify="space-between">
              <Text color="muted" fontSize="sm">
                Macro focus
              </Text>
              <Text fontSize="sm">6 driver families</Text>
            </HStack>
            <HStack align="start" justify="space-between">
              <Text color="muted" fontSize="sm">
                Equity framing
              </Text>
              <Text fontSize="sm">Multi-lens valuation</Text>
            </HStack>
            <HStack align="start" justify="space-between">
              <Text color="muted" fontSize="sm">
                Product posture
              </Text>
              <Text fontSize="sm">Method-first</Text>
            </HStack>
          </Stack>
        </Stack>
      </Grid>

      <SimpleGrid columns={{ base: 1, md: 3 }} gap="4">
        {insightStrip.map((insight) => (
          <Stack
            key={insight.title}
            bg="surface"
            borderColor="edge"
            borderWidth="1px"
            gap="3"
            minH="12rem"
            p={{ base: "5", md: "6" }}
            rounded="panel"
          >
            <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
              {insight.eyebrow}
            </Text>
            <Heading as="h2" fontSize={{ base: "xl", md: "2xl" }} lineHeight="1.05">
              {insight.title}
            </Heading>
            <Text color="muted">{insight.detail}</Text>
          </Stack>
        ))}
      </SimpleGrid>

      <Stack gap="5">
        <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Browse the desk
        </Text>
        <SimpleGrid columns={{ base: 1, xl: 2 }} gap="6">
          {sectionEntries.map((entry) => (
            <Link
              asChild
              key={entry.href}
              textDecoration="none"
              _hover={{ textDecoration: "none" }}
            >
              <NextLink href={entry.href}>
                <Stack
                  bg="surface"
                  borderColor="edge"
                  borderWidth="1px"
                  gap="4"
                  h="full"
                  justify="space-between"
                  p={{ base: "6", md: "7" }}
                  rounded="panel"
                  transition="border-color 0.2s ease, transform 0.2s ease"
                  _hover={{ borderColor: "accent", transform: "translateY(-2px)" }}
                >
                  <Stack gap="4">
                    <Text
                      color="accent"
                      fontSize="xs"
                      letterSpacing="0.16em"
                      textTransform="uppercase"
                    >
                      {entry.label}
                    </Text>
                    <Heading as="h2" fontSize={{ base: "2xl", md: "3xl" }} lineHeight="1.05">
                      {entry.title}
                    </Heading>
                    <Text color="muted" maxW="2xl">
                      {entry.description}
                    </Text>
                  </Stack>
                  <Box borderTopWidth="1px" borderColor="edge" pt="4">
                    <Text color="muted" fontSize="sm">
                      Open section
                    </Text>
                  </Box>
                </Stack>
              </NextLink>
            </Link>
          ))}
        </SimpleGrid>
      </Stack>
    </Stack>
  );
}
