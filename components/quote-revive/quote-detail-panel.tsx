'use client';

import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { cn, formatCurrency, formatDate } from '@/lib/utils';
import {
  nextMessageLabel,
  statusBadgeClasses,
  statusLabel,
  stepStatusClasses,
  stepStatusLabel,
} from '@/lib/quote-revive/ui';
import {
  CheckCircle2,
  Clock,
  Mail,
  Pause,
  Pencil,
  Send,
  X,
} from 'lucide-react';
import type { QuoteWithSequence } from '@/lib/quote-revive/types';

interface QuoteDetailPanelProps {
  quote: QuoteWithSequence | null;
  onClose: () => void;
  onSendNow: (quoteId: string, stepId: string, message: string) => void;
  onPause: (quoteId: string) => void;
}

export function QuoteDetailPanel({
  quote,
  onClose,
  onSendNow,
  onPause,
}: QuoteDetailPanelProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState('');

  // Reset the editor whenever a different quote (or its next step) is shown.
  useEffect(() => {
    setDraft(quote?.nextStep?.messageTemplate ?? '');
    setIsEditing(false);
  }, [quote?.id, quote?.nextStep?.id]);

  if (!quote) return null;

  const nextStep = quote.nextStep;

  return (
    <div className="fixed inset-0 z-50 print:hidden">
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-[1px]"
        onClick={onClose}
        aria-hidden
      />
      <aside className="absolute right-0 top-0 flex h-full w-full max-w-lg flex-col bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="truncate text-lg font-bold text-slate-900">
                {quote.customerName}
              </h2>
              <span
                className={cn(
                  'rounded-full px-2 py-0.5 text-[11px] font-semibold',
                  statusBadgeClasses(quote.status)
                )}
              >
                {statusLabel(quote.status)}
              </span>
            </div>
            <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-500">
              <Mail className="h-3.5 w-3.5" />
              {quote.customerEmail || 'No email on file'}
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

        <div className="flex-1 space-y-6 overflow-y-auto px-6 py-5">
          {/* Summary */}
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
                Quote Value
              </span>
              <span className="text-2xl font-bold text-slate-900">
                {formatCurrency(quote.quoteAmount)}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-600">{quote.jobDescription}</p>
            <p className="mt-2 flex items-center gap-1.5 text-xs text-slate-400">
              <Clock className="h-3.5 w-3.5" />
              {nextMessageLabel(quote.daysUntilNext)}
            </p>
          </div>

          {/* Timeline */}
          <div>
            <h3 className="mb-3 text-sm font-semibold text-slate-900">
              Sequence Timeline
            </h3>
            <ol className="relative space-y-4 border-l border-slate-200 pl-5">
              <li className="relative">
                <span className="absolute -left-[27px] flex h-5 w-5 items-center justify-center rounded-full bg-slate-900 text-white">
                  <CheckCircle2 className="h-3 w-3" />
                </span>
                <p className="text-sm font-medium text-slate-900">Quote sent</p>
                <p className="text-xs text-slate-400">
                  {formatDate(quote.dateSent)}
                </p>
              </li>

              {quote.sequence.map((step) => {
                const isNext = nextStep?.id === step.id;
                return (
                  <li key={step.id} className="relative">
                    <span
                      className={cn(
                        'absolute -left-[27px] flex h-5 w-5 items-center justify-center rounded-full border-2 border-white',
                        step.status === 'SENT'
                          ? 'bg-green-500'
                          : isNext
                          ? 'bg-blue-500'
                          : 'bg-slate-300'
                      )}
                    />
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium text-slate-900">
                        Day {step.dayOffset} message
                        {isNext ? (
                          <span className="ml-2 text-xs font-semibold text-blue-600">
                            • Next
                          </span>
                        ) : null}
                      </p>
                      <span
                        className={cn(
                          'rounded-full px-2 py-0.5 text-[11px] font-semibold',
                          stepStatusClasses(step.status)
                        )}
                      >
                        {stepStatusLabel(step.status)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">
                      {formatDate(step.scheduledSendDate)}
                    </p>
                    <p className="mt-1 line-clamp-2 text-xs text-slate-500">
                      {step.messageTemplate}
                    </p>
                  </li>
                );
              })}
            </ol>
          </div>

          {/* Next message composer */}
          <div>
            <h3 className="mb-3 text-sm font-semibold text-slate-900">
              Next Automated Message
            </h3>
            {nextStep ? (
              <div className="rounded-lg border border-slate-200 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-500">
                    Day {nextStep.dayOffset} · scheduled{' '}
                    {formatDate(nextStep.scheduledSendDate)}
                  </span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsEditing((v) => !v)}
                  >
                    <Pencil className="mr-1.5 h-3.5 w-3.5" />
                    {isEditing ? 'Done' : 'Edit'}
                  </Button>
                </div>

                {isEditing ? (
                  <textarea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    rows={5}
                    className="flex w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
                  />
                ) : (
                  <p className="whitespace-pre-wrap rounded-md bg-slate-50 px-3 py-2.5 text-sm text-slate-700">
                    {draft}
                  </p>
                )}

                <div className="mt-3 flex items-center gap-2">
                  <Button
                    type="button"
                    onClick={() => onSendNow(quote.id, nextStep.id, draft)}
                  >
                    <Send className="mr-1.5 h-3.5 w-3.5" />
                    Send Now
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => onPause(quote.id)}
                  >
                    <Pause className="mr-1.5 h-3.5 w-3.5" />
                    Pause Sequence
                  </Button>
                </div>
              </div>
            ) : (
              <p className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-400">
                {quote.status === 'WON' || quote.status === 'LOST'
                  ? 'This quote is closed — no further messages scheduled.'
                  : 'Sequence complete. No further messages scheduled.'}
              </p>
            )}
          </div>
        </div>
      </aside>
    </div>
  );
}
