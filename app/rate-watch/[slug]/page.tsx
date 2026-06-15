import { notFound } from 'next/navigation';
import prisma from '@/lib/db';
import { DashboardClient } from '@/components/rate-watch/dashboard-client';

export const dynamic = 'force-dynamic';

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default async function CompanyDashboardPage({ params }: PageProps) {
  const { slug } = await params;

  // Validate the company exists before rendering the client dashboard.
  const exists = await prisma.user.findUnique({ where: { slug }, select: { id: true } });
  if (!exists) notFound();

  return <DashboardClient slug={slug} />;
}
