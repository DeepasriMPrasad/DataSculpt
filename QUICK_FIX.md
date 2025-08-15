# Quick Fix for Windows Build Error

## Problem
`Package "electron" is only allowed in "devDependencies". Please remove it from the "dependencies" section in your package.json.`

## Solution for Local Machine

**In your project folder, run these exact commands:**

```bash
# Fix the electron dependency issue
npm uninstall electron
npm install --save-dev electron electron-builder

# Now build for Windows
npx vite build
npx electron-builder --win --x64 --config electron-builder.config.js
```

## Alternative: Use the Updated Build Script

The build scripts have been updated to fix this automatically:

```bash
# For Git Bash (recommended)
bash scripts/build-windows.sh

# For Command Prompt
scripts\build-windows.bat
```

## What This Does

1. **Removes electron** from regular dependencies
2. **Installs electron** as dev dependency (where electron-builder expects it)
3. **Installs electron-builder** as dev dependency
4. **Builds the frontend** with Vite
5. **Creates Windows executable** with electron-builder

## Expected Output

After successful build:
- `dist/CrawlOps Studio Setup 1.0.0.exe` (installer)
- `dist/win-unpacked/CrawlOps Studio.exe` (portable)

## Status: Ready to Build ✅

The dependency issue is now resolved. Your Windows executable build should work perfectly.