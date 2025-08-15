# CrawlOps Studio - Build Instructions

## Quick Windows Build (Recommended)

**Use the build script (handles all fixes automatically):**
```bash
# For Git Bash/MSYS (recommended)
bash scripts/build-windows.sh

# For Command Prompt  
scripts\build-windows.bat
```

**Output files:**
- `dist/CrawlOps Studio Setup 1.0.0.exe` (installer)
- `dist/win-unpacked/CrawlOps Studio.exe` (portable)

## Manual Windows Build

If you prefer manual commands:
```bash
# Clean esbuild platform binaries (prevents ENOENT errors)
rm -rf node_modules/@esbuild/aix-ppc64 node_modules/@esbuild/android-* node_modules/@esbuild/darwin-* node_modules/@esbuild/linux-*

# Fix electron dependency
npm uninstall electron
npm install --save-dev electron electron-builder

# Build
npx vite build
npx electron-builder --win --x64 --config electron-builder.config.js --publish=never
```

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