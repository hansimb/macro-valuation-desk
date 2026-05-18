import type { PropsWithChildren } from "react";
import NextLink from "next/link";
import { Box, Container, Flex, Link, Stack, Text } from "@chakra-ui/react";

import { SiteFooter } from "./footer";
import { MobileNav } from "./mobile-nav";
import { SiteNavigation } from "./navigation";

export function LayoutShell({ children }: PropsWithChildren) {
  return (
    <Box
      minH="100vh"
      bg="canvas"
      color="text"
      position="relative"
      _before={{
        content: '""',
        position: "absolute",
        top: "-4rem",
        left: "50%",
        transform: "translateX(-50%)",
        width: "100vw",
        height: { base: "38rem", md: "46rem" },
        background:
          "radial-gradient(68% 58% at 18% 8%, rgba(138, 223, 229, 0.14) 0%, rgba(138, 223, 229, 0.08) 34%, rgba(138, 223, 229, 0.025) 60%, transparent 80%), radial-gradient(42% 34% at 82% 10%, rgba(238, 242, 255, 0.08) 0%, rgba(238, 242, 255, 0.03) 42%, transparent 74%)",
        filter: "blur(28px)",
        pointerEvents: "none",
        zIndex: 0
      }}
      _after={{
        content: '""',
        position: "absolute",
        inset: "0",
        backgroundImage:
          "linear-gradient(rgba(255,255,255,0.018) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.018) 1px, transparent 1px)",
        backgroundSize: "32px 32px",
        opacity: 0.18,
        pointerEvents: "none",
        zIndex: 0
      }}
    >
      <Container
        maxW="6xl"
        px={{ base: 4, md: 6 }}
        py={{ base: 4, md: 6 }}
        position="relative"
        zIndex={1}
      >
        <Flex
          as="nav"
          align="center"
          borderBottomWidth="1px"
          borderColor="edge"
          gap={{ base: 3, md: 6 }}
          justify="space-between"
          pb={4}
          wrap="nowrap"
        >
          <Link
            asChild
            color="text"
            css={{ WebkitTapHighlightColor: "transparent" }}
            fontSize="sm"
            fontWeight="700"
            letterSpacing="0"
            textDecoration="none"
            flex="1 1 auto"
            minW={0}
          >
            <NextLink href="/">
              <Stack gap="0" maxW="100%">
                <Text lineHeight="1.15">Macro Valuation Desk</Text>
                <Text color="muted" fontSize={{ base: "10px", md: "xs" }} fontWeight="400">
                  Macro context and equity valuation framing
                </Text>
              </Stack>
            </NextLink>
          </Link>
          <Flex align="center" display={{ base: "none", md: "flex" }} gap={4}>
            <SiteNavigation />
          </Flex>
          <Flex align="center" display={{ base: "flex", md: "none" }} gap={1}>
            <MobileNav />
          </Flex>
        </Flex>

        <Box as="main" py={{ base: 10, md: 14 }}>
          {children}
        </Box>

        <SiteFooter />
      </Container>
    </Box>
  );
}
