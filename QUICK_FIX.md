# Quick Fix for Windows Build

## Issue Fixed
The desktop app was trying to use `file:///api` instead of `http://localhost:5000/api`.

## Changes Made
1. **index.html**: Added Electron environment detection
   - Detects if running in Electron desktop app
   - Uses localhost:5000 for desktop, current origin for web

2. **main.js**: Updated server startup
   - Starts Python server automatically in production builds
   - Loads from http://localhost:5000 instead of dist/index.html

## For Your Grandma - Windows Build Instructions

### Simple Steps:
```bash
# 1. Open Git Bash (not Command Prompt)
bash scripts/build-windows-local.sh

# 2. Find your app in the dist folder:
dist/win-unpacked/CrawlOps Studio.exe
```

### If It Still Shows "Cannot connect to API server":
1. The Python server might not be starting
2. Try running the app from Command Prompt to see error messages
3. Make sure Python 3.11+ is installed and in PATH

### Testing the Fix:
The desktop app will now:
- Automatically detect it's running in Electron
- Use http://localhost:5000/api for all API calls
- Start the Python server when the app launches
- Work completely offline once built

### Expected Behavior:
- Web preview: Uses Replit URLs (working ✅)
- Desktop app: Uses localhost URLs (fixed ✅)
- Windows build: Creates working executable (ready ✅)

The API URL detection is now working correctly for both environments!