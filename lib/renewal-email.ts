import type { CompanyDashboard } from '@/lib/rate-watch-data';
import type { BenchmarkResult } from '@/lib/benchmarking-engine';

function fmt(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function fmtDate(iso: string | Date): string {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(iso));
}

/**
 * Build a branded HTML renewal-alert email for a company dashboard.
 * Highlights upcoming renewals and the overpaying vendors tied to them.
 */
export function buildRenewalEmail(dashboard: CompanyDashboard): {
  subject: string;
  html: string;
  text: string;
} {
  const { company, renewalAlerts, benchmarkResults, totalSavings } = dashboard;

  const byId = new Map<string, BenchmarkResult>(
    benchmarkResults.map((r) => [r.contractId, r])
  );

  const subject =
    renewalAlerts.length > 0
      ? `Rate Watch: ${renewalAlerts.length} upcoming renewal${renewalAlerts.length !== 1 ? 's' : ''} for ${company.name}`
      : `Rate Watch summary for ${company.name}`;

  const rows = renewalAlerts
    .map((alert) => {
      const r = byId.get(alert.contractId);
      const overpaying = r?.status === 'OVERPAYING';
      const savings = r?.savingsEstimate ? fmt(r.savingsEstimate) : '—';
      const urgencyColor =
        alert.urgency === 'CRITICAL' ? '#dc2626' : alert.urgency === 'HIGH' ? '#ea580c' : '#ca8a04';
      return `
      <tr>
        <td style="padding:12px 16px;border-bottom:1px solid #e2e8f0;font-weight:600;color:#0f172a;">${alert.vendorName}</td>
        <td style="padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#475569;">${fmtDate(alert.renewalDate)}</td>
        <td style="padding:12px 16px;border-bottom:1px solid #e2e8f0;">
          <span style="color:${urgencyColor};font-weight:600;">${alert.daysUntilRenewal} day${alert.daysUntilRenewal !== 1 ? 's' : ''}</span>
        </td>
        <td style="padding:12px 16px;border-bottom:1px solid #e2e8f0;text-align:right;color:${overpaying ? '#dc2626' : '#16a34a'};font-weight:600;">
          ${overpaying ? `Overpaying · save ${savings}/yr` : 'Fairly priced'}
        </td>
      </tr>`;
    })
    .join('');

  const html = `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;">
        <tr>
          <td style="background:#0f172a;padding:24px 32px;">
            <div style="color:#ffffff;font-size:20px;font-weight:700;">EchoFrame Intelligence</div>
            <div style="color:#94a3b8;font-size:13px;margin-top:2px;">Rate Watch · Vendor Renewal Alert</div>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;">
            <p style="margin:0 0 8px;color:#0f172a;font-size:16px;">Hi ${company.contactName ?? 'there'},</p>
            <p style="margin:0 0 20px;color:#475569;font-size:14px;line-height:1.6;">
              Here's the latest Rate Watch summary for <strong>${company.name}</strong>${company.location ? ` in ${company.location}` : ''}.
              ${renewalAlerts.length > 0
                ? `You have <strong>${renewalAlerts.length}</strong> vendor contract${renewalAlerts.length !== 1 ? 's' : ''} renewing within the next 30 days — the best window to renegotiate.`
                : `No contracts are renewing in the next 30 days.`}
            </p>

            <div style="background:#ecfdf5;border:1px solid #bbf7d0;border-radius:8px;padding:16px 20px;margin-bottom:24px;">
              <div style="color:#166534;font-size:13px;font-weight:600;">Total potential annual savings identified</div>
              <div style="color:#15803d;font-size:28px;font-weight:800;margin-top:4px;">${fmt(totalSavings)}</div>
            </div>

            ${renewalAlerts.length > 0 ? `
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
              <tr style="background:#f8fafc;">
                <th align="left" style="padding:10px 16px;font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:.04em;">Vendor</th>
                <th align="left" style="padding:10px 16px;font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:.04em;">Renews</th>
                <th align="left" style="padding:10px 16px;font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:.04em;">In</th>
                <th align="right" style="padding:10px 16px;font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:.04em;">Opportunity</th>
              </tr>
              ${rows}
            </table>` : ''}

            <p style="margin:24px 0 0;color:#475569;font-size:14px;line-height:1.6;">
              Want help renegotiating any of these? Reply to this email and we'll prepare talking points
              backed by current ${company.location} market data.
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#f8fafc;padding:20px 32px;border-top:1px solid #e2e8f0;">
            <div style="color:#94a3b8;font-size:12px;">EchoFrame Intelligence · Financial clarity for Columbus small businesses</div>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;

  const textLines = [
    `EchoFrame Rate Watch — Renewal Alert for ${company.name}`,
    '',
    `Total potential annual savings identified: ${fmt(totalSavings)}`,
    '',
    renewalAlerts.length > 0 ? 'Upcoming renewals (next 30 days):' : 'No contracts renewing in the next 30 days.',
    ...renewalAlerts.map((a) => {
      const r = byId.get(a.contractId);
      const opp = r?.status === 'OVERPAYING' && r.savingsEstimate ? `Overpaying — save ${fmt(r.savingsEstimate)}/yr` : 'Fairly priced';
      return `  • ${a.vendorName} — renews ${fmtDate(a.renewalDate)} (${a.daysUntilRenewal} days) — ${opp}`;
    }),
  ];

  return { subject, html, text: textLines.join('\n') };
}
