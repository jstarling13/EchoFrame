@echo off
REM ============================================================
REM  EchoFrame  ->  GitHub commit helper
REM
REM  WHY THIS SCRIPT: Git cannot live inside a OneDrive-synced
REM  folder -- OneDrive constantly rewrites git's internal files
REM  and corrupts the repo. This script keeps git's data OUTSIDE
REM  OneDrive (in your user folder) while your actual project files
REM  stay right here. Just double-click this file to run it.
REM
REM  REQUIREMENT: Git for Windows must be installed (git-scm.com).
REM ============================================================
setlocal
set "REPO=%USERPROFILE%\OneDrive\Businesses\EchoFrame"
set "GITDIR=%USERPROFILE%\EchoFrame-gitdir"

cd /d "%REPO%" || (echo Could not find the EchoFrame folder. & pause & exit /b 1)

where git >nul 2>nul || (echo Git is not installed. Install it from https://git-scm.com then re-run. & pause & exit /b 1)

echo.
echo === 1/5  Writing .gitignore so NO secrets/client-data/personal docs get committed ===
(
echo .env
echo *.env
echo .env.*
echo *.env.txt
echo *key*.txt
echo *API*.txt
echo *.pem
echo *.key
echo **/uploads/
echo **/reports/
echo **/data/
echo *.sqlite3
echo *.db
echo *.bin
echo 02_Marketing/client_tracker.xlsx
echo 05_Strategy_and_Docs/Legal/
echo __pycache__/
echo *.pyc
echo node_modules/
echo .DS_Store
) > .gitignore

echo === 2/5  Initializing git with its data OUTSIDE OneDrive (%GITDIR%) ===
git init -b main --separate-git-dir "%GITDIR%"
git config user.email "jacobstarling4313@gmail.com"
git config user.name "Jacob Starling"

echo === 3/5  Staging files ===
git add -A

echo.
echo === 4/5  REVIEW: these files will be committed ===
echo (You should NOT see any .env, *key*.txt, uploads/, reports/, or 05_Strategy_and_Docs/Legal/ here)
git status --short
echo.
echo If anything sensitive appears above, type N to stop.
set /p OK=Proceed with the commit? (Y/N):
if /I not "%OK%"=="Y" (echo Stopped. Nothing committed. & pause & exit /b 0)

echo === 5/5  Committing ===
git commit -m "EchoFrame: legal/compliance pass (site, backend, marketing, docs)"
git remote add origin https://github.com/jstarling13/EchoFrame.git 2>nul

echo.
echo ============================================================
echo  Committed locally. To upload to GitHub, run this next:
echo.
echo      git push -u origin main
echo.
echo  If GitHub rejects it because the repo already has different
echo  history, you can either create a NEW empty GitHub repo and
echo  point to it, or OVERWRITE the old one with:
echo      git push -u origin main --force
echo.
echo  NOTE: Your personal legal docs (05_Strategy_and_Docs\Legal)
echo  are intentionally NOT uploaded -- they contain your home
echo  address, spouse's name, and the POA. Keep them local. Only
echo  add them to GitHub if your repo is PRIVATE.
echo ============================================================
pause
