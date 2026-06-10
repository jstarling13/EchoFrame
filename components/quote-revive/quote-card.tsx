import React from 'react';
import { cn, formatCurrency } from '@/lib/utils';
import {
  countdownShort,
  statusBadgeClasses,
  statusLabel,
} from '@/lib/quote-revive/ui';
import { Clock, ChevronRight } from 'lucide-react';
import type { QuoteWithSequence } from '@/lib/quote-revive/types';

interface QuoteCardProps {
  quote: QuoteWithSequence;
  onSelect: (quote: QuoteWithSequence) => void;
}

export function QuoteCard({ quote, onSelect }: QuoteCardProps) {
  const overdue = quote.daysUntilNext !== null && quote.daysUntilNext < 0;
  const complete = quote.daysUntilNext === null;

  return (
    <button
      type="button"
      onClick={() => onSelect(quote)}
      className="group w-full rounded-lg border border-slate-200 bg-white p-4 text-left shadow-sm transition-all hover:border-slate-300 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-semibold text-slate-900">
            {quote.customerName}
          </p>
          <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">
            {quote.jobDescription}
          </p>
        </div>
        <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-slate-300 transition-colors group-hover:text-slate-500" />
      </div>

      <div className="mt-3 flex items-center justify-between">
        <span className="text-lg font-bold tracking-tight text-slate-900">
          {formatCurrency(quote.quoteAmount)}
        </span>
        <span
          className={cn(
            'rounded-full px-2 py-0.5 text-[11px] font-semibold',
            statusBadgeClasses(quote.status)
          )}
        >
          {statusLabel(quote.status)}
        </span>
      </div>

      <div
        className={cn(
          'mt-3 flex items-center gap-1.5 border-t border-slate-100 pt-2.5 text-xs font-medium',
          overdue ? 'text-red-600' : complete ? 'text-slate-400' : 'text-slate-500'
        )}
      >
        <Clock className="h-3.5 w-3.5" />
        {complete ? (
          <span>Sequence complete</span>
        ) : (
          <span>
            Next message {countdownShort(quote.daysUntilNext)}
          </span>
        )}
      </div>
    </button>
  );
}
