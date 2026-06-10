// Seed script for Auto Ledger.
// Run with:  npx tsx prisma/seed-auto-ledger.ts
// (or)       npx ts-node --compiler-options '{"module":"CommonJS"}' prisma/seed-auto-ledger.ts
//
// Idempotent: it upserts a demo tenant (on the Starter tier so the upgrade
// gating is visible) and replaces that tenant's accounts, transactions, and
// monthly report each run. Categories, plain-English notes, and reconciliation
// statuses come from the same engine functions the dashboard uses.

import { PrismaClient } from '@prisma/client';
import { buildTransactions, MOCK_ACCOUNTS } from '../lib/auto-ledger/mock-data';

const prisma = new PrismaClient();

async function main() {
  const now = new Date();

  // 1. Demo tenant on the Starter tier.
  const user = await prisma.user.upsert({
    where: { email: 'demo@autoledger.test' },
    update: {
      subscriptionTier: 'STARTER',
      subscriptionStatus: 'ACTIVE',
    },
    create: {
      email: 'demo@autoledger.test',
      name: 'Maya Chen',
      slug: 'auto-ledger-demo',
      contactName: 'Maya Chen',
      location: 'Columbus, GA',
      subscriptionTier: 'STARTER',
      subscriptionStatus: 'ACTIVE',
    },
  });

  // 2. Clear previous demo data (transactions cascade from accounts).
  await prisma.connectedAccount.deleteMany({ where: { userId: user.id } });
  await prisma.monthlyReport.deleteMany({ where: { userId: user.id } });

  // 3. Recreate connected accounts.
  const accountIdMap: Record<string, string> = {};
  for (const acc of MOCK_ACCOUNTS) {
    const created = await prisma.connectedAccount.create({
      data: {
        userId: user.id,
        institutionName: acc.institutionName,
        accountType: acc.accountType,
        mask: acc.mask,
        lastSyncDate: acc.lastSyncDate,
        syncStatus: acc.syncStatus,
      },
    });
    accountIdMap[acc.id] = created.id;
  }

  // 4. Recreate transactions (run through categorization + reconciliation).
  const transactions = buildTransactions();
  for (const txn of transactions) {
    await prisma.transaction.create({
      data: {
        accountId: accountIdMap[txn.accountId],
        date: txn.date,
        amount: txn.amount,
        rawDescription: txn.rawDescription,
        aiCategory: txn.aiCategory,
        plainEnglishNote: txn.plainEnglishNote,
        status: txn.status,
      },
    });
  }

  // 5. Monthly report. Tax estimate is stored but gated to Growth/Pro in the UI.
  await prisma.monthlyReport.create({
    data: {
      userId: user.id,
      month: now.getMonth() + 1,
      year: now.getFullYear(),
      summaryText:
        "You brought in $6,800 from client work this month against $4,356 in spend, leaving roughly $2,444 in your pocket. Software and subscriptions are creeping up — six recurring tools now run about $443/month combined.",
      actionItem:
        'Review the $1,500 Venmo contractor payment — paying contractors outside of payroll can create 1099 headaches at tax time.',
      taxEstimateAmount: 3120,
    },
  });

  const txnCount = await prisma.transaction.count({
    where: { account: { userId: user.id } },
  });
  console.log(
    `Seeded ${MOCK_ACCOUNTS.length} accounts and ${txnCount} transactions for ${user.email}.`
  );
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
