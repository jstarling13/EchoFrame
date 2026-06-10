// Shared types for EchoFrame Intelligence: Quote Revive.
// These mirror the Prisma models (see prisma/schema.prisma) but are framework
// -agnostic so the staleness engine, sequence generator, mock data, and React
// components can all share one contract without importing the Prisma client.

export type QuoteStatus =
  | 'PENDING' // Fresh — sent recently, no follow-up needed yet
  | 'FOLLOW_UP_ACTIVE' // Inside the automated follow-up sequence
  | 'COLD' // Gone quiet for 30+ days — needs reactivation
  | 'WON' // Closed/won (optionally via a revive)
  | 'LOST'; // Closed/lost

export type SequenceStepStatus = 'PENDING' | 'SENT' | 'PAUSED';

/** The three Day offsets the MVP sequences on. */
export const SEQUENCE_DAY_OFFSETS = [3, 7, 14] as const;
export type SequenceDayOffset = (typeof SEQUENCE_DAY_OFFSETS)[number];

export interface FollowUpSequenceStep {
  id: string;
  quoteId: string;
  /** 1, 2, or 3 */
  sequenceStep: number;
  /** Day offset from date_sent that this step targets (3, 7, 14). */
  dayOffset: number;
  messageTemplate: string;
  scheduledSendDate: Date;
  status: SequenceStepStatus;
}

export interface Quote {
  id: string;
  userId: string;
  customerName: string;
  customerEmail: string;
  jobDescription: string;
  quoteAmount: number;
  status: QuoteStatus;
  dateSent: Date;
  lastContactDate: Date;
  /** True when this quote was closed/won after entering the revive sequence. */
  wonViaRevive?: boolean;
}

/**
 * A Quote enriched with everything the dashboard needs to render:
 * the staleness-evaluated status, its generated sequence, and the next message.
 */
export interface QuoteWithSequence extends Quote {
  sequence: FollowUpSequenceStep[];
  /** Next step that still needs to send (null if none pending). */
  nextStep: FollowUpSequenceStep | null;
  /** Whole-day count until nextStep fires. Negative = overdue. Null = none. */
  daysUntilNext: number | null;
  /** Which board column this quote belongs in. */
  column: QuoteColumn;
}

export type QuoteColumn = 'FRESH' | 'IN_SEQUENCE' | 'COLD' | 'CLOSED';
