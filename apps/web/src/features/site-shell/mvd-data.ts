export const macroDrivers: Array<{
  slug: string;
  title: string;
  summary: string;
  cue: string;
}> = [];

export const equityCoverage = [
  {
    slug: "sp-500",
    flagEmoji: "\uD83C\uDDFA\uD83C\uDDF8",
    region: "North America",
    market: "S&P 500",
    ticker: "SPX",
    pe: "24.1x",
    cape: "33.4x",
    pb: "4.7x",
    posture: "Moderately elevated"
  },
  {
    slug: "stoxx-europe-600",
    flagEmoji: "\uD83C\uDDEA\uD83C\uDDFA",
    region: "Europe",
    market: "STOXX Europe 600",
    ticker: "SXXP",
    pe: "14.8x",
    cape: "18.6x",
    pb: "1.9x",
    posture: "Historically neutral"
  },
  {
    slug: "omx-helsinki-25",
    flagEmoji: "\uD83C\uDDEB\uD83C\uDDEE",
    region: "Nordics",
    market: "OMX Helsinki 25",
    ticker: "OMXH25",
    pe: "15.2x",
    cape: "17.1x",
    pb: "1.8x",
    posture: "Moderately compressed"
  },
  {
    slug: "nikkei-225",
    flagEmoji: "\uD83C\uDDEF\uD83C\uDDF5",
    region: "Asia",
    market: "Nikkei 225",
    ticker: "N225",
    pe: "20.7x",
    cape: "25.2x",
    pb: "2.1x",
    posture: "Moderately elevated"
  },
  {
    slug: "hang-seng-index",
    flagEmoji: "\uD83C\uDDED\uD83C\uDDF0",
    region: "Asia",
    market: "Hang Seng Index",
    ticker: "HSI",
    pe: "9.3x",
    cape: "11.8x",
    pb: "0.9x",
    posture: "Moderately compressed"
  },
  {
    slug: "sp-asx-200",
    flagEmoji: "\uD83C\uDDE6\uD83C\uDDFA",
    region: "Oceania",
    market: "S&P/ASX 200",
    ticker: "ASX 200",
    pe: "18.4x",
    cape: "21.5x",
    pb: "2.0x",
    posture: "Historically neutral"
  }
];
