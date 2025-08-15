# Windows Executable Build Guide

## The Cross-Platform Build Issue

The error you're seeing happens because:
- Replit runs on Linux servers
- Building Windows executables from Linux requires `wine` (Windows emulator)
- This causes the build to fail with "wine is required" error

## Solution: Build on Your Local Windows Machine

**The Windows executable must be built on Windows itself, not from Replit.**

### Step 1: Get Your Project Files on Windows

Download or clone your project to your Windows machine:
```bash
git clone [your-repo-url]
cd DataSculpt
```

### Step 2: Install Dependencies on Windows

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies (if needed)
pip install fastapi uvicorn aiohttp beautifulsoup4 pydantic python-multipart crawl4ai pypdf pdfminer.six tldextract
```

### Step 3: Run the Windows Build Script

From your project root directory:
```bash
# For Git Bash (recommended)
bash scripts/build-windows.sh

# OR for Command Prompt
scripts\build-windows.bat
```

### Step 4: Expected Output

```
Building CrawlOps Studio for Windows...
Cleaning up esbuild platform binaries...
Fixing electron dependency placement...
Verifying electron installation...
37.3.0
Building frontend...
✓ X modules transformed.
Creating Windows executable...
• packaging platform=win32 arch=x64 electron=37.3.0
✓ Build complete! Output files:
  Installer: dist/CrawlOps Studio Setup 1.0.0.exe  
  Portable:  dist/win-unpacked/CrawlOps Studio.exe
```

## All Features Included in Windows Build

The Windows executable will include:

✅ **Core Application**
- Main Electron application with React frontend
- Full CrawlOps Studio interface (as shown in your screenshot)
- Dashboard with crawl statistics and configuration

✅ **Session Management System**
- Complete session storage with SQLite database
- Save/load cookies and tokens per domain
- Session persistence across application restarts
- Frontend integration with SessionManager class

✅ **Backend Services**
- FastAPI server (unified_server.py) 
- Session API endpoints (session_api.py)
- Content extraction with crawl4ai
- PDF processing capabilities

✅ **Python Runtime**
- All Python dependencies bundled
- Session management database
- API test utilities (test_api.py)

✅ **Crawling Features**
- Multiple export formats (JSON, MD, HTML, PDF)
- Configurable crawl depth and page limits
- Queue management system
- Challenge handling for CAPTCHA/authentication

## File Structure in Built Executable

```
CrawlOps Studio.exe
├── dist/                    # Frontend build
├── session_manager.py       # Session storage system
├── session_api.py          # REST API endpoints  
├── session_frontend.js     # Frontend session integration
├── unified_server.py       # Main FastAPI server
├── crawl_cache/            # Cache directory
└── [All Python dependencies bundled]
```

## Troubleshooting

**If build fails with "Cannot compute electron version":**
```bash
npm uninstall electron electron-builder
npm install --save-dev electron@^37.3.0 electron-builder@^26.0.12
```

**If you get "Could not resolve entry module":**
- Make sure you're running from project root (where package.json is)
- Not from inside the /scripts/ folder

**Note:** The application will work exactly as shown in your screenshot once built on Windows.