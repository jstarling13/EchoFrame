import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatCurrencyDetailed(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date);
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'OVERPAYING':
      return 'bg-red-50 text-red-900 border-red-200';
    case 'FAIR':
      return 'bg-amber-50 text-amber-900 border-amber-200';
    case 'GREAT_DEAL':
      return 'bg-green-50 text-green-900 border-green-200';
    default:
      return 'bg-slate-50 text-slate-900 border-slate-200';
  }
}

export function getStatusBadgeColor(status: string): string {
  switch (status) {
    case 'OVERPAYING':
      return 'bg-red-100 text-red-800';
    case 'FAIR':
      return 'bg-amber-100 text-amber-800';
    case 'GREAT_DEAL':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-slate-100 text-slate-800';
  }
}

export function getUrgencyColor(urgency: string): string {
  switch (urgency) {
    case 'CRITICAL':
      return 'bg-red-100 text-red-800';
    case 'HIGH':
      return 'bg-orange-100 text-orange-800';
    case 'MEDIUM':
      return 'bg-yellow-100 text-yellow-800';
    default:
      return 'bg-slate-100 text-slate-800';
  }
}
