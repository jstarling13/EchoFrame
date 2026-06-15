"use client";

import { signIn } from "next-auth/react";
import { useState } from "react";
import Link from "next/link";
import { Github, Chrome, ArrowRight } from "lucide-react";

export default function SignInPage() {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState("");

  const handleSignIn = async (provider: string) => {
    try {
      setError("");
      setLoading(provider);
      await signIn(provider, { redirectTo: "/dashboard" });
    } catch (err) {
      setError("Failed to sign in. Please try again.");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-600 via-indigo-500 to-purple-600 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Rival Scan</h1>
          <p className="text-indigo-100">
            Monitor your competitors, stay ahead of the competition
          </p>
        </div>

        {/* Sign In Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Welcome Back
          </h2>
          <p className="text-gray-600 mb-8">
            Sign in to access your competitive intelligence dashboard
          </p>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <button
              onClick={() => handleSignIn("github")}
              disabled={loading === "github"}
              className="w-full flex items-center justify-center gap-3 bg-gray-900 hover:bg-gray-800 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-lg transition-colors"
            >
              <Github className="w-5 h-5" />
              {loading === "github" ? "Signing in..." : "Sign in with GitHub"}
              {loading !== "github" && <ArrowRight className="w-4 h-4" />}
            </button>

            <button
              onClick={() => handleSignIn("google")}
              disabled={loading === "google"}
              className="w-full flex items-center justify-center gap-3 bg-white hover:bg-gray-50 disabled:bg-gray-100 text-gray-900 font-medium py-3 px-4 rounded-lg border border-gray-300 transition-colors"
            >
              <Chrome className="w-5 h-5" />
              {loading === "google" ? "Signing in..." : "Sign in with Google"}
              {loading !== "google" && <ArrowRight className="w-4 h-4" />}
            </button>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-center text-sm text-gray-600">
              Don't have an account?{" "}
              <Link href="/" className="text-indigo-600 hover:underline font-medium">
                Get started free
              </Link>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-indigo-100 text-sm">
          <p>
            By signing in, you agree to our{" "}
            <Link href="/terms" className="underline hover:text-white">
              Terms of Service
            </Link>
            {" "}and{" "}
            <Link href="/privacy" className="underline hover:text-white">
              Privacy Policy
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
