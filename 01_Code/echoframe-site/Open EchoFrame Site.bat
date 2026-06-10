@echo off
REM ============================================================
REM  Open EchoFrame Site locally
REM
REM  The site uses absolute links (e.g. /intelligence/index.html)
REM  which ONLY work when the folder is served by a web server.
REM  Opening index.html directly as a file breaks every nav link
REM  (the browser looks for C:\intelligence\... and fails).
REM
REM  This launcher starts a local web server in THIS folder and
REM  opens it in Chrome at http://localhost:3000  --  nav works.
REM
REM  Just double-click this file. Leave the small server window
REM  open while you browse; close it when you're done.
REM ============================================================

cd /d "%~dp0"

echo Starting EchoFrame local server on http://localhost:3000 ...

REM Start the Python static server (serves THIS folder) in its own window.
start "EchoFrame Server (leave open)" cmd /k python -m http.server 3000 --directory "%~dp0"

REM Give the server a moment to come up, then open Chrome.
timeout /t 2 /nobreak >nul

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://localhost:3000/index.html"

exit
