'use client';

import React, { useState } from 'react';
import { cn, formatCurrency } from '@/lib/utils';
import { Check, Copy, Lock, Send, X } from 'lucide-react';
import { hasFeatureAccess } from '@/lib/rate-watch/tier-engine';
import type { Tier, VendorRow } from '@/lib/rate-watch/types';

interface NegotiationPanelProps {
  row: VendorRow | null;
  tier: Tier;
  onClose: () => void;
  onUpgrade: (reason: string) => void;
}

export function NegotiationPanel({
  row,
  tier,
  onClose,
  onUpgrade,
}: NegotiationPanelProps) {
  const [copied, setCopied] = useState(false);
  if (!row) return null;

  const canSend = hasFeatureAccess(tier, 'DIRECT_SEND');
  const { vendor, benchmark, draft, annualPremium } = row;
  const overpaying = benchmark.status === 'OVERPAYING';

  const handleCopy = () => {
    navigator.clipboard?.writeText(`Subject: ${draft.subjectLine}\n\n${draft.bodyText}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSend = () => {
    if (!canSend) {
      onUpgrade(
        'One-click direct send is a Pro feature. Upgrade to email vendors straight from Rate Watch — no copy-paste.'
      );
      return;
    }
    alert('Sent to the vendor. (Demo — wires to email in production.)');
  };

  return (
    <div className="fixed inset-0 z-50 print:hidden">
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-[1px]"
        onClick={onClose}
        aria-hidden
      />
      <div className="absolute right-0 top-0 flex h-full w-full max-w-xl flex-col bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">{vendor.name}</h2>
            <p className="text-xs text-slate-500">
              {vendor.category} · renews in {row.daysUntilRenewal} days
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-6 py-5">
          {/* Gap breakdown */}
          <div
            className={cn(
              'rounded-xl border p-5',
              overpaying
                ? 'border-red-200 bg-red-50'
                : 'border-green-200 bg-green-50'
            )}
          >
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              The gap
            </p>
            {overpaying ? (
              <p className="mt-1 text-2xl font-bold tracking-tight text-red-700">
                You&apos;re paying {formatCurrency(annualPremium)}/yr above the
                Columbus average for this service.
              </p>
            ) : (
              <p className="mt-1 text-2xl font-bold tracking-tight text-green-700">
                You&apos;re at or below the Columbus market rate — you&apos;re in
                good shape here.
              </p>
            )}
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="rounded-lg border border-slate-200 bg-white p-3">
                <p className="text-xs text-slate-500">Your rate</p>
                <p className="text-lg font-bold text-slate-900">
                  {formatCurrency(vendor.currentRate)}
                  <span className="text-xs font-medium text-slate-400">
                    {vendor.frequency === 'MONTHLY' ? '/mo' : '/yr'}
                  </span>
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-3">
                <p className="text-xs text-slate-500">Columbus market</p>
                <p className="text-lg font-bold text-slate-900">
                  {formatCurrency(benchmark.localMarketRate)}
                  <span className="text-xs font-medium text-slate-400">
                    {vendor.frequency === 'MONTHLY' ? '/mo' : '/yr'}
                  </span>
                </p>
              </div>
            </div>
          </div>

          {/* AI-drafted email */}
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
              AI-drafted negotiation email
            </p>
            <div className="rounded-xl border border-slate-200">
              <div className="border-b border-slate-100 px-4 py-3">
                <p className="text-xs text-slate-400">Subject</p>
                <p className="text-sm font-medium text-slate-900">
                  {draft.subjectLine}
                </p>
              </div>
              <div className="px-4 py-3">
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                  {draft.bodyText}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Tiered actions */}
        <div className="flex items-center gap-3 border-t border-slate-200 px-6 py-4">
          <button
            onClick={handleCopy}
            className="inline-flex flex-1 items-center justify-center gap-2 rounded-md bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-slate-800"
          >
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? 'Copied!' : 'Copy to clipboard'}
          </button>

          <button
            onClick={handleSend}
            aria-disabled={!canSend}
            className={cn(
              'inline-flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-semibold transition-colors',
              canSend
                ? 'bg-amber-600 text-white hover:bg-amber-700'
                : 'cursor-pointer border border-slate-200 bg-slate-50 text-slate-400 hover:bg-slate-100'
            )}
          >
            {canSend ? <Send className="h-4 w-4" /> : <Lock className="h-4 w-4" />}
            Send directly to vendor
            {!canSend ? (
              <span className="ml-1 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-amber-700">
                Pro
              </span>
            ) : null}
          </button>
        </div>
      </div>
    </div>
  );
}
