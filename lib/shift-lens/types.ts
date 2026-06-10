// ============================================================================
// Shift Lens — shared types
// Framework-free source of truth shared by the engines, mock data, and UI
// (mirrors the lib/auto-ledger and lib/rate-watch patterns).
// ============================================================================

export type WaitlistStatus = 'PENDING' | 'EARLY_BIRD_LOCKED';

export type PricingTier = 'EARLY_BIRD' | 'STANDARD';

export type ShiftStatus = 'PROFITABLE' | 'BORDERLINE' | 'BLEEDING';

export type RecommendationStatus = 'PENDING' | 'APPROVED' | 'DISMISSED';

export interface ShiftLensUser {
  id: string;
  businessName: string;
  waitlistStatus: WaitlistStatus;
  posIntegration: string | null;
  scheduleIntegration: string | null;
}

export interface Shift {
  id: string;
  date: Date;
  shiftName: string;
  startTime: string;
  endTime: string;
  totalRevenue: number;
  actualLaborCost: number;
  netMargin: number;
  laborPercentage: number;
  status: ShiftStatus;
}

export interface ShiftAlert {
  id: string;
  shiftId: string;
  type: string;
  message: string;
  isResolved: boolean;
}

export interface ScheduleRecommendation {
  id: string;
  weekStartDate: Date;
  recommendationText: string;
  status: RecommendationStatus;
}

export interface ShiftLensMetrics {
  /** Net margin summed across the last 7 days of shifts. */
  netMargin7d: number;
  /** Labor as a % of revenue across all shifts (weighted). */
  avgLaborPct: number;
  /** Count of shifts flagged BLEEDING. */
  bleedingCount: number;
  totalRevenue7d: number;
  totalLabor7d: number;
}

export interface DashboardData {
  user: ShiftLensUser;
  shifts: Shift[];
  alerts: ShiftAlert[];
  recommendations: ScheduleRecommendation[];
  metrics: ShiftLensMetrics;
}
