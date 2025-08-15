#!/bin/bash
# Windows Build Script using Wine for Linux/macOS environments
# Enhanced script for cross-compilation with detailed logging

echo "===================================================="
echo "CRAWLOPS STUDIO - WINDOWS BUILD WITH WINE"
echo "===================================================="

# Navigate to project root
cd "$(dirname "$0")/.."

# Platform and Wine validation
echo "[INFO] Platform: $(uname -s) $(uname -m)"
echo "[INFO] Working directory: $(pwd)"

# Check if Wine is available
if ! command -v wine &> /dev/null; then
    echo "ERROR: Wine is not installed or not in PATH"
    echo "Please install Wine first:"
    echo "  Ubuntu/Debian: sudo apt install wine"
    echo "  macOS: brew install wine"
    echo "  Arch Linux: sudo pacman -S wine"
    exit 1
fi

echo "[INFO] Wine version: $(wine --version)"

# Verify required files exist
if [ ! -f "package.json" ]; then
    echo "ERROR: package.json not found. Are you in the correct directory?"
    exit 1
fi

if [ ! -f "electron-builder.config.js" ]; then
    echo "ERROR: electron-builder.config.js not found"
    echo "This file is required for Windows builds"
    exit 1
fi

echo "[INFO] Required files validated"

# Environment information
echo ""
echo "===================================================="
echo "ENVIRONMENT INFORMATION"
echo "===================================================="

echo "Node.js version:"
if ! node --version; then
    echo "ERROR: Node.js not found. Please install Node.js 18+ first"
    exit 1
fi

echo ""
echo "NPM version:"
if ! npm --version; then
    echo "ERROR: NPM not found"
    exit 1
fi

echo ""
echo "Current directory contents:"
ls -la | grep -E "\.(json|js|md)$"

# Clean previous builds with detailed output
echo ""
echo "===================================================="
echo "CLEANING PREVIOUS BUILDS"
echo "===================================================="

if [ -d "dist" ]; then
    echo "[INFO] Removing previous dist folder..."
    rm -rf dist
    echo "[SUCCESS] Previous build cleaned"
else
    echo "[INFO] No previous dist folder found"
fi

# Clean node_modules cache
if [ -d "node_modules/.cache" ]; then
    echo "[INFO] Cleaning node_modules cache..."
    rm -rf node_modules/.cache
    echo "[SUCCESS] Cache cleaned"
fi

# Clean problematic esbuild binaries
echo "[INFO] Cleaning esbuild platform binaries..."
find node_modules/@esbuild -type d -name "*" ! -name "*win32*" 2>/dev/null | while read dir; do
    if [[ "$dir" != *"win32"* ]]; then
        echo "[INFO] Removing non-Windows binary: $dir"
        rm -rf "$dir" 2>/dev/null
    fi
done

# Clean Wine cache to avoid version conflicts
echo "[INFO] Cleaning Wine cache..."
if [ -d "$HOME/.wine" ]; then
    rm -rf "$HOME/.wine/drive_c/users/$(whoami)/.cache/electron" 2>/dev/null
    echo "[SUCCESS] Wine Electron cache cleaned"
fi

# Install/reinstall dependencies with Windows focus
echo ""
echo "===================================================="
echo "INSTALLING DEPENDENCIES"
echo "===================================================="

echo "[INFO] Uninstalling existing electron packages..."
npm uninstall electron electron-builder 2>/dev/null

echo "[INFO] Installing Windows-compatible dependencies..."
if ! npm install --save-dev electron@37.3.0 electron-builder@26.0.12; then
    echo "ERROR: Failed to install electron dependencies"
    echo "Try running: npm cache clean --force"
    exit 1
fi

echo "[INFO] Installing remaining dependencies..."
if ! npm install; then
    echo "ERROR: npm install failed"
    exit 1
fi

echo "[SUCCESS] Dependencies installed"

# Verify electron installation
echo ""
echo "[INFO] Verifying Electron installation..."
if ! npx electron --version; then
    echo "ERROR: Electron verification failed"
    exit 1
fi

# Build frontend with detailed logging
echo ""
echo "===================================================="
echo "BUILDING FRONTEND"
echo "===================================================="

echo "[INFO] Building React frontend with Vite..."
if ! npx vite build --logLevel info; then
    echo "ERROR: Frontend build failed"
    echo "Check the output above for details"
    exit 1
fi

echo "[SUCCESS] Frontend build completed"

# Verify build output
if [ ! -f "dist/index.html" ]; then
    echo "ERROR: Frontend build did not produce expected files"
    echo "Expected: dist/index.html"
    exit 1
fi

echo "[INFO] Build verification successful"

# Build Windows executable with Wine
echo ""
echo "===================================================="
echo "BUILDING WINDOWS EXECUTABLE WITH WINE"
echo "===================================================="

echo "[INFO] Starting Electron Builder for Windows x64..."
echo "[INFO] Config file: electron-builder.config.js"
echo "[INFO] Target: Windows x64 (Wine cross-compilation)"
echo "[INFO] Publish: Never (local build only)"

# Set Wine environment variables for better compatibility
export WINEARCH=win64
export WINEPREFIX="$HOME/.wine-crawlops"

echo "[INFO] Wine environment: $WINEARCH, Prefix: $WINEPREFIX"

if ! npx electron-builder --win --x64 --config electron-builder.config.js --publish=never --verbose; then
    echo ""
    echo "===================================================="
    echo "BUILD FAILED - TROUBLESHOOTING INFORMATION"
    echo "===================================================="
    echo "Exit Code: $?"
    echo ""
    echo "Common Solutions:"
    echo "1. Ensure Wine is properly installed and configured"
    echo "2. Check Wine version compatibility: wine --version"
    echo "3. Clear all caches: npm cache clean --force"
    echo "4. Delete node_modules and run: npm install"
    echo "5. Update Wine: sudo apt update && sudo apt upgrade wine (Ubuntu)"
    echo ""
    echo "Wine-specific troubleshooting:"
    echo "- Configure Wine: winecfg"
    echo "- Check Wine logs: wine --debugmsg +all 2>&1 | grep -i error"
    echo "- Try different Wine version or install additional Windows components"
    echo ""
    echo "For detailed logs, check: dist/builder-effective-config.yaml"
    echo "===================================================="
    exit 1
fi

# Success output
echo ""
echo "===================================================="
echo "BUILD SUCCESSFUL!"
echo "===================================================="

echo "[SUCCESS] Windows executable created successfully using Wine!"
echo ""
echo "Output files:"
if [ -f "dist/win-unpacked/CrawlOps Studio.exe" ]; then
    echo "  ✓ Portable App: dist/win-unpacked/CrawlOps Studio.exe"
    echo "    (Can be run on Windows without installation)"
fi

if ls dist/CrawlOps\ Studio\ Setup*.exe 1> /dev/null 2>&1; then
    echo "  ✓ Installer: dist/CrawlOps Studio Setup*.exe"
    echo "    (Full installer for Windows distribution)"
fi

echo ""
echo "File sizes:"
if [ -f "dist/win-unpacked/CrawlOps Studio.exe" ]; then
    echo "  Executable: $(du -h 'dist/win-unpacked/CrawlOps Studio.exe' | cut -f1)"
fi

echo ""
echo "To test on Windows:"
echo "  1. Copy files to a Windows machine"
echo "  2. Double-click: CrawlOps Studio.exe"
echo "  3. Or run installer: CrawlOps Studio Setup*.exe"
echo ""
echo "Build completed at: $(date)"
echo "Wine environment: $WINEARCH, Prefix: $WINEPREFIX"
echo "===================================================="