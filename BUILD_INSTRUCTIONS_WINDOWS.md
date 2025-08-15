# Windows Build Instructions for CrawlOps Studio

## For Your Grandma's System

### Option 1: Using Bash/Git Bash (Recommended)
```bash
# In Git Bash or WSL
./scripts/build-windows-local.sh
```

### Option 2: Using Windows Command Prompt
```cmd
# In Command Prompt (cmd.exe)
scripts\build-windows-local.bat
```

### Option 3: Manual Build Steps
```bash
# If automated scripts fail, run these steps manually:

# 1. Install dependencies
npm install

# 2. Clean previous builds
rm -rf dist

# 3. Build frontend
npm run build

# 4. Build Windows executable
npx electron-builder --win --x64 --config electron-builder.config.js --publish=never
```

## Requirements
- Node.js 18+ installed
- Windows 10+ or Wine environment
- At least 2GB free disk space

## Output
The Windows executable will be created in:
- `dist/win-unpacked/CrawlOps Studio.exe` (portable version)
- `dist/CrawlOps Studio Setup *.exe` (installer version)

## Troubleshooting

### Error: "bash: @echo: command not found"
**Solution**: Use Git Bash or run the `.sh` script instead:
```bash
bash scripts/build-windows-local.sh
```

### Error: "publisherName not recognized"
**Solution**: This has been fixed in the updated electron-builder.config.js

### Error: "Node.js not found"
**Solution**: Install Node.js from https://nodejs.org/

## Priority Support for Grandma
This build system is specifically optimized for reliability and ease of use. The executable will work offline once built and requires no additional dependencies.