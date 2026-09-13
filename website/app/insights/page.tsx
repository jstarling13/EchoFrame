import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumbs from "@/components/Breadcrumbs";
import { INSIGHTS_ARTICLES } from "@/lib/insights";

export const metadata: Metadata = {
  title: "Insights",
  description: "Notes on AI workflow implementation, governance, and training.",
};

function formatDate(iso: string): string {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  });
}

export default function InsightsPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/insights", label: "Insights" }]} />
        <h1>Insights</h1>
        <p>
          Working notes on how automation projects actually succeed or fail
          &mdash; written from the discipline behind The OWNED Method&trade;,
          not as marketing copy. Verified case studies are added only after
          real, confirmed engagement results.
        </p>
        <div style={{ marginTop: "2rem" }}>
          {INSIGHTS_ARTICLES.map((article) => (
            <div
              key={article.slug}
              className="card"
              style={{ marginBottom: "1.25rem" }}
            >
              <p className="hint" style={{ marginBottom: "0.35rem" }}>
                {formatDate(article.date)} &middot; {article.readingTimeMinutes} min read
              </p>
              <h2 style={{ marginTop: 0, marginBottom: "0.5rem" }}>
                <Link href={`/insights/${article.slug}`}>{article.title}</Link>
              </h2>
              <p style={{ marginBottom: 0 }}>{article.description}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
