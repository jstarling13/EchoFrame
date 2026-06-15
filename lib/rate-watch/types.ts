// ============================================================================
// Rate Watch — shared types
// Framework-free so the engine functions, mock data, and client components
// share one source of truth (mirrors the lib/auto-ledger pattern).
// ============================================================================

export type Tier = 'CORE' | 'PRO';

/** Vendor spend categories we benchmark. */
export type Category =
  | 'Cleaning'
  | 'Insurance'
  | 'IT'
  | 'Supplies'
  | 'HVAC';

export type Frequency = 'MONTHLY' | 'ANNUAL';

/** Benchmark verdict relative to the local market rate. */
export type RateStatus = 'OVERPAYING' | 'FAIR' | 'GREAT_DEAL';

export interface RateWatchUser {
  id: string;
  businessName: string;
  industryType: string;
  tier: Tier;
  /** When the 14-day trial ends; null once on a paid plan. */
  trialEndDate: Date | null;
}

export interface Vendor {
  id: string;
  name: string;
  category: Category;
  currentRate: number;
  frequency: Frequency;
  renewalDate: Date;
}

export interface Benchmark {
  /** Local (Columbus, GA) market rate, in the vendor's own frequency. */
  localMarketRate: number;
  /** currentRate − localMarketRate, in the vendor's frequency (+ = overpaying). */
  varianceAmount: number;
  /** Variance as a percentage of the market rate. */
  variancePct: number;
  status: RateStatus;
  lastBenchmarkedDate: Date;
}

export interface NegotiationDraft {
  subjectLine: string;
  bodyText: string;
  status: 'DRAFT' | 'SENT';
}

/** A vendor enriched with its benchmark, renewal timing, and draft. */
export interface VendorRow {
  vendor: Vendor;
  benchmark: Benchmark;
  /** Annualized premium over market (always ≥ 0; 0 if at/below market). */
  annualPremium: number;
  /** Annualized potential savings (= annualPremium when overpaying, else 0). */
  annualSavings: number;
  daysUntilRenewal: number;
  /** True when renewal is within 60 days — "Action Required". */
  actionRequired: boolean;
  draft: NegotiationDraft;
}

export interface TrialStatus {
  isTrialing: boolean;
  daysRemaining: number;
  hasEnded: boolean;
}

export interface RateWatchMetrics {
  totalVendors: number;
  totalPotentialSavingsAnnual: number;
  upcomingRenewals60: number;
  overpayingCount: number;
}

export interface DashboardData {
  user: RateWatchUser;
  rows: VendorRow[];
  metrics: RateWatchMetrics;
  trial: TrialStatus;
}
