import { notFound } from 'next/navigation';
import { getCompanyDashboard } from '@/lib/rate-watch-data';
import { formatCurrencyDetailed, formatCurrency } from '@/lib/utils';
import { PrintButton } from '@/components/rate-watch/print-button';

export const dynamic = 'force-dynamic';

interface PageProps {
  params: Promise<{ slug: string }>;
}

const bracketLabel: Record<string, string> = {
  SMALL: '1–10 employees',
  MEDIUM: '11–50 employees',
  LARGE: '50+ employees',
};

function statusPill(status: string, variance: number) {
  if (status === 'OVERPAYING')
    return <span className="inline-block rounded-full bg-red-100 text-red-800 px-2.5 py-0.5 text-xs font-semibold">Overpaying +{variance}%</span>;
  if (status === 'GREAT_DEAL')
    return <span className="inline-block rounded-full bg-green-100 text-green-800 px-2.5 py-0.5 text-xs font-semibold">Great Deal {variance}%</span>;
  return <span className="inline-block rounded-full bg-slate-100 text-slate-700 px-2.5 py-0.5 text-xs font-semibold">Fair</span>;
}

function fmtDate(iso: string) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(iso));
}

export default async function ReportPage({ params }: PageProps) {
  const { slug } = await params;
  const dashboard = await getCompanyDashboard(slug);
  if (!dashboard) notFound();

  const { company, benchmarkResults, totalSpend, totalSavings, upcomingRenewals, overpayingCount } = dashboard;
  const generatedOn = new Intl.DateTimeFormat('en-US', { dateStyle: 'long' }).format(new Date());
  const overpaying = benchmarkResults.filter((r) => r.status === 'OVERPAYING');

  return (
    <div className="min-h-screen bg-slate-100 print:bg-white py-8 print:py-0">
      <div className="mx-auto max-w-4xl px-6 print:px-0">
        {/* Toolbar (hidden in print) */}
        <div className="mb-6 flex items-center justify-between print:hidden">
          <a href={`/rate-watch/${slug}`} className="text-sm text-slate-600 hover:text-slate-900">
            ← Back to dashboard
          </a>
          <PrintButton />
        </div>

        {/* Report sheet */}
        <div className="bg-white rounded-lg shadow-sm print:shadow-none border border-slate-200 print:border-0 overflow-hidden">
          {/* Header */}
          <div className="bg-slate-900 text-white px-10 py-8 print:px-8">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-xs uppercase tracking-widest text-slate-400">EchoFrame Intelligence</div>
                <h1 className="text-2xl font-bold mt-1">Rate Watch — Vendor Savings Report</h1>
              </div>
              <div className="text-right text-xs text-slate-400">
                <div>Prepared {generatedOn}</div>
                <div>{company.location}</div>
              </div>
            </div>
            <div className="mt-6 border-t border-slate-700 pt-4">
              <div className="text-lg font-semibold">{company.name}</div>
              <div className="text-sm text-slate-300">
                {company.industry} · {bracketLabel[company.companySizeBracket] ?? company.companySizeBracket}
                {company.contactName ? ` · Attn: ${company.contactName}` : ''}
              </div>
            </div>
          </div>

          {/* Executive summary */}
          <div className="px-10 py-8 print:px-8">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-4">Executive Summary</h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-lg border border-slate-200 p-4">
                <div className="text-xs text-slate-500">Total Annual Vendor Spend</div>
                <div className="text-2xl font-bold text-slate-900 mt-1">{formatCurrency(totalSpend)}</div>
              </div>
              <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                <div className="text-xs text-green-700">Potential Annual Savings</div>
                <div className="text-2xl font-bold text-green-800 mt-1">{formatCurrency(totalSavings)}</div>
              </div>
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                <div className="text-xs text-amber-700">Renewals (Next 30 Days)</div>
                <div className="text-2xl font-bold text-amber-800 mt-1">{upcomingRenewals}</div>
              </div>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed mt-5">
              Based on current {company.location} market benchmarks for {bracketLabel[company.companySizeBracket]?.toLowerCase() ?? 'similar'} businesses,
              we reviewed {benchmarkResults.length} active vendor contracts for {company.name}.
              We identified <strong>{overpayingCount}</strong> contract{overpayingCount !== 1 ? 's' : ''} priced above market,
              representing <strong>{formatCurrency(totalSavings)}</strong> in potential annual savings through renegotiation.
            </p>
          </div>

          {/* Full vendor table */}
          <div className="px-10 pb-8 print:px-8">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-3">All Vendor Contracts</h2>
            <table className="w-full text-sm border border-slate-200 rounded-lg overflow-hidden">
              <thead>
                <tr className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-4 py-2 font-semibold">Vendor</th>
                  <th className="px-4 py-2 font-semibold">Category</th>
                  <th className="px-4 py-2 font-semibold text-right">Current</th>
                  <th className="px-4 py-2 font-semibold text-right">Market</th>
                  <th className="px-4 py-2 font-semibold">Status</th>
                  <th className="px-4 py-2 font-semibold">Renews</th>
                </tr>
              </thead>
              <tbody>
                {benchmarkResults.map((r) => (
                  <tr key={r.contractId} className={`border-t border-slate-200 ${r.status === 'OVERPAYING' ? 'bg-red-50' : ''}`}>
                    <td className="px-4 py-2.5 font-medium text-slate-900">{r.vendorName}</td>
                    <td className="px-4 py-2.5 text-slate-600">{r.category}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-slate-900">{formatCurrencyDetailed(r.currentRate)}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-slate-600">{formatCurrencyDetailed(r.benchmarkRate)}</td>
                    <td className="px-4 py-2.5">{statusPill(r.status, r.variance)}</td>
                    <td className="px-4 py-2.5 text-slate-600">{fmtDate(r.renewalDate)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Renegotiation playbook */}
          {overpaying.length > 0 && (
            <div className="px-10 pb-10 print:px-8">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-3">Renegotiation Playbook</h2>
              <div className="space-y-4">
                {overpaying.map((r) => (
                  <div key={r.contractId} className="rounded-lg border border-slate-200 p-4 break-inside-avoid">
                    <div className="flex items-center justify-between mb-2">
                      <div className="font-semibold text-slate-900">{r.vendorName}</div>
                      <div className="text-sm font-semibold text-green-700">
                        Save {r.savingsEstimate ? formatCurrency(r.savingsEstimate) : '—'}/yr
                      </div>
                    </div>
                    <p className="text-sm text-slate-600 leading-relaxed">{r.renegotiationTalkingPoints}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="bg-slate-50 px-10 py-5 print:px-8 border-t border-slate-200 text-xs text-slate-500">
            EchoFrame Intelligence · Rate Watch · Benchmarks reflect {company.location} averages and are for guidance only.
          </div>
        </div>
      </div>
    </div>
  );
}
