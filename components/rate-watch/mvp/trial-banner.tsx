import React from 'react';
import { cn } from '@/lib/utils';
import { Clock } from 'lucide-react';
import type { TrialStatus } from '@/lib/rate-watch/types';

interface TrialBannerProps {
  trial: TrialStatus;
  tierName: string;
  onUpgrade: () => void;
}

/** Top-of-dashboard trial status banner. Goes amber when ≤ 3 days remain. */
export function TrialBanner({ trial, tierName, onUpgrade }: TrialBannerProps) {
  if (!trial.isTrialing && !trial.hasEnded) return null;

  const urgent = trial.hasEnded || trial.daysRemaining <= 3;

  return (
    <div
      className={cn(
        'flex flex-wrap items-center justify-between gap-3 rounded-xl border px-5 py-3.5',
        urgent
          ? 'border-amber-300 bg-amber-50'
          : 'border-slate-200 bg-slate-50'
      )}
    >
      <div className="flex items-center gap-3">
        <div
          className={cn(
            'flex h-9 w-9 items-center justify-center rounded-lg',
            urgent ? 'bg-amber-100 text-amber-700' : 'bg-slate-200 text-slate-600'
          )}
        >
          <Clock className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900">
            {trial.hasEnded
              ? 'Your free trial has ended'
              : `${trial.daysRemaining} day${trial.daysRemaining !== 1 ? 's' : ''} left in your free trial`}
          </p>
          <p className="text-xs text-slate-500">
            You&apos;re on the {tierName} plan · no card charged until the trial
            ends.
          </p>
        </div>
      </div>
      <button
        onClick={onUpgrade}
        className={cn(
          'rounded-md px-4 py-2 text-sm font-semibold text-white transition-colors',
          urgent ? 'bg-amber-600 hover:bg-amber-700' : 'bg-slate-900 hover:bg-slate-800'
        )}
      >
        {trial.hasEnded ? 'Choose a plan' : 'Manage plan'}
      </button>
    </div>
  );
}
