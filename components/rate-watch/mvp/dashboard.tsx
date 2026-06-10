'use client';

import React, { useMemo, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MetricCard } from '@/components/rate-watch/metric-card';
import { TrialBanner } from '@/components/rate-watch/mvp/trial-banner';
import { VendorTable } from '@/components/rate-watch/mvp/vendor-table';
import { NegotiationPanel } from '@/components/rate-watch/mvp/negotiation-panel';
import { AddVendorModal } from '@/components/rate-watch/mvp/add-vendor-modal';
import { SubscriptionModal } from '@/components/rate-watch/mvp/subscription-modal';
import { formatCurrency } from '@/lib/utils';
import {
  computeMetrics,
  enrichVendor,
  getDashboardData,
} from '@/lib/rate-watch/mock-data';
import {
  CORE_VENDOR_LIMIT,
  TIERS,
  canAddVendor,
  checkSubscriptionAccess,
  hasFeatureAccess,
} from '@/lib/rate-watch/tier-engine';
import type { Tier, Vendor, VendorRow } from '@/lib/rate-watch/types';
import {
  AlertTriangle,
  CalendarClock,
  Plus,
  Settings2,
  TrendingDown,
  Users,
} from 'lucide-react';

export function RateWatchDashboard() {
  const base = useMemo(() => getDashboardData('CORE'), []);

  const [tier, setTier] = useState<Tier>(base.user.tier);
  const [rows, setRows] = useState<VendorRow[]>(base.rows);
  const [selected, setSelected] = useState<VendorRow | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [subOpen, setSubOpen] = useState(false);
  const [subReason, setSubReason] = useState<string | null>(null);

  const metrics = useMemo(() => computeMetrics(rows), [rows]);
  const trial = useMemo(
    () => checkSubscriptionAccess(base.user),
    [base.user]
  );

  const unlimited = hasFeatureAccess(tier, 'UNLIMITED_VENDORS');

  const openUpgrade = (reason: string | null) => {
    setSubReason(reason);
    setSubOpen(true);
  };

  const handleAddClick = () => {
    const check = canAddVendor(tier, rows.length);
    if (!check.allowed) {
      openUpgrade(check.reason);
      return;
    }
    setShowAdd(true);
  };

  const handleAdd = (vendor: Vendor) => {
    setRows((prev) => [...prev, enrichVendor(vendor)]);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            {base.user.businessName}
          </h1>
          <p className="text-sm text-slate-500">
            {base.user.industryType} · Columbus, GA
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="secondary" className="gap-1.5 py-1">
            <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
            {TIERS[tier].name} · ${TIERS[tier].price}/mo
          </Badge>
          <Button variant="outline" size="sm" className="gap-2" onClick={handleAddClick}>
            <Plus className="h-4 w-4" />
            Add vendor
            <span className="text-slate-400">
              {unlimited ? '' : `(${rows.length}/${CORE_VENDOR_LIMIT})`}
            </span>
          </Button>
          <Button variant="outline" size="sm" className="gap-2" onClick={() => openUpgrade(null)}>
            <Settings2 className="h-4 w-4" />
            Manage plan
          </Button>
        </div>
      </div>

      <TrialBanner trial={trial} tierName={TIERS[tier].name} onUpgrade={() => openUpgrade(null)} />

      {/* Metric cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          title="Total Vendors Tracked"
          value={metrics.totalVendors}
          description={
            unlimited ? 'Unlimited on Pro' : `${rows.length} of ${CORE_VENDOR_LIMIT} on Core`
          }
          icon={<Users className="h-4 w-4" />}
        />
        <MetricCard
          title="Total Potential Savings (Annualized)"
          value={formatCurrency(metrics.totalPotentialSavingsAnnual)}
          description={`Across ${metrics.overpayingCount} overpaying vendor${
            metrics.overpayingCount !== 1 ? 's' : ''
          }`}
          variant="success"
          icon={<TrendingDown className="h-4 w-4" />}
        />
        <MetricCard
          title="Upcoming Renewals (Next 60 Days)"
          value={metrics.upcomingRenewals60}
          description="Best window to renegotiate"
          variant={metrics.upcomingRenewals60 > 0 ? 'warning' : 'default'}
          icon={<CalendarClock className="h-4 w-4" />}
        />
      </div>

      {/* Action-required callout */}
      {metrics.upcomingRenewals60 > 0 && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
          <div>
            <p className="font-semibold text-amber-900">
              {metrics.upcomingRenewals60} contract
              {metrics.upcomingRenewals60 !== 1 ? 's' : ''} renewing within 60 days
            </p>
            <p className="text-sm text-amber-800">
              Review and renegotiate now to lock in up to{' '}
              {formatCurrency(metrics.totalPotentialSavingsAnnual)} in annual savings.
            </p>
          </div>
        </div>
      )}

      <VendorTable rows={rows} onReview={setSelected} />

      {/* Slide-outs / modals */}
      <NegotiationPanel
        row={selected}
        tier={tier}
        onClose={() => setSelected(null)}
        onUpgrade={(reason) => {
          setSelected(null);
          openUpgrade(reason);
        }}
      />
      <AddVendorModal open={showAdd} onClose={() => setShowAdd(false)} onAdd={handleAdd} />
      <SubscriptionModal
        open={subOpen}
        onClose={() => setSubOpen(false)}
        currentTier={tier}
        onSelectTier={(t) => {
          setTier(t);
          setSubOpen(false);
        }}
        reason={subReason}
      />
    </div>
  );
}
