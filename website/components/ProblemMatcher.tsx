"use client";

import { FormEvent, useId, useState } from "react";
import { PROBLEM_MATCHER_DOCUMENTS } from "@/lib/problemMatcherCatalog";
import { matchProblem, type MatcherResult } from "@/lib/problemMatcher";

const MAX_LENGTH = 800;

type AiState =
  | { status: "idle" }
  | { status: "loading" }
  | {
      status: "done";
      inScope: boolean;
      summary: string;
      relevantServices: { slug: string; name: string; blurb: string }[];
      nextStep: string;
    }
  | { status: "unavailable" };

export default function ProblemMatcher() {
  const descriptionId = useId();
  const [description, setDescription] = useState("");
  const [results, setResults] = useState<MatcherResult[] | null>(null);
  const [aiState, setAiState] = useState<AiState>({ status: "idle" });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setResults(matchProblem(description, PROBLEM_MATCHER_DOCUMENTS));
    setAiState({ status: "idle" });
  }

  async function handleAiFeedback() {
    setAiState({ status: "loading" });
    try {
      const res = await fetch("/api/problem-matcher-ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description }),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        setAiState({ status: "unavailable" });
        return;
      }
      setAiState({
        status: "done",
        inScope: data.inScope,
        summary: data.summary,
        relevantServices: data.relevantServices,
        nextStep: data.nextStep,
      });
    } catch {
      setAiState({ status: "unavailable" });
    }
  }

  return (
    <section className="problem-matcher" aria-labelledby={`${descriptionId}-title`}>
      <p className="eyebrow">Problem Matcher</p>
      <h2 id={`${descriptionId}-title`}>Describe the workflow that's getting in the way.</h2>
      <p>
        Use your own words. This compares your description against
        EchoFrame&rsquo;s published services and pricing &mdash; the match
        below runs entirely in your browser and does not send anything
        anywhere.
      </p>

      <form onSubmit={handleSubmit} className="problem-matcher__form">
        <div className="form-field">
          <label htmlFor={descriptionId}>What&rsquo;s happening today?</label>
          <textarea
            id={descriptionId}
            name="problem"
            value={description}
            onChange={(event) => {
              setDescription(event.target.value);
              if (results !== null) setResults(null);
              if (aiState.status !== "idle") setAiState({ status: "idle" });
            }}
            maxLength={MAX_LENGTH}
            minLength={12}
            rows={5}
            required
            aria-describedby={`${descriptionId}-help ${descriptionId}-count`}
            placeholder="For example: Every week, someone on our team manually matches bank deposits against invoices in QuickBooks."
          />
          <div className="problem-matcher__meta">
            <span id={`${descriptionId}-help`} className="hint">
              Do not include confidential, sensitive, or personal information.
            </span>
            <span id={`${descriptionId}-count`} className="hint" aria-live="polite">
              {description.length}/{MAX_LENGTH}
            </span>
          </div>
        </div>
        <button type="submit" className="btn btn-primary">
          Find the closest fit
        </button>
      </form>

      <div className="problem-matcher__results" aria-live="polite" aria-atomic="true">
        {results !== null && results.length > 0 && (
          <>
            <h3>Where EchoFrame may fit</h3>
            <p className="hint">
              These are the closest matches from EchoFrame&rsquo;s existing
              service information &mdash; not a quote, scope, or guarantee.
            </p>
            <ul>
              {results.map((result) => (
                <li key={result.id} className="card">
                  {result.text}
                </li>
              ))}
            </ul>

            <div className="problem-matcher__ai">
              {aiState.status === "idle" && (
                <>
                  <p className="hint">
                    Want a more personalized read on this? Sending your
                    description to Groq, a third-party AI provider, generates
                    a tailored summary &mdash; optional, and separate from
                    the matches above.
                  </p>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleAiFeedback}
                  >
                    Get AI-personalized feedback &rarr;
                  </button>
                </>
              )}

              {aiState.status === "loading" && (
                <p className="hint" role="status">
                  Thinking&hellip;
                </p>
              )}

              {aiState.status === "unavailable" && (
                <p className="hint" role="status">
                  AI-personalized feedback isn&rsquo;t available right now
                  &mdash; the matches above are already confirmed from
                  EchoFrame&rsquo;s published information.
                </p>
              )}

              {aiState.status === "done" && (
                <div className="callout">
                  <p className="eyebrow">AI-generated, via Groq</p>
                  <p>{aiState.summary}</p>
                  {aiState.relevantServices.length > 0 && (
                    <ul>
                      {aiState.relevantServices.map((service) => (
                        <li key={service.slug}>
                          <strong>{service.name}:</strong> {service.blurb}
                        </li>
                      ))}
                    </ul>
                  )}
                  <p style={{ marginBottom: 0 }}>
                    <strong>Next step:</strong> {aiState.nextStep}
                  </p>
                  <p className="hint" style={{ marginTop: "0.75rem", marginBottom: 0 }}>
                    Generated by an AI model from EchoFrame&rsquo;s published
                    content &mdash; not a quote, scope, or guarantee, and not
                    reviewed by a person before you see it.
                  </p>
                </div>
              )}
            </div>
          </>
        )}

        {results !== null && results.length === 0 && (
          <div role="status" className="callout">
            <h3>This needs a closer look.</h3>
            <p style={{ marginBottom: 0 }}>
              The description didn&rsquo;t closely match enough published
              information for a reliable answer here. Put it in the message
              field below and EchoFrame can review it directly.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
