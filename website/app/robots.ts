import type { MetadataRoute } from "next";
import { isProductionDeployment } from "@/lib/environment";

export default function robots(): MetadataRoute.Robots {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

  if (!isProductionDeployment()) {
    // Preview/local: disallow everything. Search engines must never index
    // a Preview deployment or a local build.
    return {
      rules: [{ userAgent: "*", disallow: "/" }],
    };
  }

  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/api/", "/thank-you"],
      },
    ],
    sitemap: `${siteUrl}/sitemap.xml`,
  };
}
