import { VendorContract } from '@prisma/client';

export interface RenewalAlert {
  contractId: string;
  vendorName: string;
  renewalDate: Date;
  daysUntilRenewal: number;
  urgency: 'CRITICAL' | 'HIGH' | 'MEDIUM';
}

/**
 * Scans vendor contracts and returns those renewing within 30 days
 * Urgency increases as the renewal date approaches
 */
export function getUpcomingRenewals(
  contracts: VendorContract[],
  fromDate: Date = new Date(),
  daysThreshold: number = 30
): RenewalAlert[] {
  const alerts: RenewalAlert[] = [];
  const thresholdDate = new Date(fromDate.getTime() + daysThreshold * 24 * 60 * 60 * 1000);

  for (const contract of contracts) {
    if (contract.renewalDate <= thresholdDate && contract.renewalDate >= fromDate) {
      const daysUntilRenewal = Math.ceil(
        (contract.renewalDate.getTime() - fromDate.getTime()) / (24 * 60 * 60 * 1000)
      );

      let urgency: 'CRITICAL' | 'HIGH' | 'MEDIUM';
      if (daysUntilRenewal <= 7) {
        urgency = 'CRITICAL';
      } else if (daysUntilRenewal <= 14) {
        urgency = 'HIGH';
      } else {
        urgency = 'MEDIUM';
      }

      alerts.push({
        contractId: contract.id,
        vendorName: contract.vendorName,
        renewalDate: contract.renewalDate,
        daysUntilRenewal,
        urgency,
      });
    }
  }

  // Sort by days until renewal (ascending)
  return alerts.sort((a, b) => a.daysUntilRenewal - b.daysUntilRenewal);
}

/**
 * Count how many contracts are renewing within the threshold
 */
export function countUpcomingRenewals(
  contracts: VendorContract[],
  daysThreshold: number = 30
): number {
  return getUpcomingRenewals(contracts, new Date(), daysThreshold).length;
}
