import NextLink from "next/link";
import { Heading, Link, SimpleGrid, Stack, Text } from "@chakra-ui/react";

const overviewCards = [
  {
    eyebrow: "Macro",
    label: "GDP growth",
    value: "2.1%",
    detail: "Direction, change, and regional framing.",
  },
  {
    eyebrow: "Macro",
    label: "CPI",
    value: "2.9%",
    detail: "Inflation path, breadth, and persistence.",
  },
  {
    eyebrow: "Equity",
    label: "S&P 500 P/E",
    value: "24.1x",
    detail: "Valuation level, history, and posture.",
  },
  {
    eyebrow: "Equity",
    label: "STOXX Europe 600 P/E",
    value: "14.8x",
    detail: "Cross-market context and valuation posture.",
  },
];

const sectionEntries = [
  {
    href: "/macro",
    label: "Macro",
    title: "Six driver families.",
    description: "Liquidity, credit, inflation, demand, trade, and housing.",
  },
  {
    href: "/equity-markets",
    label: "Equity Markets",
    title: "Main index shortlist.",
    description: "Broad-market valuation across the main reference indexes.",
  },
];

export default function HomePage() {
  return (
    <Stack gap={{ base: "12", md: "16" }}>
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
          Market valuation analysis
        </Text>
        <Heading
          as="h1"
          fontSize={{ base: "4xl", md: "6xl" }}
          lineHeight="0.98"
          maxW="5xl"
        >
          Insights from macroeconomics and equity market valuations
        </Heading>
        <Text
          color="muted"
          fontSize={{ base: "lg", md: "xl" }}
          lineHeight="1.5"
          maxW="3xl"
        >
          Philosophy: analysis guided by the Pareto principle, focusing on the
          most important factors, supported by economic reasoning, statistical
          thinking, and real data.
        </Text>
      </Stack>

      <Stack gap="5">
        <Text
          color="muted"
          fontSize="xs"
          letterSpacing="0.16em"
          textTransform="uppercase"
        >
          Overview
        </Text>
        <SimpleGrid columns={{ base: 1, md: 2, xl: 4 }} gap="4">
          {overviewCards.map((card) => (
            <Stack
              key={`${card.eyebrow}-${card.label}`}
              bg="surface"
              borderColor="edge"
              borderWidth="1px"
              gap="3"
              minH="12rem"
              p={{ base: "5", md: "6" }}
              rounded="panel"
              transition="border-color 0.2s ease"
              _hover={{ borderColor: "rgba(138, 223, 229, 0.72)" }}
            >
              <Text
                color="accent"
                fontSize="xs"
                letterSpacing="0.16em"
                textTransform="uppercase"
              >
                {card.eyebrow}
              </Text>
              <Text
                color="muted"
                fontSize="xs"
                letterSpacing="0.16em"
                textTransform="uppercase"
              >
                {card.label}
              </Text>
              <Heading
                as="h2"
                fontSize={{ base: "2xl", md: "3xl" }}
                lineHeight="1"
              >
                {card.value}
              </Heading>
              <Text color="muted" fontSize="sm">
                {card.detail}
              </Text>
            </Stack>
          ))}
        </SimpleGrid>
      </Stack>

      <Stack gap="5">
        <Text
          color="muted"
          fontSize="xs"
          letterSpacing="0.16em"
          textTransform="uppercase"
        >
          Sections
        </Text>
        <SimpleGrid columns={{ base: 1, xl: 2 }} gap="6">
          {sectionEntries.map((entry) => (
            <Link
              asChild
              key={entry.href}
              display="block"
              textDecoration="none"
              w="full"
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
                  _hover={{
                    borderColor: "accent",
                    transform: "translateY(-2px)",
                  }}
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
                    <Heading
                      as="h2"
                      fontSize={{ base: "2xl", md: "3xl" }}
                      lineHeight="1.05"
                    >
                      {entry.title}
                    </Heading>
                    <Text color="muted" maxW="2xl">
                      {entry.description}
                    </Text>
                  </Stack>
                </Stack>
              </NextLink>
            </Link>
          ))}
        </SimpleGrid>
      </Stack>
    </Stack>
  );
}
