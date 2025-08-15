@echo off
REM Windows Build Script for CrawlOps Studio - Command Prompt Version
REM Handles esbuild platform binary issues and dependency fixes

echo Building CrawlOps Studio for Windows...

REM Step 1: Clean up problematic platform binaries
echo Cleaning up esbuild platform binaries...
if exist "node_modules\@esbuild\aix-ppc64" rmdir /s /q "node_modules\@esbuild\aix-ppc64" 2>nul
for /d %%i in ("node_modules\@esbuild\android-*") do rmdir /s /q "%%i" 2>nul
for /d %%i in ("node_modules\@esbuild\darwin-*") do rmdir /s /q "%%i" 2>nul
for /d %%i in ("node_modules\@esbuild\freebsd-*") do rmdir /s /q "%%i" 2>nul
for /d %%i in ("node_modules\@esbuild\linux-*") do rmdir /s /q "%%i" 2>nul
for /d %%i in ("node_modules\@esbuild\netbsd-*") do rmdir /s /q "%%i" 2>nul
for /d %%i in ("node_modules\@esbuild\openbsd-*") do rmdir /s /q "%%i" 2>nul
for /d %%i in ("node_modules\@esbuild\sunos-*") do rmdir /s /q "%%i" 2>nul

REM Step 2: Fix electron dependency placement
echo Fixing electron dependency placement...
call npm uninstall electron >nul 2>&1
call npm install --save-dev electron electron-builder

REM Step 3: Build frontend
echo Building frontend...
call npx vite build

REM Step 4: Create Windows executable  
echo Creating Windows executable...
call npx electron-builder --win --x64 --config electron-builder.config.js --publish=never

echo.
echo ✓ Build complete! Output files:
echo   Installer: dist\CrawlOps Studio Setup 1.0.0.exe
echo   Portable:  dist\win-unpacked\CrawlOps Studio.exe
pause