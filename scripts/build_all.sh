#!/bin/bash

# CrawlOps Studio Build Script
# Builds the entire application for production deployment

set -e

echo "🔨 Building CrawlOps Studio for production..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[BUILD]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status "Checking build prerequisites..."

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js 20 or higher."
    exit 1
fi

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Set build environment
export NODE_ENV=production
export PYTHON_ENV=production

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf dist/
rm -rf apps/desktop/dist/
rm -rf apps/api/dist/

# Create dist directory
mkdir -p dist/packages
mkdir -p dist/api
mkdir -p dist/logs

print_status "Installing dependencies..."

# Install root dependencies
npm ci --only=production

# Build desktop application
print_status "Building desktop application..."
cd apps/desktop

# Install dependencies
npm ci

# Build renderer (React app)
print_status "Building React frontend..."
npm run build:renderer

# Build main process (Electron)
print_status "Building Electron main process..."
npm run build:main

# Package desktop application
print_status "Packaging desktop application with electron-builder..."
npm run dist

# Copy packaged files to main dist directory
cp -r ../../dist/packages/* ../../dist/packages/ || true

cd ../..

# Build Python API
print_status "Building Python API..."
cd apps/api

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install production dependencies
pip install --upgrade pip
pip install fastapi uvicorn[standard] aiohttp beautifulsoup4 pydantic python-multipart

# Install optional dependencies
pip install crawl4ai pypdf pdfminer.six tldextract || print_warning "Some optional dependencies failed to install"

# Create standalone Python package
print_status "Creating Python API distribution..."

# Copy API files to dist directory
mkdir -p ../../dist/api
cp -r crawlops_api/ ../../dist/api/
cp main.py ../../dist/api/
cp -r venv/ ../../dist/api/

# Create startup scripts
cat > ../../dist/api/start_api.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
EOF

cat > ../../dist/api/start_api.bat << 'EOF'
@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
python main.py
EOF

chmod +x ../../dist/api/start_api.sh

cd ../..

# Create installation package
print_status "Creating installation package..."

# Create main startup script
cat > dist/start_crawlops.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting CrawlOps Studio..."

# Start API server in background
cd api
./start_api.sh &
API_PID=$!
cd ..

# Wait a moment for API to start
sleep 3

# Start desktop application
echo "Opening CrawlOps Studio..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open packages/*.dmg || open packages/*.app
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    ./packages/*.AppImage || ./packages/*.deb
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows
    start packages/*.exe
fi

# Function to cleanup on exit
cleanup() {
    echo "Shutting down CrawlOps Studio..."
    kill $API_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for API process
wait $API_PID
EOF

cat > dist/start_crawlops.bat << 'EOF'
@echo off
echo Starting CrawlOps Studio...

REM Start API server in background
cd api
start /B start_api.bat
cd ..

REM Wait a moment for API to start
timeout /t 3 >nul

REM Start desktop application
echo Opening CrawlOps Studio...
start packages\*.exe

echo CrawlOps Studio is running!
echo Close this window to stop the application.
pause
EOF

chmod +x dist/start_crawlops.sh

# Create README for distribution
cat > dist/README.md << 'EOF'
# CrawlOps Studio - Production Build

## Quick Start

### Windows
1. Run `start_crawlops.bat`
2. The desktop application will open automatically

### macOS/Linux  
1. Run `./start_crawlops.sh`
2. The desktop application will open automatically

## Manual Installation

### Desktop Application
Install the desktop app from the `packages/` directory:
- **Windows**: Run the `.exe` installer
- **macOS**: Mount the `.dmg` and drag to Applications
- **Linux**: Install the `.AppImage`, `.deb`, or `.rpm` package

### API Service
The API service can be run independently:
```bash
cd api
./start_api.sh          # Linux/macOS
start_api.bat           # Windows
