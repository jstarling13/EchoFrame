'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  className?: string;
}

export function MetricCard({
  title,
  value,
  description,
  icon,
  variant = 'default',
  className,
}: MetricCardProps) {
  const bgClasses = {
    default: 'border-slate-200 bg-white',
    success: 'border-green-200 bg-green-50',
    warning: 'border-yellow-200 bg-yellow-50',
    danger: 'border-red-200 bg-red-50',
  };

  const iconColorClasses = {
    default: 'text-slate-500',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    danger: 'text-red-600',
  };

  const titleColorClasses = {
    default: 'text-slate-600',
    success: 'text-green-900',
    warning: 'text-yellow-900',
    danger: 'text-red-900',
  };

  const valueColorClasses = {
    default: 'text-slate-900',
    success: 'text-green-900',
    warning: 'text-yellow-900',
    danger: 'text-red-900',
  };

  return (
    <Card className={cn(bgClasses[variant], className)}>
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <CardTitle className={cn('text-sm font-medium', titleColorClasses[variant])}>
          {title}
        </CardTitle>
        {icon && (
          <div className={cn('h-4 w-4', iconColorClasses[variant])}>
            {icon}
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className={cn('text-2xl font-bold', valueColorClasses[variant])}>
          {value}
        </div>
        {description && (
          <p className={cn('text-xs', titleColorClasses[variant])}>
            {description}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
