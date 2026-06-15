// ============================================================================
// Rate Watch — Local Benchmarking (MVP mock)
// Returns a realistic Columbus, GA market rate for a category and computes the
// variance. In production this is sourced from local market data; here it's a
// deterministic per-category baseline so the demo is stable.
// ============================================================================

import type { Benchmark, Category, Frequency } from './types';

/**
 * Baseline Columbus, GA market rate per category, expressed MONTHLY.
 * e.g. Commercial cleaning benchmarks at ~$650/mo, so a vendor charging
 * $800/mo shows a +$150/mo (~23%) premium.
 */
export const COLUMBUS_MARKET_RATES_MONTHLY: Record<Category, number> = {
  Cleaning: 650,
  IT: 1500,
  Insurance: 1300, // ≈ $15,600/yr
  Supplies: 410,
  HVAC: 295,
};

/** A premium beyond ±5% of market is treated as over/under, else fair. */
export const VARIANCE_THRESHOLD_PCT = 5;

export function annualize(rate: number, frequency: Frequency): number {
  return frequency === 'MONTHLY' ? rate * 12 : rate;
}

/**
 * Local Benchmarking mock.
 * @param category Vendor category.
 * @param currentRate The vendor's rate, in `frequency` units.
 * @param frequency MONTHLY or ANNUAL — the market rate is returned to match.
 */
export function getColumbusMarketRate(
  category: Category,
  currentRate: number,
  frequency: Frequency,
  now: Date = new Date()
): Benchmark {
  const monthlyMarket = COLUMBUS_MARKET_RATES_MONTHLY[category];
  const localMarketRate =
    frequency === 'MONTHLY' ? monthlyMarket : monthlyMarket * 12;

  const varianceAmount = round2(currentRate - localMarketRate);
  const variancePct = round2((varianceAmount / localMarketRate) * 100);

  let status: Benchmark['status'];
  if (variancePct > VARIANCE_THRESHOLD_PCT) status = 'OVERPAYING';
  else if (variancePct < -VARIANCE_THRESHOLD_PCT) status = 'GREAT_DEAL';
  else status = 'FAIR';

  return {
    localMarketRate,
    varianceAmount,
    variancePct,
    status,
    lastBenchmarkedDate: now,
  };
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}
