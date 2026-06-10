#!/bin/bash
# ============================================================
#  EchoFrame -> GitHub  (Mac / Linux)
#  Pushes your WHOLE EchoFrame folder to a NEW branch called
#  "full-project" on github.com/jstarling13/EchoFrame.
#  Your existing "main" branch is NOT touched.
#
#  HOW TO RUN (Mac): right-click this file -> Open  (or in
#  Terminal:  bash PUSH_TO_GITHUB.command )
#  You must already be signed in to GitHub in git (or have the
#  GitHub CLI `gh` logged in) on this computer.
# ============================================================
set -e

# 1) Work from the folder this script lives in
REPO="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO"
echo "Project folder: $REPO"

# 2) Keep git's data OUTSIDE the synced folder (prevents OneDrive/iCloud corruption)
GITDIR="$HOME/EchoFrame-gitdir"
BRANCH="full-project"
REMOTE="https://github.com/jstarling13/EchoFrame.git"

# 3) Clean up any leftover/broken git pointers from earlier attempts
rm -rf .git .git_windows_pointer.bak 2>/dev/null || true
rm -rf "$GITDIR" 2>/dev/null || true

# 4) Write a safe .gitignore (NO secrets, client data, or personal/legal docs)
cat > .gitignore <<'IGN'
# secrets / keys
.env
*.env
.env.*
*.env.txt
*key*.txt
*API*.txt
*.pem
*.key
# customer data & generated output
**/uploads/
**/reports/
**/data/
*.sqlite3
*.db
*.bin
# personal / legal / client (NEVER on a public repo)
02_Marketing/client_tracker.xlsx
05_Strategy_and_Docs/Legal/
# build & deps
__pycache__/
*.pyc
node_modules/
.next/
/out/
/build
.turbo/
# editor / os
.vscode/
.idea/
*.iml
.DS_Store
.git_windows_pointer.bak
IGN

# 5) Initialize git (data lives in $GITDIR, your files stay put)
git init -b "$BRANCH" --separate-git-dir "$GITDIR"
git config user.email "jacobstarling4313@gmail.com"
git config user.name  "Jacob Starling"
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE"

# 6) Stage everything (gitignore decides what is excluded)
git add -A

# 7) SAFETY: abort if anything sensitive slipped into the staging list
LEAK="$(git diff --cached --name-only | grep -Ei '(^|/)\.env|secret|/Legal/|client_tracker|\.pem$|\.key$|API.*\.txt$' || true)"
if [ -n "$LEAK" ]; then
  echo ""
  echo "!!! STOPPING — these look sensitive and should NOT go to a public repo:"
  echo "$LEAK"
  echo "Nothing was pushed. Tell Claude and we'll fix the ignore list."
  exit 1
fi

echo ""
echo "=== Files that WILL be pushed (review quickly) ==="
git diff --cached --name-only | head -50
echo "...(showing first 50)"
echo ""

# 8) Commit and push the new branch
git commit -m "Full EchoFrame project snapshot — intake pages, backend, site, docs"
git push -u origin "$BRANCH"

echo ""
echo "============================================================"
echo " DONE. Pushed to branch:  $BRANCH"
echo " View it:  https://github.com/jstarling13/EchoFrame/tree/$BRANCH"
echo ""
echo " On your Mac, get the project with:"
echo "   git clone -b $BRANCH $REMOTE"
echo "============================================================"
