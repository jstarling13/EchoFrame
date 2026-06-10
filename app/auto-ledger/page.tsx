import { DashboardClient } from '@/components/auto-ledger/dashboard-client';

export const metadata = {
  title: 'Auto Ledger — EchoFrame Intelligence',
  description:
    'Automated, plain-English bookkeeping for small businesses. Clean books on autopilot, with one specific action every month.',
};

export default function AutoLedgerPage() {
  return <DashboardClient />;
}
