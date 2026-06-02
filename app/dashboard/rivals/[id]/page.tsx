"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Trash2, ExternalLink, AlertCircle, TrendingUp, TrendingDown } from "lucide-react";

interface Competitor {
  id: string;
  name: string;
  website: string;
  googleBusinessUrl?: string;
  yelpUrl?: string;
  status: string;
  snapshots?: any[];
  alerts?: any[];
}

export default function CompetitorDetailPage() {
  const params = useParams();
  const router = useRouter();
  const competitorId = params.id as string;

  const [competitor, setCompetitor] = useState<Competitor | null>(null);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"overview" | "history" | "alerts">("overview");

  useEffect(() => {
    fetchCompetitorData();
  }, [competitorId]);

  const fetchCompetitorData = async () => {
    try {
      setLoading(true);
      const [compRes, snapRes, alertRes] = await Promise.all([
        fetch(`/api/rivals/${competitorId}`),
        fetch(`/api/rivals/${competitorId}/snapshots`),
        fetch(`/api/rivals/${competitorId}/alerts`),
      ]);

      if (!compRes.ok) throw new Error("Failed to fetch competitor");

      const comp = await compRes.json();
      setCompetitor(comp);

      if (snapRes.ok) {
        const snaps = await snapRes.json();
        setSnapshots(snaps);
      }

      if (alertRes.ok) {
        const alts = await alertRes.json();
        setAlerts(alts);
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this competitor?")) {
      return;
    }

    try {
      const res = await fetch(`/api/rivals/${competitorId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete");
      router.push("/dashboard");
    } catch (err) {
      setError(String(err));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!competitor) {
    return (
      <div className="text-center">
        <p className="text-gray-600">Competitor not found</p>
        <Link href="/dashboard" className="text-indigo-600 hover:underline">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const latestSnapshot = snapshots[0];
  const unsentAlerts = alerts.filter((a) => !a.sentAt);

  return (
    <div>
      <Link
        href="/dashboard"
        className="flex items-center gap-2 text-indigo-600 hover:text-indigo-700 mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {competitor.name}
            </h1>
            <a
              href={competitor.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 hover:text-indigo-700 flex items-center gap-2"
            >
              {competitor.website}
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
          <button
            onClick={handleDelete}
            className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>

        {unsentAlerts.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium text-yellow-800">
                {unsentAlerts.length} unsent alert{unsentAlerts.length !== 1 ? "s" : ""}
              </p>
              <p className="text-sm text-yellow-700">
                These will be sent in the next daily alert email
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Latest Data */}
      {latestSnapshot && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {latestSnapshot.priceRange && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-sm text-gray-600 mb-1">Price Range</p>
              <p className="text-2xl font-bold text-gray-900">
                {latestSnapshot.priceRange}
              </p>
            </div>
          )}

          {latestSnapshot.averageRating && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-sm text-gray-600 mb-1">Average Rating</p>
              <div className="flex items-center gap-2">
                <p className="text-2xl font-bold text-gray-900">
                  {latestSnapshot.averageRating.toFixed(1)}
                </p>
                <span className="text-yellow-400 text-xl">★</span>
              </div>
            </div>
          )}

          {latestSnapshot.reviewCount && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-sm text-gray-600 mb-1">Review Count</p>
              <p className="text-2xl font-bold text-gray-900">
                {latestSnapshot.reviewCount}
              </p>
            </div>
          )}

          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-sm text-gray-600 mb-1">Last Updated</p>
            <p className="text-lg font-bold text-gray-900">
              {new Date(latestSnapshot.scrapedAt).toLocaleDateString()}
            </p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <div className="flex gap-8">
          <button
            onClick={() => setActiveTab("overview")}
            className={`py-3 px-1 font-medium border-b-2 transition-colors ${
              activeTab === "overview"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-600 hover:text-gray-900"
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`py-3 px-1 font-medium border-b-2 transition-colors ${
              activeTab === "history"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-600 hover:text-gray-900"
            }`}
          >
            History ({snapshots.length})
          </button>
          <button
            onClick={() => setActiveTab("alerts")}
            className={`py-3 px-1 font-medium border-b-2 transition-colors ${
              activeTab === "alerts"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-600 hover:text-gray-900"
            }`}
          >
            Alerts ({alerts.length})
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {latestSnapshot?.activePromos && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Active Promotions
              </h3>
              {latestSnapshot.activePromos.split("|").length > 0 ? (
                <ul className="space-y-2">
                  {latestSnapshot.activePromos.split("|").map((promo: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-indigo-600 mt-1">•</span>
                      <span className="text-gray-700">{promo.trim()}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-600">No active promotions detected</p>
              )}
            </div>
          )}

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Links</h3>
            <div className="space-y-3">
              <a
                href={competitor.website}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded-lg"
              >
                <span className="text-gray-900 font-medium">Website</span>
                <ExternalLink className="w-4 h-4 text-gray-400" />
              </a>
              {competitor.googleBusinessUrl && (
                <a
                  href={competitor.googleBusinessUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded-lg"
                >
                  <span className="text-gray-900 font-medium">Google Business</span>
                  <ExternalLink className="w-4 h-4 text-gray-400" />
                </a>
              )}
              {competitor.yelpUrl && (
                <a
                  href={competitor.yelpUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded-lg"
                >
                  <span className="text-gray-900 font-medium">Yelp</span>
                  <ExternalLink className="w-4 h-4 text-gray-400" />
                </a>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === "history" && (
        <div className="bg-white rounded-lg border border-gray-200">
          {snapshots.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-600">No history yet. Check back after the first scan.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-gray-200 bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Date</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Price</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Rating</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Reviews</th>
                  </tr>
                </thead>
                <tbody>
                  {snapshots.map((snap) => (
                    <tr key={snap.id} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-6 py-3 text-sm text-gray-900">
                        {new Date(snap.scrapedAt).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-600">
                        {snap.priceRange || "—"}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-600">
                        {snap.averageRating ? `${snap.averageRating.toFixed(1)} ★` : "—"}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-600">
                        {snap.reviewCount || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === "alerts" && (
        <div className="space-y-4">
          {alerts.length === 0 ? (
            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
              <p className="text-gray-600">No alerts yet</p>
            </div>
          ) : (
            alerts.map((alert) => (
              <div
                key={alert.id}
                className={`bg-white rounded-lg border p-4 ${
                  alert.severity === "HIGH"
                    ? "border-red-200 bg-red-50"
                    : alert.severity === "MEDIUM"
                      ? "border-yellow-200 bg-yellow-50"
                      : "border-green-200 bg-green-50"
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold text-gray-900">
                      {alert.alertType.replace(/_/g, " ")}
                    </h4>
                    <p className="text-gray-700 mt-1">{alert.description}</p>
                    {alert.oldValue && (
                      <p className="text-sm text-gray-600 mt-2">
                        <span className="font-medium">Changed from:</span> {alert.oldValue}
                        <span className="mx-2">→</span>
                        <span className="font-medium">to:</span> {alert.newValue}
                      </p>
                    )}
                  </div>
                  <span className={`text-xs font-medium px-2 py-1 rounded ${
                    alert.severity === "HIGH"
                      ? "bg-red-200 text-red-800"
                      : alert.severity === "MEDIUM"
                        ? "bg-yellow-200 text-yellow-800"
                        : "bg-green-200 text-green-800"
                  }`}>
                    {alert.severity}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-3">
                  {new Date(alert.createdAt).toLocaleString()}
                  {alert.sentAt && ` • Sent: ${new Date(alert.sentAt).toLocaleString()}`}
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
