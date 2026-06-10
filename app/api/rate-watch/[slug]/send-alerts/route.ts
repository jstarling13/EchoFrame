import { NextResponse, NextRequest } from 'next/server';
import { getCompanyDashboard } from '@/lib/rate-watch-data';
import { buildRenewalEmail } from '@/lib/renewal-email';

interface RouteContext {
  params: Promise<{ slug: string }>;
}

/**
 * GET → return a rendered preview of the renewal-alert email (HTML + subject).
 * Useful for showing clients what they'd receive without sending anything.
 */
export async function GET(_request: NextRequest, context: RouteContext) {
  const { slug } = await context.params;
  const dashboard = await getCompanyDashboard(slug);
  if (!dashboard) {
    return NextResponse.json({ error: 'Company not found' }, { status: 404 });
  }
  const { subject, html } = buildRenewalEmail(dashboard);
  // Return raw HTML so it can be opened directly in a browser tab.
  return new NextResponse(html, {
    status: 200,
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'X-Email-Subject': subject },
  });
}

/**
 * POST → actually send the renewal-alert email via Resend.
 * Falls back to a dry-run (returns the rendered email) when RESEND_API_KEY
 * is not configured, so the flow is demonstrable without credentials.
 */
export async function POST(request: NextRequest, context: RouteContext) {
  try {
    const { slug } = await context.params;
    const dashboard = await getCompanyDashboard(slug);
    if (!dashboard) {
      return NextResponse.json({ error: 'Company not found' }, { status: 404 });
    }

    const { subject, html, text } = buildRenewalEmail(dashboard);

    // Allow overriding the recipient in the request body (demo-friendly).
    let to = dashboard.company.contactName ? undefined : undefined;
    try {
      const body = await request.json().catch(() => ({}));
      to = body?.to ?? to;
    } catch {
      /* no body */
    }
    const recipient = to ?? process.env.RATE_WATCH_DEMO_RECIPIENT ?? 'demo@echoframe.local';

    const apiKey = process.env.RESEND_API_KEY;
    if (!apiKey) {
      return NextResponse.json({
        sent: false,
        dryRun: true,
        reason: 'RESEND_API_KEY not configured — returning rendered email instead of sending.',
        subject,
        to: recipient,
        previewUrl: `/api/rate-watch/${slug}/send-alerts`,
      });
    }

    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: process.env.RATE_WATCH_FROM_EMAIL ?? 'Rate Watch <onboarding@resend.dev>',
        to: [recipient],
        subject,
        html,
        text,
      }),
    });

    if (!res.ok) {
      const detail = await res.text();
      return NextResponse.json(
        { sent: false, error: 'Resend API error', detail },
        { status: 502 }
      );
    }

    const data = await res.json();
    return NextResponse.json({ sent: true, id: data?.id, to: recipient, subject });
  } catch (error) {
    console.error('send-alerts error:', error);
    return NextResponse.json({ error: 'Failed to send alerts' }, { status: 500 });
  }
}
