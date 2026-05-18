import NextLink from "next/link";
import {
  Box,
  Heading,
  Link,
  Stack,
  Text
} from "@chakra-ui/react";

import { equityCoverage } from "../../features/site-shell/mvd-data";

export default function EquityMarketsPage() {
  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Stack gap="4" maxW="4xl">
        <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Global Equity Valuation Desk
        </Text>
        <Heading as="h1" fontSize={{ base: "4xl", md: "5xl" }} lineHeight="0.98">
          Equity Markets
        </Heading>
        <Text color="muted" fontSize={{ base: "lg", md: "xl" }} maxW="4xl">
          Broad-market valuation overview across the main reference indexes.
        </Text>
      </Stack>

      <Stack bg="surface" borderColor="edge" borderWidth="1px" gap="0" rounded="panel">
        <Text
          color="muted"
          fontSize="xs"
          letterSpacing="0.16em"
          px={{ base: "5", md: "6" }}
          pt={{ base: "5", md: "6" }}
          textTransform="uppercase"
        >
          Coverage shortlist
        </Text>
        <Box as="table" role="table" w="full" borderCollapse="collapse">
          <Box as="tbody">
            {equityCoverage.map((market, index) => (
              <Box as="tr" key={market.slug}>
                <Box as="td" p="0" borderBottomWidth={index === equityCoverage.length - 1 ? "0" : "1px"} borderColor="edge">
                  <Link
                    asChild
                    display="block"
                    textDecoration="none"
                    _hover={{ textDecoration: "none" }}
                  >
                    <NextLink href={`/equity-markets/${market.slug}`}>
                      <Box
                        display="grid"
                        gridTemplateColumns={{ base: "1fr", md: "1.2fr 0.8fr" }}
                        gap="4"
                        px={{ base: "5", md: "6" }}
                        py={{ base: "4", md: "5" }}
                        transition="background-color 0.2s ease"
                        _hover={{ bg: "surfaceRaised" }}
                      >
                        <Stack gap="1">
                          <Text fontWeight="semibold">{market.market}</Text>
                          <Text color="muted" fontSize="sm">
                            {market.region} · {market.ticker}
                          </Text>
                        </Stack>
                        <Text color="accent" fontSize="sm" textAlign={{ base: "left", md: "right" }}>
                          {market.posture}
                        </Text>
                      </Box>
                    </NextLink>
                  </Link>
                </Box>
              </Box>
            ))}
          </Box>
        </Box>
      </Stack>
    </Stack>
  );
}
