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



# Step 2: Fix electron dependency placement
echo "Fixing electron dependency placement..."
npm uninstall electron 2>/dev/null || true
npm install --save-dev electron electron-builder

# Step 3: Build frontend
echo "Building frontend..."
npx vite build

# Ensure problematic esbuild directories exist right before packaging
mkdir -p node_modules/@esbuild/aix-ppc64
mkdir -p node_modules/@esbuild/android-arm64
mkdir -p node_modules/@esbuild/darwin-arm64
mkdir -p node_modules/@esbuild/freebsd-x64
mkdir -p node_modules/@esbuild/linux-x64
mkdir -p node_modules/@esbuild/netbsd-x64
mkdir -p node_modules/@esbuild/openbsd-x64
mkdir -p node_modules/@esbuild/sunos-x64
mkdir -p node_modules/@esbuild/windows-arm64
mkdir -p node_modules/@esbuild/windows-ia32
mkdir -p node_modules/@esbuild/windows-arm
mkdir -p node_modules/@esbuild/windows-ppc64
mkdir -p node_modules/@esbuild/windows-ppc64le
mkdir -p node_modules/@esbuild/windows-s390x
mkdir -p node_modules/@esbuild/windows-riscv64
mkdir -p node_modules/@esbuild/windows-riscv64le

# Step 4: Create Windows executable
echo "Creating Windows executable..."
npx electron-builder --win --x64 --config electron-builder.config.js --publish=never

echo "✓ Build complete! Output files:"
echo "  Installer: dist/CrawlOps Studio Setup 1.0.0.exe"  
echo "  Portable:  dist/win-unpacked/CrawlOps Studio.exe"