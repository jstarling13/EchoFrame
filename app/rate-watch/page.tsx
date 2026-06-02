'use client';

import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { MetricCard } from '@/components/rate-watch/metric-card';
import { VendorTable } from '@/components/rate-watch/vendor-table';
import { VendorDetail } from '@/components/rate-watch/vendor-detail';
import { AddVendorForm } from '@/components/rate-watch/add-vendor-form';
import { formatCurrency } from '@/lib/utils';
import { AlertCircle, Plus, TrendingDown } from 'lucide-react';
import type { BenchmarkResult } from '@/lib/benchmarking-engine';

export default function RateWatchPage() {
  const [benchmarkResults, setBenchmarkResults] = useState<BenchmarkResult[]>([]);
  const [selectedVendor, setSelectedVendor] = useState<BenchmarkResult | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [totalSpend, setTotalSpend] = useState(0);
  const [totalSavings, setTotalSavings] = useState(0);
  const [upcomingRenewals, setUpcomingRenewals] = useState(0);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/rate-watch/dashboard');
      if (!response.ok) throw new Error('Failed to fetch dashboard data');

      const data = await response.json();
      setBenchmarkResults(data.benchmarkResults);
      setTotalSpend(data.totalSpend);
      setTotalSavings(data.totalSavings);
      setUpcomingRenewals(data.upcomingRenewals);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddVendor = async (formData: any) => {
    try {
      const response = await fetch('/api/rate-watch/contracts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error('Failed to add vendor');

      setShowAddForm(false);
      await fetchDashboardData();
    } catch (error) {
      throw error;
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

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

  const overpayingCount = benchmarkResults.filter(
    (r) => r.status === 'OVERPAYING'
  ).length;

  return (
    <div className="space-y-8">
      {/* Action Bar */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-slate-900">Dashboard</h2>
        <Button onClick={() => setShowAddForm(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Vendor
        </Button>
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
              Review and renegotiate these contracts to unlock savings.
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
      <VendorTable
        benchmarkResults={benchmarkResults}
        onSelectVendor={setSelectedVendor}
      />

      {/* Modals */}
      {selectedVendor && (
        <VendorDetail
          result={selectedVendor}
          onClose={() => setSelectedVendor(null)}
        />
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
