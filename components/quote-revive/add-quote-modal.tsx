'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { X } from 'lucide-react';
import type { Quote } from '@/lib/quote-revive/types';

interface AddQuoteModalProps {
  open: boolean;
  onClose: () => void;
  onAdd: (quote: Quote) => void;
}

function todayInputValue(): string {
  return new Date().toISOString().slice(0, 10);
}

const EMPTY = {
  customerName: '',
  customerEmail: '',
  jobDescription: '',
  quoteAmount: '',
  dateSent: todayInputValue(),
};

export function AddQuoteModal({ open, onClose, onAdd }: AddQuoteModalProps) {
  const [form, setForm] = useState({ ...EMPTY });
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const set = (key: keyof typeof EMPTY, value: string) =>
    setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const amount = parseFloat(form.quoteAmount);
    if (!form.customerName.trim()) return setError('Customer name is required.');
    if (!form.jobDescription.trim()) return setError('Job description is required.');
    if (Number.isNaN(amount) || amount <= 0)
      return setError('Enter a valid quote amount.');

    // dateSent comes in as YYYY-MM-DD (local midnight) — anchor to noon to avoid
    // timezone drift pushing the date a day backward.
    const dateSent = new Date(`${form.dateSent}T12:00:00`);

    onAdd({
      id: `q-${Date.now()}`,
      userId: 'demo-user',
      customerName: form.customerName.trim(),
      customerEmail: form.customerEmail.trim(),
      jobDescription: form.jobDescription.trim(),
      quoteAmount: amount,
      status: 'PENDING',
      dateSent,
      lastContactDate: dateSent,
    });

    setForm({ ...EMPTY, dateSent: todayInputValue() });
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 print:hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-[1px]"
        onClick={onClose}
        aria-hidden
      />
      {/* Slide-out panel */}
      <div className="absolute right-0 top-0 flex h-full w-full max-w-md flex-col bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Add a Quote</h2>
            <p className="text-xs text-slate-500">
              Manual entry — CRM sync comes later
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

        <form
          onSubmit={handleSubmit}
          className="flex flex-1 flex-col gap-4 overflow-y-auto px-6 py-5"
        >
          <div className="space-y-1.5">
            <Label htmlFor="customerName">Customer Name</Label>
            <Input
              id="customerName"
              value={form.customerName}
              onChange={(e) => set('customerName', e.target.value)}
              placeholder="Marcus Bell"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="customerEmail">Email</Label>
            <Input
              id="customerEmail"
              type="email"
              value={form.customerEmail}
              onChange={(e) => set('customerEmail', e.target.value)}
              placeholder="marcus@greenscapeatl.com"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="jobDescription">Job Description</Label>
            <textarea
              id="jobDescription"
              value={form.jobDescription}
              onChange={(e) => set('jobDescription', e.target.value)}
              placeholder="Full-season lawn care for a 2-acre commercial lot"
              rows={3}
              className="flex w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="quoteAmount">Quote Amount</Label>
              <Input
                id="quoteAmount"
                type="number"
                min="0"
                step="0.01"
                value={form.quoteAmount}
                onChange={(e) => set('quoteAmount', e.target.value)}
                placeholder="2400"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="dateSent">Date Sent</Label>
              <Input
                id="dateSent"
                type="date"
                value={form.dateSent}
                max={todayInputValue()}
                onChange={(e) => set('dateSent', e.target.value)}
              />
            </div>
          </div>

          {error ? (
            <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          ) : null}

          <div className="mt-auto flex items-center justify-end gap-2 border-t border-slate-200 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit">Add Quote &amp; Start Sequence</Button>
          </div>
        </form>
      </div>
    </div>
  );
}
