"use client";

import { ChakraProvider } from "@chakra-ui/react";
import React, { type PropsWithChildren } from "react";

import { EmotionRegistry } from "./emotion-registry";
import { mvdSystem } from "./system";

export function ThemeProvider({ children }: PropsWithChildren) {
  return (
    <EmotionRegistry>
      <ChakraProvider value={mvdSystem}>{children}</ChakraProvider>
    </EmotionRegistry>
  );
}
