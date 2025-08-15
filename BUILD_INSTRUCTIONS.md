# CrawlOps Studio - Build Instructions

## Quick Windows Build (Recommended)

**IMPORTANT**: You must run this from the **project root directory**, not from the scripts folder.

**Use the build script (handles all fixes automatically):**
```bash
# For Git Bash/MSYS (recommended) - from project root:
bash scripts/build-windows.sh

# For Command Prompt - from project root:
scripts\build-windows.bat
```

**Output files:**
- `dist/CrawlOps Studio Setup 1.0.0.exe` (installer)
- `dist/win-unpacked/CrawlOps Studio.exe` (portable)

## Manual Windows Build

If you prefer manual commands (run from project root directory):
```bash
# Clean esbuild platform binaries (prevents ENOENT errors)
rm -rf node_modules/@esbuild/aix-ppc64 node_modules/@esbuild/android-* node_modules/@esbuild/darwin-* node_modules/@esbuild/linux-*

# Fix electron dependency
npm uninstall electron
npm install --save-dev electron electron-builder

# Build frontend (make sure index.html exists in root)
npx vite build

# Create Windows executable
npx electron-builder --win --x64 --config electron-builder.config.js --publish=never
```

## Common Build Errors & Fixes

**Error: "Could not resolve entry module 'index.html'"**
- Solution: Make sure you're running the build from the project root directory (not inside /scripts/)
- The index.html file must be in the same folder as package.json

## Other Platforms

**macOS:**
```bash
bash scripts/build-mac.sh
```

**Linux:**
```bash
bash scripts/build-linux.sh  
```

**All Platforms:**
```bash
bash scripts/build-all.sh
```

## Common Issues Fixed

- ✅ **ENOENT scandir '@esbuild/aix-ppc64'** - Build scripts clean problematic platform binaries
- ✅ **"electron" only allowed in devDependencies** - Scripts auto-fix dependency placement  
- ✅ **Application entry file "index.js" corrupted** - Added proper entry point configuration