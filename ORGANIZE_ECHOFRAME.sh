#!/bin/bash
# =============================================================================
# EchoFrame — safe folder organizer
# -----------------------------------------------------------------------------
# WHAT IT DOES
#   1. Tags a full backup of your current state (nothing is ever deleted).
#   2. Builds ONE branch ("organized") that contains EVERY file from all your
#      branches, so files stop appearing/disappearing.
#   3. Keeps your LIVE backend (01_Code/echoframe-backend) exactly as deployed.
#   4. Moves the loose docs / CSVs / scripts at the top level into clean folders
#      (uses `git mv` only — never `rm`, never deletes).
#   5. Writes 00_START_HERE.md — a one-page map anyone can read.
#   6. Does NOT push and does NOT change deployments. Review it, then we make it
#      official together.
#
# HOW TO RUN  (use the normal macOS Terminal, NOT PowerShell):
#   bash "$HOME/Library/Mobile Documents/com~apple~CloudDocs/EchoFrame/ORGANIZE_ECHOFRAME.sh"
#
# TO UNDO EVERYTHING later:  git checkout <the backup tag this script prints>
# =============================================================================
set -euo pipefail

ROOT="$HOME/Library/Mobile Documents/com~apple~CloudDocs/EchoFrame"
cd "$ROOT" 2>/dev/null || { echo "ERROR: can't find EchoFrame folder at $ROOT"; exit 1; }
[ -d .git ] || { echo "ERROR: this folder isn't a git repo."; exit 1; }

# --- Guard: refuse to run with uncommitted edits to tracked files -----------
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "You have uncommitted changes to tracked files."
  echo "Tell Claude before running this so nothing gets disturbed. Aborting."
  exit 1
fi

STAMP=$(date +%Y%m%d-%H%M%S)
echo "==> [1/4] Backing up current state (tags — fully reversible, nothing deleted)"
git fetch origin --quiet || true
git tag "backup-before-organize-$STAMP" 2>/dev/null || true
git tag "backup-main-$STAMP" origin/main 2>/dev/null || true
git tag "backup-reorg-$STAMP" report-products-reorg 2>/dev/null || true
echo "    Backup tag: backup-before-organize-$STAMP"

echo "==> [2/4] Building ONE branch with EVERYTHING (live backend preserved)"
git checkout -B organized origin/main
# bring in every file from the full work branch...
git checkout report-products-reorg -- . 2>/dev/null || true
# ...but keep the live, deployed backend (includes the email failsafe)
git checkout origin/main -- 01_Code/echoframe-backend 2>/dev/null || true
git add -A
git commit -m "Consolidate all EchoFrame work into one branch (nothing deleted)" --quiet \
  || echo "    (already unified — nothing to consolidate)"

echo "==> [3/4] Tidying loose top-level files into folders (move only, never delete)"
mkdir -p 05_Strategy_and_Docs 06_Scripts 04_Sample_Reports/source_data

move() {  # move SRC DESTDIR — skips silently if the file isn't there
  if [ -e "$1" ]; then
    git mv -k "$1" "$2"/ 2>/dev/null && echo "    moved: $1  ->  $2/" || true
  fi
}

# Loose documentation -> 05_Strategy_and_Docs
for f in BUILD_SUMMARY.md CLAUDE_CODE_PROMPT_recurring-reports.md HANDOFF_INTAKE_PAGES.md \
         RATE_WATCH_SAMPLES.md README_RATE_WATCH.md RIVAL_SCAN_CHANGES.md RIVAL_SCAN_SETUP.md \
         SETUP_INSTRUCTIONS.md Sample_Generation_Prompts.md; do
  move "$f" 05_Strategy_and_Docs
done

# Marketing docs -> 02_Marketing
move EchoFrame_marketing_plan.md 02_Marketing
move EchoFrame_30Day_Launch_Plan.md 02_Marketing

# Loose source-data CSVs -> 04_Sample_Reports/source_data
for f in Sample_AutoLedger_PLAIN_May2026.csv Sample_AutoLedger_Transactions_May2026.csv \
         Sample_CompetitorLandscape_May2026.csv Sample_DrivePay_RepairOrders_May2026.csv \
         Sample_Restaurant_Detailed_PnL.csv Sample_Restaurant_PnL_clean.csv; do
  move "$f" 04_Sample_Reports/source_data
done

# Loose helper scripts -> 06_Scripts
for f in COMMIT_TO_GITHUB.bat PUSH_TO_GITHUB.bat PUSH_TO_GITHUB.command \
         reseed-rate-watch.bat run-rate-watch.bat \
         clone-live-to-test.js list-sessions.js test-purchases.js; do
  move "$f" 06_Scripts
done

echo "==> [4/4] Writing 00_START_HERE.md (the map)"
cat > 00_START_HERE.md <<'MAP'
# EchoFrame — Start Here

**EchoFrame** delivers a plain-English monthly financial report that tells Columbus, GA
small-business owners exactly where their money is leaking and the one thing to fix this
month — CFO-grade analysis in owner-grade language, for $150/month.

Founder: **Jacob Starling**, M.S. Finance, Emory University · Columbus, GA.

---

## Live & in production
- **Website:** https://echoframe.net  (free-sample funnel + checkout)
- **Backend / report engine:** `01_Code/echoframe-backend/` — deployed on Railway
- **Payments:** Stripe (live) · **Email:** Resend
- **Offer:** Monthly Clarity Report $150/mo · Business Review $499 · Competitor Report $299

## Folder guide
| Folder | What's inside |
|---|---|
| `01_Code/echoframe-backend/` | The live product — FastAPI app + all 16 report engines. **Deployed (Railway).** |
| `01_Code/` (other) | Website copies and per-product prototypes/experiments. |
| `02_Marketing/` | Marketing plan, 30-day launch plan, campaign material. |
| `03_Brand_Assets/` | Logo, brand kit, design assets. |
| `04_Sample_Reports/` | Example reports + their source data (`source_data/`). |
| `05_Strategy_and_Docs/` | Strategy notes, setup/handoff docs, build summaries. |
| `06_Scripts/` | Helper + dev scripts (deploy helpers, test utilities). |

## The products (report engines)
Auto Ledger · Clear Ledger · Business Audit · Clarity (Monthly) · Competitor Landscape ·
Rival Scan · Revenue Suite · Quote Revive · Rate Watch · Drive Pay · Crew Hire ·
Bay Coach · Shift Lens · Permit Watch · Call Catch · Call Router.

## Notes
- This repo also feeds the website. The website folders are left in place on purpose;
  the live deploy source is being confirmed before any of them are rearranged.
- Backups: every reorganization tags a `backup-before-organize-*` point you can restore.

*Map generated by the organize script. Safe to edit by hand.*
MAP

git add -A
git commit -m "Organize top level + add START_HERE map (nothing deleted)" --quiet || true

echo
echo "============================================================================"
echo "DONE — you're now on the 'organized' branch with EVERYTHING present & tidy."
echo "Nothing was deleted. Deployments were not touched. Nothing was pushed."
echo
echo "  • Open the folder in Finder and look around — start with 00_START_HERE.md"
echo "  • Love it? Tell Claude and we'll make it official + archive the old site copies."
echo "  • Want to undo it all?   git checkout backup-before-organize-$STAMP"
echo "============================================================================"
