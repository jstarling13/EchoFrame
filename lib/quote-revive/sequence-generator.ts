// Sequence Generator
// ------------------
// Builds the 3-touch follow-up sequence for a quote: Day 3, Day 7, Day 14 from
// date_sent. Each step gets a context-aware draft message that adapts to the
// quote amount and job description, plus a status derived from the calendar
// (anything whose scheduled date is in the past is treated as already SENT).
//
// Pure functions so they can run server-side (cron/seed) or client-side (UI).

import {
  SEQUENCE_DAY_OFFSETS,
  type FollowUpSequenceStep,
  type Quote,
  type SequenceStepStatus,
} from './types';
import { daysBetween } from './staleness-engine';

const MS_PER_DAY = 1000 * 60 * 60 * 24;

function addDays(date: Date, days: number): Date {
  return new Date(date.getTime() + days * MS_PER_DAY);
}

function firstName(customerName: string): string {
  return customerName.trim().split(/\s+/)[0] || customerName;
}

function money(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/** Lowercase, trimmed job description for inlining mid-sentence. */
function job(jobDescription: string): string {
  const d = jobDescription.trim();
  return d.charAt(0).toLowerCase() + d.slice(1);
}

/**
 * Draft a context-aware message for a given step.
 * Tone scales with deal size: larger quotes lean consultative (offer a call),
 * smaller quotes stay light and frictionless.
 */
export function draftMessage(quote: Quote, sequenceStep: number): string {
  const name = firstName(quote.customerName);
  const amount = money(quote.quoteAmount);
  const work = job(quote.jobDescription);
  const isHighValue = quote.quoteAmount >= 5000;

  switch (sequenceStep) {
    case 1:
      return (
        `Hi ${name}, just making sure my quote for the ${work} landed in your inbox ` +
        `(${amount}). Happy to answer any questions — is this still something you're ` +
        `looking to move forward on?`
      );
    case 2:
      return isHighValue
        ? `Hi ${name}, following up on the ${work} proposal (${amount}). On jobs this ` +
            `size most folks have a question or two on scope or scheduling — want to grab ` +
            `15 minutes this week so I can walk you through it?`
        : `Hi ${name}, checking back on the ${work} quote (${amount}). I can usually get ` +
            `something on the calendar within a week or two — want me to pencil you in?`;
    case 3:
      return isHighValue
        ? `Hi ${name}, I don't want to crowd your inbox, so this is my last note on the ` +
            `${work} (${amount}). If the timing or budget needs adjusting I'm glad to rework ` +
            `the scope — just let me know what would make this an easy yes.`
        : `Hi ${name}, last check-in on the ${work} (${amount})! If now isn't the right ` +
            `time, no worries at all — just reply and I'll follow up down the road. ` +
            `Otherwise I'd love to get you booked.`;
    default:
      return `Hi ${name}, following up on your ${work} quote (${amount}).`;
  }
}

/**
 * Generate the full 3-step sequence for a quote.
 * A step is SENT if its scheduled date is on/before `now`, otherwise PENDING.
 */
export function generateSequence(
  quote: Quote,
  now: Date = new Date()
): FollowUpSequenceStep[] {
  return SEQUENCE_DAY_OFFSETS.map((dayOffset, index) => {
    const sequenceStep = index + 1;
    const scheduledSendDate = addDays(quote.dateSent, dayOffset);

    let status: SequenceStepStatus = 'PENDING';
    if (quote.status === 'WON' || quote.status === 'LOST' || quote.status === 'COLD') {
      // Closed or cold quotes: past steps sent, future steps effectively halted.
      status = scheduledSendDate.getTime() <= now.getTime() ? 'SENT' : 'PAUSED';
    } else {
      status = scheduledSendDate.getTime() <= now.getTime() ? 'SENT' : 'PENDING';
    }

    return {
      id: `${quote.id}-step-${sequenceStep}`,
      quoteId: quote.id,
      sequenceStep,
      dayOffset,
      messageTemplate: draftMessage(quote, sequenceStep),
      scheduledSendDate,
      status,
    };
  });
}

/** The next step that still needs to send, or null if the sequence is done. */
export function getNextStep(
  sequence: FollowUpSequenceStep[]
): FollowUpSequenceStep | null {
  return (
    sequence
      .filter((s) => s.status === 'PENDING')
      .sort((a, b) => a.scheduledSendDate.getTime() - b.scheduledSendDate.getTime())[0] ?? null
  );
}

/** Whole days until a step fires (negative = overdue). */
export function daysUntil(date: Date, now: Date = new Date()): number {
  return daysBetween(now, date);
}
