import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { scrapeWebsite, scrapeGoogleBusiness } from "@/lib/scraping/firecrawl";
import { parseScrapedContent } from "@/lib/scraping/parser";
import { generateAlertsFromSnapshots, createAlerts } from "@/lib/alerts/differ";

// Verify request is from Vercel Cron
export async function POST(request: NextRequest) {
  const authHeader = request.headers.get("authorization");
  if (
    authHeader !== `Bearer ${process.env.CRON_SECRET}` &&
    process.env.NODE_ENV === "production"
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    console.log("[CRON] Starting competitor scraping job...");

    // Get all active competitors
    const competitors = await db.competitor.findMany({
      where: { status: "ACTIVE" },
      include: { user: true },
    });

    console.log(`[CRON] Found ${competitors.length} active competitors`);

    let successCount = 0;
    let errorCount = 0;

    for (const competitor of competitors) {
      try {
        console.log(`[CRON] Scraping ${competitor.name}...`);

        // Scrape website
        let scrapedContent = "";
        try {
          scrapedContent = await scrapeWebsite(competitor.website);
        } catch (error) {
          console.warn(
            `[CRON] Failed to scrape ${competitor.website}:`,
            error
          );
        }

        // Parse content
        const parsedData = parseScrapedContent(scrapedContent);

        // Scrape Google Business data
        let googleData = { reviewCount: null, rating: null };
        if (competitor.googleBusinessUrl) {
          try {
            googleData = await scrapeGoogleBusiness(
              competitor.googleBusinessUrl
            );
          } catch (error) {
            console.warn(
              `[CRON] Failed to scrape Google Business for ${competitor.name}:`,
              error
            );
          }
        }

        // Create snapshot
        const snapshot = await db.competitorSnapshot.create({
          data: {
            competitorId: competitor.id,
            priceRange: parsedData.priceRange,
            reviewCount: googleData.reviewCount,
            averageRating: googleData.rating,
            activePromos: parsedData.activePromos?.join("|"),
            scrapedData: JSON.stringify({
              website: {
                priceRange: parsedData.priceRange,
                promos: parsedData.activePromos,
              },
              googleBusiness: googleData,
            }),
          },
        });

        // Generate alerts from this snapshot
        const alerts = await generateAlertsFromSnapshots(
          competitor.id,
          snapshot
        );

        if (alerts.length > 0) {
          await createAlerts(alerts);
          console.log(
            `[CRON] Created ${alerts.length} alert(s) for ${competitor.name}`
          );
        }

        successCount++;
      } catch (error) {
        console.error(
          `[CRON] Error processing ${competitor.name}:`,
          error
        );
        errorCount++;
      }
    }

    console.log(
      `[CRON] Scraping job completed: ${successCount} succeeded, ${errorCount} failed`
    );

    return NextResponse.json({
      success: true,
      processed: successCount,
      failed: errorCount,
    });
  } catch (error) {
    console.error("[CRON] Fatal error in scraping job:", error);
    return NextResponse.json(
      { error: "Scraping job failed", details: String(error) },
      { status: 500 }
    );
  }
}
