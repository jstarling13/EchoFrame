// ============================================================================
// Rate Watch — Mock data for the MVP dashboard
// A Columbus, GA mid-size business with 5 vendors. Rows are built through the
// same benchmarking + negotiation engines the production app would use.
// ============================================================================

import { annualize, getColumbusMarketRate } from './benchmarking';
import {
  daysUntil,
  generateNegotiationDraft,
  isActionRequired,
} from './negotiation';
import { TRIAL_LENGTH_DAYS } from './tier-engine';
import type {
  Category,
  DashboardData,
  Frequency,
  RateWatchMetrics,
  RateWatchUser,
  Tier,
  Vendor,
  VendorRow,
} from './types';

const NOW = new Date();

function inDays(days: number): Date {
  return new Date(NOW.getTime() + days * 24 * 60 * 60 * 1000);
}

interface RawVendor {
  id: string;
  name: string;
  category: Category;
  currentRate: number;
  frequency: Frequency;
  renewalInDays: number;
}

// 2 significantly over market with 45-day renewals, 1 slightly under, 2 average.
const RAW_VENDORS: RawVendor[] = [
  {
    id: 'ven_cleaning',
    name: 'Peach State Commercial Cleaning',
    category: 'Cleaning',
    currentRate: 800, // market ~650 → +$150/mo (~23%), +$1,800/yr
    frequency: 'MONTHLY',
    renewalInDays: 45,
  },
  {
    id: 'ven_it',
    name: 'Chattahoochee Valley IT Support',
    category: 'IT',
    currentRate: 1850, // market ~1500 → +$350/mo (~23%), +$4,200/yr
    frequency: 'MONTHLY',
    renewalInDays: 45,
  },
  {
    id: 'ven_insurance',
    name: 'Local Insurance Brokerage',
    category: 'Insurance',
    currentRate: 14400, // market ~15,600/yr → −$1,200/yr (~8% under)
    frequency: 'ANNUAL',
    renewalInDays: 180,
  },
  {
    id: 'ven_supplies',
    name: 'Office Supplies Co',
    category: 'Supplies',
    currentRate: 420, // market ~410 → +$10/mo (~2%), fair
    frequency: 'MONTHLY',
    renewalInDays: 120,
  },
  {
    id: 'ven_hvac',
    name: 'HVAC Maintenance',
    category: 'HVAC',
    currentRate: 300, // market ~295 → +$5/mo (~2%), fair
    frequency: 'MONTHLY',
    renewalInDays: 150,
  },
];

/** Enrich a single vendor with its benchmark, renewal timing, and draft. */
export function enrichVendor(vendor: Vendor, now: Date = new Date()): VendorRow {
  const benchmark = getColumbusMarketRate(
    vendor.category,
    vendor.currentRate,
    vendor.frequency,
    now
  );

  const annualPremium = Math.max(
    0,
    annualize(vendor.currentRate, vendor.frequency) -
      annualize(benchmark.localMarketRate, vendor.frequency)
  );
  const annualSavings = benchmark.status === 'OVERPAYING' ? annualPremium : 0;

  return {
    vendor,
    benchmark,
    annualPremium: round2(annualPremium),
    annualSavings: round2(annualSavings),
    daysUntilRenewal: daysUntil(vendor.renewalDate, now),
    actionRequired: isActionRequired(vendor.renewalDate, now),
    draft: generateNegotiationDraft(vendor, benchmark),
  };
}

/** Build the enriched vendor rows by running raw vendors through the engines. */
export function buildRows(now: Date = NOW): VendorRow[] {
  return RAW_VENDORS.map((raw) =>
    enrichVendor(
      {
        id: raw.id,
        name: raw.name,
        category: raw.category,
        currentRate: raw.currentRate,
        frequency: raw.frequency,
        renewalDate: inDays(raw.renewalInDays),
      },
      now
    )
  );
}

export function computeMetrics(rows: VendorRow[]): RateWatchMetrics {
  return {
    totalVendors: rows.length,
    totalPotentialSavingsAnnual: round2(
      rows.reduce((sum, r) => sum + r.annualSavings, 0)
    ),
    upcomingRenewals60: rows.filter((r) => r.actionRequired).length,
    overpayingCount: rows.filter((r) => r.benchmark.status === 'OVERPAYING')
      .length,
  };
}

function buildUser(tier: Tier): RateWatchUser {
  return {
    id: 'user_rw_demo',
    businessName: 'Riverside Dental Group',
    industryType: 'Healthcare / Dental',
    tier,
    // Mid-trial so the banner shows days remaining.
    trialEndDate: inDays(TRIAL_LENGTH_DAYS - 5), // ~9 days remaining
  };
}

/**
 * One payload for the dashboard. Default tier is CORE so the UI demonstrates
 * the Pro gating (locked direct-send, 10-vendor limit) out of the box.
 */
export function getDashboardData(tier: Tier = 'CORE'): DashboardData {
  const rows = buildRows();
  return {
    user: buildUser(tier),
    rows,
    metrics: computeMetrics(rows),
    trial: {
      // computed in the client via checkSubscriptionAccess; placeholder here.
      isTrialing: true,
      daysRemaining: TRIAL_LENGTH_DAYS - 5,
      hasEnded: false,
    },
  };
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}
