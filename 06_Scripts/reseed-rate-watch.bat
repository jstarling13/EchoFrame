@echo off
REM Rebuild the SQLite demo database and reseed the 3 sample clients.
cd /d "%~dp0"
set DATABASE_URL=file:./dev.db

if not exist "prisma\rate-watch.prisma" (
  if exist "prisma\rate-watch.prisma.bak" copy /Y "prisma\rate-watch.prisma.bak" "prisma\rate-watch.prisma" >nul
)

echo Generating client + resetting database...
call npx prisma generate --schema=prisma/rate-watch.prisma
call npx prisma db push --schema=prisma/rate-watch.prisma --skip-generate --force-reset --accept-data-loss

echo Seeding 3 sample clients...
call npx tsx prisma/seed.ts

echo.
echo Done. Start the app with run-rate-watch.bat
pause
