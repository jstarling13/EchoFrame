'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatCurrency, formatDate, getStatusBadgeColor } from '@/lib/utils';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { BenchmarkResult } from '@/lib/benchmarking-engine';

interface VendorTableProps {
  benchmarkResults: BenchmarkResult[];
  onSelectVendor?: (result: BenchmarkResult) => void;
}

type SortColumn = 'vendorName' | 'category' | 'currentRate' | 'variance' | 'renewalDate';
type SortDirection = 'asc' | 'desc';

export function VendorTable({
  benchmarkResults,
  onSelectVendor,
}: VendorTableProps) {
  const [sortColumn, setSortColumn] = useState<SortColumn>('vendorName');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const getSortedData = () => {
    const data = [...benchmarkResults];
    data.sort((a, b) => {
      let aValue: any = a[sortColumn];
      let bValue: any = b[sortColumn];

      if (sortColumn === 'renewalDate') {
        aValue = new Date(a.renewalDate).getTime();
        bValue = new Date(b.renewalDate).getTime();
      } else if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = (bValue as string).toLowerCase();
      }

      if (sortDirection === 'asc') {
        return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
      } else {
        return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
      }
    });
    return data;
  };

  const SortIcon = ({ column }: { column: SortColumn }) => {
    if (sortColumn !== column) {
      return <div className="w-4 h-4 opacity-0" />;
    }
    return sortDirection === 'asc' ? (
      <ChevronUp className="w-4 h-4" />
    ) : (
      <ChevronDown className="w-4 h-4" />
    );
  };

  const sortedData = getSortedData();

  // Highlight overpaying vendors
  const getRowClass = (result: BenchmarkResult) => {
    if (result.status === 'OVERPAYING') {
      return 'bg-red-50 hover:bg-red-100 border-b border-red-200';
    }
    return 'border-b border-slate-200 hover:bg-slate-50';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Vendor Contracts</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="px-6 py-3 text-left font-semibold text-slate-700">
                  <button
                    onClick={() => handleSort('vendorName')}
                    className="flex items-center gap-2 hover:text-slate-900 cursor-pointer"
                  >
                    Vendor Name
                    <SortIcon column="vendorName" />
                  </button>
                </th>
                <th className="px-6 py-3 text-left font-semibold text-slate-700">
                  <button
                    onClick={() => handleSort('category')}
                    className="flex items-center gap-2 hover:text-slate-900 cursor-pointer"
                  >
                    Category
                    <SortIcon column="category" />
                  </button>
                </th>
                <th className="px-6 py-3 text-right font-semibold text-slate-700">
                  <button
                    onClick={() => handleSort('currentRate')}
                    className="flex items-center justify-end gap-2 hover:text-slate-900 cursor-pointer w-full"
                  >
                    Current Rate
                    <SortIcon column="currentRate" />
                  </button>
                </th>
                <th className="px-6 py-3 text-right font-semibold text-slate-700">
                  Market Rate
                </th>
                <th className="px-6 py-3 text-center font-semibold text-slate-700">
                  Status
                </th>
                <th className="px-6 py-3 text-left font-semibold text-slate-700">
                  <button
                    onClick={() => handleSort('renewalDate')}
                    className="flex items-center gap-2 hover:text-slate-900 cursor-pointer"
                  >
                    Renewal Date
                    <SortIcon column="renewalDate" />
                  </button>
                </th>
                <th className="px-6 py-3 text-center font-semibold text-slate-700">
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedData.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                    No vendors found
                  </td>
                </tr>
              ) : (
                sortedData.map((result) => (
                  <tr key={result.contractId} className={getRowClass(result)}>
                    <td className="px-6 py-4 font-medium text-slate-900">
                      {result.vendorName}
                    </td>
                    <td className="px-6 py-4 text-slate-700">{result.category}</td>
                    <td className="px-6 py-4 text-right font-mono text-slate-900">
                      {formatCurrencyDetailed(result.currentRate)}/mo
                    </td>
                    <td className="px-6 py-4 text-right font-mono text-slate-700">
                      {formatCurrencyDetailed(result.benchmarkRate)}/mo
                    </td>
                    <td className="px-6 py-4 text-center">
                      <Badge
                        variant={
                          result.status === 'OVERPAYING'
                            ? 'destructive'
                            : result.status === 'GREAT_DEAL'
                            ? 'success'
                            : 'secondary'
                        }
                      >
                        {result.status === 'OVERPAYING'
                          ? `⚠️ Overpaying ${result.variance > 0 ? '+' : ''}${result.variance}%`
                          : result.status === 'GREAT_DEAL'
                          ? `✓ Great Deal`
                          : `Fair`}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-left text-slate-700">
                      {formatRenewalDate(result.renewalDate)}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onSelectVendor?.(result)}
                      >
                        View Details
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function formatCurrencyDetailed(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatRenewalDate(iso: string): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(iso));
}
