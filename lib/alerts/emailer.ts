import { Resend } from "resend";
import { Alert, Competitor, User } from "@prisma/client";
import { db } from "../db";

// Lazily construct the Resend client. Instantiating at module load throws when
// RESEND_API_KEY is unset, which breaks `next build` (route page-data collection)
// and any deploy where the key isn't present yet.
function getResend(): Resend {
  return new Resend(process.env.RESEND_API_KEY);
}

// Sender + links are env-driven. RESEND_FROM_EMAIL must be on a domain you've
// verified in Resend (use "onboarding@resend.dev" for local/test sends).
const FROM_EMAIL =
  process.env.RESEND_FROM_EMAIL ?? "Rival Scan <onboarding@resend.dev>";
const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

export async function sendDailyAlert(
  user: User,
  alerts: (Alert & { competitor: Competitor })[]
): Promise<void> {
  if (!user.email || alerts.length === 0) {
    return;
  }

  const alertsByCompetitor = alerts.reduce(
    (acc, alert) => {
      const competitorId = alert.competitor.id;
      if (!acc[competitorId]) {
        acc[competitorId] = {
          competitor: alert.competitor,
          alerts: [],
        };
      }
      acc[competitorId].alerts.push(alert);
      return acc;
    },
    {} as Record<
      string,
      {
        competitor: Competitor;
        alerts: Alert[];
      }
    >
  );

  const emailContent = generateDailyAlertEmail(user, alertsByCompetitor);

  try {
    await getResend().emails.send({
      from: FROM_EMAIL,
      to: user.email,
      subject: `🔔 Rival Scan Daily Alert - ${alerts.length} change(s) detected`,
      html: emailContent,
    });

    // Mark alerts as sent
    for (const alert of alerts) {
      await db.alert.update({
        where: { id: alert.id },
        data: { sentAt: new Date() },
      });
    }
  } catch (error) {
    console.error("Failed to send alert email:", error);
    throw error;
  }
}

export async function sendWeeklyDigest(
  user: User,
  weeklyAlerts: (Alert & { competitor: Competitor })[]
): Promise<void> {
  if (!user.email || weeklyAlerts.length === 0) {
    return;
  }

  const emailContent = generateWeeklyDigestEmail(user, weeklyAlerts);

  try {
    await getResend().emails.send({
      from: FROM_EMAIL,
      to: user.email,
      subject: "📊 Rival Scan Weekly Digest - Competitive Intelligence Report",
      html: emailContent,
    });
  } catch (error) {
    console.error("Failed to send weekly digest:", error);
    throw error;
  }
}

function generateDailyAlertEmail(
  user: User,
  alertsByCompetitor: Record<
    string,
    {
      competitor: Competitor;
      alerts: Alert[];
    }
  >
): string {
  let html = `
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }
    .competitor-section { border: 1px solid #ddd; margin: 15px 0; border-radius: 8px; overflow: hidden; }
    .competitor-name { background: #f5f5f5; padding: 12px; font-weight: bold; }
    .alert-item { padding: 12px; border-bottom: 1px solid #eee; }
    .alert-item:last-child { border-bottom: none; }
    .alert-high { border-left: 4px solid #e74c3c; }
    .alert-medium { border-left: 4px solid #f39c12; }
    .alert-low { border-left: 4px solid #27ae60; }
    .footer { text-align: center; margin-top: 30px; color: #999; font-size: 12px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🔔 Daily Alert Summary</h1>
      <p>Hi ${user.name || user.email}, here are today's competitor updates.</p>
    </div>
`;

  for (const competitorId in alertsByCompetitor) {
    const { competitor, alerts } = alertsByCompetitor[competitorId];
    html += `
    <div class="competitor-section">
      <div class="competitor-name">
        <a href="${competitor.website}" style="color: #667eea; text-decoration: none;">
          ${competitor.name}
        </a>
      </div>
`;

    for (const alert of alerts) {
      const severityClass = `alert-${alert.severity.toLowerCase()}`;
      html += `
      <div class="alert-item ${severityClass}">
        <strong>${alert.alertType.replace(/_/g, " ")}</strong><br>
        <p style="margin: 5px 0 0 0; color: #666;">${alert.description}</p>
        ${alert.oldValue ? `<small>Old: ${alert.oldValue} → New: ${alert.newValue}</small>` : ""}
      </div>
`;
    }

    html += `</div>`;
  }

  html += `
    <div class="footer">
      <p>Rival Scan • Competitive Intelligence Tool</p>
      <p><a href="${APP_URL}/dashboard" style="color: #667eea;">View Dashboard</a></p>
    </div>
  </div>
</body>
</html>
`;

  return html;
}

function generateWeeklyDigestEmail(
  user: User,
  alerts: (Alert & { competitor: Competitor })[]
): string {
  const competitors = Array.from(new Set(alerts.map((a) => a.competitor.id)));
  const priceChanges = alerts.filter((a) => a.alertType === "PRICE_CHANGE").length;
  const newReviews = alerts.filter((a) => a.alertType === "REVIEW_UPDATE").length;
  const newPromos = alerts.filter((a) => a.alertType === "PROMO_NEW").length;

  return `
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }
    .stats { display: flex; justify-content: space-around; margin: 20px 0; }
    .stat { text-align: center; }
    .stat-number { font-size: 32px; font-weight: bold; color: #667eea; }
    .stat-label { color: #666; font-size: 12px; }
    .footer { text-align: center; margin-top: 30px; color: #999; font-size: 12px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📊 Weekly Digest</h1>
      <p>Your competitive intelligence summary for this week</p>
    </div>

    <div class="stats">
      <div class="stat">
        <div class="stat-number">${competitors.length}</div>
        <div class="stat-label">Competitors Tracked</div>
      </div>
      <div class="stat">
        <div class="stat-number">${priceChanges}</div>
        <div class="stat-label">Price Changes</div>
      </div>
      <div class="stat">
        <div class="stat-number">${newReviews}</div>
        <div class="stat-label">New Reviews</div>
      </div>
      <div class="stat">
        <div class="stat-number">${newPromos}</div>
        <div class="stat-label">New Promos</div>
      </div>
    </div>

    <div class="footer">
      <p>Rival Scan • Competitive Intelligence Tool</p>
      <p><a href="${APP_URL}/dashboard" style="color: #667eea;">View Full Report</a></p>
    </div>
  </div>
</body>
</html>
`;
}
