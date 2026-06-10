'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatCurrencyDetailed } from '@/lib/utils';
import { Copy, X } from 'lucide-react';
import type { BenchmarkResult } from '@/lib/benchmarking-engine';

interface VendorDetailProps {
  result: BenchmarkResult;
  onClose?: () => void;
}

export function VendorDetail({ result, onClose }: VendorDetailProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopyTalkingPoints = () => {
    navigator.clipboard.writeText(result.renegotiationTalkingPoints);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OVERPAYING':
        return 'destructive';
      case 'FAIR':
        return 'secondary';
      case 'GREAT_DEAL':
        return 'success';
      default:
        return 'outline';
    }
  };

  const difference = result.currentRate - result.benchmarkRate;
  const annualSavings = (result.savingsEstimate || 0) * 12;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-4">
          <div className="flex-1">
            <CardTitle>{result.vendorName}</CardTitle>
            <CardDescription>{result.category}</CardDescription>
          </div>
          {onClose && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Status Section */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-slate-600 mb-1">Status</p>
              <Badge variant={getStatusColor(result.status)}>
                {result.status === 'OVERPAYING'
                  ? `⚠️ Overpaying ${result.variance > 0 ? '+' : ''}${result.variance}%`
                  : result.status === 'GREAT_DEAL'
                  ? '✓ Great Deal'
                  : 'Fair'}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-slate-600 mb-1">Variance</p>
              <p className={`text-lg font-semibold ${
                result.variance > 0 ? 'text-red-600' : 'text-green-600'
              }`}>
                {result.variance > 0 ? '+' : ''}{result.variance}%
              </p>
            </div>
          </div>

          {/* Rate Comparison */}
          <div className="border-t border-slate-200 pt-6">
            <h3 className="font-semibold text-slate-900 mb-4">Rate Comparison</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                <p className="text-xs text-slate-600 mb-1">Your Current Rate</p>
                <p className="text-2xl font-bold text-slate-900">
                  {formatCurrencyDetailed(result.currentRate)}
                </p>
                <p className="text-xs text-slate-600 mt-1">/month</p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <p className="text-xs text-green-700 mb-1">Market Benchmark</p>
                <p className="text-2xl font-bold text-green-900">
                  {formatCurrencyDetailed(result.benchmarkRate)}
                </p>
                <p className="text-xs text-green-700 mt-1">/month</p>
              </div>
            </div>

            {result.savingsEstimate !== null && (
              <div className="mt-4 bg-amber-50 p-4 rounded-lg border border-amber-200">
                <p className="text-xs text-amber-700 mb-1">Monthly Difference</p>
                <p className="text-2xl font-bold text-amber-900">
                  {formatCurrencyDetailed(difference)}/month
                </p>
                <p className="text-sm text-amber-700 mt-2">
                  Potential Annual Savings: <span className="font-bold">{formatCurrencyDetailed(annualSavings)}</span>
                </p>
              </div>
            )}
          </div>

          {/* Renegotiation Talking Points */}
          {result.status === 'OVERPAYING' && (
            <div className="border-t border-slate-200 pt-6">
              <h3 className="font-semibold text-slate-900 mb-3">
                Renegotiation Talking Points
              </h3>
              <div className="relative">
                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 min-h-[140px]">
                  <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                    {result.renegotiationTalkingPoints}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCopyTalkingPoints}
                  className="absolute top-2 right-2"
                >
                  <Copy className="h-4 w-4 mr-1" />
                  {copied ? 'Copied!' : 'Copy'}
                </Button>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Use this text as a starting point for your vendor negotiation.
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2 border-t border-slate-200 pt-6">
            {onClose && (
              <Button variant="secondary" onClick={onClose}>
                Close
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
