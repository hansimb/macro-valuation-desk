import { Heading, Stack, Text } from "@chakra-ui/react";

import { macroDrivers } from "../../features/site-shell/mvd-data";

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
          Analysis-driven macro work without fixed placeholder dashboards.
        </Text>
      </Stack>

      <Stack gap="5">
        <Text color="muted" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Analysis
        </Text>
        {macroDrivers.length === 0 ? (
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
        ) : null}
      </Stack>
    </Stack>
  );
}
