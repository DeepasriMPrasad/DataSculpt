#!/bin/bash
# Windows Build Script for CrawlOps Studio - Fixed Version
# Handles esbuild platform binary issues and dependency fixes

set -e

echo "Building CrawlOps Studio for Windows..."

# Step 1: Clean up problematic platform binaries that cause ENOENT errors
echo "Cleaning up esbuild platform binaries..."
find node_modules -name "@esbuild" -type d -exec find {} -name "*aix*" -type d -exec rm -rf {} + 2>/dev/null || true
find node_modules -name "@esbuild" -type d -exec find {} -name "*android*" -type d -exec rm -rf {} + 2>/dev/null || true
find node_modules -name "@esbuild" -type d -exec find {} -name "*darwin*" -type d -exec rm -rf {} + 2>/dev/null || true
find node_modules -name "@esbuild" -type d -exec find {} -name "*freebsd*" -type d -exec rm -rf {} + 2>/dev/null || true
find node_modules -name "@esbuild" -type d -exec find {} -name "*linux*" -type d -exec rm -rf {} + 2>/dev/null || true
find node_modules -name "@esbuild" -type d -exec find {} -name "*netbsd*" -type d -exec rm -rf {} + 2>/dev/null || true
find node_modules -name "@esbuild" -type d -exec find {} -name "*openbsd*" -type d -exec rm -rf {} + 2>/dev/null || true
find node_modules -name "@esbuild" -type d -exec find {} -name "*sunos*" -type d -exec rm -rf {} + 2>/dev/null || true

# Step 2: Fix electron dependency placement and ensure clean install
echo "Fixing electron dependency placement..."
npm uninstall electron 2>/dev/null || true
npm uninstall electron-builder 2>/dev/null || true
npm install --save-dev electron@^37.3.0 electron-builder@^26.0.12
echo "Verifying electron installation..."
npx electron --version || echo "Warning: Electron verification failed"

# Step 3: Build frontend
echo "Building frontend..."
npx vite build

# Step 4: Create Windows executable
echo "Creating Windows executable..."
npx electron-builder --win --x64 --config electron-builder.config.js --publish=never

echo "✓ Build complete! Output files:"
echo "  Installer: dist/CrawlOps Studio Setup 1.0.0.exe"  
echo "  Portable:  dist/win-unpacked/CrawlOps Studio.exe"