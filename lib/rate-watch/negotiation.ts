// ============================================================================
// Rate Watch — Alert & Draft Generator
// Flags vendors whose contract renews within 60 days as "Action Required" and
// generates an AI-style negotiation email draft backed by the variance data.
// ============================================================================

import { annualize } from './benchmarking';
import type { Benchmark, NegotiationDraft, Vendor } from './types';

/** Renewals within this many days are "Action Required". */
export const RENEWAL_WINDOW_DAYS = 60;

export function daysUntil(date: Date, now: Date = new Date()): number {
  const ms = date.getTime() - now.getTime();
  return Math.ceil(ms / (1000 * 60 * 60 * 24));
}

export function isActionRequired(
  renewalDate: Date,
  now: Date = new Date()
): boolean {
  const d = daysUntil(renewalDate, now);
  return d >= 0 && d <= RENEWAL_WINDOW_DAYS;
}

function money(n: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n);
}

function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
}

/**
 * Generate a negotiation email draft for an overpaying (or renewing) vendor,
 * grounded in the Columbus market variance. Returns a DRAFT.
 */
export function generateNegotiationDraft(
  vendor: Vendor,
  benchmark: Benchmark
): NegotiationDraft {
  const freqLabel = vendor.frequency === 'MONTHLY' ? 'per month' : 'per year';
  const annualPremium = Math.max(
    0,
    annualize(vendor.currentRate, vendor.frequency) -
      annualize(benchmark.localMarketRate, vendor.frequency)
  );
  const pct = Math.abs(benchmark.variancePct).toFixed(1);

  const subjectLine = `Renewal pricing review ahead of our ${formatDate(
    vendor.renewalDate
  )} contract date`;

  const overpaying = benchmark.status === 'OVERPAYING';

  const bodyText = overpaying
    ? `Hi ${vendor.name} team,

As we approach our renewal on ${formatDate(
        vendor.renewalDate
      )}, we've been reviewing our vendor agreements against current local market rates.

Market data for the Columbus, GA area indicates comparable ${vendor.category.toLowerCase()} services are running about ${money(
        benchmark.localMarketRate
      )} ${freqLabel}. Our current rate is ${money(
        vendor.currentRate
      )} ${freqLabel} — roughly ${pct}% above the local benchmark, which works out to about ${money(
        annualPremium
      )} per year.

We value the relationship and would like to continue working together. Before we renew, could we discuss bringing our rate in line with the current market? We're happy to talk through scope and find a number that works for both of us.

Looking forward to your thoughts.

Best regards`
    : `Hi ${vendor.name} team,

As we approach our renewal on ${formatDate(
        vendor.renewalDate
      )}, we're reviewing our vendor agreements. Our current rate of ${money(
        vendor.currentRate
      )} ${freqLabel} looks competitive against the local Columbus, GA market, and we'd like to lock in continued service at current terms.

Could you confirm the renewal terms and flag any planned rate changes? We'd like to avoid surprises at renewal.

Thanks for the continued partnership.

Best regards`;

  return { subjectLine, bodyText, status: 'DRAFT' };
}
