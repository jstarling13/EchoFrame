import { ShiftLensDashboard } from '@/components/shift-lens/dashboard';

export const metadata = {
  title: 'Shift Lens — EchoFrame Intelligence',
  description:
    'Shift-by-shift P&L and labor tracking. See which shifts are profitable and which are bleeding margin, with plain-English schedule recommendations.',
};

export default function ShiftLensPage() {
  return <ShiftLensDashboard />;
}
