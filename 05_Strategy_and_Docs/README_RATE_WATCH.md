# EchoFrame Intelligence: Rate Watch

A B2B SaaS MVP for monitoring vendor contracts and identifying savings opportunities through market benchmarking.

## Features

### 📊 Dashboard Overview
- **Total Vendor Spend**: Aggregate annual spending across all contracts
- **Potential Savings Identified**: Calculate how much could be saved from overpaying vendors
- **Upcoming Renewals**: Track contracts renewing within 30 days

### 🎯 Core Functionality
- **Market Benchmarking**: Compare your vendor rates against Columbus, GA market averages
- **Savings Estimation**: Automatic calculation of potential annual savings for overpaying vendors
- **Renewal Alerts**: Smart alerting system (CRITICAL: ≤7 days, HIGH: ≤14 days, MEDIUM: ≤30 days)
- **Renegotiation Talking Points**: AI-generated negotiation scripts based on market data

### 📋 Vendor Management
- Browse all vendor contracts in a sortable, filterable table
- Color-coded status badges (Overpaying, Fair, Great Deal)
- Add new vendor contracts through an intuitive form
- Detailed vendor view with benchmarking analysis

## Tech Stack

- **Frontend**: Next.js 15 (App Router), React 19, TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **Database**: Prisma ORM with SQLite (dev), easily switchable to PostgreSQL
- **Core Logic**: TypeScript utilities for benchmarking and renewal alerts

## Project Structure

```
.
├── app/
│   ├── api/
│   │   └── rate-watch/          # API routes
│   │       ├── dashboard/       # Dashboard metrics endpoint
│   │       └── contracts/       # Vendor contract CRUD
│   ├── rate-watch/              # Rate Watch feature
│   │   ├── layout.tsx           # Rate Watch layout
│   │   └── page.tsx             # Main dashboard
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Landing page
│   └── globals.css              # Global styles
├── components/
│   ├── rate-watch/              # Feature-specific components
│   │   ├── metric-card.tsx      # KPI cards
│   │   ├── vendor-table.tsx     # Vendor contracts table
│   │   ├── vendor-detail.tsx    # Detailed view modal
│   │   └── add-vendor-form.tsx  # Add vendor form modal
│   └── ui/                      # Base UI components (shadcn-style)
│       ├── button.tsx
│       ├── card.tsx
│       ├── badge.tsx
│       ├── input.tsx
│       ├── label.tsx
│       └── select.tsx
├── lib/
│   ├── benchmarking-engine.ts   # Core benchmarking logic
│   ├── renewal-alerts.ts        # Renewal alert logic
│   ├── db.ts                    # Prisma client
│   └── utils.ts                 # Utility functions
├── prisma/
│   ├── schema.prisma            # Database schema
│   ├── seed.ts                  # Database seeding script
│   └── dev.db                   # SQLite database (generated)
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── next.config.js
└── .env.local                   # Environment variables
```

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Set Up Database

```bash
# Generate Prisma client
npm run prisma:generate

# Run migrations
npm run prisma:migrate

# Seed database with demo data
npx prisma db seed
```

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. View Prisma Studio (optional)

```bash
npm run prisma:studio
```

## Database Schema

### Users
- `id`: Unique identifier
- `email`: User email
- `name`: User name
- `createdAt`, `updatedAt`: Timestamps

### VendorContract
- `id`: Unique identifier
- `userId`: Reference to User
- `vendorName`: Vendor company name
- `category`: Service category (e.g., "Janitorial Services")
- `currentRate`: Current contract rate
- `frequency`: "MONTHLY" or "ANNUAL"
- `renewalDate`: When the contract renews
- `notes`: Optional notes
- `createdAt`, `updatedAt`: Timestamps

### MarketBenchmark
- `id`: Unique identifier
- `category`: Service category
- `companySizeBracket`: "SMALL" (1-10), "MEDIUM" (11-50), "LARGE" (50+)
- `location`: Geographic location (e.g., "Columbus, GA")
- `localAvgRateMonthly`: Average monthly rate for the category
- `localAvgRateAnnual`: Average annual rate (optional)
- `createdAt`, `updatedAt`: Timestamps

## Demo Data

The seeding script creates:
- 1 demo user
- 6 market benchmarks for Columbus, GA (Small business bracket)
- 6 realistic vendor contracts with a mix of overpaying and fair rates

