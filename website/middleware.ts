import { NextRequest, NextResponse } from "next/server";

/**
 * Scoped to /admin only (see matcher below) — unrelated to the CSP-nonce
 * middleware attempt documented in next.config.ts, which was reverted
 * because it forced every route to render dynamically. This middleware
 * never touches other routes' rendering; it only gates a handful of
 * internal-tool pages behind one shared password.
 */
export const config = {
  matcher: ["/admin/:path*"],
};

export function middleware(req: NextRequest) {
  const username = process.env.ADMIN_INVOICE_USERNAME;
  const password = process.env.ADMIN_INVOICE_PASSWORD;

  // Fail closed: an internal billing tool (client names, rates) must
  // never be reachable just because credentials weren't configured yet.
  if (!username || !password) {
    return new NextResponse("Not configured", { status: 503 });
  }

  const expected = `Basic ${Buffer.from(`${username}:${password}`).toString("base64")}`;
  if (req.headers.get("authorization") === expected) {
    return NextResponse.next();
  }

  return new NextResponse("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="EchoFrame Admin"' },
  });
}
