// ============================================================================
// Shift Lens — Waitlist Pricing Engine
// Early-bird waitlist members lock in $99/mo; everyone else pays $149/mo.
// ============================================================================

import type { PricingTier, ShiftLensUser } from './types';

export interface PricingTierConfig {
  id: PricingTier;
  name: string;
  price: number; // monthly USD
  blurb: string;
}

export const PRICING: Record<PricingTier, PricingTierConfig> = {
  EARLY_BIRD: {
    id: 'EARLY_BIRD',
    name: 'Early Bird',
    price: 99,
    blurb: 'Locked-in launch rate for waitlist members.',
  },
  STANDARD: {
    id: 'STANDARD',
    name: 'Standard',
    price: 149,
    blurb: 'Standard monthly plan.',
  },
};

/**
 * Waitlist Pricing Engine.
 * Early-bird-locked users get the $99 tier; everyone else sees Standard ($149).
 */
export function getPricingTier(
  user: Pick<ShiftLensUser, 'waitlistStatus'>
): PricingTierConfig {
  return user.waitlistStatus === 'EARLY_BIRD_LOCKED'
    ? PRICING.EARLY_BIRD
    : PRICING.STANDARD;
}

export function isEarlyBird(
  user: Pick<ShiftLensUser, 'waitlistStatus'>
): boolean {
  return user.waitlistStatus === 'EARLY_BIRD_LOCKED';
}
