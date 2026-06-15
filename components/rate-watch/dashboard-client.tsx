'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MetricCard } from '@/components/rate-watch/metric-card';
import { VendorTable } from '@/components/rate-watch/vendor-table';
import { VendorDetail } from '@/components/rate-watch/vendor-detail';
import { AddVendorForm } from '@/components/rate-watch/add-vendor-form';
import { formatCurrency } from '@/lib/utils';
import { AlertCircle, ArrowLeft, FileText, Mail, Plus, TrendingDown } from 'lucide-react';
import type { BenchmarkResult } from '@/lib/benchmarking-engine';
import type { CompanySummary } from '@/lib/rate-watch-data';

interface DashboardClientProps {
  slug: string;
}

export function DashboardClient({ slug }: DashboardClientProps) {
  const [company, setCompany] = useState<CompanySummary | null>(null);
  const [benchmarkResults, setBenchmarkResults] = useState<BenchmarkResult[]>([]);
  const [selectedVendor, setSelectedVendor] = useState<BenchmarkResult | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalSpend, setTotalSpend] = useState(0);
  const [totalSavings, setTotalSavings] = useState(0);
  const [upcomingRenewals, setUpcomingRenewals] = useState(0);
  const [overpayingCount, setOverpayingCount] = useState(0);

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`/api/rate-watch/dashboard?slug=${encodeURIComponent(slug)}`);
      if (!response.ok) throw new Error('Failed to fetch dashboard data');

      const data = await response.json();
      setCompany(data.company);
      setBenchmarkResults(data.benchmarkResults);
      setTotalSpend(data.totalSpend);
      setTotalSavings(data.totalSavings);
      setUpcomingRenewals(data.upcomingRenewals);
      setOverpayingCount(data.overpayingCount);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }, [slug]);

  const handleAddVendor = async (formData: any) => {
    const response = await fetch('/api/rate-watch/contracts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...formData, companySlug: slug }),
    });
    if (!response.ok) throw new Error('Failed to add vendor');
    setShowAddForm(false);
    await fetchDashboardData();
  };

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900 mb-4"></div>
          <p className="text-slate-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Link href="/rate-watch" className="inline-flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900">
          <ArrowLeft className="w-4 h-4" /> Back to clients
        </Link>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">{error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Breadcrumb + title */}
      <div>
        <Link
          href="/rate-watch"
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-900 mb-3"
        >
          <ArrowLeft className="w-4 h-4" /> All clients
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">{company?.name}</h2>
            <p className="text-sm text-slate-600 mt-1">
              {company?.industry} · {company?.location}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href={`/rate-watch/${slug}/report`} target="_blank">
              <Button variant="outline" className="gap-2">
                <FileText className="h-4 w-4" /> Printable Report
              </Button>
            </Link>
            <Link href={`/api/rate-watch/${slug}/send-alerts`} target="_blank">
              <Button variant="outline" className="gap-2">
                <Mail className="h-4 w-4" /> Preview Email
              </Button>
            </Link>
            <Button onClick={() => setShowAddForm(true)} className="gap-2">
              <Plus className="h-4 w-4" /> Add Vendor
            </Button>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {overpayingCount > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900">
              {overpayingCount} vendor{overpayingCount !== 1 ? 's' : ''} identified as overpaying
            </h3>
            <p className="text-sm text-red-800 mt-1">
              Review and renegotiate these contracts to unlock {formatCurrency(totalSavings)} in annual savings.
            </p>
          </div>
        </div>
      )}

      {upcomingRenewals > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex gap-3">
          <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-amber-900">
              {upcomingRenewals} contract{upcomingRenewals !== 1 ? 's' : ''} renewing in the next 30 days
            </h3>
            <p className="text-sm text-amber-800 mt-1">
              Now is the best time to renegotiate rates before renewal.
            </p>
          </div>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Total Vendor Spend"
          value={formatCurrency(totalSpend)}
          description="Annual spend across all contracts"
          icon={<TrendingDown className="h-4 w-4" />}
        />
        <MetricCard
          title="Potential Savings Identified"
          value={formatCurrency(totalSavings)}
          description={`From ${overpayingCount} overpaying vendor${overpayingCount !== 1 ? 's' : ''}`}
          variant="success"
          icon={<TrendingDown className="h-4 w-4" />}
        />
        <MetricCard
          title="Upcoming Renewals"
          value={upcomingRenewals}
          description="Next 30 days"
          variant={upcomingRenewals > 0 ? 'warning' : 'default'}
        />
      </div>

      {/* Vendor Table */}
      <VendorTable benchmarkResults={benchmarkResults} onSelectVendor={setSelectedVendor} />

      {/* Modals */}
      {selectedVendor && (
        <VendorDetail result={selectedVendor} onClose={() => setSelectedVendor(null)} />
      )}

      {showAddForm && (
        <AddVendorForm
          onSubmit={handleAddVendor}
          onClose={() => setShowAddForm(false)}
          loading={false}
        />
      )}
    </div>
  );
}