### Sample Vendors
1. **Superior Cleaning Solutions** - Janitorial ($650/mo vs $450 benchmark) - OVERPAYING
2. **Guardian Business Insurance** - Insurance ($350/mo vs $350 benchmark) - FAIR
3. **TechPro IT Solutions** - IT Support ($950/mo vs $800 benchmark) - OVERPAYING
4. **Elite HVAC Services** - HVAC ($300/mo vs $300 benchmark) - FAIR
5. **Global Office Leasing** - Equipment Lease ($250/mo vs $200 benchmark) - OVERPAYING
6. **ConnectTech Communications** - Phone & Internet ($200/mo vs $150 benchmark) - OVERPAYING

## Core Logic

### Benchmarking Engine (`lib/benchmarking-engine.ts`)

**`benchmarkContract()`**
- Compares vendor rate against market benchmark
- Calculates variance percentage
- Flags as OVERPAYING if variance > 5%
- Generates negotiation talking points for overpaying vendors
- Estimates annual savings

**`calculateTotalSavings()`**
- Aggregates potential savings across all overpaying vendors

**`calculateTotalSpend()`**
- Calculates annual spending across all contracts

### Renewal Alerts (`lib/renewal-alerts.ts`)

**`getUpcomingRenewals()`**
- Returns contracts renewing within 30 days
- Assigns urgency levels:
  - CRITICAL: ≤7 days
  - HIGH: ≤14 days
  - MEDIUM: 15-30 days

**`countUpcomingRenewals()`**
- Quick count for dashboard metrics

## API Endpoints

### GET `/api/rate-watch/dashboard`
Returns dashboard metrics:
```json
{
  "benchmarkResults": [...],
  "totalSpend": 123456.78,
  "totalSavings": 45678.90,
  "upcomingRenewals": 3
}
```

### GET `/api/rate-watch/contracts`
Returns all vendor contracts for the user.

### POST `/api/rate-watch/contracts`
Creates a new vendor contract.

**Request Body:**
```json
{
  "vendorName": "Example Vendor",
  "category": "Janitorial Services",
  "currentRate": 500,
  "frequency": "MONTHLY",
  "renewalDate": "2026-12-31"
}
```

## Component Hierarchy

```
RateWatchPage
├── MetricCard (3x)
│   ├── Total Vendor Spend
│   ├── Potential Savings
│   └── Upcoming Renewals
├── AlertBanners
│   ├── Overpaying vendors alert
│   └── Upcoming renewals alert
├── VendorTable
│   └── Sortable table with status badges
├── VendorDetail (modal)
│   ├── Rate comparison view
│   ├── Savings estimate
│   └── Renegotiation talking points
└── AddVendorForm (modal)
    └── Form inputs
```

## Styling

Uses Tailwind CSS with a professional slate/gray color scheme:
- **Primary**: Slate 900 (dark gray)
- **Backgrounds**: Slate 50 (light gray)
- **Accent Colors**:
  - Red: Overpaying status
  - Amber: Fair status / Upcoming renewals
  - Green: Great deal / Savings

## Customization

### Add New Vendor Categories
1. Update the `CATEGORIES` array in `components/rate-watch/add-vendor-form.tsx`
2. Add corresponding market benchmarks via Prisma Studio or seed script

### Adjust Benchmark Thresholds
- Edit `benchmarking-engine.ts` to change the 5% overpaying threshold
- Modify renewal alert thresholds in `renewal-alerts.ts`

### Change Database Provider
1. Update `prisma/schema.prisma` datasource
2. Update `.env.local` DATABASE_URL

```prisma
datasource db {
  provider = "postgresql"  // or "mysql", "sqlserver"
  url      = env("DATABASE_URL")
}
```

## Performance Considerations

- Dashboard data is fetched client-side on page load
- Consider adding SWR or React Query for better caching
- For large datasets (1000+ vendors), implement pagination in VendorTable
- Consider indexing on category and userId in production

## Future Enhancements

- [ ] User authentication (Clerk, Auth0)
- [ ] Multi-user/multi-tenant support
- [ ] Export reports (PDF, CSV)
- [ ] Historical tracking of rates
- [ ] Automated email alerts for upcoming renewals
- [ ] Integration with vendor management platforms
- [ ] AI-powered negotiation suggestions
- [ ] Contract document uploads
- [ ] Audit trail for savings achieved

## Troubleshooting

### Database Issues
```bash
# Reset database (CAUTION: deletes all data)
npx prisma migrate reset

# Re-seed
npx prisma db seed
```

### Prisma Client Issues
```bash
# Regenerate Prisma client
npm run prisma:generate
```

### Port Already in Use
```bash
# Change port in dev script
npm run dev -- -p 3001
```

## Support

For issues or questions, refer to:
- [Next.js Documentation](https://nextjs.org/docs)
- [Prisma Documentation](https://www.prisma.io/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
