# CrawlOps Studio - Windows Local Build Instructions

## For Windows Local Development (Updated August 15, 2025)

### Prerequisites
- Windows 10/11 (for native builds) OR Linux/macOS with Wine installed
- Node.js 18+ installed
- Git for Windows (if cloning from repository)
- Administrator privileges recommended (Windows) or sudo access (Linux/macOS)

#### Wine Setup (for Linux/macOS)
If building on Linux/macOS, install Wine first:
```bash
# Ubuntu/Debian
sudo apt install wine

# macOS with Homebrew
brew install wine

# Verify Wine installation
wine --version
```

### Step-by-Step Build Process

#### Option 1: Use the Enhanced Build Scripts

**For Native Windows:**
```cmd
# Open Command Prompt or PowerShell as Administrator
# Navigate to your project directory
cd path\to\crawlops-studio

# Run the enhanced Windows build script
scripts\build-windows-local.bat
```

**For Linux/macOS with Wine:**
```bash
# Navigate to your project directory
cd path/to/crawlops-studio

# Make script executable and run
chmod +x scripts/build-windows-wine.sh
./scripts/build-windows-wine.sh
```

This script includes:
- ✅ Detailed logging and environment validation
- ✅ Platform detection (ensures Windows-only execution)
- ✅ Automatic cleanup of problematic esbuild binaries
- ✅ Electron cache management
- ✅ Windows-specific dependency handling
- ✅ Comprehensive error reporting with troubleshooting tips

#### Option 2: Manual Build Process
If you prefer to run commands manually:

1. **Clean Environment**
   ```bash
   # Remove previous builds
   rmdir /s /q dist 2>nul
   rmdir /s /q node_modules\.cache 2>nul
   
   # Clean Electron cache
   rmdir /s /q "%USERPROFILE%\.cache\electron" 2>nul
   ```

2. **Install Dependencies**
   ```bash
   # Reinstall Electron for Windows compatibility
   npm uninstall electron electron-builder
   npm install --save-dev electron@37.3.0 electron-builder@26.0.12
   npm install
   ```

3. **Build Frontend**
   ```bash
   npx vite build
   ```

4. **Build Windows Executable**
   ```bash
   npx electron-builder --win --x64 --config electron-builder.config.js --publish=never --verbose
   ```

### Output Files

After successful build, you'll find:

- **Portable Executable**: `dist\win-unpacked\CrawlOps Studio.exe`
  - Can be run directly without installation
  - Suitable for development and testing

- **Installer**: `dist\CrawlOps Studio Setup 1.0.0.exe`
  - Full installer for distribution
  - Creates desktop shortcuts and start menu entries

### Common Issues & Solutions

#### Error: "wine is required"
- **Cause**: Trying to build Windows executable from Linux/macOS without Wine
- **Solution**: Install Wine on your system or use the enhanced build script which detects Wine automatically

#### Error: "Cannot find module electron"
- **Cause**: Electron not properly installed for Windows
- **Solution**: Run the dependency reinstallation steps above

#### Error: "ENOENT esbuild platform binary"
- **Cause**: Incompatible esbuild binaries for cross-platform development
- **Solution**: Use the enhanced build script which cleans these automatically

#### Build hangs or fails randomly
- **Cause**: Windows Defender or antivirus interference
- **Solution**: 
  1. Add project folder to Windows Defender exclusions
  2. Run Command Prompt as Administrator
  3. Temporarily disable real-time protection during build

#### Error: "Failed to sign executable"
- **Cause**: Code signing certificate issues
- **Solution**: Build script disables code signing for local builds automatically

### Performance Tips

1. **SSD Recommended**: Building on SSD significantly improves build speed
2. **RAM**: Ensure at least 8GB RAM available during build
3. **Antivirus**: Temporarily disable real-time scanning for faster builds
4. **Network**: Use stable internet connection for dependency downloads

### Troubleshooting Checklist

Before asking for help, verify:

- [ ] Running on Windows 10/11 (not Linux/macOS)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] NPM working (`npm --version`)
- [ ] Administrator privileges if possible
- [ ] Project files present (package.json, electron-builder.config.js)
- [ ] No antivirus blocking build process
- [ ] Sufficient disk space (at least 2GB free)

### Advanced Configuration

For custom builds, modify `electron-builder.config.js`:

```javascript
// Windows-specific options
win: {
  target: [
    { target: 'nsis', arch: ['x64'] },      // Installer
    { target: 'portable', arch: ['x64'] }   // Portable
  ],
  requestedExecutionLevel: 'asInvoker',     // No admin required
  publisherName: 'Your Company Name'
}
```

### Build Verification

Test your build:

1. Navigate to `dist\win-unpacked\`
2. Double-click `CrawlOps Studio.exe`
3. Verify application launches and core features work
4. Test crawling functionality with a simple URL

### Distribution

- **Development**: Use portable executable from `win-unpacked`
- **End Users**: Distribute the installer from `dist\CrawlOps Studio Setup*.exe`
- **Corporate**: Package with additional enterprise tools as needed

---

**Note**: This build process is optimized for Windows local development environments. Cross-compilation from Linux (like Replit) requires additional tooling and is not covered in this guide.