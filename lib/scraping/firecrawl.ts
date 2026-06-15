import axios from "axios";

/**
 * Web + reviews ingestion for Rival Scan.
 *
 * - scrapeWebsite:        Firecrawl v1 scrape -> markdown (for pricing/promo parsing)
 * - fetchGooglePlacesData: real Google Places rating + review count (no mock data)
 * - fetchYelpData:        real Yelp Fusion rating + review count (no mock data)
 * - fetchReviewMetrics:   convenience wrapper used by the scraper cron
 *
 * IMPORTANT: when a key is missing or no match is found, these return `null`
 * (not random/zero values) so the diffing engine never fires false alerts.
 */

interface FirecrawlV1Response {
  success: boolean;
  data?: {
    markdown?: string;
    html?: string;
    content?: string;
    metadata?: Record<string, unknown>;
  };
}

export async function scrapeWebsite(url: string): Promise<string> {
  if (!process.env.FIRECRAWL_API_KEY) {
    throw new Error("FIRECRAWL_API_KEY not configured");
  }

  // Firecrawl v1 payload: `formats` + top-level `onlyMainContent`
  // (the old `pageOptions` shape is v0 and is ignored by /v1/scrape).
  const response = await axios.post<FirecrawlV1Response>(
    "https://api.firecrawl.dev/v1/scrape",
    {
      url,
      formats: ["markdown"],
      onlyMainContent: true,
    },
    {
      headers: { Authorization: `Bearer ${process.env.FIRECRAWL_API_KEY}` },
      timeout: 60_000,
    }
  );

  if (response.data.success && response.data.data) {
    return response.data.data.markdown || response.data.data.content || "";
  }
  throw new Error("Firecrawl request failed");
}

export interface ReviewMetrics {
  reviewCount: number | null;
  averageRating: number | null;
  source: "google" | "yelp" | null;
}

/** Try to pull an explicit place_id out of a Google Maps/Business URL. */
function extractPlaceId(url?: string | null): string | null {
  if (!url) return null;
  const q = url.match(/[?&]place_id=([^&]+)/);
  if (q) return decodeURIComponent(q[1]);
  return null;
}

/**
 * Google Places review count + rating.
 * Uses Place Details when a place_id is known, otherwise a Text Search by
 * "name + location". Returns null fields when the key/match is unavailable.
 */
export async function fetchGooglePlacesData(opts: {
  name: string;
  location?: string | null;
  googleBusinessUrl?: string | null;
}): Promise<{ reviewCount: number | null; averageRating: number | null }> {
  const key = process.env.GOOGLE_PLACES_API_KEY;
  if (!key) return { reviewCount: null, averageRating: null };

  try {
    const placeId = extractPlaceId(opts.googleBusinessUrl);

    if (placeId) {
      const { data } = await axios.get(
        "https://maps.googleapis.com/maps/api/place/details/json",
        {
          params: {
            place_id: placeId,
            fields: "rating,user_ratings_total",
            key,
          },
          timeout: 20_000,
        }
      );
      const r = data?.result;
      if (r) {
        return {
          reviewCount: typeof r.user_ratings_total === "number" ? r.user_ratings_total : null,
          averageRating: typeof r.rating === "number" ? r.rating : null,
        };
      }
    }

    // Fallback: text search by name + location
    const query = [opts.name, opts.location].filter(Boolean).join(" ");
    const { data } = await axios.get(
      "https://maps.googleapis.com/maps/api/place/textsearch/json",
      { params: { query, key }, timeout: 20_000 }
    );
    const hit = data?.results?.[0];
    if (hit) {
      return {
        reviewCount: typeof hit.user_ratings_total === "number" ? hit.user_ratings_total : null,
        averageRating: typeof hit.rating === "number" ? hit.rating : null,
      };
    }
  } catch (error) {
    console.error(`[places] lookup failed for ${opts.name}:`, error);
  }
  return { reviewCount: null, averageRating: null };
}

/**
 * Yelp Fusion review count + rating via business search (name + location).
 * Returns null fields when the key/match is unavailable.
 */
export async function fetchYelpData(opts: {
  name: string;
  location?: string | null;
}): Promise<{ reviewCount: number | null; averageRating: number | null }> {
  const key = process.env.YELP_API_KEY;
  if (!key) return { reviewCount: null, averageRating: null };

  try {
    const { data } = await axios.get(
      "https://api.yelp.com/v3/businesses/search",
      {
        params: { term: opts.name, location: opts.location || "United States", limit: 1 },
        headers: { Authorization: `Bearer ${key}` },
        timeout: 20_000,
      }
    );
    const biz = data?.businesses?.[0];
    if (biz) {
      return {
        reviewCount: typeof biz.review_count === "number" ? biz.review_count : null,
        averageRating: typeof biz.rating === "number" ? biz.rating : null,
      };
    }
  } catch (error) {
    console.error(`[yelp] lookup failed for ${opts.name}:`, error);
  }
  return { reviewCount: null, averageRating: null };
}

/**
 * Combined review metrics for a competitor. Google Places is the primary
 * source; Yelp is used as a fallback when Google has no data.
 */
export async function fetchReviewMetrics(opts: {
  name: string;
  location?: string | null;
  googleBusinessUrl?: string | null;
  yelpUrl?: string | null;
}): Promise<ReviewMetrics> {
  const google = await fetchGooglePlacesData(opts);
  if (google.reviewCount !== null || google.averageRating !== null) {
    return { ...google, source: "google" };
  }

  if (opts.yelpUrl || process.env.YELP_API_KEY) {
    const yelp = await fetchYelpData(opts);
    if (yelp.reviewCount !== null || yelp.averageRating !== null) {
      return { ...yelp, source: "yelp" };
    }
  }

  return { reviewCount: null, averageRating: null, source: null };
}
