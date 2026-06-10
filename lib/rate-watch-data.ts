import prisma from '@/lib/db';
import {
  benchmarkContract,
  calculateTotalSavings,
  calculateTotalSpend,
  type BenchmarkResult,
} from '@/lib/benchmarking-engine';
import { getUpcomingRenewals, type RenewalAlert } from '@/lib/renewal-alerts';

export interface CompanySummary {
  id: string;
  slug: string;
  name: string;
  industry: string | null;
  companySizeBracket: string;
  location: string;
  contactName: string | null;
  vendorCount: number;
}

export interface CompanyDashboard {
  company: CompanySummary;
  benchmarkResults: BenchmarkResult[];
  renewalAlerts: RenewalAlert[];
  totalSpend: number;
  totalSavings: number;
  upcomingRenewals: number;
  overpayingCount: number;
}

/**
 * List all sample companies (tenants) with a vendor count.
 */
export async function getCompanies(): Promise<CompanySummary[]> {
  const users = await prisma.user.findMany({
    orderBy: { name: 'asc' },
    include: { _count: { select: { contracts: true } } },
  });

  return users.map((u) => ({
    id: u.id,
    slug: u.slug ?? '', // slug is now optional (NextAuth users have none); samples always set it
    name: u.name ?? 'Untitled Company',
    industry: u.industry,
    companySizeBracket: u.companySizeBracket,
    location: u.location,
    contactName: u.contactName,
    vendorCount: u._count.contracts,
  }));
}

/**
 * Compute the full benchmarked dashboard for a single company by slug.
 * Matches each contract to a market benchmark by category, the company's
 * size bracket, and location. Returns null if the company doesn't exist.
 */
export async function getCompanyDashboard(
  slug: string
): Promise<CompanyDashboard | null> {
  const user = await prisma.user.findUnique({
    where: { slug },
    include: { contracts: true },
  });

  if (!user) return null;

  const benchmarks = await prisma.marketBenchmark.findMany({
    where: { companySizeBracket: user.companySizeBracket, location: user.location },
  });

  const benchmarkResults: BenchmarkResult[] = user.contracts
    .map((contract) => {
      const benchmark = benchmarks.find((b) => b.category === contract.category);
      if (!benchmark) return null;

      const benchmarkRate =
        contract.frequency === 'MONTHLY'
          ? benchmark.localAvgRateMonthly
          : benchmark.localAvgRateAnnual ?? benchmark.localAvgRateMonthly * 12;

      return benchmarkContract(
        contract,
        benchmarkRate,
        contract.frequency as 'MONTHLY' | 'ANNUAL'
      );
    })
    .filter((r): r is BenchmarkResult => r !== null);

  const renewalAlerts = getUpcomingRenewals(user.contracts);

  return {
    company: {
      id: user.id,
      slug: user.slug ?? '',
      name: user.name ?? 'Untitled Company',
      industry: user.industry,
      companySizeBracket: user.companySizeBracket,
      location: user.location,
      contactName: user.contactName,
      vendorCount: user.contracts.length,
    },
    benchmarkResults,
    renewalAlerts,
    totalSpend: calculateTotalSpend(user.contracts),
    totalSavings: calculateTotalSavings(benchmarkResults),
    upcomingRenewals: renewalAlerts.length,
    overpayingCount: benchmarkResults.filter((r) => r.status === 'OVERPAYING').length,
  };
}
