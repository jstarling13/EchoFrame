'use client';

import React from 'react';
import { cn, formatDate } from '@/lib/utils';
import { Check, Lightbulb, ThumbsDown, X } from 'lucide-react';
import type { ScheduleRecommendation } from '@/lib/shift-lens/types';

interface WeeklyReportPanelProps {
  open: boolean;
  onClose: () => void;
  narrative: string;
  recommendations: ScheduleRecommendation[];
  onApprove: (id: string) => void;
  onDismiss: (id: string) => void;
}

export function WeeklyReportPanel({
  open,
  onClose,
  narrative,
  recommendations,
  onApprove,
  onDismiss,
}: WeeklyReportPanelProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 print:hidden">
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-[1px]"
        onClick={onClose}
        aria-hidden
      />
      <div className="absolute right-0 top-0 flex h-full w-full max-w-xl flex-col bg-white shadow-2xl">
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Weekly shift report</h2>
            <p className="text-xs text-slate-500">
              What changed, and what to do about it next week.
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

        <div className="flex-1 space-y-5 overflow-y-auto px-6 py-5">
          {/* Narrative */}
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              The story
            </p>
            <p className="mt-2 text-[15px] leading-relaxed text-slate-800">
              {narrative}
            </p>
          </div>

          {/* Recommendations */}
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Recommended schedule changes
            </p>
            {recommendations.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
                No changes recommended — your schedule is tracking healthy.
              </div>
            ) : (
              <div className="space-y-3">
                {recommendations.map((rec) => (
                  <div
                    key={rec.id}
                    className={cn(
                      'rounded-xl border p-4',
                      rec.status === 'APPROVED'
                        ? 'border-green-200 bg-green-50'
                        : rec.status === 'DISMISSED'
                        ? 'border-slate-200 bg-slate-50 opacity-70'
                        : 'border-amber-200 bg-amber-50'
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-amber-600 ring-1 ring-amber-200">
                        <Lightbulb className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                          Week of {formatDate(rec.weekStartDate)}
                        </p>
                        <p className="mt-0.5 text-sm font-medium leading-snug text-slate-800">
                          {rec.recommendationText}
                        </p>

                        {rec.status === 'PENDING' ? (
                          <div className="mt-3 flex gap-2">
                            <button
                              onClick={() => onApprove(rec.id)}
                              className="inline-flex items-center gap-1.5 rounded-md bg-green-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-green-700"
                            >
                              <Check className="h-3.5 w-3.5" /> Approve
                            </button>
                            <button
                              onClick={() => onDismiss(rec.id)}
                              className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                            >
                              <ThumbsDown className="h-3.5 w-3.5" /> Dismiss
                            </button>
                          </div>
                        ) : (
                          <p
                            className={cn(
                              'mt-2 text-xs font-semibold',
                              rec.status === 'APPROVED'
                                ? 'text-green-700'
                                : 'text-slate-400'
                            )}
                          >
                            {rec.status === 'APPROVED' ? '✓ Approved' : 'Dismissed'}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
