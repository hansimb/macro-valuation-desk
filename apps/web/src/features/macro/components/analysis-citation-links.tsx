"use client";

import React from "react";
import { Box, Link } from "@chakra-ui/react";

export type AnalysisCitationRef = {
  number: number;
  href?: string;
};

export function AnalysisCitationLinks({
  refs,
}: {
  refs: AnalysisCitationRef[];
}) {
  return (
    <Box as="span" ml="1">
      {refs.map((ref) =>
        ref.href ? (
          <Link color="accent" display="inline" fontSize="0.8em" href={ref.href} key={`${ref.number}-${ref.href}`} target="_blank">
            [{ref.number}]
          </Link>
        ) : (
          <Box as="span" color="accent" fontSize="0.8em" key={ref.number}>
            [{ref.number}]
          </Box>
        ),
      )}
    </Box>
  );
}
