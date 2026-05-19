import NextLink from "next/link";
import { notFound } from "next/navigation";
import {
  Box,
  Heading,
  Link,
  Stack,
  Text
} from "@chakra-ui/react";

import { macroDrivers } from "../../../features/site-shell/mvd-data";

export function generateStaticParams() {
  return macroDrivers.map((driver) => ({ driver: driver.slug }));
}

export default async function MacroDriverPage({
  params
}: {
  params: Promise<{ driver: string }>;
}) {
  const { driver } = await params;
  const current = macroDrivers.find((item) => item.slug === driver);

  if (!current) {
    notFound();
  }

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Stack gap="4" maxW="4xl">
        <Link
          asChild
          alignSelf="flex-start"
          color="muted"
          fontSize="sm"
          gap="2"
          textDecoration="none"
          transition="color 0.2s ease"
          _hover={{ color: "text", textDecoration: "none" }}
        >
          <NextLink href="/macro">← Back to Macro</NextLink>
        </Link>
        <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Macro Driver
        </Text>
        <Heading as="h1" fontSize={{ base: "4xl", md: "5xl" }} lineHeight="0.98">
          {current.title}
        </Heading>
        <Text color="muted" fontSize={{ base: "lg", md: "xl" }} maxW="3xl">
          Analysis coming soon.
        </Text>
      </Stack>

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
        <Stack gap="3">
          <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
            Analysis
          </Text>
          <Text color="muted">
            Detailed charts, interpretation, and methodology for {current.title} are coming soon.
          </Text>
        </Stack>
      </Box>
    </Stack>
  );
}
