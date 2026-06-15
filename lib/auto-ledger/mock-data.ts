// ============================================================================
// Auto Ledger — Mock data for the MVP dashboard
// A realistic month for a solo creative agency. Raw transactions are run
// through the SAME engine functions the production app would use, so the demo
// exercises the real categorization + reconciliation logic.
// ============================================================================

import { categorizeTransaction } from './categorization';
import { reconcileTransaction } from './reconciliation';
import type {
  ConnectedAccount,
  DashboardData,
  LedgerMetrics,
  LedgerUser,
  MonthlyReport,
  Tier,
  Transaction,
} from './types';

// Anchor the demo month to the current calendar month so the dashboard always
// reads as "this month". `day` is the day-of-month for each transaction.
const NOW = new Date();
const YEAR = NOW.getFullYear();
const MONTH = NOW.getMonth(); // 0-indexed

function d(day: number): Date {
  return new Date(YEAR, MONTH, day, 12, 0, 0);
}

function hoursAgo(h: number): Date {
  return new Date(NOW.getTime() - h * 60 * 60 * 1000);
}

const ACCOUNT_CHASE = 'acct_chase_checking';
const ACCOUNT_AMEX = 'acct_amex_credit';

export const MOCK_ACCOUNTS: ConnectedAccount[] = [
  {
    id: ACCOUNT_CHASE,
    institutionName: 'Chase',
    accountType: 'CHECKING',
    mask: '4021',
    lastSyncDate: hoursAgo(2),
    syncStatus: 'HEALTHY',
  },
  {
    id: ACCOUNT_AMEX,
    institutionName: 'American Express',
    accountType: 'CREDIT_CARD',
    mask: '1007',
    lastSyncDate: hoursAgo(5),
    syncStatus: 'HEALTHY',
  },
];

/** Raw feed rows — exactly what a bank/card sync would hand us. */
interface RawRow {
  id: string;
  accountId: string;
  day: number;
  amount: number; // negative = money out
  rawDescription: string;
}

const RAW_ROWS: RawRow[] = [
  {
    id: 'txn_01',
    accountId: ACCOUNT_CHASE,
    day: 22,
    amount: 6800.0,
    rawDescription: 'STRIPE TRANSFER PAYOUT ST-X3K9',
  },
  {
    id: 'txn_02',
    accountId: ACCOUNT_CHASE,
    day: 21,
    amount: -1950.0,
    rawDescription: 'GUSTO PAY 9F2C CONTRACTOR',
  },
  {
    id: 'txn_03',
    accountId: ACCOUNT_AMEX,
    day: 20,
    amount: -39.0,
    rawDescription: 'FS *WEBSITE SUBSCRIPTION',
  },
  {
    id: 'txn_04',
    accountId: ACCOUNT_AMEX,
    day: 18,
    amount: -212.45,
    rawDescription: 'AWS EMEA AMAZON WEB SVC',
  },
  {
    id: 'txn_05',
    accountId: ACCOUNT_AMEX,
    day: 16,
    amount: -54.2,
    rawDescription: 'UBER EATS 8842',
  },
  {
    id: 'txn_06',
    accountId: ACCOUNT_AMEX,
    day: 14,
    amount: -72.0,
    rawDescription: 'GOOGLE WORKSPACE GSUITE',
  },
  {
    id: 'txn_07',
    accountId: ACCOUNT_AMEX,
    day: 11,
    amount: -59.99,
    rawDescription: 'ADOBE CREATIVE CLOUD',
  },
  {
    id: 'txn_08',
    accountId: ACCOUNT_AMEX,
    day: 9,
    amount: -128.36,
    rawDescription: 'AMZN MKTPLACE PMT',
  },
  {
    id: 'txn_09',
    accountId: ACCOUNT_CHASE,
    day: 6,
    amount: -1500.0,
    rawDescription: 'VENMO PAYMENT TO CONTRACTOR',
  },
  {
    id: 'txn_10',
    accountId: ACCOUNT_AMEX,
    day: 3,
    amount: -340.0,
    rawDescription: 'META PLATFORMS ADS',
  },
];

/** Build the enriched transaction list by running rows through the engines. */
export function buildTransactions(): Transaction[] {
  return RAW_ROWS.map((row) => {
    const { aiCategory, plainEnglishNote } = categorizeTransaction(
      row.rawDescription,
      row.amount
    );
    const { status } = reconcileTransaction(row);
    return {
      id: row.id,
      accountId: row.accountId,
      date: d(row.day),
      amount: row.amount,
      rawDescription: row.rawDescription,
      aiCategory,
      plainEnglishNote,
      status,
    };
  });
}

/**
 * Compute the dashboard metrics from a transaction list. "MTD" = the calendar
 * month of the most recent transaction (the demo's current period).
 */
export function computeMetrics(transactions: Transaction[]): LedgerMetrics {
  if (transactions.length === 0) {
    return {
      netCashflowMtd: 0,
      moneyInMtd: 0,
      moneyOutMtd: 0,
      unreviewedCount: 0,
      flaggedCount: 0,
      reconciledCount: 0,
    };
  }

  const newest = transactions.reduce((a, b) => (a.date > b.date ? a : b)).date;
  const inPeriod = transactions.filter(
    (t) =>
      t.date.getFullYear() === newest.getFullYear() &&
      t.date.getMonth() === newest.getMonth()
  );

  const moneyIn = inPeriod
    .filter((t) => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0);
  const moneyOut = inPeriod
    .filter((t) => t.amount < 0)
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);
  const flagged = transactions.filter((t) => t.status === 'FLAGGED').length;

  return {
    netCashflowMtd: moneyIn - moneyOut,
    moneyInMtd: moneyIn,
    moneyOutMtd: moneyOut,
    unreviewedCount: flagged,
    flaggedCount: flagged,
    reconciledCount: transactions.length - flagged,
  };
}

function buildUser(tier: Tier): LedgerUser {
  return {
    id: 'user_demo',
    name: 'Maya Chen',
    email: 'maya@northlightstudio.co',
    businessName: 'Northlight Studio',
    subscriptionTier: tier,
    subscriptionStatus: 'ACTIVE',
  };
}

function buildReport(): MonthlyReport {
  return {
    month: MONTH + 1,
    year: YEAR,
    summaryText:
      "You brought in $6,800 from client work this month against $4,356 in spend, leaving roughly $2,444 in your pocket. Software and subscriptions are creeping up — six recurring tools now run about $443/month combined. Your biggest single outflow was a $1,950 contractor payroll run.",
    actionItem:
      'Review the $1,500 Venmo contractor payment — paying contractors outside of payroll can create 1099 headaches at tax time. Move recurring contractor pay into Gusto so it is tracked and reported automatically.',
    // Populated here, but gated to Growth/Pro in the UI.
    taxEstimateAmount: 3120,
  };
}

/**
 * One payload with everything the dashboard needs. Default tier is STARTER so
 * the UI demonstrates the upgrade gating out of the box.
 */
export function getDashboardData(tier: Tier = 'STARTER'): DashboardData {
  const transactions = buildTransactions();
  return {
    user: buildUser(tier),
    accounts: MOCK_ACCOUNTS,
    transactions,
    report: buildReport(),
    metrics: computeMetrics(transactions),
  };
}
