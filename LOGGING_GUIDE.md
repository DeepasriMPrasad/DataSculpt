# CrawlOps Studio Logging System

## Log File Locations

### Development Mode (Web Browser)
- **Location**: `./logs/` directory in project root
- **Files Created**:
  - `crawlops_server.log` - Main application events
  - `scraping_activity.log` - Detailed crawling operations
  - `api_requests.log` - HTTP API request/response logs
  - `scraping_detailed.log` - Comprehensive scraping debug info

### Windows Desktop Application
- **Primary Location**: Same directory as executable `./logs/`
- **Fallback Location**: `%USERPROFILE%\CrawlOpsStudio\logs\`
- **Permission Handling**: Automatically falls back to user directory if current directory not writable

## Log File Contents

### `crawlops_server.log`
- Server startup/shutdown events
- Platform and Python version info
- General application status messages
- Error handling and recovery

### `scraping_activity.log`
- Individual URL crawling attempts
- Authentication method usage
- Robots.txt compliance checking
- Content extraction success/failure
- Rate limiting and delays
- Browser automation vs HTTP fallback decisions

### `api_requests.log`
- Incoming API requests with parameters
- Response status codes and timing
- Authentication attempts
- Error responses and debugging info

### `scraping_detailed.log`
- Debug-level scraping information
- Full error stack traces
- Performance metrics
- Memory usage tracking

## Logging Features

### Windows Compatibility
- UTF-8 encoding for all log files
- Automatic permission checking
- Fallback directory creation
- Windows-specific path handling

### Security
- No sensitive data logged (passwords, tokens, etc.)
- Authentication methods logged without credentials
- URL parameters sanitized
- Custom headers logged without values

### Real-time Monitoring
- All logs updated in real-time during operations
- Separate loggers prevent duplicate entries
- Structured formatting for easy parsing

## Viewing Logs

### Windows Desktop App
1. Navigate to application directory
2. Open `logs` folder
3. Use any text editor to view log files
4. If not found, check `%USERPROFILE%\CrawlOpsStudio\logs\`

### Development Environment
```bash
# View recent activity
tail -f logs/scraping_activity.log

# Check API requests
tail -20 logs/api_requests.log

# Monitor all activity
tail -f logs/*.log
```

## Troubleshooting

### No Log Files Created
1. **Check Permissions**: Ensure write access to application directory
2. **Check Fallback Location**: Windows: `C:\Users\[Username]\CrawlOpsStudio\logs\`
3. **Verify Application**: Ensure CrawlOps Studio is running

### Empty Log Files
1. **Check Application Status**: Server must be running to generate logs
2. **Perform Operations**: Logs populate when crawling or using API
3. **Check File Handles**: Restart application if logs appear stuck

### Missing Specific Logs
- `scraping_activity.log` - Only created when crawling operations occur
- `api_requests.log` - Only created when API calls are made
- All log files created on first relevant event

## Example Log Entries

### Authentication Usage
```
2025-08-15 23:58:37 - SCRAPING - INFO - Using Basic authentication for https://example.com (user: testuser)
2025-08-15 23:58:37 - SCRAPING - INFO - Added 2 custom headers for https://example.com
```

### Robots.txt Handling
```
2025-08-15 23:58:37 - SCRAPING - INFO - Ignoring robots.txt for https://reddit.com (user override)
2025-08-15 23:58:38 - SCRAPING - INFO - Skipping https://blocked.com - blocked by robots.txt
```

### Crawling Operations
```
2025-08-15 23:58:39 - SCRAPING - INFO - Starting crawl for https://example.com - Max Depth: 2, Max Pages: 100
2025-08-15 23:58:40 - SCRAPING - DEBUG - Browser automation failed for https://example.com: Connection timeout
2025-08-15 23:58:41 - SCRAPING - INFO - Falling back to HTTP extraction for https://example.com
```

This comprehensive logging system provides full visibility into CrawlOps Studio operations for debugging, monitoring, and audit purposes.