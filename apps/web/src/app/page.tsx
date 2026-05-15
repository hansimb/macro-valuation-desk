import React from "react";
import { Box, Grid, Heading, Link, Stack, Text } from "@chakra-ui/react";

const sections = [
  {
    href: "/macro",
    title: "Macro",
    description:
      "Track inflation, rates, liquidity, and regime context through a calm institutional lens."
  },
  {
    href: "/stock-markets",
    title: "Stock Markets",
    description:
      "Monitor market-level valuation backdrops, breadth, and the environment for value investors."
  }
];

export default function HomePage() {
  return (
    <Box minH="100vh" bgGradient="linear(to-b, white, gray.100)" _dark={{ bgGradient: "linear(to-b, gray.950, gray.900)" }}>
      <Stack gap="12" maxW="6xl" mx="auto" px={{ base: "6", md: "10" }} py={{ base: "10", md: "16" }}>
        <Stack gap="4" maxW="3xl">
          <Text
            alignSelf="flex-start"
            borderWidth="1px"
            borderColor="blackAlpha.200"
            px="3"
            py="1"
            rounded="full"
            fontSize="sm"
            letterSpacing="0.12em"
            textTransform="uppercase"
          >
            Macro Valuation Desk
          </Text>
          <Heading size="2xl" lineHeight="1.05">
            A serious workspace for macro context and market valuation discipline.
          </Heading>
          <Text fontSize="lg" color="fg.muted">
            MVD is designed for focused investors who want a cleaner read on macro conditions,
            valuation backdrops, and market context without turning the product into a noisy stock screener.
          </Text>
        </Stack>

        <Grid gap="6" templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }}>
          {sections.map((section) => (
            <Link
              key={section.href}
              href={section.href}
              _hover={{ textDecoration: "none", transform: "translateY(-2px)" }}
              transition="all 0.2s ease"
            >
              <Stack
                h="full"
                gap="4"
                rounded="panel"
                borderWidth="1px"
                borderColor="blackAlpha.200"
                bg="whiteAlpha.900"
                p="6"
                shadow="sm"
                _dark={{ borderColor: "whiteAlpha.200", bg: "whiteAlpha.50" }}
              >
                <Text fontSize="xs" letterSpacing="0.16em" textTransform="uppercase" color="fg.muted">
                  Section
                </Text>
                <Heading size="lg">{section.title}</Heading>
                <Text color="fg.muted">{section.description}</Text>
              </Stack>
            </Link>
          ))}
        </Grid>
      </Stack>
    </Box>
  );
}
