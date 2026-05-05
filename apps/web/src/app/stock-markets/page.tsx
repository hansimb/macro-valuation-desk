import { Heading, Stack, Text } from "@chakra-ui/react";

export default function StockMarketsPage() {
  return (
    <Stack gap="4" px={{ base: "6", md: "10" }} py={{ base: "10", md: "14" }}>
      <Heading size="xl">Stock Markets</Heading>
      <Text color="fg.muted">
        The stock markets section will focus on market-level valuation context, not broad single-stock coverage.
      </Text>
    </Stack>
  );
}
