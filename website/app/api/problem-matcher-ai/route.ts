import { NextRequest, NextResponse } from "next/server";
import { checkRateLimit } from "@/lib/rate-limit";
import { getAiProblemMatch } from "@/lib/problemMatcherAi";

export const runtime = "nodejs";

function getClientIdentifier(req: NextRequest): string {
  const forwarded = req.headers.get("x-forwarded-for");
  return forwarded?.split(",")[0]?.trim() || "unknown";
}

export async function POST(req: NextRequest) {
  const identifier = getClientIdentifier(req);

  // Tighter than the contact form: this feature calls a third-party AI
  // provider on a shared free-tier quota, so one visitor should never be
  // able to exhaust the site's entire daily allotment.
  const { success: withinLimit } = await checkRateLimit(identifier, {
    namespace: "problem-matcher-ai",
    maxRequests: 3,
    windowSeconds: 60,
  });
  if (!withinLimit) {
    return NextResponse.json(
      { ok: false, reason: "rate_limited" },
      { status: 429 }
    );
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json(
      { ok: false, reason: "invalid_input" },
      { status: 400 }
    );
  }

  const description =
    typeof body === "object" && body !== null && "description" in body
      ? (body as { description: unknown }).description
      : undefined;

  if (typeof description !== "string") {
    return NextResponse.json(
      { ok: false, reason: "invalid_input" },
      { status: 400 }
    );
  }

  // Never log the visitor's free-text description — only the outcome.
  const result = await getAiProblemMatch(description);
  console.info("problem_matcher_ai_outcome", {
    ok: result.ok,
    reason: result.ok ? undefined : result.reason,
  });

  if (!result.ok) {
    const status =
      result.reason === "not_configured"
        ? 503
        : result.reason === "invalid_input"
          ? 400
          : result.reason === "rate_limited"
            ? 429
            : 502;
    return NextResponse.json({ ok: false, reason: result.reason }, { status });
  }

  return NextResponse.json(result);
}
