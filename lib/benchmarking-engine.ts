import { VendorContract } from '@prisma/client';

export interface BenchmarkResult {
  contractId: string;
  vendorName: string;
  category: string;
  currentRate: number;
  benchmarkRate: number;
  frequency: 'MONTHLY' | 'ANNUAL';
  renewalDate: string; // ISO string for serialization across API boundary
  variance: number; // percentage
  status: 'OVERPAYING' | 'FAIR' | 'GREAT_DEAL';
  savingsEstimate: number | null;
  renegotiationTalkingPoints: string;
}

/**
 * Benchmarks a vendor contract against market data
 * Returns variance percentage and savings estimate if overpaying (> 5%)
 */
export function benchmarkContract(
  contract: VendorContract,
  benchmarkRate: number,
  frequency: 'MONTHLY' | 'ANNUAL'
): BenchmarkResult {
  const variance = ((contract.currentRate - benchmarkRate) / benchmarkRate) * 100;

  let status: 'OVERPAYING' | 'FAIR' | 'GREAT_DEAL';
  let savingsEstimate: number | null = null;

  if (variance > 5) {
    status = 'OVERPAYING';
    const monthlyDifference = contract.currentRate - benchmarkRate;
    savingsEstimate = frequency === 'MONTHLY'
      ? monthlyDifference * 12
      : monthlyDifference;
  } else if (variance < -5) {
    status = 'GREAT_DEAL';
  } else {
    status = 'FAIR';
  }

  const renegotiationTalkingPoints = generateTalkingPoints(
    contract.vendorName,
    benchmarkRate,
    contract.currentRate,
    contract.renewalDate,
    frequency
  );

  return {
    contractId: contract.id,
    vendorName: contract.vendorName,
    category: contract.category,
    currentRate: contract.currentRate,
    benchmarkRate,
    frequency,
    renewalDate: contract.renewalDate.toISOString(),
    variance: Math.round(variance * 100) / 100,
    status,
    savingsEstimate: savingsEstimate ? Math.round(savingsEstimate * 100) / 100 : null,
    renegotiationTalkingPoints,
  };
}

/**
 * Generates dynamic talking points for renegotiation
 */
function generateTalkingPoints(
  vendorName: string,
  benchmarkRate: number,
  currentRate: number,
  renewalDate: Date,
  frequency: 'MONTHLY' | 'ANNUAL'
): string {
  const formatter = new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const renewalDateStr = formatter.format(renewalDate);
  const difference = currentRate - benchmarkRate;
  const percentDiff = ((difference / benchmarkRate) * 100).toFixed(1);
  const frequencyLabel = frequency === 'MONTHLY' ? 'per month' : 'per year';

  return `Market data indicates similar businesses in the Columbus, GA area are paying approximately $${benchmarkRate.toFixed(2)} ${frequencyLabel} for this service. We are currently paying $${currentRate.toFixed(2)} ${frequencyLabel}, which is ${percentDiff}% above market rate. I'd like to discuss adjusting our rate to align with current local market conditions before we renew on ${renewalDateStr}. This adjustment could result in significant savings for our organization while maintaining quality service.`;
}

/**
 * Calculate total potential savings across multiple contracts
 */
export function calculateTotalSavings(results: BenchmarkResult[]): number {
  return results.reduce((total, result) => total + (result.savingsEstimate || 0), 0);
}

/**
 * Calculate total vendor spend
 */
export function calculateTotalSpend(contracts: VendorContract[]): number {
  return contracts.reduce((total, contract) => {
    const annualSpend = contract.frequency === 'MONTHLY'
      ? contract.currentRate * 12
      : contract.currentRate;
    return total + annualSpend;
  }, 0);
}
