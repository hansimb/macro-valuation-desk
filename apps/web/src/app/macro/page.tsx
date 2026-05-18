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

import { macroDrivers, macroOverviewMetrics } from "../../features/site-shell/mvd-data";

const regions = ["World", "USA", "Euro Area", "China", "Asia ex-China"];

export default function MacroPage() {
  return (
    <Stack gap={{ base: "10", md: "14" }}>
      <Stack gap="4" maxW="4xl">
        <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Macro Workspace
        </Text>
        <Heading as="h1" fontSize={{ base: "4xl", md: "5xl" }} lineHeight="0.98">
          Macro
        </Heading>
        <Text color="muted" fontSize={{ base: "lg", md: "xl" }} maxW="3xl">
          Macro overview built around a small set of drivers and a compact headline layer.
        </Text>
      </Stack>

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
          {macroOverviewMetrics.map((metric) => (
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
                {metric.detail}
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
          {macroDrivers.map((driver, index) => (
            <Link
              asChild
              key={driver.slug}
              display="block"
              h="full"
              textDecoration="none"
              _hover={{ textDecoration: "none" }}
            >
              <NextLink href={`/macro/${driver.slug}`}>
                <Stack
                  bg="surface"
                  borderColor="edge"
                  borderWidth="1px"
                  gap="4"
                  h="full"
                  justify="space-between"
                  minH={{ base: "20rem", xl: "21rem" }}
                  p={{ base: "5", md: "6" }}
                  rounded="panel"
                  transition="border-color 0.2s ease, transform 0.2s ease"
                  _hover={{ borderColor: "accent", transform: "translateY(-2px)" }}
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
                </Stack>
              </NextLink>
            </Link>
          ))}
        </SimpleGrid>
      </Stack>
    </Stack>
  );
}
