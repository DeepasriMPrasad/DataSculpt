@echo off
echo Building CrawlOps Studio for Windows...

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    exit /b 1
)

REM Install dependencies if needed
echo Installing dependencies...
npm install

REM Install electron-builder as dev dependency
echo Installing electron-builder...
npm install --save-dev electron-builder

REM Build the frontend
echo Building frontend with Vite...
npx vite build

REM Create Windows executable
echo Packaging Windows executable...
npx electron-builder --win --x64 --config electron-builder.config.js

echo.
echo Build complete! Check the dist/ folder for:
echo - CrawlOps Studio Setup 1.0.0.exe (installer)
echo - win-unpacked/CrawlOps Studio.exe (portable)
echo.
pause