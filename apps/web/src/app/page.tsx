import React from "react";
import NextLink from "next/link";
import { Heading, Link, SimpleGrid, Stack, Text } from "@chakra-ui/react";

const featuredAnalysis = {
  href: "/equity-markets/return-expectation",
  eyebrow: "Featured analysis",
  title: "Stock Return Expectation",
  summary: "Compare dividend, earnings-yield, and free-cash-flow return assumptions in one front-end calculator.",
  cue: "Use it as a reusable equity valuation workspace with saved local analyses and transparent input methods."
};

const sectionEntries = [
  {
    href: "/macro",
    label: "Macro",
    title: "Analysis archive.",
    description: "A growing set of reasoning-led macro analyses that update through dedicated data pipelines."
  },
  {
    href: "/equity-markets",
    label: "Equity Markets",
    title: "Analysis archive.",
    description: "Equity analysis tools, calculators, and valuation workups collected in one research archive."
  }
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
          textStyle="eyebrow"
          px="3"
          py="1"
        >
          Market valuation analysis
        </Text>
        <Heading as="h1" maxW="5xl" textStyle="hero">
          Insights from macroeconomics and equity market valuations
        </Heading>
        <Text color="muted" maxW="3xl" textStyle="subtitle">
          Philosophy: analysis guided by the Pareto principle, focusing on the most important
          factors, supported by economic reasoning, statistical thinking, and real data.
        </Text>
      </Stack>

      <Stack gap="5">
        <Text color="muted" textStyle="eyebrow">
          Featured analysis
        </Text>
        <Link asChild display="block" textDecoration="none" w="full" _hover={{ textDecoration: "none" }}>
          <NextLink href={featuredAnalysis.href}>
            <Stack
              bg="surface"
              borderColor="edge"
              borderWidth="1px"
              gap="4"
              minH="12rem"
              justify="center"
              p={{ base: "6", md: "7" }}
              rounded="panel"
              transition="border-color 0.2s ease, transform 0.2s ease"
              _hover={{
                borderColor: "accent",
                transform: "translateY(-2px)"
              }}
            >
              <Text color="accent" textStyle="eyebrow">
                {featuredAnalysis.eyebrow}
              </Text>
              <Heading as="h2" textStyle="title">
                {featuredAnalysis.title}
              </Heading>
              <Text color="muted" maxW="2xl" textStyle="body">
                {featuredAnalysis.summary}
              </Text>
              <Text color="subtle" maxW="2xl" textStyle="small">
                {featuredAnalysis.cue}
              </Text>
            </Stack>
          </NextLink>
        </Link>
      </Stack>

      <Stack gap="5">
        <Text color="muted" textStyle="eyebrow">
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
                    transform: "translateY(-2px)"
                  }}
                >
                  <Stack gap="4">
                    <Text color="accent" textStyle="eyebrow">
                      {entry.label}
                    </Text>
                    <Heading as="h2" textStyle="title">
                      {entry.title}
                    </Heading>
                    {entry.description ? (
                      <Text color="muted" maxW="2xl" textStyle="body">
                        {entry.description}
                      </Text>
                    ) : null}
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
