// Presentational helpers shared across Quote Revive components.
// Pure functions returning labels + Tailwind class strings — no JSX here so the
// file stays importable from both server and client components.

import type { QuoteColumn, QuoteStatus, SequenceStepStatus } from './types';

export interface ColumnMeta {
  key: QuoteColumn;
  title: string;
  description: string;
  /** Tailwind classes for the column's accent dot/header. */
  accent: string;
}

export const BOARD_COLUMNS: ColumnMeta[] = [
  {
    key: 'FRESH',
    title: 'Fresh Quotes',
    description: 'Sent in the last 3 days',
    accent: 'bg-blue-500',
  },
  {
    key: 'IN_SEQUENCE',
    title: 'In Follow-up Sequence',
    description: 'Automated touches going out',
    accent: 'bg-amber-500',
  },
  {
    key: 'COLD',
    title: 'Cold — Needs Reactivation',
    description: 'No response in 30+ days',
    accent: 'bg-red-500',
  },
];

export function statusLabel(status: QuoteStatus): string {
  switch (status) {
    case 'PENDING':
      return 'Fresh';
    case 'FOLLOW_UP_ACTIVE':
      return 'In Sequence';
    case 'COLD':
      return 'Cold';
    case 'WON':
      return 'Won';
    case 'LOST':
      return 'Lost';
    default:
      return status;
  }
}

/** Tailwind classes for a quote-status pill. */
export function statusBadgeClasses(status: QuoteStatus): string {
  switch (status) {
    case 'PENDING':
      return 'bg-blue-100 text-blue-800';
    case 'FOLLOW_UP_ACTIVE':
      return 'bg-amber-100 text-amber-800';
    case 'COLD':
      return 'bg-red-100 text-red-800';
    case 'WON':
      return 'bg-green-100 text-green-800';
    case 'LOST':
      return 'bg-slate-200 text-slate-700';
    default:
      return 'bg-slate-100 text-slate-800';
  }
}

export function stepStatusLabel(status: SequenceStepStatus): string {
  switch (status) {
    case 'SENT':
      return 'Sent';
    case 'PENDING':
      return 'Scheduled';
    case 'PAUSED':
      return 'Paused';
    default:
      return status;
  }
}

export function stepStatusClasses(status: SequenceStepStatus): string {
  switch (status) {
    case 'SENT':
      return 'bg-green-100 text-green-800';
    case 'PENDING':
      return 'bg-blue-100 text-blue-800';
    case 'PAUSED':
      return 'bg-slate-200 text-slate-700';
    default:
      return 'bg-slate-100 text-slate-800';
  }
}

/**
 * Compact countdown phrase for a card, e.g. "in 2 days", "today",
 * "3d overdue", or "complete".
 */
export function countdownShort(daysUntilNext: number | null): string {
  if (daysUntilNext === null) return 'complete';
  if (daysUntilNext < 0) return `${Math.abs(daysUntilNext)}d overdue`;
  if (daysUntilNext === 0) return 'today';
  if (daysUntilNext === 1) return 'in 1 day';
  return `in ${daysUntilNext} days`;
}

/** Full sentence for the card body. */
export function nextMessageLabel(daysUntilNext: number | null): string {
  if (daysUntilNext === null) return 'Sequence complete';
  if (daysUntilNext < 0) return `Next message ${Math.abs(daysUntilNext)} day(s) overdue`;
  if (daysUntilNext === 0) return 'Next message sends today';
  if (daysUntilNext === 1) return 'Next message sends in 1 day';
  return `Next message sends in ${daysUntilNext} days`;
}
