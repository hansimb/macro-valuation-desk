import NextLink from "next/link";
import { Flex, Link, Stack, Text } from "@chakra-ui/react";

import { siteNavigationItems } from "./navigation-items";

export function SiteFooter() {
  return (
    <Flex
      as="footer"
      borderTopWidth="1px"
      borderColor="border.default"
      color="fg.muted"
      fontSize="sm"
      gap={4}
      justify="space-between"
      pt={4}
      wrap={{ base: "wrap", md: "nowrap" }}
    >
      <Stack gap={2} maxW="2xl">
        <Text color="fg.default">
          Macro Valuation Desk is a research-oriented workspace for fast macro context and
          serious broad-market valuation framing.
        </Text>
        <Flex align="center" color="fg.muted" fontSize="sm" gap={4} wrap="wrap">
          {siteNavigationItems.map((item) => (
            <Link
              asChild
              color="fg.muted"
              key={item.href}
              textDecoration="none"
              _hover={{ color: "accent" }}
            >
              <NextLink href={item.href}>{item.label}</NextLink>
            </Link>
          ))}
        </Flex>
      </Stack>
      <Stack align={{ base: "start", md: "end" }} gap={1}>
        <Text color="fg.default">Phase 1 Skeleton</Text>
        <Text>Methodology-first placeholders. Models and formulas come next.</Text>
      </Stack>
    </Flex>
  );
}
