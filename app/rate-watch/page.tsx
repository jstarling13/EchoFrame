import Link from 'next/link';
import { getCompanies } from '@/lib/rate-watch-data';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Building2, ArrowRight } from 'lucide-react';

export const dynamic = 'force-dynamic';

const bracketLabel: Record<string, string> = {
  SMALL: '1–10 employees',
  MEDIUM: '11–50 employees',
  LARGE: '50+ employees',
};

export default async function RateWatchHome() {
  const companies = await getCompanies();

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Sample Clients</h2>
        <p className="text-sm text-slate-600 mt-1">
          Select a business to view its Rate Watch dashboard and renegotiation report.
        </p>
      </div>

      {companies.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            No companies seeded yet. Run{' '}
            <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-700">
              npx tsx prisma/seed.ts
            </code>
            .
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {companies.map((c) => (
            <Link key={c.slug} href={`/rate-watch/${c.slug}`} className="group">
              <Card className="h-full transition-all group-hover:border-slate-400 group-hover:shadow-md">
                <CardContent className="p-6 flex flex-col h-full">
                  <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-slate-900 text-white mb-4">
                    <Building2 className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">{c.name}</h3>
                  <p className="text-sm text-slate-600 mt-1">{c.industry}</p>

                  <div className="flex flex-wrap gap-2 mt-4">
                    <Badge variant="secondary">{c.location}</Badge>
                    <Badge variant="outline">{bracketLabel[c.companySizeBracket] ?? c.companySizeBracket}</Badge>
                    <Badge variant="info">{c.vendorCount} vendors</Badge>
                  </div>

                  <div className="mt-auto pt-6 flex items-center gap-1 text-sm font-medium text-slate-900">
                    View dashboard
                    <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
