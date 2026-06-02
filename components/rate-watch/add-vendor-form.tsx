'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { X } from 'lucide-react';

const CATEGORIES = [
  'Janitorial Services',
  'Commercial Insurance',
  'IT Support',
  'HVAC Maintenance',
  'Office Equipment Lease',
  'Phone & Internet',
  'Software / SaaS',
  'Waste Management',
  'Payroll Services',
  'Security / Alarm Monitoring',
  'Medical Waste Disposal',
  'Uniform / Linen Service',
];

interface AddVendorFormProps {
  onSubmit: (data: {
    vendorName: string;
    category: string;
    currentRate: number;
    frequency: 'MONTHLY' | 'ANNUAL';
    renewalDate: string;
  }) => Promise<void>;
  onClose?: () => void;
  loading?: boolean;
}

export function AddVendorForm({
  onSubmit,
  onClose,
  loading = false,
}: AddVendorFormProps) {
  const [formData, setFormData] = useState({
    vendorName: '',
    category: CATEGORIES[0],
    currentRate: '',
    frequency: 'MONTHLY' as const,
    renewalDate: '',
  });
  const [error, setError] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.vendorName.trim()) {
      setError('Vendor name is required');
      return;
    }

    if (!formData.currentRate || parseFloat(formData.currentRate) <= 0) {
      setError('Current rate must be greater than 0');
      return;
    }

    if (!formData.renewalDate) {
      setError('Renewal date is required');
      return;
    }

    try {
      await onSubmit({
        ...formData,
        currentRate: parseFloat(formData.currentRate),
      });
      setFormData({
        vendorName: '',
        category: CATEGORIES[0],
        currentRate: '',
        frequency: 'MONTHLY',
        renewalDate: '',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add vendor');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="flex flex-row items-start justify-between space-y-0">
          <div className="flex-1">
            <CardTitle>Add New Vendor</CardTitle>
            <CardDescription>Enter vendor contract details</CardDescription>
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

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="vendorName">Vendor Name *</Label>
              <Input
                id="vendorName"
                name="vendorName"
                placeholder="e.g., Superior Cleaning Solutions"
                value={formData.vendorName}
                onChange={handleChange}
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Category *</Label>
              <Select
                id="category"
                name="category"
                value={formData.category}
                onChange={handleChange}
                disabled={loading}
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="currentRate">Contract Amount *</Label>
                <Input
                  id="currentRate"
                  name="currentRate"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={formData.currentRate}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="frequency">Frequency *</Label>
                <Select
                  id="frequency"
                  name="frequency"
                  value={formData.frequency}
                  onChange={handleChange}
                  disabled={loading}
                >
                  <option value="MONTHLY">Monthly</option>
                  <option value="ANNUAL">Annually</option>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="renewalDate">Renewal Date *</Label>
              <Input
                id="renewalDate"
                name="renewalDate"
                type="date"
                value={formData.renewalDate}
                onChange={handleChange}
                disabled={loading}
              />
            </div>

            <div className="flex gap-2 pt-4">
              {onClose && (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={onClose}
                  disabled={loading}
                >
                  Cancel
                </Button>
              )}
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? 'Adding...' : 'Add Vendor'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
