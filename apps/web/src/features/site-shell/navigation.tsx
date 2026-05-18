"use client";

import NextLink from "next/link";
import { usePathname } from "next/navigation";
import { Flex, Link } from "@chakra-ui/react";

import { siteNavigationItems } from "./navigation-items";

export function SiteNavigation() {
  const pathname = usePathname();

  return (
    <Flex
      align="center"
      flexShrink={0}
      gap={{ base: 2, md: 5 }}
      wrap="nowrap"
      whiteSpace="nowrap"
    >
      {siteNavigationItems.map((item) => {
        const isActive =
          pathname === item.href ||
          (item.href !== "/" && pathname.startsWith(item.href));

        return (
          <Link
            asChild
            color={isActive ? "accent" : "muted"}
            fontSize={{ base: "xs", md: "sm" }}
            key={item.href}
            textDecoration="none"
            _hover={{ color: "accent" }}
          >
            <NextLink href={item.href}>{item.label}</NextLink>
          </Link>
        );
      })}
    </Flex>
  );
}
