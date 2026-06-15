'use client';

import React, { useMemo, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { MetricCard } from '@/components/rate-watch/metric-card';
import { ShiftTable } from '@/components/shift-lens/shift-table';
import { WeeklyReportPanel } from '@/components/shift-lens/weekly-report-panel';
import { formatCurrency } from '@/lib/utils';
import {
  buildShifts,
  computeMetrics,
  getUser,
} from '@/lib/shift-lens/mock-data';
import { getPricingTier } from '@/lib/shift-lens/pricing-engine';
import { buildWeeklyNarrative, sweepShifts } from '@/lib/shift-lens/recommendations';
import type {
  ScheduleRecommendation,
  Shift,
} from '@/lib/shift-lens/types';
import {
  BadgeCheck,
  CalendarClock,
  CreditCard,
  DollarSign,
  Droplets,
  FileBarChart,
  Percent,
  RefreshCw,
  Sparkles,
} from 'lucide-react';

export function ShiftLensDashboard() {
  const user = useMemo(() => getUser(), []);
  const pricing = getPricingTier(user);

  const [shifts, setShifts] = useState<Shift[]>([]);
  const [recommendations, setRecommendations] = useState<ScheduleRecommendation[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);

  const synced = shifts.length > 0;
  const metrics = useMemo(() => computeMetrics(shifts), [shifts]);
  const narrative = useMemo(() => buildWeeklyNarrative(shifts), [shifts]);

  const handleSync = () => {
    setSyncing(true);
    // Simulate a POS pull.
    setTimeout(() => {
      const fresh = buildShifts();
      setShifts(fresh);
      setRecommendations(sweepShifts(fresh).recommendations);
      setSyncing(false);
    }, 650);
  };

  const setRecStatus = (id: string, status: ScheduleRecommendation['status']) =>
    setRecommendations((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status } : r))
    );

  return (
    <div className="space-y-6">
      {/* Waitlist banner */}
      {user.waitlistStatus === 'EARLY_BIRD_LOCKED' && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-300 bg-gradient-to-r from-amber-50 to-white px-5 py-3.5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">
                You&apos;re in — your Early Bird rate is locked. 🎉
              </p>
              <p className="text-xs text-slate-600">
                Thanks for joining the waitlist. You&apos;ll keep{' '}
                <span className="font-semibold text-amber-700">
                  ${pricing.price}/mo
                </span>{' '}
                for your first year — instead of the ${149}/mo standard rate.
              </p>
            </div>
          </div>
          <span className="rounded-full bg-amber-600 px-3 py-1 text-xs font-bold uppercase tracking-wide text-white">
            Early Bird Locked
          </span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            {user.businessName}
          </h1>
          <p className="text-sm text-slate-500">Shift P&amp;L · last 7 days</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            disabled={!synced}
            onClick={() => setReportOpen(true)}
          >
            <FileBarChart className="h-4 w-4" />
            View weekly report
          </Button>
          <Button size="sm" className="gap-2" onClick={handleSync} disabled={syncing}>
            <RefreshCw className={syncing ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />
            {syncing ? 'Syncing…' : synced ? 'Re-sync shifts' : 'Sync recent shifts'}
          </Button>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          title="Net Margin (Last 7 Days)"
          value={formatCurrency(metrics.netMargin7d)}
          description={synced ? `${formatCurrency(metrics.totalRevenue7d)} revenue` : 'Sync to calculate'}
          variant="success"
          icon={<DollarSign className="h-4 w-4" />}
        />
        <MetricCard
          title="Average Labor %"
          value={synced ? `${metrics.avgLaborPct}%` : '—'}
          description="Labor as % of revenue"
          variant={metrics.avgLaborPct > 35 ? 'danger' : metrics.avgLaborPct >= 25 ? 'warning' : 'default'}
          icon={<Percent className="h-4 w-4" />}
        />
        <MetricCard
          title="Bleeding Shifts (Needs Action)"
          value={metrics.bleedingCount}
          description={metrics.bleedingCount > 0 ? 'Losing money on labor' : synced ? 'All shifts healthy' : 'Sync to detect'}
          variant={metrics.bleedingCount > 0 ? 'danger' : 'default'}
          icon={<Droplets className="h-4 w-4" />}
        />
      </div>

      {/* Integration status */}
      <Card className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-sm font-semibold text-slate-900">Integration status</h2>
          <div className="flex flex-wrap gap-6">
            <IntegrationItem
              icon={<CreditCard className="h-4 w-4" />}
              label="POS Connected"
              value={user.posIntegration}
            />
            <IntegrationItem
              icon={<CalendarClock className="h-4 w-4" />}
              label="Scheduling Connected"
              value={user.scheduleIntegration}
            />
          </div>
        </div>
      </Card>

      {/* Shifts or empty state */}
      {synced ? (
        <ShiftTable shifts={shifts} />
      ) : (
        <Card className="flex flex-col items-center justify-center gap-3 p-12 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-500">
            <RefreshCw className="h-6 w-6" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900">No shifts synced yet</h3>
          <p className="max-w-sm text-sm text-slate-500">
            Pull your last 7 days from {user.posIntegration} and {user.scheduleIntegration} to see
            shift-by-shift profitability and spot where labor is bleeding margin.
          </p>
          <Button className="mt-2 gap-2" onClick={handleSync} disabled={syncing}>
            <RefreshCw className={syncing ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />
            {syncing ? 'Syncing…' : 'Sync recent shifts'}
          </Button>
        </Card>
      )}

      <WeeklyReportPanel
        open={reportOpen}
        onClose={() => setReportOpen(false)}
        narrative={narrative}
        recommendations={recommendations}
        onApprove={(id) => setRecStatus(id, 'APPROVED')}
        onDismiss={(id) => setRecStatus(id, 'DISMISSED')}
      />
    </div>
  );
}

function IntegrationItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | null;
}) {
  const connected = Boolean(value);
  return (
    <div className="flex items-center gap-2.5">
      <div
        className={
          connected
            ? 'flex h-8 w-8 items-center justify-center rounded-lg bg-green-100 text-green-700'
            : 'flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-400'
        }
      >
        {icon}
      </div>
      <div>
        <p className="flex items-center gap-1 text-sm font-medium text-slate-900">
          {label}
          {connected ? <BadgeCheck className="h-4 w-4 text-green-600" /> : null}
        </p>
        <p className="text-xs text-slate-500">
          {connected ? value : 'Not connected'}
        </p>
      </div>
    </div>
  );
}
