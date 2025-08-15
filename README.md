# CrawlOps Studio

Enterprise-grade desktop application for professional web crawling with visible browser navigation, session management, and multi-format content export.

## Key Features

- **Visual Crawling**: All navigation occurs in visible browser windows (no headless browsing)
- **Session Management**: Persistent storage of authentication tokens and cookies per domain
- **Multi-format Export**: JSON, Markdown, SingleFile HTML, and PDF outputs
- **Enterprise Authentication**: SSO support for corporate systems (Okta, Azure AD, etc.)
- **Human-in-the-Loop**: CAPTCHA and challenge resolution with manual intervention
- **Execution Profiles**: Standard (fast), Safe (cautious), and Guided (manual approval) modes
- **Corporate Network**: Custom CA bundles and proxy configuration support

## Technology Stack

- **Frontend**: Electron, React 19, TypeScript, TailwindCSS
- **Backend**: FastAPI with Python 3.11+
- **Content Processing**: crawl4ai, SingleFile web capture
- **Session Storage**: SQLite with automatic expiration handling
- **Build System**: Vite, electron-builder for cross-platform packaging

## Quick Start

### Development
```bash
# Start the application
python3.11 unified_server.py
```

### Building Executables

**Windows:**
```bash
npm uninstall electron
npm install --save-dev electron electron-builder
npx vite build
npx electron-builder --win --x64 --config electron-builder.config.js --publish=never
```

**macOS/Linux:** See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)

## Architecture

- **Unified Server**: Single FastAPI server serves both frontend and backend on port 5000
- **IPC Communication**: Secure Electron context bridge for main-renderer communication
- **Queue Management**: In-memory URL queue with status tracking and concurrent processing
- **Session Persistence**: Local SQLite database stores authentication data with domain isolation
- **Content Pipeline**: Parallel processing for multiple output formats

## Security & Privacy

- **Local Operation**: All processing occurs locally, no external telemetry
- **Session Isolation**: Domain-based session storage with automatic expiration
- **Visible Browsing**: No headless automation, all navigation is user-visible
- **Corporate Ready**: Enterprise authentication and network configuration support

## Platform Support

- Windows 10/11 (x64)
- macOS 10.15+ (Intel & Apple Silicon)
- Linux (x64) - AppImage and DEB packages