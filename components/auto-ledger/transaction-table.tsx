import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn, formatCurrencyDetailed, formatDate } from '@/lib/utils';
import { CheckCircle2, FileDown, Flag, Lock } from 'lucide-react';
import type { ConnectedAccount, Transaction } from '@/lib/auto-ledger/types';

interface TransactionTableProps {
  transactions: Transaction[];
  accounts: ConnectedAccount[];
  /** Whether the current tier can use CPA export. */
  canExport: boolean;
  onExportClick: () => void;
}

function accountLabel(
  accounts: ConnectedAccount[],
  accountId: string
): string {
  const a = accounts.find((acc) => acc.id === accountId);
  if (!a) return 'Account';
  const kind = a.accountType === 'CHECKING' ? 'Checking' : 'Card';
  return `${a.institutionName} ${kind} ••${a.mask ?? ''}`;
}

export function TransactionTable({
  transactions,
  accounts,
  canExport,
  onExportClick,
}: TransactionTableProps) {
  return (
    <Card className="overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-5">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-slate-900">
            Transactions, in plain English
          </h2>
          <p className="text-sm text-slate-500">
            Every line categorized and explained — no accounting degree required.
          </p>
        </div>
        <Button
          variant={canExport ? 'default' : 'outline'}
          size="sm"
          onClick={onExportClick}
          className="gap-2"
        >
          {canExport ? (
            <FileDown className="h-4 w-4" />
          ) : (
            <Lock className="h-4 w-4" />
          )}
          Export to CPA
        </Button>
      </div>

      {/* Desktop table */}
      <div className="hidden md:block">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
              <th className="px-5 py-3 font-semibold">Date</th>
              <th className="px-5 py-3 text-right font-semibold">Amount</th>
              <th className="px-5 py-3 font-semibold">The story</th>
              <th className="px-5 py-3 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((t) => (
              <tr
                key={t.id}
                className="border-b border-slate-100 last:border-0 hover:bg-slate-50/70"
              >
                <td className="whitespace-nowrap px-5 py-4 align-top text-slate-500">
                  {formatDate(t.date)}
                </td>
                <td className="whitespace-nowrap px-5 py-4 text-right align-top">
                  <span
                    className={cn(
                      'font-semibold tabular-nums',
                      t.amount > 0 ? 'text-green-600' : 'text-slate-900'
                    )}
                  >
                    {t.amount > 0 ? '+' : '−'}
                    {formatCurrencyDetailed(Math.abs(t.amount))}
                  </span>
                </td>
                {/* The hero column */}
                <td className="px-5 py-4 align-top">
                  <div className="flex items-center gap-2">
                    <span className="inline-flex rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                      {t.aiCategory}
                    </span>
                  </div>
                  <p className="mt-1.5 max-w-md text-[15px] font-medium leading-snug text-slate-900">
                    {t.plainEnglishNote}
                  </p>
                  <p className="mt-1 font-mono text-[11px] uppercase tracking-wide text-slate-400">
                    {t.rawDescription} · {accountLabel(accounts, t.accountId)}
                  </p>
                </td>
                <td className="whitespace-nowrap px-5 py-4 align-top">
                  <StatusBadge status={t.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="divide-y divide-slate-100 md:hidden">
        {transactions.map((t) => (
          <div key={t.id} className="p-4">
            <div className="flex items-start justify-between gap-3">
              <span className="inline-flex rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                {t.aiCategory}
              </span>
              <span
                className={cn(
                  'font-semibold tabular-nums',
                  t.amount > 0 ? 'text-green-600' : 'text-slate-900'
                )}
              >
                {t.amount > 0 ? '+' : '−'}
                {formatCurrencyDetailed(Math.abs(t.amount))}
              </span>
            </div>
            <p className="mt-2 text-[15px] font-medium leading-snug text-slate-900">
              {t.plainEnglishNote}
            </p>
            <div className="mt-2 flex items-center justify-between gap-2">
              <p className="font-mono text-[11px] uppercase tracking-wide text-slate-400">
                {formatDate(t.date)} · {t.rawDescription}
              </p>
              <StatusBadge status={t.status} />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function StatusBadge({ status }: { status: Transaction['status'] }) {
  if (status === 'FLAGGED') {
    return (
      <Badge variant="warning" className="gap-1">
        <Flag className="h-3 w-3" />
        Flagged
      </Badge>
    );
  }
  return (
    <Badge variant="success" className="gap-1">
      <CheckCircle2 className="h-3 w-3" />
      Reconciled
    </Badge>
  );
}
