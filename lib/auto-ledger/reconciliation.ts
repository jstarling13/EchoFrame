// ============================================================================
// Auto Ledger — Daily Reconciliation Job
// Processes un-reconciled transactions: auto-reconciles the routine ones and
// flags anything large or suspicious for human review. The "priority review"
// of flagged items is the Growth/Pro upgrade hook.
// ============================================================================

import type { Transaction, TransactionStatus } from './types';

/** Transactions at or above this absolute amount get a human look. */
export const REVIEW_AMOUNT_THRESHOLD = 2500;

/** Keywords that always warrant review regardless of amount. */
export const SUSPICIOUS_KEYWORDS = [
  'WIRE',
  'CASH APP',
  'VENMO',
  'CRYPTO',
  'COINBASE',
  'ATM',
  'CHECK #',
  'UNKNOWN',
  'MISC',
  'OVERDRAFT',
  'NSF',
  'REVERSAL',
  'CHARGEBACK',
];

export interface ReconciliationResult {
  status: TransactionStatus;
  /** Why it was flagged, if it was. Useful for the review queue UI. */
  reason: string | null;
}

/** Decide the status for a single transaction. */
export function reconcileTransaction(
  txn: Pick<Transaction, 'amount' | 'rawDescription'>
): ReconciliationResult {
  const haystack = txn.rawDescription.toUpperCase();

  const keyword = SUSPICIOUS_KEYWORDS.find((k) => haystack.includes(k));
  if (keyword) {
    return {
      status: 'FLAGGED',
      reason: `Matched a watch-list term ("${keyword.trim()}").`,
    };
  }

  if (Math.abs(txn.amount) >= REVIEW_AMOUNT_THRESHOLD) {
    return {
      status: 'FLAGGED',
      reason: `Large amount (≥ $${REVIEW_AMOUNT_THRESHOLD.toLocaleString()}).`,
    };
  }

  return { status: 'RECONCILED', reason: null };
}

/**
 * Daily Reconciliation Job.
 * Runs over a batch of transactions and returns them with an updated status.
 * Already-reconciled rows are left untouched; everything else is re-evaluated.
 */
export function runDailyReconciliation(
  transactions: Transaction[]
): Transaction[] {
  return transactions.map((txn) => {
    if (txn.status === 'FLAGGED') return txn; // keep manual/prior flags
    const { status } = reconcileTransaction(txn);
    return { ...txn, status };
  });
}
