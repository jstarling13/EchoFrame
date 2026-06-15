import React from 'react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  label: string;
  value: string;
  hint?: string;
  icon?: React.ReactNode;
  /** Tailwind classes for the icon chip background/text. */
  iconClassName?: string;
}

export function MetricCard({
  label,
  value,
  hint,
  icon,
  iconClassName,
}: MetricCardProps) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
            {value}
          </p>
          {hint ? (
            <p className="mt-1 text-xs text-slate-400">{hint}</p>
          ) : null}
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
