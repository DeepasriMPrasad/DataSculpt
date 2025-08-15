#!/bin/bash
echo "Building CrawlOps Studio for macOS..."

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

# Create macOS executable
echo "Packaging macOS application..."
npx electron-builder --mac --config electron-builder.config.js

echo ""
echo "Build complete! Check the dist/ folder for:"
echo "- CrawlOps Studio-1.0.0.dmg (installer)"
echo "- mac/CrawlOps Studio.app (application bundle)"
echo ""