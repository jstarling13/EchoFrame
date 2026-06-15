# EchoFrame Portfolio — Real-Code Audit (corrected source of truth)

**Audited:** 2026-06-02 · **By:** Claude (Opus 4.8)
**Why this exists:** The overnight brief said only Clarity Report had code and the other 12 were
"marketing concepts with no code." That was **wrong** — the user then pointed me at
`C:\Users\jacob\OneDrive\Businesses\`, which contains **8 real, separately-built apps** (their own
GitHub repos) implementing most of these products in **TypeScript/Next.js**, not Python. This doc
is the corrected, consolidated status. The Python MVPs I built overnight in `01_Code/*` are
**superseded prototypes** (see bottom).

> Assessment is **static** (code/docs/build artifacts/git), not a live build+test run. A live
> verification per app needs `npm install` + real keys/DB (see "To verify live" per row).

---

## Consolidated status

| Product (page) | Folder / GitHub | Stack | Build state | Tests | Maturity |
|---|---|---|---|---|---|
| **Clarity Report** (flagship) | `EchoFrame/01_Code/echoframe-backend` | Python/FastAPI | runs (demo) | **83 ✅** | **Production-ready** (rescued this run) |
| **Rate Watch** = Oryn | `Oryn` · `jstarling13/oryn` | Next.js 16 + Prisma + Clerk + Stripe + Claude(web search) | **built** (`.next`) | ❌ none | Feature-complete app; needs test coverage + live verify |
| **Shift Lens** = Strata | `Strata` · `jstarling13/Strata` | Next.js + Prisma + Clerk + Stripe + Square/Toast | **built** (`.next`) | ❌ none | Feature-complete (attribution + agents + seed data); recent TS-error fix commit |
| **Bay Coach + Permit Watch** = BaySignal | `BaySignal` · `jstarling13/baysignal-backend` | Node/Express + TS + Prisma + Twilio + Stripe + Claude Vision | not built (deps installed) | **jest, 5 files ✅** | Two products in one backend; **only repo with tests**; `Initial commit` (early) |
| **Rival Scan** = Veris | `Veris` · `jstarling13/veris` | Next.js + Prisma + Clerk + Stripe + Google Places + Claude + Twilio | **built** (`.next`) | ❌ none | Feature-complete (collect + brief agents, React Email); already hardened secrets |
| **Call Catch / Call Router** = LeadCatcher | `LeadCatcher/leadcatcher-backend` · `jstarling13/leadcatcher-backend` | Node + TS + Prisma + Twilio voice + Claude | **compiled** (`dist`) | ❌ none | Working voice→SMS relay flow; most recent fixes (dotenv, keep-alive, relay) |
| **Auto Ledger** = Vericount | `Vericount` · `jstarling13/vericount` | Turbo monorepo + Next.js dashboard | not built | ❌ none | Monorepo w/ dashboard + 4 services; env-validation added; biggest/most complex |
| **Drive Pay** = HydroPay | `HydroPay` · `jstarling13/hydropay` | Next.js + Twilio + Stripe (no DB; Stripe metadata as state) | **built** (`.next`) | ❌ none | Small, elegant, well-documented; **⚠ committed secret (below)**; `Initial commit` |
| **FDS** (Financial Document Studio — parent biz tooling) | `FDS` · `jstarling13/fds-backend` | Node (scraper, pipeline, outreach) | deps not installed | ❌ none | Sales/outreach tooling, not one of the 12 products |

All 8 are pushed to GitHub under **jstarling13** and were last touched **2026-05-31 → 06-01**.

---

## Cross-cutting findings

### 🔴 Security — needs your attention
1. **HydroPay commits `API Keys.txt` to git** (`jstarling13/hydropay`, in the initial commit). If
   that repo is **public**, those keys are exposed publicly; either way they're in git history.
   - **Action:** confirm repo visibility, **rotate every key in that file**, `git rm --cached
     "API Keys.txt"`, add it to `.gitignore`, and scrub history (e.g. `git filter-repo`) if the
     repo is or ever was public. **Veris already did exactly this** (commit *"protect API Keys.txt
     from git tracking"*) — use it as the template.
2. **Your home directory `C:\Users\jacob` is itself a git repository.** `LeadCatcher/` (the parent
   of `leadcatcher-backend`) resolves to that home repo. A home-dir git repo makes it dangerously
   easy to `git add` and commit secrets/keys/SSH material from anywhere under your profile.
   - **Action:** confirm whether that repo has a remote and what it tracks; consider removing it
     (`C:\Users\jacob\.git`) if it was created by accident.
3. `.env` / `.env.local` / `API Keys.txt` in the **other** folders are **not** git-tracked (good).
   Tracked `.env.example` files are fine — those are intended placeholder templates.

### 🟡 Testing gap
- **Only BaySignal has automated tests** (jest, 5 files). The six Next.js/Node apps (Oryn, Strata,
  Veris, LeadCatcher, Vericount, HydroPay) have **no test framework or tests**. For products that
  move money (Stripe) and send messages (Twilio), the webhook/parse/idempotency paths are the
  highest-value place to add tests — exactly the pattern proven out in the flagship's suite.

### 🟢 Good signals
- Consistent, sensible architecture across the Next.js apps (Clerk auth, Prisma, Stripe billing,
  cron-secured agent endpoints, Resend email). Oryn/Strata/Veris each ship a README + deploy plan +
  week-1 GTM. HydroPay's guide is genuinely strong (signature verification, raw-body handling,
  return-200-on-SMS-failure, restricted-key guidance).

---

## To verify each app live (per-app, when you want it)
Generic recipe (none of this was run in this audit):
```
cd <folder> ; npm install
cp .env.example .env(.local) ; # fill real/test keys
npm run db:push   # or prisma migrate, where a DB is used
npm run build     # confirm it compiles
npm run dev       # smoke test
```
- **BaySignal:** `npm test` should pass today (has jest) — quickest live signal in the portfolio.
- **Oryn/Strata/Veris/HydroPay:** already have `.next` build output, so they've built before;
  re-run `npm run build` + the app's agent test script (`agent:test`, `cron:*`, etc.).
- **Vericount:** monorepo — `npm run build` / `type-check` at root via turbo.

---

## What about the overnight Python MVPs in `01_Code/*`?
`rate-watch`, `shift-lens`, `permit-watch`, `bay-coach`, `quote-revive`, `clear-ledger`,
`call-catch`, `crew-hire` were built against the (incorrect) premise that no code existed. They are
**superseded** by the real TS apps above and should be treated as **throwaway reference
prototypes**, not shipping code. They remain self-contained and green (186 tests) on the
`overnight/products-2026-06-02` branch; recommend **leaving them on that branch only** (do not merge
to main). The one piece of overnight work that is *not* superseded and *should* be kept is the
**flagship rescue** (the truncated `engine.py` fix + tests + SETUP/demo).

## Recommended next steps (your call)
1. **Now:** remediate HydroPay's committed keys (rotate + scrub) and decide on the home-dir git repo.
2. **High-leverage:** add a small test suite to whichever 1–2 apps are closest to paying users
   (Stripe webhook signature + Twilio parse + idempotency), mirroring the flagship's tests.
3. **Pick the lead product** to push to first revenue (Oryn/Strata/Veris each have a week-1 GTM) and
   live-verify just that one end-to-end.
