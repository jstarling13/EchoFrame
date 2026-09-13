"use client";

import { FormEvent, useId, useState } from "react";
import { PROBLEM_MATCHER_DOCUMENTS } from "@/lib/problemMatcherCatalog";
import { matchProblem, type MatcherResult } from "@/lib/problemMatcher";

const MAX_LENGTH = 800;

export default function ProblemMatcher() {
  const descriptionId = useId();
  const resultsId = useId();
  const [description, setDescription] = useState("");
  const [results, setResults] = useState<MatcherResult[] | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setResults(matchProblem(description, PROBLEM_MATCHER_DOCUMENTS));
  }

  return (
    <section
      className="problem-matcher"
      aria-labelledby={`${descriptionId}-title`}
    >
      <div className="problem-matcher__intro">
        <p className="eyebrow">Problem matcher</p>
        <h2 id={`${descriptionId}-title`}>
          Describe the workflow that is getting in the way.
        </h2>
        <p>
          Use your own words. This tool compares your description with
          EchoFrame’s published services and does not send it to an AI model.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="problem-matcher__form">
        <label htmlFor={descriptionId}>What is happening today?</label>
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
          rows={6}
          required
          aria-describedby={`${descriptionId}-help ${descriptionId}-count`}
          placeholder="For example: [PLACEHOLDER — replace with a reviewed, representative client problem.]"
        />
        <div className="problem-matcher__meta">
          <p id={`${descriptionId}-help`}>
            Do not include confidential, sensitive, or personal information.
          </p>
          <p id={`${descriptionId}-count`} aria-live="polite">
            {description.length}/{MAX_LENGTH}
          </p>
        </div>
        <button type="submit">Find the closest fit</button>
      </form>

      <div
        id={resultsId}
        className="problem-matcher__results"
        aria-live="polite"
        aria-atomic="true"
      >
        {results !== null && results.length > 0 && (
          <>
            <h3>Where EchoFrame may fit</h3>
            <p>
              These are the closest matches from EchoFrame’s existing service
              information.
            </p>
            <ul>
              {results.map((result) => (
                <li key={result.id}>
                  <p>{result.text}</p>
                </li>
              ))}
            </ul>
            <p>
              A match is informational, not a quote, scope, guarantee, or
              confirmation that the work is a fit.
            </p>
          </>
        )}

        {results !== null && results.length === 0 && (
          <div role="status">
            <h3>This needs a closer look.</h3>
            <p>
              The description did not closely match enough published information
              for this tool to give a reliable answer. Send it with your
              fit-call request and EchoFrame can review it directly.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
