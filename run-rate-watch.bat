@echo off
REM ============================================================
REM  EchoFrame Rate Watch - reliable local launcher
REM  Double-click this file to start the 3 client sample demo.
REM
REM  Why this exists: this folder is shared with other tooling
REM  that keeps `prisma/schema.prisma` on PostgreSQL. This script
REM  generates the local SQLite client from `prisma/rate-watch.prisma`
REM  and starts the dev server. Do NOT use `npm run build` locally
REM  (it regenerates the Postgres client and breaks the SQLite run).
REM ============================================================

cd /d "%~dp0"
set DATABASE_URL=file:./dev.db

echo [1/3] Restoring SQLite schema (if needed)...
if not exist "prisma\rate-watch.prisma" (
  if exist "prisma\rate-watch.prisma.bak" copy /Y "prisma\rate-watch.prisma.bak" "prisma\rate-watch.prisma" >nul
)

echo [2/3] Generating Prisma client (SQLite)...
call npx prisma generate --schema=prisma/rate-watch.prisma

echo [3/3] Starting Rate Watch at http://localhost:3000/rate-watch ...
echo.
echo   Sample clients:
echo     - http://localhost:3000/rate-watch/riverside-family-dental
echo     - http://localhost:3000/rate-watch/chattahoochee-coffee-roasters
echo     - http://localhost:3000/rate-watch/fountain-city-auto-repair
echo.
call npm run dev
