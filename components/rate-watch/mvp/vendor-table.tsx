import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn, formatCurrency, formatDate } from '@/lib/utils';
import { AlertTriangle, ArrowRight } from 'lucide-react';
import type { VendorRow } from '@/lib/rate-watch/types';

interface VendorTableProps {
  rows: VendorRow[];
  onReview: (row: VendorRow) => void;
}

function rateLabel(rate: number, frequency: 'MONTHLY' | 'ANNUAL'): string {
  return `${formatCurrency(rate)}${frequency === 'MONTHLY' ? '/mo' : '/yr'}`;
}

/** The "Premium Paid" cell — the financial focal point. */
function PremiumCell({ row }: { row: VendorRow }) {
  const { status } = row.benchmark;
  if (status === 'OVERPAYING') {
    return (
      <div className="text-right">
        <div className="font-semibold tabular-nums text-red-600">
          +{formatCurrency(row.annualPremium)}/yr
        </div>
        <div className="text-xs text-red-400">
          +{row.benchmark.variancePct.toFixed(0)}% over market
        </div>
      </div>
    );
  }
  if (status === 'GREAT_DEAL') {
    return (
      <div className="text-right">
        <div className="font-semibold tabular-nums text-green-600">
          −{formatCurrency(Math.abs(row.benchmark.varianceAmount) * (row.vendor.frequency === 'MONTHLY' ? 12 : 1))}/yr
        </div>
        <div className="text-xs text-green-500">below market</div>
      </div>
    );
  }
  return (
    <div className="text-right">
      <div className="font-semibold tabular-nums text-green-600">At market</div>
      <div className="text-xs text-slate-400">fairly priced</div>
    </div>
  );
}

function RenewalCell({ row }: { row: VendorRow }) {
  return (
    <div>
      <div className="text-slate-700">{formatDate(row.vendor.renewalDate)}</div>
      <div
        className={cn(
          'text-xs',
          row.actionRequired ? 'font-medium text-amber-600' : 'text-slate-400'
        )}
      >
        in {row.daysUntilRenewal} days
      </div>
    </div>
  );
}

export function VendorTable({ rows, onReview }: VendorTableProps) {
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-slate-200 p-5">
        <h2 className="text-lg font-semibold tracking-tight text-slate-900">
          Vendor benchmarking
        </h2>
        <p className="text-sm text-slate-500">
          Your rates vs. the current Columbus, GA market.
        </p>
      </div>

      {/* Desktop */}
      <div className="hidden md:block">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
              <th className="px-5 py-3">Vendor</th>
              <th className="px-5 py-3">Category</th>
              <th className="px-5 py-3 text-right">Current rate</th>
              <th className="px-5 py-3 text-right">Local market</th>
              <th className="px-5 py-3 text-right">Premium paid</th>
              <th className="px-5 py-3">Renewal</th>
              <th className="px-5 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.vendor.id}
                className="border-b border-slate-100 last:border-0 hover:bg-slate-50/70"
              >
                <td className="px-5 py-4 align-middle font-medium text-slate-900">
                  {row.vendor.name}
                </td>
                <td className="px-5 py-4 align-middle">
                  <Badge variant="secondary">{row.vendor.category}</Badge>
                </td>
                <td className="px-5 py-4 text-right align-middle tabular-nums text-slate-900">
                  {rateLabel(row.vendor.currentRate, row.vendor.frequency)}
                </td>
                <td className="px-5 py-4 text-right align-middle tabular-nums text-slate-500">
                  {rateLabel(row.benchmark.localMarketRate, row.vendor.frequency)}
                </td>
                <td className="px-5 py-4 align-middle">
                  <PremiumCell row={row} />
                </td>
                <td className="px-5 py-4 align-middle">
                  <RenewalCell row={row} />
                </td>
                <td className="px-5 py-4 text-right align-middle">
                  {row.actionRequired ? (
                    <Button size="sm" onClick={() => onReview(row)} className="gap-1.5">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Review &amp; Negotiate
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => onReview(row)}
                      className="gap-1 text-slate-500"
                    >
                      View
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile */}
      <div className="divide-y divide-slate-100 md:hidden">
        {rows.map((row) => (
          <div key={row.vendor.id} className="p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium text-slate-900">{row.vendor.name}</p>
                <Badge variant="secondary" className="mt-1">
                  {row.vendor.category}
                </Badge>
              </div>
              <PremiumCell row={row} />
            </div>
            <div className="mt-3 flex items-center justify-between gap-2 text-xs text-slate-500">
              <span>
                {rateLabel(row.vendor.currentRate, row.vendor.frequency)} vs{' '}
                {rateLabel(row.benchmark.localMarketRate, row.vendor.frequency)}
              </span>
              <span className={row.actionRequired ? 'font-medium text-amber-600' : ''}>
                renews in {row.daysUntilRenewal}d
              </span>
            </div>
            <Button
              size="sm"
              variant={row.actionRequired ? 'default' : 'outline'}
              onClick={() => onReview(row)}
              className="mt-3 w-full gap-1.5"
            >
              {row.actionRequired ? (
                <>
                  <AlertTriangle className="h-3.5 w-3.5" /> Review &amp; Negotiate
                </>
              ) : (
                'View details'
              )}
            </Button>
          </div>
        ))}
      </div>
    </Card>
  );
}
