@echo off
REM ============================================================
REM  EchoFrame Rate Watch - reliable local launcher (PRODUCTION mode)
REM  Double-click to build + serve the 3 client sample dashboards.
REM
REM  Why production mode: this folder is OneDrive-synced. OneDrive locks
REM  files in Next.js's dev cache (.next) and breaks `next dev` within
REM  minutes. A production build + `next start` serves from a stable build
REM  and stays up. We also bypass `npm run build` because its prisma step
REM  targets the PostgreSQL schema; we generate the local SQLite client
REM  from prisma/rate-watch.prisma instead.
REM ============================================================

cd /d "%~dp0"
set DATABASE_URL=file:./dev.db

echo [1/4] Ensuring SQLite schema...
if not exist "prisma\rate-watch.prisma" (
  if exist "prisma\rate-watch.prisma.bak" copy /Y "prisma\rate-watch.prisma.bak" "prisma\rate-watch.prisma" >nul
)

echo [2/4] Generating Prisma client (SQLite)...
call npx prisma generate --schema=prisma/rate-watch.prisma

echo [3/4] Building (this takes ~1-2 min)...
REM Dummy key lets the other app's cron route compile; cleared before serving.
set RESEND_API_KEY=re_dummy_build_only
call npx next build
set RESEND_API_KEY=

echo [4/4] Starting Rate Watch at http://localhost:3000/rate-watch
echo.
echo   Sample clients:
echo     - http://localhost:3000/rate-watch/riverside-family-dental
echo     - http://localhost:3000/rate-watch/chattahoochee-coffee-roasters
echo     - http://localhost:3000/rate-watch/fountain-city-auto-repair
echo.
call npx next start -p 3000
