import React from 'react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { Lock } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string;
  hint?: string;
  icon?: React.ReactNode;
  iconClassName?: string;
  /** Tailwind class applied to the value (e.g. text-green-600 for positive). */
  valueClassName?: string;
}

/** Standard top-line metric tile. */
export function MetricCard({
  label,
  value,
  hint,
  icon,
  iconClassName,
  valueClassName,
}: MetricCardProps) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p
            className={cn(
              'mt-2 text-3xl font-bold tracking-tight text-slate-900',
              valueClassName
            )}
          >
            {value}
          </p>
          {hint ? <p className="mt-1 text-xs text-slate-400">{hint}</p> : null}
        </div>
        {icon ? (
          <div
            className={cn(
              'flex h-10 w-10 shrink-0 items-center justify-center rounded-lg',
              iconClassName ?? 'bg-slate-100 text-slate-600'
            )}
          >
            {icon}
          </div>
        ) : null}
      </div>
    </Card>
  );
}

interface LockedMetricCardProps {
  label: string;
  /** The real value, blurred until unlocked. */
  value: string;
  /** Tier name the user must reach, e.g. "Growth". */
  requiredTierName: string;
  onUpgrade: () => void;
}

/**
 * Tier-gated metric tile. Shows the real value blurred behind a lock with an
 * inline upgrade prompt — used for the tax-estimate card on the Starter tier.
 */
export function LockedMetricCard({
  label,
  value,
  requiredTierName,
  onUpgrade,
}: LockedMetricCardProps) {
  return (
    <Card className="relative overflow-hidden p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p
            aria-hidden
            className="mt-2 select-none text-3xl font-bold tracking-tight text-slate-900 blur-[6px]"
          >
            {value}
          </p>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
          <Lock className="h-5 w-5" />
        </div>
      </div>
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/60 backdrop-blur-[1px]">
        <p className="text-xs font-medium text-slate-600">
          Available on {requiredTierName}
        </p>
        <button
          onClick={onUpgrade}
          className="rounded-md bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-amber-700"
        >
          Unlock
        </button>
      </div>
    </Card>
  );
}
