# Rival Scan MVP - Setup Guide

## Overview
Rival Scan is a competitive intelligence tool that monitors your competitors' pricing, reviews, and promotions. The system runs daily checks and sends alerts via email.

## Project Structure
```
.
├── app/
│   ├── api/
│   │   ├── auth/[...nextauth]/          # NextAuth.js handlers
│   │   ├── rivals/                       # Competitor API endpoints
│   │   │   ├── route.ts                  # GET/POST competitors
│   │   │   ├── [id]/route.ts            # GET/PATCH/DELETE specific competitor
│   │   │   ├── [id]/snapshots/route.ts  # GET competitor snapshots
│   │   │   └── [id]/alerts/route.ts     # GET competitor alerts
│   │   └── cron/                         # Background jobs (Vercel Cron)
│   │       ├── scrape-competitors/       # Daily scraper (6 AM UTC)
│   │       ├── send-alerts/              # Daily alert sender (8 AM UTC)
│   │       └── send-weekly-digest/       # Weekly digest (Friday 9 AM UTC)
│   ├── dashboard/                        # Protected dashboard routes
│   │   ├── layout.tsx                    # Dashboard layout
│   │   ├── page.tsx                      # Competitor list
│   │   ├── rivals/
│   │   │   ├── new/page.tsx             # Add competitor form
│   │   │   └── [id]/page.tsx            # Competitor detail view
│   │   └── settings/page.tsx            # User preferences
│   └── auth/
│       ├── signin/page.tsx              # Sign in page
│       └── error/page.tsx               # Auth error page
├── lib/
│   ├── auth.ts                          # NextAuth configuration
│   ├── db.ts                            # Prisma client singleton
│   ├── scraping/
│   │   ├── firecrawl.ts                # Web scraping API
│   │   └── parser.ts                   # Parse scraped data
│   └── alerts/
│       ├── differ.ts                   # Compare snapshots & generate alerts
│       └── emailer.ts                  # Send emails via Resend
├── prisma/
│   ├── schema.prisma                   # Database schema
│   └── migrations/                     # Database migrations
├── middleware.ts                        # Route protection
├── vercel.json                         # Cron configuration
└── .env.example                        # Environment variables template
```

## Setup Instructions

### 1. Install Dependencies
```bash
npm install
```

This will install:
- `next-auth` & `@auth/prisma-adapter` - Authentication
- `@prisma/client` - ORM
- `resend` & `react-email` - Email sending
- `axios` - HTTP client for scraping

### 2. Database Setup

#### Option A: Local PostgreSQL (Development)
```bash
# Install PostgreSQL locally
# Create a database
createdb echoframe_dev

# Update .env.local
DATABASE_URL="postgresql://user:password@localhost:5432/echoframe_dev"

# Run migrations
npm run prisma:migrate
```

#### Option B: Supabase (Recommended for Production)
1. Create a free account at https://supabase.com
2. Create a new project
3. Copy the PostgreSQL connection string
4. Update `.env.local` with the Supabase connection string

#### Option C: Vercel PostgreSQL
1. Deploy to Vercel
2. Add Vercel Postgres database from dashboard
3. Environment variables are auto-configured

### 3. Authentication Setup

#### GitHub OAuth
1. Go to https://github.com/settings/developers
2. Create a new OAuth App
3. Set Authorization callback URL to `http://localhost:3000/api/auth/callback/github`
4. Copy Client ID and Secret to `.env.local`:
   ```
   AUTH_GITHUB_ID=your-client-id
   AUTH_GITHUB_SECRET=your-client-secret
   ```

#### Google OAuth
1. Go to https://console.cloud.google.com
2. Create a new OAuth 2.0 Client ID (Web Application)
3. Add `http://localhost:3000/api/auth/callback/google` to authorized redirect URIs
4. Copy Client ID and Secret to `.env.local`:
   ```
   AUTH_GOOGLE_ID=your-client-id
   AUTH_GOOGLE_SECRET=your-client-secret
   ```

### 4. Generate NextAuth Secret
```bash
openssl rand -base64 32
```
Copy the output to `.env.local`:
```
NEXTAUTH_SECRET=your-generated-secret
```

### 5. Email Service Setup (Resend)

1. Create account at https://resend.com
2. Get API key from dashboard
3. Verify your domain (or use Resend subdomain for testing)
4. Add to `.env.local`:
   ```
   RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxx
   ```

### 6. Web Scraping Setup (Firecrawl)

1. Sign up at https://firecrawl.dev
2. Get API key from dashboard
3. Add to `.env.local`:
   ```
   FIRECRAWL_API_KEY=fc_xxxxxxxxxxxxxxxxx
   ```

### 7. Create .env.local
Copy `.env.example` to `.env.local` and fill in all values:
```bash
cp .env.example .env.local
```

