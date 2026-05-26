import NextLink from "next/link";
import { Flex, Link, Stack, Text } from "@chakra-ui/react";

import { siteNavigationItems } from "./navigation-items";

export function SiteFooter() {
  return (
    <Flex
      as="footer"
      borderTopWidth="1px"
      borderColor="edge"
      color="muted"
      fontSize="sm"
      gap={4}
      justify="space-between"
      pt={4}
      wrap={{ base: "wrap", md: "nowrap" }}
    >
      <Stack gap={2} maxW="2xl">
        <Text color="text">
          Personal market analysis with transparent reasoning and updateable data workflows.
        </Text>
        <Flex align="center" color="muted" fontSize="sm" gap={4} wrap="wrap">
          {siteNavigationItems.map((item) => (
            <Link
              asChild
              color="muted"
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
        <Text color="text">Research and build by Hans Imberg</Text>
        <Link
          color="muted"
          href="https://imberg.dev/"
          target="_blank"
          rel="noreferrer"
          _hover={{ color: "accent" }}
        >
          https://imberg.dev/
        </Link>
      </Stack>
    </Flex>
  );
}
