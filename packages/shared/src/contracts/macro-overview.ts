export interface MacroOverviewMetric {
  label: string;
  value: string;
}

export interface MacroOverviewResponse {
  asOf: string;
  metrics: MacroOverviewMetric[];
}
