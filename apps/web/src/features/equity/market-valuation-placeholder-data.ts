export type MarketValuationRow = {
  region: string;
  market: string;
  proxy: string;
  pe: string;
  pb: string;
  ps: string;
  pfcf: string;
  dividendYield: string;
  sourceStatus: "placeholder";
  isPlaceholder: true;
};

export const PLACEHOLDER_MARKET_VALUATION_DATASET_STATUS = "PLACEHOLDER_ONLY_DO_NOT_SHIP";

export const marketValuationRows: MarketValuationRow[] = [
  {
    region: "USA",
    market: "Broad large-cap equity",
    proxy: "S&P 500 / broad ETF proxy",
    pe: "22.4x",
    pb: "4.3x",
    ps: "2.8x",
    pfcf: "28.0x",
    dividendYield: "1.4%",
    sourceStatus: "placeholder",
    isPlaceholder: true,
  },
  {
    region: "Europe",
    market: "Developed Europe broad equity",
    proxy: "STOXX Europe / broad ETF proxy",
    pe: "14.2x",
    pb: "1.9x",
    ps: "1.2x",
    pfcf: "17.5x",
    dividendYield: "3.1%",
    sourceStatus: "placeholder",
    isPlaceholder: true,
  },
  {
    region: "Germany",
    market: "German large-cap equity",
    proxy: "DAX / Germany ETF proxy",
    pe: "13.7x",
    pb: "1.8x",
    ps: "0.9x",
    pfcf: "15.8x",
    dividendYield: "2.8%",
    sourceStatus: "placeholder",
    isPlaceholder: true,
  },
  {
    region: "France",
    market: "French large-cap equity",
    proxy: "CAC 40 / France ETF proxy",
    pe: "15.1x",
    pb: "2.0x",
    ps: "1.1x",
    pfcf: "18.2x",
    dividendYield: "2.9%",
    sourceStatus: "placeholder",
    isPlaceholder: true,
  },
  {
    region: "United Kingdom",
    market: "UK broad equity",
    proxy: "FTSE 100 / UK ETF proxy",
    pe: "11.8x",
    pb: "1.6x",
    ps: "0.9x",
    pfcf: "13.4x",
    dividendYield: "3.7%",
    sourceStatus: "placeholder",
    isPlaceholder: true,
  },
  {
    region: "Finland",
    market: "Finnish broad equity",
    proxy: "OMX Helsinki / Finland ETF proxy",
    pe: "16.5x",
    pb: "1.7x",
    ps: "1.1x",
    pfcf: "19.0x",
    dividendYield: "3.5%",
    sourceStatus: "placeholder",
    isPlaceholder: true,
  },
  {
    region: "Sweden",
    market: "Swedish broad equity",
    proxy: "OMX Stockholm / Sweden ETF proxy",
    pe: "17.9x",
    pb: "2.4x",
    ps: "1.7x",
    pfcf: "22.0x",
    dividendYield: "2.5%",
    sourceStatus: "placeholder",
    isPlaceholder: true,
  },
  {
    region: "China",
    market: "China broad equity",
    proxy: "MSCI China / China ETF proxy",
    pe: "10.9x",
    pb: "1.3x",
    ps: "0.8x",
    pfcf: "12.7x",
    dividendYield: "2.7%",
    sourceStatus: "placeholder",
    isPlaceholder: true,
  },
  {
    region: "Japan",
    market: "Japanese broad equity",
    proxy: "TOPIX / Japan ETF proxy",
    pe: "15.8x",
    pb: "1.5x",
    ps: "0.9x",
    pfcf: "16.8x",
    dividendYield: "2.2%",
    sourceStatus: "placeholder",
    isPlaceholder: true,
  },
  {
    region: "Taiwan",
    market: "Taiwan broad equity",
    proxy: "TAIEX / Taiwan ETF proxy",
    pe: "19.6x",
    pb: "2.8x",
    ps: "2.1x",
    pfcf: "24.5x",
    dividendYield: "2.9%",
    sourceStatus: "placeholder",
    isPlaceholder: true,
  },
];
