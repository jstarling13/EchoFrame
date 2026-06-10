import { NextResponse, NextRequest } from 'next/server';
import { getCompanyDashboard } from '@/lib/rate-watch-data';

export async function GET(request: NextRequest) {
  try {
    const slug = request.nextUrl.searchParams.get('slug');
    if (!slug) {
      return NextResponse.json(
        { error: 'Missing required "slug" query parameter' },
        { status: 400 }
      );
    }

    const dashboard = await getCompanyDashboard(slug);
    if (!dashboard) {
      return NextResponse.json(
        { error: `No company found for slug "${slug}"` },
        { status: 404 }
      );
    }

    return NextResponse.json(dashboard);
  } catch (error) {
    console.error('Dashboard error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch dashboard data' },
      { status: 500 }
    );
  }
}
