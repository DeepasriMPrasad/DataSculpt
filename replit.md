# CrawlOps Studio

## Overview

CrawlOps Studio is an enterprise-grade desktop application for professional web crawling built with Electron, React (TypeScript), and FastAPI. The application provides visual crawling capabilities through visible browser windows (no headless browsing), supports SSO authentication for enterprise systems, handles CAPTCHA challenges with human-in-the-loop resolution, and exports content in multiple formats (JSON, Markdown, SingleFile HTML, and PDF). It features three execution profiles (Standard, Safe, and Guided modes) and is designed for corporate environments with support for custom CA bundles and proxy configurations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Electron desktop application with React 19 and TypeScript
- **UI Library**: TailwindCSS for styling with dark/light theme support
- **State Management**: Zustand for client-side state management
- **Build System**: Vite for development and bundling, electron-builder for packaging
- **Component Structure**: Modular React components for Dashboard, Queue, Challenge Center, and Settings

### Backend Architecture
- **API Framework**: FastAPI with Python 3.11+ for REST API endpoints
- **Content Extraction**: crawl4ai library for structured content extraction to JSON/Markdown
- **PDF Processing**: pypdf/PyPDF2 for PDF link extraction with fallback to pdfminer
- **URL Processing**: Custom URL validation and normalization utilities
- **Architecture Pattern**: Service-oriented with separate services for crawling, PDF processing, and extraction

### IPC Communication
- **Main-Renderer Communication**: Electron IPC with contextBridge for secure communication
- **Channel System**: Structured IPC channels for profile management, authentication, capture operations, queue management, and settings
- **Security**: Context isolation enabled with preload scripts for API exposure

### Content Processing Pipeline
- **Visual Crawling**: All navigation occurs in visible Electron BrowserWindow instances
- **SingleFile Integration**: Full web API implementation with CSS and image inlining for rich HTML capture
- **PDF Generation**: Uses webContents.printToPDF from SingleFile HTML output
- **Multi-format Export**: Parallel processing for JSON, Markdown, Rich HTML (SingleFile), and PDF outputs

### Queue Management System
- **In-memory Queue**: Map-based URL queue with status tracking (queued, running, waiting_captcha, waiting_user, done, failed, skipped)
- **Execution Profiles**: Standard (3 concurrent, 1-2s delay), Safe (1 concurrent, 8-15s delay), Guided (manual approval)
- **Challenge Handling**: Human-in-the-loop system for CAPTCHA and authentication challenges

### Authentication & Security
- **SSO Support**: Interactive login through visible browser windows for enterprise systems (Okta, Azure AD, etc.)
- **Session Persistence**: Reuse authenticated sessions across crawl operations
- **Corporate Network**: Custom CA bundle support and proxy configuration
- **Security Model**: No headless browsing, local-only operation with no external telemetry

## External Dependencies

### Core Runtime Dependencies
- **Node.js**: 20+ for Electron and build processes
- **Python**: 3.11+ for FastAPI backend
- **Electron**: 37.3.0 for cross-platform desktop application framework

### Frontend Libraries
- **React**: 19.1.1 with react-dom for UI framework
- **TypeScript**: 5.9.2 for type safety
- **TailwindCSS**: 4.1.12 for utility-first styling
- **Zustand**: 5.0.7 for lightweight state management
- **Lucide React**: 0.539.0 for icon components

### Backend Libraries
- **FastAPI**: Web framework for Python API
- **crawl4ai**: Primary content extraction engine
- **aiohttp**: Async HTTP client for web requests and SingleFile capture
- **beautifulsoup4**: HTML parsing for SingleFile resource inlining
- **pypdf/PyPDF2**: PDF processing and link extraction
- **pdfminer.six**: Fallback PDF processing library

### Development & Build Tools
- **Vite**: 7.1.2 for development server and bundling
- **electron-builder**: 26.0.12 for application packaging
- **vite-plugin-electron**: 0.29.0 for Electron integration
- **Autoprefixer**: 10.4.21 for CSS processing

### Browser Extensions
- **SingleFile**: Browser extension or core script injection for complete webpage capture

### System Requirements
- **Memory**: 4GB minimum, 8GB recommended
- **Storage**: 500MB for installation
- **Platform**: Windows, macOS, Linux support via Electron