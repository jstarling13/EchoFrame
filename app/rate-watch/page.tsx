import { RateWatchDashboard } from '@/components/rate-watch/mvp/dashboard';

export const metadata = {
  title: 'Rate Watch — EchoFrame Intelligence',
  description:
    'Benchmark every vendor against the local Columbus, GA market, spot overpayments, and renegotiate with AI-drafted emails.',
};

export default function RateWatchPage() {
  return <RateWatchDashboard />;
}
