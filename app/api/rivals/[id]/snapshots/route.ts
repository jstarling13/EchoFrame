import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const competitor = await db.competitor.findUnique({
    where: { id: params.id },
  });

  if (!competitor || competitor.userId !== session.user.id) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const snapshots = await db.competitorSnapshot.findMany({
    where: { competitorId: params.id },
    orderBy: { scrapedAt: "desc" },
    take: 30,
  });

  return NextResponse.json(snapshots);
}
