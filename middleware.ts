import { auth } from "@/lib/auth";

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isOnDashboard = req.nextUrl.pathname.startsWith("/dashboard");
  const isOnRivals = req.nextUrl.pathname.startsWith("/rivals");

  if ((isOnDashboard || isOnRivals) && !isLoggedIn) {
    return Response.redirect(new URL("/auth/signin", req.nextUrl));
  }
});

export const config = {
  matcher: ["/dashboard/:path*", "/rivals/:path*", "/api/rivals/:path*"],
};
