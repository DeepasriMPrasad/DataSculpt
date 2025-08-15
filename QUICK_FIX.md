# Windows Build Quick Fix Guide

## The Issue You Encountered
```
error during build:
Could not resolve entry module "index.html".
```

## Root Cause
You were running the build from the `/scripts/` directory instead of the project root directory.

## Quick Fix

**Step 1:** Navigate to your project root (where package.json is located)
```bash
# From your current location in scripts/
cd ..

# Verify you're in the right place (should show package.json)
ls package.json
```

**Step 2:** Run the build script from project root
```bash
# Now run the script (note the scripts/ prefix)
bash scripts/build-windows.sh
```

## Why This Happens
- Vite looks for `index.html` in the current working directory
- When run from `/scripts/`, it can't find `index.html` (which is in project root)
- The build script must be executed from project root to work properly

## Alternative (if you prefer staying in scripts directory)
```bash
# From inside scripts/ directory, you can run:
cd .. && bash scripts/build-windows.sh
```

## Expected Output After Fix
```
Building CrawlOps Studio for Windows...
Cleaning up esbuild platform binaries...
Fixing electron dependency placement...
Building frontend...
vite v7.1.2 building for production...
✓ X modules transformed.
dist/index.html  XX.XX kB │ gzip: X.XX kB
✓ built in XXXms
Creating Windows executable...
✓ Build complete! Output files:
  Installer: dist/CrawlOps Studio Setup 1.0.0.exe
  Portable:  dist/win-unpacked/CrawlOps Studio.exe
```