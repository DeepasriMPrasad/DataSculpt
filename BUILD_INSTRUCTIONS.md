# CrawlOps Studio - Build Instructions

## Quick Windows Build (Recommended)

**IMPORTANT**: 
- Windows executables must be built on Windows (not from Replit/Linux)
- You must run this from the **project root directory**, not from the scripts folder
- See `WINDOWS_EXECUTABLE_GUIDE.md` for detailed Windows build instructions

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

**Error: "Cannot compute electron version from installed node modules"**
- Solution: Run the build script again, it will reinstall electron with specific versions
- Or manually run: `npm uninstall electron electron-builder && npm install --save-dev electron@^37.3.0 electron-builder@^26.0.12`

**Error: "script src='./session_frontend.js' can't be bundled without type='module'"**
- This is now fixed automatically - the script tag includes type="module"

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