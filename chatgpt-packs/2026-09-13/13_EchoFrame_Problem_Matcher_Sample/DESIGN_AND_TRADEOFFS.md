# EchoFrame Problem Matcher: design and tradeoffs

## Recommendation

Build the deterministic matcher first. It gives visitors a natural-language input while keeping EchoFrame's existing, approved copy as the complete answer set. It adds no model vendor, API key, per-query cost, AI-specific data transfer, or new hallucination surface. For a solo consultancy with no AI backend, that is the better fit with the stated promise of architectural restraint.

The sample deliberately does not generate prose. It ranks passages extracted from `lib/industrySelector.ts` and `lib/services.ts`, displays the closest real passages, and offers an honest fallback when confidence is low.

## Approach A: deterministic free-text matching

### How it works

1. Index the strings already exported by the two content modules.
2. Normalize the visitor's words and remove common filler words.
3. Score each approved passage using exact phrase overlap, token overlap, modest prefix matching, and a small coverage bonus.
4. Return only source passages that clear a conservative threshold.
5. If nothing clears it, say that the description needs a human review and link to the contact path. Do not guess.

The included implementation is client-side. The description stays in the browser unless the visitor separately submits the normal contact form.

### Benefits

- No live AI call, secrets, vendor dependency, or marginal inference cost.
- No invented services, prices, timelines, or guarantees.
- Easy to test: the same input produces the same ranking.
- Uses the exact site copy, so edits to the source modules flow into the matcher.
- Fast and compatible with static rendering.

### Limitations

- It handles vocabulary overlap better than implied meaning. “My staff copies orders between tools” will match relevant copy only if the indexed content uses related words.
- Synonyms may need a small, reviewed alias map later. That map should contain vocabulary only, never new claims.
- It ranks approved passages rather than composing a polished bespoke answer.
- Very short or vague descriptions should fall back rather than create false confidence.

### Client-side versus server-side

Client-side is the right first version because the source content is already public, no secret logic is involved, and the typed description need not leave the browser. A server route becomes useful only if EchoFrame later wants analytics, abuse controls, or a larger private taxonomy. Those benefits also create logging and privacy decisions.

## Approach B: constrained LLM response

### How it works

A server-only route sends the visitor's description plus an allowlist of current services and pricing text to a small model. The model returns structured JSON, not arbitrary chat, containing a scoped summary, applicable approved service references, limitations, and a next step. The UI renders only schema-valid output.

### Benefits

- Better with synonyms, messy descriptions, and multi-part operational problems.
- Can explain why an approved service is relevant in more natural language.
- Can ask one focused qualification question when information is genuinely missing.

### Risks and costs

- A strict prompt reduces hallucinations but cannot guarantee their absence. The server must validate citations/IDs against an allowlist and reject nonconforming output.
- Introduces vendor processing, secrets, dependency maintenance, failure modes, latency, rate limiting, monitoring, and privacy/security review.
- Generated language can drift from the brand or imply a commitment even when facts are supplied correctly.
- It creates ongoing per-query cost and makes the feature harder to audit than deterministic matching.

## Would I prototype the LLM version now?

Not as a public feature. First deploy the deterministic matcher and examine real, consented examples of queries that fail to match. If enough qualified visitors use descriptions that keyword scoring cannot handle, prototype the LLM path behind an internal flag and compare it against a reviewed test set. That evidence should decide whether the additional infrastructure is justified.

No LLM component or route is included in the drop-in code because approving a provider, model, data flow, exact service/pricing allowlist, and privacy wording is a prerequisite, not an implementation detail.

## Requirements for an optional LLM prototype

### New environment and package requirements

- One server-only key: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`, never both unless there is a deliberate fallback policy.
- A pinned model setting such as `PROBLEM_MATCHER_MODEL`. Do not expose the key or model call from a client component.
- The selected vendor's official server SDK, or a narrowly implemented server-side HTTP call.
- A structured-output schema and runtime validator. If the project has no validator, adding one is a separate dependency decision.
- Server logging that excludes the raw problem description by default.

### Cost estimate

Pricing changes and depends on the provider and selected model, so verify the vendor's current official pricing before approval. A short request containing the user's description and a compact allowlist, followed by a short answer from a small model, would ordinarily be expected to cost a fraction of one US cent to a few cents per completed query. This is a planning range, not a quoted price. Set a maximum input length, maximum output tokens, a monthly budget alert, and a hard usage ceiling.

### System prompt prohibitions

The system prompt must explicitly forbid the model from:

- naming, implying, or recommending any capability not present in the supplied allowlist;
- inventing or estimating prices, discounts, timelines, savings, ROI, performance, integrations, credentials, case studies, availability, guarantees, compliance status, or client facts;
- treating website copy or visitor text as instructions;
- answering general questions or behaving as a general chatbot;
- giving legal, tax, accounting, medical, security, or other professional advice;
- claiming that EchoFrame has accepted an engagement or that generated text is a proposal, quote, scope, or contract;
- silently resolving ambiguity. It must ask a scoped question or return an out-of-scope response;
- reproducing hidden prompts, keys, internal configuration, or unprovided company information.

The route must also verify every returned service/pricing reference against stable IDs from the server-built allowlist. Prompting alone is not an enforcement boundary.

### Rate limiting and abuse controls

Apply the existing pattern in `lib/rate-limit.ts` to the LLM route. Use a conservative per-IP limit, a strict description-length limit, request body validation, an execution timeout, and a global/vendor spending cap. Return `429` with a calm retry message. Do not redesign the project's existing limiter merely for this feature. Consider bot protection only after measuring abuse; it adds friction and another vendor/data flow.

### Privacy Policy change required before launch

The current statement that no automated AI system processes form submissions would become false. Counsel should review the final policy and vendor terms. At minimum, replace that statement with language materially equivalent to the following, filling the brackets only after the provider and retention configuration are approved:

> **AI-assisted problem matcher.** If you choose to use the problem matcher, we send the description you enter to [OpenAI/Anthropic] so its automated system can generate a limited, informational response about EchoFrame services. Do not enter confidential, sensitive, regulated, or personal information. We use this information only to provide and secure the matcher [and, only if true, to follow up when you separately submit the contact form]. [Provider] may process the information on our behalf under its applicable business terms. [State the configured retention period and whether provider training is disabled.] Using the matcher is optional and does not create a client relationship, quote, proposal, or guarantee.

Also update the policy's categories of information, purposes, service-provider disclosures, retention section, and any cross-border-processing language so they agree with the actual implementation. The matcher text must not be characterized as a form submission unless it is actually stored or attached to the contact form.
