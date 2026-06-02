import { CompetitorSnapshot } from "@prisma/client";
import { db } from "../db";

export interface AlertData {
  competitorId: string;
  alertType: string;
  oldValue?: string;
  newValue?: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
  description: string;
}

export async function generateAlertsFromSnapshots(
  competitorId: string,
  newSnapshot: CompetitorSnapshot
): Promise<AlertData[]> {
  const alerts: AlertData[] = [];

  // Get the previous snapshot
  const previousSnapshot = await db.competitorSnapshot.findFirst({
    where: { competitorId },
    orderBy: { scrapedAt: "desc" },
    skip: 1, // Skip the current/new snapshot
  });

  if (!previousSnapshot) {
    // First snapshot, no alerts
    return alerts;
  }

  // Check for price changes
  if (newSnapshot.priceRange && previousSnapshot.priceRange) {
    if (newSnapshot.priceRange !== previousSnapshot.priceRange) {
      alerts.push({
        competitorId,
        alertType: "PRICE_CHANGE",
        oldValue: previousSnapshot.priceRange,
        newValue: newSnapshot.priceRange,
        severity: "HIGH",
        description: `Price changed from ${previousSnapshot.priceRange} to ${newSnapshot.priceRange}`,
      });
    }
  }

  // Check for review count increases
  if (newSnapshot.reviewCount && previousSnapshot.reviewCount) {
    const reviewDiff = newSnapshot.reviewCount - previousSnapshot.reviewCount;
    if (reviewDiff > 0) {
      alerts.push({
        competitorId,
        alertType: "REVIEW_UPDATE",
        oldValue: String(previousSnapshot.reviewCount),
        newValue: String(newSnapshot.reviewCount),
        severity: "MEDIUM",
        description: `${reviewDiff} new review(s) - now at ${newSnapshot.reviewCount} total`,
      });
    }
  }

  // Check for rating changes
  if (newSnapshot.averageRating && previousSnapshot.averageRating) {
    const ratingDiff = newSnapshot.averageRating - previousSnapshot.averageRating;
    if (Math.abs(ratingDiff) >= 0.1) {
      const direction = ratingDiff > 0 ? "improved" : "declined";
      alerts.push({
        competitorId,
        alertType: "RATING_CHANGE",
        oldValue: String(previousSnapshot.averageRating),
        newValue: String(newSnapshot.averageRating),
        severity: ratingDiff < 0 ? "HIGH" : "LOW",
        description: `Rating ${direction} from ${previousSnapshot.averageRating} to ${newSnapshot.averageRating}`,
      });
    }
  }

  // Check for new promotions
  if (newSnapshot.activePromos && previousSnapshot.activePromos) {
    const newPromos = newSnapshot.activePromos
      .split("|")
      .filter((p) => p.trim());
    const oldPromos = previousSnapshot.activePromos
      .split("|")
      .filter((p) => p.trim());

    const addedPromos = newPromos.filter((p) => !oldPromos.includes(p));
    const removedPromos = oldPromos.filter((p) => !newPromos.includes(p));

    if (addedPromos.length > 0) {
      alerts.push({
        competitorId,
        alertType: "PROMO_NEW",
        oldValue: previousSnapshot.activePromos,
        newValue: newSnapshot.activePromos,
        severity: "HIGH",
        description: `New promotion(s): ${addedPromos.join(", ")}`,
      });
    }

    if (removedPromos.length > 0) {
      alerts.push({
        competitorId,
        alertType: "PROMO_ENDED",
        oldValue: previousSnapshot.activePromos,
        newValue: newSnapshot.activePromos,
        severity: "LOW",
        description: `Promotion(s) ended: ${removedPromos.join(", ")}`,
      });
    }
  }

  return alerts;
}

export async function createAlerts(alertData: AlertData[]): Promise<void> {
  for (const alert of alertData) {
    await db.alert.create({
      data: {
        competitorId: alert.competitorId,
        alertType: alert.alertType,
        oldValue: alert.oldValue,
        newValue: alert.newValue,
        severity: alert.severity,
        description: alert.description,
      },
    });
  }
}
