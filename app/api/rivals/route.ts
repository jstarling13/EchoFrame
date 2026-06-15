import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { name, website, googleBusinessUrl, yelpUrl } = await request.json();

  if (!name || !website) {
    return NextResponse.json(
      { error: "Name and website are required" },
      { status: 400 }
    );
  }

  const competitor = await db.competitor.create({
    data: {
      userId: session.user.id,
      name,
      website,
      googleBusinessUrl,
      yelpUrl,
    },
  });

  return NextResponse.json(competitor, { status: 201 });
}

export async function GET(request: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const competitors = await db.competitor.findMany({
    where: { userId: session.user.id },
    include: {
      snapshots: {
        orderBy: { scrapedAt: "desc" },
        take: 1,
      },
      alerts: {
        where: { sentAt: null },
        orderBy: { createdAt: "desc" },
        take: 5,
      },
    },
  });

  return NextResponse.json(competitors);
}
