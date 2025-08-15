#!/bin/bash
echo "Building CrawlOps Studio for Linux..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed or not in PATH"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Install dependencies if needed
echo "Installing dependencies..."
npm install

# Fix electron dependency location and install electron-builder
echo "Fixing electron dependency and installing electron-builder..."
npm uninstall electron
npm install --save-dev electron electron-builder

# Build the frontend
echo "Building frontend with Vite..."
npx vite build

# Create Linux executable
echo "Packaging Linux application..."
npx electron-builder --linux --config electron-builder.config.js

echo ""
echo "Build complete! Check the dist/ folder for:"
echo "- CrawlOps Studio-1.0.0.AppImage (portable)"
echo "- CrawlOps Studio-1.0.0.deb (Debian/Ubuntu installer)"
echo "- linux-unpacked/crawlops-studio (executable)"
echo ""