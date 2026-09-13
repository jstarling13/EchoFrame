"use client";

import { FormEvent, useId, useState } from "react";
import { PROBLEM_MATCHER_DOCUMENTS } from "@/lib/problemMatcherCatalog";
import { matchProblem, type MatcherResult } from "@/lib/problemMatcher";

const MAX_LENGTH = 800;

export default function ProblemMatcher() {
  const descriptionId = useId();
  const [description, setDescription] = useState("");
  const [results, setResults] = useState<MatcherResult[] | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setResults(matchProblem(description, PROBLEM_MATCHER_DOCUMENTS));
  }

  return (
    <section className="problem-matcher" aria-labelledby={`${descriptionId}-title`}>
      <p className="eyebrow">Problem Matcher</p>
      <h2 id={`${descriptionId}-title`}>Describe the workflow that's getting in the way.</h2>
      <p>
        Use your own words. This compares your description against
        EchoFrame&rsquo;s published services and pricing &mdash; it does not
        send anything to an AI model.
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
