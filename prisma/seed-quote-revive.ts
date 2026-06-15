// Seed script for Quote Revive.
// Run with:  npx tsx prisma/seed-quote-revive.ts
// (or)       npx ts-node --compiler-options '{"module":"CommonJS"}' prisma/seed-quote-revive.ts
//
// Idempotent: it upserts a demo user and replaces that user's quotes each run.
// Statuses + sequences are produced by the same engine the UI uses, so the
// seeded data matches what you see in the dashboard.

import { PrismaClient } from '@prisma/client';
import { buildMockQuotes } from '../lib/quote-revive/mock-data';
import { generateSequence } from '../lib/quote-revive/sequence-generator';
import { evaluateStaleness } from '../lib/quote-revive/staleness-engine';

const prisma = new PrismaClient();

async function main() {
  const now = new Date();

  // 1. Demo tenant.
  const user = await prisma.user.upsert({
    where: { email: 'demo@quoterevive.test' },
    update: {},
    create: {
      email: 'demo@quoterevive.test',
      name: 'Quote Revive Demo',
      slug: 'quote-revive-demo',
      contactName: 'Demo Owner',
      location: 'Columbus, GA',
    },
  });

  // 2. Clear any previous demo quotes (cascades to sequences).
  await prisma.quote.deleteMany({ where: { userId: user.id } });

  // 3. Recreate quotes + their generated sequences.
  const mockQuotes = buildMockQuotes(now);

  for (const mock of mockQuotes) {
    const status = evaluateStaleness(mock, now).status;
    const resolved = { ...mock, status };
    const sequence = generateSequence(resolved, now);

    await prisma.quote.create({
      data: {
        userId: user.id,
        customerName: resolved.customerName,
        customerEmail: resolved.customerEmail,
        jobDescription: resolved.jobDescription,
        quoteAmount: resolved.quoteAmount,
        status: resolved.status,
        dateSent: resolved.dateSent,
        lastContactDate: resolved.lastContactDate,
        wonViaRevive: resolved.wonViaRevive ?? false,
        sequence: {
          create: sequence.map((step) => ({
            sequenceStep: step.sequenceStep,
            dayOffset: step.dayOffset,
            messageTemplate: step.messageTemplate,
            scheduledSendDate: step.scheduledSendDate,
            status: step.status === 'PAUSED' ? 'PENDING' : step.status,
          })),
        },
      },
    });
  }

  const count = await prisma.quote.count({ where: { userId: user.id } });
  console.log(`Seeded ${count} quotes for ${user.email}.`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
