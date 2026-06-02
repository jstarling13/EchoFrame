export interface ScrapedData {
  priceRange?: string;
  activePromos?: string[];
  content: string;
}

export function parseScrapedContent(markdown: string): ScrapedData {
  const data: ScrapedData = {
    content: markdown,
    activePromos: [],
  };

  // Extract price ranges (look for common patterns like $X-$Y or $X/hour)
  const priceMatch = markdown.match(/\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*-\s*\$(\d+(?:,\d{3})*(?:\.\d{2})?)/);
  if (priceMatch) {
    data.priceRange = `$${priceMatch[1]} - $${priceMatch[2]}`;
  }

  // Extract promotions (look for common promo keywords)
  const promoKeywords = [
    "discount",
    "off",
    "special",
    "offer",
    "promotion",
    "sale",
    "deal",
    "limited time",
  ];

  const lines = markdown.split("\n");
  lines.forEach((line) => {
    const lowerLine = line.toLowerCase();
    promoKeywords.forEach((keyword) => {
      if (lowerLine.includes(keyword) && line.length < 200) {
        if (!data.activePromos?.includes(line.trim())) {
          data.activePromos?.push(line.trim());
        }
      }
    });
  });

  return data;
}

export function extractMetricsFromMarkdown(markdown: string) {
  const metrics: Record<string, any> = {};

  // Count review/rating mentions
  const ratingMatch = markdown.match(
    /(\d+(?:\.\d+)?)\s*(?:star|\/\s*5|rating)/i
  );
  if (ratingMatch) {
    metrics.estimatedRating = parseFloat(ratingMatch[1]);
  }

  // Count review count mentions
  const reviewMatch = markdown.match(/(\d+(?:,\d{3})*)\s*(?:review|rating)/i);
  if (reviewMatch) {
    metrics.estimatedReviewCount = parseInt(
      reviewMatch[1].replace(/,/g, ""),
      10
    );
  }

  return metrics;
}
