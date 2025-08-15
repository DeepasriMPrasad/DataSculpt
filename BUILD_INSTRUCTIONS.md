# Windows Executable Build Instructions

## For Local Windows Machine ✅

Since you're building on your local Windows machine, here are the exact steps:

### Quick Build (Copy & Paste)

**Open Command Prompt or Git Bash in your project folder and run:**

```bash
# Install dependencies
npm install

# Fix electron dependency issue and install electron-builder
npm uninstall electron
npm install --save-dev electron electron-builder

# Build frontend
npx vite build

# Create Windows executable
npx electron-builder --win --x64 --config electron-builder.config.js
```

### Alternative: Use Build Script

I've created a build script for you. Run this in your project folder:

**For Command Prompt:**
```cmd
scripts\build-windows.bat
```

**For Git Bash/WSL:**
```bash
bash scripts/build-windows.sh
```

## What You'll Get

After running the build commands, you'll find in the `dist/` folder:
- **Installer**: `CrawlOps Studio Setup 1.0.0.exe`
- **Portable**: `win-unpacked/CrawlOps Studio.exe`

## Why No npm Scripts?

This project was designed for Replit workflows, not traditional npm scripts. The build scripts replace the missing `npm run build:win` command.

## Common Issues Fixed

### Electron Dependency Error ✅
**Problem**: `Package "electron" is only allowed in "devDependencies"`
**Solution**: All build scripts now automatically move electron to devDependencies where electron-builder expects it.

### Missing Scripts Error ✅  
**Problem**: `npm error Missing script: "build:win"`
**Solution**: Use the provided build scripts or manual commands instead of npm scripts.

## Troubleshooting

**"electron-builder not found"**
```bash
npm install --save-dev electron-builder
```

**"vite not found"** 
```bash
npm install
```

**Build fails with dependency errors**
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

**"Package electron is only allowed in devDependencies"**
- Fixed by moving electron from dependencies to devDependencies
- All build commands and scripts now handle this automatically
- Manual fix: `npm uninstall electron && npm install --save-dev electron`

## Key Files Created

1. **vite.config.js** - Frontend build configuration
2. **electron-builder.config.js** - Electron packaging settings
3. **main.js** - Electron main process
4. **preload.js** - Secure IPC communication

## Windows Compatibility Features

✅ **Event Loop Fix**: Automatic aiodns SelectorEventLoop policy for Windows  
✅ **Dependency Management**: Electron properly installed as dev dependency  
✅ **Build Configuration**: Complete electron-builder setup for Windows  
✅ **Backend Integration**: Python FastAPI server embedded in executable

## Distribution

The resulting executable is completely self-contained and includes:
- Complete React frontend
- Electron runtime and Chromium
- Python backend integration
- All required dependencies
- Windows-specific compatibility fixes

Recipients need only the executable file - no additional software installation required.

## Multi-Platform Build Support ✅

### macOS Build

**Commands:**
```bash
# Install dependencies
npm install

# Fix electron dependency issue and install electron-builder
npm uninstall electron
npm install --save-dev electron electron-builder

# Build for macOS
npx vite build
npx electron-builder --mac --config electron-builder.config.js
```

**Or use the build script:**
```bash
bash scripts/build-mac.sh
```

**Output:**
- `CrawlOps Studio-1.0.0.dmg` (installer)
- `mac/CrawlOps Studio.app` (application bundle)

### Linux Build

**Commands:**
```bash
# Install dependencies
npm install

# Fix electron dependency issue and install electron-builder
npm uninstall electron
npm install --save-dev electron electron-builder

# Build for Linux
npx vite build
npx electron-builder --linux --config electron-builder.config.js
```

**Or use the build script:**
```bash
bash scripts/build-linux.sh
```

**Output:**
- `CrawlOps Studio-1.0.0.AppImage` (portable)
- `CrawlOps Studio-1.0.0.deb` (Debian/Ubuntu installer)
- `linux-unpacked/crawlops-studio` (executable)

### Build All Platforms

**Build everything at once:**
```bash
bash scripts/build-all.sh
```

This creates Windows, macOS, and Linux executables in one command.

## Cross-Platform Notes

- **Windows**: Requires Windows machine for proper code signing
- **macOS**: Requires macOS machine for proper app notarization
- **Linux**: Can be built on any platform but works best on Linux
- **Universal**: The `build-all.sh` script works on any Unix-like system

## Status: Ready for Multi-Platform Build ✅

All configuration files and build scripts are in place for Windows, macOS, and Linux.