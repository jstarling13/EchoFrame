import { NextResponse } from 'next/server';
import prisma from '@/lib/db';
import { benchmarkContract, calculateTotalSavings, calculateTotalSpend } from '@/lib/benchmarking-engine';
import { getUpcomingRenewals } from '@/lib/renewal-alerts';

export async function GET() {
  try {
    // For demo: use the first user or create one
    let user = await prisma.user.findFirst();
    if (!user) {
      user = await prisma.user.create({
        data: {
          email: 'demo@echoframe.local',
          name: 'Demo Business',
        },
      });
    }

    // Fetch all contracts for the user
    const contracts = await prisma.vendorContract.findMany({
      where: { userId: user.id },
    });

    // Fetch market benchmarks
    const benchmarks = await prisma.marketBenchmark.findMany();

    // Calculate benchmark results
    const benchmarkResults = contracts.map((contract) => {
      // Find matching benchmark
      const benchmark = benchmarks.find(
        (b) => b.category === contract.category && b.location === 'Columbus, GA'
      );

      if (!benchmark) {
        return null;
      }

      const benchmarkRate =
        contract.frequency === 'MONTHLY'
          ? benchmark.localAvgRateMonthly
          : (benchmark.localAvgRateAnnual || benchmark.localAvgRateMonthly * 12);

      return benchmarkContract(contract, benchmarkRate, contract.frequency);
    }).filter(Boolean);

    // Calculate metrics
    const totalSpend = calculateTotalSpend(contracts);
    const totalSavings = calculateTotalSavings(benchmarkResults as any);
    const upcomingRenewals = getUpcomingRenewals(contracts).length;

    return NextResponse.json({
      benchmarkResults,
      totalSpend,
      totalSavings,
      upcomingRenewals,
    });
  } catch (error) {
    console.error('Dashboard error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch dashboard data' },
      { status: 500 }
    );
  }
}
