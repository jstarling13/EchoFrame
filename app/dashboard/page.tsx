"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Plus, AlertCircle, TrendingDown, TrendingUp } from "lucide-react";
import { Competitor } from "@prisma/client";

interface CompetitorWithData extends Competitor {
  snapshots?: any[];
  alerts?: any[];
}

export default function DashboardPage() {
  const [competitors, setCompetitors] = useState<CompetitorWithData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchCompetitors();
  }, []);

  const fetchCompetitors = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/rivals");
      if (!res.ok) throw new Error("Failed to fetch competitors");
      const data = await res.json();
      setCompetitors(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-gray-600">
            {competitors.length} competitor{competitors.length !== 1 ? "s" : ""}{" "}
            monitored
          </p>
        </div>
        <Link
          href="/dashboard/rivals/new"
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg"
        >
          <Plus className="w-5 h-5" />
          Add Competitor
        </Link>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {competitors.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">
            No competitors yet
          </p>
          <p className="text-gray-600 mb-6">
            Start monitoring your competitors by adding their information.
          </p>
          <Link
            href="/dashboard/rivals/new"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg"
          >
            <Plus className="w-5 h-5" />
            Add Your First Competitor
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {competitors.map((competitor) => {
            const latestSnapshot = competitor.snapshots?.[0];
            const unsentAlerts = competitor.alerts?.filter(
              (a) => !a.sentAt
            ).length || 0;

            return (
              <Link
                key={competitor.id}
                href={`/dashboard/rivals/${competitor.id}`}
                className="block bg-white rounded-lg border border-gray-200 hover:shadow-lg hover:border-indigo-300 transition-all p-6"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {competitor.name}
                    </h3>
                    <p className="text-sm text-gray-600 truncate">
                      {competitor.website}
                    </p>
                  </div>
                  {unsentAlerts > 0 && (
                    <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-medium">
                      {unsentAlerts} new
                    </span>
                  )}
                </div>

                {latestSnapshot && (
                  <div className="space-y-3">
                    {latestSnapshot.priceRange && (
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Price Range:</span>
                        <span className="font-medium text-gray-900">
                          {latestSnapshot.priceRange}
                        </span>
                      </div>
                    )}

                    {latestSnapshot.averageRating && (
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Rating:</span>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">
                            {latestSnapshot.averageRating.toFixed(1)}
                          </span>
                          <span className="text-yellow-400">★</span>
                        </div>
                      </div>
                    )}

                    {latestSnapshot.reviewCount && (
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Reviews:</span>
                        <span className="font-medium text-gray-900">
                          {latestSnapshot.reviewCount}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-500">
                    Last updated:{" "}
                    {latestSnapshot
                      ? new Date(latestSnapshot.scrapedAt).toLocaleDateString()
                      : "Never"}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