Complete the file with all your API keys and credentials.

## Running Locally

### Development Server
```bash
npm run dev
```
Open http://localhost:3000 in your browser.

### Database Admin UI
```bash
npm run prisma:studio
```
Open http://localhost:5555 to view/edit database directly.

## Testing Workflow

1. **Sign In**
   - Go to http://localhost:3000/auth/signin
   - Sign in with GitHub or Google
   - You'll be redirected to dashboard

2. **Add a Competitor**
   - Click "Add Competitor"
   - Enter competitor name, website, and optional Google Business/Yelp URLs
   - Click "Add Competitor"

3. **Manual Scraping (Testing)**
   - Go to http://localhost:3000/api/cron/scrape-competitors
   - The system will scrape all active competitors
   - Check database: `npm run prisma:studio`
   - Look for new entries in `competitor_snapshots` and `alerts` tables

4. **View Results**
   - Go back to dashboard to see updated competitor data
   - Click on a competitor to see:
     - Latest pricing, ratings, reviews
     - Alerts generated from changes
     - Historical snapshots

5. **Test Email Alerts**
   - Modify competitor data in Prisma Studio
   - Run the scraper again to detect changes
   - Check Resend dashboard for email logs

## Deployment to Vercel

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Rival Scan MVP"
git push origin main
```

### 2. Connect to Vercel
1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Set environment variables:
   - All `.env.local` variables
   - `CRON_SECRET` (generate with: `openssl rand -base64 32`)

### 3. Database Migration
```bash
vercel env pull  # Download environment variables
npm run prisma:migrate deploy  # Run migrations
```

### 4. Cron Jobs Activation
- Vercel will automatically pick up `vercel.json` cron configuration
- Jobs run at:
  - 6 AM UTC: Scrape all competitors
  - 8 AM UTC: Send daily alerts
  - 9 AM UTC Friday: Send weekly digest

### 5. Verify Crons
- Check Vercel dashboard → Functions → Crons
- View logs: Vercel dashboard → Deployments → Logs

## Email Testing

### Local Testing with Resend Sandbox
- During development, Resend sends test emails to the registered email
- Check your email inbox for alerts

### Production Email Sending
1. Verify your domain in Resend
2. Update email sender: `alerts@yourdomain.com`
3. Update `lib/alerts/emailer.ts`:
   ```typescript
   from: "alerts@yourdomain.com",  // Change from default
   ```

## Troubleshooting

### "Unauthorized" error on API calls
- Make sure you're signed in
- Check that middleware.ts is correctly protecting routes
- Verify NEXTAUTH_SECRET is set

### No data appearing after scrape
1. Check Firecrawl API key is valid
2. Verify competitor websites are accessible
3. Check database in Prisma Studio for `competitor_snapshots`

### Emails not sending
1. Verify Resend API key
2. Check Resend dashboard for email logs
3. For development: Resend sends to registered email only

### Database migration errors
```bash
# Reset database (development only!)
npx prisma migrate reset

# Re-run migrations
npm run prisma:migrate
```

## Next Steps for Production

1. **Add User Dashboard Settings**
   - Endpoint to save alert time preferences
   - Different email frequencies

2. **Improve Scraping**
   - Add Yelp review scraping
   - Better price extraction logic
   - Competitor photo/logo tracking

3. **Advanced Features**
   - Price history graphs
   - Competitor comparison view
   - Automated renegotiation suggestions
   - Custom alert rules

4. **Analytics**
   - Track competitor changes over time
   - Industry trends
   - User engagement metrics

5. **Security**
   - Rate limiting on API routes
   - Better error handling
   - Audit logging for user actions

## API Endpoints Reference

### Authentication
- `POST /api/auth/signin` - Sign in with provider
- `POST /api/auth/signout` - Sign out
- `POST /api/auth/callback/[provider]` - OAuth callback

### Competitors
- `GET /api/rivals` - List user's competitors
- `POST /api/rivals` - Create new competitor
- `GET /api/rivals/[id]` - Get competitor details
- `PATCH /api/rivals/[id]` - Update competitor
- `DELETE /api/rivals/[id]` - Delete competitor

### Snapshots & Alerts
- `GET /api/rivals/[id]/snapshots` - Get historical data
- `GET /api/rivals/[id]/alerts` - Get competitor alerts

### Cron Jobs
- `POST /api/cron/scrape-competitors` - Manual trigger
- `POST /api/cron/send-alerts` - Manual trigger
- `POST /api/cron/send-weekly-digest` - Manual trigger

## Questions or Issues?

- Check GitHub Issues
- Review implementation plan: `RIVAL_SCAN_SETUP.md`
- Test locally before deploying to Vercel
