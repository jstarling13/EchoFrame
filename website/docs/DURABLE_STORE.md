# Durable store requirement (idempotency + rate limiting)

## What it's for

Two things in this app need state that survives across serverless
instances and cold starts:

1. **Stripe webhook idempotency** (`lib/idempotency.ts`) — so a
   duplicate/retried webhook delivery is never processed twice.
2. **Contact-form rate limiting** (`lib/rate-limit.ts`) — so abuse limits
   apply across all instances, not just whichever one handled a given
   request.

An in-memory `Map`/`Set` only exists inside a single running process. On
Vercel, each serverless invocation can run in a different instance with
no shared memory, and instances are recycled/cold-started constantly — an
in-memory store there is not "eventually consistent," it's just wrong.

## The guard

`lib/durable-store.ts` gates both features on `NODE_ENV === "production"`
(not `VERCEL_ENV`) — Vercel sets `NODE_ENV=production` for **both**
Preview and Production deployments, so this intentionally covers Preview
too. Only local `next dev` (`NODE_ENV=development`) and the test runner
(`NODE_ENV=test`) are exempt.

- **Webhook idempotency fails CLOSED.** If `RATE_LIMIT_STORE_URL` /
  `RATE_LIMIT_STORE_TOKEN` are unset outside local dev/test,
  `markEventProcessedIfNew` throws `DurableStoreRequiredError`, and
  `app/api/stripe/webhook/route.ts` returns `500` so Stripe retries. If
  the store IS configured but unreachable at request time, it also fails
  closed in production (same reasoning: never risk double-processing a
  payment event). Locally, a store failure falls back to in-memory so
  development isn't blocked by an unconfigured store.
- **Contact-form rate limiting fails OPEN, but flags loudly.** A public
  lead-capture form staying available matters more than perfect abuse
  protection from one instance, so a missing/unreachable store does not
  block submissions. It does log a distinct, greppable event —
  `rate_limit_durable_store_missing_production` — every time, so this is
  never silently ignored in production.

## Required store and environment variables

Any Redis REST-compatible store implementing Upstash's REST protocol
works (`GET/SET .../pipeline` endpoints, bearer-token auth). Upstash
Redis is the reference choice because it's serverless-friendly (no
persistent connection) and has a generous free tier.

```
RATE_LIMIT_STORE_URL=https://<your-db>.upstash.io
RATE_LIMIT_STORE_TOKEN=<REST token>
```

Set both in **every** Vercel environment that will see real traffic
(Preview and Production) — see `website/docs/VERCEL_DEPLOYMENT.md` for
where. Do not reuse the same logical keyspace across environments if you
want Preview traffic to not affect Production rate-limit counters —
either use separate Upstash databases per environment, or accept shared
counters (lower risk, since both events and rate-limit keys are already
namespaced by `stripe-event:`/`contact-form:` prefixes and won't collide
with anything else).

## What this does NOT cover

This guard only concerns *this app's* in-process state. It has nothing to
do with Stripe's own retry behavior, database persistence (this app has
no database), or CRM/email delivery reliability (see
`website/docs/O5_INITIAL_TERM.md` and the lead-routing failure handling
in `app/api/contact/route.ts` for those).
