import React from "react";
import NextLink from "next/link";
import { Link } from "@chakra-ui/react";

type BackLinkProps = {
  href: string;
  label: string;
};

export function BackLink({ href, label }: BackLinkProps) {
  return (
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
      <NextLink href={href}>← {label}</NextLink>
    </Link>
  );
}
