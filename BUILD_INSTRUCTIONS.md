# CrawlOps Studio - Build Instructions

## Windows Build

**Run these commands:**
```bash
npm uninstall electron
npm install --save-dev electron electron-builder
npx vite build
npx electron-builder --win --x64 --config electron-builder.config.js --publish=never
```

**Output:**
- `dist/CrawlOps Studio Setup 1.0.0.exe` (installer)
- `dist/win-unpacked/CrawlOps Studio.exe` (portable)

## macOS Build

```bash
npm uninstall electron
npm install --save-dev electron electron-builder
npx vite build
npx electron-builder --mac --x64 --config electron-builder.config.js --publish=never
```

## Linux Build

```bash
npm uninstall electron
npm install --save-dev electron electron-builder
npx vite build
npx electron-builder --linux --x64 --config electron-builder.config.js --publish=never
```

## Build Scripts

Alternative automated builds:
- **Windows**: `bash scripts/build-windows.sh`
- **macOS**: `bash scripts/build-mac.sh`
- **Linux**: `bash scripts/build-linux.sh`
- **All Platforms**: `bash scripts/build-all.sh`