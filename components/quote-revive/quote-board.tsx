import React from 'react';
import { QuoteCard } from '@/components/quote-revive/quote-card';
import { BOARD_COLUMNS } from '@/lib/quote-revive/ui';
import { cn, formatCurrency } from '@/lib/utils';
import type { QuoteColumn, QuoteWithSequence } from '@/lib/quote-revive/types';

interface QuoteBoardProps {
  quotes: QuoteWithSequence[];
  onSelect: (quote: QuoteWithSequence) => void;
}

export function QuoteBoard({ quotes, onSelect }: QuoteBoardProps) {
  const byColumn = (col: QuoteColumn) =>
    quotes.filter((q) => q.column === col);

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      {BOARD_COLUMNS.map((column) => {
        const items = byColumn(column.key);
        const columnValue = items.reduce((sum, q) => sum + q.quoteAmount, 0);

        return (
          <section
            key={column.key}
            className="flex flex-col rounded-xl border border-slate-200 bg-slate-100/60"
          >
            <header className="flex items-center justify-between gap-2 px-4 pt-4 pb-3">
              <div className="flex items-center gap-2">
                <span className={cn('h-2.5 w-2.5 rounded-full', column.accent)} />
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">
                    {column.title}
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    {column.description}
                  </p>
                </div>
              </div>
              <span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-slate-600 shadow-sm">
                {items.length}
              </span>
            </header>

            <div className="flex-1 space-y-3 px-3 pb-3">
              {items.length === 0 ? (
                <p className="rounded-lg border border-dashed border-slate-300 bg-white/50 px-3 py-6 text-center text-xs text-slate-400">
                  No quotes here
                </p>
              ) : (
                items.map((quote) => (
                  <QuoteCard key={quote.id} quote={quote} onSelect={onSelect} />
                ))
              )}
            </div>

            {items.length > 0 ? (
              <footer className="border-t border-slate-200 px-4 py-2.5 text-xs text-slate-500">
                Column value:{' '}
                <span className="font-semibold text-slate-700">
                  {formatCurrency(columnValue)}
                </span>
              </footer>
            ) : null}
          </section>
        );
      })}
    </div>
  );
}
