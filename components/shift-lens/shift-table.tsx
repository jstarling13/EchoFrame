import React from 'react';
import { Card } from '@/components/ui/card';
import { cn, formatCurrency, formatDate } from '@/lib/utils';
import type { Shift, ShiftStatus } from '@/lib/shift-lens/types';

const STATUS_STYLES: Record<
  ShiftStatus,
  { label: string; badge: string; pct: string; row: string }
> = {
  PROFITABLE: {
    label: 'Profitable',
    badge: 'bg-green-100 text-green-800 border border-green-200',
    pct: 'text-green-700',
    row: '',
  },
  BORDERLINE: {
    label: 'Borderline',
    badge: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
    pct: 'text-yellow-700',
    row: '',
  },
  BLEEDING: {
    label: 'Bleeding',
    badge: 'bg-red-100 text-red-800 border border-red-300',
    pct: 'text-red-700 font-bold',
    row: 'bg-red-50/60',
  },
};

function StatusBadge({ status }: { status: ShiftStatus }) {
  const s = STATUS_STYLES[status];
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold',
        s.badge
      )}
    >
      {status === 'BLEEDING' ? (
        <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
      ) : null}
      {s.label}
    </span>
  );
}

export function ShiftTable({ shifts }: { shifts: Shift[] }) {
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-slate-200 p-5">
        <h2 className="text-lg font-semibold tracking-tight text-slate-900">
          Shift-by-shift P&amp;L
        </h2>
        <p className="text-sm text-slate-500">Last 7 days · where the money is made and lost.</p>
      </div>

      {/* Desktop */}
      <div className="hidden md:block">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
              <th className="px-5 py-3">Date / Time</th>
              <th className="px-5 py-3">Shift</th>
              <th className="px-5 py-3 text-right">Revenue</th>
              <th className="px-5 py-3 text-right">Labor cost</th>
              <th className="px-5 py-3 text-right">Labor %</th>
              <th className="px-5 py-3 text-right">Net margin</th>
              <th className="px-5 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {shifts.map((shift) => {
              const s = STATUS_STYLES[shift.status];
              return (
                <tr
                  key={shift.id}
                  className={cn('border-b border-slate-100 last:border-0', s.row)}
                >
                  <td className="px-5 py-4 align-middle">
                    <div className="text-slate-700">{formatDate(shift.date)}</div>
                    <div className="text-xs text-slate-400">
                      {shift.startTime}–{shift.endTime}
                    </div>
                  </td>
                  <td className="px-5 py-4 align-middle font-medium text-slate-900">
                    {shift.shiftName}
                  </td>
                  <td className="px-5 py-4 text-right align-middle tabular-nums text-slate-900">
                    {formatCurrency(shift.totalRevenue)}
                  </td>
                  <td className="px-5 py-4 text-right align-middle tabular-nums text-slate-600">
                    {formatCurrency(shift.actualLaborCost)}
                  </td>
                  <td className={cn('px-5 py-4 text-right align-middle tabular-nums', s.pct)}>
                    {shift.laborPercentage}%
                  </td>
                  <td className="px-5 py-4 text-right align-middle tabular-nums font-semibold text-slate-900">
                    {formatCurrency(shift.netMargin)}
                  </td>
                  <td className="px-5 py-4 align-middle">
                    <StatusBadge status={shift.status} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile */}
      <div className="divide-y divide-slate-100 md:hidden">
        {shifts.map((shift) => {
          const s = STATUS_STYLES[shift.status];
          return (
            <div key={shift.id} className={cn('p-4', s.row)}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-slate-900">{shift.shiftName}</p>
                  <p className="text-xs text-slate-400">
                    {formatDate(shift.date)} · {shift.startTime}–{shift.endTime}
                  </p>
                </div>
                <StatusBadge status={shift.status} />
              </div>
              <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
                <div>
                  <p className="text-xs text-slate-400">Revenue</p>
                  <p className="tabular-nums text-slate-900">{formatCurrency(shift.totalRevenue)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Labor %</p>
                  <p className={cn('tabular-nums', s.pct)}>{shift.laborPercentage}%</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Net margin</p>
                  <p className="tabular-nums font-semibold text-slate-900">
                    {formatCurrency(shift.netMargin)}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
