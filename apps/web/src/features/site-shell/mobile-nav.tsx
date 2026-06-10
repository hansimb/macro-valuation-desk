"use client";

import { useState } from "react";
import NextLink from "next/link";
import { usePathname } from "next/navigation";
import {
  Drawer,
  Flex,
  IconButton,
  Link,
  Portal,
  Stack
} from "@chakra-ui/react";

import { siteNavigationItems } from "./navigation-items";

function MenuIcon() {
  return (
    <svg aria-hidden="true" fill="none" height="20" viewBox="0 0 24 24" width="20">
      <path
        d="M4 7h16M4 12h16M4 17h16"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="2.1"
      />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg aria-hidden="true" fill="none" height="18" viewBox="0 0 24 24" width="18">
      <path
        d="M6 6l12 12M18 6 6 18"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="2"
      />
    </svg>
  );
}

export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <Drawer.Root
      lazyMount
      onOpenChange={(details) => setOpen(details.open)}
      open={open}
      placement="end"
    >
      <Drawer.Trigger asChild>
        <IconButton
          aria-label="Open menu"
          color="text"
          display={{ base: "inline-flex", md: "none" }}
          size="sm"
          variant="ghost"
        >
          <MenuIcon />
        </IconButton>
      </Drawer.Trigger>
      <Portal>
        <Drawer.Backdrop bg="rgba(5, 8, 22, 0.7)" />
        <Drawer.Positioner>
          <Drawer.Content
            bg="surface"
            borderColor="edge"
            borderLeftWidth="1px"
            maxW="xs"
          >
            <Drawer.Header alignItems="center" display="flex" justifyContent="space-between">
              <Drawer.Title color="text">Menu</Drawer.Title>
              <Drawer.CloseTrigger asChild>
                <IconButton aria-label="Close menu" color="text" size="sm" variant="ghost">
                  <CloseIcon />
                </IconButton>
              </Drawer.CloseTrigger>
            </Drawer.Header>
            <Drawer.Body>
              <Stack gap={5}>
                <Stack gap={3}>
                  {siteNavigationItems.map((item) => {
                    const isActive =
                      pathname === item.href ||
                      (item.href !== "/" && pathname.startsWith(item.href));

                    return (
                      <Link
                        asChild
                        border="0"
                        color={isActive ? "accent" : "text"}
                        css={{ WebkitTapHighlightColor: "transparent" }}
                        key={item.href}
                        onClick={() => setOpen(false)}
                        textStyle="body"
                        textDecoration="none"
                        _active={{ borderColor: "transparent", boxShadow: "none", color: "accent", outline: "none" }}
                        _focus={{ borderColor: "transparent", boxShadow: "none", outline: "none" }}
                        _focusVisible={{ borderColor: "transparent", boxShadow: "none", outline: "none" }}
                        _hover={{ color: "accent" }}
                      >
                        <NextLink href={item.href}>{item.label}</NextLink>
                      </Link>
                    );
                  })}
                </Stack>
                <Flex borderTopWidth="1px" borderColor="edge" pt="4">
                  <Stack gap="1">
                    <Link asChild color="muted" textDecoration="none" textStyle="caption" _hover={{ color: "accent" }}>
                      <NextLink href="/macro">Research workspace</NextLink>
                    </Link>
                    <Link asChild color="muted" textDecoration="none" textStyle="caption" _hover={{ color: "accent" }}>
                      <NextLink href="/equity-markets">Method-first market framing</NextLink>
                    </Link>
                  </Stack>
                </Flex>
              </Stack>
            </Drawer.Body>
          </Drawer.Content>
        </Drawer.Positioner>
      </Portal>
    </Drawer.Root>
  );
}
