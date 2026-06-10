// ============================================================================
// Shift Lens — Alert & Recommendation Generator
// Sweeps recent shifts; for every BLEEDING shift it raises an Alert and drafts
// a ScheduleRecommendation for the upcoming week tied to that time slot.
// ============================================================================

import { BORDERLINE_MAX_PCT } from './profitability';
import type {
  ScheduleRecommendation,
  Shift,
  ShiftAlert,
} from './types';

/** Labor % we steer shifts back toward when estimating savings. */
const TARGET_LABOR_PCT = 25;

function money(n: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n);
}

/** The most recent past Monday (week anchor) relative to `from`. */
export function startOfWeek(from: Date): Date {
  const d = new Date(from);
  const day = d.getDay(); // 0 = Sun
  const diff = (day + 6) % 7; // days since Monday
  d.setDate(d.getDate() - diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

/** The upcoming week's Monday — what recommendations target. */
export function nextWeekStart(from: Date = new Date()): Date {
  const d = startOfWeek(from);
  d.setDate(d.getDate() + 7);
  return d;
}

/** Estimated weekly savings from pulling a bleeding shift back to target labor %. */
export function estimatedWeeklySavings(shift: Shift): number {
  const targetLabor = shift.totalRevenue * (TARGET_LABOR_PCT / 100);
  return Math.max(0, Math.round(shift.actualLaborCost - targetLabor));
}

export function buildAlert(shift: Shift): ShiftAlert {
  return {
    id: `alert_${shift.id}`,
    shiftId: shift.id,
    type: 'Labor Threshold Exceeded',
    message: `${shift.shiftName} ran at ${shift.laborPercentage}% labor — you brought in ${money(
      shift.totalRevenue
    )} but spent ${money(
      shift.actualLaborCost
    )} on labor, well above the ${BORDERLINE_MAX_PCT}% healthy ceiling.`,
    isResolved: false,
  };
}

export function buildRecommendation(
  shift: Shift,
  weekStart: Date
): ScheduleRecommendation {
  const savings = estimatedWeeklySavings(shift);
  return {
    id: `rec_${shift.id}`,
    weekStartDate: weekStart,
    recommendationText: `Trim one floor staff member (or cut ~1 hour) from the ${shift.shiftName} shift next week to bring labor toward ${TARGET_LABOR_PCT}% and recover about ${money(
      savings
    )}/week.`,
    status: 'PENDING',
  };
}

export interface SweepResult {
  alerts: ShiftAlert[];
  recommendations: ScheduleRecommendation[];
}

/**
 * Alert & Recommendation Generator.
 * Sweeps shifts and, for each BLEEDING one, produces an alert + a draft
 * recommendation for the upcoming week.
 */
export function sweepShifts(
  shifts: Shift[],
  now: Date = new Date()
): SweepResult {
  const weekStart = nextWeekStart(now);
  const bleeding = shifts.filter((s) => s.status === 'BLEEDING');
  return {
    alerts: bleeding.map(buildAlert),
    recommendations: bleeding.map((s) => buildRecommendation(s, weekStart)),
  };
}

/**
 * Plain-English weekly narrative anchored on the worst bleeding shift.
 */
export function buildWeeklyNarrative(shifts: Shift[]): string {
  const bleeders = shifts
    .filter((s) => s.status === 'BLEEDING')
    .sort((a, b) => b.laborPercentage - a.laborPercentage);

  if (bleeders.length === 0) {
    return 'No shifts are bleeding this week — labor is tracking healthy across the board. Keep the current schedule and keep an eye on borderline shifts.';
  }

  const worst = bleeders[0];
  const savings = estimatedWeeklySavings(worst);
  const lead = `Your ${worst.shiftName} shift is quietly eating your margin. You brought in ${money(
    worst.totalRevenue
  )} but spent ${money(worst.actualLaborCost)} on labor (${worst.laborPercentage}%). We recommend trimming this shift by an hour or cutting one floor staff member — worth about ${money(
    savings
  )}/week.`;

  if (bleeders.length > 1) {
    return `${lead} ${bleeders.length - 1} other shift${
      bleeders.length - 1 !== 1 ? 's are' : ' is'
    } also over the labor ceiling — see the recommendations below.`;
  }
  return lead;
}
