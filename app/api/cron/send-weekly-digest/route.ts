import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { sendWeeklyDigest } from "@/lib/alerts/emailer";

// Vercel Cron invokes scheduled endpoints with GET, so support both.
export async function GET(request: NextRequest) {
  return POST(request);
}

export async function POST(request: NextRequest) {
  const authHeader = request.headers.get("authorization");
  if (
    authHeader !== `Bearer ${process.env.CRON_SECRET}` &&
    process.env.NODE_ENV === "production"
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    console.log("[CRON] Starting weekly digest job...");

    // Get all users
    const users = await db.user.findMany({
      include: {
        competitors: {
          include: {
            alerts: {
              where: {
                createdAt: {
                  // Last 7 days
                  gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
                },
              },
            },
          },
        },
      },
    });

    console.log(`[CRON] Found ${users.length} users`);

    let sentCount = 0;
    let errorCount = 0;

    for (const user of users) {
      try {
        // Get all alerts from the past week
        const allAlerts = user.competitors
          .flatMap((c) =>
            c.alerts.map((a) => ({
              ...a,
              competitor: c,
            }))
          );

        if (allAlerts.length > 0) {
          await sendWeeklyDigest(user, allAlerts);
          sentCount++;
          console.log(
            `[CRON] Sent weekly digest to ${user.email} with ${allAlerts.length} alerts`
          );
        }
      } catch (error) {
        console.error(
          `[CRON] Failed to send weekly digest to ${user.email}:`,
          error
        );
        errorCount++;
      }
    }

    console.log(
      `[CRON] Weekly digest job completed: ${sentCount} sent, ${errorCount} failed`
    );

    return NextResponse.json({
      success: true,
      sent: sentCount,
      failed: errorCount,
    });
  } catch (error) {
    console.error("[CRON] Fatal error in weekly digest job:", error);
    return NextResponse.json(
      { error: "Weekly digest job failed", details: String(error) },
      { status: 500 }
    );
  }
}
