# CrawlOps Studio - Quick Start for Windows

## For Your Grandma - Simple Instructions

### Building the Windows Application

**Step 1: Open Git Bash (or Command Prompt)**
- Look for "Git Bash" in your Windows start menu
- Right-click and "Run as Administrator" if needed

**Step 2: Navigate to your project folder**
```bash
cd /path/to/your/DataSculpt/folder
```

**Step 3: Run the build script**
```bash
bash scripts/build-windows-local.sh
```

**Step 4: Find your application**
- Look in the `dist` folder
- Double-click `CrawlOps Studio.exe` to run

### If You Get Errors

**Error: "bash: @echo: command not found"**
- You're trying to run a .bat file with bash
- Use: `bash scripts/build-windows-local.sh` instead

**Error: "Node.js not found"**
- Install Node.js from https://nodejs.org/
- Choose the LTS version (recommended)

**Error: "npm not found"**
- Node.js should include npm
- Restart your command prompt after installing Node.js

### What This Application Does

1. **Web Crawling**: Visits websites and downloads their content
2. **Multiple Formats**: Saves content as JSON, Markdown, HTML, and text files
3. **Enterprise Features**: Professional-grade crawling with scope control
4. **Offline Operation**: Works without internet once built

### Features for Grandma

- **Simple Interface**: Easy-to-use web interface
- **No Technical Knowledge Required**: Just enter a website URL
- **Automatic File Saving**: Content saved to organized folders
- **Safe Crawling**: Respects website rules and limits
- **Professional Quality**: Enterprise-grade features

### Output Files Location

All downloaded content goes to: `crawl_output/` folder
- `.json` files: Raw data
- `.md` files: Readable text format
- `.html` files: Complete web pages
- `.txt` files: Plain text content

### Support

If you need help:
1. Check the error messages carefully
2. Make sure Node.js is installed
3. Run as Administrator if needed
4. Use the bash script (.sh) not the batch file (.bat)

**Remember**: This tool is designed to be professional and reliable for your data extraction needs.