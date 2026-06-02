import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { sendDailyAlert } from "@/lib/alerts/emailer";

export async function POST(request: NextRequest) {
  const authHeader = request.headers.get("authorization");
  if (
    authHeader !== `Bearer ${process.env.CRON_SECRET}` &&
    process.env.NODE_ENV === "production"
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    console.log("[CRON] Starting alert distribution job...");

    // Get all users with unsent alerts from today
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const usersWithAlerts = await db.user.findMany({
      where: {
        competitors: {
          some: {
            alerts: {
              some: {
                sentAt: null,
                createdAt: {
                  gte: today,
                },
              },
            },
          },
        },
      },
      include: {
        competitors: {
          include: {
            alerts: {
              where: {
                sentAt: null,
                createdAt: {
                  gte: today,
                },
              },
            },
          },
        },
      },
    });

    console.log(`[CRON] Found ${usersWithAlerts.length} users with alerts`);

    let sentCount = 0;
    let errorCount = 0;

    for (const user of usersWithAlerts) {
      try {
        // Flatten all unsent alerts for this user
        const allAlerts = user.competitors
          .flatMap((c) =>
            c.alerts.map((a) => ({
              ...a,
              competitor: c,
            }))
          )
          .filter((a) => a.sentAt === null);

        if (allAlerts.length > 0) {
          await sendDailyAlert(user, allAlerts);
          sentCount++;
          console.log(
            `[CRON] Sent alert email to ${user.email} with ${allAlerts.length} alerts`
          );
        }
      } catch (error) {
        console.error(`[CRON] Failed to send alerts to ${user.email}:`, error);
        errorCount++;
      }
    }

    console.log(
      `[CRON] Alert distribution completed: ${sentCount} sent, ${errorCount} failed`
    );

    return NextResponse.json({
      success: true,
      sent: sentCount,
      failed: errorCount,
    });
  } catch (error) {
    console.error("[CRON] Fatal error in alert distribution:", error);
    return NextResponse.json(
      { error: "Alert distribution failed", details: String(error) },
      { status: 500 }
    );
  }
}
