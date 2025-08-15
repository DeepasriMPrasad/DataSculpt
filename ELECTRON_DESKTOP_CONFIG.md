# Desktop Application Configuration

## API Server Integration

The desktop application automatically detects when running in Electron and switches to localhost:5000 for API calls.

### Environment Detection
- **Web Browser**: Uses current origin (e.g., https://replit.dev/api)
- **Electron Desktop**: Uses http://localhost:5000/api

### Server Startup
When the desktop app launches, it automatically:
1. Starts the Python FastAPI server on localhost:5000
2. Serves the React frontend from the server
3. Handles all API calls locally

### Windows Build Process
1. Run `bash scripts/build-windows-local.sh`
2. The executable will be in `dist/win-unpacked/CrawlOps Studio.exe`
3. Double-click to run - server starts automatically

### Troubleshooting Desktop App

**Error: "Cannot connect to API server"**
- The Python server may not have started
- Check if port 5000 is available
- Look for Python error messages in console

**Error: "file:///api" URL**
- This indicates the Electron detection failed
- The app is trying to use file:// protocol instead of http://
- Check user agent string in browser dev tools

**Error: Dependencies missing**
- Run `npm install` before building
- Ensure Python 3.11+ is installed
- Install required Python packages

### Server Dependencies
The desktop app bundles:
- Python FastAPI server
- All crawling dependencies
- Session management
- File output system

No internet connection required after installation.