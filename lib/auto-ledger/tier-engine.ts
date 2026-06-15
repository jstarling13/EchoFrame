// ============================================================================
// Auto Ledger — Tier Enforcement Engine
// Single source of truth for what each subscription tier unlocks.
// ============================================================================

import type { Feature, Tier } from './types';

export interface TierConfig {
  id: Tier;
  name: string;
  /** Monthly price in whole dollars. */
  price: number;
  /** Short positioning line for the pricing UI. */
  tagline: string;
  popular?: boolean;
  /** Features this tier unlocks (cumulative — higher tiers inherit lower ones). */
  features: Feature[];
}

/** Human-readable labels for each feature, used in the pricing table. */
export const FEATURE_LABELS: Record<Feature, string> = {
  BANK_SYNC: 'Automatic bank & card sync',
  AI_NOTES: 'Plain-English notes on every transaction',
  DAILY_RECONCILIATION: 'Daily reconciliation',
  MONTHLY_NARRATIVE: 'Monthly plain-English narrative',
  TAX_ESTIMATES: 'Quarterly tax estimates',
  PRIORITY_REVIEW: 'Priority human review of flagged items',
  CPA_EXPORTS: 'One-click CPA / tax exports',
  MULTIPLE_ACCOUNTS: 'Unlimited connected accounts',
  CUSTOM_RULES: 'Custom categorization rules',
};

const STARTER_FEATURES: Feature[] = [
  'BANK_SYNC',
  'AI_NOTES',
  'DAILY_RECONCILIATION',
  'MONTHLY_NARRATIVE',
];

const GROWTH_FEATURES: Feature[] = [
  ...STARTER_FEATURES,
  'TAX_ESTIMATES',
  'PRIORITY_REVIEW',
  'CPA_EXPORTS',
];

const PRO_FEATURES: Feature[] = [
  ...GROWTH_FEATURES,
  'MULTIPLE_ACCOUNTS',
  'CUSTOM_RULES',
];

export const TIERS: Record<Tier, TierConfig> = {
  STARTER: {
    id: 'STARTER',
    name: 'Starter',
    price: 79,
    tagline: 'Clean books, on autopilot.',
    features: STARTER_FEATURES,
  },
  GROWTH: {
    id: 'GROWTH',
    name: 'Growth',
    price: 149,
    tagline: 'Tax-ready, with a human in the loop.',
    popular: true,
    features: GROWTH_FEATURES,
  },
  PRO: {
    id: 'PRO',
    name: 'Pro',
    price: 299,
    tagline: 'For multi-account, multi-entity operators.',
    features: PRO_FEATURES,
  },
};

/** Tiers in display / upgrade order. */
export const TIER_ORDER: Tier[] = ['STARTER', 'GROWTH', 'PRO'];

/**
 * Tier Enforcement Engine.
 * Returns true if the given tier unlocks the given feature.
 */
export function hasFeatureAccess(tier: Tier, feature: Feature): boolean {
  return TIERS[tier].features.includes(feature);
}

export function getTierConfig(tier: Tier): TierConfig {
  return TIERS[tier];
}

/**
 * The lowest tier that unlocks a feature — used to tell a user what they'd
 * need to upgrade to (e.g. "Available on Growth").
 */
export function requiredTierFor(feature: Feature): Tier {
  return TIER_ORDER.find((tier) => hasFeatureAccess(tier, feature)) ?? 'PRO';
}

/** Account limit per tier (Pro bypasses the limit). */
export function accountLimit(tier: Tier): number {
  return hasFeatureAccess(tier, 'MULTIPLE_ACCOUNTS')
    ? Number.POSITIVE_INFINITY
    : 2;
}
