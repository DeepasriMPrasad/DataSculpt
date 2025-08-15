# CrawlOps Studio

Enterprise-grade desktop application for professional web crawling with SSO support, human-in-the-loop CAPTCHA handling, and multiple export formats.

![CrawlOps Studio](https://img.shields.io/badge/Version-1.0.0-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/License-Enterprise-orange.svg)

## 🌟 Features

### Core Capabilities
- **Visual Crawling**: All navigation in visible Electron BrowserWindow (no headless browsing)
- **Multiple Export Formats**: JSON, Markdown, SingleFile HTML, and PDF
- **SSO Authentication**: Interactive login support for enterprise systems (Okta, Azure AD, etc.)
- **CAPTCHA Handling**: Human-in-the-loop resolution for challenges
- **PDF Link Extraction**: Recursive crawling of links found within generated PDFs

### Execution Profiles
- **Standard Mode**: Balanced speed and politeness (3 concurrent, 1-2s delay)
- **Safe Mode**: Ultra-respectful crawling (1 concurrent, 8-15s delay, strict robots.txt)
- **Guided Mode**: Manual review and approval for each page

### Enterprise Features
- **Corporate Network Support**: Custom CA bundles and proxy configuration
- **Local-Only Operation**: No telemetry or external dependencies
- **Professional UI**: Dark/light themes with real-time queue management
- **Comprehensive Reporting**: Structured logs and exportable run reports

## 🚀 Quick Start

### Prerequisites

- **Node.js** 20 or higher
- **Python** 3.11 or higher  
- **Git** for development
- **4GB RAM** minimum, 8GB recommended
- **500MB** disk space for installation

### Development Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd crawlops-studio

# 2. Start development environment
./scripts/dev.sh
