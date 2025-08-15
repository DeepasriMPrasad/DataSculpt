# CrawlOps Studio - Logging System

This folder contains detailed logs for the CrawlOps Studio application.

## Log Files

### Main Application Logs
- **`crawlops_server.log`** - Main server logs with general application events
- **`scraping_detailed.log`** - General scraping events mixed with server logs

### Specialized Logs
- **`scraping_activity.log`** - Dedicated scraping operations log
  - Crawl start/end events
  - Success/failure details
  - Word counts and extracted content metadata
  - Robots.txt compliance logging
  - Fallback extraction events

- **`api_requests.log`** - API endpoint access log
  - Incoming crawl requests
  - Request parameters and validation
  - API errors and responses

## Log Levels

- **DEBUG**: Detailed information for troubleshooting (file names, metadata)
- **INFO**: General operational information (successful crawls, status updates)
- **WARNING**: Important events that need attention (robots.txt ignored, fallback extraction)
- **ERROR**: Error events that need investigation (crawl failures, API errors)

## Log Format

```
YYYY-MM-DD HH:MM:SS,mmm - LOGGER_NAME - LEVEL - MESSAGE
```

Example:
```
2025-08-15 22:30:15,123 - SCRAPING - INFO - SUCCESS: Extracted 605 words from https://httpbin.org/html
2025-08-15 22:30:15,124 - API - INFO - Crawl request received: https://httpbin.org/html
```

## Log Rotation

Logs are appended to files and will grow over time. Consider implementing log rotation for production deployments:

- Maximum file size: 10MB per log file
- Keep last 5 rotated files
- Compress old log files

## Troubleshooting Guide

### Common Log Patterns

**Successful Crawl:**
```
API - INFO - Crawl request received: https://example.com
SCRAPING - INFO - Starting crawl for https://example.com - Max Depth: 1, Max Pages: 1, Ignore Robots: true
SCRAPING - WARNING - ROBOTS.TXT IGNORED for https://example.com - Enterprise crawling mode enabled
SCRAPING - INFO - SUCCESS: Extracted 234 words from https://example.com
```

**Failed Crawl (crawl4ai fallback):**
```
SCRAPING - WARNING - crawl4ai failed for https://example.com: BrowserType.launch: Host system is missing dependencies
SCRAPING - INFO - Falling back to HTTP + BeautifulSoup extraction for https://example.com
SCRAPING - INFO - SUCCESS: Extracted 123 words from https://example.com
```

**Complete Failure:**
```
SCRAPING - ERROR - CRAWL FAILED for https://example.com: Connection timeout
API - ERROR - Crawl request failed: https://example.com - Error: Connection timeout
```

## Privacy & Security

- URLs are logged for debugging purposes
- No user credentials or sensitive data are logged
- Robots.txt compliance decisions are logged for audit purposes
- All logs are stored locally and not transmitted externally

## Maintenance

To clear logs for fresh start:
```bash
# Remove all log files
rm logs/*.log

# Keep only the directory structure
# (logs/.gitkeep will remain)
```

The log files will be recreated automatically when the application starts.