#!/bin/bash

# CrawlOps Studio Development Script - Fixed for Root Directory Structure
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
if [ "$NODE_VERSION" -lt 18 ]; then
    print_warning "Node.js version is $NODE_VERSION. Version 18 or higher is recommended."
fi

# Check Python version
if command_exists python3.11; then
    PYTHON_CMD="python3.11"
elif command_exists python3.12; then
    PYTHON_CMD="python3.12"
else
    PYTHON_CMD="python3"
fi

print_status "Using Python: $PYTHON_CMD"
print_status "Using Node: $(node --version)"

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

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
if [ ! -d "node_modules" ]; then
    npm install
fi

# Start the FastAPI backend (unified_server.py in root directory)
print_status "Starting FastAPI backend on port 5000..."
$PYTHON_CMD unified_server.py &
API_PID=$!

# Wait for API to start
print_status "Waiting for API to start..."
sleep 3

# Check if API is running
if ! curl -s http://localhost:5000/health >/dev/null 2>&1; then
    print_warning "API health check failed, but continuing..."
fi

# Start the Electron desktop app in development mode
print_status "Starting Electron desktop application..."
npm run dev &
ELECTRON_PID=$!

print_status "✅ CrawlOps Studio is starting up!"
print_status ""
print_status "🌐 API Server: http://localhost:5000"
print_status "🖥️  Desktop App: Starting Electron..."
print_status ""
print_status "📚 Available endpoints:"
print_status "   - GET  /health           - Health check"
print_status "   - POST /api/extract      - Extract content from URL"
print_status "   - POST /api/pdf/links    - Extract links from PDF"
print_status "   - GET  /api/queue/status - Queue status"
print_status ""
print_status "Press Ctrl+C to stop all services"

# Wait for processes
wait $API_PID $ELECTRON_PID

print_status "All services stopped."