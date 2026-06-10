import React from "react";
import NextLink from "next/link";
import { Heading, Link, Stack, Text } from "@chakra-ui/react";

import { macroAnalyses } from "../../features/site-shell/mvd-data";

export default function MacroPage() {
  return (
    <Stack gap={{ base: "10", md: "14" }}>
      <Stack gap="4" maxW="4xl">
        <Text color="accent" textStyle="eyebrow">
          Macro Workspace
        </Text>
        <Heading as="h1" textStyle="hero">
          Macro
        </Heading>
        <Text color="muted" maxW="3xl" textStyle="subtitle">
          Macro analysis and research notes.
        </Text>
      </Stack>

      <Stack gap="5">
        <Text color="muted" textStyle="eyebrow">
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
            <Heading as="h2" textStyle="title">
              No analysis yet
            </Heading>
            <Text color="muted" maxW="2xl" textStyle="body">
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
                    <Text color="accent" textStyle="eyebrow">
                      {analysis.eyebrow}
                    </Text>
                    <Heading as="h2" textStyle="title">
                      {analysis.title}
                    </Heading>
                    <Text color="muted" textStyle="body">{analysis.summary}</Text>
                    <Text color="muted" textStyle="caption">
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
