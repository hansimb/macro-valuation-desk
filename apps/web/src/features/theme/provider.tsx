"use client";

import { ChakraProvider } from "@chakra-ui/react";
import React, { type PropsWithChildren } from "react";

import { mvdSystem } from "./system";

export function ThemeProvider({ children }: PropsWithChildren) {
  return <ChakraProvider value={mvdSystem}>{children}</ChakraProvider>;
}
