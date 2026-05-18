"use client";

import createCache from "@emotion/cache";
import { CacheProvider } from "@emotion/react";
import { useServerInsertedHTML } from "next/navigation";
import React, { type PropsWithChildren, useState } from "react";

type EmotionCacheWithFlush = {
  cache: ReturnType<typeof createCache>;
  flush: () => string[];
};

function createEmotionCache(): EmotionCacheWithFlush {
  const cache = createCache({ key: "chakra" });
  cache.compat = true;

  const prevInsert = cache.insert;
  let inserted: string[] = [];

  cache.insert = (...args) => {
    const serialized = args[1];

    if (cache.inserted[serialized.name] === undefined) {
      inserted.push(serialized.name);
    }

    return prevInsert(...args);
  };

  return {
    cache,
    flush: () => {
      const names = inserted;
      inserted = [];
      return names;
    }
  };
}

export function EmotionRegistry({ children }: PropsWithChildren) {
  const [{ cache, flush }] = useState(createEmotionCache);

  useServerInsertedHTML(() => {
    const names = flush();

    if (names.length === 0) {
      return null;
    }

    let styles = "";

    for (const name of names) {
      styles += cache.inserted[name];
    }

    return (
      <style
        data-emotion={`${cache.key} ${names.join(" ")}`}
        dangerouslySetInnerHTML={{ __html: styles }}
      />
    );
  });

  return <CacheProvider value={cache}>{children}</CacheProvider>;
}
