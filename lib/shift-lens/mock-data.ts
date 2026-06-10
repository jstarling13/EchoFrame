// ============================================================================
// Shift Lens — Mock data for the MVP dashboard
// A local coffee shop's last week of shifts. Each shift runs through the same
// profitability engine the production app uses. Shifts are NOT loaded until the
// user clicks "Sync Recent Shifts" (see buildShifts()).
// ============================================================================

import { computeShiftProfitability } from './profitability';
import type {
  Shift,
  ShiftLensMetrics,
  ShiftLensUser,
} from './types';

/** The most recent date (≤ now) that falls on the given weekday, at noon. */
function lastWeekday(targetDow: number, now: Date): Date {
  const d = new Date(now);
  const diff = (d.getDay() - targetDow + 7) % 7;
  d.setDate(d.getDate() - diff);
  d.setHours(12, 0, 0, 0);
  return d;
}

export function getUser(): ShiftLensUser {
  return {
    id: 'user_sl_demo',
    businessName: 'Riverside Roasters',
    waitlistStatus: 'EARLY_BIRD_LOCKED',
    posIntegration: 'Square',
    scheduleIntegration: '7shifts',
  };
}

interface RawShift {
  id: string;
  dow: number; // 0=Sun ... 6=Sat
  shiftName: string;
  startTime: string;
  endTime: string;
  totalRevenue: number;
  actualLaborCost: number;
}

// Mon=1, Tue=2, Wed=3, Thu=4, Fri=5, Sat=6.
const RAW_SHIFTS: RawShift[] = [
  { id: 'sh_mon_am', dow: 1, shiftName: 'Monday Morning', startTime: '6:00 AM', endTime: '11:00 AM', totalRevenue: 1200, actualLaborCost: 180 }, // 15% Profitable
  { id: 'sh_mon_pm', dow: 1, shiftName: 'Monday Evening', startTime: '4:00 PM', endTime: '10:00 PM', totalRevenue: 950, actualLaborCost: 200 }, // 21% Profitable
  { id: 'sh_tue_noon', dow: 2, shiftName: 'Tuesday Afternoon', startTime: '12:00 PM', endTime: '4:00 PM', totalRevenue: 150, actualLaborCost: 100 }, // 66.7% Bleeding
  { id: 'sh_tue_pm', dow: 2, shiftName: 'Tuesday Evening', startTime: '5:00 PM', endTime: '11:00 PM', totalRevenue: 400, actualLaborCost: 220 }, // 55% Bleeding
  { id: 'sh_wed_pm', dow: 3, shiftName: 'Wednesday Evening', startTime: '5:00 PM', endTime: '11:00 PM', totalRevenue: 800, actualLaborCost: 240 }, // 30% Borderline
  { id: 'sh_thu_am', dow: 4, shiftName: 'Thursday Morning', startTime: '6:00 AM', endTime: '11:00 AM', totalRevenue: 1100, actualLaborCost: 190 }, // 17.3% Profitable
  { id: 'sh_fri_pm', dow: 5, shiftName: 'Friday Evening', startTime: '5:00 PM', endTime: '11:00 PM', totalRevenue: 1400, actualLaborCost: 460 }, // 32.9% Borderline
  { id: 'sh_sat_am', dow: 6, shiftName: 'Saturday Morning', startTime: '7:00 AM', endTime: '12:00 PM', totalRevenue: 1300, actualLaborCost: 210 }, // 16.2% Profitable
];

/**
 * Build the last week of shifts, each run through the profitability engine.
 * Returned only when the user "syncs" — the dashboard starts empty.
 */
export function buildShifts(now: Date = new Date()): Shift[] {
  return RAW_SHIFTS.map((raw) => {
    const { laborPercentage, netMargin, status } = computeShiftProfitability(
      raw.totalRevenue,
      raw.actualLaborCost
    );
    return {
      id: raw.id,
      date: lastWeekday(raw.dow, now),
      shiftName: raw.shiftName,
      startTime: raw.startTime,
      endTime: raw.endTime,
      totalRevenue: raw.totalRevenue,
      actualLaborCost: raw.actualLaborCost,
      netMargin,
      laborPercentage,
      status,
    };
  }).sort((a, b) => a.date.getTime() - b.date.getTime());
}

export function computeMetrics(shifts: Shift[]): ShiftLensMetrics {
  const totalRevenue7d = shifts.reduce((s, x) => s + x.totalRevenue, 0);
  const totalLabor7d = shifts.reduce((s, x) => s + x.actualLaborCost, 0);
  return {
    netMargin7d: round2(shifts.reduce((s, x) => s + x.netMargin, 0)),
    totalRevenue7d: round2(totalRevenue7d),
    totalLabor7d: round2(totalLabor7d),
    avgLaborPct:
      totalRevenue7d > 0 ? round1((totalLabor7d / totalRevenue7d) * 100) : 0,
    bleedingCount: shifts.filter((s) => s.status === 'BLEEDING').length,
  };
}

function round1(n: number): number {
  return Math.round(n * 10) / 10;
}
function round2(n: number): number {
  return Math.round(n * 100) / 100;
}
