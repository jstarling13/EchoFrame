@echo off
REM ============================================================
REM  EchoFrame -> GitHub  (Windows)
REM  Pushes your WHOLE EchoFrame folder to a NEW branch called
REM  "full-project" on github.com/jstarling13/EchoFrame.
REM  Your existing "main" branch is NOT touched.
REM
REM  HOW TO RUN: just double-click this file.
REM  REQUIREMENT: Git for Windows installed, and you are signed
REM  in to GitHub (Git Credential Manager will prompt if not).
REM ============================================================
setlocal
set "REPO=%~dp0"
set "GITDIR=%USERPROFILE%\EchoFrame-gitdir"
set "BRANCH=full-project"
set "REMOTE=https://github.com/jstarling13/EchoFrame.git"

cd /d "%REPO%" || (echo Could not find the project folder. & pause & exit /b 1)
where git >nul 2>nul || (echo Git is not installed. Get it at https://git-scm.com then re-run. & pause & exit /b 1)

echo === Cleaning up any leftover git pointers ===
if exist ".git" rmdir /s /q ".git" 2>nul
if exist ".git" del /f /q ".git" 2>nul
if exist ".git_windows_pointer.bak" del /f /q ".git_windows_pointer.bak" 2>nul
if exist "%GITDIR%" rmdir /s /q "%GITDIR%" 2>nul

echo === Writing safe .gitignore (no secrets / legal / client data) ===
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
echo .next/
echo /out/
echo /build
echo .turbo/
echo .vscode/
echo .idea/
echo *.iml
echo .DS_Store
echo .git_windows_pointer.bak
) > .gitignore

echo === Initializing git (data kept OUTSIDE OneDrive: %GITDIR%) ===
git init -b %BRANCH% --separate-git-dir "%GITDIR%"
git config user.email "jacobstarling4313@gmail.com"
git config user.name "Jacob Starling"
git remote remove origin 2>nul
git remote add origin %REMOTE%

echo === Staging files ===
git add -A

echo.
echo === REVIEW: the files below will be pushed ===
echo (You should NOT see any .env, *key*.txt, uploads/, reports/, or 05_Strategy_and_Docs/Legal/ here)
git status --short
echo.
set /p OK=Proceed and push to the "full-project" branch? (Y/N):
if /I not "%OK%"=="Y" (echo Stopped. Nothing pushed. & pause & exit /b 0)

git commit -m "Full EchoFrame project snapshot — intake pages, backend, site, docs"
git push -u origin %BRANCH%

echo.
echo ============================================================
echo  DONE. Pushed to branch: %BRANCH%
echo  View it: https://github.com/jstarling13/EchoFrame/tree/%BRANCH%
echo.
echo  On your Mac, get the project with:
echo     git clone -b %BRANCH% %REMOTE%
echo ============================================================
pause
