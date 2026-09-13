"use client";

import { useState } from "react";
import Link from "next/link";
import {
  INDUSTRY_OPTIONS,
  PROBLEM_OPTIONS,
  getSelectorResult,
  getOptionLabel,
} from "@/lib/industrySelector";

export default function IndustrySelector() {
  const [industry, setIndustry] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  const result = industry && problem ? getSelectorResult(industry, problem) : null;
  const industryLabel = industry ? getOptionLabel(INDUSTRY_OPTIONS, industry) : undefined;

  return (
    <div className="industry-selector">
      <h2>What kind of business are you running?</h2>
      <p className="hint">Choose the closest fit. The workflow matters more than the label.</p>
      <div className="pill-group" role="group" aria-label="Industry">
        {INDUSTRY_OPTIONS.map((option) => (
          <button
            key={option.slug}
            type="button"
            className="pill"
            aria-pressed={industry === option.slug}
            onClick={() => {
              setIndustry(option.slug);
              setProblem(null);
            }}
          >
            {option.label}
          </button>
        ))}
      </div>

      {industry && (
        <div style={{ marginTop: "2rem" }}>
          <h2>What is taking too much time?</h2>
          <div className="pill-group" role="group" aria-label="Workflow problem">
            {PROBLEM_OPTIONS.map((option) => (
              <button
                key={option.slug}
                type="button"
                className="pill"
                aria-pressed={problem === option.slug}
                onClick={() => setProblem(option.slug)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <div aria-live="polite">
        {result && (
          <div className="callout industry-selector-result" style={{ marginTop: "2rem" }}>
            <p className="eyebrow">A Practical Place to Start</p>
            <p style={{ fontFamily: "var(--font-serif)", fontSize: "1.3rem" }}>
              {result.headline}
            </p>
            <p>
              <strong>{industryLabel}</strong> &mdash; common workflows EchoFrame can evaluate:
            </p>
            <ul>
              {result.startingPoints.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
            <p className="hint">{result.industryMessage}</p>
            <p>
              <strong>First question:</strong> {result.firstQuestion}
            </p>
            <Link
              href={`/contact?industry=${encodeURIComponent(industry!)}&problem=${encodeURIComponent(problem!)}`}
              className="btn btn-primary"
              style={{ marginTop: "1rem" }}
            >
              Talk Through This Workflow
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
