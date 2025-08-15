# CrawlOps Studio

## Overview
CrawlOps Studio is an enterprise-grade desktop application designed for professional web crawling. Built with Electron, React, and FastAPI, it offers visual crawling through visible browser windows, supports SSO authentication, handles CAPTCHA challenges with human-in-the-loop resolution, and exports content in various formats (JSON, Markdown, SingleFile HTML, PDF). It provides Standard, Safe, and Guided execution profiles and is tailored for corporate environments with support for custom CA bundles and proxy configurations. The project aims to provide a robust, secure, and user-friendly solution for complex web data extraction needs, enhancing business intelligence and data acquisition capabilities.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Electron desktop application with React 19 and TypeScript.
- **UI Library**: TailwindCSS for styling with dark/light theme support.
- **State Management**: Zustand for client-side state management.
- **Build System**: Vite for development and bundling, electron-builder for packaging.
- **Component Structure**: Modular React components for Dashboard, Queue, Challenge Center, and Settings.

### Backend Architecture
- **API Framework**: FastAPI with Python 3.11+ for REST API endpoints.
- **Content Extraction**: `crawl4ai` library for structured content extraction. Features a fallback system using `aiohttp` and `BeautifulSoup` for robust content extraction when `crawl4ai`'s Playwright dependencies are unavailable.
- **PDF Processing**: `pypdf`/`PyPDF2` for PDF link extraction with fallback to `pdfminer`.
- **URL Processing**: Custom URL validation and normalization utilities.
- **Architecture Pattern**: Service-oriented with separate services for crawling, PDF processing, and extraction.
- **Logging**: Comprehensive logging system with dedicated files for server, scraping activity, and API requests, supporting multiple log levels.

### IPC Communication
- **Main-Renderer Communication**: Electron IPC with `contextBridge` for secure communication.
- **Channel System**: Structured IPC channels for profile management, authentication, capture operations, queue management, and settings.
- **Security**: Context isolation enabled with preload scripts for API exposure.

### Content Processing Pipeline
- **Visual Crawling**: All navigation occurs in visible Electron BrowserWindow instances.
- **SingleFile Integration**: Full web API implementation with CSS and image inlining for rich HTML capture.
- **PDF Generation**: Uses `webContents.printToPDF` from SingleFile HTML output.
- **Multi-format Export**: Parallel processing for JSON, Markdown, Rich HTML (SingleFile), and PDF outputs saved automatically to `./crawl_output/`.
- **Robots.txt Handling**: User-controlled override option to ignore `robots.txt` directives.

### Queue Management System
- **In-memory Queue**: Map-based URL queue with status tracking (queued, running, waiting_captcha, waiting_user, done, failed, skipped).
- **Execution Profiles**: Standard (3 concurrent, 1-2s delay), Safe (1 concurrent, 8-15s delay), Guided (manual approval).
- **Challenge Handling**: Human-in-the-loop system for CAPTCHA and authentication challenges.

### Authentication & Security
- **SSO Support**: Interactive login through visible browser windows for enterprise systems.
- **Session Persistence**: Comprehensive session token and cookie storage system using SQLite, with automatic expiration handling and domain-specific management.
- **Corporate Network**: Custom CA bundle support and proxy configuration.
- **Security Model**: No headless browsing, local-only operation with no external telemetry.

### Build System
- Supports multi-platform executable builds for Windows, macOS, and Linux using `electron-builder`. Includes specific build scripts and configurations for Windows local builds and Wine cross-compilation.

### Enhanced JavaScript and Cookie Support ✅
- **Issue**: Websites with JavaScript protection (Cloudflare, etc.) returning minimal content
- **Solution**: Enhanced HTTP client with JavaScript simulation and cookie support
- **Implementation**:
  - Upgraded HTTP client headers to simulate JavaScript-enabled browser
  - Added cookie jar support for session persistence
  - Enhanced Cloudflare and JavaScript protection detection
  - Intelligent fallback content extraction from multiple sources
- **Features Added**:
  - Real browser headers (Chrome 120 user agent, sec-fetch headers)
  - Cookie jar with automatic cookie handling
  - Enhanced JavaScript protection detection (Cloudflare, security checks)
  - Multi-source content extraction (noscript, JSON-LD, meta tags)
  - Structured data extraction for protected sites
- **Content Sources**: noscript tags, JSON-LD structured data, meta descriptions, Open Graph tags
- **Logging**: Detailed protection detection and enhanced content extraction logging
- **Status**: JavaScript protection handling operational with intelligent content extraction

### JavaScript-Heavy Site Limitations ⚠️
- **Reality**: Some sites (like AWS documentation) require full JavaScript execution to load content
- **Current Capability**: Enhanced HTTP extraction with multiple fallback methods
- **Behavior**: 
  - Detects JavaScript protection automatically
  - Extracts available static content (noscript, meta tags, structured data)
  - Attempts deeper content extraction from HTML containers
  - Provides meaningful feedback when content is JavaScript-dependent
- **Alternative**: For full JavaScript rendering, users would need browser automation tools like Playwright locally
- **Status**: Working as designed - extracts maximum possible content from static HTML sources

## External Dependencies

### Core Runtime Dependencies
- **Node.js**: 20+
- **Python**: 3.11+
- **Electron**: 37.3.0

### Frontend Libraries
- **React**: 19.1.1
- **TypeScript**: 5.9.2
- **TailwindCSS**: 4.1.12
- **Zustand**: 5.0.7
- **Lucide React**: 0.539.0

### Backend Libraries
- **FastAPI**: Web framework
- **crawl4ai**: Primary content extraction engine
- **aiohttp**: Async HTTP client
- **beautifulsoup4**: HTML parsing
- **pypdf/PyPDF2**: PDF processing
- **pdfminer.six**: Fallback PDF processing
- **aiodns**: DNS resolver (with Windows compatibility fixes)

### Development & Build Tools
- **Vite**: 7.1.2
- **electron-builder**: 26.0.12
- **vite-plugin-electron**: 0.29.0
- **Autoprefixer**: 10.4.21

### Browser Extensions
- **SingleFile**: Core script injection for complete webpage capture.