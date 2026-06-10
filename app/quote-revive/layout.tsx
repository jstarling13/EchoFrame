import React from 'react';
import Link from 'next/link';
import { RefreshCw } from 'lucide-react';

export default function QuoteReviveLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40 print:hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <Link href="/quote-revive" className="flex items-center gap-3 group">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-slate-900 text-white">
              <RefreshCw className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900 leading-tight group-hover:text-slate-700">
                Quote Revive
              </h1>
              <p className="text-xs text-slate-500 leading-tight">
                EchoFrame Intelligence
              </p>
            </div>
          </Link>
          <span className="text-xs text-slate-400 hidden sm:block">
            Never let a quote go cold
          </span>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
