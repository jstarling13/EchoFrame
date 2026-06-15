'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Check, Sparkles, X } from 'lucide-react';
import {
  FEATURE_LABELS,
  TIERS,
  TIER_ORDER,
  hasFeatureAccess,
} from '@/lib/auto-ledger/tier-engine';
import type { Feature, Tier } from '@/lib/auto-ledger/types';

interface SubscriptionModalProps {
  open: boolean;
  onClose: () => void;
  currentTier: Tier;
  onSelectTier: (tier: Tier) => void;
  /** Optional context line shown when opened from a locked action. */
  reason?: string | null;
}

// Every feature, in the order we want to list it in the pricing table.
const ALL_FEATURES: Feature[] = [
  'BANK_SYNC',
  'AI_NOTES',
  'DAILY_RECONCILIATION',
  'MONTHLY_NARRATIVE',
  'TAX_ESTIMATES',
  'PRIORITY_REVIEW',
  'CPA_EXPORTS',
  'MULTIPLE_ACCOUNTS',
  'CUSTOM_RULES',
];

export function SubscriptionModal({
  open,
  onClose,
  currentTier,
  onSelectTier,
  reason,
}: SubscriptionModalProps) {
  if (!open) return null;

  const currentIndex = TIER_ORDER.indexOf(currentTier);

  return (
    <div className="fixed inset-0 z-50 print:hidden">
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-[1px]"
        onClick={onClose}
        aria-hidden
      />
      <div className="absolute right-0 top-0 flex h-full w-full max-w-lg flex-col bg-white shadow-2xl">
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Plans &amp; billing</h2>
            <p className="text-xs text-slate-500">
              You&apos;re on the{' '}
              <span className="font-semibold text-slate-700">
                {TIERS[currentTier].name}
              </span>{' '}
              plan
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto px-6 py-5">
          {reason ? (
            <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-900">
              <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
              <span>{reason}</span>
            </div>
          ) : null}

          {TIER_ORDER.map((tierId) => {
            const tier = TIERS[tierId];
            const isCurrent = tierId === currentTier;
            const tierIndex = TIER_ORDER.indexOf(tierId);
            const isUpgrade = tierIndex > currentIndex;

            return (
              <div
                key={tierId}
                className={cn(
                  'rounded-xl border p-5 transition-colors',
                  isCurrent
                    ? 'border-slate-900 bg-slate-50'
                    : tier.popular
                    ? 'border-amber-300'
                    : 'border-slate-200'
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-slate-900">
                        {tier.name}
                      </h3>
                      {tier.popular ? (
                        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-amber-700">
                          Most popular
                        </span>
                      ) : null}
                      {isCurrent ? (
                        <span className="rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-slate-600">
                          Current
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {tier.tagline}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-2xl font-bold tracking-tight text-slate-900">
                      ${tier.price}
                    </span>
                    <span className="text-xs text-slate-400">/mo</span>
                  </div>
                </div>

                <ul className="mt-4 space-y-1.5">
                  {ALL_FEATURES.filter((f) => hasFeatureAccess(tierId, f)).map(
                    (f) => (
                      <li
                        key={f}
                        className="flex items-center gap-2 text-sm text-slate-600"
                      >
                        <Check className="h-4 w-4 shrink-0 text-green-600" />
                        {FEATURE_LABELS[f]}
                      </li>
                    )
                  )}
                </ul>

                <button
                  disabled={isCurrent}
                  onClick={() => onSelectTier(tierId)}
                  className={cn(
                    'mt-4 w-full rounded-md px-4 py-2 text-sm font-semibold transition-colors',
                    isCurrent
                      ? 'cursor-default bg-slate-100 text-slate-400'
                      : tier.popular
                      ? 'bg-amber-600 text-white hover:bg-amber-700'
                      : 'bg-slate-900 text-white hover:bg-slate-800'
                  )}
                >
                  {isCurrent
                    ? 'Current plan'
                    : isUpgrade
                    ? `Upgrade to ${tier.name}`
                    : `Switch to ${tier.name}`}
                </button>
              </div>
            );
          })}

          <p className="pt-1 text-center text-xs text-slate-400">
            Prices in USD. Cancel or change anytime — changes apply to your next
            billing cycle.
          </p>
        </div>
      </div>
    </div>
  );
}
