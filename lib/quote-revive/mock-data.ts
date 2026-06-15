// Mock data for Quote Revive.
// -----------------------------
// Dates are expressed relative to "now" so the dashboard always shows a healthy
// mix of fresh / in-sequence / cold quotes whenever you open it. The raw quotes
// are intentionally left with their *entered* status; the staleness engine
// re-derives the live status in `getDashboardData()`.

import { columnForStatus, evaluateStaleness } from './staleness-engine';
import { generateSequence, getNextStep, daysUntil } from './sequence-generator';
import type { Quote, QuoteWithSequence } from './types';

const MS_PER_DAY = 1000 * 60 * 60 * 24;

/** Date N days before `now`. */
function daysAgo(n: number, now: Date = new Date()): Date {
  return new Date(now.getTime() - n * MS_PER_DAY);
}

const MOCK_USER_ID = 'demo-user';

/**
 * Build the raw mock quote set relative to a reference time.
 * Mix: 2 fresh, 3 in follow-up, 2 cold, 1 won-via-revive.
 */
export function buildMockQuotes(now: Date = new Date()): Quote[] {
  return [
    // --- Fresh (sent <= 3 days ago) ---
    {
      id: 'q-greenscape',
      userId: MOCK_USER_ID,
      customerName: 'Marcus Bell',
      customerEmail: 'marcus@greenscapeatl.com',
      jobDescription: 'Full-season lawn care & landscaping for a 2-acre commercial lot',
      quoteAmount: 2400,
      status: 'PENDING',
      dateSent: daysAgo(1, now),
      lastContactDate: daysAgo(1, now),
    },
    {
      id: 'q-coolcomfort',
      userId: MOCK_USER_ID,
      customerName: 'Dana Whitfield',
      customerEmail: 'dana.whitfield@gmail.com',
      jobDescription: 'HVAC repair — replace compressor & recharge refrigerant',
      quoteAmount: 850,
      status: 'PENDING',
      dateSent: daysAgo(2, now),
      lastContactDate: daysAgo(2, now),
    },

    // --- In follow-up sequence (4-14 days, still open) ---
    {
      id: 'q-sparklepro',
      userId: MOCK_USER_ID,
      customerName: 'Priya Nair',
      customerEmail: 'priya@sparkleprocleaning.com',
      jobDescription: 'Recurring commercial cleaning for a 12,000 sq ft office',
      quoteAmount: 1200,
      status: 'FOLLOW_UP_ACTIVE',
      dateSent: daysAgo(5, now),
      lastContactDate: daysAgo(2, now), // day-3 message went out
    },
    {
      id: 'q-northstar',
      userId: MOCK_USER_ID,
      customerName: 'Tony Alvarez',
      customerEmail: 'tony@northstarlogistics.com',
      jobDescription: 'IT setup — 18-workstation network, firewall & server install',
      quoteAmount: 6800,
      status: 'FOLLOW_UP_ACTIVE',
      dateSent: daysAgo(8, now),
      lastContactDate: daysAgo(1, now), // day-7 message went out
    },
    {
      id: 'q-patriot',
      userId: MOCK_USER_ID,
      customerName: 'Karen Doyle',
      customerEmail: 'kdoyle@patriotpropertygroup.com',
      jobDescription: 'Commercial roof replacement — 6,500 sq ft TPO membrane',
      quoteAmount: 14500,
      status: 'FOLLOW_UP_ACTIVE',
      dateSent: daysAgo(12, now),
      lastContactDate: daysAgo(5, now),
    },

    // --- Cold (no response 30+ days) ---
    {
      id: 'q-riverside',
      userId: MOCK_USER_ID,
      customerName: 'Greg Holloway',
      customerEmail: 'greg@riversidebrewing.com',
      jobDescription: 'Electrical panel upgrade & sub-panel for a taproom expansion',
      quoteAmount: 3200,
      status: 'FOLLOW_UP_ACTIVE', // engine will downgrade to COLD
      dateSent: daysAgo(34, now),
      lastContactDate: daysAgo(34, now),
    },
    {
      id: 'q-magnolia',
      userId: MOCK_USER_ID,
      customerName: 'Sandra Pope',
      customerEmail: 'sandra.pope@magnoliainn.com',
      jobDescription: 'Interior repaint of a 14-room boutique inn',
      quoteAmount: 4750,
      status: 'FOLLOW_UP_ACTIVE', // engine will downgrade to COLD
      dateSent: daysAgo(41, now),
      lastContactDate: daysAgo(41, now),
    },

    // --- Won via revive (drives the "Jobs Won via Revive" metric) ---
    {
      id: 'q-heritage',
      userId: MOCK_USER_ID,
      customerName: 'Will Carter',
      customerEmail: 'will@heritagefenceco.com',
      jobDescription: 'Install 320 ft of cedar privacy fencing with two gates',
      quoteAmount: 5600,
      status: 'WON',
      dateSent: daysAgo(16, now),
      lastContactDate: daysAgo(2, now),
      wonViaRevive: true,
    },
  ];
}

/** Enrich a single quote with engine-derived status, sequence, and next step. */
export function enrichQuote(quote: Quote, now: Date = new Date()): QuoteWithSequence {
  const { status } = evaluateStaleness(quote, now);
  const resolved: Quote = { ...quote, status };
  const sequence = generateSequence(resolved, now);
  const nextStep = getNextStep(sequence);
  return {
    ...resolved,
    sequence,
    nextStep,
    daysUntilNext: nextStep ? daysUntil(nextStep.scheduledSendDate, now) : null,
    column: columnForStatus(status),
  };
}

export interface DashboardMetrics {
  totalOpenValue: number;
  followUpsSentThisWeek: number;
  jobsWonViaRevive: number;
}

export interface DashboardData {
  quotes: QuoteWithSequence[];
  metrics: DashboardMetrics;
}

/**
 * Headline metrics derived from a set of enriched quotes. Exported so the
 * client can recompute after the user adds a quote or sends/pauses a message.
 */
export function computeMetrics(
  quotes: QuoteWithSequence[],
  now: Date = new Date()
): DashboardMetrics {
  const open = quotes.filter((q) => q.status !== 'WON' && q.status !== 'LOST');
  const totalOpenValue = open.reduce((sum, q) => sum + q.quoteAmount, 0);

  const weekAgo = new Date(now.getTime() - 7 * MS_PER_DAY);
  const followUpsSentThisWeek = quotes.reduce((count, q) => {
    return (
      count +
      q.sequence.filter(
        (s) =>
          s.status === 'SENT' &&
          s.scheduledSendDate.getTime() >= weekAgo.getTime() &&
          s.scheduledSendDate.getTime() <= now.getTime()
      ).length
    );
  }, 0);

  const jobsWonViaRevive = quotes.filter(
    (q) => q.status === 'WON' && q.wonViaRevive
  ).length;

  return { totalOpenValue, followUpsSentThisWeek, jobsWonViaRevive };
}

/**
 * The single entry point the UI calls. Returns enriched quotes + headline
 * metrics, all computed live from the staleness engine and sequence generator.
 */
export function getDashboardData(now: Date = new Date()): DashboardData {
  const quotes = buildMockQuotes(now).map((q) => enrichQuote(q, now));
  return { quotes, metrics: computeMetrics(quotes, now) };
}
