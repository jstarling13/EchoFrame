import type { MetadataRoute } from "next";
import { INSIGHTS_ARTICLES } from "@/lib/insights";

const ROUTES = [
  "",
  "/services",
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

  const staticEntries = ROUTES.map((route) => ({
    url: `${siteUrl}${route}`,
    lastModified,
    changeFrequency: "monthly" as const,
    priority: route === "" ? 1 : 0.6,
  }));

  // Generated from the same list that drives the /insights index, so a
  // held-back article (removed from INSIGHTS_ARTICLES, noindexed on its
  // own page) never ends up back in the sitemap by accident.
  const insightEntries = INSIGHTS_ARTICLES.map((article) => ({
    url: `${siteUrl}/insights/${article.slug}`,
    lastModified: new Date(article.date),
    changeFrequency: "monthly" as const,
    priority: 0.5,
  }));

  return [...staticEntries, ...insightEntries];
}
