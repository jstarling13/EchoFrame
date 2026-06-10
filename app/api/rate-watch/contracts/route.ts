import { NextResponse, NextRequest } from 'next/server';
import prisma from '@/lib/db';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { companySlug, vendorName, category, currentRate, frequency, renewalDate } = body;

    // Validation
    if (!companySlug || !vendorName || !category || !currentRate || !frequency || !renewalDate) {
      return NextResponse.json(
        { error: 'Missing required fields (companySlug, vendorName, category, currentRate, frequency, renewalDate)' },
        { status: 400 }
      );
    }

    const user = await prisma.user.findUnique({ where: { slug: companySlug } });
    if (!user) {
      return NextResponse.json(
        { error: `No company found for slug "${companySlug}"` },
        { status: 404 }
      );
    }

    const contract = await prisma.vendorContract.create({
      data: {
        userId: user.id,
        vendorName,
        category,
        currentRate: parseFloat(currentRate),
        frequency,
        renewalDate: new Date(renewalDate),
      },
    });

    return NextResponse.json(contract, { status: 201 });
  } catch (error) {
    console.error('Contract creation error:', error);
    return NextResponse.json(
      { error: 'Failed to create contract' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const slug = request.nextUrl.searchParams.get('slug');
    if (!slug) {
      return NextResponse.json(
        { error: 'Missing required "slug" query parameter' },
        { status: 400 }
      );
    }

    const user = await prisma.user.findUnique({
      where: { slug },
      include: { contracts: true },
    });
    if (!user) {
      return NextResponse.json(
        { error: `No company found for slug "${slug}"` },
        { status: 404 }
      );
    }

    return NextResponse.json(user.contracts);
  } catch (error) {
    console.error('Contract fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch contracts' },
      { status: 500 }
    );
  }
}
