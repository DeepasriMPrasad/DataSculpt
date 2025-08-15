#!/bin/bash

# CrawlOps Studio Development Script
# Starts both the FastAPI backend and Electron frontend in development mode

set -e

echo "🚀 Starting CrawlOps Studio in development mode..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js 20 or higher."
    exit 1
fi

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

if ! command_exists npm; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    print_warning "Node.js version is $NODE_VERSION. Version 20 or higher is recommended."
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
if command_exists python3.11; then
    PYTHON_CMD="python3.11"
elif command_exists python3.12; then
    PYTHON_CMD="python3.12"
else
    PYTHON_CMD="python3"
fi

print_status "Using Python: $PYTHON_CMD"
print_status "Using Node: $(node --version)"

# Create virtual environment for Python API if it doesn't exist
if [ ! -d "apps/api/venv" ]; then
    print_status "Creating Python virtual environment..."
    cd apps/api
    $PYTHON_CMD -m venv venv
    cd ../..
fi

# Function to cleanup background processes
cleanup() {
    print_status "Shutting down services..."
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    if [ ! -z "$ELECTRON_PID" ]; then
        kill $ELECTRON_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Install dependencies
print_status "Installing dependencies..."

# Install root dependencies
if [ ! -d "node_modules" ]; then
    npm install
fi

# Install desktop app dependencies
if [ ! -d "apps/desktop/node_modules" ]; then
    print_status "Installing desktop app dependencies..."
    cd apps/desktop
    npm install
    cd ../..
fi

# Install and activate Python dependencies
print_status "Installing Python API dependencies..."
cd apps/api

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install fastapi uvicorn[standard] aiohttp beautifulsoup4 pydantic python-multipart

# Try to install optional dependencies
print_status "Installing optional dependencies..."
pip install crawl4ai pypdf pdfminer.six tldextract || print_warning "Some optional dependencies failed to install"

cd ../..

# Start the FastAPI backend
print_status "Starting FastAPI backend on port 8000..."
cd apps/api
source venv/bin/activate
$PYTHON_CMD -m uvicorn crawlops_api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
cd ../..

# Wait for API to start
print_status "Waiting for API to start..."
sleep 3

# Check if API is running
if ! curl -s http://localhost:8000/health >/dev/null 2>&1; then
    print_warning "API health check failed, but continuing..."
fi

# Start the Electron desktop app
print_status "Starting Electron desktop application..."
cd apps/desktop
npm run dev &
ELECTRON_PID=$!
cd ../..

print_status "✅ CrawlOps Studio is starting up!"
print_status ""
print_status "🌐 API Server: http://localhost:8000"
print_status "🖥️  Desktop App: Starting Electron..."
print_status ""
print_status "📚 Available endpoints:"
print_status "   - GET  /health           - Health check"
print_status "   - POST /extract          - Extract content from URL"
print_status "   - POST /pdf/links        - Extract links from PDF"
print_status "   - GET  /report/runs      - List crawl reports"
print_status ""
print_status "Press Ctrl+C to stop all services"

# Wait for processes
wait $API_PID $ELECTRON_PID

print_status "All services stopped."
