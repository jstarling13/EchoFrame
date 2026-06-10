'use client';

import React, { useMemo, useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { MetricCard } from '@/components/quote-revive/metric-card';
import { QuoteBoard } from '@/components/quote-revive/quote-board';
import { AddQuoteModal } from '@/components/quote-revive/add-quote-modal';
import { QuoteDetailPanel } from '@/components/quote-revive/quote-detail-panel';
import { formatCurrency } from '@/lib/utils';
import {
  computeMetrics,
  enrichQuote,
  getDashboardData,
} from '@/lib/quote-revive/mock-data';
import { getNextStep, daysUntil } from '@/lib/quote-revive/sequence-generator';
import { ArrowLeft, DollarSign, Plus, Send, Trophy } from 'lucide-react';
import type {
  FollowUpSequenceStep,
  Quote,
  QuoteWithSequence,
} from '@/lib/quote-revive/types';

/** Recompute nextStep/daysUntilNext after a sequence mutation. */
function withRecomputedNext(
  quote: QuoteWithSequence,
  sequence: FollowUpSequenceStep[]
): QuoteWithSequence {
  const nextStep = getNextStep(sequence);
  return {
    ...quote,
    sequence,
    nextStep,
    daysUntilNext: nextStep ? daysUntil(nextStep.scheduledSendDate) : null,
  };
}

export function DashboardClient() {
  // Initialize once from the mock dataset (run through the real engine).
  const [quotes, setQuotes] = useState<QuoteWithSequence[]>(
    () => getDashboardData().quotes
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);

  const metrics = useMemo(() => computeMetrics(quotes), [quotes]);
  const selected = useMemo(
    () => quotes.find((q) => q.id === selectedId) ?? null,
    [quotes, selectedId]
  );

  const openCount = quotes.filter(
    (q) => q.status !== 'WON' && q.status !== 'LOST'
  ).length;

  const handleAdd = (quote: Quote) => {
    setQuotes((prev) => [enrichQuote(quote), ...prev]);
  };

  const handleSendNow = (quoteId: string, stepId: string, message: string) => {
    setQuotes((prev) =>
      prev.map((q) => {
        if (q.id !== quoteId) return q;
        const sequence = q.sequence.map((s) =>
          s.id === stepId
            ? { ...s, status: 'SENT' as const, messageTemplate: message }
            : s
        );
        return withRecomputedNext(
          { ...q, lastContactDate: new Date() },
          sequence
        );
      })
    );
  };

  const handlePause = (quoteId: string) => {
    setQuotes((prev) =>
      prev.map((q) => {
        if (q.id !== quoteId) return q;
        const sequence = q.sequence.map((s) =>
          s.status === 'PENDING' ? { ...s, status: 'PAUSED' as const } : s
        );
        return withRecomputedNext(q, sequence);
      })
    );
  };

  return (
    <div>
      {/* Page heading */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Link
            href="/"
            className="mb-1 inline-flex items-center gap-1 text-xs font-medium text-slate-400 hover:text-slate-600"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            EchoFrame
          </Link>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Pipeline Dashboard
          </h1>
          <p className="text-sm text-slate-500">
            {openCount} open quote{openCount === 1 ? '' : 's'} in play
          </p>
        </div>
        <Button onClick={() => setShowAdd(true)}>
          <Plus className="mr-1.5 h-4 w-4" />
          Add Quote
        </Button>
      </div>

      {/* Metrics */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <MetricCard
          label="Total Open Quote Value"
          value={formatCurrency(metrics.totalOpenValue)}
          hint="Across fresh, in-sequence & cold"
          icon={<DollarSign className="h-5 w-5" />}
          iconClassName="bg-blue-50 text-blue-600"
        />
        <MetricCard
          label="Follow-ups Sent This Week"
          value={String(metrics.followUpsSentThisWeek)}
          hint="Automated touches in the last 7 days"
          icon={<Send className="h-5 w-5" />}
          iconClassName="bg-amber-50 text-amber-600"
        />
        <MetricCard
          label="Jobs Won via Revive"
          value={String(metrics.jobsWonViaRevive)}
          hint="Closed after a follow-up sequence"
          icon={<Trophy className="h-5 w-5" />}
          iconClassName="bg-green-50 text-green-600"
        />
      </div>

      {/* Board */}
      <QuoteBoard quotes={quotes} onSelect={(q) => setSelectedId(q.id)} />

      {/* Slide-outs */}
      <AddQuoteModal
        open={showAdd}
        onClose={() => setShowAdd(false)}
        onAdd={handleAdd}
      />
      <QuoteDetailPanel
        quote={selected}
        onClose={() => setSelectedId(null)}
        onSendNow={handleSendNow}
        onPause={handlePause}
      />
    </div>
  );
}
