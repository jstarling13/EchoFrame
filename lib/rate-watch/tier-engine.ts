// ============================================================================
// Rate Watch — Tier & Trial Enforcement Engine
// Core $99 / Pro $199, 14-day trial. Single source of truth for what each
// plan unlocks and how the trial is evaluated.
// ============================================================================

import type { RateWatchUser, Tier, TrialStatus } from './types';

export type Feature =
  | 'BENCHMARK_REPORTS'
  | 'NEGOTIATION_DRAFTS'
  | 'RENEWAL_ALERTS'
  | 'COPY_TO_CLIPBOARD'
  | 'UNLIMITED_VENDORS'
  | 'DIRECT_SEND'
  | 'WEEKLY_REFRESH'
  | 'PRIORITY_SUPPORT';

export interface TierConfig {
  id: Tier;
  name: string;
  price: number; // monthly USD
  tagline: string;
  popular?: boolean;
  features: Feature[];
}

export const FEATURE_LABELS: Record<Feature, string> = {
  BENCHMARK_REPORTS: 'AI benchmark report for every vendor',
  NEGOTIATION_DRAFTS: 'Negotiation email drafts',
  RENEWAL_ALERTS: 'Contract renewal alerts (60 days out)',
  COPY_TO_CLIPBOARD: 'Copy-to-clipboard email send',
  UNLIMITED_VENDORS: 'Unlimited vendors tracked',
  DIRECT_SEND: 'One-click direct send to vendor',
  WEEKLY_REFRESH: 'Weekly benchmarking refresh',
  PRIORITY_SUPPORT: 'Priority support',
};

/** Core tier vendor cap. Pro is unlimited. */
export const CORE_VENDOR_LIMIT = 10;

/** Trial length in days. */
export const TRIAL_LENGTH_DAYS = 14;

const CORE_FEATURES: Feature[] = [
  'BENCHMARK_REPORTS',
  'NEGOTIATION_DRAFTS',
  'RENEWAL_ALERTS',
  'COPY_TO_CLIPBOARD',
];

const PRO_FEATURES: Feature[] = [
  ...CORE_FEATURES,
  'UNLIMITED_VENDORS',
  'DIRECT_SEND',
  'WEEKLY_REFRESH',
  'PRIORITY_SUPPORT',
];

export const TIERS: Record<Tier, TierConfig> = {
  CORE: {
    id: 'CORE',
    name: 'Core',
    price: 99,
    tagline: 'For owners who want to stop overpaying — up to 10 vendors.',
    features: CORE_FEATURES,
  },
  PRO: {
    id: 'PRO',
    name: 'Pro',
    price: 199,
    tagline: 'Unlimited vendors, weekly refresh, and one-click send.',
    popular: true,
    features: PRO_FEATURES,
  },
};

export const TIER_ORDER: Tier[] = ['CORE', 'PRO'];

export function getTierConfig(tier: Tier): TierConfig {
  return TIERS[tier];
}

export function hasFeatureAccess(tier: Tier, feature: Feature): boolean {
  return TIERS[tier].features.includes(feature);
}

/**
 * Trial & subscription status for a user. Days remaining is clamped at 0;
 * `hasEnded` flips once the trial date has passed.
 */
export function checkSubscriptionAccess(
  user: Pick<RateWatchUser, 'trialEndDate'>,
  now: Date = new Date()
): TrialStatus {
  if (!user.trialEndDate) {
    return { isTrialing: false, daysRemaining: 0, hasEnded: false };
  }
  const ms = user.trialEndDate.getTime() - now.getTime();
  const daysRemaining = Math.max(0, Math.ceil(ms / (1000 * 60 * 60 * 24)));
  return {
    isTrialing: ms > 0,
    daysRemaining,
    hasEnded: ms <= 0,
  };
}

export interface AddVendorCheck {
  allowed: boolean;
  reason: string | null;
}

/**
 * Enforces the 10-vendor cap on Core. Pro bypasses it.
 */
export function canAddVendor(tier: Tier, currentVendorCount: number): AddVendorCheck {
  if (hasFeatureAccess(tier, 'UNLIMITED_VENDORS')) {
    return { allowed: true, reason: null };
  }
  if (currentVendorCount >= CORE_VENDOR_LIMIT) {
    return {
      allowed: false,
      reason: `The Core plan tracks up to ${CORE_VENDOR_LIMIT} vendors. Upgrade to Pro for unlimited vendor tracking.`,
    };
  }
  return { allowed: true, reason: null };
}
