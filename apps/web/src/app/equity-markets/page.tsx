import React from "react";
import NextLink from "next/link";
import { Box, Heading, Link, Stack, Text } from "@chakra-ui/react";

import { equityMarketAnalyses } from "../../features/site-shell/mvd-data";

export default function EquityMarketsPage() {
  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Stack gap="4" maxW="4xl">
        <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Global Equity Valuation
        </Text>
        <Heading as="h1" fontSize={{ base: "4xl", md: "5xl" }} lineHeight="0.98">
          Equity market index valuation analysis
        </Heading>
        <Text color="muted" fontSize={{ base: "lg", md: "xl" }} maxW="4xl">
          Broad-market valuation overview across the main reference indexes.
        </Text>
      </Stack>

      <Stack bg="surface" borderColor="edge" borderWidth="1px" gap="0" overflowX="auto" rounded="panel">
        {equityMarketAnalyses.length === 0 ? (
          <Stack gap="3" justify="center" minH="12rem" p={{ base: "6", md: "7" }}>
            <Heading as="h2" fontSize={{ base: "2xl", md: "3xl" }} lineHeight="1.05">
              No analysis yet
            </Heading>
            <Text color="muted" maxW="2xl">
              Index valuation analysis pages will appear here once the first market coverage is published.
            </Text>
          </Stack>
        ) : (
          <>
            <Text
              color="muted"
              fontSize="xs"
              letterSpacing="0.16em"
              px={{ base: "5", md: "6" }}
              pt={{ base: "5", md: "6" }}
              textTransform="uppercase"
            >
              Standardized coverage
            </Text>
            <Box as="table" borderCollapse="collapse" role="table" w="full">
              <Box as="thead">
                <Box as="tr">
                  <Box as="th" px={{ base: "5", md: "6" }} py="3" textAlign="left">
                    <Text color="muted" fontSize="xs" fontWeight="500" letterSpacing="0.16em" textTransform="uppercase">
                      Market
                    </Text>
                  </Box>
                  <Box as="th" display={{ base: "none", md: "table-cell" }} px={{ base: "5", md: "6" }} py="3" textAlign="left">
                    <Text color="muted" fontSize="xs" fontWeight="500" letterSpacing="0.16em" textTransform="uppercase">
                      Ticker
                    </Text>
                  </Box>
                  <Box as="th" display={{ base: "none", lg: "table-cell" }} px={{ base: "5", md: "6" }} py="3" textAlign="right">
                    <Text color="muted" fontSize="xs" fontWeight="500" letterSpacing="0.16em" textTransform="uppercase">
                      P/E
                    </Text>
                  </Box>
                  <Box as="th" display={{ base: "none", lg: "table-cell" }} px={{ base: "5", md: "6" }} py="3" textAlign="right">
                    <Text color="muted" fontSize="xs" fontWeight="500" letterSpacing="0.16em" textTransform="uppercase">
                      CAPE
                    </Text>
                  </Box>
                  <Box as="th" display={{ base: "none", xl: "table-cell" }} px={{ base: "5", md: "6" }} py="3" textAlign="right">
                    <Text color="muted" fontSize="xs" fontWeight="500" letterSpacing="0.16em" textTransform="uppercase">
                      P/B
                    </Text>
                  </Box>
                  <Box as="th" px={{ base: "5", md: "6" }} py="3" textAlign="right">
                    <Text color="muted" fontSize="xs" fontWeight="500" letterSpacing="0.16em" textTransform="uppercase">
                      Valuation posture
                    </Text>
                  </Box>
                </Box>
              </Box>
              <Box as="tbody">
                {equityMarketAnalyses.map((market, index) => (
                  <Box as="tr" key={market.slug}>
                    <Box
                      as="td"
                      borderBottomWidth={index === equityMarketAnalyses.length - 1 ? "0" : "1px"}
                      borderColor="edge"
                      px={{ base: "5", md: "6" }}
                      py={{ base: "4", md: "5" }}
                    >
                      <Link
                        asChild
                        color="text"
                        fontWeight="semibold"
                        textDecoration="none"
                        _hover={{ color: "accent", textDecoration: "none" }}
                      >
                        <NextLink href={`/equity-markets/${market.slug}`}>
                          {market.flagEmoji} {market.market}
                        </NextLink>
                      </Link>
                      <Text color="muted" fontSize="sm" mt="1">
                        {market.region}
                      </Text>
                    </Box>
                    <Box
                      as="td"
                      borderBottomWidth={index === equityMarketAnalyses.length - 1 ? "0" : "1px"}
                      borderColor="edge"
                      display={{ base: "none", md: "table-cell" }}
                      px={{ base: "5", md: "6" }}
                      py={{ base: "4", md: "5" }}
                    >
                      <Text color="muted">{market.ticker}</Text>
                    </Box>
                    <Box
                      as="td"
                      borderBottomWidth={index === equityMarketAnalyses.length - 1 ? "0" : "1px"}
                      borderColor="edge"
                      display={{ base: "none", lg: "table-cell" }}
                      px={{ base: "5", md: "6" }}
                      py={{ base: "4", md: "5" }}
                      textAlign="right"
                    >
                      <Text>{market.pe}</Text>
                    </Box>
                    <Box
                      as="td"
                      borderBottomWidth={index === equityMarketAnalyses.length - 1 ? "0" : "1px"}
                      borderColor="edge"
                      display={{ base: "none", lg: "table-cell" }}
                      px={{ base: "5", md: "6" }}
                      py={{ base: "4", md: "5" }}
                      textAlign="right"
                    >
                      <Text>{market.cape}</Text>
                    </Box>
                    <Box
                      as="td"
                      borderBottomWidth={index === equityMarketAnalyses.length - 1 ? "0" : "1px"}
                      borderColor="edge"
                      display={{ base: "none", xl: "table-cell" }}
                      px={{ base: "5", md: "6" }}
                      py={{ base: "4", md: "5" }}
                      textAlign="right"
                    >
                      <Text>{market.pb}</Text>
                    </Box>
                    <Box
                      as="td"
                      borderBottomWidth={index === equityMarketAnalyses.length - 1 ? "0" : "1px"}
                      borderColor="edge"
                      px={{ base: "5", md: "6" }}
                      py={{ base: "4", md: "5" }}
                      textAlign="right"
                    >
                      <Text color="accent" fontSize="sm">
                        {market.posture}
                      </Text>
                    </Box>
                  </Box>
                ))}
              </Box>
            </Box>
          </>
        )}
      </Stack>
    </Stack>
  );
}
