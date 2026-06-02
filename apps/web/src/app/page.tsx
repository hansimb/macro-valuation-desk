import React from "react";
import NextLink from "next/link";
import { Heading, Link, SimpleGrid, Stack, Text } from "@chakra-ui/react";

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
    title: "Index valuations.",
    description: "Comparable valuation snapshots across the main market indexes."
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
          fontSize="xs"
          letterSpacing="0.16em"
          px="3"
          py="1"
          textTransform="uppercase"
        >
          Market valuation analysis
        </Text>
        <Heading as="h1" fontSize={{ base: "4xl", md: "6xl" }} lineHeight="0.98" maxW="5xl">
          Insights from macroeconomics and equity market valuations
        </Heading>
        <Text color="muted" fontSize={{ base: "lg", md: "xl" }} lineHeight="1.5" maxW="3xl">
          Philosophy: analysis guided by the Pareto principle, focusing on the most important
          factors, supported by economic reasoning, statistical thinking, and real data.
        </Text>
      </Stack>

      <Stack gap="5">
        <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Featured analysis
        </Text>
        <Stack
          bg="surface"
          borderColor="edge"
          borderWidth="1px"
          gap="3"
          minH="12rem"
          justify="center"
          p={{ base: "6", md: "7" }}
          rounded="panel"
        >
          <Heading as="h2" fontSize={{ base: "2xl", md: "3xl" }} lineHeight="1.05">
            No featured analysis yet.
          </Heading>
          <Text color="muted" maxW="2xl">
            Published analyses will appear here once the first macro or market work is ready to be highlighted on the front page.
          </Text>
        </Stack>
      </Stack>

      <Stack gap="5">
        <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
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
                    <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                      {entry.label}
                    </Text>
                    <Heading as="h2" fontSize={{ base: "2xl", md: "3xl" }} lineHeight="1.05">
                      {entry.title}
                    </Heading>
                    {entry.description ? (
                      <Text color="muted" maxW="2xl">
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
