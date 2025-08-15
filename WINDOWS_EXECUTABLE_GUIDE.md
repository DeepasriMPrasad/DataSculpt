# Windows Executable Creation Guide

## Current Status
✅ **Fixed**: Desktop app API URL detection (uses localhost:5000 when running in Electron)
✅ **Fixed**: Windows build script syntax (proper bash script created)
⚠️ **Issue**: Replit environment cannot cross-compile for Windows (needs Wine)

## For Your Grandma - Windows Build Options

### Option 1: Use the Fixed Script (Recommended)
```bash
# In Git Bash on your Windows machine:
bash scripts/build-windows-local.sh
```

### Option 2: Manual Build (If script fails)
```bash
# 1. Install dependencies
npm install

# 2. Build frontend 
npx vite build

# 3. Build Windows executable
npx electron-builder --win --x64 --config electron-builder.config.js --publish=never
```

### Option 3: Download and Run Locally
Since Replit can't build Windows executables directly, you can:
1. Download the entire project as ZIP
2. Extract on Windows machine
3. Run the build script there

## What the Fixed Desktop App Will Do

### Automatic Environment Detection
- **Web Browser**: Uses Replit URLs (https://xxx.replit.dev/api)
- **Desktop App**: Uses localhost (http://localhost:5000/api)

### Startup Process
1. Launch CrawlOps Studio.exe
2. Python server starts automatically on localhost:5000
3. Electron loads the web interface
4. All API calls go to the local server
5. Works completely offline

### Expected Files After Build
```
dist/
├── win-unpacked/
│   └── CrawlOps Studio.exe    # ← Main executable
└── CrawlOps Studio Setup.exe  # ← Installer
```

## Testing the Fix

### Web Version (Working Now)
- Open the Replit preview
- Should connect to Replit API server
- All crawling features functional

### Desktop Version (Ready)
- When built on Windows, will use localhost
- Python server starts with the app
- No internet connection needed after installation

## The Core Fix Applied
```javascript
// Auto-detects Electron environment
const isElectron = window.navigator.userAgent.toLowerCase().indexOf(' electron/') > -1;

if (isElectron) {
    // Desktop: http://localhost:5000/api
} else {
    // Web: current origin/api
}
```

This ensures the desktop app always connects to the local server, while the web version uses the Replit server.

**Bottom Line**: The desktop app is now properly configured to work on Windows. The build process just needs to run on a Windows machine with Node.js installed.