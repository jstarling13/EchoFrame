// ============================================================================
// Auto Ledger — shared types
// Mirrors the Prisma models but kept framework-free so the engine functions and
// client components can share one source of truth.
// ============================================================================

/** Subscription tiers, ordered cheapest → most expensive. */
export type Tier = 'STARTER' | 'GROWTH' | 'PRO';

export type SubscriptionStatus =
  | 'ACTIVE'
  | 'PAST_DUE'
  | 'CANCELED'
  | 'TRIALING';

/** Every gateable capability in the product. */
export type Feature =
  | 'BANK_SYNC'
  | 'AI_NOTES'
  | 'DAILY_RECONCILIATION'
  | 'MONTHLY_NARRATIVE'
  | 'TAX_ESTIMATES'
  | 'PRIORITY_REVIEW'
  | 'CPA_EXPORTS'
  | 'MULTIPLE_ACCOUNTS'
  | 'CUSTOM_RULES';

export type AccountType = 'CHECKING' | 'CREDIT_CARD';

export type SyncStatus = 'HEALTHY' | 'SYNCING' | 'ERROR';

export type TransactionStatus = 'RECONCILED' | 'FLAGGED';

export interface ConnectedAccount {
  id: string;
  institutionName: string;
  accountType: AccountType;
  mask: string | null;
  lastSyncDate: Date | null;
  syncStatus: SyncStatus;
}

export interface Transaction {
  id: string;
  accountId: string;
  date: Date;
  /** Negative = money out, positive = money in. */
  amount: number;
  rawDescription: string;
  aiCategory: string | null;
  plainEnglishNote: string | null;
  status: TransactionStatus;
}

export interface MonthlyReport {
  month: number; // 1-12
  year: number;
  summaryText: string;
  actionItem: string;
  /** Only populated on GROWTH / PRO tiers. */
  taxEstimateAmount: number | null;
}

export interface LedgerUser {
  id: string;
  name: string;
  email: string;
  businessName: string;
  subscriptionTier: Tier;
  subscriptionStatus: SubscriptionStatus;
}

/** Result of the AI categorization mock. */
export interface Categorization {
  aiCategory: string;
  plainEnglishNote: string;
}

/** Top-line numbers shown on the dashboard. */
export interface LedgerMetrics {
  netCashflowMtd: number;
  moneyInMtd: number;
  moneyOutMtd: number;
  unreviewedCount: number;
  flaggedCount: number;
  reconciledCount: number;
}

/** Everything the dashboard needs in one payload. */
export interface DashboardData {
  user: LedgerUser;
  accounts: ConnectedAccount[];
  transactions: Transaction[];
  report: MonthlyReport;
  metrics: LedgerMetrics;
}
