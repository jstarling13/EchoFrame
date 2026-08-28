import type { MetadataRoute } from "next";

const ROUTES = [
  "",
  "/services",
  "/workflow-diagnostic",
  "/build-sprint",
  "/transformation",
  "/enterprise",
  "/support",
  "/industries",
  "/method",
  "/training",
  "/security",
  "/about",
  "/insights",
  "/contact",
  "/privacy",
  "/terms",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
  const lastModified = new Date();
  return ROUTES.map((route) => ({
    url: `${siteUrl}${route}`,
    lastModified,
    changeFrequency: "monthly",
    priority: route === "" ? 1 : 0.6,
  }));
}
