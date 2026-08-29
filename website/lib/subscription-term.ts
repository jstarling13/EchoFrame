/**
 * Pure helpers for detecting whether a Stripe subscription cancellation
 * falls inside an offer's contractual initial term.
 *
 * IMPORTANT — read before changing this file: Stripe subscriptions do NOT
 * natively enforce a minimum commitment. Nothing in this codebase stops a
 * subscription from being canceled at any time via the Stripe dashboard,
 * API, or a future customer portal. The 3-month initial term for O5 is a
 * CONTRACTUAL obligation (the signed SOW/MSA), not a technical one. This
 * module only detects and flags early cancellations for manual, contract-
 * based owner review — it must never auto-charge a penalty or block
 * cancellation, per strategy/DECISION_LOG.md and the explicit instruction
 * not to build a punitive, legally-unreviewed cancellation mechanism.
 */

const SECONDS_PER_DAY = 86400;
const AVG_DAYS_PER_MONTH = 30.44; // matches common contract "N-month term" conventions

export interface EarlyCancellationCheck {
  isWithinInitialTerm: boolean;
  monthsElapsed: number;
  initialTermMonths: number;
}

/**
 * @param subscriptionStartEpochSeconds Stripe subscription `start_date` (or `created` as a fallback).
 * @param cancellationEpochSeconds When the cancellation was requested/took effect.
 * @param initialTermMonths The offer's contractual minimum term (e.g. 3 for O5).
 */
export function checkEarlyCancellation(
  subscriptionStartEpochSeconds: number,
  cancellationEpochSeconds: number,
  initialTermMonths: number
): EarlyCancellationCheck {
  // Rounded to the nearest whole second: real Stripe timestamps are always
  // integer Unix seconds, so this only ever discards floating-point noise,
  // never meaningful precision — and it keeps a cancellation landing
  // exactly on the term boundary from reading as fractionally-under-term
  // due to multiplication-order rounding error.
  const elapsedSeconds = Math.max(
    0,
    Math.round(cancellationEpochSeconds - subscriptionStartEpochSeconds)
  );
  const termBoundarySeconds = Math.round(
    initialTermMonths * AVG_DAYS_PER_MONTH * SECONDS_PER_DAY
  );
  const monthsElapsed = elapsedSeconds / SECONDS_PER_DAY / AVG_DAYS_PER_MONTH;
  return {
    isWithinInitialTerm: elapsedSeconds < termBoundarySeconds,
    monthsElapsed,
    initialTermMonths,
  };
}
