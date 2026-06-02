import axios from "axios";

interface FirecrawlResponse {
  success: boolean;
  data: {
    content: string;
    markdown: string;
    html: string;
    metadata: Record<string, any>;
  };
}

export async function scrapeWebsite(url: string): Promise<string> {
  if (!process.env.FIRECRAWL_API_KEY) {
    throw new Error("FIRECRAWL_API_KEY not configured");
  }

  try {
    const response = await axios.post<FirecrawlResponse>(
      "https://api.firecrawl.dev/v1/scrape",
      {
        url,
        pageOptions: {
          onlyMainContent: true,
        },
      },
      {
        headers: {
          Authorization: `Bearer ${process.env.FIRECRAWL_API_KEY}`,
        },
      }
    );

    if (response.data.success) {
      return response.data.data.markdown || response.data.data.content;
    }

    throw new Error("Firecrawl request failed");
  } catch (error) {
    console.error(`Failed to scrape ${url}:`, error);
    throw error;
  }
}

export async function scrapeGoogleBusiness(
  googleUrl: string
): Promise<{
  reviewCount?: number;
  rating?: number;
}> {
  // Note: Actual Google Business scraping would require special handling
  // For MVP, return mock data or skip if google-play-scraper doesn't work
  // In production, consider using Google Places API instead
  return {
    reviewCount: Math.floor(Math.random() * 500),
    rating: Math.round(Math.random() * 50) / 10,
  };
}
