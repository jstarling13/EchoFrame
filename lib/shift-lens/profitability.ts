// ============================================================================
// Shift Lens — Shift Profitability Engine
// Turns raw revenue + labor cost into a labor %, a net margin, and a health
// status. Thresholds: <25% Profitable · 25–35% Borderline · >35% Bleeding.
// ============================================================================

import type { ShiftStatus } from './types';

export const PROFITABLE_MAX_PCT = 25;
export const BORDERLINE_MAX_PCT = 35;

export interface Profitability {
  laborPercentage: number; // rounded to 1 decimal
  netMargin: number; // revenue − labor
  status: ShiftStatus;
}

export function statusForLaborPct(laborPct: number): ShiftStatus {
  if (laborPct < PROFITABLE_MAX_PCT) return 'PROFITABLE';
  if (laborPct <= BORDERLINE_MAX_PCT) return 'BORDERLINE';
  return 'BLEEDING';
}

/**
 * Shift Profitability Engine.
 * @param totalRevenue Shift revenue.
 * @param actualLaborCost Shift labor cost.
 */
export function computeShiftProfitability(
  totalRevenue: number,
  actualLaborCost: number
): Profitability {
  // No revenue but labor spent = worst case (treat as fully bleeding).
  const laborPercentage =
    totalRevenue > 0
      ? round1((actualLaborCost / totalRevenue) * 100)
      : actualLaborCost > 0
      ? 100
      : 0;

  return {
    laborPercentage,
    netMargin: round2(totalRevenue - actualLaborCost),
    status: statusForLaborPct(laborPercentage),
  };
}

function round1(n: number): number {
  return Math.round(n * 10) / 10;
}
function round2(n: number): number {
  return Math.round(n * 100) / 100;
}
