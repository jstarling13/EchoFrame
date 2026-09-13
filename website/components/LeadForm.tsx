"use client";

import { useId, useRef, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { employeeRanges, urgencyLevels } from "@/lib/validation";

const HONEYPOT_FIELD =
  process.env.NEXT_PUBLIC_CONTACT_FORM_HONEYPOT_FIELD || "company_website";

type Errors = Record<string, string>;

export default function LeadForm({
  initialWorkflowProblem,
}: {
  initialWorkflowProblem?: string;
}) {
  const router = useRouter();
  const [errors, setErrors] = useState<Errors>({});
  const [submitting, setSubmitting] = useState(false);
  const summaryRef = useRef<HTMLDivElement>(null);
  const formId = useId();

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setErrors({});

    const form = e.currentTarget;
    const data = new FormData(form);
    const payload = {
      name: String(data.get("name") || ""),
      email: String(data.get("email") || ""),
      company: String(data.get("company") || ""),
      role: String(data.get("role") || ""),
      website: String(data.get("website") || ""),
      employeeRange: String(data.get("employeeRange") || ""),
      state: String(data.get("state") || ""),
      workflowProblem: String(data.get("workflowProblem") || ""),
      urgency: String(data.get("urgency") || ""),
      referralSource: String(data.get("referralSource") || ""),
      consent: data.get("consent") === "on",
      [HONEYPOT_FIELD]: String(data.get(HONEYPOT_FIELD) || ""),
    };

    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await res.json();

      if (!res.ok || !body.ok) {
        setErrors(body.errors || { form: "Something went wrong. Try again." });
        setSubmitting(false);
        requestAnimationFrame(() => summaryRef.current?.focus());
        return;
      }

      router.push(`/thank-you?leadId=${encodeURIComponent(body.leadId)}`);
    } catch {
      setErrors({ form: "Network error. Check your connection and try again." });
      setSubmitting(false);
      requestAnimationFrame(() => summaryRef.current?.focus());
    }
  }

  const errorEntries = Object.entries(errors);

  return (
    <form onSubmit={onSubmit} noValidate aria-describedby={errorEntries.length ? `${formId}-errors` : undefined}>
      {errorEntries.length > 0 && (
        <div
          className="error-summary"
          id={`${formId}-errors`}
          ref={summaryRef}
          tabIndex={-1}
          role="alert"
        >
          <h2>Please fix the following</h2>
          <ul>
            {errorEntries.map(([field, message]) => (
              <li key={field}>
                <a href={`#${formId}-${field}`}>{message}</a>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className={`form-field ${errors.name ? "has-error" : ""}`}>
        <label htmlFor={`${formId}-name`}>Name</label>
        <input id={`${formId}-name`} name="name" type="text" autoComplete="name" required />
        {errors.name && <span className="field-error">{errors.name}</span>}
      </div>

      <div className={`form-field ${errors.email ? "has-error" : ""}`}>
        <label htmlFor={`${formId}-email`}>Work email</label>
        <input id={`${formId}-email`} name="email" type="email" autoComplete="email" required />
        {errors.email && <span className="field-error">{errors.email}</span>}
      </div>

      <div className={`form-field ${errors.company ? "has-error" : ""}`}>
        <label htmlFor={`${formId}-company`}>Company</label>
        <input id={`${formId}-company`} name="company" type="text" autoComplete="organization" required />
        {errors.company && <span className="field-error">{errors.company}</span>}
      </div>

      <div className={`form-field ${errors.role ? "has-error" : ""}`}>
        <label htmlFor={`${formId}-role`}>Role</label>
        <input id={`${formId}-role`} name="role" type="text" required />
        {errors.role && <span className="field-error">{errors.role}</span>}
      </div>

      <div className={`form-field ${errors.website ? "has-error" : ""}`}>
        <label htmlFor={`${formId}-website`}>
          Company website <span className="hint">(optional)</span>
        </label>
        <input id={`${formId}-website`} name="website" type="url" placeholder="https://" />
        {errors.website && <span className="field-error">{errors.website}</span>}
      </div>

      <div className={`form-field ${errors.employeeRange ? "has-error" : ""}`}>
        <label htmlFor={`${formId}-employeeRange`}>Employees</label>
        <select id={`${formId}-employeeRange`} name="employeeRange" required defaultValue="">
          <option value="" disabled>
            Select a range
          </option>
          {employeeRanges.map((range) => (
            <option key={range} value={range}>
              {range}
            </option>
          ))}
        </select>
        {errors.employeeRange && <span className="field-error">{errors.employeeRange}</span>}
      </div>

      <div className={`form-field ${errors.state ? "has-error" : ""}`}>
        <label htmlFor={`${formId}-state`}>State</label>
        <input id={`${formId}-state`} name="state" type="text" autoComplete="address-level1" required />
        {errors.state && <span className="field-error">{errors.state}</span>}
      </div>

      <div className={`form-field ${errors.workflowProblem ? "has-error" : ""}`}>
        <label htmlFor={`${formId}-workflowProblem`}>Where does work wait or repeat?</label>
        <span className="hint">
          Do not include confidential, health, financial-account, credential, or privileged
          information.
        </span>
        <textarea
          id={`${formId}-workflowProblem`}
          name="workflowProblem"
          required
          defaultValue={initialWorkflowProblem}
        />
        {errors.workflowProblem && (
          <span className="field-error">{errors.workflowProblem}</span>
        )}
      </div>

      <fieldset>
        <legend>Urgency</legend>
        {urgencyLevels.map((level) => (
          <div key={level} style={{ marginBottom: "0.5rem" }}>
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: 400 }}>
              <input type="radio" name="urgency" value={level} required />
              {level}
            </label>
          </div>
        ))}
        {errors.urgency && <span className="field-error">{errors.urgency}</span>}
      </fieldset>

      <div className={`form-field ${errors.referralSource ? "has-error" : ""}`}>
        <label htmlFor={`${formId}-referralSource`}>
          Referral source <span className="hint">(optional)</span>
        </label>
        <input id={`${formId}-referralSource`} name="referralSource" type="text" />
      </div>

      {/* Honeypot: hidden from real users; a filled value marks the submission as spam. */}
      <div className="honeypot-field" aria-hidden="true">
        <label htmlFor={`${formId}-${HONEYPOT_FIELD}`}>Leave this field empty</label>
        <input id={`${formId}-${HONEYPOT_FIELD}`} name={HONEYPOT_FIELD} type="text" tabIndex={-1} autoComplete="off" />
      </div>

      <div className={`form-field ${errors.consent ? "has-error" : ""}`}>
        <label style={{ display: "flex", alignItems: "flex-start", gap: "0.6rem", fontWeight: 400 }}>
          <input type="checkbox" name="consent" required style={{ width: "auto", marginTop: "0.2rem" }} />
          <span className="consent-notice">
            I consent to EchoFrame contacting me about this request and
            storing the information above per the <a href="/privacy">privacy policy</a>.
          </span>
        </label>
        {errors.consent && <span className="field-error">{errors.consent}</span>}
      </div>

      {errors.form && (
        <p className="field-error" role="alert">
          {errors.form}
        </p>
      )}

      <button type="submit" className="btn btn-primary" disabled={submitting}>
        {submitting ? "Sending…" : "Request a Quote"}
      </button>
    </form>
  );
}
