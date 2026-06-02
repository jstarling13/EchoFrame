import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";

// Next.js 15: `params` is a Promise and must be awaited.
type RouteParams = { params: Promise<{ id: string }> };

export async function GET(request: NextRequest, { params }: RouteParams) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;

  const competitor = await db.competitor.findUnique({
    where: { id },
    include: {
      snapshots: {
        orderBy: { scrapedAt: "desc" },
        take: 5,
      },
      alerts: {
        orderBy: { createdAt: "desc" },
        take: 20,
      },
    },
  });

  if (!competitor || competitor.userId !== session.user.id) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  return NextResponse.json(competitor);
}

export async function PATCH(request: NextRequest, { params }: RouteParams) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;

  const competitor = await db.competitor.findUnique({
    where: { id },
  });

  if (!competitor || competitor.userId !== session.user.id) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const { name, website, googleBusinessUrl, yelpUrl, status } =
    await request.json();

  const updated = await db.competitor.update({
    where: { id },
    data: {
      ...(name && { name }),
      ...(website && { website }),
      ...(googleBusinessUrl !== undefined && { googleBusinessUrl }),
      ...(yelpUrl !== undefined && { yelpUrl }),
      ...(status && { status }),
    },
  });

  return NextResponse.json(updated);
}

export async function DELETE(request: NextRequest, { params }: RouteParams) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;

  const competitor = await db.competitor.findUnique({
    where: { id },
  });

  if (!competitor || competitor.userId !== session.user.id) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  await db.competitor.delete({
    where: { id },
  });

  return NextResponse.json({ success: true });
}
