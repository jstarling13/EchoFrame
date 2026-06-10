// Staleness Engine
// -----------------
// Evaluates a Quote against the calendar and decides whether it has gone stale.
// Rules (per MVP spec):
//   - A PENDING quote whose date_sent is > 3 days ago      -> FOLLOW_UP_ACTIVE
//   - Any quote with no response for > 30 days             -> COLD
//   - WON / LOST quotes are terminal and never re-evaluated.
//
// Pure + deterministic: pass `now` in for testability.

import type { Quote, QuoteColumn, QuoteStatus } from './types';

export const FOLLOW_UP_THRESHOLD_DAYS = 3;
export const COLD_THRESHOLD_DAYS = 30;

const MS_PER_DAY = 1000 * 60 * 60 * 24;

/** Whole days elapsed between two dates (floored, never negative-rounded). */
export function daysBetween(from: Date, to: Date): number {
  return Math.floor((to.getTime() - from.getTime()) / MS_PER_DAY);
}

export interface StalenessResult {
  status: QuoteStatus;
  daysSinceSent: number;
  daysSinceContact: number;
  /** Human-readable explanation of why the status was assigned. */
  reason: string;
}

/**
 * Derive the *current* status of a quote from its dates.
 * Terminal statuses (WON/LOST) are returned unchanged.
 */
export function evaluateStaleness(quote: Quote, now: Date = new Date()): StalenessResult {
  const daysSinceSent = daysBetween(quote.dateSent, now);
  const daysSinceContact = daysBetween(quote.lastContactDate, now);

  if (quote.status === 'WON' || quote.status === 'LOST') {
    return {
      status: quote.status,
      daysSinceSent,
      daysSinceContact,
      reason: `Quote is closed (${quote.status.toLowerCase()}).`,
    };
  }

  // No response in 30+ days -> the lead has gone cold.
  if (daysSinceContact > COLD_THRESHOLD_DAYS) {
    return {
      status: 'COLD',
      daysSinceSent,
      daysSinceContact,
      reason: `No response in ${daysSinceContact} days (> ${COLD_THRESHOLD_DAYS}). Needs reactivation.`,
    };
  }

  // Sent more than 3 days ago and still open -> follow-up sequence is active.
  if (daysSinceSent > FOLLOW_UP_THRESHOLD_DAYS) {
    return {
      status: 'FOLLOW_UP_ACTIVE',
      daysSinceSent,
      daysSinceContact,
      reason: `Sent ${daysSinceSent} days ago (> ${FOLLOW_UP_THRESHOLD_DAYS}). Follow-up sequence active.`,
    };
  }

  return {
    status: 'PENDING',
    daysSinceSent,
    daysSinceContact,
    reason: `Sent ${daysSinceSent} day${daysSinceSent === 1 ? '' : 's'} ago. Still fresh.`,
  };
}

/** Map an evaluated status to the dashboard board column. */
export function columnForStatus(status: QuoteStatus): QuoteColumn {
  switch (status) {
    case 'PENDING':
      return 'FRESH';
    case 'FOLLOW_UP_ACTIVE':
      return 'IN_SEQUENCE';
    case 'COLD':
      return 'COLD';
    case 'WON':
    case 'LOST':
    default:
      return 'CLOSED';
  }
}

/**
 * Re-evaluate a batch of quotes, returning copies with their `status` field
 * updated to the engine's verdict. Useful for a nightly cron or on page load.
 */
export function applyStaleness<T extends Quote>(quotes: T[], now: Date = new Date()): T[] {
  return quotes.map((q) => ({ ...q, status: evaluateStaleness(q, now).status }));
}
