#!/bin/bash

echo "===================================================="
echo "CRAWLOPS STUDIO - WINDOWS LOCAL BUILD (BASH VERSION)"
echo "===================================================="

# Change to project root
cd "$(dirname "$0")/.."

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed or not in PATH"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed or not in PATH"
    exit 1
fi

echo "Installing dependencies..."
npm install

echo "Building Vite frontend..."
npm run build

echo "Building Windows executable..."
npx electron-builder --win --x64 --config electron-builder.config.js --publish=never

echo ""
echo "Build completed! Check the 'dist' directory for your Windows executable."
echo "Look for: dist/CrawlOps Studio Setup *.exe"
echo ""