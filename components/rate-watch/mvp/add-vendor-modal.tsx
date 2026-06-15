'use client';

import React, { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { X } from 'lucide-react';
import type { Category, Frequency, Vendor } from '@/lib/rate-watch/types';

interface AddVendorModalProps {
  open: boolean;
  onClose: () => void;
  onAdd: (vendor: Vendor) => void;
}

const CATEGORIES: Category[] = ['Cleaning', 'Insurance', 'IT', 'Supplies', 'HVAC'];

function todayPlus(days: number): string {
  return new Date(Date.now() + days * 86400000).toISOString().slice(0, 10);
}

const EMPTY = {
  name: '',
  category: 'Cleaning' as Category,
  currentRate: '',
  frequency: 'MONTHLY' as Frequency,
  renewalDate: todayPlus(90),
};

export function AddVendorModal({ open, onClose, onAdd }: AddVendorModalProps) {
  const [form, setForm] = useState({ ...EMPTY });
  const [error, setError] = useState<string | null>(null);
  if (!open) return null;

  const set = <K extends keyof typeof EMPTY>(key: K, value: (typeof EMPTY)[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const rate = parseFloat(form.currentRate);
    if (!form.name.trim()) return setError('Vendor name is required.');
    if (Number.isNaN(rate) || rate <= 0) return setError('Enter a valid current rate.');

    const [y, m, d] = form.renewalDate.split('-').map(Number);
    onAdd({
      id: `ven_${Date.now()}`,
      name: form.name.trim(),
      category: form.category,
      currentRate: rate,
      frequency: form.frequency,
      renewalDate: new Date(y, m - 1, d, 12, 0, 0),
    });
    setForm({ ...EMPTY });
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 print:hidden">
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-[1px]"
        onClick={onClose}
        aria-hidden
      />
      <div className="absolute right-0 top-0 flex h-full w-full max-w-md flex-col bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Add a vendor</h2>
            <p className="text-xs text-slate-500">
              We&apos;ll benchmark it against the Columbus market instantly.
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

        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4 overflow-y-auto px-6 py-5">
          <div className="space-y-1.5">
            <Label htmlFor="rw-name">Vendor name</Label>
            <Input
              id="rw-name"
              value={form.name}
              onChange={(e) => set('name', e.target.value)}
              placeholder="e.g. Peach State Commercial Cleaning"
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="rw-category">Category</Label>
            <select
              id="rw-category"
              value={form.category}
              onChange={(e) => set('category', e.target.value as Category)}
              className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="rw-rate">Current rate ($)</Label>
              <Input
                id="rw-rate"
                type="number"
                min="0"
                step="0.01"
                value={form.currentRate}
                onChange={(e) => set('currentRate', e.target.value)}
                placeholder="800"
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="rw-frequency">Frequency</Label>
              <select
                id="rw-frequency"
                value={form.frequency}
                onChange={(e) => set('frequency', e.target.value as Frequency)}
                className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950"
              >
                <option value="MONTHLY">Monthly</option>
                <option value="ANNUAL">Annual</option>
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="rw-renewal">Contract renewal date</Label>
            <Input
              id="rw-renewal"
              type="date"
              value={form.renewalDate}
              onChange={(e) => set('renewalDate', e.target.value)}
              required
            />
          </div>

          {error ? (
            <p className="text-sm text-red-600">{error}</p>
          ) : null}

          <div className="mt-auto flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-md border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 rounded-md bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
            >
              Add &amp; benchmark
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
