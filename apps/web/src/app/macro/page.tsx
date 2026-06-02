import React from "react";
import NextLink from "next/link";
import { Heading, Link, Stack, Text } from "@chakra-ui/react";

import { macroAnalyses } from "../../features/site-shell/mvd-data";

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
          Macro analysis and research notes.
        </Text>
      </Stack>

      <Stack gap="5">
        <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Analysis
        </Text>
        {macroAnalyses.length === 0 ? (
          <Stack
            bg="surface"
            borderColor="edge"
            borderWidth="1px"
            gap="3"
            minH="12rem"
            justify="center"
            p={{ base: "6", md: "7" }}
            rounded="panel"
          >
            <Heading as="h2" fontSize={{ base: "2xl", md: "3xl" }} lineHeight="1.05">
              No analysis yet
            </Heading>
            <Text color="muted" maxW="2xl">
              New macro analysis pages will appear here once the first published work is ready.
            </Text>
          </Stack>
        ) : (
          <Stack gap="4">
            {macroAnalyses.map((analysis) => (
              <Link
                asChild
                key={analysis.slug}
                display="block"
                textDecoration="none"
                _hover={{ textDecoration: "none" }}
              >
                <NextLink href={`/macro/${analysis.slug}`}>
                  <Stack
                    bg="surface"
                    borderColor="edge"
                    borderWidth="1px"
                    gap="3"
                    p={{ base: "6", md: "7" }}
                    rounded="panel"
                    transition="border-color 0.2s ease, transform 0.2s ease"
                    _hover={{ borderColor: "accent", transform: "translateY(-2px)" }}
                  >
                    <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                      {analysis.eyebrow}
                    </Text>
                    <Heading as="h2" fontSize={{ base: "2xl", md: "3xl" }} lineHeight="1.05">
                      {analysis.title}
                    </Heading>
                    <Text color="muted">{analysis.summary}</Text>
                    <Text color="muted" fontSize="sm">
                      {analysis.cue}
                    </Text>
                  </Stack>
                </NextLink>
              </Link>
            ))}
          </Stack>
        )}
      </Stack>
    </Stack>
  );
}
