'use client';

import React, { useMemo, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MetricCard, LockedMetricCard } from '@/components/auto-ledger/metric-card';
import { TransactionTable } from '@/components/auto-ledger/transaction-table';
import { SubscriptionModal } from '@/components/auto-ledger/subscription-modal';
import { formatCurrency } from '@/lib/utils';
import { getDashboardData, computeMetrics } from '@/lib/auto-ledger/mock-data';
import {
  TIERS,
  hasFeatureAccess,
  requiredTierFor,
} from '@/lib/auto-ledger/tier-engine';
import type { Tier } from '@/lib/auto-ledger/types';
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  CreditCard,
  Landmark,
  Lightbulb,
  Settings2,
  Wallet,
} from 'lucide-react';

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

function hoursSince(date: Date | null): number | null {
  if (!date) return null;
  return (Date.now() - date.getTime()) / (1000 * 60 * 60);
}

export function DashboardClient() {
  // Load the demo dataset once; tier is interactive so the upgrade gating is
  // fully demonstrable without a backend.
  const base = useMemo(() => getDashboardData('STARTER'), []);
  const { accounts, transactions, report } = base;

  const [tier, setTier] = useState<Tier>(base.user.subscriptionTier);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalReason, setModalReason] = useState<string | null>(null);

  const metrics = useMemo(() => computeMetrics(transactions), [transactions]);

  const canSeeTax = hasFeatureAccess(tier, 'TAX_ESTIMATES');
  const canExport = hasFeatureAccess(tier, 'CPA_EXPORTS');
  const netPositive = metrics.netCashflowMtd >= 0;

  const openUpgrade = (reason: string | null = null) => {
    setModalReason(reason);
    setModalOpen(true);
  };

  const handleExport = () => {
    if (canExport) {
      // In production this streams a CPA-ready file; here we just confirm.
      alert('Your CPA export is being prepared and will download shortly.');
      return;
    }
    openUpgrade(
      'One-click CPA exports are part of the Growth plan. Upgrade to hand your accountant a clean, categorized file in one click.'
    );
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            {base.user.businessName}
          </h1>
          <p className="text-sm text-slate-500">
            {MONTH_NAMES[report.month - 1]} {report.year} · books up to date
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="secondary" className="gap-1.5 py-1">
            <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
            {TIERS[tier].name} plan · ${TIERS[tier].price}/mo
          </Badge>
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() => openUpgrade(null)}
          >
            <Settings2 className="h-4 w-4" />
            Manage plan
          </Button>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          label="Net Cashflow (MTD)"
          value={`${netPositive ? '+' : '−'}${formatCurrency(
            Math.abs(metrics.netCashflowMtd)
          )}`}
          hint={`${formatCurrency(metrics.moneyInMtd)} in · ${formatCurrency(
            metrics.moneyOutMtd
          )} out`}
          valueClassName={netPositive ? 'text-green-600' : 'text-red-600'}
          icon={
            netPositive ? (
              <ArrowUpRight className="h-5 w-5" />
            ) : (
              <ArrowDownRight className="h-5 w-5" />
            )
          }
          iconClassName={
            netPositive
              ? 'bg-green-100 text-green-700'
              : 'bg-red-100 text-red-700'
          }
        />

        <MetricCard
          label="Unreviewed Transactions"
          value={String(metrics.unreviewedCount)}
          hint={
            metrics.unreviewedCount > 0
              ? 'Flagged for a quick human look'
              : 'All clear — nothing to review'
          }
          icon={<AlertTriangle className="h-5 w-5" />}
          iconClassName="bg-amber-100 text-amber-700"
        />

        {canSeeTax ? (
          <MetricCard
            label={`Q${Math.ceil(report.month / 3)} Tax Estimate`}
            value={formatCurrency(report.taxEstimateAmount ?? 0)}
            hint="Set this aside for quarterly taxes"
            icon={<Wallet className="h-5 w-5" />}
            iconClassName="bg-slate-900 text-white"
          />
        ) : (
          <LockedMetricCard
            label={`Q${Math.ceil(report.month / 3)} Tax Estimate`}
            value={formatCurrency(report.taxEstimateAmount ?? 0)}
            requiredTierName={TIERS[requiredTierFor('TAX_ESTIMATES')].name}
            onUpgrade={() =>
              openUpgrade(
                'Quarterly tax estimates come with the Growth plan, so you never get surprised by a tax bill again.'
              )
            }
          />
        )}
      </div>

      {/* Narrative + Recent syncs */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Monthly plain-English narrative */}
        <Card className="lg:col-span-2 p-6">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-amber-600">
              This month&apos;s story
            </span>
          </div>
          <p className="mt-3 text-[15px] leading-relaxed text-slate-700">
            {report.summaryText}
          </p>
          <div className="mt-4 flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
              <Lightbulb className="h-4 w-4" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">
                The one thing to do this month
              </p>
              <p className="mt-1 text-sm font-medium leading-snug text-slate-800">
                {report.actionItem}
              </p>
            </div>
          </div>
        </Card>

        {/* Recent syncs */}
        <Card className="p-6">
          <h2 className="text-sm font-semibold text-slate-900">Recent syncs</h2>
          <p className="text-xs text-slate-500">Connected accounts</p>
          <ul className="mt-4 space-y-3">
            {accounts.map((acc) => {
              const hrs = hoursSince(acc.lastSyncDate);
              const fresh = acc.syncStatus === 'HEALTHY' && hrs !== null && hrs < 24;
              return (
                <li key={acc.id} className="flex items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                    {acc.accountType === 'CHECKING' ? (
                      <Landmark className="h-4 w-4" />
                    ) : (
                      <CreditCard className="h-4 w-4" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-slate-900">
                      {acc.institutionName}
                    </p>
                    <p className="truncate text-xs text-slate-500">
                      {acc.accountType === 'CHECKING' ? 'Checking' : 'Credit card'}{' '}
                      ••{acc.mask}
                    </p>
                  </div>
                  {fresh ? (
                    <Badge variant="success" className="gap-1">
                      <CheckCircle2 className="h-3 w-3" />
                      Within 24hrs
                    </Badge>
                  ) : (
                    <Badge variant="warning" className="gap-1">
                      <Clock className="h-3 w-3" />
                      Stale
                    </Badge>
                  )}
                </li>
              );
            })}
          </ul>
        </Card>
      </div>

      {/* Transactions */}
      <TransactionTable
        transactions={transactions}
        accounts={accounts}
        canExport={canExport}
        onExportClick={handleExport}
      />

      <SubscriptionModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        currentTier={tier}
        onSelectTier={(t) => {
          setTier(t);
          setModalOpen(false);
        }}
        reason={modalReason}
      />
    </div>
  );
}
