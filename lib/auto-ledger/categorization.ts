// ============================================================================
// Auto Ledger — AI Categorization (MVP mock)
// Takes a raw bank-feed string + amount and returns a category plus a
// plain-English note. In production this is a model call; here it's a
// deterministic rules map so the demo is realistic and stable.
// ============================================================================

import type { Categorization } from './types';

interface Rule {
  /** Substrings to look for in the raw description (case-insensitive). */
  match: string[];
  category: string;
  /**
   * Note builder. Receives the absolute dollar amount so the note can read
   * naturally ("$42.10 ...").
   */
  note: (absAmount: number) => string;
}

function money(n: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n);
}

// Order matters: first match wins, so put specific rules before generic ones.
const RULES: Rule[] = [
  {
    match: ['UBER EATS', 'DOORDASH', 'GRUBHUB'],
    category: 'Meals & Entertainment',
    note: (a) => `Team lunch / meal delivery — ${money(a)}. Likely 50% deductible.`,
  },
  {
    match: ['UBER', 'LYFT'],
    category: 'Travel',
    note: (a) => `Rideshare for a client or work trip — ${money(a)}.`,
  },
  {
    match: ['GUSTO', 'ADP', 'PAYCHEX'],
    category: 'Payroll',
    note: (a) => `Payroll run processed through your provider — ${money(a)}.`,
  },
  {
    match: ['AWS', 'AMAZON WEB', 'GOOGLE CLOUD', 'GCP', 'AZURE', 'DIGITALOCEAN'],
    category: 'Software & Hosting',
    note: (a) => `Cloud hosting bill for your apps and infrastructure — ${money(a)}.`,
  },
  {
    match: ['WEBSITE SUBSCRIPTION', 'WEBFLOW', 'SQUARESPACE', 'WIX'],
    category: 'Software & Hosting',
    note: (a) => `Monthly hosting fee for your marketing website — ${money(a)}.`,
  },
  {
    match: ['ADOBE', 'FIGMA', 'CANVA', 'CREATIVE CLOUD'],
    category: 'Software & Subscriptions',
    note: (a) => `Design software subscription used by the team — ${money(a)}.`,
  },
  {
    match: ['GOOGLE WORKSPACE', 'MICROSOFT 365', 'SLACK', 'ZOOM', 'NOTION', 'GSUITE'],
    category: 'Software & Subscriptions',
    note: (a) => `Productivity software your team uses day to day — ${money(a)}.`,
  },
  {
    match: ['AMZN', 'AMAZON', 'STAPLES', 'OFFICE DEPOT'],
    category: 'Office Supplies',
    note: (a) => `Office supplies bought online — ${money(a)}.`,
  },
  {
    match: ['SHELL', 'CHEVRON', 'EXXON', 'BP ', 'GAS'],
    category: 'Auto & Fuel',
    note: (a) => `Fuel for a business vehicle — ${money(a)}. Keep the mileage log.`,
  },
  {
    match: ['DELTA', 'AMERICAN AIR', 'UNITED', 'SOUTHWEST', 'AIRLINE'],
    category: 'Travel',
    note: (a) => `Airfare for a business trip — ${money(a)}.`,
  },
  {
    match: ['MARRIOTT', 'HILTON', 'HYATT', 'HOTEL', 'AIRBNB'],
    category: 'Travel',
    note: (a) => `Lodging for a business trip — ${money(a)}.`,
  },
  {
    match: ['STARBUCKS', 'DUNKIN', 'COFFEE'],
    category: 'Meals & Entertainment',
    note: (a) => `Coffee meeting with a client or prospect — ${money(a)}.`,
  },
  {
    match: ['FACEBOOK', 'META PLAT', 'GOOGLE ADS', 'LINKEDIN', 'MAILCHIMP'],
    category: 'Advertising & Marketing',
    note: (a) => `Ad spend / marketing campaign — ${money(a)}.`,
  },
  {
    match: ['STRIPE', 'SQUARE', 'PAYPAL', 'DEPOSIT', 'PAYMENT FROM', 'ACH CREDIT'],
    category: 'Client Income',
    note: (a) => `Payment received from a client — ${money(a)} deposited.`,
  },
  {
    match: ['IRS', 'EFTPS', 'TAX PYMT', 'DEPT OF REV'],
    category: 'Taxes',
    note: (a) => `Tax payment to a government agency — ${money(a)}.`,
  },
  {
    match: ['RENT', 'WEWORK', 'REGUS', 'LANDLORD'],
    category: 'Rent & Facilities',
    note: (a) => `Office rent / coworking space — ${money(a)}.`,
  },
  {
    match: ['STATE FARM', 'GEICO', 'INSURANCE', 'HISCOX', 'NEXT INSURANCE'],
    category: 'Insurance',
    note: (a) => `Business insurance premium — ${money(a)}.`,
  },
  {
    match: ['TRANSFER', 'XFER', 'ONLINE BANKING'],
    category: 'Transfer',
    note: (a) => `Internal transfer between your accounts — ${money(a)}. Not income or an expense.`,
  },
];

/**
 * AI Categorization mock.
 * @param rawDescription The raw bank-feed string, e.g. "AMZN MKTPLACE PMT".
 * @param amount Signed amount (negative = money out).
 */
export function categorizeTransaction(
  rawDescription: string,
  amount: number
): Categorization {
  const haystack = rawDescription.toUpperCase();
  const abs = Math.abs(amount);

  for (const rule of RULES) {
    if (rule.match.some((needle) => haystack.includes(needle))) {
      return { aiCategory: rule.category, plainEnglishNote: rule.note(abs) };
    }
  }

  // Fallback: classify by direction so nothing is ever left blank.
  if (amount > 0) {
    return {
      aiCategory: 'Income',
      plainEnglishNote: `Money in — ${money(abs)} deposited. We'll confirm the source.`,
    };
  }
  return {
    aiCategory: 'Uncategorized',
    plainEnglishNote: `Expense of ${money(abs)} we couldn't match yet — flagged for a quick human look.`,
  };
}
