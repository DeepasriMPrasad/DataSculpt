@echo off
REM Windows Local Build Script for CrawlOps Studio
REM This script is specifically designed for Windows local development environments
REM Includes detailed logging and Windows-specific fixes

echo ====================================================
echo CRAWLOPS STUDIO - WINDOWS LOCAL BUILD
echo ====================================================

REM Navigate to project root
cd /d "%~dp0\.."

REM Platform validation - ensure this is Windows
if not "%OS%"=="Windows_NT" (
    echo ERROR: This script requires Windows OS
    echo Current OS detected: %OS%
    echo Please use appropriate scripts for your platform
    pause
    exit /b 1
)

echo [INFO] Platform validated: Windows %PROCESSOR_ARCHITECTURE%
echo [INFO] Working directory: %CD%

REM Display environment information
echo.
echo ====================================================
echo ENVIRONMENT INFORMATION
echo ====================================================
echo Node.js version:
node --version || (
    echo ERROR: Node.js not found. Please install Node.js 18+ first
    pause
    exit /b 1
)

echo.
echo NPM version:
npm --version || (
    echo ERROR: NPM not found
    pause
    exit /b 1
)

echo.
echo Current directory contents:
dir /b | findstr /E ".json .js .md"

REM Verify required files exist
if not exist "package.json" (
    echo ERROR: package.json not found. Are you in the correct directory?
    pause
    exit /b 1
)

if not exist "electron-builder.config.js" (
    echo ERROR: electron-builder.config.js not found
    echo This file is required for Windows builds
    pause
    exit /b 1
)

echo [INFO] Required files validated

REM Clean previous builds with detailed output
echo.
echo ====================================================
echo CLEANING PREVIOUS BUILDS
echo ====================================================

if exist "dist" (
    echo [INFO] Removing previous dist folder...
    rmdir /s /q "dist"
    if %ERRORLEVEL% equ 0 (
        echo [SUCCESS] Previous build cleaned
    ) else (
        echo [WARNING] Could not clean previous build - continuing anyway
    )
) else (
    echo [INFO] No previous dist folder found
)

REM Clean node_modules cache
if exist "node_modules\.cache" (
    echo [INFO] Cleaning node_modules cache...
    rmdir /s /q "node_modules\.cache"
    echo [SUCCESS] Cache cleaned
)

REM Clean problematic esbuild binaries that cause Windows build issues
echo [INFO] Cleaning esbuild platform binaries...
for /d %%i in ("node_modules\@esbuild\*") do (
    echo [DEBUG] Found esbuild binary: %%i
    if /i "%%~ni" neq "@esbuild\win32-x64" (
        if /i "%%~ni" neq "@esbuild\win32-ia32" (
            echo [INFO] Removing non-Windows binary: %%i
            rmdir /s /q "%%i" 2>nul
        )
    )
)

REM Force clean electron cache to avoid version conflicts
echo [INFO] Cleaning Electron cache...
if exist "%USERPROFILE%\.cache\electron" (
    rmdir /s /q "%USERPROFILE%\.cache\electron" 2>nul
    echo [SUCCESS] Electron cache cleaned
)

REM Install/reinstall dependencies with Windows focus
echo.
echo ====================================================
echo INSTALLING DEPENDENCIES
echo ====================================================

echo [INFO] Uninstalling existing electron packages...
call npm uninstall electron electron-builder 2>nul

echo [INFO] Installing Windows-compatible dependencies...
call npm install --save-dev electron@37.3.0 electron-builder@26.0.12 --verbose
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install electron dependencies
    echo Try running: npm cache clean --force
    pause
    exit /b %ERRORLEVEL%
)

echo [INFO] Installing remaining dependencies...
call npm install --verbose
if %ERRORLEVEL% neq 0 (
    echo ERROR: npm install failed
    pause
    exit /b %ERRORLEVEL%
)

echo [SUCCESS] Dependencies installed

REM Verify electron installation
echo.
echo [INFO] Verifying Electron installation...
call npx electron --version
if %ERRORLEVEL% neq 0 (
    echo ERROR: Electron verification failed
    pause
    exit /b %ERRORLEVEL%
)

REM Build frontend with detailed logging
echo.
echo ====================================================
echo BUILDING FRONTEND
echo ====================================================

echo [INFO] Building React frontend with Vite...
call npx vite build --logLevel info
if %ERRORLEVEL% neq 0 (
    echo ERROR: Frontend build failed
    echo Check the output above for details
    pause
    exit /b %ERRORLEVEL%
)

echo [SUCCESS] Frontend build completed

REM Verify build output
if not exist "dist\index.html" (
    echo ERROR: Frontend build did not produce expected files
    echo Expected: dist\index.html
    pause
    exit /b 1
)

echo [INFO] Build verification successful

REM Build Windows executable with maximum verbosity
echo.
echo ====================================================
echo BUILDING WINDOWS EXECUTABLE
echo ====================================================

echo [INFO] Starting Electron Builder for Windows x64...
echo [INFO] Config file: electron-builder.config.js
echo [INFO] Target: Windows x64 (current platform)
echo [INFO] Publish: Never (local build only)

call npx electron-builder --win --x64 --config electron-builder.config.js --publish=never --verbose
if %ERRORLEVEL% neq 0 (
    echo.
    echo ====================================================
    echo BUILD FAILED - TROUBLESHOOTING INFORMATION
    echo ====================================================
    echo Exit Code: %ERRORLEVEL%
    echo.
    echo Common Solutions:
    echo 1. Ensure you're running on Windows (required for native builds)
    echo 2. Check Windows Defender / Antivirus isn't blocking the build
    echo 3. Run Command Prompt as Administrator
    echo 4. Clear all caches: npm cache clean --force
    echo 5. Delete node_modules and run: npm install
    echo.
    echo For detailed logs, check: dist\builder-effective-config.yaml
    echo ====================================================
    pause
    exit /b %ERRORLEVEL%
)

REM Success output
echo.
echo ====================================================
echo BUILD SUCCESSFUL!
echo ====================================================

echo [SUCCESS] Windows executable created successfully!
echo.
echo Output files:
if exist "dist\win-unpacked\CrawlOps Studio.exe" (
    echo   ✓ Portable App: dist\win-unpacked\CrawlOps Studio.exe
    echo     ^(Can be run directly without installation^)
)

if exist "dist\CrawlOps Studio Setup*.exe" (
    echo   ✓ Installer: dist\CrawlOps Studio Setup*.exe
    echo     ^(Full installer for distribution^)
)

echo.
echo File sizes:
if exist "dist\win-unpacked\CrawlOps Studio.exe" (
    for %%i in ("dist\win-unpacked\CrawlOps Studio.exe") do echo   Executable: %%~zi bytes
)

echo.
echo To run the application:
echo   Double-click: dist\win-unpacked\CrawlOps Studio.exe
echo.
echo Build completed at: %DATE% %TIME%
echo ====================================================

pause