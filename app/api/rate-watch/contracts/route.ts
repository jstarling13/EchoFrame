import { NextResponse, NextRequest } from 'next/server';
import prisma from '@/lib/db';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const { vendorName, category, currentRate, frequency, renewalDate } = body;

    // Validation
    if (!vendorName || !category || !currentRate || !frequency || !renewalDate) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Get or create demo user
    let user = await prisma.user.findFirst();
    if (!user) {
      user = await prisma.user.create({
        data: {
          email: 'demo@echoframe.local',
          name: 'Demo Business',
        },
      });
    }

    // Create vendor contract
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

export async function GET() {
  try {
    // Get or create demo user
    let user = await prisma.user.findFirst();
    if (!user) {
      user = await prisma.user.create({
        data: {
          email: 'demo@echoframe.local',
          name: 'Demo Business',
        },
      });
    }

    const contracts = await prisma.vendorContract.findMany({
      where: { userId: user.id },
    });

    return NextResponse.json(contracts);
  } catch (error) {
    console.error('Contract fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch contracts' },
      { status: 500 }
    );
  }
}
